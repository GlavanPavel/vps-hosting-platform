<template>
	<div class="flex h-screen w-screen bg-gray-50 font-sans text-gray-800">
		<AppSidebar />

		<div class="flex-1 flex flex-col overflow-hidden">
			<AppHeader />

			<main class="flex-1 overflow-y-auto p-4">
				<slot />
			</main>
		</div>
	</div>
</template>
