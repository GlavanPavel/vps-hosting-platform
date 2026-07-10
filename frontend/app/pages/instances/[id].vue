<template>
	<div>
		<NuxtLink
			to="/"
			class="inline-flex items-center gap-1.5 text-sm text-slate-500 hover:text-slate-800 transition-colors mb-5"
		>
			<Icon name="solar:alt-arrow-left-outline" />
			Back to dashboard
		</NuxtLink>

		<div
			v-if="pending && !instance"
			class="text-slate-400 py-20 text-center"
		>
			Loading…
		</div>

		<EmptyState
			v-else-if="!instance"
			icon="solar:server-square-outline"
			title="Instance not found"
			description="It may have been deleted."
		>
			<NuxtLink
				to="/"
				class="text-sm text-slate-700 font-medium hover:underline"
			>
				Return to dashboard
			</NuxtLink>
		</EmptyState>

		<template v-else>
			<!-- header -->
			<div class="flex items-start justify-between mb-7">
				<div class="flex items-center gap-3">
					<div class="h-11 w-11 rounded-xl bg-slate-800 text-yellow-400 flex items-center justify-center">
						<Icon
							name="solar:server-square-bold-duotone"
							class="text-2xl"
						/>
					</div>
					<div>
						<div class="flex items-center gap-3">
							<h1 class="text-2xl font-bold text-slate-900">
								{{ instance.name }}
							</h1>
							<StatusBadge :status="instance.status" />
						</div>
						<p class="text-sm text-slate-500 mt-0.5">
							{{ instance.image_name }} · {{ instance.flavor_name }}
						</p>
					</div>
				</div>
				<div class="flex items-center gap-3">
					<button
						v-if="instance.status === 'SHUTOFF'"
						class="inline-flex items-center gap-2 border border-green-200 text-green-700 hover:bg-green-50 font-medium py-2 px-4 rounded-lg transition-colors disabled:opacity-40"
						:disabled="powerLoading"
						@click="powerAction('start')"
					>
						<Icon
							name="solar:play-circle-outline"
							class="text-lg"
						/>
						Start
					</button>
					<template v-else-if="instance.status === 'ACTIVE'">
						<button
							class="inline-flex items-center gap-2 border border-blue-200 text-blue-700 hover:bg-blue-50 font-medium py-2 px-4 rounded-lg transition-colors disabled:opacity-40"
							:disabled="powerLoading"
							title="Reboot the guest OS (stays running, brief restart)"
							@click="powerAction('reboot')"
						>
							<Icon
								name="solar:restart-outline"
								class="text-lg"
							/>
							Restart
						</button>
						<button
							class="inline-flex items-center gap-2 border border-amber-200 text-amber-700 hover:bg-amber-50 font-medium py-2 px-4 rounded-lg transition-colors disabled:opacity-40"
							:disabled="powerLoading"
							@click="powerAction('stop')"
						>
							<Icon
								name="solar:stop-circle-outline"
								class="text-lg"
							/>
							Stop
						</button>
					</template>
					<button
						class="inline-flex items-center gap-2 bg-slate-800 hover:bg-slate-700 disabled:opacity-40 text-white font-medium py-2 px-4 rounded-lg transition-colors"
						:disabled="instance.status !== 'ACTIVE' || consoleLoading"
						title="Open the VNC console in the browser"
						@click="openConsole"
					>
						<Icon
							name="solar:monitor-outline"
							class="text-lg"
						/>
						{{ consoleLoading ? "Opening…" : "Console" }}
					</button>
					<button
						v-if="can('instance:snapshot') && (instance.status === 'ACTIVE' || instance.status === 'SHUTOFF')"
						class="inline-flex items-center gap-2 border border-slate-200 text-slate-700 hover:bg-slate-50 font-medium py-2 px-4 rounded-lg transition-colors disabled:opacity-40"
						:disabled="snapshotLoading"
						title="Capture this instance's disk as a reusable image"
						@click="snapshot"
					>
						<Icon
							name="solar:camera-outline"
							class="text-lg"
						/>
						{{ snapshotLoading ? "Snapshotting…" : "Snapshot" }}
					</button>
					<button
						v-if="can('instance:delete')"
						class="inline-flex items-center gap-2 border border-red-200 text-red-600 hover:bg-red-50 font-medium py-2 px-4 rounded-lg transition-colors disabled:opacity-40"
						:disabled="instance.status === 'DELETING'"
						@click="remove"
					>
						<Icon
							name="solar:trash-bin-trash-outline"
							class="text-lg"
						/>
						Delete
					</button>
				</div>
			</div>

			<p
				v-if="actionError"
				class="text-red-600 text-sm -mt-4 mb-5"
			>
				{{ actionError }}
			</p>

			<!-- specs -->
			<div class="grid grid-cols-2 lg:grid-cols-4 gap-5 mb-5">
				<div class="bg-white rounded-xl border border-slate-200/70 shadow-sm p-5">
					<div class="flex items-center gap-2 text-slate-500 mb-1">
						<Icon
							name="solar:cpu-outline"
							class="text-base"
						/>
						<p class="text-sm">
							vCPUs
						</p>
					</div>
					<p class="text-2xl font-bold text-slate-900">
						{{ instance.vcpus }}
					</p>
				</div>
				<div class="bg-white rounded-xl border border-slate-200/70 shadow-sm p-5">
					<div class="flex items-center gap-2 text-slate-500 mb-1">
						<Icon
							name="solar:ssd-square-outline"
							class="text-base"
						/>
						<p class="text-sm">
							Memory
						</p>
					</div>
					<p class="text-2xl font-bold text-slate-900">
						{{ ramDisplay }}
					</p>
				</div>
				<div class="bg-white rounded-xl border border-slate-200/70 shadow-sm p-5">
					<div class="flex items-center gap-2 text-slate-500 mb-1">
						<Icon
							name="solar:database-outline"
							class="text-base"
						/>
						<p class="text-sm">
							Storage
						</p>
					</div>
					<p class="text-2xl font-bold text-slate-900">
						{{ totalStorageGb }} GB
					</p>
					<p class="text-xs text-slate-400 mt-0.5">
						{{ storageBreakdown }}
					</p>
				</div>
				<div class="bg-white rounded-xl border border-slate-200/70 shadow-sm p-5">
					<div class="flex items-center gap-2 text-slate-500 mb-1">
						<Icon
							name="solar:server-outline"
							class="text-base"
						/>
						<p class="text-sm">
							Flavor
						</p>
					</div>
					<p class="text-lg font-bold text-slate-900">
						{{ instance.flavor_name }}
					</p>
					<p class="text-xs text-slate-400 mt-0.5 truncate">
						{{ instance.image_name }}
					</p>
				</div>
			</div>

			<!-- network / meta -->
			<div class="grid grid-cols-2 lg:grid-cols-3 gap-5 mb-6">
				<div class="bg-white rounded-xl border border-slate-200/70 shadow-sm p-5">
					<p class="text-sm text-slate-500 mb-1">
						Private IP
					</p>
					<p class="font-mono text-slate-900 font-medium">
						{{ instance.private_ip_address ?? "—" }}
					</p>
				</div>
				<div class="bg-white rounded-xl border border-slate-200/70 shadow-sm p-5">
					<p class="text-sm text-slate-500 mb-1">
						Public IP
					</p>
					<p class="font-mono text-slate-900 font-medium">
						{{ instance.floating_ip?.ip_address ?? "—" }}
					</p>
					<button
						v-if="can('floating_ip:manage') && instance.floating_ip"
						class="text-xs text-slate-500 hover:text-red-600 font-medium mt-1.5 transition-colors disabled:opacity-40"
						:disabled="fipLoading"
						@click="detachFip"
					>
						Detach
					</button>
					<button
						v-else-if="can('floating_ip:manage') && !instance.floating_ip && instance.openstack_id"
						class="text-xs text-slate-500 hover:text-slate-900 font-medium mt-1.5 transition-colors disabled:opacity-40"
						:disabled="fipLoading"
						@click="openAttachFip"
					>
						Attach a public IP
					</button>
				</div>
				<div class="bg-white rounded-xl border border-slate-200/70 shadow-sm p-5">
					<p class="text-sm text-slate-500 mb-1">
						Created
					</p>
					<p class="text-slate-900 font-medium text-sm">
						{{ new Date(instance.created_at).toLocaleString() }}
					</p>
				</div>
			</div>

			<div class="grid lg:grid-cols-2 gap-6 mb-6">
				<!-- connection -->
				<div class="bg-white rounded-xl border border-slate-200/70 shadow-sm p-6">
					<h2 class="font-semibold text-slate-900 mb-4 flex items-center gap-2">
						<Icon
							name="solar:command-outline"
							class="text-slate-400"
						/>
						SSH Connection
					</h2>
					<div v-if="sshCommand">
						<div class="flex items-center justify-between gap-3 bg-slate-900 rounded-lg px-4 py-3">
							<code class="text-sm text-slate-100 font-mono break-all">{{ sshCommand }}</code>
							<CopyButton :text="sshCommand" />
						</div>
						<p class="text-xs text-slate-400 mt-2">
							Uses key <span class="font-medium text-slate-600">{{ instance.keypair?.name }}</span>.
							Adjust the path if your private key lives elsewhere.
						</p>
					</div>
					<p
						v-else
						class="text-sm text-slate-500"
					>
						<template v-if="!instance.floating_ip">
							No public IP assigned — assign a floating IP to connect over SSH.
						</template>
						<template v-else>
							No keypair recorded for this instance.
						</template>
					</p>
				</div>

				<!-- network & security -->
				<div class="bg-white rounded-xl border border-slate-200/70 shadow-sm p-6">
					<h2 class="font-semibold text-slate-900 mb-4 flex items-center gap-2">
						<Icon
							name="solar:global-outline"
							class="text-slate-400"
						/>
						Network &amp; Security
					</h2>
					<dl class="space-y-3 text-sm">
						<div class="flex justify-between gap-4">
							<dt class="text-slate-500">
								Network
							</dt>
							<dd class="text-slate-900 font-medium text-right">
								{{ instance.subnet?.network_name ?? "—" }}
							</dd>
						</div>
						<div class="flex justify-between gap-4">
							<dt class="text-slate-500">
								Subnet
							</dt>
							<dd class="text-slate-900 font-medium text-right">
								{{ instance.subnet ? `${instance.subnet.name} (${instance.subnet.cidr})` : "—" }}
							</dd>
						</div>
						<div class="flex justify-between gap-4">
							<dt class="text-slate-500">
								Keypair
							</dt>
							<dd class="text-slate-900 font-medium text-right">
								{{ instance.keypair?.name ?? "—" }}
							</dd>
						</div>
						<div class="flex justify-between gap-4 items-start">
							<dt class="text-slate-500 pt-1">
								Security groups
							</dt>
							<dd class="flex flex-wrap gap-1.5 justify-end">
								<span
									v-for="sg in instance.security_groups"
									:key="sg.id"
									class="text-xs font-medium bg-slate-100 text-slate-700 rounded-md px-2 py-1"
								>
									{{ sg.name }}
								</span>
								<span
									v-if="instance.security_groups.length === 0"
									class="text-slate-400"
								>—</span>
							</dd>
						</div>
					</dl>
				</div>
			</div>

			<!-- storage -->
			<div
				v-if="instance.volumes?.length"
				class="bg-white rounded-xl border border-slate-200/70 shadow-sm p-6 mb-6"
			>
				<h2 class="font-semibold text-slate-900 mb-4 flex items-center gap-2">
					<Icon
						name="solar:database-outline"
						class="text-slate-400"
					/>
					Storage
				</h2>
				<table class="w-full text-left text-sm">
					<thead class="text-slate-400 text-xs uppercase tracking-wider">
						<tr>
							<th class="py-1.5 pr-4 font-semibold">
								Volume
							</th>
							<th class="py-1.5 pr-4 font-semibold">
								Size
							</th>
							<th class="py-1.5 pr-4 font-semibold">
								Device
							</th>
							<th class="py-1.5 pr-4 font-semibold">
								Status
							</th>
						</tr>
					</thead>
					<tbody>
						<tr
							v-for="vol in instance.volumes"
							:key="vol.id"
							class="text-slate-600"
						>
							<td class="py-1.5 pr-4 font-medium text-slate-800">
								{{ vol.name }}
							</td>
							<td class="py-1.5 pr-4">
								{{ vol.size_gb }} GB
							</td>
							<td class="py-1.5 pr-4 font-mono">
								{{ vol.device ?? "—" }}
							</td>
							<td class="py-1.5 pr-4">
								<StatusBadge :status="vol.status" />
							</td>
						</tr>
					</tbody>
				</table>
			</div>

			<!-- event log -->
			<div class="bg-white rounded-xl border border-slate-200/70 shadow-sm p-6 mb-6">
				<h2 class="font-semibold text-slate-900 mb-4 flex items-center gap-2">
					<Icon
						name="solar:history-outline"
						class="text-slate-400"
					/>
					Event log
				</h2>
				<p
					v-if="!events || events.length === 0"
					class="text-sm text-slate-400"
				>
					No events recorded yet — actions like start, stop and errors will appear here.
				</p>
				<ul
					v-else
					class="space-y-2.5 max-h-72 overflow-auto pr-1"
				>
					<li
						v-for="ev in events"
						:key="ev.id"
						class="flex items-start gap-3 text-sm"
					>
						<Icon
							:name="eventIcon(ev.severity)"
							class="text-base mt-0.5 shrink-0"
							:class="eventColor(ev.severity)"
						/>
						<span class="text-slate-700 flex-1 break-words">{{ ev.message }}</span>
						<time
							class="text-xs text-slate-400 whitespace-nowrap mt-0.5"
							:title="new Date(ev.created_at).toLocaleString()"
						>
							{{ eventTime(ev.created_at) }}
						</time>
					</li>
				</ul>
			</div>

			<!-- metrics -->
			<div class="flex items-center justify-between mb-4">
				<h2 class="font-semibold text-slate-900 text-lg">
					Metrics
				</h2>
				<div class="inline-flex rounded-lg bg-slate-100 p-1">
					<button
						v-for="r in ranges"
						:key="r.value"
						class="px-3 py-1.5 rounded-md text-sm font-medium transition-colors"
						:class="range === r.value ? 'bg-white text-slate-900 shadow-sm' : 'text-slate-500 hover:text-slate-700'"
						@click="range = r.value"
					>
						{{ r.label }}
					</button>
				</div>
			</div>

			<!-- CPU: live + persisted history, from hypervisor diagnostics -->
			<LineChart
				v-if="cpuSeries.length >= 2"
				title="CPU usage"
				:unit="`/ ${totalVcpu} vCPU`"
				color="#8b5cf6"
				:series="cpuSeries"
				:labels="cpuLabels"
				:y-min="0"
				:y-max="totalVcpu"
			/>
			<div
				v-else
				class="bg-white rounded-xl border border-dashed border-slate-300 p-8 flex items-center justify-center text-center text-sm text-slate-500"
			>
				No CPU telemetry yet for this window — a sample is recorded about a minute after
				the instance first boots, and the history is kept afterwards.
			</div>

			<!-- console log (full width, at the end of the page) -->
			<div class="bg-white rounded-xl border border-slate-200/70 shadow-sm overflow-hidden mt-6">
				<div class="flex items-center justify-between px-5 py-3 border-b border-slate-200 bg-slate-50">
					<h2 class="font-semibold text-slate-900 flex items-center gap-2">
						<Icon
							name="solar:document-text-outline"
							class="text-slate-400"
						/>
						Console log
						<span
							v-if="logLines.length"
							class="text-xs font-normal text-slate-400"
						>· {{ logLines.length }} lines</span>
					</h2>
					<button
						class="inline-flex items-center gap-1.5 text-sm text-slate-500 hover:text-slate-800 disabled:opacity-40 transition-colors"
						:disabled="logsLoading || !instance.openstack_id"
						@click="fetchLogs"
					>
						<Icon
							name="solar:refresh-outline"
							class="text-base"
						/>
						{{ logsLoading ? "Refreshing…" : "Refresh" }}
					</button>
				</div>
				<div class="max-h-[480px] overflow-auto">
					<div
						v-if="logLines.length === 0"
						class="px-5 py-12 text-center text-sm text-slate-400"
					>
						{{ logsLoading
							? "Fetching console log…"
							: !instance.openstack_id
								? "The console log appears once the instance is provisioned."
								: "No console output yet." }}
					</div>
					<div
						v-for="(line, idx) in logLines"
						v-else
						:key="idx"
						class="flex gap-4 px-4 py-0.5 font-mono text-xs leading-5 hover:bg-slate-50 border-b border-slate-50"
					>
						<span class="select-none text-slate-300 w-12 shrink-0 text-right tabular-nums">{{ idx + 1 }}</span>
						<span class="text-slate-700 whitespace-pre-wrap break-all flex-1">{{ line }}</span>
					</div>
				</div>
			</div>
		</template>

		<!-- attach floating IP modal -->
		<div
			v-if="attachFipOpen"
			class="fixed inset-0 z-40 bg-slate-900/50 flex items-center justify-center p-4"
		>
			<div class="bg-white rounded-xl shadow-xl w-full max-w-md p-6">
				<h2 class="text-lg font-bold text-slate-900 mb-1">
					Attach a public IP
				</h2>
				<p class="text-sm text-slate-500 mb-5">
					Pick a reserved floating IP to attach to this instance.
				</p>

				<div
					v-if="availableFips.length === 0"
					class="text-sm text-slate-500 mb-5"
				>
					No reserved IPs available.
					<NuxtLink
						to="/floating-ips"
						class="text-slate-700 font-medium hover:underline"
					>
						Allocate one →
					</NuxtLink>
				</div>
				<select
					v-else
					v-model="attachFipId"
					class="w-full rounded-lg border border-slate-300 px-3 py-2.5 bg-white outline-none focus:border-slate-800 mb-5"
				>
					<option
						:value="null"
						disabled
					>
						Select a floating IP
					</option>
					<option
						v-for="fip in availableFips"
						:key="fip.id"
						:value="fip.id"
					>
						{{ fip.ip_address }}
					</option>
				</select>

				<p
					v-if="fipError"
					class="text-red-600 text-sm mb-4"
				>
					{{ fipError }}
				</p>

				<div class="flex justify-end gap-3">
					<button
						class="text-slate-600 hover:text-slate-900 font-medium py-2.5 px-4 rounded-lg transition-colors"
						@click="attachFipOpen = false"
					>
						Cancel
					</button>
					<button
						:disabled="attachFipId === null || fipLoading"
						class="bg-slate-800 hover:bg-slate-700 disabled:opacity-50 text-white font-medium py-2.5 px-5 rounded-lg transition-colors"
						@click="confirmAttachFip"
					>
						{{ fipLoading ? "Attaching…" : "Attach" }}
					</button>
				</div>
			</div>
		</div>

		<!-- noVNC console modal -->
		<div
			v-if="consoleUrl"
			class="fixed inset-0 z-40 bg-slate-900/70 flex items-center justify-center p-4"
		>
			<div class="bg-white rounded-xl shadow-2xl w-full max-w-6xl h-[85vh] flex flex-col overflow-hidden">
				<div class="flex items-center justify-between px-5 py-3 border-b border-slate-100">
					<h2 class="font-semibold text-slate-900 flex items-center gap-2">
						<Icon
							name="solar:monitor-outline"
							class="text-slate-400"
						/>
						Console — {{ instance?.name }}
					</h2>
					<div class="flex items-center gap-5">
						<a
							:href="consoleUrl"
							target="_blank"
							rel="noopener"
							class="text-sm text-slate-500 hover:text-slate-800"
						>
							Open in new tab ↗
						</a>
						<button
							class="text-slate-400 hover:text-slate-700"
							title="Close console"
							@click="consoleUrl = null"
						>
							<Icon
								name="solar:close-circle-outline"
								class="text-2xl"
							/>
						</button>
					</div>
				</div>
				<iframe
					:src="consoleUrl"
					class="flex-1 w-full border-0"
				/>
			</div>
		</div>
	</div>
