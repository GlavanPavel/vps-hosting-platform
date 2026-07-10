<template>
	<aside class="w-64 bg-slate-900 text-slate-300 flex flex-col h-full shrink-0">
		<NuxtLink
			to="/"
			class="h-[70px] flex items-center px-6 gap-3 border-b border-white/5"
		>
			<div class="w-9 h-9 bg-yellow-400 rounded-lg flex items-center justify-center text-slate-900 shrink-0 shadow-lg shadow-yellow-400/20">
				<Icon
					name="solar:server-square-bold-duotone"
					class="text-xl"
				/>
			</div>
			<span class="font-extrabold text-lg tracking-wide text-white">
				Cloud<span class="text-yellow-400">VPS</span>
			</span>
		</NuxtLink>

		<nav class="flex-1 px-3 py-5 space-y-1">
			<p class="px-3 pb-2 text-[11px] font-semibold uppercase tracking-wider text-slate-500">
				Manage
			</p>
			<NuxtLink
				v-for="item in baseItems"
				:key="item.url"
				:to="item.url"
				class="flex items-center gap-3 rounded-lg px-3 py-2.5 text-sm font-medium transition-colors"
				:class="isActive(item.url)
					? 'bg-yellow-400 text-slate-900 shadow-sm'
					: 'text-slate-300 hover:bg-white/5 hover:text-white'"
			>
				<Icon
					:name="item.icon"
					class="text-lg"
				/>
				{{ item.title }}
			</NuxtLink>
		</nav>

		<div class="p-3 border-t border-white/5 space-y-1">
			<NuxtLink
				v-if="isAdmin"
				to="/admin"
				class="flex items-center gap-3 rounded-lg px-3 py-2.5 text-sm font-medium transition-colors"
				:class="isActive('/admin')
					? 'bg-yellow-400 text-slate-900 shadow-sm'
					: 'text-slate-300 hover:bg-white/5 hover:text-white'"
			>
				<Icon
					name="solar:shield-user-outline"
					class="text-lg"
				/>
				Admin Console
			</NuxtLink>
			<button
				class="w-full flex items-center gap-3 rounded-lg px-3 py-2.5 text-sm font-medium text-slate-300 hover:bg-white/5 hover:text-white transition-colors"
				@click="logout"
			>
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

const route = useRoute();
const { logout, isAdmin } = useAuth();

const baseItems = [
	{ title: "Dashboard", url: "/", icon: "solar:widget-5-outline" },
	{ title: "Create Instance", url: "/create", icon: "solar:add-square-outline" },
	{ title: "Volumes", url: "/volumes", icon: "solar:database-outline" },
	{ title: "Images", url: "/images", icon: "solar:gallery-outline" },
	{ title: "Networks", url: "/networks", icon: "solar:global-outline" },
	{ title: "Floating IPs", url: "/floating-ips", icon: "solar:point-on-map-outline" },
	{ title: "Security Groups", url: "/security-groups", icon: "solar:shield-keyhole-outline" },
	{ title: "SSH Keys", url: "/keypairs", icon: "solar:key-outline" },
	{ title: "Team", url: "/team", icon: "solar:users-group-rounded-outline" },
	{ title: "Usage", url: "/usage", icon: "solar:chart-2-outline" },
];

// the admin console link is rendered separately in the footer, just above Log out —
// only shown to a platform administrator (isAdmin)

function isActive(url) {
	// the instance detail page lives under the Dashboard section
	if (url === "/") return route.path === "/" || route.path.startsWith("/instances");
	return route.path.startsWith(url);
}
</script>
