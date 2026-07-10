<template>
	<div class="fixed bottom-5 right-5 z-50 flex flex-col gap-2.5 w-80">
		<TransitionGroup name="toast">
			<div
				v-for="t in toasts"
				:key="t.id"
				class="flex items-start gap-3 rounded-xl border shadow-lg px-4 py-3 bg-white"
				:class="tone(t.type).border"
			>
				<Icon
					:name="tone(t.type).icon"
					class="text-xl shrink-0 mt-0.5"
					:class="tone(t.type).color"
				/>
				<p class="text-sm text-slate-700 flex-1 break-words">
					{{ t.message }}
				</p>
				<button
					class="text-slate-300 hover:text-slate-600 transition-colors shrink-0"
					@click="store.remove(t.id)"
				>
					<Icon
						name="solar:close-circle-outline"
						class="text-lg"
					/>
				</button>
			</div>
		</TransitionGroup>
	</div>
</template>

<script setup lang="ts">
import { storeToRefs } from "pinia";
import { useToastStore } from "~/stores/toast";
import type { ToastType } from "~/stores/toast";

const store = useToastStore();
const { toasts } = storeToRefs(store);

function tone(type: ToastType) {
	switch (type) {
		case "success":
			return { border: "border-emerald-200", color: "text-emerald-500", icon: "solar:check-circle-outline" };
		case "error":
			return { border: "border-red-200", color: "text-red-500", icon: "solar:danger-triangle-outline" };
		default:
			return { border: "border-slate-200", color: "text-slate-500", icon: "solar:info-circle-outline" };
	}
}
</script>

<style scoped>
.toast-enter-active,
.toast-leave-active {
	transition: all 0.25s ease;
}
.toast-enter-from,
.toast-leave-to {
	opacity: 0;
	transform: translateX(1rem);
}
</style>