</template>

<script setup lang="ts">
import { useRoute } from "vue-router";
import type { InstanceDetailResponse, MetricsResponse, MetricPoint, ConsoleResponse, ConsoleLogResponse, InstanceEventResponse, FloatingIPResponse } from "~/types/api";
import { useToastStore } from "~/stores/toast";

const route = useRoute();
const api = useApi();
const { can } = useAuth();
const toast = useToastStore();
const id = route.params.id as string;

const { data: instance, pending, refresh } = await useAsyncData(
	`instance-${id}`,
	() => api<InstanceDetailResponse>(`/instances/${id}`),
);

// floating IPs are managed as separate resources — fetched here so we can offer the
// reserved (available) ones to attach and find this instance's IP id to detach
const { data: floatingIps, refresh: refreshFloatingIps } = await useAsyncData(
	`instance-fips-${id}`,
	() => api<FloatingIPResponse[]>("/floating-ips/"),
);
const availableFips = computed(() =>
	(floatingIps.value ?? []).filter(f => f.status === "available" && f.instance_id === null),
);
const attachedFip = computed(() =>
	(floatingIps.value ?? []).find(f => f.instance_id === Number(id)) ?? null,
);

// the instance's own event log — lifecycle, errors and warnings, newest first
const { data: events, refresh: refreshEvents } = await useAsyncData(
	`instance-events-${id}`,
	() => api<InstanceEventResponse[]>(`/instances/${id}/events?limit=50`),
);

