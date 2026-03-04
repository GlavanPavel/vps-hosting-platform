<template>
	<aside class="w-58 bg-slate-800 text-white flex flex-col justify-between h-full">
		<div>
			<NuxtLink
				to="/"
				class="h-24 flex items-center px-8 gap-4 border-b border-white/10"
			>
				<div class="w-10 h-10 bg-yellow-400 rounded-lg flex items-center justify-center text-slate-900 shrink-0 shadow-lg shadow-yellow-400/20">
					<Icon
						name="solar:server-square-bold-duotone"
						class="text-2xl"
					/>
				</div>
				<span class="font-extrabold text-xl tracking-wide whitespace-nowrap text-white">
					Cloud<span class="text-yellow-400">VPS</span>
				</span>
			</NuxtLink>

			<nav class="flex flex-col mt-4">
				<NuxtLink
					v-for="(item, index) in menuItems"
					:key="index"
					:to="item.url"
					class="flex items-center py-3 px-4 font-medium transition-colors"
					active-class="bg-yellow-400 text-black"
					exact-active-class="bg-yellow-400 text-black"
					:class="[$route.path === item.url ? '' : 'text-gray-300 hover:bg-gray-800 hover:text-white']"
				>
					<Icon
						v-if="item.icon"
						:name="item.icon"
						class="text-xl"
					/>
					{{ item.title }}
				</NuxtLink>
			</nav>
		</div>

		<div class="p-5 border-t border-white/10 flex justify-start">
			<button class="flex items-center gap-2 text-yellow-400 hover:text-yellow-300 text-sm font-medium transition-colors">
				<Icon
					name="solar:logout-2-outline"
					class="text-lg"
				/>
				Log out
			</button>
		</div>
	</aside>
</template>

<script setup>
import { useRoute } from "vue-router";

const $route = useRoute();

const menuItems = [
	{ title: "Dashboard", url: "/", icon: "" },
	{ title: "Volumes", url: "/volumes", icon: "" },
	{ title: "Monitoring", url: "/monitoring", icon: "" },
	{ title: "Settings", url: "/settings", icon: "" },
];
</script>
