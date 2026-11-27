"use client";

/**
 * SwellBackground: the baked Swell wave field behind app screens.
 * Variant "chat" carries the five-band field fading out below the header;
 * "empty" carries the single warm band for quiet states. Art is baked WebP
 * (see public/swell); theme crossfades at 600ms; drift is transform-only and
 * disabled under prefers-reduced-motion. Texture lives on the art layer only,
 * so UI text above stays crisp.
 */
export default function SwellBackground({
  variant = "chat",
}: {
  variant?: "chat" | "empty";
}) {
  return (
    <div aria-hidden className={`swell-bg swell-bg-${variant}`}>
      <div className="swell-art swell-art-day" />
      <div className="swell-art swell-art-night" />
      <div className="swell-tooth" />
    </div>
  );
}
