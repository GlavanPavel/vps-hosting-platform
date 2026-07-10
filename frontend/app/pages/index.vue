<template>
	<div>
		<div class="flex items-center justify-between mb-7">
			<div>
				<h1 class="text-2xl font-bold text-slate-900">
					Dashboard
				</h1>
				<p class="text-sm text-slate-500 mt-1">
					Overview of your cloud infrastructure
				</p>
			</div>
			<NuxtLink
				to="/create"
				class="inline-flex items-center gap-2 bg-yellow-400 hover:bg-yellow-300 text-slate-900 font-semibold py-2.5 px-5 rounded-lg transition-colors shadow-sm active:scale-[0.98]"
			>
				<Icon
					name="solar:add-square-outline"
					class="text-lg"
				/>
				New Instance
			</NuxtLink>
		</div>

		<div class="grid grid-cols-3 gap-5 mb-8">
			<StatCard
				label="Instances"
				:value="instances?.length ?? 0"
				icon="solar:server-square-outline"
				icon-bg="bg-slate-100"
				icon-color="text-slate-700"
			/>
			<StatCard
				label="Running"
				:value="activeCount"
				icon="solar:play-circle-outline"
				icon-bg="bg-green-100"
				icon-color="text-green-600"
			/>
			<StatCard
				label="Floating IPs"
				:value="floatingIps?.length ?? 0"
				icon="solar:global-outline"
				icon-bg="bg-blue-100"
				icon-color="text-blue-600"
			/>
		</div>

		<h2 class="font-semibold text-slate-900 mb-4 text-lg">
			Instances
		</h2>

		<EmptyState
			v-if="!instances || instances.length === 0"
			icon="solar:server-square-outline"
			title="No instances yet"
			description="Spin up your first virtual machine to get started."
		>
			<NuxtLink
				to="/create"
				class="inline-flex items-center gap-2 bg-yellow-400 hover:bg-yellow-300 text-slate-900 font-semibold py-2.5 px-5 rounded-lg transition-colors shadow-sm"
			>
				<Icon
					name="solar:add-square-outline"
					class="text-lg"
				/>
				Create Instance
			</NuxtLink>
		</EmptyState>

		<div
			v-else
			class="bg-white rounded-xl shadow-sm border border-slate-200/70 overflow-hidden"
		>
			<table class="w-full text-left">
				<thead class="bg-slate-50 text-slate-500 text-xs uppercase tracking-wider">
					<tr>
						<th class="py-3 px-5 font-semibold">
							Name
						</th>
						<th class="py-3 px-5 font-semibold">
							Status
						</th>
						<th class="py-3 px-5 font-semibold">
							Image
						</th>
						<th class="py-3 px-5 font-semibold">
							Flavor
						</th>
						<th class="py-3 px-5 font-semibold">
							Private IP
						</th>
						<th class="py-3 px-5 font-semibold">
							Public IP
						</th>
						<th class="py-3 px-5" />
					</tr>
				</thead>
				<tbody class="divide-y divide-slate-100">
					<tr
						v-for="instance in instances"
						:key="instance.id"
						class="hover:bg-slate-50 cursor-pointer transition-colors"
						@click="navigateTo(`/instances/${instance.id}`)"
					>
						<td class="py-3.5 px-5 font-medium text-slate-900">
							{{ instance.name }}
						</td>
						<td class="py-3.5 px-5">
							<StatusBadge :status="instance.status" />
						</td>
						<td class="py-3.5 px-5 text-slate-600">
							{{ instance.image_name }}
						</td>
						<td class="py-3.5 px-5 text-slate-600">
							{{ instance.flavor_name }}
						</td>
						<td class="py-3.5 px-5 text-slate-600 font-mono text-sm">
							{{ instance.private_ip_address ?? "—" }}
						</td>
						<td class="py-3.5 px-5 text-slate-600 font-mono text-sm">
							{{ publicIpFor(instance.id) }}
						</td>
						<td class="py-3.5 px-5 text-right">
							<button
								v-if="instance.status === 'ACTIVE' || instance.status === 'SHUTOFF'"
								class="text-slate-400 hover:text-slate-800 transition-colors mr-3"
								:title="instance.status === 'ACTIVE' ? 'Stop instance' : 'Start instance'"
								@click.stop="powerAction(instance)"
							>
								<Icon
									:name="instance.status === 'ACTIVE' ? 'solar:stop-circle-outline' : 'solar:play-circle-outline'"
									class="text-xl"
								/>
							</button>
							<button
								v-if="can('instance:delete')"
								class="text-slate-400 hover:text-red-600 transition-colors disabled:opacity-40"
								:disabled="instance.status === 'DELETING'"
								title="Delete instance"
								@click.stop="removeInstance(instance)"
							>
								<Icon
									name="solar:trash-bin-trash-outline"
									class="text-xl"
								/>
							</button>
						</td>
					</tr>
				</tbody>
			</table>
		</div>
	</div>
</template>

<script setup lang="ts">
import type { InstanceResponse, FloatingIPResponse } from "~/types/api";
import { useToastStore } from "~/stores/toast";

const api = useApi();
const { can } = useAuth();
const toast = useToastStore();

const { data: instances, refresh: refreshInstances } = await useAsyncData(
	"instances",
	() => api<InstanceResponse[]>("/instances/"),
);
const { data: floatingIps, refresh: refreshFloatingIps } = await useAsyncData(
	"floating-ips",
	() => api<FloatingIPResponse[]>("/networks/floating-ips"),
);

const activeCount = computed(
	() => instances.value?.filter(i => i.status === "ACTIVE").length ?? 0,
);

function publicIpFor(instanceId: number): string {
	return floatingIps.value?.find(f => f.instance_id === instanceId)?.ip_address ?? "—";
}

async function removeInstance(instance: InstanceResponse) {
	if (!confirm(`Delete instance "${instance.name}"? This cannot be undone.`)) return;
	try {
		await api(`/instances/${instance.id}`, { method: "DELETE" });
		await refreshInstances();
		toast.success(`Deleting "${instance.name}"…`);
	}
	catch (e: unknown) {
		const err = e as { data?: { detail?: string } };
		toast.error(err.data?.detail ?? "Failed to delete instance");
	}
}

async function powerAction(instance: InstanceResponse) {
	const action = instance.status === "ACTIVE" ? "stop" : "start";
	try {
		await api(`/instances/${instance.id}/${action}`, { method: "POST" });
		await refreshInstances();
		toast.success(`${action === "stop" ? "Stopping" : "Starting"} "${instance.name}"…`);
	}
	catch (e: unknown) {
		const err = e as { data?: { detail?: string } };
		toast.error(err.data?.detail ?? `Failed to ${action} instance`);
	}
}

// poll while instances are provisioning/deleting so statuses stay fresh
let poll: ReturnType<typeof setInterval> | undefined;
onMounted(() => {
	poll = setInterval(() => {
		refreshInstances();
		refreshFloatingIps();
	}, 10000);
});
onUnmounted(() => clearInterval(poll));
</script>
