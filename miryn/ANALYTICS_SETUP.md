# Owner analytics setup (not activated)

This branch does not turn on collection. Finish the legal-first update and review this PR before a production merge.

## What is prepared

- Vercel Web Analytics: visits and page views of public landing/auth/legal routes only. Queries and fragments are stripped; site-wide strict-origin referrer policy prevents path/query leakage through referrers; private app routes and dynamic IDs are dropped. No custom events, emails, account IDs, conversation content, replay or persistent cross-site identity.
- Existing PostHog provider is no longer mounted. Do not set its key to enable broad default capture.
- `/analytics/owner`: authenticated, server-allowlisted aggregate account counts. Empty `ANALYTICS_OWNER_USER_IDS` denies everyone. No public metrics or service keys in the browser.
- `/owner/analytics`: private UI with total created, not-deleted, soft-deleted, new today/7/30 days, daily counts. All calendar boundaries are Asia/Kolkata (IST) and include test/owner accounts. Not-deleted is not daily active users.

## Remaining setup after legal approval and PR review

1. Verify the owner's existing Miryn account UUID using the database/account record. Never authorize by a client-supplied email. Set only that UUID as Render's server variable `ANALYTICS_OWNER_USER_IDS` (comma separated if explicitly needed). No schema changes are required.
2. Merge/deploy the reviewed branch only with applicable owner permission. This auto-deploys on the current hosting setup.
3. After the legal changes are live, choose the **included Hobby** option on the existing Vercel project's Analytics page. Do not upgrade or start a paid trial. Confirm the current plan limits in the UI.
4. Set `NEXT_PUBLIC_TRAFFIC_ANALYTICS_ENABLED=true` on Vercel Production and redeploy. `NEXT_PUBLIC_VERCEL_ENV` must be `production` as supplied by Vercel, so previews remain off.
5. Make one controlled public-page test. Inspect outgoing payload to verify no query/hash, private routes, content or identifying properties. Confirm its arrival in the private Vercel dashboard, record exact first ingestion time, and distinguish this test from real visitors.
6. Test unauthenticated 401, normal-account 403, and owner success on the actual deployment. Counts are not verified until the live database has been read. Confirm no-store response and no public sharing.

## Limitations and dashboard

Private traffic dashboard: https://vercel.com/shanu133s-projects/miryn-ai/analytics

Verified Oct 31, 2026: Hobby includes 50,000 events/month shared across projects, 30 days viewable history, no custom events and capped ingestion without paid overage. Recheck before activation. Visitor hashes expire after 24h, so totals are not exact durable people counts. Browser blockers and omitted private routes can reduce counts; no historical visitor backfill. Database counts use retained `users.created_at` and soft-deletion status, so permanently removed accounts cannot be reconstructed. No conversion rate is claimed between these differently scoped measures.

Sources: https://vercel.com/docs/analytics/limits-and-pricing and https://vercel.com/docs/analytics/privacy-policy

## Checks

- Frontend Next production build, TypeScript and lint (existing Chat hook warnings only).
- `SECRET_KEY=test PYTHONPATH=. python -m unittest discover -s tests -p test_owner_metrics_unit.py -v` from backend: counts, daily gaps, IST midnight boundaries, deletion distinctions, no PII, empty data and fail-closed owner allowlist.
- URL sanitizer tested for query/hash removal, private/dynamic/reset URL rejection, external hosts and custom event rejection.
- Desktop/mobile previews use fictional fixture counts, not real Miryn data.
