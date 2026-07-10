<template>
	<div>
		<div class="mb-7">
			<h1 class="text-2xl font-bold text-slate-900">
				Images
			</h1>
			<p class="text-sm text-slate-500 mt-1">
				Import a custom OS image from a URL — Glance downloads it for you. Active images
				appear as a choice on the Create page.
			</p>
		</div>

		<div class="bg-white rounded-xl shadow-sm border border-slate-200/70 p-6 mb-8">
			<h2 class="font-semibold text-slate-900 mb-4">
				Import from URL
			</h2>
			<form
				class="space-y-4"
				@submit.prevent="submit"
			>
				<div class="grid grid-cols-3 gap-4">
					<div class="flex flex-col gap-2">
						<label class="text-sm font-medium text-slate-700">Name</label>
						<input
							v-model="form.name"
							type="text"
							required
							maxlength="40"
							placeholder="debian-12"
							class="w-full rounded-lg border border-slate-300 px-3 py-2.5 outline-none focus:border-slate-800 focus:ring-2 focus:ring-slate-800/10 transition"
						>
					</div>
					<div class="flex flex-col gap-2 col-span-2">
						<label class="text-sm font-medium text-slate-700">Image URL</label>
						<input
							v-model="form.sourceUrl"
							type="url"
							required
							placeholder="https://cloud.debian.org/images/cloud/.../debian-12-genericcloud-amd64.qcow2"
							class="w-full rounded-lg border border-slate-300 px-3 py-2.5 outline-none focus:border-slate-800 focus:ring-2 focus:ring-slate-800/10 transition"
						>
					</div>
				</div>
				<div class="flex items-end justify-between gap-4">
					<div class="flex flex-col gap-2 w-40">
						<label class="text-sm font-medium text-slate-700">Disk format</label>
						<select
							v-model="form.diskFormat"
							class="w-full rounded-lg border border-slate-300 px-3 py-2.5 bg-white outline-none focus:border-slate-800 focus:ring-2 focus:ring-slate-800/10 transition"
						>
							<option value="qcow2">
								qcow2
							</option>
							<option value="raw">
								raw
							</option>
							<option value="vmdk">
								vmdk
							</option>
							<option value="vdi">
								vdi
							</option>
							<option value="iso">
								iso
							</option>
						</select>
					</div>
					<button
						type="submit"
						:disabled="submitting"
						class="inline-flex items-center gap-2 bg-slate-800 hover:bg-slate-700 disabled:opacity-60 text-white font-medium py-2.5 px-5 rounded-lg transition-colors"
					>
						<Icon
							name="solar:cloud-download-outline"
							class="text-lg"
						/>
						{{ submitting ? "Importing…" : "Import image" }}
					</button>
				</div>
			</form>
			<p
				v-if="error"
				class="text-red-600 text-sm mt-3"
			>
				{{ error }}
			</p>
			<p class="text-xs text-slate-400 mt-3">
				The URL must be reachable from the OpenStack host and point at a bootable cloud image
				(cloud-init + virtio). Large images can take several minutes to import.
			</p>
		</div>

		<EmptyState
			v-if="!images || images.length === 0"
			icon="solar:gallery-outline"
			title="No custom images yet"
			description="Import a .qcow2/.img from a URL to launch instances from your own OS image."
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
							Format
						</th>
						<th class="py-3 px-5 font-semibold">
							Size
						</th>
						<th class="py-3 px-5 font-semibold">
							Min disk
						</th>
						<th class="py-3 px-5 font-semibold">
							Status
						</th>
						<th class="py-3 px-5 font-semibold">
							Source
						</th>
						<th class="py-3 px-5 font-semibold">
							Public
						</th>
						<th class="py-3 px-5" />
					</tr>
				</thead>
				<tbody class="divide-y divide-slate-100">
					<tr
						v-for="img in images"
						:key="img.id"
					>
						<td class="py-3.5 px-5 font-medium text-slate-900">
							{{ img.name }}
							<span
								v-if="img.source_type === 'snapshot'"
								class="ml-1.5 inline-flex items-center gap-1 rounded-md bg-violet-100 text-violet-700 px-1.5 py-0.5 text-[11px] font-semibold align-middle"
							>
								<Icon name="solar:camera-outline" />
								snapshot
							</span>
						</td>
						<td class="py-3.5 px-5 text-slate-600 font-mono text-sm">
							{{ img.disk_format }}
						</td>
						<td class="py-3.5 px-5 text-slate-600">
							{{ formatSize(img.size_bytes) }}
						</td>
						<td class="py-3.5 px-5 text-slate-600">
							{{ img.min_disk_gb ? `${img.min_disk_gb} GB` : "—" }}
						</td>
						<td class="py-3.5 px-5">
							<StatusBadge :status="img.status" />
						</td>
						<td class="py-3.5 px-5 text-slate-500 text-sm max-w-xs truncate">
							<a
								v-if="img.source_url"
								:href="img.source_url"
								target="_blank"
								rel="noopener noreferrer"
								class="hover:underline"
								:title="img.source_url"
							>{{ img.source_url }}</a>
							<span v-else>
								{{ img.source_instance_id ? `snapshot of instance #${img.source_instance_id}` : "snapshot" }}
							</span>
						</td>
						<td class="py-3.5 px-5">
							<button
								v-if="can('image:publish')"
								:disabled="img.status !== 'active'"
								class="relative inline-flex h-5 w-9 items-center rounded-full transition-colors disabled:opacity-40 disabled:cursor-not-allowed"
								:class="img.is_public ? 'bg-green-500' : 'bg-slate-300'"
								:title="img.status !== 'active'
									? 'Only active images can be shared'
									: (img.is_public ? 'Public — everyone can use it. Click to make private.' : 'Private — only your org. Click to make public.')"
								@click="toggleVisibility(img)"
							>
								<span
									class="inline-block h-3.5 w-3.5 transform rounded-full bg-white transition-transform"
									:class="img.is_public ? 'translate-x-5' : 'translate-x-1'"
								/>
							</button>
							<span
								v-else
								class="text-xs text-slate-500"
							>{{ img.is_public ? "Public" : "Private" }}</span>
						</td>
						<td class="py-3.5 px-5 text-right whitespace-nowrap">
							<button
								v-if="can('image:delete')"
								class="text-slate-400 hover:text-red-600 transition-colors disabled:opacity-30"
								:disabled="img.status === 'deleting'"
								title="Delete image"
								@click="remove(img)"
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
	</div>