function eventIcon(severity: string): string {
	if (severity === "error") return "solar:close-circle-outline";
	if (severity === "warning") return "solar:danger-triangle-outline";
	return "solar:info-circle-outline";
}

function eventColor(severity: string): string {
	if (severity === "error") return "text-rose-500";
	if (severity === "warning") return "text-amber-500";
	return "text-sky-500";
}

function eventTime(iso: string): string {
	const secs = Math.round((Date.now() - new Date(iso).getTime()) / 1000);
	if (secs < 45) return "just now";
	const mins = Math.round(secs / 60);
	if (mins < 60) return `${mins} min ago`;
	const hours = Math.round(mins / 60);
	if (hours < 24) return `${hours}h ago`;
	return new Date(iso).toLocaleString([], { month: "short", day: "numeric", hour: "2-digit", minute: "2-digit" });
}

const metrics = ref<MetricPoint[]>([]);

// CPU metric look-back window
const ranges = [
	{ label: "30m", value: "-30m" },
	{ label: "1h", value: "-1h" },
	{ label: "24h", value: "-24h" },
	{ label: "30d", value: "-30d" },
];
const range = ref("-1h");

async function loadMetrics() {
	// load whenever the instance has been provisioned — the telemetry persists in
	// InfluxDB, so the CPU history stays visible even after a stop/reboot (not just
	// while ACTIVE)
	const osId = instance.value?.openstack_id;
	if (!osId) return;
	try {
		const res = await api<MetricsResponse>(`/instances/${osId}/metrics?time_range=${range.value}`);
		metrics.value = res.data;
	}
	catch {
		// telemetry endpoint may transiently fail — keep last good data
	}
}

