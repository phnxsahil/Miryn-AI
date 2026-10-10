# Round 12C — PAUSED checkpoint

Status: **PAUSED / NOT COMPLETE**. This is a safe-buffer checkpoint, not a release or deployment approval. The owner requested committing and pushing the work in progress. Remote `main` is intentionally unchanged; this checkpoint is published on `checkpoint/12c-paused`.

Base before checkpoint: `7dd026d7bea47d072c616603055e942bdc4851c0`.

## Saved work

The preceding item commits restore the native spectrum orb, floating pill navigation and logo, hero glass cards and generic tool icons, glowing mood cards and snap carousel, wave charts, two-column FAQ, contact aurora, gradient blog art, and About reveal/eyebrow pills.

This checkpoint preserves the follow-up fixes: shared styles moved out of the CSS module so child components actually receive them; mobile carousel containment and 44px targets; hero card/headline separation; sampled mood colours; chart accent restricted to the first segment; accessibility/contrast fixes; canonical metadata; a navigation IntersectionObserver sentinel; and offscreen ambient-animation pausing. A runnable production-browser check is retained at `miryn/frontend/scripts/check-landing.mjs`.

No new npm dependency, deployment, or change to `frontend/public/landing` was made for this checkpoint. Unrelated local databases, smoke output, screenshots and other pre-existing files are deliberately excluded.

## Last completed checks before pausing

- Fresh checkpoint checks: `npx tsc --noEmit` passed; `npm run lint` returned `No ESLint warnings or errors`; `git diff --check` passed.
- Production build passed with TypeScript and lint checks enabled. `/` first-load JS: 94.7 kB.
- Backend import passed; pytest: 77 passed, 1 skipped, 70 warnings. These are earlier completed results, not fresh checks for this checkpoint.
- Browser check passed at 390, 768, 1024, 1440 and 1920px: no horizontal overflow or headline/card overlap, one h1, zero iframes, zero console/page errors, and zero undersized visible a/button/summary targets.
- Reduced-motion check: no running CSS animations. Without JavaScript: no hidden reveals or dim About words.
- Whole-page transfer: desktop 18 requests / 339.5 kB; mobile 17 requests / 312.3 kB. The owner's supplied 12A baseline was 18 requests / 655 kB.
- Required routes and all three blog detail routes returned 200.

## Outstanding / limitations

- **Desktop jank check still misses the target:** 4x CPU / Slow 4G recorded 5 scroll long tasks and 8.24% rAF intervals over 34ms; targets are 0–2 and under 5%. Mobile recorded 1 long task and 3.97%. The interval percentage is a proxy, not an authoritative GPU dropped-frame count.
- Recorded load-plus-scroll blocking sums were 1599ms mobile / 2115ms desktop; these are not standard Lighthouse TBT. Hero content layers were 5 mobile / 13 desktop.
- Final Lighthouse rerun and post-commit final gates remain unfinished. An earlier report scored 95 performance / 100 accessibility / 100 SEO; do not label it a final-checkpoint measurement.
- Original native BEFORE screenshots were overwritten during an intermediate capture. Do not present the saved unstyled-intermediate screenshots as valid pre-change evidence.
- Exact Framer spring timings and every colour/value were not recovered. Native approximations include gradient artwork, glass geometry, chart accents, eyebrow tints, float/reveal timing, and softer orb construction. Nav blur was reduced to 8px for cost; mobile side cards are hidden; carousel uses native snap rather than automatic drift; violet fourth mood follows the requested palette rather than the old orange card.
- The worktree contains unrelated pre-existing modifications/untracked files; it is not globally clean. Preserve them.

Ignored evidence is in `docs/screens/`, including `12c-checks.json`, the motion catalog, desktop/mobile comparison and detail screenshots, and performance traces. It is local evidence and is not included in this pushed checkpoint.

Resume by checking this checkpoint, addressing the desktop scroll-performance miss without dropping the requested atmosphere, rerunning Lighthouse and the final gates, and updating the final per-item report. Do not deploy or publish to main without further owner direction.

## Merge review — 2026-10-10

The owner subsequently requested reviewing checkpoint 12C and merging it into main. The paused status above records the original checkpoint; it is not the status of this review. Reviewed checkpoint `a9b22cc` against local and remote main `7dd026d` in a separate checkout, preserving the owner's unrelated local files. The merge has no conflicts. The checkpoint changes landing components, styles, metadata, and verification only; it does not change backend behavior, authentication, dependencies, or migrations.

### Review fixes

- Restore the stable `landing` class on the page shell. Moving CSS-module rules into the global stylesheet otherwise leaves `.landing section` unmatched, losing the 96px anchor spacing beneath the sticky navigation. The browser check now asserts that spacing.
- Make screenshot comparisons optional when genuine local before-images are unavailable. Functional checks and result export now run in a fresh checkout without requiring untracked screenshots or inventing baseline evidence.
- Check mobile navigation opening and closing, and collect console errors through the end of each viewport check.
- Correct the auth smoke check's obsolete black-background expectation to the existing dark-theme background on main.

### Fresh verification

- Backend: `pytest -q` — 77 passed, 1 skipped, 63 existing warnings, using a separate SQLite database and dummy provider credentials.
- Frontend: `npm run verify`, TypeScript checking, and production build passed. Landing first-load JS remains 94.7 kB.
- Production-browser landing check passed at 390, 768, 1024, 1440, and 1920px: no horizontal overflow, headline/card overlap, undersized visible link/button/summary targets, or browser errors. Carousel scrolling, mobile navigation, reduced motion, and no-JavaScript content passed.
- All ten checked public/auth/blog routes returned 200. Whole-page transfer was 319.2 kB / 19 requests on mobile (including the navigation interaction) and 339.5 kB / 18 requests on desktop.
- The three focused auth-screen browser checks passed.
- Fresh Lighthouse 13.5.0 mobile report: performance 94, accessibility 100, best practices 100, SEO 100; LCP 2.6s, standard Lighthouse TBT 150ms. The JSON and HTML reports completed with no audit runtime error; the CLI subsequently hit a Windows temporary-directory cleanup permission error.

### Remaining limitations

- A separate serial scroll measurement with 4x CPU and Slow 4G recorded mobile 1 long task / 4.42% intervals over 34ms, and desktop 3 long tasks / 10.99%. Desktop still misses the prior 0–2 / under-5% target. This timing proxy is hardware-sensitive and is not a GPU dropped-frame measurement. The merge does not claim that performance target is met.
- The existing conversation-sidebar browser test uses the obsolete `More options for` label. Temporarily using the current `Options for` label exposed an existing menu-positioning issue: Pin is outside the viewport. The conversation component and app layout are unchanged from main; the temporary test-label edit was reverted. The broader browser suite is not fully green.
- Reusing installed dependencies through a Windows junction caused Next.js standalone trace-copy symlink warnings. The production build and standalone server ran successfully with the installed dependencies available; a fully isolated standalone package was not independently verified.
- Genuine before-screenshots remain unavailable. No visual comparison is presented as historical baseline evidence.

Fresh local evidence is retained under `docs/screens/12c-merge-review/` in the owner's checkout and is intentionally excluded from Git. This review supports the requested main merge with the limitations above; it does not describe the prototype as release-complete.
