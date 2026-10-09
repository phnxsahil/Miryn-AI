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
