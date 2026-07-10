<template>
	<div>
		<div class="mb-7">
			<h1 class="text-2xl font-bold text-slate-900">
				SSH Keys
			</h1>
			<p class="text-sm text-slate-500 mt-1">
				Generate a new keypair or import an existing public key.
			</p>
		</div>

		<div class="bg-white rounded-xl shadow-sm border border-slate-200/70 p-6 mb-8">
			<!-- mode tabs -->
			<div class="inline-flex rounded-lg bg-slate-100 p-1 mb-6">
				<button
					v-for="m in (['generate', 'import'] as const)"
					:key="m"
					class="px-4 py-1.5 rounded-md text-sm font-medium transition-colors"
					:class="mode === m ? 'bg-white text-slate-900 shadow-sm' : 'text-slate-500 hover:text-slate-700'"
					@click="mode = m"
				>
					{{ m === "generate" ? "Generate new" : "Import existing" }}
				</button>
			</div>

			<!-- generate -->
			<form
				v-if="mode === 'generate'"
				class="space-y-4"
				@submit.prevent="generate"
			>
				<div class="grid grid-cols-2 gap-5">
					<div class="flex flex-col gap-2">
						<label class="text-sm font-medium text-slate-700">Name</label>
						<input
							v-model="genForm.name"
							type="text"
							required
							placeholder="my-laptop"
							class="w-full rounded-lg border border-slate-300 px-3 py-2.5 outline-none focus:border-slate-800 focus:ring-2 focus:ring-slate-800/10 transition"
						>
					</div>
					<div class="flex flex-col gap-2">
						<label class="text-sm font-medium text-slate-700">Key type</label>
						<select
							v-model="genForm.keyType"
							class="w-full rounded-lg border border-slate-300 px-3 py-2.5 bg-white outline-none focus:border-slate-800 focus:ring-2 focus:ring-slate-800/10 transition"
						>
							<option value="ed25519">
								Ed25519 (recommended)
							</option>
							<option value="rsa">
								RSA 4096
							</option>
						</select>
					</div>
				</div>
				<p
					v-if="genError"
					class="text-red-600 text-sm"
				>
					{{ genError }}
				</p>
				<button
					type="submit"
					:disabled="submitting"
					class="inline-flex items-center gap-2 bg-yellow-400 hover:bg-yellow-300 disabled:opacity-60 text-slate-900 font-semibold py-2.5 px-5 rounded-lg transition-colors shadow-sm"
				>
					<Icon
						name="solar:magic-stick-3-outline"
						class="text-lg"
					/>
					{{ submitting ? "Generating…" : "Generate keypair" }}
				</button>
			</form>

			<!-- import -->
			<form
				v-else
				class="space-y-4"
				@submit.prevent="importKey"
			>
				<div class="flex flex-col gap-2 w-1/2">
					<label class="text-sm font-medium text-slate-700">Name</label>
					<input
						v-model="impForm.name"
						type="text"
						required
						placeholder="my-laptop"
						class="w-full rounded-lg border border-slate-300 px-3 py-2.5 outline-none focus:border-slate-800 focus:ring-2 focus:ring-slate-800/10 transition"
					>
				</div>
				<div class="flex flex-col gap-2">
					<label class="text-sm font-medium text-slate-700">Public key</label>
					<textarea
						v-model="impForm.publicKey"
						required
						rows="3"
						placeholder="ssh-ed25519 AAAA... user@host"
						class="w-full rounded-lg border border-slate-300 px-3 py-2.5 outline-none focus:border-slate-800 focus:ring-2 focus:ring-slate-800/10 transition font-mono text-sm"
					/>
				</div>
				<p
					v-if="impError"
					class="text-red-600 text-sm"
				>
					{{ impError }}
				</p>
				<button
					type="submit"
					:disabled="submitting"
					class="inline-flex items-center gap-2 bg-slate-800 hover:bg-slate-700 disabled:opacity-60 text-white font-medium py-2.5 px-5 rounded-lg transition-colors"
				>
					<Icon
						name="solar:upload-outline"
						class="text-lg"
					/>
					{{ submitting ? "Importing…" : "Import keypair" }}
				</button>
			</form>
		</div>

		<EmptyState
			v-if="!keypairs || keypairs.length === 0"
			icon="solar:key-outline"
			title="No SSH keys yet"
			description="Generate or import a key so you can connect to your instances."
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
							Fingerprint
						</th>
						<th class="py-3 px-5 font-semibold">
							OpenStack
						</th>
						<th class="py-3 px-5 font-semibold">
							Created
						</th>
						<th class="py-3 px-5" />
					</tr>
				</thead>
				<tbody class="divide-y divide-slate-100">
					<tr
						v-for="kp in keypairs"
						:key="kp.id"
					>
						<td class="py-3.5 px-5 font-medium text-slate-900">
							{{ kp.name }}
						</td>
						<td class="py-3.5 px-5 text-slate-600 font-mono text-xs">
							{{ kp.fingerprint }}
						</td>
						<td class="py-3.5 px-5">
							<SyncBadge :synced="!!kp.openstack_name" />
						</td>
						<td class="py-3.5 px-5 text-slate-600 text-sm">
							{{ new Date(kp.created_at).toLocaleString() }}
						</td>
						<td class="py-3.5 px-5 text-right">
							<button
								class="text-slate-400 hover:text-red-600 transition-colors"
								title="Delete keypair"
								@click="remove(kp)"
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

		<!-- one-time private key modal -->
		<div
			v-if="generated"
			class="fixed inset-0 z-30 bg-slate-900/50 flex items-center justify-center p-4"
		>
			<div class="bg-white rounded-xl shadow-xl w-full max-w-2xl">
				<div class="p-6 border-b border-slate-100">
					<h2 class="text-lg font-bold text-slate-900 flex items-center gap-2">
						<Icon
							name="solar:key-bold-duotone"
							class="text-yellow-500 text-2xl"
						/>
						Save your private key
					</h2>
				</div>

				<div class="p-6 space-y-4">
					<div class="flex items-start gap-2.5 bg-amber-50 border border-amber-200 rounded-lg p-3.5">
						<Icon
							name="solar:danger-triangle-outline"
							class="text-amber-500 text-xl shrink-0 mt-0.5"
						/>
						<p class="text-sm text-amber-800">
							This is the only time the private key for
							<span class="font-semibold">{{ generated.name }}</span>
							will be shown. Download or copy it now — it is never stored on the server.
						</p>
					</div>

					<div class="relative">
						<textarea
							:value="generated.private_key"
							readonly
							rows="9"
							class="w-full rounded-lg border border-slate-300 bg-slate-50 p-3 font-mono text-xs text-slate-700 resize-none"
						/>
					</div>

					<div class="flex items-center gap-3">
						<button
							class="inline-flex items-center gap-2 bg-yellow-400 hover:bg-yellow-300 text-slate-900 font-semibold py-2.5 px-5 rounded-lg transition-colors shadow-sm"
							@click="downloadKey"
						>
							<Icon
								name="solar:download-outline"
								class="text-lg"
							/>
							Download .pem
						</button>
						<CopyButton
							:text="generated.private_key"
							with-label
							label="Copy key"
							class="border border-slate-300 rounded-lg px-4 py-2.5 hover:bg-slate-50"
						/>
					</div>

					<p class="text-xs text-slate-400">
						After downloading, restrict its permissions: <code class="font-mono">chmod 600 {{ generated.name }}.pem</code>
					</p>
				</div>

				<div class="p-6 border-t border-slate-100 flex justify-end">
					<button
						class="bg-slate-800 hover:bg-slate-700 text-white font-medium py-2.5 px-6 rounded-lg transition-colors"
						@click="closeModal"
					>
						I&apos;ve saved it
					</button>
				</div>
			</div>
		</div>
	</div>
