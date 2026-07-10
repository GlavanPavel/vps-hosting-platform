<template>
	<div class="bg-white rounded-xl border border-slate-200/70 shadow-sm p-5">
		<div class="flex items-baseline justify-between mb-2">
			<p class="text-sm font-medium text-slate-600">
				{{ label }}
			</p>
			<p class="text-sm text-slate-900 font-semibold tabular-nums">
				{{ used }} / {{ total }} {{ unit }}
				<span class="text-slate-400 font-normal ml-1">({{ pct }}%)</span>
			</p>
		</div>
		<div class="h-3 w-full rounded-full bg-slate-100 overflow-hidden">
			<div
				class="h-full rounded-full transition-all"
				:class="barColor"
				:style="{ width: `${pct}%` }"
			/>
		</div>
	</div>
</template>

<script setup lang="ts">
const props = defineProps<{
	label: string;
	used: number;
	total: number;
	unit: string;
}>();

const pct = computed(() => {
	if (!props.total || props.total <= 0) return 0;
	return Math.min(100, Math.round((props.used / props.total) * 100));
});

// green under load, amber when filling up, red when nearly full
const barColor = computed(() => {
	if (pct.value >= 90) return "bg-red-500";
	if (pct.value >= 70) return "bg-amber-500";
	return "bg-emerald-500";
});
</script>
