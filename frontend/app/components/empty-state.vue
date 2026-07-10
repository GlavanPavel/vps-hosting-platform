<template>
	<div class="bg-white rounded-xl border border-dashed border-slate-300 p-12 text-center">
		<div class="mx-auto mb-4 h-14 w-14 rounded-full bg-slate-100 flex items-center justify-center">
			<Icon
				:name="icon"
				class="text-3xl text-slate-400"
			/>
		</div>
		<p class="font-medium text-slate-700">
			{{ title }}
		</p>
		<p
			v-if="description"
			class="text-sm text-slate-500 mt-1"
		>
			{{ description }}
		</p>
		<div
			v-if="$slots.default"
			class="mt-5 flex justify-center"
		>
			<slot />
		</div>
	</div>
</template>

<script setup lang="ts">
defineProps<{ icon: string; title: string; description?: string }>();
</script>
