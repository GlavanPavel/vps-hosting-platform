// https://nuxt.com/docs/api/configuration/nuxt-config
export default defineNuxtConfig({
	modules: ["@nuxt/eslint", "@nuxtjs/tailwindcss", "@nuxt/icon", "@pinia/nuxt"],
	ssr: false,
	devtools: { enabled: true },
	runtimeConfig: {
		public: {
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
