import { useUserStore } from "~/stores/user";

let refreshInFlight: Promise<boolean> | null = null;
const NO_RETRY = ["/auth/login", "/auth/register", "/auth/refresh", "/auth/logout"];

export function useApi() {
	const config = useRuntimeConfig();
	const store = useUserStore();

	function refreshToken(): Promise<boolean> {
		if (!refreshInFlight) {
			refreshInFlight = $fetch("/auth/refresh", {
				baseURL: config.public.apiBase,
				method: "POST",
				credentials: "include",
			})
				.then(() => true)
				.catch(() => false)
				.finally(() => { refreshInFlight = null; });
		}
		return refreshInFlight;
	}

	return async <T>(request: string, opts: Record<string, unknown> = {}): Promise<T> => {
		const fetchOptions = {
			baseURL: config.public.apiBase,
			credentials: "include" as const,
			...opts,
		};
		const noRetry = typeof request === "string" && NO_RETRY.some(p => request.startsWith(p));
		try {
			return await $fetch<T>(request, fetchOptions);
		}
		catch (e: unknown) {
			const status = (e as { response?: { status?: number } })?.response?.status;
			if (status === 401 && !noRetry) {
				// access token expired → refresh once and retry the original request
				if (await refreshToken()) {
					return await $fetch<T>(request, fetchOptions);
				}
				// refresh failed → the session is truly over; the auth-redirect plugin
				// watches the store and bounces to /login when user becomes null
				store.user = null;
			}
			throw e;
		}
	};
}
