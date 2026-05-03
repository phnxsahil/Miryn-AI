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
        void: "#09090e",
        surface: "#0f0f17",
        card: "#14141f",
        glass: "rgba(255, 255, 255, 0.06)",
        accent: {
          DEFAULT: "#c8b8ff",
          glow: "rgba(200, 184, 255, 0.15)",
          muted: "rgba(200, 184, 255, 0.2)",
          beta: "#5c5280",
        },
        primary: "#eef2ff",
        muted: "#9ca3bb",
        dim: "#66708b",
        ghost: "#48506a",
        border: {
          DEFAULT: "rgba(255,255,255,0.08)",
          hover: "rgba(255,255,255,0.12)",
        },
      },
      fontSize: {
        'xs': ['0.8125rem', { lineHeight: '1.25rem' }],
        'sm': ['0.9375rem', { lineHeight: '1.5rem' }],
        'base': ['1.0625rem', { lineHeight: '1.625rem' }],
        'lg': ['1.1875rem', { lineHeight: '1.75rem' }],
        'xl': ['1.3125rem', { lineHeight: '1.875rem' }],
      },
      fontFamily: {
        ui: ["var(--font-space-grotesk)", "sans-serif"],
        editorial: ["var(--font-eb-garamond)", "serif"],
        mono: ["var(--font-jetbrains-mono)", "monospace"],
      },
    },
  },
  plugins: [],
};

export default config;
