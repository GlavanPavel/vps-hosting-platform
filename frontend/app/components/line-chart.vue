<template>
	<div class="bg-white rounded-xl border border-slate-200/70 shadow-sm p-5">
		<div class="flex items-baseline justify-between mb-3">
			<h3 class="text-sm font-medium text-slate-500">
				{{ title }}
			</h3>
			<p class="text-lg font-bold text-slate-900">
				{{ currentLabel }}<span class="text-sm font-medium text-slate-400 ml-1">{{ unit }}</span>
			</p>
		</div>

		<div
			v-if="series.length < 2"
			class="h-[160px] flex items-center justify-center text-sm text-slate-400"
		>
			Not enough data yet
		</div>

		<div
			v-else
			class="relative"
			style="height: 160px"
		>
			<svg
				viewBox="0 0 600 160"
				class="w-full block"
				style="height: 160px"
				preserveAspectRatio="none"
				@mousemove="onMove"
				@mouseleave="hoverIndex = null"
			>
				<line
					v-for="g in 3"
					:key="g"
					x1="0"
					x2="600"
					:y1="g * 40"
					:y2="g * 40"
					stroke="#f1f5f9"
					stroke-width="1"
					vector-effect="non-scaling-stroke"
				/>
				<polygon
					:points="areaPoints"
					:fill="color"
					fill-opacity="0.1"
				/>
				<polyline
					:points="linePoints"
					fill="none"
					:stroke="color"
					stroke-width="2"
					vector-effect="non-scaling-stroke"
					stroke-linejoin="round"
					stroke-linecap="round"
				/>
				<!-- vertical guide at the hovered point -->
				<line
					v-if="hoverIndex !== null"
					:x1="px(hoverIndex)"
					:x2="px(hoverIndex)"
					y1="0"
					y2="160"
					stroke="#94a3b8"
					stroke-width="1"
					stroke-dasharray="3 3"
					vector-effect="non-scaling-stroke"
				/>
			</svg>

			<!-- marker dot (HTML, so it stays round despite the stretched SVG) -->
			<div
				v-if="hoverIndex !== null"
				class="absolute w-2.5 h-2.5 rounded-full border-2 border-white shadow"
				:style="{ left: `${hoverPxX}px`, top: `${hoverPxY}px`, background: color, transform: 'translate(-50%, -50%)' }"
			/>

			<!-- tooltip -->
			<div
				v-if="hoverIndex !== null"
				class="absolute pointer-events-none bg-slate-900 text-white rounded-md px-2.5 py-1.5 text-xs whitespace-nowrap shadow-lg z-10"
				:style="{ left: `${hoverPxX}px`, top: `${hoverPxY}px`, transform: 'translate(-50%, -135%)' }"
			>
				<div
					v-if="labels && labels[hoverIndex]"
					class="text-[11px] text-slate-300 mb-0.5"
				>
					{{ labels[hoverIndex] }}
				</div>
				<div class="font-semibold">
					{{ fmt(series[hoverIndex]) }}<span class="text-slate-300 font-normal">{{ unit ? ` ${unit}` : "" }}</span>
				</div>
			</div>
		</div>
	</div>
</template>

<script setup lang="ts">
const props = withDefaults(
	defineProps<{
		series: number[];
		title: string;
		unit?: string;
		color?: string;
		yMin?: number;
		yMax?: number;
		labels?: string[];
	}>(),
	{ unit: "", color: "#0ea5e9" },
);

const W = 600;
const H = 160;
const pad = 14;

// fixed axis when yMin/yMax are given (e.g. 0–N vCPU), otherwise auto-scale
const min = computed(() => props.yMin ?? Math.min(...props.series));
const max = computed(() => props.yMax ?? Math.max(...props.series));

// position in viewBox coordinates (0–600 × 0–160)
function px(i: number): number {
	return props.series.length <= 1 ? 0 : (i / (props.series.length - 1)) * W;
}
function py(v: number): number {
	const span = max.value - min.value || 1;
	return H - pad - ((v - min.value) / span) * (H - pad * 2);
}

const linePoints = computed(() =>
	props.series.map((v, i) => `${px(i).toFixed(1)},${py(v).toFixed(1)}`).join(" "),
);
const areaPoints = computed(() => `0,${H} ${linePoints.value} ${W},${H}`);

function fmt(v: number): string {
	return Number.isInteger(v) ? v.toString() : v.toFixed(1);
}
const currentLabel = computed(() => fmt(props.series.at(-1) ?? 0));

// ── hover state ───────────────────────────────────────────────────────────────
const hoverIndex = ref<number | null>(null);
const hoverPxX = ref(0); // pixels within the chart box
const hoverPxY = ref(0);

function onMove(e: MouseEvent) {
	const n = props.series.length;
	if (n < 2) return;
	const rect = (e.currentTarget as SVGElement).getBoundingClientRect();
	const frac = Math.min(1, Math.max(0, (e.clientX - rect.left) / rect.width));
	const idx = Math.round(frac * (n - 1));
	hoverIndex.value = idx;
	// snap horizontally to the data point; vertical viewBox is 1:1 with px (height 160)
	hoverPxX.value = (idx / (n - 1)) * rect.width;
	hoverPxY.value = py(props.series[idx]);
}
</script>
