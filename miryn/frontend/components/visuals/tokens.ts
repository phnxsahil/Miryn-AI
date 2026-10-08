/**
 * Miryn visual system — ink roles.
 *
 * The drawing color is resolved here, once, instead of being re-derived at every
 * call site. Every asset in this system paints with `currentColor`, so a caller
 * only has to pick an ink role and the SVG follows.
 *
 * Palette lives in styles/globals.css as CSS custom properties.
 */

export type VisualTone = "dark" | "light";

/** Stroke color for the background-plane drawings. */
export const INK: Record<VisualTone, string> = {
  dark: "text-[var(--miryn-moss)]",
  light: "text-[var(--miryn-olive)]",
};

/** The surface the drawings sit on. */
export const GROUND: Record<VisualTone, string> = {
  dark: "bg-[var(--miryn-warm-black)]",
  light: "bg-[var(--theme-bg)]",
};

/** Text color that belongs on that surface. */
export const FOREGROUND: Record<VisualTone, string> = {
  dark: "text-[var(--miryn-parchment)]",
  light: "text-[var(--miryn-ink)]",
};

/**
 * Art direction, not decoration: these drawings are the background plane and
 * must never compete with content. Three named stops keep sections consistent
 * instead of each one guessing at an opacity.
 */
export const PRESENCE = {
  whisper: "opacity-[0.22]",
  muted: "opacity-[0.34]",
  present: "opacity-[0.5]",
} as const;

export type Presence = keyof typeof PRESENCE;

export const SURFACE_PRESET: Record<string, string> = {
  landing: "landing",
  auth: "auth",
  onboarding: "onboarding",
  memory: "memory",
  identity: "identity",
};
