/**
 * Miryn visual system — thought-wall compositions.
 *
 * The wall is the shared background plane. Each surface gets a named preset, so
 * a page asks for `preset="memory"` instead of hand-placing shapes with magic
 * offsets and guessing at opacities.
 *
 * Asymmetry is deliberate: every preset puts its heaviest element in one corner
 * and a light counterweight on the opposite diagonal, so the eye crosses the
 * surface rather than resting on a centred mass. Presets differ in *arrangement*,
 * not just in scale, which is what keeps five surfaces from looking like one.
 */

import type { ReactNode } from "react";
import { cn } from "@/lib/utils";
import { GROUND, PRESENCE, type VisualTone } from "./tokens";
import {
  ContourLines,
  ConversationMarks,
  InkGrain,
  ThreadLine,
  type ContourVariant,
  type MarksVariant,
  type ThreadVariant,
} from "./svg";

export type SurfaceName = "landing" | "auth" | "onboarding" | "memory" | "identity";

type Layer =
  | { asset: "contour"; variant: ContourVariant; at: string; presence: keyof typeof PRESENCE }
  | { asset: "marks"; variant: MarksVariant; at: string; presence: keyof typeof PRESENCE }
  | { asset: "thread"; variant: ThreadVariant; at: string; presence: keyof typeof PRESENCE };

/**
 * One preset per surface. The arrangement is the composition — changing a page's
 * preset changes where the weight sits, not just how big it is.
 */
const PRESETS: Record<SurfaceName, Layer[]> = {
  // Marketing: wide open drift weighted right, marks grounding the lower left.
  landing: [
    { asset: "contour", variant: "drift", at: "-top-16 -right-40 h-[520px] w-[760px]", presence: "present" },
    { asset: "marks", variant: "cluster", at: "-left-28 bottom-12 h-[200px] w-[480px]", presence: "muted" },
  ],

  // Auth: a centered contour and mirrored marks keep the background quiet and
  // balanced behind the single form column.
  auth: [
    { asset: "contour", variant: "drift", at: "top-1/2 left-1/2 h-[420px] w-[640px] -translate-x-1/2 -translate-y-1/2", presence: "whisper" },
    { asset: "marks", variant: "cluster", at: "top-1/2 left-1/2 h-[180px] w-[420px] -translate-x-1/2 -translate-y-1/2", presence: "whisper" },
  ],

  // Onboarding: a climb. The thread runs down the centre behind the steps;
  // contours and fragments stay at whisper so nothing competes with the step.
  onboarding: [
    { asset: "contour", variant: "ridge", at: "top-1/4 -right-24 h-[300px] w-[560px]", presence: "whisper" },
    { asset: "thread", variant: "ascent", at: "top-0 left-1/2 h-[380px] w-[200px] -translate-x-1/2", presence: "muted" },
    { asset: "marks", variant: "field", at: "bottom-0 -left-32 h-[280px] w-[480px]", presence: "whisper" },
  ],

  // Memory: fragments are the subject. The densest mark field leads from the
  // upper left; sediment contours and the through-line counter it lower right.
  memory: [
    { asset: "marks", variant: "field", at: "-top-12 -left-24 h-[400px] w-[620px]", presence: "present" },
    { asset: "contour", variant: "ridge", at: "bottom-0 -right-40 h-[280px] w-[520px]", presence: "whisper" },
    { asset: "thread", variant: "spine", at: "-top-10 -right-36 h-[300px] w-[220px]", presence: "muted" },
  ],

  // Identity: one self as a contour map. Concentric rings carry the weight right
  // of centre, the through-line descends past the header, marks stay sparse.
  identity: [
    { asset: "contour", variant: "pool", at: "top-8 -right-32 h-[440px] w-[440px]", presence: "present" },
    { asset: "thread", variant: "spine", at: "-top-16 -right-28 h-[320px] w-[220px]", presence: "muted" },
    { asset: "marks", variant: "cluster", at: "bottom-16 -left-20 h-[180px] w-[440px]", presence: "whisper" },
  ],
};

function renderLayer(layer: Layer, tone: VisualTone, key: string): ReactNode {
  const className = cn(layer.at, PRESENCE[layer.presence]);

  if (layer.asset === "contour") {
    return <ContourLines key={key} variant={layer.variant} tone={tone} className={className} />;
  }
  if (layer.asset === "marks") {
    return <ConversationMarks key={key} variant={layer.variant} tone={tone} className={className} />;
  }
  return <ThreadLine key={key} variant={layer.variant} tone={tone} className={className} />;
}

/**
 * Full-bleed background wall. Pass `pinned` for a viewport-fixed page backdrop
 * (landing) or omit it for a wall that scrolls with its section.
 */
export function ThoughtWall({
  preset = "landing",
  tone = "dark",
  pinned = false,
  className,
}: {
  preset?: SurfaceName;
  tone?: VisualTone;
  pinned?: boolean;
  className?: string;
}) {
  return (
    <div
      aria-hidden="true"
      className={cn(
        "pointer-events-none overflow-hidden",
        pinned ? "fixed inset-0" : "absolute inset-0",
        GROUND[tone],
        className,
      )}
    >
      <InkGrain />
      {PRESETS[preset].map((layer, i) => renderLayer(layer, tone, `${layer.asset}-${i}`))}
    </div>
  );
}

/**
 * A wall that carries content: used where a surface is a framed slab rather than
 * a full page (the split auth panel).
 */
export function ThoughtWallPanel({
  children,
  preset = "auth",
  tone = "dark",
  className,
}: {
  children?: ReactNode;
  preset?: SurfaceName;
  tone?: VisualTone;
  className?: string;
}) {
  return (
    <div className={cn("relative overflow-hidden", GROUND[tone], className)}>
      <ThoughtWall preset={preset} tone={tone} />
      <div className={cn("relative z-10", tone === "dark" ? "text-[var(--miryn-parchment)]" : "text-[var(--miryn-ink)]")}>
        {children}
      </div>
    </div>
  );
}