// re-fetch immediately when the user switches the range
watch(range, () => loadMetrics());

// vCPUs / RAM / root disk come from the backend (flavor specs in core/flavors.py),
// so the detail page shows accurate specs without the frontend guessing.
const totalVcpu = computed(() => instance.value?.vcpus ?? 1);

const ramDisplay = computed(() => {
	const mb = instance.value?.ram_mb ?? 0;
	if (!mb) return "—";
	return mb % 1024 === 0 ? `${mb / 1024} GB` : `${mb} MB`;
});

// storage = the flavor's root disk + any attached block-storage volumes
const volumesGb = computed(() =>
	(instance.value?.volumes ?? []).reduce((sum, v) => sum + (v.size_gb ?? 0), 0),
);
const totalStorageGb = computed(() => (instance.value?.disk_gb ?? 0) + volumesGb.value);
const storageBreakdown = computed(() => {
	const root = instance.value?.disk_gb ?? 0;
	const vols = volumesGb.value;
	return vols > 0 ? `${root} GB root · ${vols} GB volumes` : `${root} GB root disk`;
});

const cpuSeries = computed(() => {
	const pts = metrics.value;
	const out: number[] = [];
	for (let i = 1; i < pts.length; i++) {
		const cur = pts[i];
		const prev = pts[i - 1];
		if (!cur || !prev) continue;
		const dtNs = (new Date(cur.timestamp).getTime() - new Date(prev.timestamp).getTime()) * 1e6;
		const dCpuNs = cur.cpu_time >= prev.cpu_time
			? cur.cpu_time - prev.cpu_time
			: cur.cpu_time;
		if (dtNs <= 0) {
			out.push(0);
			continue;
		}
		const used = dCpuNs / dtNs;
		out.push(Math.max(0, Math.min(totalVcpu.value, Math.round(used * 10) / 10)));
	}
	return out;
});

