<template>
	<div>
		<div class="mb-7">
			<h1 class="text-2xl font-bold text-slate-900">
				Volumes
			</h1>
			<p class="text-sm text-slate-500 mt-1">
				Block storage you can attach to instances.
			</p>
		</div>

		<div class="bg-white rounded-xl shadow-sm border border-slate-200/70 p-6 mb-8">
			<h2 class="font-semibold text-slate-900 mb-4">
				Create a volume
			</h2>
			<form
				class="flex items-end gap-4"
				@submit.prevent="submit"
			>
				<div class="flex flex-col gap-2 flex-1">
					<label class="text-sm font-medium text-slate-700">Name</label>
					<input
						v-model="form.name"
						type="text"
						required
						placeholder="data-disk"
						class="w-full rounded-lg border border-slate-300 px-3 py-2.5 outline-none focus:border-slate-800 focus:ring-2 focus:ring-slate-800/10 transition"
					>
				</div>
				<div class="flex flex-col gap-2 w-40">
					<label class="text-sm font-medium text-slate-700">Size (GB)</label>
					<input
						v-model.number="form.sizeGb"
						type="number"
						min="1"
						max="1024"
						required
						class="w-full rounded-lg border border-slate-300 px-3 py-2.5 outline-none focus:border-slate-800 focus:ring-2 focus:ring-slate-800/10 transition"
					>
				</div>
				<button
					type="submit"
					:disabled="submitting"
					class="inline-flex items-center gap-2 bg-slate-800 hover:bg-slate-700 disabled:opacity-60 text-white font-medium py-2.5 px-5 rounded-lg transition-colors"
				>
					<Icon
						name="solar:add-circle-outline"
						class="text-lg"
					/>
					{{ submitting ? "Creating…" : "Create volume" }}
				</button>
			</form>
			<p
				v-if="error"
				class="text-red-600 text-sm mt-3"
			>
				{{ error }}
			</p>
		</div>

		<EmptyState
			v-if="!volumes || volumes.length === 0"
			icon="solar:database-outline"
			title="No volumes yet"
			description="Create a block-storage volume and attach it to an instance."
		/>

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
							Size
						</th>
						<th class="py-3 px-5 font-semibold">
							Status
						</th>
						<th class="py-3 px-5 font-semibold">
							Attached to
						</th>
						<th class="py-3 px-5 font-semibold">
							Device
						</th>
						<th class="py-3 px-5" />
					</tr>
				</thead>
				<tbody class="divide-y divide-slate-100">
					<tr
						v-for="vol in volumes"
						:key="vol.id"
					>
						<td class="py-3.5 px-5 font-medium text-slate-900">
							{{ vol.name }}
						</td>
						<td class="py-3.5 px-5 text-slate-600">
							{{ vol.size_gb }} GB
						</td>
						<td class="py-3.5 px-5">
							<StatusBadge :status="vol.status" />
						</td>
						<td class="py-3.5 px-5 text-slate-600">
							<NuxtLink
								v-if="vol.instance_id"
								:to="`/instances/${vol.instance_id}`"
								class="text-slate-700 hover:underline"
							>
								{{ instanceName(vol.instance_id) }}
							</NuxtLink>
							<span
								v-else
								class="text-slate-400"
							>—</span>
						</td>
						<td class="py-3.5 px-5 text-slate-600 font-mono text-sm">
							{{ vol.device ?? "—" }}
						</td>
						<td class="py-3.5 px-5 text-right whitespace-nowrap">
							<button
								v-if="vol.status === 'available'"
								class="text-sm text-slate-500 hover:text-slate-900 font-medium mr-4 transition-colors"
								@click="openAttach(vol)"
							>
								Attach
							</button>
							<button
								v-else-if="vol.status === 'in-use'"
								class="text-sm text-slate-500 hover:text-slate-900 font-medium mr-4 transition-colors"
								@click="detach(vol)"
							>
								Detach
							</button>
							<button
								v-if="can('volume:delete')"
								class="text-slate-400 hover:text-red-600 transition-colors disabled:opacity-30"
								:disabled="vol.instance_id !== null || vol.status === 'deleting'"
								title="Delete volume"
								@click="remove(vol)"
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

		<!-- attach modal -->
		<div
			v-if="attachTarget"
			class="fixed inset-0 z-30 bg-slate-900/50 flex items-center justify-center p-4"
		>
			<div class="bg-white rounded-xl shadow-xl w-full max-w-md p-6">
				<h2 class="text-lg font-bold text-slate-900 mb-1">
					Attach “{{ attachTarget.name }}”
				</h2>
				<p class="text-sm text-slate-500 mb-5">
					Choose an active instance to attach this {{ attachTarget.size_gb }} GB volume to.
				</p>

				<div
					v-if="activeInstances.length === 0"
					class="text-sm text-slate-500 mb-5"
				>
					No active instances available.
				</div>
				<select
					v-else
					v-model="attachInstanceId"
					class="w-full rounded-lg border border-slate-300 px-3 py-2.5 bg-white outline-none focus:border-slate-800 mb-5"
				>
					<option
						:value="null"
						disabled
					>
						Select an instance
					</option>
					<option
						v-for="inst in activeInstances"
						:key="inst.id"
						:value="inst.id"
					>
						{{ inst.name }}
					</option>
				</select>

				<p
					v-if="attachError"
					class="text-red-600 text-sm mb-4"
				>
					{{ attachError }}
				</p>

				<div class="flex justify-end gap-3">
					<button
						class="text-slate-600 hover:text-slate-900 font-medium py-2.5 px-4 rounded-lg transition-colors"
						@click="attachTarget = null"
					>
						Cancel
					</button>
					<button
						:disabled="attachInstanceId === null || attaching"
						class="bg-slate-800 hover:bg-slate-700 disabled:opacity-50 text-white font-medium py-2.5 px-5 rounded-lg transition-colors"
						@click="confirmAttach"
					>
						{{ attaching ? "Attaching…" : "Attach" }}
					</button>
				</div>
			</div>
		</div>
	</div>
