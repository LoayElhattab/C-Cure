import type { Config } from "tailwindcss";

export default {
  darkMode: 'class',  // ← added this line
  content: ["./src/**/*.{html,js,svelte,ts}"],

  theme: {
    extend: {}
  },

  plugins: []
} as Config;