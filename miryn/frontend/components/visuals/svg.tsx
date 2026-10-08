/**
 * Miryn visual system — local SVG assets.
 *
 * Hand-drawn contour lines, fragmented conversation marks, a through-line and an
 * ink grain. Everything is inline SVG that paints with `currentColor`, so there
 * are no image requests, no icon dependency and no theme-specific duplicates.
 *
 * Performance rules this file follows:
 *  - no SVG filters (feTurbulence / feGaussianBlur force per-frame raster work)
 *  - no Math.random() — path data is static, so server and client render identically
 *  - small viewBoxes, CSS-scaled, `pointer-events-none` and `aria-hidden`
 */

import { cn } from "@/lib/utils";
import { INK, type VisualTone } from "./tokens";

/* ── Contour lines ───────────────────────────────────────────────────────────
   Topographic sweeps. `drift` is an open landscape, `pool` closes into an
   irregular set of rings (a contour map of a self), `ridge` stacks into
   uneven sediment lines.
   ─────────────────────────────────────────────────────────────────────────── */

export type ContourVariant = "drift" | "pool" | "ridge";

const CONTOURS: Record<ContourVariant, { viewBox: string; strokes: string[]; dots?: string[] }> = {
  drift: {
    viewBox: "0 0 640 420",
    strokes: [
      "M40 262C96 156 196 90 312 86 438 82 552 152 596 246 618 296 588 356 500 384",
      "M118 264C166 182 240 128 332 126 430 124 512 176 552 250 574 292 552 340 478 364",
      "M192 266C236 208 292 170 356 168 428 166 484 202 514 256 532 288 514 322 456 340",
      "M262 268C294 230 336 206 382 205 428 204 466 230 486 264 498 286 486 306 446 316",
    ],
    dots: [
      "M92 118C128 138 168 142 206 132",
      "M446 104C486 118 520 142 548 176",
      "M112 372C154 392 204 402 254 404",
      "M508 320C494 342 472 358 444 368",
    ],
  },
  pool: {
    viewBox: "0 0 480 480",
    strokes: [
      "M244 40C340 42 416 112 424 202 432 296 364 402 264 428 162 454 66 384 52 284 38 186 116 50 224 42",
      "M246 84C322 86 380 142 386 212 392 286 338 366 260 386 180 406 106 352 96 276 86 198 148 92 232 86",
      "M250 130C306 132 346 174 350 226 354 282 314 336 256 350 196 364 142 324 136 268 130 210 176 136 238 132",
      "M254 176C290 178 314 204 316 240 318 278 292 310 254 318 214 326 180 300 176 264 172 226 202 180 242 178",
      "M258 222C276 224 288 238 288 258 288 278 274 292 256 294 236 296 220 282 220 262 220 240 236 224 254 222",
    ],
    dots: ["M240 10V58", "M240 424V470", "M10 240H58", "M424 240H470"],
  },
  ridge: {
    viewBox: "0 0 640 360",
    strokes: [
      "M40 62C140 48 240 78 340 62 440 48 542 76 606 58",
      "M34 122C150 110 250 138 356 122 456 108 548 134 612 120",
      "M44 184C148 172 256 200 360 184 462 170 552 196 610 182",
      "M36 246C142 236 248 262 352 246 452 232 546 258 608 244",
      "M48 306C152 296 252 320 356 306 458 292 550 316 606 304",
    ],
  },
};

export function ContourLines({
  variant = "drift",
  tone = "dark",
  className,
}: {
  variant?: ContourVariant;
  tone?: VisualTone;
  className?: string;
}) {
  const { viewBox, strokes, dots } = CONTOURS[variant];

  return (
    <svg
      aria-hidden="true"
      viewBox={viewBox}
      fill="none"
      className={cn("pointer-events-none absolute", INK[tone], className)}
    >
      {strokes.map((d, i) => (
        <path
          key={d}
          d={d}
          stroke="currentColor"
          strokeWidth={1.5 - i * 0.08}
          strokeLinecap="round"
          fill="none"
          opacity={0.4 - i * 0.05}
        />
      ))}
      {dots?.map((d) => (
        <path
          key={d}
          d={d}
          stroke="currentColor"
          strokeWidth="1.1"
          strokeLinecap="round"
          fill="none"
          opacity="0.28"
        />
      ))}
    </svg>
  );
}

/* ── Conversation marks ──────────────────────────────────────────────────────
   Fragmented turns of talk: dash runs of uneven length, half-drawn arcs where a
   reply curves back on itself, and dots that anchor a thread. Nothing here is a
   chat bubble — the fragments stay unresolved, which is the point.
   ─────────────────────────────────────────────────────────────────────────── */

export type MarksVariant = "cluster" | "field" | "stub";

