<template>
	<div class="h-full flex flex-col">
		<h1 class="text-3xl text-gray-800 mb-12 tracking-wide">
			Dashboard
		</h1>

		<div class="text-gray-800 space-y-5 mb-auto text-lg">
			<p>Summary</p>
			<p>1 instance</p>
			<p>No images</p>
			<p>1 volume</p>
		</div>

		<div class="flex-1 flex items-center justify-center pb-32">
			<NuxtLink
				to="/create"
				class="bg-slate-800 hover:bg-slate-700 text-yellow-400 py-3 px-6 rounded-md transition-colors text-lg font-medium"
			>
				Create New Instance
			</NuxtLink>
		</div>
	</div>
</template>
