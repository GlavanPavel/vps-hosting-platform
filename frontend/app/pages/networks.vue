<template>
	<div>
		<div class="mb-7">
			<h1 class="text-2xl font-bold text-slate-900">
				Networks
			</h1>
			<p class="text-sm text-slate-500 mt-1">
				Private VPC networks and their subnets.
			</p>
		</div>

		<div class="bg-white rounded-xl shadow-sm border border-slate-200/70 p-6 mb-8">
			<h2 class="font-semibold text-slate-900 mb-4">
				Create a network
			</h2>
			<form
				class="space-y-4"
				@submit.prevent="submit"
			>
				<div class="flex flex-col gap-2 w-1/2">
					<label class="text-sm font-medium text-slate-700">Network name</label>
					<input
						v-model="form.name"
						type="text"
						required
						placeholder="my-vpc"
						class="w-full rounded-lg border border-slate-300 px-3 py-2.5 outline-none focus:border-slate-800 focus:ring-2 focus:ring-slate-800/10 transition"
					>
				</div>

				<div class="space-y-2">
					<label class="text-sm font-medium text-slate-700">Subnets</label>
					<div
						v-for="(subnet, i) in form.subnets"
						:key="i"
						class="flex gap-3 items-center"
					>
						<input
							v-model="subnet.name"
							type="text"
							required
							placeholder="subnet name"
							class="w-1/3 rounded-lg border border-slate-300 px-3 py-2.5 outline-none focus:border-slate-800 focus:ring-2 focus:ring-slate-800/10 transition"
						>
						<input
							v-model="subnet.cidr"
							type="text"
							required
							placeholder="10.0.1.0/24"
							class="w-1/3 rounded-lg border border-slate-300 px-3 py-2.5 outline-none focus:border-slate-800 focus:ring-2 focus:ring-slate-800/10 transition font-mono text-sm"
						>
						<button
							v-if="form.subnets.length > 1"
							type="button"
							class="text-slate-400 hover:text-red-500 transition-colors"
							@click="form.subnets.splice(i, 1)"
						>
							<Icon
								name="solar:close-circle-outline"
								class="text-xl"
							/>
						</button>
					</div>
					<button
						type="button"
						class="text-sm text-slate-600 hover:text-slate-900 font-medium transition-colors"
						@click="form.subnets.push({ name: '', cidr: '' })"
					>
						+ Add another subnet
					</button>
				</div>

				<p
					v-if="error"
					class="text-red-600 text-sm"
				>
					{{ error }}
				</p>
				<button
					type="submit"
					:disabled="submitting"
					class="inline-flex items-center gap-2 bg-slate-800 hover:bg-slate-700 disabled:opacity-60 text-white font-medium py-2.5 px-5 rounded-lg transition-colors"
				>
					<Icon
						name="solar:add-circle-outline"
						class="text-lg"
					/>
					{{ submitting ? "Creating…" : "Create network" }}
				</button>
			</form>
		</div>

		<EmptyState
			v-if="!networks || networks.length === 0"
			icon="solar:global-outline"
			title="No networks yet"
			description="Create a VPC network with at least one subnet."
		/>

		<div
			v-else
			class="space-y-4"
		>
			<div
				v-for="net in networks"
				:key="net.id"
				class="bg-white rounded-xl shadow-sm border border-slate-200/70 p-6"
			>
				<div class="flex items-center justify-between mb-4">
					<div class="flex items-center gap-3">
						<h3 class="font-bold text-lg text-slate-900">
							{{ net.name }}
						</h3>
						<SyncBadge
							:synced="!!net.openstack_network_id"
							synced-label="Provisioned"
							pending-label="Provisioning"
						/>
					</div>
					<button
						v-if="can('network:delete')"
						class="text-slate-400 hover:text-red-600 transition-colors"
						title="Delete network"
						@click="remove(net)"
					>
						<Icon
							name="solar:trash-bin-trash-outline"
							class="text-xl"
						/>
					</button>
				</div>
				<div class="space-y-2">
					<div
						v-for="subnet in net.subnets"
						:key="subnet.id"
						class="flex items-center gap-3 text-sm"
					>
						<Icon
							name="solar:branching-paths-up-outline"
							class="text-base text-slate-400"
						/>
						<span class="font-medium text-slate-700">{{ subnet.name }}</span>
						<span class="font-mono text-slate-500">{{ subnet.cidr }}</span>
						<span
							class="text-xs px-2 py-0.5 rounded-full"
							:class="subnet.openstack_subnet_id ? 'bg-green-50 text-green-600' : 'bg-yellow-50 text-yellow-600'"
						>
							{{ subnet.openstack_subnet_id ? "ready" : "pending" }}
						</span>
					</div>
				</div>
			</div>
		</div>
	</div>
</template>

<script setup lang="ts">
import type { NetworkResponse } from "~/types/api";
import { useToastStore } from "~/stores/toast";

const api = useApi();
const { can } = useAuth();
const toast = useToastStore();

const { data: networks, refresh } = await useAsyncData(
	"networks",
	() => api<NetworkResponse[]>("/networks/"),
);

const form = ref({
	name: "",
	subnets: [{ name: "", cidr: "" }],
});
const error = ref("");
const submitting = ref(false);

async function submit() {
	error.value = "";
	submitting.value = true;
	try {
		await api("/networks/", {
			method: "POST",
			body: {
				name: form.value.name.trim(),
				subnets: form.value.subnets.map(s => ({ name: s.name.trim(), cidr: s.cidr.trim() })),
			},
		});
		form.value = { name: "", subnets: [{ name: "", cidr: "" }] };
		toast.success("Network created — provisioning…");
		await refresh();
	}
	catch (e: unknown) {
		const err = e as { data?: { detail?: string } };
		error.value = err.data?.detail ?? "Failed to create network";
		toast.error(error.value);
	}
	finally {
		submitting.value = false;
	}
}

async function remove(net: NetworkResponse) {
	if (!confirm(`Delete network "${net.name}" and its subnets?`)) return;
	try {
		await api(`/networks/${net.id}`, { method: "DELETE" });
		await refresh();
		toast.success(`Deleting network "${net.name}"…`);
	}
	catch (e: unknown) {
		const err = e as { data?: { detail?: string } };
		toast.error(err.data?.detail ?? "Failed to delete network");
	}
}

// poll so provisioning badges update once Celery finishes
let poll: ReturnType<typeof setInterval> | undefined;
onMounted(() => {
	poll = setInterval(refresh, 5000);
});
onUnmounted(() => clearInterval(poll));
</script>
