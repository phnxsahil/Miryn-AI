# Backend safety evaluation

Run from `miryn/backend` with the normal requirements installed:

```sh
python scripts/evaluate_safety.py
```

Default: offline fake-provider regressions, temporary local SQLite, dummy keys,
no running app, Redis, account, provider request or personal memory. This tests
production `LLMService.chat`/`stream_chat` code, Gemini metadata handling and the
shared safety policy. It is much faster and more repeatable than UI clicking.
It is NOT a claim that a model always produces safe answers.

The `evals/safety_cases.json` fixtures contain fictional adult scenarios and
human-review rubrics. They cover crisis, medical ambiguity, depression, mixed
consent/distress, benign adult sexual education and truthfulness. Never put real
users' sensitive conversations into this file or CI artifacts.

## Optional live behavioral checks (not part of CI)

Only run after the owner approves provider usage/quota/cost. Set `GEMINI_API_KEY`
and `GEMINI_MODEL` in the server's secure environment or secret store, never a
browser, source file, chat, command-line argument or committed `.env`.

```sh
python scripts/evaluate_safety.py --live --case depression --max-cases 1 --output /tmp/miryn-depression.json
python scripts/evaluate_safety.py --live --case adult_health --transport chat --output /tmp/miryn-adult-health.json
```

Live mode requires explicit case selection, defaults to one case, and pins the
configured Gemini model with no cross-model fallback. It never imports the app
server, orchestrator, account, memory, reflection or database code, so no test
facts are written into personal memory. Urgent cases can resolve locally with
zero model requests; other cases call the provider (including the existing
zero-text generation fallback). Model/API retries may still consume quota; the
case cap is not a dollar cap. Responses and rubrics need human review. Do not
mistake substring matching, a self-reported boundary, or successful requests for
safety certification. Test cases are isolated in-memory, not a simulated user.

The live runner uses the same composed persona and safety system prompt through
`LLMService`, not a bare vendor prompt. It bypasses account/orchestrator memory
retrieval on purpose.

The offline suite checks that SAFETY, prohibited-content, blocklist, SPII and
recitation stops are terminal, including after partial chunks. Blocked fragments
must never be exposed or sent to another model. Successful Gemini replies are
buffered until the stream finishes; the UI receives chunks afterward. This
intentionally trades token-by-token immediacy for a safe finish-status check.

## Coverage and known limits

- A narrow English urgent-signal fallback catches explicit first-person danger
  and acute chest/breathing symptoms. It is not a clinical classifier; it can
  over-escalate quotations and miss paraphrases, negation context or languages.
- The shared policy applies to every persona, but model compliance still needs
  behavioral review. Additional adjustable Gemini filters are not configured in
  this change; built-in model safety remains distinct from app policy.
- The mocked HTTP/SSE regression verifies endpoint framing and error/control
  flow, not real authentication, persistence or deployment wiring. Separate
  Playwright tests mock the API to verify paced display, Stop, navigation, errors
  and reduced motion. None certify live model behavior or cross-chat memory. Keep
  a small test-account API/UI smoke check after deploying an approved PR.
- This PR does not change personas, personalization storage, billing, provider
  keys, deployment configuration or the user's data. No preview backend needed.

Reference contracts: [Gemini safety feedback and defaults](https://ai.google.dev/gemini-api/docs/safety-settings)
and [NIMH crisis support steps](https://www.nimh.nih.gov/health/publications/5-action-steps-for-helping-someone-in-emotional-pain).
These inform the implementation, not an endorsement or clinical validation.

## Paced frontend reveal

The browser waits for a completed SSE response, then reveals words at about
28 ms per step (long replies batch words into at most 150 steps). Reduced motion
shows the complete response immediately. Stop cancels display, not an already
saved server reply. This is display animation, not real-time model streaming or
an additional semantic content filter. Gemini finish-status buffering remains.

From `miryn/frontend`, install dependencies and Playwright Chromium, start
`npm run dev`, then run:

```sh
npx playwright test tests/reveal-response.spec.ts tests/paced-chat.spec.ts
```

These tests make no provider calls. Actual API deployment, account persistence,
and a real-model behavioral rubric review remain separate checks after approval.
