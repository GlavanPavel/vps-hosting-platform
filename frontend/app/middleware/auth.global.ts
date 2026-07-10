import { useUserStore } from "~/stores/user";

const publicPages = ["/login", "/register"];

export default defineNuxtRouteMiddleware(async (to) => {
	const store = useUserStore();
	if (!store.user) await store.fetchUser();

	const authed = !!store.user;
	if (!authed && !publicPages.includes(to.path)) return navigateTo("/login");
	if (authed && publicPages.includes(to.path)) return navigateTo("/");
});