const MARKS: Record<MarksVariant, { viewBox: string; dashes: string[]; curves: string[]; anchors: [number, number][] }> = {
  cluster: {
    viewBox: "0 0 520 220",
    dashes: [
      "M18 44h126",
      "M41 72h83",
      "M272 38h156",
      "M305 66h72",
      "M88 157h181",
      "M111 185h112",
      "M334 151h149",
      "M360 180h68",
    ],
    curves: ["M154 44c16 0 24 8 24 24s-8 24-24 24", "M264 151c20 0 30 10 30 30", "M322 38c-17 0-26 9-26 26"],
    anchors: [
      [18, 44],
      [334, 151],
      [272, 38],
    ],
  },
  field: {
    viewBox: "0 0 620 400",
    dashes: [
      "M22 34h84",
      "M140 34h142",
      "M318 30h96",
      "M448 38h148",
      "M44 96h172",
      "M250 92h64",
      "M348 100h118",
      "M500 92h92",
      "M26 160h118",
      "M176 156h196",
      "M406 164h176",
      "M60 224h146",
      "M240 220h96",
      "M370 228h192",
      "M30 288h190",
      "M254 284h72",
      "M360 292h176",
      "M52 352h128",
      "M214 348h164",
      "M412 356h158",
    ],
    curves: [
      "M106 34c18 0 26 9 26 26",
      "M314 156c22 0 32 12 32 34",
      "M220 288c-20 0-30 10-30 28",
      "M576 288c18 0 26 10 26 26",
    ],
    anchors: [
      [22, 34],
      [318, 30],
      [176, 156],
      [240, 220],
      [360, 292],
    ],
  },
  stub: {
    viewBox: "0 0 360 160",
    dashes: ["M16 30h148", "M38 58h96", "M204 112h140"],
    curves: ["M164 30c20 0 30 10 30 30"],
    anchors: [
      [16, 30],
      [204, 112],
    ],
  },
};

export function ConversationMarks({
  variant = "cluster",
  tone = "dark",
  className,
}: {
  variant?: MarksVariant;
  tone?: VisualTone;
  className?: string;
}) {
  const { viewBox, dashes, curves, anchors } = MARKS[variant];

  return (
    <svg
      aria-hidden="true"
      viewBox={viewBox}
      fill="none"
      className={cn("pointer-events-none absolute", INK[tone], className)}
    >
      <g stroke="currentColor" strokeWidth="1.4" strokeLinecap="round" opacity="0.34">
        {dashes.map((d) => (
          <path key={d} d={d} />
        ))}
      </g>
      <g stroke="currentColor" strokeWidth="1.1" strokeLinecap="round" fill="none" opacity="0.26">
        {curves.map((d) => (
          <path key={d} d={d} />
        ))}
      </g>
      <g fill="currentColor" opacity="0.34">
        {anchors.map(([cx, cy]) => (
          <circle key={`${cx}-${cy}`} cx={cx} cy={cy} r="3" />
        ))}
      </g>
    </svg>
  );
}

/* ── Thread line ─────────────────────────────────────────────────────────────
   The single line that runs through a surface and ties the fragments together.
   `spine` wanders and returns; `ascent` climbs with knots along the way.
   ─────────────────────────────────────────────────────────────────────────── */

export type ThreadVariant = "spine" | "ascent";

const THREADS: Record<ThreadVariant, { viewBox: string; d: string; nodes: [number, number][] }> = {
  spine: {
    viewBox: "0 0 240 320",
    d: "M118 6c-18 33 22 51 4 85s-30 53-10 87 26 51 8 83",
    nodes: [
      [118, 6],
      [120, 261],
    ],
  },
  ascent: {
    viewBox: "0 0 200 360",
    d: "M96 354c-26-40 18-58 6-98s-32-56-14-96 34-58 18-98",
    nodes: [
      [96, 354],
      [82, 256],
      [106, 152],
      [104, 62],
    ],
  },
};

export function ThreadLine({
  variant = "spine",
  tone = "dark",
  className,
}: {
  variant?: ThreadVariant;
  tone?: VisualTone;
  className?: string;
}) {
  const { viewBox, d, nodes } = THREADS[variant];

  return (
    <svg
      aria-hidden="true"
      viewBox={viewBox}
      fill="none"
      className={cn("pointer-events-none absolute", INK[tone], className)}
    >
      <path d={d} stroke="currentColor" strokeWidth="1.3" strokeLinecap="round" opacity="0.4" fill="none" />
      <g fill="currentColor" opacity="0.44">
        {nodes.map(([cx, cy]) => (
          <circle key={`${cx}-${cy}`} cx={cx} cy={cy} r="2.4" />
        ))}
      </g>
    </svg>
  );
}

/* ── Ink grain ───────────────────────────────────────────────────────────────
   Chalk and ink tooth. Pure CSS — a repeating-linear-gradient pair composites on
   the GPU, where an SVG turbulence filter would rasterize on every paint.
   ─────────────────────────────────────────────────────────────────────────── */

export function InkGrain({ className }: { className?: string }) {
  return <div aria-hidden="true" className={cn("pointer-events-none absolute inset-0 miryn-ink-grain", className)} />;
}

/* ── The mark ────────────────────────────────────────────────────────────────
   Miryn's sigil. `idle` holds its shape, `thinking` loosens into a spiral, and
   `avatar` is the same form at conversation scale.
   ─────────────────────────────────────────────────────────────────────────── */

export type MarkState = "idle" | "thinking" | "avatar";

export function MirynMark({
  state = "idle",
  className,
}: {
  state?: MarkState;
  tone?: VisualTone;
  className?: string;
}) {
  return (
    <div
      className={cn(
        "relative flex items-center justify-center rounded-full overflow-hidden shrink-0",
        state === "avatar" ? "h-8 w-8" : "h-full w-full",
        className,
      )}
    >
      {/* eslint-disable-next-line @next/next/no-img-element */}
      <img
        src="/miryn-logo.png"
        alt="Miryn Logo"
        className={`w-full h-full object-cover rounded-full ${state === "thinking" ? "animate-pulse" : ""}`}
      />
    </div>
  );
}
