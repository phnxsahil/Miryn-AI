import type { BeforeSendEvent } from "@vercel/analytics";

// No dynamic paths, account IDs, search text, tokens, hashes, or private app routes.
const PUBLIC_PATHS = new Set(["/", "/login", "/signup", "/privacy", "/terms"]);
export function sanitizeAnalyticsEvent(event: BeforeSendEvent): BeforeSendEvent | null {
  if (event.type !== "pageview") return null;
  try {
    const url = new URL(event.url);
    if (url.hostname !== "miryn-ai.vercel.app" || !PUBLIC_PATHS.has(url.pathname)) return null;
    return { type: "pageview", url: url.origin + url.pathname };
  } catch { return null; }
}
