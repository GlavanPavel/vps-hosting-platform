<template>
	<div class="flex h-screen w-screen bg-slate-50 font-sans text-slate-800">
		<AppSidebar />

		<div class="flex-1 flex flex-col overflow-hidden">
			<AppHeader />

			<main class="flex-1 overflow-y-auto px-8 py-7">
				<div class="mx-auto max-w-6xl">
					<slot />
				</div>
			</main>
		</div>

		<ToastHost />
	</div>
</template>
