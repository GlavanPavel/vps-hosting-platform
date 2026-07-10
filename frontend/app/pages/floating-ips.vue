<template>
	<div>
		<div class="flex items-start justify-between mb-7">
			<div>
				<h1 class="text-2xl font-bold text-slate-900">
					Floating IPs
				</h1>
				<p class="text-sm text-slate-500 mt-1">
					Public IPs you reserve from the external pool and attach to instances — like AWS
					Elastic IPs. A reserved IP survives instance deletion until you release it.
				</p>
			</div>
			<button
				v-if="can('floating_ip:manage')"
				:disabled="allocating"
				class="inline-flex items-center gap-2 bg-slate-800 hover:bg-slate-700 disabled:opacity-60 text-white font-medium py-2.5 px-5 rounded-lg transition-colors shrink-0"
				@click="allocate"
			>
				<Icon
					name="solar:add-circle-outline"
					class="text-lg"
				/>
				{{ allocating ? "Allocating…" : "Allocate floating IP" }}
			</button>
		</div>

		<p
			v-if="error"
			class="text-red-600 text-sm mb-4"
		>
			{{ error }}
		</p>

		<EmptyState
			v-if="!floatingIps || floatingIps.length === 0"
			icon="solar:point-on-map-outline"
			title="No floating IPs"
			description="Allocate a public IP from the external pool, then attach it to an instance."
		/>

		<div
			v-else
			class="bg-white rounded-xl shadow-sm border border-slate-200/70 overflow-hidden"
		>
			<table class="w-full text-left">
				<thead class="bg-slate-50 text-slate-500 text-xs uppercase tracking-wider">
					<tr>
						<th class="py-3 px-5 font-semibold">
							IP address
						</th>
						<th class="py-3 px-5 font-semibold">
							Status
						</th>
						<th class="py-3 px-5 font-semibold">
							Attached to
						</th>
						<th class="py-3 px-5 font-semibold">
							Pool
						</th>
						<th class="py-3 px-5" />
					</tr>
				</thead>
				<tbody class="divide-y divide-slate-100">
					<tr
						v-for="fip in floatingIps"
						:key="fip.id"
					>
						<td class="py-3.5 px-5">
							<div class="flex items-center gap-2">
								<code class="font-mono text-slate-900 font-medium">{{ fip.ip_address }}</code>
								<CopyButton :text="fip.ip_address" />
							</div>
						</td>
						<td class="py-3.5 px-5">
							<StatusBadge :status="fip.status" />
						</td>
						<td class="py-3.5 px-5 text-slate-600">
							<NuxtLink
								v-if="fip.instance_id"
								:to="`/instances/${fip.instance_id}`"
								class="text-slate-700 hover:underline"
							>
								{{ fip.instance_name ?? `#${fip.instance_id}` }}
							</NuxtLink>
							<span
								v-else
								class="text-slate-400"
							>—</span>
						</td>
						<td class="py-3.5 px-5 text-slate-500 text-sm">
							{{ fip.external_network_name }}
						</td>
						<td class="py-3.5 px-5 text-right whitespace-nowrap">
							<button
								v-if="can('floating_ip:manage') && fip.instance_id === null && !isBusy(fip)"
								class="text-sm text-slate-500 hover:text-slate-900 font-medium mr-4 transition-colors"
								@click="openAssociate(fip)"
							>
								Associate
							</button>
							<button
								v-else-if="can('floating_ip:manage') && fip.instance_id !== null && !isBusy(fip)"
								class="text-sm text-slate-500 hover:text-slate-900 font-medium mr-4 transition-colors"
								@click="disassociate(fip)"
							>
								Disassociate
							</button>
							<button
								v-if="can('floating_ip:release')"
								class="text-slate-400 hover:text-red-600 transition-colors disabled:opacity-30"
								:disabled="fip.instance_id !== null || fip.status === 'releasing'"
								:title="fip.instance_id !== null ? 'Disassociate before releasing' : 'Release back to the pool'"
								@click="release(fip)"
							>
								<Icon
									name="solar:trash-bin-trash-outline"
									class="text-xl align-middle"
								/>
							</button>
						</td>
					</tr>
				</tbody>
			</table>
		</div>

		<!-- associate modal -->
		<div
			v-if="associateTarget"
			class="fixed inset-0 z-30 bg-slate-900/50 flex items-center justify-center p-4"
		>
			<div class="bg-white rounded-xl shadow-xl w-full max-w-md p-6">
				<h2 class="text-lg font-bold text-slate-900 mb-1">
					Associate {{ associateTarget.ip_address }}
				</h2>
				<p class="text-sm text-slate-500 mb-5">
					Attach this public IP to an active instance. Only instances without a public IP are shown.
				</p>

				<div
					v-if="attachableInstances.length === 0"
					class="text-sm text-slate-500 mb-5"
				>
					No eligible instances — every active instance already has a public IP.
				</div>
				<select
					v-else
					v-model="associateInstanceId"
					class="w-full rounded-lg border border-slate-300 px-3 py-2.5 bg-white outline-none focus:border-slate-800 mb-5"
				>
					<option
						:value="null"
						disabled
					>
						Select an instance
					</option>
					<option
						v-for="inst in attachableInstances"
						:key="inst.id"
						:value="inst.id"
					>
						{{ inst.name }}
					</option>
				</select>

				<p
					v-if="associateError"
					class="text-red-600 text-sm mb-4"
				>
					{{ associateError }}
				</p>

				<div class="flex justify-end gap-3">
					<button
						class="text-slate-600 hover:text-slate-900 font-medium py-2.5 px-4 rounded-lg transition-colors"
						@click="associateTarget = null"
					>
						Cancel
					</button>
					<button
						:disabled="associateInstanceId === null || associating"
						class="bg-slate-800 hover:bg-slate-700 disabled:opacity-50 text-white font-medium py-2.5 px-5 rounded-lg transition-colors"
						@click="confirmAssociate"
					>
						{{ associating ? "Associating…" : "Associate" }}
					</button>
				</div>
			</div>
		</div>
	</div>