</template>

<script setup lang="ts">
import type { ImageResponse } from "~/types/api";
import { useToastStore } from "~/stores/toast";

const api = useApi();
const { can } = useAuth();
const toast = useToastStore();

const { data: images, refresh } = await useAsyncData(
	"images",
	() => api<ImageResponse[]>("/images/"),
);

const form = ref({ name: "", sourceUrl: "", diskFormat: "qcow2" });
const error = ref("");
const submitting = ref(false);

function formatSize(bytes: number | null): string {
	if (!bytes) return "—";
	const gb = bytes / 1024 ** 3;
	if (gb >= 1) return `${gb.toFixed(2)} GB`;
	return `${(bytes / 1024 ** 2).toFixed(0)} MB`;
}

async function submit() {
	error.value = "";
	submitting.value = true;
	try {
		await api("/images/", {
			method: "POST",
			body: {
				name: form.value.name.trim(),
				source_url: form.value.sourceUrl.trim(),
				disk_format: form.value.diskFormat,
			},
		});
		form.value = { name: "", sourceUrl: "", diskFormat: "qcow2" };
		toast.success("Image import started — Glance is downloading it…");
		await refresh();
	}
	catch (e: unknown) {
		const err = e as { data?: { detail?: string } };
		error.value = typeof err.data?.detail === "string" ? err.data.detail : "Failed to import image";
		toast.error(error.value);
	}
	finally {
		submitting.value = false;
	}
}

async function toggleVisibility(img: ImageResponse) {
	const next = !img.is_public;
	try {
		await api(`/images/${img.id}/visibility`, { method: "POST", body: { is_public: next } });
		await refresh();
		toast.success(next ? "Image is now public." : "Image is now private.");
	}
	catch (e: unknown) {
		const err = e as { data?: { detail?: string } };
		toast.error(typeof err.data?.detail === "string" ? err.data.detail : "Failed to change visibility");
	}
}

async function remove(img: ImageResponse) {
	if (!confirm(`Delete image “${img.name}”? This cannot be undone.`)) return;
	try {
		await api(`/images/${img.id}`, { method: "DELETE" });
		await refresh();
		toast.success(`Deleting image "${img.name}"…`);
	}
	catch (e: unknown) {
		const err = e as { data?: { detail?: string } };
		toast.error(err.data?.detail ?? "Failed to delete image");
	}
}

// poll so queued/importing statuses settle in the UI
let poll: ReturnType<typeof setInterval> | undefined;
onMounted(() => {
	poll = setInterval(refresh, 5000);
});
onUnmounted(() => clearInterval(poll));
</script>
