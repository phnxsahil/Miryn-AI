"use client";

import { Analytics } from "@vercel/analytics/react";
import type { BeforeSendEvent } from "@vercel/analytics";
import { sanitizeAnalyticsEvent } from "@/lib/analytics-privacy";

// Legal review and an explicit production environment flag are required before collection.
export default function TrafficAnalytics() {
  if (process.env.NEXT_PUBLIC_TRAFFIC_ANALYTICS_ENABLED !== "true" ||
      process.env.NEXT_PUBLIC_VERCEL_ENV !== "production") return null;
  return <Analytics debug={false} beforeSend={(event: BeforeSendEvent) => sanitizeAnalyticsEvent(event)} />;
}