// timestamps aligned to cpuSeries
const cpuLabels = computed(() => {
	const pts = metrics.value;
	const out: string[] = [];
	for (let i = 1; i < pts.length; i++) {
		const cur = pts[i];
		if (!cur) continue;
		out.push(new Date(cur.timestamp).toLocaleString([], {
			month: "short", day: "numeric", hour: "2-digit", minute: "2-digit",
		}));
	}
	return out;
});

function sshUser(image: string): string {
	const i = image.toLowerCase();
	if (i.includes("ubuntu")) return "ubuntu";
	if (i.includes("debian")) return "debian";
	if (i.includes("cirros")) return "cirros";
	if (i.includes("centos") || i.includes("rocky") || i.includes("alma")) return "cloud-user";
	return "root";
}

const sshCommand = computed(() => {
	const ip = instance.value?.floating_ip?.ip_address;
	const key = instance.value?.keypair?.name;
	if (!ip || !key) return "";
	return `ssh -i ~/.ssh/${key} ${sshUser(instance.value!.image_name)}@${ip}`;
});

async function remove() {
	if (!instance.value) return;
	if (!confirm(`Delete instance "${instance.value.name}"? This cannot be undone.`)) return;
	try {
		await api(`/instances/${id}`, { method: "DELETE" });
		toast.success(`Deleting "${instance.value.name}"…`);
		await navigateTo("/");
	}
	catch (e: unknown) {
		const err = e as { data?: { detail?: string } };
		toast.error(err.data?.detail ?? "Failed to delete instance");
	}
}

