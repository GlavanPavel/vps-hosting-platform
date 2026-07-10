<template>
	<span
		class="inline-flex items-center gap-1.5 rounded-full px-2.5 py-1 text-xs font-semibold"
		:class="tone.badge"
	>
		<span
			class="h-1.5 w-1.5 rounded-full"
			:class="[tone.dot, tone.pulse ? 'animate-pulse' : '']"
		/>
		{{ status }}
	</span>
</template>

<script setup lang="ts">
// Maps an instance lifecycle status to a coloured pill.
const props = defineProps<{ status: string }>();

const map: Record<string, { badge: string; dot: string; pulse?: boolean }> = {
	"ACTIVE": { badge: "bg-green-100 text-green-700", dot: "bg-green-500" },
	"BUILD": { badge: "bg-blue-100 text-blue-700", dot: "bg-blue-500", pulse: true },
	"STARTING": { badge: "bg-blue-100 text-blue-700", dot: "bg-blue-500", pulse: true },
	"REBOOT": { badge: "bg-blue-100 text-blue-700", dot: "bg-blue-500", pulse: true },
	"STOPPING": { badge: "bg-orange-100 text-orange-700", dot: "bg-orange-500", pulse: true },
	"DELETING": { badge: "bg-orange-100 text-orange-700", dot: "bg-orange-500", pulse: true },
	"SHUTOFF": { badge: "bg-slate-100 text-slate-600", dot: "bg-slate-400" },
	"ERROR": { badge: "bg-red-100 text-red-700", dot: "bg-red-500" },
	// volume statuses
	"available": { badge: "bg-green-100 text-green-700", dot: "bg-green-500" },
	"in-use": { badge: "bg-blue-100 text-blue-700", dot: "bg-blue-500" },
	"creating": { badge: "bg-amber-100 text-amber-700", dot: "bg-amber-500", pulse: true },
	"attaching": { badge: "bg-amber-100 text-amber-700", dot: "bg-amber-500", pulse: true },
	"detaching": { badge: "bg-orange-100 text-orange-700", dot: "bg-orange-500", pulse: true },
	"deleting": { badge: "bg-orange-100 text-orange-700", dot: "bg-orange-500", pulse: true },
	// floating IP statuses (available / in-use share the volume tones above)
	"allocating": { badge: "bg-amber-100 text-amber-700", dot: "bg-amber-500", pulse: true },
	"associating": { badge: "bg-amber-100 text-amber-700", dot: "bg-amber-500", pulse: true },
	"disassociating": { badge: "bg-orange-100 text-orange-700", dot: "bg-orange-500", pulse: true },
	"releasing": { badge: "bg-orange-100 text-orange-700", dot: "bg-orange-500", pulse: true },
	// image statuses
	"active": { badge: "bg-green-100 text-green-700", dot: "bg-green-500" },
	"queued": { badge: "bg-amber-100 text-amber-700", dot: "bg-amber-500", pulse: true },
	"importing": { badge: "bg-amber-100 text-amber-700", dot: "bg-amber-500", pulse: true },
	"snapshotting": { badge: "bg-amber-100 text-amber-700", dot: "bg-amber-500", pulse: true },
};

const tone = computed(
	() => map[props.status] ?? { badge: "bg-slate-100 text-slate-600", dot: "bg-slate-400" },
);
</script>
