<template>
	<div>
		<div class="mb-7">
			<h1 class="text-2xl font-bold text-slate-900">
				Organizations
			</h1>
			<p class="text-sm text-slate-500 mt-1">
				Every tenant on the platform and the resources it has allocated.
			</p>
		</div>

		<div class="bg-white rounded-xl shadow-sm border border-slate-200/70 overflow-hidden">
			<table class="w-full text-left">
				<thead class="bg-slate-50 text-slate-500 text-xs uppercase tracking-wider">
					<tr>
						<th class="py-3 px-5 font-semibold">
							Organization
						</th>
						<th class="py-3 px-5 font-semibold">
							Status
						</th>
						<th class="py-3 px-5 font-semibold text-right">
							Users
						</th>
						<th class="py-3 px-5 font-semibold text-right">
							Instances
						</th>
						<th class="py-3 px-5 font-semibold text-right">
							Running
						</th>
						<th class="py-3 px-5 font-semibold text-right">
							vCPUs
						</th>
						<th class="py-3 px-5 font-semibold text-right">
							RAM
						</th>
						<th class="py-3 px-5 font-semibold text-right">
							Storage
						</th>
						<th class="py-3 px-5 font-semibold">
							Created
						</th>
						<th class="py-3 px-5" />
					</tr>
				</thead>
				<tbody class="divide-y divide-slate-100">
					<tr
						v-for="org in orgs ?? []"
						:key="org.id"
					>
						<td class="py-3.5 px-5 font-medium text-slate-900">
							{{ org.name }}
						</td>
						<td class="py-3.5 px-5">
							<span
								v-if="org.suspended"
								class="inline-flex rounded-full px-2.5 py-1 text-xs font-semibold bg-amber-100 text-amber-700"
							>Suspended</span>
							<span
								v-else
								class="inline-flex rounded-full px-2.5 py-1 text-xs font-semibold bg-emerald-100 text-emerald-700"
							>Active</span>
						</td>
						<td class="py-3.5 px-5 text-right text-slate-600 tabular-nums">
							{{ org.users }}
						</td>
						<td class="py-3.5 px-5 text-right text-slate-600 tabular-nums">
							{{ org.instances }}
						</td>
						<td class="py-3.5 px-5 text-right text-slate-600 tabular-nums">
							{{ org.running_instances }}
						</td>
						<td class="py-3.5 px-5 text-right text-slate-600 tabular-nums">
							{{ org.vcpus_allocated }}
						</td>
						<td class="py-3.5 px-5 text-right text-slate-600 tabular-nums">
							{{ org.ram_gb_allocated.toFixed(1) }} GB
						</td>
						<td class="py-3.5 px-5 text-right text-slate-600 tabular-nums">
							{{ org.storage_gb }} GB
						</td>
						<td class="py-3.5 px-5 text-slate-500 text-sm">
							{{ new Date(org.created_at).toLocaleDateString() }}
						</td>
						<td class="py-3.5 px-5 text-right whitespace-nowrap">
							<button
								class="text-sm font-medium text-slate-500 hover:text-indigo-600 transition-colors mr-4"
								@click="openQuota(org)"
							>
								Quota
							</button>
							<template v-if="org.id !== selfOrgId">
								<button
									class="text-sm font-medium mr-4 transition-colors"
									:class="org.suspended ? 'text-slate-500 hover:text-emerald-600' : 'text-slate-500 hover:text-amber-600'"
									@click="setActive(org, org.suspended)"
								>
									{{ org.suspended ? "Activate" : "Suspend" }}
								</button>
								<button
									class="text-sm font-medium text-slate-400 hover:text-red-600 transition-colors"
									@click="remove(org)"
								>
									Delete
								</button>
							</template>
							<span
								v-else
								class="text-xs text-slate-300"
							>yours</span>
						</td>
					</tr>
					<tr v-if="(orgs?.length ?? 0) === 0">
						<td
							colspan="10"
							class="py-6 px-5 text-center text-sm text-slate-400"
						>
							No organizations yet.
						</td>
					</tr>
				</tbody>
			</table>
		</div>

		<!-- quota editor modal -->
		<div
			v-if="quotaTarget"
			class="fixed inset-0 z-30 bg-slate-900/50 flex items-center justify-center p-4"
		>
			<div class="bg-white rounded-xl shadow-xl w-full max-w-lg p-6">
				<h2 class="text-lg font-bold text-slate-900 mb-1">
					Quota — {{ quotaTarget.name }}
				</h2>
				<p class="text-sm text-slate-500 mb-5">
					Maximum resources this organization can provision.
					<span v-if="quotaIsDefault">Currently on the platform defaults.</span>
				</p>

				<div
					v-if="quotaLoading"
					class="text-sm text-slate-400 py-6 text-center"
				>
					Loading…
				</div>
				<div
					v-else
					class="grid grid-cols-2 gap-4 mb-6"
				>
					<div
						v-for="f in quotaFields"
						:key="f.key"
						class="flex flex-col gap-1.5"
					>
						<label class="text-sm font-medium text-slate-700">{{ f.label }}</label>
						<input
							v-model.number="quotaForm[f.key]"
							type="number"
							min="0"
							class="w-full rounded-lg border border-slate-300 px-3 py-2 outline-none focus:border-slate-800 focus:ring-2 focus:ring-slate-800/10 transition"
						>
						<span class="text-xs text-slate-400">using {{ quotaUsage?.[f.usageKey] ?? 0 }}</span>
					</div>
				</div>

				<div class="flex justify-end gap-3">
					<button
						class="text-slate-600 hover:text-slate-900 font-medium py-2.5 px-4 rounded-lg transition-colors"
						@click="quotaTarget = null"
					>
						Cancel
					</button>
					<button
						:disabled="quotaSaving || quotaLoading"
						class="bg-slate-800 hover:bg-slate-700 disabled:opacity-50 text-white font-medium py-2.5 px-5 rounded-lg transition-colors"
						@click="saveQuota"
					>
						{{ quotaSaving ? "Saving…" : "Save quota" }}
					</button>
				</div>
			</div>
		</div>
	</div>