const actionError = ref("");
const powerLoading = ref(false);
const consoleUrl = ref<string | null>(null);
const consoleLoading = ref(false);
const snapshotLoading = ref(false);

async function snapshot() {
	const name = prompt("Snapshot name (max 40 chars):", `${instance.value?.name}-snapshot`);
	if (!name) return;
	actionError.value = "";
	snapshotLoading.value = true;
	try {
		await api(`/instances/${id}/snapshot`, { method: "POST", body: { name: name.trim().slice(0, 40) } });
		toast.success("Snapshot started — track it on Images.");
		await navigateTo("/images"); // watch it go snapshotting → active there
	}
	catch (e: unknown) {
		const err = e as { data?: { detail?: string } };
		actionError.value = err.data?.detail ?? "Could not start snapshot";
		toast.error(actionError.value);
	}
	finally {
		snapshotLoading.value = false;
	}
}

async function powerAction(action: "stop" | "start" | "reboot") {
	actionError.value = "";
	powerLoading.value = true;
	try {
		await api(`/instances/${id}/${action}`, { method: "POST" });
		await refresh(); // reflect STOPPING/STARTING immediately
		toast.success(`${action === "stop" ? "Stopping" : action === "start" ? "Starting" : "Restarting"} the instance…`);
	}
	catch (e: unknown) {
		const err = e as { data?: { detail?: string } };
		actionError.value = err.data?.detail ?? `Could not ${action} the instance`;
		toast.error(actionError.value);
	}
	finally {
		powerLoading.value = false;
	}
}

