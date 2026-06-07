import js from "@eslint/js"

export default [
  {
    ignores: [
      "dist/**",
      "node_modules/**",
      "src/**/*.{ts,tsx}",
      "vite.config.ts",
    ],
  },
  {
    files: ["**/*.{js,mjs,cjs}"],
    ...js.configs.recommended,
  },
]
