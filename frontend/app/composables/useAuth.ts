import { storeToRefs } from "pinia";
import { useUserStore } from "~/stores/user";

export function useAuth() {
	const store = useUserStore();
	const { user, isAuthenticated, isOwner, isAdmin } = storeToRefs(store);

	return {
		user,
		isAuthenticated,
		isOwner,
		isAdmin,
		can: store.can,
		login: store.login,
		register: store.register,
		fetchUser: store.fetchUser,
		logout: store.logout,
	};
}
