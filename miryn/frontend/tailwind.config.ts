import type { Config } from "tailwindcss";

const config: Config = {
  content: [
    "./app/**/*.{ts,tsx}",
    "./components/**/*.{ts,tsx}",
    "./lib/**/*.{ts,tsx}",
  ],
  theme: {
    extend: {
      colors: {
        void: "#040404",
        accent: "#c8b89a",
        secondary: "#7a7a7a",
        border: "rgba(255,255,255,0.07)",
      },
    },
  },
  plugins: [],
};

export default config;
