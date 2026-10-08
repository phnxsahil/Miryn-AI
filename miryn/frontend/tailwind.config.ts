import type { Config } from "tailwindcss";
import typography from "@tailwindcss/typography";

/**
 * Miryn palette matching Framer design:
 * Dark background #0a0a0a, card #171717 / #141414, surface #1f1f1f, border rgba(255,255,255,0.08)
 * Yellow accent #fee435 (primary CTA), Moss green #a8bb94 / #65bf72 (memory/identity tags), Parchment #ece4d0
 */
const miryn = {
  warmBlack: "#0a0a0a",
  ink: "#f5f5f5",
  surface: "#141414",
  card: "#171717",
  border: "rgba(255, 255, 255, 0.08)",
  moss: "#a8bb94",
  mossLight: "#65bf72",
  yellow: "#fee435",
  lavender: "#c8d4b6",
  olive: "#61724f",
  parchment: "#ece4d0",
  parchmentMuted: "#a3a3a3",
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
        dim: "#737373",
        muted: "#a3a3a3",
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
        ui: [
          '"Inter"',
          "-apple-system",
          "BlinkMacSystemFont",
          '"SF Pro Display"',
          "system-ui",
          "sans-serif",
        ],
        editorial: ["Georgia", '"Times New Roman"', "serif"],
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
