<template>
	<header class="h-[70px] bg-white border-b border-slate-200/70 flex items-center justify-between px-8 shrink-0">
		<h1 class="text-lg font-semibold text-slate-900">
			{{ title }}
		</h1>

		<div
			ref="menuRef"
			class="relative"
		>
			<button
				class="flex items-center gap-2.5 rounded-full pl-1 pr-2.5 py-1 hover:bg-slate-100 transition-colors"
				@click="open = !open"
			>
				<span class="h-8 w-8 rounded-full bg-slate-800 text-white text-sm font-semibold flex items-center justify-center">
					{{ initials }}
				</span>
				<span class="text-sm text-slate-600 max-w-[180px] truncate">{{ user?.email ?? "…" }}</span>
				<Icon
					name="solar:alt-arrow-down-outline"
					class="text-slate-400 text-sm"
				/>
			</button>

			<div
				v-if="open"
				class="absolute right-0 mt-2 w-48 bg-white rounded-lg border border-slate-200 shadow-lg py-1 z-20"
			>
				<div class="px-3 py-2 text-xs text-slate-400 border-b border-slate-100 truncate">
					{{ user?.email }}
				</div>
				<button
					class="w-full text-left px-3 py-2 text-sm text-slate-700 hover:bg-slate-50 flex items-center gap-2 transition-colors"
					@click="logout"
				>
					<Icon name="solar:logout-2-outline" />
					Log out
				</button>
			</div>
		</div>
	</header>
</template>

<script setup lang="ts">
import { useRoute } from "vue-router";

const route = useRoute();
const { user, fetchUser, logout } = useAuth();

onMounted(() => {
	if (!user.value) fetchUser();
});

const titles: Record<string, string> = {
	"/": "Dashboard",
	"/create": "Create Instance",
	"/volumes": "Volumes",
	"/images": "Images",
	"/networks": "Networks",
	"/floating-ips": "Floating IPs",
	"/security-groups": "Security Groups",
	"/keypairs": "SSH Keys",
	"/team": "Team",
	"/usage": "Usage",
};

const title = computed(() => {
	if (route.path.startsWith("/instances/")) return "Instance Details";
	return titles[route.path] ?? "CloudVPS";
});

const initials = computed(() => {
	const email = user.value?.email ?? "";
	return email.slice(0, 2).toUpperCase() || "?";
});

// dropdown open state + close on outside click
const open = ref(false);
const menuRef = ref<HTMLElement | null>(null);

function onDocClick(e: MouseEvent) {
	if (menuRef.value && !menuRef.value.contains(e.target as Node)) open.value = false;
}
onMounted(() => document.addEventListener("click", onDocClick));
onUnmounted(() => document.removeEventListener("click", onDocClick));
</script>