</template>

<script setup lang="ts">
import type { KeypairResponse, KeypairGenerateResponse } from "~/types/api";
import { useToastStore } from "~/stores/toast";

const api = useApi();
const toast = useToastStore();

const { data: keypairs, refresh } = await useAsyncData(
	"keypairs",
	() => api<KeypairResponse[]>("/keypairs/"),
);

const mode = ref<"generate" | "import">("generate");
const submitting = ref(false);

const genForm = ref<{ name: string; keyType: "ed25519" | "rsa" }>({ name: "", keyType: "ed25519" });
const genError = ref("");

const impForm = ref({ name: "", publicKey: "" });
const impError = ref("");

// holds the freshly generated key while the modal is open
const generated = ref<KeypairGenerateResponse | null>(null);

async function generate() {
	genError.value = "";
	submitting.value = true;
	try {
		const res = await api<KeypairGenerateResponse>("/keypairs/generate", {
			method: "POST",
			body: { name: genForm.value.name.trim(), key_type: genForm.value.keyType },
		});
		generated.value = res;
		toast.success("Keypair generated — save the private key.");
		genForm.value = { name: "", keyType: "ed25519" };
	}
	catch (e: unknown) {
		const err = e as { data?: { detail?: string } };
		genError.value = err.data?.detail ?? "Failed to generate keypair";
		toast.error(genError.value);
	}
	finally {
		submitting.value = false;
	}
}

async function importKey() {
	impError.value = "";
	submitting.value = true;
	try {
		await api("/keypairs/", {
			method: "POST",
			body: { name: impForm.value.name.trim(), public_key: impForm.value.publicKey.trim() },
		});
		impForm.value = { name: "", publicKey: "" };
		toast.success("Keypair imported — uploading to OpenStack…");
		await refresh();
	}
	catch (e: unknown) {
		const err = e as { data?: { detail?: string } };
		impError.value = err.data?.detail ?? "Failed to import keypair";
		toast.error(impError.value);
	}
	finally {
		submitting.value = false;
	}
}

function downloadKey() {
	if (!generated.value) return;
	const blob = new Blob([generated.value.private_key], { type: "application/x-pem-file" });
	const url = URL.createObjectURL(blob);
	const a = document.createElement("a");
	a.href = url;
	a.download = `${generated.value.name}.pem`;
	a.click();
	URL.revokeObjectURL(url);
}

function closeModal() {
	generated.value = null;
	refresh();
}

async function remove(kp: KeypairResponse) {
	if (!confirm(`Delete keypair "${kp.name}"?`)) return;
	try {
		await api(`/keypairs/${kp.id}`, { method: "DELETE" });
		await refresh();
		toast.success(`Deleting keypair "${kp.name}"…`);
	}
	catch (e: unknown) {
		const err = e as { data?: { detail?: string } };
		toast.error(err.data?.detail ?? "Failed to delete keypair");
	}
}

// poll so the Synced badge updates once Celery uploads the key
let poll: ReturnType<typeof setInterval> | undefined;
onMounted(() => {
	poll = setInterval(refresh, 5000);
});
onUnmounted(() => clearInterval(poll));
</script>
