<template>
	<div>
		<div class="mb-7">
			<h1 class="text-2xl font-bold text-slate-900">
				Usage
			</h1>
			<p class="text-sm text-slate-500 mt-1">
				Per-instance uptime (metered) and the resources your running instances currently have
				allocated by their flavor.
			</p>
		</div>

		<!-- quota: current usage vs the org's limits -->
		<div class="flex items-center gap-2 mb-3">
			<h2 class="font-semibold text-slate-900">
				Quota
			</h2>
			<span
				v-if="quota?.is_default"
				class="text-xs text-slate-400"
			>(platform defaults)</span>
		</div>
		<div class="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-5 mb-8">
			<UsageBar
				label="Instances"
				:used="quota?.usage.instances ?? 0"
				:total="quota?.limits.max_instances ?? 0"
				unit=""
			/>
			<UsageBar
				label="vCPUs"
				:used="quota?.usage.vcpus ?? 0"
				:total="quota?.limits.max_vcpus ?? 0"
				unit="vCPU"
			/>
			<UsageBar
				label="RAM"
				:used="quota?.usage.ram_gb ?? 0"
				:total="quota?.limits.max_ram_gb ?? 0"
				unit="GB"
			/>
			<UsageBar
				label="Volumes"
				:used="quota?.usage.volumes ?? 0"
				:total="quota?.limits.max_volumes ?? 0"
				unit=""
			/>
			<UsageBar
				label="Storage"
				:used="quota?.usage.storage_gb ?? 0"
				:total="quota?.limits.max_storage_gb ?? 0"
				unit="GB"
			/>
			<UsageBar
				label="Floating IPs"
				:used="quota?.usage.floating_ips ?? 0"
				:total="quota?.limits.max_floating_ips ?? 0"
				unit=""
			/>
		</div>

		<!-- live footprint cards -->
		<div class="grid grid-cols-2 lg:grid-cols-4 gap-5 mb-8">
			<div class="bg-white rounded-xl border border-slate-200/70 shadow-sm p-5">
				<p class="text-sm text-slate-500 mb-1">
					Running instances
				</p>
				<p class="text-2xl font-bold text-slate-900 tabular-nums">
					{{ usage?.running_instances ?? 0 }}
				</p>
			</div>
			<div class="bg-white rounded-xl border border-slate-200/70 shadow-sm p-5">
				<p class="text-sm text-slate-500 mb-1">
					vCPUs allocated
				</p>
				<p class="text-2xl font-bold text-slate-900 tabular-nums">
					{{ usage?.vcpus_allocated ?? 0 }}
				</p>
			</div>
			<div class="bg-white rounded-xl border border-slate-200/70 shadow-sm p-5">
				<p class="text-sm text-slate-500 mb-1">
					RAM allocated
				</p>
				<p class="text-2xl font-bold text-slate-900 tabular-nums">
					{{ (usage?.ram_gb_allocated ?? 0).toFixed(1) }} GB
				</p>
			</div>
			<div class="bg-white rounded-xl border border-slate-200/70 shadow-sm p-5">
				<p class="text-sm text-slate-500 mb-1">
					Storage allocated
				</p>
				<p class="text-2xl font-bold text-slate-900 tabular-nums">
					{{ usage?.storage_gb ?? 0 }} GB
				</p>
			</div>
		</div>

		<!-- instances -->
		<h2 class="font-semibold text-slate-900 mb-3">
			Compute (instance-hours)
		</h2>
		<div class="bg-white rounded-xl shadow-sm border border-slate-200/70 overflow-hidden mb-8">
			<table class="w-full text-left">
				<thead class="bg-slate-50 text-slate-500 text-xs uppercase tracking-wider">
					<tr>
						<th class="py-3 px-5 font-semibold">
							Instance
						</th>
						<th class="py-3 px-5 font-semibold">
							Flavor
						</th>
						<th class="py-3 px-5 font-semibold">
							Status
						</th>
						<th class="py-3 px-5 font-semibold text-right">
							Hours run
						</th>
					</tr>
				</thead>
				<tbody class="divide-y divide-slate-100">
					<tr
						v-for="row in usage?.instances ?? []"
						:key="row.id"
					>
						<td class="py-3 px-5 font-medium text-slate-900">
							{{ row.name }}
						</td>
						<td class="py-3 px-5 text-slate-600">
							{{ row.flavor_name }}
						</td>
						<td class="py-3 px-5">
							<StatusBadge :status="row.status" />
						</td>
						<td class="py-3 px-5 text-slate-900 font-medium text-right tabular-nums">
							{{ row.hours.toFixed(2) }}
						</td>
					</tr>
					<tr v-if="(usage?.instances?.length ?? 0) === 0">
						<td
							colspan="4"
							class="py-6 px-5 text-center text-sm text-slate-400"
						>
							No instances yet.
						</td>
					</tr>
				</tbody>
			</table>
		</div>

		<!-- volumes -->
		<h2 class="font-semibold text-slate-900 mb-3">
			Storage (volumes)
		</h2>
		<div class="bg-white rounded-xl shadow-sm border border-slate-200/70 overflow-hidden">
			<table class="w-full text-left">
				<thead class="bg-slate-50 text-slate-500 text-xs uppercase tracking-wider">
					<tr>
						<th class="py-3 px-5 font-semibold">
							Volume
						</th>
						<th class="py-3 px-5 font-semibold text-right">
							Size
						</th>
					</tr>
				</thead>
				<tbody class="divide-y divide-slate-100">
					<tr
						v-for="row in usage?.volumes ?? []"
						:key="row.id"
					>
						<td class="py-3 px-5 font-medium text-slate-900">
							{{ row.name }}
						</td>
						<td class="py-3 px-5 text-slate-600 text-right tabular-nums">
							{{ row.size_gb }} GB
						</td>
					</tr>
					<tr v-if="(usage?.volumes?.length ?? 0) === 0">
						<td
							colspan="2"
							class="py-6 px-5 text-center text-sm text-slate-400"
						>
							No volumes yet.
						</td>
					</tr>
				</tbody>
			</table>
		</div>

		<p class="text-xs text-slate-400 mt-4">
			vCPU and RAM are the amounts <span class="font-medium">allocated</span> by each running
			instance's flavor — not measured in-guest consumption (the hypervisor doesn't expose live
			guest RAM). Per-instance hours are metered every 60 s and update live.
		</p>
	</div>
</template>

<script setup lang="ts">
import type { UsageResponse, QuotaResponse } from "~/types/api";

const api = useApi();

const { data: usage, refresh } = await useAsyncData(
	"usage",
	() => api<UsageResponse>("/usage/"),
);
const { data: quota, refresh: refreshQuota } = await useAsyncData(
	"quota",
	() => api<QuotaResponse>("/quota/"),
);

// poll so metered hours + quota usage tick up live as resources change
let poll: ReturnType<typeof setInterval> | undefined;
onMounted(() => {
	poll = setInterval(() => {
		refresh();
		refreshQuota();
	}, 60000);
});
onUnmounted(() => clearInterval(poll));
</script>
