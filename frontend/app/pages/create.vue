<template>
	<div class="max-w-5xl">
		<h1 class="text-2xl font-semibold text-gray-800 mb-8">
			Create an instance
		</h1>

		<div class="space-y-10">
			<div class="grid grid-cols-2 gap-8">
				<div class="flex flex-col gap-2">
					<label class="font-medium text-gray-700">Name</label>
					<input
						v-model="form.name"
						type="text"
						placeholder="Add text"
						class="border border-slate-300 rounded-md p-2 outline-none focus:border-slate-800 transition-colors"
					>
				</div>
				<div class="flex flex-col gap-2">
					<label class="font-medium text-gray-700">Region</label>
					<select
						v-model="form.region"
						class="border border-slate-300 rounded-md p-2 outline-none bg-white focus:border-slate-800 transition-colors"
					>
						<option value="eu-cest-iasi">
							EU Central-East (Iasi)
						</option>
						<option value="eu-cest-trans">
							EU Central-East (Transnistria)
						</option>
					</select>
				</div>
			</div>

			<div>
				<div class="flex gap-6 border-b border-gray-200 mb-6">
					<button class="pb-2 border-b-2 border-slate-800 font-medium">
						OS Images
					</button>
					<button class="pb-2 text-gray-400 hover:text-gray-600 transition-colors">
						Custom images
					</button>
				</div>

				<div class="grid grid-cols-4 gap-4">
					<div
						v-for="os in osList"
						:key="os.id"
						:class="[form.os === os.id ? 'border-slate-800 bg-slate-50' : 'border-gray-200 hover:border-slate-400']"
						class="border-2 rounded-lg p-6 flex flex-col items-center justify-center cursor-pointer transition-all gap-3"
						@click="form.os = os.id"
					>
						<Icon
							:name="os.icon"
							class="text-3xl"
							:class="form.os === os.id ? 'text-slate-800' : 'text-gray-500'"
						/>
						<span class="font-medium">{{ os.name }}</span>
					</div>
				</div>
			</div>

			<div class="flex flex-col gap-2 w-1/3">
				<label class="font-medium text-gray-700">Version</label>
				<select
					v-model="form.version"
					class="border border-slate-300 rounded-md p-2 bg-white"
				>
					<option>Latest Stable</option>
					<option>LTS 22.04</option>
				</select>
			</div>

			<div>
				<h2 class="font-medium text-gray-700 mb-4 text-lg">
					Select Configuration
				</h2>
				<div class="grid grid-cols-3 gap-6">
					<div
						v-for="config in configList"
						:key="config.id"
						:class="[form.config === config.id ? 'border-slate-800 ring-1 ring-slate-800' : 'border-gray-200 hover:border-slate-400']"
						class="border-2 rounded-lg p-6 cursor-pointer transition-all"
						@click="form.config = config.id"
					>
						<p class="font-bold text-lg mb-1">
							{{ config.name }}
						</p>
						<p class="text-sm text-gray-600">
							{{ config.cpu }} vCPU
						</p>
						<p class="text-sm text-gray-600">
							{{ config.ram }} RAM
						</p>
					</div>
				</div>
			</div>

			<div class="flex flex-col gap-2 w-1/3">
				<label class="font-medium text-gray-700">SSH Key</label>
				<select
					v-model="form.sshKey"
					class="border border-slate-300 rounded-md p-2 bg-white"
				>
					<option>None</option>
					<option>my-laptop-key</option>
				</select>
			</div>

			<div class="flex items-end justify-between pt-6">
				<div class="flex flex-col gap-2 w-32">
					<label class="font-medium text-gray-700">Quantity</label>
					<input
						v-model="form.quantity"
						type="number"
						class="border border-slate-300 rounded-md p-2 outline-none"
					>
				</div>

				<button class="bg-yellow-400 hover:bg-yellow-500 text-slate-900 font-bold py-3 px-10 rounded-md transition-all shadow-md active:scale-95">
					Create Instance
				</button>
			</div>
		</div>
	</div>
</template>

<script setup>
const form = ref({
	name: "",
	region: "eu-central",
	os: "ubuntu",
	version: "Latest Stable",
	config: "small",
	sshKey: "None",
	quantity: 1,
});

const osList = [
	{ id: "cirros", name: "CirrOS", icon: "simple-icons:linux" },
	{ id: "ubuntu", name: "Ubuntu", icon: "logos:ubuntu" },
	{ id: "debian", name: "Debian", icon: "logos:debian" },
	{ id: "centos", name: "CentOS", icon: "logos:centos" },
];

const configList = [
	{ id: "tiny", name: "Tiny", cpu: 1, ram: "512MB" },
	{ id: "small", name: "Small", cpu: 1, ram: "1GB" },
	{ id: "medium", name: "Medium", cpu: 2, ram: "2GB" },
];
</script>
