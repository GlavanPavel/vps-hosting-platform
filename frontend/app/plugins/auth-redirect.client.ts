import { useUserStore } from "~/stores/user";

// When a session ends mid-use send to /login
export default defineNuxtPlugin(() => {
	const store = useUserStore();
	const router = useRouter();
	const publicPages = ["/login", "/register"];

	watch(() => store.user, (current, previous) => {
		if (previous && !current && !publicPages.includes(router.currentRoute.value.path)) {
			navigateTo("/login");
		}
	});
});