</template>

<script setup lang="ts">
import type { VolumeResponse, InstanceResponse } from "~/types/api";
import { useToastStore } from "~/stores/toast";

const api = useApi();
const { can } = useAuth();
const toast = useToastStore();

const { data: volumes, refresh } = await useAsyncData(
	"volumes",
	() => api<VolumeResponse[]>("/volumes/"),
);
const { data: instances, refresh: refreshInstances } = await useAsyncData(
	"instances-for-volumes",
	() => api<InstanceResponse[]>("/instances/"),
);

const activeInstances = computed(() => instances.value?.filter(i => i.status === "ACTIVE") ?? []);

function instanceName(id: number): string {
	return instances.value?.find(i => i.id === id)?.name ?? `#${id}`;
}

const form = ref({ name: "", sizeGb: 10 });
const error = ref("");
const submitting = ref(false);

async function submit() {
	error.value = "";
	submitting.value = true;
	try {
		await api("/volumes/", {
			method: "POST",
			body: { name: form.value.name.trim(), size_gb: form.value.sizeGb },
		});
		form.value = { name: "", sizeGb: 10 };
		toast.success("Volume created.");
		await refresh();
	}
	catch (e: unknown) {
		const err = e as { data?: { detail?: string } };
		error.value = typeof err.data?.detail === "string" ? err.data.detail : "Failed to create volume";
		toast.error(error.value);
	}
	finally {
		submitting.value = false;
	}
}

// attach modal
const attachTarget = ref<VolumeResponse | null>(null);
const attachInstanceId = ref<number | null>(null);
const attachError = ref("");
const attaching = ref(false);

function openAttach(vol: VolumeResponse) {
	attachTarget.value = vol;
	attachInstanceId.value = null;
	attachError.value = "";
}

async function confirmAttach() {
	if (!attachTarget.value || attachInstanceId.value === null) return;
	attachError.value = "";
	attaching.value = true;
	try {
		await api(`/volumes/${attachTarget.value.id}/attach`, {
			method: "POST",
			body: { instance_id: attachInstanceId.value },
		});
		attachTarget.value = null;
		toast.success("Attaching volume…");
		await refresh();
	}
	catch (e: unknown) {
		const err = e as { data?: { detail?: string } };
		attachError.value = err.data?.detail ?? "Failed to attach";
		toast.error(attachError.value);
	}
	finally {
		attaching.value = false;
	}
}

async function detach(vol: VolumeResponse) {
	if (!confirm(`Detach “${vol.name}”?`)) return;
	try {
		await api(`/volumes/${vol.id}/detach`, { method: "POST" });
		await refresh();
		toast.success(`Detaching "${vol.name}"…`);
	}
	catch (e: unknown) {
		const err = e as { data?: { detail?: string } };
		toast.error(err.data?.detail ?? "Failed to detach volume");
	}
}

async function remove(vol: VolumeResponse) {
	if (!confirm(`Delete volume “${vol.name}”? This cannot be undone.`)) return;
	try {
		await api(`/volumes/${vol.id}`, { method: "DELETE" });
		await refresh();
		toast.success(`Deleting volume "${vol.name}"…`);
	}
	catch (e: unknown) {
		const err = e as { data?: { detail?: string } };
		toast.error(err.data?.detail ?? "Failed to delete volume");
	}
}

// poll so creating/attaching/detaching statuses settle in the UI
let poll: ReturnType<typeof setInterval> | undefined;
onMounted(() => {
	poll = setInterval(() => {
		refresh();
		refreshInstances();
	}, 5000);
});
onUnmounted(() => clearInterval(poll));
</script>