async function openConsole() {
	actionError.value = "";
	consoleLoading.value = true;
	try {
		const res = await api<ConsoleResponse>(`/instances/${id}/console`);
		consoleUrl.value = res.console_url;
	}
	catch (e: unknown) {
		const err = e as { data?: { detail?: string } };
		actionError.value = err.data?.detail ?? "Could not open console";
	}
	finally {
		consoleLoading.value = false;
	}
}

const logsOutput = ref("");
const logsLoading = ref(false);
const logLines = computed(() =>
	logsOutput.value ? logsOutput.value.replace(/\n+$/, "").split("\n") : [],
);

async function fetchLogs() {
	if (!instance.value?.openstack_id) return;
	logsLoading.value = true;
	try {
		const res = await api<ConsoleLogResponse>(`/instances/${id}/logs?lines=500`);
		logsOutput.value = res.output || "";
	}
	catch (e: unknown) {
		const err = e as { data?: { detail?: string } };
		toast.error(err.data?.detail ?? "Could not fetch logs");
	}
	finally {
		logsLoading.value = false;
	}
}

const attachFipOpen = ref(false);
const attachFipId = ref<number | null>(null);
const fipError = ref("");
const fipLoading = ref(false);

function openAttachFip() {
	attachFipId.value = null;
	fipError.value = "";
	attachFipOpen.value = true;
}