</template>

<script setup lang="ts">
import type { OrgUsageRow, QuotaResponse, QuotaLimits, QuotaUsage } from "~/types/api";
import { useToastStore } from "~/stores/toast";

definePageMeta({ layout: "admin", middleware: "admin" });

const api = useApi();
const toast = useToastStore();
const { user } = useAuth();
const selfOrgId = computed(() => user.value?.organization_id);

const { data: orgs, refresh } = await useAsyncData(
	"admin-organizations",
	() => api<OrgUsageRow[]>("/admin/organizations"),
);

async function setActive(org: OrgUsageRow, makeActive: boolean) {
	if (!makeActive && !confirm(`Suspend "${org.name}"? This disables every member's login and stops all of its instances.`)) return;
	try {
		await api(`/admin/organizations/${org.id}/active`, { method: "POST", body: { is_active: makeActive } });
		toast.success(`${makeActive ? "Activated" : "Suspended"} "${org.name}".`);
		await refresh();
	}
	catch (e: unknown) {
		const err = e as { data?: { detail?: string } };
		toast.error(err.data?.detail ?? "Could not change the organization");
	}
}

async function remove(org: OrgUsageRow) {
	const typed = prompt(
		`This permanently deletes "${org.name}" and tears down ALL its OpenStack resources `
		+ `(instances, volumes, floating IPs, networks, images, keys). This cannot be undone.\n\n`
		+ `Type the organization name to confirm:`,
	);
	if (typed === null) return;
	if (typed.trim() !== org.name) {
		toast.error("Name did not match — deletion cancelled.");
		return;
	}
	try {
		await api(`/admin/organizations/${org.id}`, { method: "DELETE" });
		toast.success(`Tearing down "${org.name}"…`);
		await refresh();
	}
	catch (e: unknown) {
		const err = e as { data?: { detail?: string } };
		toast.error(err.data?.detail ?? "Could not delete the organization");
	}
}

// ── quota editor ──────────────────────────────────────────────────────────────
const quotaFields: { key: keyof QuotaLimits; label: string; usageKey: keyof QuotaUsage }[] = [
	{ key: "max_instances", label: "Instances", usageKey: "instances" },
	{ key: "max_vcpus", label: "vCPUs", usageKey: "vcpus" },
	{ key: "max_ram_gb", label: "RAM (GB)", usageKey: "ram_gb" },
	{ key: "max_volumes", label: "Volumes", usageKey: "volumes" },
	{ key: "max_storage_gb", label: "Storage (GB)", usageKey: "storage_gb" },
	{ key: "max_floating_ips", label: "Floating IPs", usageKey: "floating_ips" },
];

function emptyLimits(): QuotaLimits {
	return { max_instances: 0, max_vcpus: 0, max_ram_gb: 0, max_volumes: 0, max_storage_gb: 0, max_floating_ips: 0 };
}

const quotaTarget = ref<OrgUsageRow | null>(null);
const quotaForm = ref<QuotaLimits>(emptyLimits());
const quotaUsage = ref<QuotaUsage | null>(null);
const quotaIsDefault = ref(false);
const quotaLoading = ref(false);
const quotaSaving = ref(false);

async function openQuota(org: OrgUsageRow) {
	quotaTarget.value = org;
	quotaUsage.value = null;
	quotaLoading.value = true;
	try {
		const q = await api<QuotaResponse>(`/admin/organizations/${org.id}/quota`);
		quotaForm.value = { ...q.limits };
		quotaUsage.value = q.usage;
		quotaIsDefault.value = q.is_default;
	}
	catch {
		toast.error("Could not load the quota.");
		quotaTarget.value = null;
	}
	finally {
		quotaLoading.value = false;
	}
}

async function saveQuota() {
	if (!quotaTarget.value) return;
	quotaSaving.value = true;
	try {
		await api(`/admin/organizations/${quotaTarget.value.id}/quota`, { method: "PUT", body: quotaForm.value });
		toast.success(`Quota updated for "${quotaTarget.value.name}".`);
		quotaTarget.value = null;
		await refresh();
	}
	catch (e: unknown) {
		const err = e as { data?: { detail?: string } };
		toast.error(err.data?.detail ?? "Could not save the quota");
	}
	finally {
		quotaSaving.value = false;
	}
}

// poll so a suspended badge / a finished teardown (row disappears) shows up
let poll: ReturnType<typeof setInterval> | undefined;
onMounted(() => {
	poll = setInterval(refresh, 5000);
});
onUnmounted(() => clearInterval(poll));
</script>
