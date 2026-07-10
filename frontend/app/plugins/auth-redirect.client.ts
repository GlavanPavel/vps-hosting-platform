import { useUserStore } from "~/stores/user";

// When a session ends mid-use (the refresh token expired/was revoked, so useApi()
// cleared the user), bounce to /login. Living in a plugin — rather than in useApi() —
// keeps navigation out of route-middleware execution. Client-only; there is no SSR.
export default defineNuxtPlugin(() => {
	const store = useUserStore();
	const router = useRouter();
	const publicPages = ["/login", "/register"];

	watch(() => store.user, (current, previous) => {
		// only react to an authenticated → logged-out transition
		if (previous && !current && !publicPages.includes(router.currentRoute.value.path)) {
			navigateTo("/login");
		}
	});
});
