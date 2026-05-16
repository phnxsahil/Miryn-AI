import type { Config } from "tailwindcss";
import typography from "@tailwindcss/typography";

const config: Config = {
  content: [
    "./pages/**/*.{js,ts,jsx,tsx,mdx}",
    "./components/**/*.{js,ts,jsx,tsx,mdx}",
    "./app/**/*.{js,ts,jsx,tsx,mdx}",
  ],
  theme: {
    extend: {
      colors: {
        void: "#0a0a0f",
        card: "#12121a",
        surface: "#0f0f17",
        accent: {
          DEFAULT: "#c8b8ff",
          beta: "#5c5280",
        },
        primary: "#ede9ff",
        dim: "#8b89a3",
        muted: "#4a4868",
        success: "#a3d9a5",
        warning: "#e2c08d",
        danger: "#e24b4a",
      },
      fontFamily: {
        ui: ["var(--font-space-grotesk)", "sans-serif"],
        editorial: ["var(--font-eb-garamond)", "serif"],
        mono: ["var(--font-jetbrains-mono)", "monospace"],
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
