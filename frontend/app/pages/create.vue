<template>
	<div class="max-w-4xl">
		<div class="mb-7">
			<h1 class="text-2xl font-bold text-slate-900">
				Create an instance
			</h1>
			<p class="text-sm text-slate-500 mt-1">
				Pick an image, size, and the resources to attach.
			</p>
		</div>

		<div class="space-y-6">
			<div class="bg-white rounded-xl border border-slate-200/70 shadow-sm p-6">
				<div class="grid grid-cols-2 gap-6">
					<div class="flex flex-col gap-2">
						<label class="text-sm font-medium text-slate-700">Name</label>
						<input
							v-model="form.name"
							type="text"
							placeholder="my-server"
							class="w-full rounded-lg border border-slate-300 px-3 py-2.5 outline-none focus:border-slate-800 focus:ring-2 focus:ring-slate-800/10 transition"
						>
					</div>
					<div class="flex flex-col gap-2">
						<label class="text-sm font-medium text-slate-700">Region</label>
						<select
							v-model="form.region"
							class="w-full rounded-lg border border-slate-300 px-3 py-2.5 bg-white outline-none focus:border-slate-800 focus:ring-2 focus:ring-slate-800/10 transition"
						>
							<option value="eu-cest-iasi">
								EU Central-East (Iasi)
							</option>
						</select>
					</div>
				</div>
			</div>

			<div class="bg-white rounded-xl border border-slate-200/70 shadow-sm p-6">
				<h2 class="font-semibold text-slate-900 mb-4">
					OS Image
				</h2>
				<div class="grid grid-cols-4 gap-4">
					<button
						v-for="os in mainOsGrid"
						:key="os.id"
						type="button"
						:class="isMainSelected(os)
							? 'border-slate-800 bg-slate-50 ring-1 ring-slate-800'
							: 'border-slate-200 hover:border-slate-400'"
						class="border-2 rounded-xl p-6 flex flex-col items-center justify-center cursor-pointer transition-all gap-3"
						@click="chooseMain(os)"
					>
						<Icon
							:name="os.icon"
							class="text-3xl"
							:class="isMainSelected(os) ? 'text-slate-800' : 'text-slate-500'"
						/>
						<span class="font-medium text-sm">{{ os.name }}</span>
					</button>
				</div>

				<div
					v-if="appliedPresetLabel"
					class="mt-4 flex items-center gap-2 rounded-lg bg-yellow-50 border border-yellow-200 px-3 py-2 text-sm text-yellow-800"
				>
					<Icon
						name="solar:bolt-circle-bold"
						class="text-lg shrink-0"
					/>
					<span>
						Preconfigured: <span class="font-semibold">{{ appliedPresetLabel }}</span> — a startup
						script runs on first boot. Open the needed port in your security group.
					</span>
				</div>

				<button
					type="button"
					class="mt-4 inline-flex items-center gap-1.5 text-sm font-semibold text-yellow-600 hover:text-yellow-700"
					@click="showPicker = true"
				>
					<Icon name="solar:widget-add-outline" />
					Browse presets &amp; custom images
				</button>
			</div>

			<div class="bg-white rounded-xl border border-slate-200/70 shadow-sm p-6">
				<h2 class="font-semibold text-slate-900 mb-4">
					Configuration
				</h2>
				<div class="grid grid-cols-3 gap-4">
					<button
						v-for="flavor in flavorList"
						:key="flavor.id"
						type="button"
						:class="form.flavorName === flavor.flavor
							? 'border-slate-800 ring-1 ring-slate-800'
							: 'border-slate-200 hover:border-slate-400'"
						class="border-2 rounded-xl p-5 cursor-pointer transition-all text-left"
						@click="form.flavorName = flavor.flavor"
					>
						<p class="font-bold text-lg mb-1 text-slate-900">
							{{ flavor.name }}
						</p>
						<p class="text-sm text-slate-500">
							{{ flavor.cpu }} vCPU · {{ flavor.ram }} RAM · {{ flavor.disk }} disk
						</p>
					</button>
				</div>

				<div class="mt-6 flex flex-col gap-2 max-w-xs">
					<label class="text-sm font-medium text-slate-700">Root disk size (GB)</label>
					<input
						v-model.number="form.rootDiskGb"
						type="number"
						min="1"
						max="1024"
						:placeholder="`Default: ${selectedFlavorDisk} (flavor disk)`"
						class="w-full rounded-lg border border-slate-300 px-3 py-2.5 outline-none focus:border-slate-800 focus:ring-2 focus:ring-slate-800/10 transition"
					>
					<span class="text-xs text-slate-400">
						Leave blank to use the flavor's disk. Set a value to boot from a volume of that
						size instead (Ubuntu needs ≈ 5 GB or more).
					</span>
				</div>
			</div>

			<div class="bg-white rounded-xl border border-slate-200/70 shadow-sm p-6">
				<h2 class="font-semibold text-slate-900 mb-4">
					Resources
				</h2>
				<div class="grid grid-cols-3 gap-6">
					<div class="flex flex-col gap-2">
						<label class="text-sm font-medium text-slate-700">SSH Key</label>
						<select
							v-model="form.keypairId"
							class="w-full rounded-lg border border-slate-300 px-3 py-2.5 bg-white outline-none focus:border-slate-800 focus:ring-2 focus:ring-slate-800/10 transition"
						>
							<option
								:value="null"
								disabled
							>
								Select a keypair
							</option>
							<option
								v-for="kp in readyKeypairs"
								:key="kp.id"
								:value="kp.id"
							>
								{{ kp.name }}
							</option>
						</select>
						<NuxtLink
							v-if="readyKeypairs.length === 0"
							to="/keypairs"
							class="text-sm text-amber-600 hover:underline"
						>
							No synced keypairs — add one first
						</NuxtLink>
					</div>

					<div class="flex flex-col gap-2">
						<label class="text-sm font-medium text-slate-700">Subnet</label>
						<select
							v-model="form.subnetId"
							class="w-full rounded-lg border border-slate-300 px-3 py-2.5 bg-white outline-none focus:border-slate-800 focus:ring-2 focus:ring-slate-800/10 transition"
						>
							<option
								:value="null"
								disabled
							>
								Select a subnet
							</option>
							<option
								v-for="subnet in readySubnets"
								:key="subnet.id"
								:value="subnet.id"
							>
								{{ subnet.networkName }} / {{ subnet.name }} ({{ subnet.cidr }})
							</option>
						</select>
						<NuxtLink
							v-if="readySubnets.length === 0"
							to="/networks"
							class="text-sm text-amber-600 hover:underline"
						>
							No provisioned subnets — create a network first
						</NuxtLink>
					</div>

					<div class="flex flex-col gap-2">
						<label class="text-sm font-medium text-slate-700">Security Groups</label>
						<div class="border border-slate-300 rounded-lg p-2 bg-white max-h-32 overflow-y-auto space-y-1">
							<label
								v-for="sg in readySecurityGroups"
								:key="sg.id"
								class="flex items-center gap-2 cursor-pointer text-sm py-1 px-1 rounded hover:bg-slate-50"
							>
								<input
									v-model="form.securityGroupIds"
									type="checkbox"
									:value="sg.id"
								>
								{{ sg.name }}
							</label>
							<p
								v-if="readySecurityGroups.length === 0"
								class="text-sm text-slate-400 py-1 px-1"
							>
								None available
							</p>
						</div>
						<NuxtLink
							v-if="readySecurityGroups.length === 0"
							to="/security-groups"
							class="text-sm text-amber-600 hover:underline"
						>
							No synced security groups — create one first
						</NuxtLink>
					</div>
				</div>
			</div>

			<!-- public IP -->
			<div class="bg-white rounded-xl border border-slate-200/70 shadow-sm p-6">
				<label class="flex items-start gap-3 cursor-pointer">
					<input
						v-model="form.assignFloatingIp"
						type="checkbox"
						class="mt-1 h-4 w-4 rounded border-slate-300 text-slate-800 focus:ring-slate-800/20"
					>
					<span>
						<span class="font-semibold text-slate-900">Assign a public IP</span>
						<span class="block text-sm text-slate-500 mt-0.5">
							Allocates a floating IP from the external pool and attaches it once the
							instance is active — required for inbound SSH and to reach services from the
							internet. You can attach or detach one later on the Floating IPs page.
						</span>
					</span>
				</label>
			</div>

			<!-- storage -->
			<div class="bg-white rounded-xl border border-slate-200/70 shadow-sm p-6">
				<h2 class="font-semibold text-slate-900 mb-1">
					Storage
				</h2>
				<p class="text-sm text-slate-500 mb-4">
					Optional — add a new data disk and/or attach existing volumes.
				</p>
				<div class="grid grid-cols-2 gap-6">
					<div class="flex flex-col gap-2">
						<label class="text-sm font-medium text-slate-700">New data volume (GB)</label>
						<input
							v-model.number="form.dataVolumeSizeGb"
							type="number"
							min="1"
							max="1024"
							placeholder="e.g. 50 — leave blank for none"
							class="w-full rounded-lg border border-slate-300 px-3 py-2.5 outline-none focus:border-slate-800 focus:ring-2 focus:ring-slate-800/10 transition"
						>
						<span class="text-xs text-slate-400">Created and attached automatically once the VM is active.</span>
					</div>
					<div class="flex flex-col gap-2">
						<label class="text-sm font-medium text-slate-700">Attach existing volumes</label>
						<p
							v-if="form.count > 1"
							class="border border-slate-200 rounded-lg p-2 bg-slate-50 text-sm text-slate-400"
						>
							Unavailable when launching multiple instances — a volume attaches to one server.
						</p>
						<div
							v-else
							class="border border-slate-300 rounded-lg p-2 bg-white max-h-32 overflow-y-auto space-y-1"
						>
							<label
								v-for="vol in availableVolumes"
								:key="vol.id"
								class="flex items-center gap-2 cursor-pointer text-sm py-1 px-1 rounded hover:bg-slate-50"
							>
								<input
									v-model="form.attachVolumeIds"
									type="checkbox"
									:value="vol.id"
								>
								{{ vol.name }} ({{ vol.size_gb }} GB)
							</label>
							<p
								v-if="availableVolumes.length === 0"
								class="text-sm text-slate-400 py-1 px-1"
							>
								No available volumes
							</p>
						</div>
						<NuxtLink
							to="/volumes"
							class="text-sm text-slate-500 hover:underline"
						>
							Manage volumes
						</NuxtLink>
					</div>
				</div>
			</div>

			<!-- startup script -->
			<div class="bg-white rounded-xl border border-slate-200/70 shadow-sm p-6">
				<div class="flex items-center justify-between mb-1">
					<h2 class="font-semibold text-slate-900">
						Startup script
					</h2>
					<label class="inline-flex items-center gap-1.5 text-sm text-slate-600 hover:text-slate-900 cursor-pointer">
						<Icon name="solar:upload-minimalistic-outline" />
						Upload file
						<input
							type="file"
							accept=".sh,.yaml,.yml,.txt,text/*"
							class="hidden"
							@change="onScriptFile"
						>
					</label>
				</div>
				<p class="text-sm text-slate-500 mb-4">
					Optional — runs once on first boot via cloud-init. Paste a shell script
					(starting with <span class="font-mono">#!/bin/bash</span>) or cloud-config YAML.
				</p>
				<textarea
					v-model="form.userData"
					rows="6"
					placeholder="#!/bin/bash&#10;apt-get update -y&#10;apt-get install -y nginx"
					class="w-full rounded-lg border border-slate-300 px-3 py-2.5 font-mono text-sm outline-none focus:border-slate-800 focus:ring-2 focus:ring-slate-800/10 transition resize-y"
					@input="appliedPresetLabel = ''"
				/>
			</div>

			<div class="flex items-end justify-between pt-1">
				<p
					v-if="error"
					class="text-red-600 text-sm self-center"
				>
					{{ error }}
				</p>
				<span v-else />
				<div class="flex items-end gap-4">
					<div class="flex flex-col gap-1.5">
						<label class="text-sm font-medium text-slate-700">Instances</label>
						<input
							v-model.number="form.count"
							type="number"
							min="1"
							max="10"
							title="Launch up to 10 identical instances at once (named name-1, name-2, …)"
							class="w-24 rounded-lg border border-slate-300 px-3 py-3 outline-none focus:border-slate-800 focus:ring-2 focus:ring-slate-800/10 transition"
						>
					</div>
					<button
						:disabled="!canSubmit || submitting"
						class="inline-flex items-center gap-2 bg-yellow-400 hover:bg-yellow-300 disabled:opacity-50 disabled:cursor-not-allowed text-slate-900 font-semibold py-3 px-8 rounded-lg transition-all shadow-sm active:scale-[0.98]"
						@click="submit"
					>
						{{ submitting ? "Creating…" : "Create Instance" }}
					</button>
				</div>
			</div>
		</div>

		<!-- image picker modal -->
		<div
			v-if="showPicker"
			class="fixed inset-0 z-30 bg-slate-900/50 flex items-center justify-center p-4"
			@click.self="showPicker = false"
		>
			<div class="bg-white rounded-xl shadow-xl w-full max-w-3xl max-h-[80vh] flex flex-col">
				<div class="flex items-center justify-between px-6 py-4 border-b border-slate-200">
					<h2 class="text-lg font-bold text-slate-900">
						Choose an image
					</h2>
					<button
						class="text-slate-400 hover:text-slate-700"
						@click="showPicker = false"
					>
						<Icon
							name="solar:close-circle-outline"
							class="text-2xl"
						/>
					</button>
				</div>

				<div class="flex gap-1 px-6 pt-4">
					<button
						v-for="tab in pickerTabs"
						:key="tab.id"
						type="button"
						:class="pickerTab === tab.id ? 'bg-slate-800 text-white' : 'text-slate-600 hover:bg-slate-100'"
						class="px-4 py-2 rounded-lg text-sm font-medium transition-colors"
						@click="pickerTab = tab.id"
					>
						{{ tab.label }}
					</button>
				</div>

				<div class="p-6 overflow-y-auto">
					<!-- bare os -->
					<div
						v-if="pickerTab === 'os'"
						class="grid grid-cols-3 gap-3"
					>
						<button
							v-for="os in builtinOs"
							:key="os.id"
							type="button"
							class="border-2 border-slate-200 hover:border-slate-400 rounded-xl p-5 flex flex-col items-center justify-center gap-2 transition-all"
							@click="selectImage(os.image)"
						>
							<Icon
								:name="os.icon"
								class="text-3xl text-slate-600"
							/>
							<span class="font-medium text-sm">{{ os.name }}</span>
						</button>
					</div>

					<!-- preconfigured servers -->
					<div
						v-else-if="pickerTab === 'presets'"
						class="grid grid-cols-2 gap-3"
					>
						<button
							v-for="preset in presetCatalog"
							:key="preset.id"
							type="button"
							class="border-2 border-slate-200 hover:border-slate-400 rounded-xl p-5 flex items-start gap-3 text-left transition-all"
							@click="applyPreset(preset)"
						>
							<Icon
								:name="preset.icon"
								class="text-3xl text-slate-700 shrink-0"
							/>
							<div>
								<p class="font-semibold text-slate-900">
									{{ preset.name }}
								</p>
								<p class="text-xs text-slate-500 mt-0.5">
									{{ preset.hint }}
								</p>
								<p class="text-xs text-slate-400 mt-1">
									Ubuntu 24.04 · {{ preset.rootDiskGb }} GB disk
								</p>
							</div>
						</button>
					</div>

					<!-- custom images (own + public, never the bare builtins) -->
					<div
						v-else
						class="grid grid-cols-3 gap-3"
					>
						<button
							v-for="os in customImageList"
							:key="os.id"
							type="button"
							class="border-2 border-slate-200 hover:border-slate-400 rounded-xl p-5 flex flex-col items-center justify-center gap-2 transition-all"
							@click="selectImage(os.image)"
						>
							<Icon
								:name="os.icon"
								class="text-3xl text-slate-600"
							/>
							<span class="font-medium text-sm">{{ os.name }}</span>
						</button>
						<p
							v-if="customImageList.length === 0"
							class="col-span-3 text-sm text-slate-400 py-6 text-center"
						>
							No custom images yet. Import one on the Images page (and toggle it public to share it).
						</p>
					</div>
				</div>
			</div>
		</div>
	</div>
</template>

<script setup lang="ts">
import type { InstanceResponse, KeypairResponse, NetworkResponse, SecurityGroupResponse, VolumeResponse, ImageResponse } from "~/types/api";
import { useToastStore } from "~/stores/toast";

const api = useApi();
const toast = useToastStore();

// built-in public images (must exist in OpenStack/Glance)
const builtinOs = [
	{ id: "cirros", name: "CirrOS", icon: "simple-icons:linux", image: "cirros" },
	{ id: "ubuntu", name: "Ubuntu 24.04", icon: "logos:ubuntu", image: "ubuntu-24.04" },
];

const flavorList = [
	{ id: "tiny", name: "Tiny", cpu: 1, ram: "512MB", disk: "1GB", flavor: "m1.tiny" },
	{ id: "small", name: "Small", cpu: 1, ram: "2GB", disk: "20GB", flavor: "m1.small" },
	{ id: "medium", name: "Medium", cpu: 2, ram: "4GB", disk: "40GB", flavor: "m1.medium" },
];

const form = ref({
	name: "",
	region: "eu-cest-iasi",
	imageName: "cirros",
	flavorName: "m1.tiny",
	keypairId: null as number | null,
	subnetId: null as number | null,
	securityGroupIds: [] as number[],
	rootDiskGb: null as number | null,
	dataVolumeSizeGb: null as number | null,
	attachVolumeIds: [] as number[],
	userData: "",
	count: 1,
	assignFloatingIp: true,
});

// an existing volume can only attach to one server
watch(() => form.value.count, (n) => {
	if (n > 1) {
		form.value.attachVolumeIds = [];
	}
});

function onScriptFile(event: Event) {
	const file = (event.target as HTMLInputElement).files?.[0];
	if (!file) return;
	const reader = new FileReader();
	reader.onload = () => {
		form.value.userData = String(reader.result ?? "");
	};
	reader.readAsText(file);
}

const selectedFlavorDisk = computed(
	() => flavorList.find(f => f.flavor === form.value.flavorName)?.disk ?? "",
);

const error = ref("");
const submitting = ref(false);

const [{ data: keypairs }, { data: networks }, { data: securityGroups }, { data: volumes }, { data: customImages }] = await Promise.all([
	useAsyncData("keypairs", () => api<KeypairResponse[]>("/keypairs/")),
	useAsyncData("networks", () => api<NetworkResponse[]>("/networks/")),
	useAsyncData("security-groups", () => api<SecurityGroupResponse[]>("/security-groups/")),
	useAsyncData("volumes", () => api<VolumeResponse[]>("/volumes/")),
	useAsyncData("create-images", () => api<ImageResponse[]>("/images/?include_public=true")),
]);

// pick a distro logo from an image name so the OS grid stays pretty
function iconForImage(name: string): string {
	const n = name.toLowerCase();
	if (n.includes("ubuntu")) return "logos:ubuntu";
	if (n.includes("debian")) return "logos:debian";
	if (n.includes("arch")) return "simple-icons:archlinux";
	if (n.includes("fedora")) return "logos:fedora";
	if (n.includes("rocky")) return "simple-icons:rockylinux";
	if (n.includes("cirros")) return "simple-icons:linux";
	return "solar:gallery-outline";
}

// active custom images visible to this org
const activeCustomImages = computed(() =>
	(customImages.value ?? []).filter(i => i.status === "active" && i.openstack_image_id),
);
const customImageList = computed(() =>
	activeCustomImages.value.map(i => ({
		id: `img-${i.id}`, name: i.name, icon: iconForImage(i.name), image: `${i.name}-${i.id}`,
	})),
);

// preconfigured servers
const presetCatalog = [
	{
		id: "ollama",
		name: "Ollama",
		icon: "simple-icons:ollama",
		baseImage: "ubuntu-24.04",
		rootDiskGb: 25,
		hint: "LLM server — open port 11434 in your security group.",
		userData: `#!/bin/bash
set -e
curl -fsSL https://ollama.com/install.sh | sh
mkdir -p /etc/systemd/system/ollama.service.d
cat >/etc/systemd/system/ollama.service.d/override.conf <<'EOF'
[Service]
Environment="OLLAMA_HOST=0.0.0.0:11434"
EOF
systemctl daemon-reload
systemctl enable --now ollama
sleep 10
ollama pull llama3.2:1b
`,
	},
	{
		id: "wordpress",
		name: "WordPress",
		icon: "simple-icons:wordpress",
		baseImage: "ubuntu-24.04",
		rootDiskGb: 15,
		hint: "Served on port 80 — open it in your security group.",
		userData: `#!/bin/bash
set -e
apt-get update -y
apt-get install -y docker.io docker-compose-v2
systemctl enable --now docker
mkdir -p /opt/wordpress
cat >/opt/wordpress/compose.yaml <<'EOF'
services:
  db:
    image: mariadb:11
    restart: always
    environment:
      MARIADB_ROOT_PASSWORD: rootpass
      MARIADB_DATABASE: wordpress
      MARIADB_USER: wordpress
      MARIADB_PASSWORD: wordpress
    volumes:
      - db:/var/lib/mysql
  wordpress:
    image: wordpress:latest
    restart: always
    ports:
      - "80:80"
    environment:
      WORDPRESS_DB_HOST: db
      WORDPRESS_DB_USER: wordpress
      WORDPRESS_DB_PASSWORD: wordpress
      WORDPRESS_DB_NAME: wordpress
    depends_on:
      - db
volumes:
  db:
EOF
cd /opt/wordpress
docker compose up -d
`,
	},
];

// image-picker modal
const showPicker = ref(false);
const pickerTab = ref<"os" | "presets" | "custom">("os");
const pickerTabs = [
	{ id: "os", label: "Bare OS" },
	{ id: "presets", label: "Preconfigured servers" },
	{ id: "custom", label: "Custom images" },
] as const;
// non-empty while a preset startup script is applied
const appliedPresetLabel = ref("");

function selectImage(image: string) {
	form.value.imageName = image;
	if (appliedPresetLabel.value) {
		form.value.userData = "";
		appliedPresetLabel.value = "";
	}
	showPicker.value = false;
}

function applyPreset(preset: typeof presetCatalog[number]) {
	form.value.imageName = preset.baseImage;
	form.value.userData = preset.userData;
	form.value.rootDiskGb = preset.rootDiskGb;
	appliedPresetLabel.value = preset.name;
	showPicker.value = false;
}

// the main grid on the page = the two built-in OSes + the preconfigured servers
// (custom images like Debian/Arch live in the "Browse" modal instead)
type GridEntry
	= | { kind: "os"; id: string; name: string; icon: string; image: string }
		| { kind: "preset"; id: string; name: string; icon: string; preset: typeof presetCatalog[number] };

const mainOsGrid = computed<GridEntry[]>(() => [
	...builtinOs.map(o => ({ kind: "os" as const, id: o.id, name: o.name, icon: o.icon, image: o.image })),
	...presetCatalog.map(p => ({ kind: "preset" as const, id: p.id, name: p.name, icon: p.icon, preset: p })),
]);

function isMainSelected(entry: GridEntry): boolean {
	return entry.kind === "preset"
		? appliedPresetLabel.value === entry.name
		: form.value.imageName === entry.image && !appliedPresetLabel.value;
}

function chooseMain(entry: GridEntry) {
	if (entry.kind === "preset") {
		applyPreset(entry.preset);
	}
	else {
		selectImage(entry.image);
	}
}

// only resources that finished provisioning in OpenStack can be used
const readyKeypairs = computed(() => keypairs.value?.filter(kp => kp.openstack_name) ?? []);
const readySubnets = computed(() =>
	(networks.value ?? []).flatMap(net =>
		net.subnets
			.filter(s => s.openstack_subnet_id)
			.map(s => ({ ...s, networkName: net.name })),
	),
);
const readySecurityGroups = computed(() => securityGroups.value?.filter(sg => sg.openstack_id) ?? []);
// only unattached, available volumes can be attached at create time
const availableVolumes = computed(() => volumes.value?.filter(v => v.status === "available" && v.instance_id === null) ?? []);

const canSubmit = computed(() =>
	form.value.name.trim().length > 0
	&& form.value.keypairId !== null
	&& form.value.subnetId !== null
	&& form.value.securityGroupIds.length > 0,
);

async function submit() {
	error.value = "";
	submitting.value = true;
	try {
		await api<InstanceResponse[]>("/instances/", {
			method: "POST",
			body: {
				name: form.value.name.trim(),
				flavor_name: form.value.flavorName,
				image_name: form.value.imageName,
				keypair_id: form.value.keypairId,
				subnet_id: form.value.subnetId,
				security_group_ids: form.value.securityGroupIds,
				root_disk_gb: form.value.rootDiskGb || null,
				data_volume_size_gb: form.value.dataVolumeSizeGb || null,
				attach_volume_ids: form.value.attachVolumeIds,
				user_data: form.value.userData.trim() || null,
				count: form.value.count || 1,
				assign_floating_ip: form.value.assignFloatingIp,
			},
		});
		toast.success(form.value.count > 1 ? `Launching ${form.value.count} instances…` : "Launching instance…");
		await navigateTo("/");
	}
	catch (e: unknown) {
		const err = e as { data?: { detail?: string } };
		error.value = typeof err.data?.detail === "string" ? err.data.detail : "Failed to create instance";
		toast.error(error.value);
	}
	finally {
		submitting.value = false;
	}
}
</script>
