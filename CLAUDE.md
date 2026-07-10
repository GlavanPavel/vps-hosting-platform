# VPS Hosting Platform

EC2-style IaaS built on OpenStack. This is the working codebase — read this before touching anything.

## Stack

| Layer | Technology |
|---|---|
| API | FastAPI (async) |
| Frontend | Nuxt 4 + Vue 3 + Tailwind CSS |
| Task queue | Celery + RabbitMQ |
| Relational DB | MariaDB + SQLAlchemy (async via aiomysql) |
| Time-series DB | InfluxDB |
| Infrastructure | OpenStack (managed by Kolla-Ansible) |

## Golden Rules — never break these

1. **FastAPI only reads** from MariaDB and InfluxDB. It never calls the OpenStack SDK.
2. **Celery workers own all OpenStack SDK calls.** VM creation, deletion, network provisioning, telemetry collection — all Celery.
3. **Domain Events decouple services from Celery.** Services emit events via `domain/dispatcher.py`. The `tasks/` package registers handlers with `@on(EventType)` (split per resource: `instance_tasks.py`, `keypair_tasks.py`, `security_group_tasks.py`, `network_tasks.py`, `floating_ip_tasks.py`, `volume_tasks.py`, `image_tasks.py`, `monitoring_tasks.py`, `org_tasks.py`, `telemetry.py`; shared DB session/OpenStack-connection helpers in `tasks/common.py`; `tasks/__init__.py` imports them all — `import tasks` in `main.py` wires the handlers, and Celery's `include=['tasks']` does the same for the worker). Services have zero knowledge of Celery.
4. **Networking is VPC-style.** No hardcoded global networks. Each org has private tenant networks. Floating IPs come from the external provider pool (`OS_EXTERNAL_NETWORK` in config).

## Architecture Patterns

### Repository Pattern
`backend/repositories/` — `BaseRepository[T]` provides generic CRUD. Specialized repos add domain queries (always org-scoped: `get_by_id_and_org`).

### Unit of Work
`backend/core/unit_of_work.py` — bundles all repos under one `AsyncSession`. Services accept a `UnitOfWork`, span multiple repos, call `uow.commit()` once. Never instantiate repos directly in services.

### Domain Events
`backend/domain/events.py` — plain dataclasses inheriting `DomainEvent`.
`backend/domain/dispatcher.py` — `dispatch(event)` calls registered handlers. `@on(EventType)` decorator registers a handler.
Pattern: service emits event → handler in the matching `tasks/*_tasks.py` module calls `.delay()`.

## Data Model

```
Organization
├── User (many)           → owns Keypairs
├── Network (many)        → has Subnets → Instances attach here
├── SecurityGroup (many)  → reusable, M2M with Instance
└── FloatingIP (many)     → nullable instance_id (SET NULL on delete)

Instance
├── organization_id  FK
├── user_id          FK
├── keypair_id       FK (SET NULL — survives keypair deletion)
├── subnet_id        FK
└── security_groups  M2M via instance_security_groups junction table
```

Key fields that are set *after* OpenStack provisioning (null until Celery task completes):
- `keypairs.openstack_name`
- `networks.openstack_network_id`
- `subnets.openstack_subnet_id`
- `security_groups.openstack_id`
- `instances.openstack_id`, `instances.private_ip_address`
- `floating_ips.*` (whole row created by Celery)

## Auth Status

**JWT in httpOnly cookies + short access token + refresh rotation.** `POST /auth/register` creates an Organization + User (bcrypt-hashed password). `POST /auth/login` validates and sets two **httpOnly cookies** (the service returns only the profile — token issuance is router-only via `_set_auth_cookies`): a **short-lived `access_token`** (`ACCESS_TOKEN_EXPIRE_MINUTES`, default 15, path `/`) and a **long-lived `refresh_token`** (`REFRESH_TOKEN_EXPIRE_DAYS`, default 7, path `/auth` so it only travels to the auth endpoints). Both JWTs carry a `type` claim (`access`/`refresh`); `core/security.py` `decode_token(token, expected_type)` rejects the wrong kind. **Server-side revocation via `users.refresh_token_hash`** (SHA-256 of the current refresh token; new nullable column → run `migrate_refresh_token.py` once on live MariaDB, `create_all` covers fresh installs + tests). `_issue_session` mints the token pair, stores its hash on the row, and sets the cookies. `POST /auth/refresh` requires the presented refresh token to **match the stored hash** (else 401 "revoked"), the user to be active, then **rotates** (new pair → new hash → sliding session) — so a logged-out, superseded or stolen-then-rotated token is rejected. `POST /auth/logout` nulls the hash (real server-side invalidation) and clears the cookies. Tokens carry a `jti` so every mint is unique. Note: a single hash column = **one active session per user** (a new login on another device invalidates the old one), and two tabs whose access tokens expire at the exact same instant can log the second one out — acceptable for this app; multi-session would need a separate `refresh_tokens` table. `GET /auth/me` returns the profile (incl. `role`). `routers/deps.py` `get_current_user_id` reads the `access_token` cookie (falling back to an `Authorization: Bearer` header for API clients). Cookie flags from `core/config.py`: `COOKIE_SECURE` (default False — set True on HTTPS in prod), `COOKIE_SAMESITE` (default `lax`; localhost :3000 ↔ :8000 are same-site so cookies flow; a cross-site prod deploy needs `none` + Secure). Set `JWT_SECRET_KEY` in `.env` for production. **Frontend is SPA (`ssr: false`)** — JS never sees the token; `composables/useApi.ts` sends `credentials: "include"` and, on a 401, silently calls `/auth/refresh` (single-flight) then retries; `stores/user.ts` derives auth state from `/auth/me` (no token in JS); `auth.global` middleware resolves the session via `fetchUser`; a `plugins/auth-redirect.client.ts` watcher bounces to `/login` when the session ends mid-use.

**Roles + RBAC + multi-user orgs.** `users.role` is `owner` | `member` | `admin` (the registering user is `owner`; existing rows defaulted to `owner` via an `ALTER TABLE`). `admin` is a **platform-level role above orgs** (see the admin-console bullet in What's Built + `make_admin.py` to grant it) — distinct from the org-scoped `owner`/`member`. **RBAC policy lives in `core/permissions.py`** — a single `ROLE_PERMISSIONS` map; the `OWNER_ONLY` set is the one knob (currently: `instance:delete`, `volume:delete`, `network:delete`, `security_group:delete`, `floating_ip:release`, `image:delete`, `image:publish`, `org:manage` — members get everything else, incl. create/power/attach/keypair:manage/image:create/`floating_ip:manage`). Enforced by `require_permission("…")` (`routers/deps.py`), added to the destructive routes via `dependencies=[Depends(require_permission(...))]`; a denied call is **403**. `deps.py` also has `get_current_user` (loads the row — a deactivated user's token 401s at once) + `CurrentUserModelDep`. The user profile (`/auth/me`) exposes a computed `permissions` list (from role) so the frontend can hide what a role can't do (`useAuth().can("instance:delete")`, plus `isOwner`); destructive buttons are `v-if`-gated across the dashboard, detail, volumes, networks, security-groups, images pages. `/org` router (`GET /org/members` any member; `POST`/`PATCH` owner-only via `org:manage`) manages members; `org_service` guards against self-deactivation and removing the org's **last active owner**. "Remove" = deactivate (`is_active=False`), avoiding FK fallout from `instances.user_id`/`keypairs.user_id`. Frontend `/team` page: owner sees add-member form + role selects + activate/deactivate; members see a read-only roster.

## What's Built

- All SQLAlchemy models (`models/`)
- All Pydantic schemas (`schemas/`)
- Repository layer (`repositories/`)
- Unit of Work (`core/unit_of_work.py`)
- Domain events + dispatcher (`domain/`)
- Services for instances, keypairs, security groups, networks, auth (`services/`)
- JWT auth: `/auth/register`, `/auth/login`, `/auth/me` + bearer dependency (`core/security.py`, `routers/deps.py`)
- FastAPI routers: `/auth`, `/instances` (list + `GET /instances/{id}` detail + create + delete + `POST /instances/{id}/stop` + `POST /instances/{id}/start` + `POST /instances/{id}/reboot` + `GET /instances/{id}/console` + `GET /instances/{id}/logs` + `GET /instances/{id}/events` + `POST /instances/{id}/snapshot`), `/keypairs` (list/import + `POST /keypairs/generate` + delete), `/security-groups`, `/networks`, `/floating-ips` (allocate/associate/disassociate/release), `/volumes`, `/images`, `/org` (member management), `/usage` (metered usage), `/instances/{id}/metrics` (all auth-protected; CORS enabled for the frontend origin)
- Block storage (Cinder volumes): `/volumes` router (list/create/delete + `POST /volumes/{id}/attach` + `POST /volumes/{id}/detach`). `Volume` model is org-scoped with a nullable `instance_id` (SET NULL). Service emits `VolumeCreationRequested`/`VolumeDeletionRequested`/`VolumeAttachRequested`/`VolumeDetachRequested`; Celery tasks `provision_volume`/`delete_volume`/`attach_volume`/`detach_volume` own the Cinder + nova-attach SDK calls. Create-instance also accepts `root_disk_gb` (custom root disk — boots from a Cinder volume created from the image via `block_device_mapping_v2` with `delete_on_termination`, instead of the flavor's ephemeral disk), `data_volume_size_gb` (a new data disk) and `attach_volume_ids` (existing volumes) — the data disk + existing volumes are created/attached by `provision_instance` after the VM is ACTIVE (best-effort, like floating IPs). Frontend: `/volumes` page + a Storage section on `/create` + an attached-volumes card on the instance detail page. **Requires Cinder enabled in Kolla** (`enable_cinder` + `enable_cinder_backend_lvm`).
- Floating IP management (EC2 Elastic-IP style): floating IPs are **first-class resources** — `/floating-ips` router (list + `POST /floating-ips/` allocate + `POST /floating-ips/{id}/associate` `{instance_id}` + `POST /floating-ips/{id}/disassociate` + `DELETE /floating-ips/{id}` release). Service emits `FloatingIPAllocationRequested`/`FloatingIPAssociationRequested`/`FloatingIPDisassociationRequested`/`FloatingIPReleaseRequested`; Celery tasks `allocate_floating_ip`/`associate_floating_ip`/`disassociate_floating_ip`/`release_floating_ip` own the neutron `create_ip`/`update_ip`/`delete_ip` calls. **Allocation is the one place Celery creates the row** (not the service) — `ip_address`/`openstack_floatingip_id` are NOT NULL and only exist after the SDK call, so the new row shows up on the next list poll (no schema migration needed). Status vocabulary: `allocating`→`available` (reserved, unattached) ⇄ `associating`→`in-use` (attached) / `disassociating` / `releasing` / `ERROR`. RBAC: allocate/associate/disassociate are **member-allowed** (`floating_ip:manage`); **release is owner-only** (`floating_ip:release`, in `OWNER_ONLY`). **Opt-in on create**: `InstanceRequest.assign_floating_ip` (default `true`, pass-through — not stored) gates the auto-allocate in `provision_instance`; a checkbox on `/create` ("Assign a public IP") drives it. **Instance delete now disassociates (keeps) the FIP** instead of releasing it (`delete_instance` sets `instance_id=None`, `status=available`) — the reserved IP survives, reusable, AWS-faithful (replaces the old release-on-delete). Frontend: `/floating-ips` page (allocate button + per-row associate/disassociate/release, polling) + Attach/Detach controls on the instance detail Public-IP card + the create-page checkbox. Legacy note: pre-existing auto-allocated FIP rows used status `ACTIVE`; the UI keys its row actions off `instance_id` (+ a transient-status guard), not the exact status string, so those still work.
- Startup script + batch launch (EC2-style): `POST /instances/` also accepts `user_data` (a cloud-init script, plain text — `provision_instance` base64-encodes it and passes it to nova's `create_server`, runs once on first boot) and `count` (1–10; the service creates N DB rows in one commit, suffixes their names `name-1`/`name-2`/… when `count > 1`, and fans out one `InstanceProvisioningStarted` event each). The endpoint now returns `list[InstanceResponse]`. `attach_volume_ids` is rejected (422) when `count > 1` — a volume attaches to exactly one server. `user_data` is pass-through only (not stored on the Instance row — avoids a non-`create_all` column migration). Frontend `/create`: a Startup script card (textarea + file upload) and a Number-of-instances field next to the Create button; the existing-volumes picker is disabled in batch mode.
- Instance snapshots: `POST /instances/{id}/snapshot` (`{name}`, gated by member-allowed `instance:snapshot`) captures a running/stopped instance's disk as a **Glance image — reusing the `Image` model**. The `Image` row carries `source_type` (`url` | `snapshot`) + nullable `source_instance_id` (SET NULL). Service `snapshot_instance` (ACTIVE/SHUTOFF only) creates an Image (`status=snapshotting`) and emits `InstanceSnapshotRequested`; Celery `snapshot_instance` calls `conn.compute.create_server_image(server, "{name}-{id}")`, polls to active, records the UUID/size. The snapshot then appears on `/images` (violet "snapshot" badge) and is launchable from `/create` like any active image. Frontend: a "Snapshot" button on the instance detail page (ACTIVE/SHUTOFF). **Boot-from-volume instances snapshot via Cinder volume snapshots** (consumes the LVM VG); ephemeral instances make a plain Glance image.
- Custom OS images (Glance, URL import): `/images` router (list/create/delete + `POST /images/{id}/visibility`). `Image` model is org-scoped (`source_url`, `disk_format`, nullable `openstack_image_id`, `status` queued→importing→active|ERROR, `size_bytes`/`min_disk_gb` filled once active, `is_public` flag). Service emits `ImageCreationRequested`/`ImageDeletionRequested`/`ImageVisibilityChangeRequested`; Celery `provision_image` registers a queued Glance image then `conn.image.import_image(method="web-download", uri=source_url)` so **Glance fetches the file itself** (no multi-GB upload through FastAPI), polls to `active`, and records the UUID + size; `delete_image` removes it from Glance; `set_image_visibility` flips the Glance `visibility` public/private (needs the admin OpenStack user). Image name is capped at 40 chars so the Glance name `{name}-{id}` fits `instances.image_name(50)`. `GET /images/?include_public=true` returns the org's own images **plus** every public image (any org). Frontend: `/images` page (import-from-URL form + status-polling table + per-row public/private toggle). Direct file upload is the not-yet-built phase 2.
- Image picker + preconfigured servers (on `/create`): the **main OS grid shows built-in cirros/ubuntu + the two presets** (Ollama, WordPress) — a clean 4-card row. A "Browse presets & custom images" link opens a modal with three tabs — **Bare OS** (builtins only), **Preconfigured servers** (a frontend `presetCatalog`: Ollama, WordPress — each sets the base image `ubuntu-24.04` + a cloud-init `user_data` script + a recommended `root_disk_gb`), and **Custom images** (all **active** customs visible to the org — own + public, distro-iconed by name; deliberately kept out of the Bare OS list). Presets reuse the existing `user_data` plumbing — no backend involved; selecting one shows a chip and the script runs on first boot (the user must open the relevant port in a security group, and the instance needs outbound internet).
- Instance power management: `stop`/`start`/`reboot` follow the domain-event → Celery pattern. Service sets a transient status (`STOPPING`/`STARTING`/`REBOOT`) + dispatches `InstanceStopRequested`/`InstanceStartRequested`/`InstanceRebootRequested`; the Celery task powers the VM and writes the terminal status (`SHUTOFF`/`ACTIVE`, or `ERROR` on failure). `reboot` is a **soft** reboot (`conn.compute.reboot_server(server, "SOFT")` — graceful guest reboot, stays ACTIVE; the task sleeps 5s so it doesn't catch the pre-reboot ACTIVE, then waits for the return to ACTIVE). `REBOOT` is in `_TRANSIENT_STATES` so the poller won't clobber it. Stop = graceful power-off (SHUTOFF, nothing deleted). Available from the dashboard rows and the detail page (Restart shows for ACTIVE instances next to Stop).
- Usage metering: `meter_usage` (Celery Beat, every 60s) adds one interval of runtime to every **ACTIVE** instance's `instances.running_seconds` counter — **pure DB, no OpenStack call**, so it keeps metering even when the cloud API is unreachable (approximate by design: only measured time is counted). `usage_service.get_usage` (`GET /usage/`) returns per-instance uptime hours (`running_seconds/3600`) + an **allocated footprint**: `running_instances`, `vcpus_allocated`, `ram_gb_allocated` (flavor-reserved amounts summed over ACTIVE instances via `core/flavors.py` `FLAVOR_SPECS` — **not** measured in-guest consumption, which the hypervisor doesn't expose), and `storage_gb` (sum of volume sizes). **No cost/pricing** — usage only (the earlier billing/cost layer + `core/pricing.py` were removed). Frontend `/usage` page (sidebar "Usage"): footprint cards (running instances / vCPUs / RAM GB / storage GB) + a per-instance hours table + a volume name/size table, polling every 60s. `running_seconds` was added via `ALTER TABLE`.
- Platform administrator role + admin console: a **third role `admin`** that sits *above* organizations (owner/member are org-scoped; admin is platform-level). `core/permissions.py` adds `ROLE_PERMISSIONS["admin"] = ALL_PERMISSIONS ∪ {"admin:view"}`; **`admin:view` is deliberately NOT in `ALL_PERMISSIONS`**, so owner/member never receive it. `routers/deps.py` `require_admin` gates the whole `/admin` router (403 otherwise). Admin endpoints **bypass org-scoping** via the repos' non-scoped `get_all()`: `GET /admin/overview` (real cluster capacity + platform totals), `GET /admin/organizations` (per-org usage rows), `GET /admin/users` (every account + per-user footprint) — all read-only (`services/admin_service.py`, aggregates in Python via `flavor_spec`). `POST /admin/cloud-stats/refresh` triggers `collect_cloud_stats.delay()` so the admin can pull capacity on demand (the Overview page has a "Refresh from OpenStack" button) without waiting for the 60s beat. The Overview shows the cluster **maximums** (`vcpus_total`/`ram_gb_total`/`disk_gb_total`/`storage_gb_total`) as headline cards (used·free) plus utilization bars — "Total" = the hardware ceiling from nova, distinct from the DB-derived *allocated* footprint below. **The collector pins the nova call to microversion 2.87** (`conn.compute.get("/os-hypervisors/statistics", microversion="2.87")`) because nova ≥ 2.88 dropped the vcpus/memory_mb/local_gb fields — without the pin the totals come back 0 (Cinder is unaffected); the old per-hypervisor SDK loop is a fallback. **Admin lifecycle actions** (cross-org, gated by `require_admin`): `PATCH /admin/users/{id}` `{is_active}` activate/deactivate (deactivate also **stops** the instances that user owns), `DELETE /admin/users/{id}` (reassigns their instances to an org owner + removes their keypairs, then deletes the user — `instances.user_id`/`keypairs.user_id` are NOT NULL so a raw delete would FK-fail), `POST /admin/organizations/{id}/active` `{is_active}` suspend/reactivate the whole org (suspend = deactivate every member + stop all its instances), `DELETE /admin/organizations/{id}` → emits `OrganizationDeletionRequested` → Celery **`teardown_organization`** deletes every OpenStack resource the org owns (servers → floating IPs → volumes → security groups → networks/routers → images → keypairs, each best-effort) then removes all DB rows in FK order. Key insight surfaced to the user: **deactivating frees nothing** (VMs keep running/metering — it's access control); only stop (drops the ACTIVE-only footprint + pauses metering) or delete (frees everything) changes allocation. Self-guards: an admin can't deactivate/delete their own account or org. `OrgUsageRow.suspended` (derived: has users but none active) drives the Suspended badge; admins can't act on their own org row (`yours`). Frontend: per-row Deactivate/Reactivate + Delete on `/admin/users`, Suspend/Activate + Delete (type-the-name confirm) on `/admin/organizations`, both polling.
- Per-org quotas: admin caps each org's `max_instances`/`max_vcpus`/`max_ram_gb`/`max_volumes`/`max_storage_gb`/`max_floating_ips`. Limits live in a new **`quotas` table** (one row per org, unique `organization_id`; new table → `create_all`, no migration); an org **without a row falls back to `core/quotas.py` `DEFAULT_QUOTA`** (`QuotaResponse.is_default` flags this). `services/quota_service.py`: `get_quota` (effective limits + current usage), `set_quota` (upsert the row), and **`enforce_quota(...)`** which raises **409** ("Quota exceeded — …") if a create would exceed any limit. Enforcement is wired into the three create paths: `create_instance` (instances + vCPU + RAM × `count`, plus a floating IP each when `assign_floating_ip`), `create_volume` (volumes + storage), `allocate_floating_ip` (floating IPs). **Usage counts every row the org owns regardless of status** (a stopped/building instance still holds its slot until deleted) — stricter than the admin dashboard's ACTIVE-only footprint, by design. Endpoints: member `GET /quota/` (own org), admin `GET`/`PUT /admin/organizations/{id}/quota`. Frontend: a **Quota section on `/usage`** (six `UsageBar`s, used/max) + a **Quota editor modal on `/admin/organizations`** (per-row "Quota" button, prefilled, shows current usage per field); the create-page 409s surface via the existing toasts. **Real OpenStack capacity** comes from a new Celery Beat task `collect_cloud_stats` (every 60s) that sums nova `hypervisors(details=True)` (vCPU/RAM/disk/running VMs) + best-effort cinder pool capacity into a **single-row `cloud_stats` table** (new table → `create_all` makes it, **no manual migration**); FastAPI only reads that row (golden rule intact). Bootstrap: `python make_admin.py <email>` (`--revoke` to demote) flips a registered user's `role` to `admin` via the sync pymysql engine — admins can't self-register; role re-reads from DB on every `/auth/me`, so a refresh applies it (no re-login). Frontend: a **separate indigo `admin` layout** (`layouts/admin.vue`, own sidebar Overview/Organizations/Users + "Back to app"), `middleware/admin.ts` bounces non-admins to `/`, pages under `pages/admin/` (`index` capacity bars via `UsageBar` + totals, `organizations`, `users`), `useAuth().isAdmin`, and an "Admin Console" sidebar entry shown only to admins.
- Periodic health check: `sync_instance_states` (Celery Beat, every 30s) reconciles each instance's DB status with the live OpenStack power state, so a VM stopped/crashed out-of-band shows up correctly. It skips in-flight states (`BUILD`/`DELETING`/`STOPPING`/`STARTING`) so it never clobbers a running task; a non-transient `ERROR` self-heals on the next pass.
- Web noVNC console: `GET /instances/{id}/console` returns a fresh nova noVNC URL. The OpenStack SDK call stays in Celery (`get_console_url` task); FastAPI waits on the result via the **rpc result backend** (`backend="rpc://"` in `core/celery_app.py`, reuses RabbitMQ — no extra service). The frontend opens it in an iframe modal. The URL points at the novncproxy on `kolla_internal_vip_address:6080` (reachable over Tailscale).
- Instance console log: `GET /instances/{id}/logs?lines=N` returns the server's nova console (boot/serial) output — the equivalent of `nova console-log`. Same pattern as the console URL: the SDK call (`conn.compute.get_server_console_output`) lives in a Celery task (`get_console_output`) and FastAPI waits on the **rpc result backend**; not retried (synchronous, user-facing). Available for any provisioned instance (has `openstack_id`), not just ACTIVE — a 502 surfaces if nova can't return it. Frontend: an inline, GCP-Logging-style **Console log panel at the end of the instance detail page** (line-numbered monospace rows, fetched once on load + a Refresh button for the last 500 lines).
- Per-instance event log: a small **`instance_events` table** (new table → `create_all`, no migration) gives each machine its own timeline of lifecycle events, errors and warnings. `models/instance_event.py` carries `instance_id` (FK **ON DELETE CASCADE** — events die with the instance), `severity` (`info` | `warning` | `error`, drives the icon/colour), `message`, `created_at`. **Two writers, one table**: FastAPI logs user-initiated *requests* via the async **`services/instance_event_service.py` `record_event(uow, instance_id, severity, message)`** (created · stop/start/restart requested · snapshot requested · deletion requested), and **Celery logs the real OpenStack outcomes** via a sync **`_log_event(instance_id, severity, message)`** in `tasks/common.py` (became active + private IP, public-IP assigned, provisioning failed = error, volume/FIP warnings, powered off, started, reboot completed, snapshot created/failed). The **30s `sync_instance_states` health check also logs out-of-band transitions** (entered ERROR, powered off outside the dashboard, active again) — this is how "an error happened at this time / a warning about something" lands in the log without any user action. Both writers are **best-effort** (never raise, so a logging hiccup can't fail the action/task). `GET /instances/{id}/events?limit=N` (org-scoped via the instance ownership check) → `services.list_events`, most-recent-first (`id` breaks `created_at` ties). `teardown_organization` deletes the org's instance events before its instances (they'd cascade anyway). Frontend: an **"Event log" card on the instance detail page** — a compact severity-iconed (sky/amber/rose) timeline with relative timestamps, polling with the page's 10s tick. **No separate activity page** — deliberately per-machine, on the detail page.
- Server-side keypair generation: `POST /keypairs/generate` mints an ed25519/RSA keypair with `cryptography`, stores only the public half, and returns the private key once (never persisted). Pure crypto in FastAPI — Celery still uploads the public key, same as an imported one.
- Celery tasks: `provision_instance` (auto-allocates a FIP only when `assign_floating_ip`), `delete_instance` (disassociates + keeps any FIP), `stop_instance`, `start_instance`, `sync_instance_states` (periodic health check), `upload_keypair`, `delete_keypair`, `provision_security_group`, `delete_security_group`, `provision_network` (creates network + subnets, then a router with external gateway and a subnet interface so floating IPs route), `delete_network` (409 while instances attached; tears down router interfaces + router, then subnets + network), `allocate_floating_ip`/`associate_floating_ip`/`disassociate_floating_ip`/`release_floating_ip` (floating IP management), `get_console_url` (returns a noVNC URL synchronously via the rpc backend), `poll_instance_metrics`
- `networks.openstack_router_id` stores the per-network router; passed through `NetworkDeletionRequested` for cleanup
- Event handler wiring lives next to each task in its `tasks/*_tasks.py` module
- Frontend ↔ backend integration: login/register pages, JWT in httpOnly cookies with silent refresh (`useAuth`/`useApi` composables, global auth middleware — see Auth Status), live dashboard with clickable rows, instance detail page (`/instances/[id]` — specs cards (vCPUs/RAM/storage from the flavor, exposed on `InstanceDetailResponse`), SSH connect command, network/security info, persisted CPU usage chart, inline console log), create-instance flow, management pages for keypairs (generate + import)/networks/security groups
- Frontend state (Pinia, `@pinia/nuxt`): **`stores/user.ts` (`useUserStore`)** is the session source of truth (user/role/`permissions`, getters `isAuthenticated`/`isOwner`/`isAdmin`, `can()`, + `login`/`register`/`fetchUser`/`logout`); the JWT stays in an SSR-aware **cookie** (not persisted store state). **`useAuth()` is a thin adapter** over it (`storeToRefs` + actions) so all existing call sites are unchanged — new code may call `useUserStore()` directly. **`stores/toast.ts` (`useToastStore`)** is a global toast queue (`success`/`error`/`info`, auto-dismiss) rendered by `<ToastHost>` in both layouts; wired into the floating-IPs page actions (other pages can adopt incrementally). **Page data still uses `useAsyncData` + polling** — deliberately *not* moved into per-resource stores (idiomatic Nuxt; keeps SSR/hydration + live polling).
- Shared UI components in `frontend/app/components/` (`StatusBadge`, `SyncBadge`, `StatCard`, `CopyButton`, `EmptyState`, `LineChart`)

## What's NOT Built Yet

- Custom-image **direct file upload** (only URL import / web-download is built — phase 2 would stream a local file through FastAPI to a staging path, then Celery pushes it to Glance)

## Infrastructure

- OpenStack runs on an Ubuntu Server VM in VMware on a Windows 11 host
- Kolla-Ansible all-in-one deployment
- `kolla_internal_vip_address = 192.168.144.200` (the OpenStack API endpoint)
- Tailscale installed on the OpenStack VM — routes `192.168.144.200/32` through the tunnel
- Dev machine connects to OpenStack over Tailscale from anywhere
- `OS_AUTH_URL=http://192.168.144.200:5000/v3` in `.env`

## Running the Project

```bash
# 1. Start infra (from backend/)
docker compose up -d

# 2. FastAPI
uvicorn main:app --reload --host 0.0.0.0 --port 8000

# 3. Celery worker (--pool=solo required on Windows)
celery -A core.celery_app worker --loglevel=info --pool=solo

# 4. Celery Beat (telemetry every 60s)
celery -A core.celery_app beat --loglevel=info
```

```bash
# 5. Frontend (from frontend/)
npm run dev   # http://localhost:3000, API base configurable via NUXT_PUBLIC_API_BASE
```

## Testing

Backend test suite under `backend/tests/` (pytest + pytest-asyncio). Runs against an
**in-memory SQLite** DB (no MariaDB) and **never touches OpenStack or Celery** — the
domain dispatcher is a no-op because the `tasks` package isn't imported, so no handlers
are registered (the `events` fixture in `conftest.py` captures dispatched events when a
test asserts on them). `conftest.py` sets throwaway env vars before importing
`core.config`, builds a fresh SQLite engine per test (`StaticPool` so `:memory:`
persists), and exposes `uow`/`session`/`engine`/`events` fixtures; `tests/factories.py`
seeds orgs/users/subnets/keypairs/SGs/instances. Coverage: RBAC matrix
(`core/permissions.py`), JWT + bcrypt (`core/security.py`), flavor specs, quota
enforcement (`enforce_quota` 409s, defaults, usage counting), auth register/login
(incl. deactivated-user 403), org-member guards (last active owner, self-deactivate),
instance create (batch name suffixing + event fan-out + quota rejection), admin
actions (deactivate stops instances, delete-user reassigns + drops keypairs, suspend
org, self-guards, overview totals), and the per-instance event log (record_event
appends to an instance's log, most-recent-first + per-instance scoping, and
create_instance / stop_instance emit lifecycle events).

```bash
# from backend/ (test deps: pip install -r requirements-dev.txt)
pytest            # 63 tests, in-memory SQLite, no external services
```

## Bootstrap

No manual SQL needed — `POST /auth/register` (or the frontend `/register` page) creates the first org + user. To grant the **platform admin** role, register a user normally then run `python make_admin.py <email>` from `backend/` (admins can't self-register).

## Create Instance — prerequisite chain

1. Keypair created via `POST /keypairs/` (import) or `POST /keypairs/generate` (server-side) — Celery uploads it to OpenStack and fills `openstack_name`
2. Network + Subnet provisioned (Celery fills `openstack_subnet_id`)
3. SecurityGroup created via `POST /security-groups/` — Celery mirrors it and fills `openstack_id`
4. Then `POST /instances/` with `{ name, flavor_name, image_name, keypair_id, subnet_id, security_group_ids }`

The frontend create page (`/create`) enforces this chain — it only offers resources whose OpenStack ids are set. Built-in image names + the flavor list are defined in `frontend/app/pages/create.vue` (`builtinOs`/`flavorList`) and must match what exists in OpenStack; the OS grid (`osList`) is now a computed that appends the org's **active** custom images (from `GET /images/`, launched by their Glance name `{name}-{id}`).
