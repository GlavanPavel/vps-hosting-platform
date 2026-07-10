<template>
	<span
		class="inline-flex items-center gap-1.5 rounded-full px-2.5 py-1 text-xs font-semibold"
		:class="synced ? 'bg-green-100 text-green-700' : 'bg-yellow-100 text-yellow-700'"
	>
		<span
			class="h-1.5 w-1.5 rounded-full"
			:class="synced ? 'bg-green-500' : 'bg-yellow-500 animate-pulse'"
		/>
		{{ synced ? syncedLabel : pendingLabel }}
	</span>
</template>

<script setup lang="ts">
// Reflects whether a resource has finished provisioning in OpenStack.
withDefaults(
	defineProps<{ synced: boolean; syncedLabel?: string; pendingLabel?: string }>(),
	{ syncedLabel: "Synced", pendingLabel: "Pending" },
);
</script>
