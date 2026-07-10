<template>
	<div class="flex h-screen w-screen bg-slate-50 font-sans text-slate-800">
		<aside class="w-64 bg-indigo-950 text-indigo-200 flex flex-col h-full shrink-0">
			<div class="h-[70px] flex items-center px-6 gap-3 border-b border-white/10">
				<div class="w-9 h-9 bg-indigo-400 rounded-lg flex items-center justify-center text-indigo-950 shrink-0 shadow-lg shadow-indigo-500/20">
					<Icon
						name="solar:shield-user-bold-duotone"
						class="text-xl"
					/>
				</div>
				<span class="font-extrabold text-lg tracking-wide text-white">
					Admin<span class="text-indigo-400">Console</span>
				</span>
			</div>

			<nav class="flex-1 px-3 py-5 space-y-1">
				<p class="px-3 pb-2 text-[11px] font-semibold uppercase tracking-wider text-indigo-400/70">
					Platform
				</p>
				<NuxtLink
					v-for="item in menuItems"
					:key="item.url"
					:to="item.url"
					class="flex items-center gap-3 rounded-lg px-3 py-2.5 text-sm font-medium transition-colors"
					:class="isActive(item.url)
						? 'bg-indigo-400 text-indigo-950 shadow-sm'
						: 'text-indigo-200 hover:bg-white/5 hover:text-white'"
				>
					<Icon
						:name="item.icon"
						class="text-lg"
					/>
					{{ item.title }}
				</NuxtLink>
			</nav>

			<div class="p-3 border-t border-white/10 space-y-1">
				<NuxtLink
					to="/"
					class="w-full flex items-center gap-3 rounded-lg px-3 py-2.5 text-sm font-medium text-indigo-200 hover:bg-white/5 hover:text-white transition-colors"
				>
					<Icon
						name="solar:arrow-left-outline"
						class="text-lg"
					/>
					Back to app
				</NuxtLink>
				<button
					class="w-full flex items-center gap-3 rounded-lg px-3 py-2.5 text-sm font-medium text-indigo-200 hover:bg-white/5 hover:text-white transition-colors"
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

		<div class="flex-1 flex flex-col overflow-hidden">
			<header class="h-[70px] bg-white border-b border-slate-200/70 flex items-center justify-between px-8 shrink-0">
				<h1 class="text-lg font-semibold text-slate-900">
					{{ title }}
				</h1>
				<div class="flex items-center gap-2.5">
					<span class="text-xs font-semibold bg-indigo-100 text-indigo-700 rounded-full px-2.5 py-1">
						ADMINISTRATOR
					</span>
					<span class="text-sm text-slate-600 max-w-[220px] truncate">{{ user?.email ?? "…" }}</span>
				</div>
			</header>

			<main class="flex-1 overflow-y-auto px-8 py-7">
				<div class="mx-auto max-w-6xl">
					<slot />
				</div>
			</main>
		</div>

		<ToastHost />
	</div>
</template>

<script setup lang="ts">
import { useRoute } from "vue-router";

const route = useRoute();
const { user, fetchUser, logout } = useAuth();

onMounted(() => {
	if (!user.value) fetchUser();
});

const menuItems = [
	{ title: "Overview", url: "/admin", icon: "solar:chart-square-outline" },
	{ title: "Organizations", url: "/admin/organizations", icon: "solar:buildings-2-outline" },
	{ title: "Users", url: "/admin/users", icon: "solar:users-group-rounded-outline" },
];

const titles: Record<string, string> = {
	"/admin": "Platform Overview",
	"/admin/organizations": "Organizations",
	"/admin/users": "Users",
};
const title = computed(() => titles[route.path] ?? "Admin");

function isActive(url: string): boolean {
	if (url === "/admin") return route.path === "/admin";
	return route.path.startsWith(url);
}
</script>
