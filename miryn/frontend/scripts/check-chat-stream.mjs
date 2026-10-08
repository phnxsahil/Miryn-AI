import assert from "node:assert/strict";
import { api } from "../lib/api.ts";

const originalFetch = globalThis.fetch;
const encoder = new TextEncoder();
try {
  globalThis.fetch = async () => new Response(new ReadableStream({
    start(controller) {
      for (const part of ['data: {"chunk":"Hel"}\r', '\n\r\n', 'data: {"chunk":"lo"}\r\n\r\n', 'data: {"done":true,"conversation_id":"demo"}\n\n']) {
        controller.enqueue(encoder.encode(part));
      }
      controller.close();
    },
  }), { status: 200 });
  const events = [];
  for await (const event of api.streamMessage("test")) events.push(event);
  assert.deepEqual(events, [
    { chunk: "Hel" },
    { chunk: "lo" },
    { done: true, conversation_id: "demo" },
  ]);

  globalThis.fetch = async () => new Response(JSON.stringify({ detail: "No access" }), { status: 403 });
  await assert.rejects(async () => {
    for await (const _ of api.streamMessage("test")) { /* Consume the stream. */ }
  }, /Session expired/);
  console.log("Chat SSE framing and auth checks passed.");
} finally {
  globalThis.fetch = originalFetch;
}
