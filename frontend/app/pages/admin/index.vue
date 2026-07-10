<template>
	<div>
		<div class="mb-7">
			<h1 class="text-2xl font-bold text-slate-900">
				Platform Overview
			</h1>
			<p class="text-sm text-slate-500 mt-1">
				The real OpenStack cluster's capacity and everything the platform has provisioned
				across all organizations.
			</p>
		</div>

		<!-- cluster capacity (live from nova/cinder) -->
		<div class="flex items-center justify-between mb-3">
			<h2 class="font-semibold text-slate-900">
				Cluster capacity
			</h2>
			<button
				class="inline-flex items-center gap-1.5 text-sm text-slate-500 hover:text-slate-900 font-medium transition-colors disabled:opacity-50"
				:disabled="refreshing"
				@click="refreshStats"
			>
				<Icon
					name="solar:refresh-outline"
					class="text-base"
					:class="refreshing ? 'animate-spin' : ''"
				/>
				{{ refreshing ? "Refreshing…" : "Refresh from OpenStack" }}
			</button>
		</div>
		<div
			v-if="!data?.capacity"
			class="bg-white rounded-xl border border-dashed border-slate-300 p-8 text-center text-sm text-slate-500 mb-8"
		>
			No cluster snapshot yet. Click <span class="font-medium">Refresh from OpenStack</span> (the
			Celery worker must be running), or wait for the 60&nbsp;s collector beat.
		</div>
		<template v-else>
			<!-- total (max) capacity reported by OpenStack -->
			<div class="grid grid-cols-2 lg:grid-cols-4 gap-5 mb-5">
				<div class="bg-white rounded-xl border border-slate-200/70 shadow-sm p-5">
					<p class="text-sm text-slate-500 mb-1">
						Total vCPUs
					</p>
					<p class="text-2xl font-bold text-slate-900 tabular-nums">
						{{ data.capacity.vcpus_total }}
					</p>
					<p class="text-xs text-slate-400 mt-1">
						{{ data.capacity.vcpus_used }} used · {{ data.capacity.vcpus_total - data.capacity.vcpus_used }} free
					</p>
				</div>
				<div class="bg-white rounded-xl border border-slate-200/70 shadow-sm p-5">
					<p class="text-sm text-slate-500 mb-1">
						Total RAM
					</p>
					<p class="text-2xl font-bold text-slate-900 tabular-nums">
						{{ data.capacity.ram_gb_total.toFixed(1) }} GB
					</p>
					<p class="text-xs text-slate-400 mt-1">
						{{ data.capacity.ram_gb_used.toFixed(1) }} used · {{ (data.capacity.ram_gb_total - data.capacity.ram_gb_used).toFixed(1) }} free
					</p>
				</div>
				<div class="bg-white rounded-xl border border-slate-200/70 shadow-sm p-5">
					<p class="text-sm text-slate-500 mb-1">
						Total disk (compute)
					</p>
					<p class="text-2xl font-bold text-slate-900 tabular-nums">
						{{ data.capacity.disk_gb_total }} GB
					</p>
					<p class="text-xs text-slate-400 mt-1">
						{{ data.capacity.disk_gb_used }} used · {{ data.capacity.disk_gb_total - data.capacity.disk_gb_used }} free
					</p>
				</div>
				<div class="bg-white rounded-xl border border-slate-200/70 shadow-sm p-5">
					<p class="text-sm text-slate-500 mb-1">
						Total block storage
					</p>
					<p class="text-2xl font-bold text-slate-900 tabular-nums">
						{{ data.capacity.storage_gb_total !== null ? `${data.capacity.storage_gb_total} GB` : "—" }}
					</p>
					<p
						v-if="data.capacity.storage_gb_total !== null"
						class="text-xs text-slate-400 mt-1"
					>
						{{ data.capacity.storage_gb_used ?? 0 }} used · {{ data.capacity.storage_gb_total - (data.capacity.storage_gb_used ?? 0) }} free
					</p>
				</div>
			</div>

			<!-- utilization bars -->
			<div class="grid grid-cols-1 lg:grid-cols-2 gap-5 mb-3">
				<UsageBar
					label="vCPUs"
					:used="data.capacity.vcpus_used"
					:total="data.capacity.vcpus_total"
					unit="vCPU"
				/>
				<UsageBar
					label="Memory"
					:used="data.capacity.ram_gb_used"
					:total="data.capacity.ram_gb_total"
					unit="GB"
				/>
				<UsageBar
					label="Local disk (compute)"
					:used="data.capacity.disk_gb_used"
					:total="data.capacity.disk_gb_total"
					unit="GB"
				/>
				<UsageBar
					v-if="data.capacity.storage_gb_total !== null"
					label="Block storage (Cinder)"
					:used="data.capacity.storage_gb_used ?? 0"
					:total="data.capacity.storage_gb_total"
					unit="GB"
				/>
			</div>
			<p class="text-xs text-slate-400 mb-8">
				{{ data.capacity.hypervisor_count }} hypervisor(s) · {{ data.capacity.running_vms }} running VMs ·
				snapshot {{ new Date(data.capacity.updated_at).toLocaleString() }}
			</p>
		</template>

		<!-- platform totals (DB-derived, across all orgs) -->
		<h2 class="font-semibold text-slate-900 mb-3">
			Platform totals
		</h2>
		<div class="grid grid-cols-2 lg:grid-cols-4 gap-5 mb-5">
			<StatCard
				label="Organizations"
				:value="data?.totals.organizations ?? 0"
				icon="solar:buildings-2-outline"
				icon-bg="bg-indigo-100"
				icon-color="text-indigo-600"
			/>
			<StatCard
				label="Users"
				:value="data?.totals.users ?? 0"
				icon="solar:users-group-rounded-outline"
				icon-bg="bg-sky-100"
				icon-color="text-sky-600"
			/>
			<StatCard
				label="Instances"
				:value="data?.totals.instances ?? 0"
				icon="solar:server-square-outline"
				icon-bg="bg-emerald-100"
				icon-color="text-emerald-600"
			/>
			<StatCard
				label="Volumes"
				:value="data?.totals.volumes ?? 0"
				icon="solar:database-outline"
				icon-bg="bg-amber-100"
				icon-color="text-amber-600"
			/>
		</div>
		<div class="grid grid-cols-2 lg:grid-cols-4 gap-5">
			<div class="bg-white rounded-xl border border-slate-200/70 shadow-sm p-5">
				<p class="text-sm text-slate-500 mb-1">
					Running instances
				</p>
				<p class="text-2xl font-bold text-slate-900 tabular-nums">
					{{ data?.totals.running_instances ?? 0 }}
				</p>
			</div>
			<div class="bg-white rounded-xl border border-slate-200/70 shadow-sm p-5">
				<p class="text-sm text-slate-500 mb-1">
					vCPUs allocated
				</p>
				<p class="text-2xl font-bold text-slate-900 tabular-nums">
					{{ data?.totals.vcpus_allocated ?? 0 }}
				</p>
			</div>
			<div class="bg-white rounded-xl border border-slate-200/70 shadow-sm p-5">
				<p class="text-sm text-slate-500 mb-1">
					RAM allocated
				</p>
				<p class="text-2xl font-bold text-slate-900 tabular-nums">
					{{ (data?.totals.ram_gb_allocated ?? 0).toFixed(1) }} GB
				</p>
			</div>
			<div class="bg-white rounded-xl border border-slate-200/70 shadow-sm p-5">
				<p class="text-sm text-slate-500 mb-1">
					Storage provisioned
				</p>
				<p class="text-2xl font-bold text-slate-900 tabular-nums">
					{{ data?.totals.storage_gb ?? 0 }} GB
				</p>
			</div>
		</div>

		<p class="text-xs text-slate-400 mt-5">
			Cluster capacity is the actual cloud maximum — nova hypervisor totals + Cinder pool capacity,
			collected by a Celery task. "Total" is the hardware ceiling; "used"/"free" is what the whole
			cluster currently consumes. Platform totals below are what this platform provisioned —
			allocated vCPU/RAM are flavor-reserved amounts of ACTIVE instances, not measured in-guest usage.
		</p>
	</div>
</template>

<script setup lang="ts">
import type { AdminOverview } from "~/types/api";
import { useToastStore } from "~/stores/toast";

definePageMeta({ layout: "admin", middleware: "admin" });

const api = useApi();
const toast = useToastStore();
const { data, refresh } = await useAsyncData(
	"admin-overview",
	() => api<AdminOverview>("/admin/overview"),
);

// trigger the collector on demand so the admin doesn't wait for the 60s beat
const refreshing = ref(false);
async function refreshStats() {
	refreshing.value = true;
	try {
		await api("/admin/cloud-stats/refresh", { method: "POST" });
		toast.success("Pulling live capacity from OpenStack…");
		// the collector runs in Celery — give it a few seconds, then re-read
		await new Promise(r => setTimeout(r, 4000));
		await refresh();
	}
	catch (e: unknown) {
		const err = e as { data?: { detail?: string } };
		toast.error(err.data?.detail ?? "Could not refresh cluster stats");
	}
	finally {
		refreshing.value = false;
	}
}

let poll: ReturnType<typeof setInterval> | undefined;
onMounted(() => {
	poll = setInterval(refresh, 60000);
});
onUnmounted(() => clearInterval(poll));
</script>
