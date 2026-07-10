<template>
	<div class="bg-white rounded-xl border border-slate-200/70 shadow-sm p-5 flex items-center gap-4">
		<div
			class="h-12 w-12 rounded-xl flex items-center justify-center shrink-0"
			:class="iconBg"
		>
			<Icon
				:name="icon"
				class="text-2xl"
				:class="iconColor"
			/>
		</div>
		<div class="min-w-0">
			<p class="text-sm text-slate-500">
				{{ label }}
			</p>
			<p class="text-2xl font-bold text-slate-900 leading-tight">
				{{ value }}
			</p>
		</div>
	</div>
</template>

<script setup lang="ts">
defineProps<{
	label: string;
	value: string | number;
	icon: string;
	iconBg: string;
	iconColor: string;
}>();
</script>
