import { defineStore } from "pinia";
import type { UserResponse } from "~/types/api";

export const useUserStore = defineStore("user", () => {
	const user = ref<UserResponse | null>(null);

	const isAuthenticated = computed(() => !!user.value);
	const isOwner = computed(() => user.value?.role === "owner");
	const isAdmin = computed(() => user.value?.role === "admin");

	function can(permission: string): boolean {
		return user.value?.permissions?.includes(permission) ?? false;
	}

	async function login(email: string, password: string): Promise<void> {
		user.value = await useApi()<UserResponse>("/auth/login", {
			method: "POST",
			body: { email, password },
		});
	}

	async function register(email: string, password: string, organizationName: string): Promise<void> {
		await useApi()<UserResponse>("/auth/register", {
			method: "POST",
			body: { email, password, organization_name: organizationName },
		});
	}

	async function fetchUser(): Promise<void> {
		try {
			user.value = await useApi()<UserResponse>("/auth/me");
		}
		catch {
			user.value = null;
		}
	}

	async function logout(): Promise<void> {
		try {
			await useApi()("/auth/logout", { method: "POST" });
		}
		catch {
			// clear local state even if the network call fails
		}
		user.value = null;
		await navigateTo("/login");
	}

	return { user, isAuthenticated, isOwner, isAdmin, can, login, register, fetchUser, logout };
});