async function confirmAttachFip() {
	if (attachFipId.value === null) return;
	fipError.value = "";
	fipLoading.value = true;
	try {
		await api(`/floating-ips/${attachFipId.value}/associate`, {
			method: "POST",
			body: { instance_id: Number(id) },
		});
		attachFipOpen.value = false;
		toast.success("Attaching public IP…");
		await Promise.all([refresh(), refreshFloatingIps()]);
	}
	catch (e: unknown) {
		const err = e as { data?: { detail?: string } };
		fipError.value = err.data?.detail ?? "Could not attach the floating IP";
		toast.error(fipError.value);
	}
	finally {
		fipLoading.value = false;
	}
}

async function detachFip() {
	const fip = attachedFip.value;
	if (!fip) return;
	if (!confirm(`Detach ${fip.ip_address} from this instance?`)) return;
	fipError.value = "";
	fipLoading.value = true;
	try {
		await api(`/floating-ips/${fip.id}/disassociate`, { method: "POST" });
		toast.success(`Detaching ${fip.ip_address}…`);
		await Promise.all([refresh(), refreshFloatingIps()]);
	}
	catch (e: unknown) {
		const err = e as { data?: { detail?: string } };
		actionError.value = err.data?.detail ?? "Could not detach the floating IP";
		toast.error(actionError.value);
	}
	finally {
		fipLoading.value = false;
	}
}

async function tick() {
	// keep the instance fresh so status (ACTIVE / SHUTOFF / ERROR) and the public
	// IP stay current. The page no longer blanks on refresh, so this doesn't flicker.
	try {
		await refresh();
	}
	catch {
		// a 404 means the instance is gone — bounce back to the dashboard
		await navigateTo("/");
		return;
	}
	await refreshFloatingIps();
	await refreshEvents();
	await loadMetrics();
}

await loadMetrics();

let poll: ReturnType<typeof setInterval> | undefined;
onMounted(() => {
	fetchLogs(); // populate the console-log panel once on load (manual Refresh after)
	poll = setInterval(tick, 10000);
});
onUnmounted(() => clearInterval(poll));
</script>