</template>

<script setup lang="ts">
import type { FloatingIPResponse, InstanceResponse } from "~/types/api";
import { useToastStore } from "~/stores/toast";

const api = useApi();
const { can } = useAuth();
const toast = useToastStore();

const { data: floatingIps, refresh } = await useAsyncData(
	"floating-ips-page",
	() => api<FloatingIPResponse[]>("/floating-ips/"),
);
const { data: instances, refresh: refreshInstances } = await useAsyncData(
	"instances-for-fips",
	() => api<InstanceResponse[]>("/instances/"),
);

// a FIP mid-transition (allocating / associating / disassociating / releasing) —
// no row action while OpenStack is settling it
function isBusy(fip: FloatingIPResponse): boolean {
	return ["allocating", "associating", "disassociating", "releasing"].includes(fip.status);
}

// active instances that don't already hold a floating IP
const attachableInstances = computed(() => {
	const taken = new Set((floatingIps.value ?? []).map(f => f.instance_id).filter(Boolean));
	return (instances.value ?? []).filter(i => i.status === "ACTIVE" && !taken.has(i.id));
});

const error = ref("");
const allocating = ref(false);

async function allocate() {
	error.value = "";
	allocating.value = true;
	try {
		await api("/floating-ips/", { method: "POST" });
		// Celery creates the row once OpenStack returns the address — poll it in
		await new Promise(r => setTimeout(r, 1500));
		await refresh();
		toast.success("Floating IP allocation requested.");
	}
	catch (e: unknown) {
		const err = e as { data?: { detail?: string } };
		error.value = err.data?.detail ?? "Failed to allocate floating IP";
		toast.error(error.value);
	}
	finally {
		allocating.value = false;
	}
}

// associate modal
const associateTarget = ref<FloatingIPResponse | null>(null);
const associateInstanceId = ref<number | null>(null);
const associateError = ref("");
const associating = ref(false);

function openAssociate(fip: FloatingIPResponse) {
	associateTarget.value = fip;
	associateInstanceId.value = null;
	associateError.value = "";
}

async function confirmAssociate() {
	if (!associateTarget.value || associateInstanceId.value === null) return;
	associateError.value = "";
	associating.value = true;
	try {
		await api(`/floating-ips/${associateTarget.value.id}/associate`, {
			method: "POST",
			body: { instance_id: associateInstanceId.value },
		});
		toast.success(`Associating ${associateTarget.value.ip_address}…`);
		associateTarget.value = null;
		await refresh();
	}
	catch (e: unknown) {
		const err = e as { data?: { detail?: string } };
		associateError.value = err.data?.detail ?? "Failed to associate";
	}
	finally {
		associating.value = false;
	}
}

async function disassociate(fip: FloatingIPResponse) {
	if (!confirm(`Detach ${fip.ip_address} from its instance?`)) return;
	try {
		await api(`/floating-ips/${fip.id}/disassociate`, { method: "POST" });
		await refresh();
		toast.success(`Detaching ${fip.ip_address}…`);
	}
	catch (e: unknown) {
		const err = e as { data?: { detail?: string } };
		toast.error(err.data?.detail ?? "Failed to disassociate");
	}
}

async function release(fip: FloatingIPResponse) {
	if (!confirm(`Release ${fip.ip_address} back to the pool? This cannot be undone.`)) return;
	try {
		await api(`/floating-ips/${fip.id}`, { method: "DELETE" });
		await refresh();
		toast.success(`Releasing ${fip.ip_address}…`);
	}
	catch (e: unknown) {
		const err = e as { data?: { detail?: string } };
		toast.error(err.data?.detail ?? "Failed to release");
	}
}

// poll so allocating/associating/disassociating statuses settle in the UI
let poll: ReturnType<typeof setInterval> | undefined;
onMounted(() => {
	poll = setInterval(() => {
		refresh();
		refreshInstances();
	}, 5000);
});
onUnmounted(() => clearInterval(poll));
</script>
