export default defineNuxtRouteMiddleware(async () => {
	const { user, fetchUser, isAdmin } = useAuth();
	if (!user.value) await fetchUser();
	if (!isAdmin.value) return navigateTo("/");
});
