<template>
	<div class="min-h-screen flex items-center justify-center bg-gradient-to-br from-slate-900 to-slate-700 p-4">
		<div class="bg-white rounded-2xl shadow-2xl p-10 w-full max-w-md">
			<div class="flex items-center gap-3 mb-8 justify-center">
				<div class="w-11 h-11 bg-yellow-400 rounded-xl flex items-center justify-center text-slate-900 shadow-lg shadow-yellow-400/30">
					<Icon
						name="solar:server-square-bold-duotone"
						class="text-2xl"
					/>
				</div>
				<span class="font-extrabold text-2xl tracking-wide text-slate-800">
					Cloud<span class="text-yellow-500">VPS</span>
				</span>
			</div>

			<h1 class="text-xl font-semibold text-slate-900 mb-1 text-center">
				Create your account
			</h1>
			<p class="text-sm text-slate-500 mb-6 text-center">
				Spin up your own cloud organization
			</p>

			<form
				class="space-y-5"
				@submit.prevent="submit"
			>
				<div class="flex flex-col gap-2">
					<label class="text-sm font-medium text-slate-700">Organization name</label>
					<input
						v-model="organizationName"
						type="text"
						required
						placeholder="my-company"
						class="w-full rounded-lg border border-slate-300 px-3 py-2.5 outline-none focus:border-slate-800 focus:ring-2 focus:ring-slate-800/10 transition"
					>
				</div>
				<div class="flex flex-col gap-2">
					<label class="text-sm font-medium text-slate-700">Email</label>
					<input
						v-model="email"
						type="email"
						required
						placeholder="you@example.com"
						class="w-full rounded-lg border border-slate-300 px-3 py-2.5 outline-none focus:border-slate-800 focus:ring-2 focus:ring-slate-800/10 transition"
					>
				</div>
				<div class="flex flex-col gap-2">
					<label class="text-sm font-medium text-slate-700">Password</label>
					<input
						v-model="password"
						type="password"
						required
						minlength="8"
						placeholder="At least 8 characters"
						class="w-full rounded-lg border border-slate-300 px-3 py-2.5 outline-none focus:border-slate-800 focus:ring-2 focus:ring-slate-800/10 transition"
					>
				</div>

				<p
					v-if="error"
					class="text-red-600 text-sm"
				>
					{{ error }}
				</p>

				<button
					type="submit"
					:disabled="loading"
					class="w-full bg-yellow-400 hover:bg-yellow-300 disabled:opacity-60 text-slate-900 font-semibold py-3 rounded-lg transition-colors shadow-sm"
				>
					{{ loading ? "Creating account…" : "Create account" }}
				</button>
			</form>

			<p class="text-sm text-slate-500 mt-6 text-center">
				Already registered?
				<NuxtLink
					to="/login"
					class="text-slate-800 font-semibold hover:underline"
				>
					Sign in
				</NuxtLink>
			</p>
		</div>
	</div>
</template>

<script setup lang="ts">
definePageMeta({ layout: false });

const { register, login } = useAuth();

const organizationName = ref("");
const email = ref("");
const password = ref("");
const error = ref("");
const loading = ref(false);

async function submit() {
	error.value = "";
	loading.value = true;
	try {
		await register(email.value, password.value, organizationName.value);
		// log straight in after a successful registration
		await login(email.value, password.value);
		await navigateTo("/");
	}
	catch (e: unknown) {
		const err = e as { data?: { detail?: string } };
		error.value = err.data?.detail ?? "Registration failed — is the API running?";
	}
	finally {
		loading.value = false;
	}
}
</script>
