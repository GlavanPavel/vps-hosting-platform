import { defineStore } from "pinia";

export type ToastType = "success" | "error" | "info";

export interface Toast {
	id: number;
	type: ToastType;
	message: string;
}

// Global, app-wide toast notifications (mirrors the reference project's
// notificationStore). Any component/page/store can push a toast; <ToastHost>
// (rendered in the layouts) displays them. Toasts auto-dismiss.
export const useToastStore = defineStore("toast", () => {
	const toasts = ref<Toast[]>([]);
	let seq = 0;

	function push(type: ToastType, message: string, timeout = 4000): number {
		const id = ++seq;
		toasts.value.push({ id, type, message });
		if (timeout > 0) setTimeout(() => remove(id), timeout);
		return id;
	}

	function remove(id: number): void {
		toasts.value = toasts.value.filter(t => t.id !== id);
	}

	const success = (message: string) => push("success", message);
	const error = (message: string) => push("error", message);
	const info = (message: string) => push("info", message);

	return { toasts, push, remove, success, error, info };
});
