import type { Config } from "tailwindcss";
import typography from "@tailwindcss/typography";

/**
 * Miryn's shared UI palette follows the Framer landing page in both themes.
 */
const miryn = {
  warmBlack: "rgb(var(--theme-bg-rgb) / <alpha-value>)",
  ink: "rgb(var(--theme-text-rgb) / <alpha-value>)",
  surface: "rgb(var(--theme-surface-rgb) / <alpha-value>)",
  card: "rgb(var(--theme-card-rgb) / <alpha-value>)",
  border: "rgb(var(--theme-border-rgb) / <alpha-value>)",
  moss: "rgb(var(--theme-accent-rgb) / <alpha-value>)",
  mossLight: "rgb(var(--theme-accent-strong-rgb) / <alpha-value>)",
  yellow: "#fee435",
  lavender: "#c8d4b6",
  olive: "#61724f",
  parchment: "rgb(var(--theme-text-rgb) / <alpha-value>)",
  parchmentMuted: "rgb(var(--theme-muted-rgb) / <alpha-value>)",
};

const config: Config = {
  content: [
    "./pages/**/*.{js,ts,jsx,tsx,mdx}",
    "./components/**/*.{js,ts,jsx,tsx,mdx}",
    "./app/**/*.{js,ts,jsx,tsx,mdx}",
  ],
  theme: {
    extend: {
      colors: {
        void: miryn.warmBlack,
        card: miryn.card,
        surface: miryn.surface,
        yellowCta: miryn.yellow,
        accent: {
          DEFAULT: miryn.moss,
          beta: miryn.olive,
          yellow: miryn.yellow,
        },
        lavender: miryn.lavender,
        primary: miryn.parchment,
        dim: "rgb(var(--theme-dim-rgb) / <alpha-value>)",
        muted: "rgb(var(--theme-muted-rgb) / <alpha-value>)",
        success: "#a3d9a5",
        warning: "#fee435",
        danger: "#e24b4a",
        moss: miryn.moss,
        "moss-light": miryn.mossLight,
        olive: miryn.olive,
        parchment: miryn.parchment,
        "parchment-muted": miryn.parchmentMuted,
        ink: miryn.ink,
        rule: miryn.border,
        wall: miryn.warmBlack,
        wallSurface: miryn.surface,
        wallCard: miryn.card,
      },
      fontFamily: {
        ui: ["Onest", "system-ui", "sans-serif"],
        editorial: ["Gambarino", "Georgia", '"Times New Roman"', "serif"],
        mono: ['"Fragment Mono"', "ui-monospace", "SFMono-Regular", "Menlo", "monospace"],
      },
      backgroundImage: {
        "gradient-radial": "radial-gradient(var(--tw-gradient-stops))",
        "gradient-conic":
          "conic-gradient(from 180deg at 50% 50%, var(--tw-gradient-stops))",
      },
    },
  },
  plugins: [
    typography,
  ],
};

export default config;
