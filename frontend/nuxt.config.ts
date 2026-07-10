// https://nuxt.com/docs/api/configuration/nuxt-config
export default defineNuxtConfig({
	modules: ["@nuxt/eslint", "@nuxtjs/tailwindcss", "@nuxt/icon", "@pinia/nuxt"],
	// SPA: this is an authenticated dashboard (no SEO need), and httpOnly auth cookies
	// + silent token refresh are far simpler/safer resolved entirely on the client.
	ssr: false,
	devtools: { enabled: true },
	runtimeConfig: {
		public: {
			// override with NUXT_PUBLIC_API_BASE
			apiBase: "http://localhost:8000",
		},
	},
	compatibilityDate: "2025-07-15",
	vite: {
		optimizeDeps: {
			include: [
				"@vue/devtools-core",
				"@vue/devtools-kit",
			],
		},
	},
	eslint: {
		config: {
			stylistic: {
				semi: true,
				quotes: "double",
				commaDangle: "always-multiline",
				indent: "tab",
			},
		},
	},
});
