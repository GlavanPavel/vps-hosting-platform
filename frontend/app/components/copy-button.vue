<template>
	<button
		type="button"
		class="inline-flex items-center gap-1.5 text-slate-400 hover:text-slate-700 transition-colors"
		:title="copied ? 'Copied!' : 'Copy to clipboard'"
		@click="copy"
	>
		<Icon
			:name="copied ? 'solar:check-circle-bold' : 'solar:copy-outline'"
			class="text-base"
			:class="copied ? 'text-green-500' : ''"
		/>
		<span
			v-if="withLabel"
			class="text-xs font-medium"
		>{{ copied ? "Copied" : label }}</span>
	</button>
</template>

<script setup lang="ts">
const props = withDefaults(
	defineProps<{ text: string; withLabel?: boolean; label?: string }>(),
	{ withLabel: false, label: "Copy" },
);

const copied = ref(false);

async function copy() {
	try {
		await navigator.clipboard.writeText(props.text);
		copied.value = true;
		setTimeout(() => (copied.value = false), 1500);
	}
	catch {
		// clipboard API unavailable (e.g. non-https) — silently ignore
	}
}
</script>
