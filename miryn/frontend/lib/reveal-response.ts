/** Display animation only, never a content classifier or live model stream. */
export type ReplyEvent = { chunk?: string; error?: string; done?: boolean; conversation_id?: string };

type Options = {
  signal: AbortSignal;
  reducedMotion: () => boolean;
  append: (text: string) => void;
  wait?: (ms: number, signal: AbortSignal) => Promise<void>;
};

function checkAbort(signal: AbortSignal) {
  if (signal.aborted) throw new DOMException("Reply stopped", "AbortError");
}

export function abortableWait(ms: number, signal: AbortSignal): Promise<void> {
  return new Promise((resolve, reject) => {
    checkAbort(signal);
    const abort = () => { clearTimeout(timer); reject(new DOMException("Reply stopped", "AbortError")); };
    const timer = setTimeout(() => { signal.removeEventListener("abort", abort); resolve(); }, ms);
    signal.addEventListener("abort", abort, { once: true });
  });
}

export async function revealResponse(text: string, options: Options): Promise<void> {
  const words = text.match(/\S+\s*|\s+/gu) || [];
  // A long answer should not trap the reader in a minute-long animation.
  const batchSize = Math.max(1, Math.ceil(words.length / 150));
  const wait = options.wait || abortableWait;
  for (let index = 0; index < words.length; index += batchSize) {
    checkAbort(options.signal);
    if (options.reducedMotion()) {
      options.append(words.slice(index).join(""));
      return;
    }
    options.append(words.slice(index, index + batchSize).join(""));
    if (index + batchSize < words.length) await wait(28, options.signal);
  }
}

export async function consumeReply(
  events: AsyncIterable<ReplyEvent>, options: Options & { ready?: (id?: string) => void },
): Promise<string | undefined> {
  let response = "";
  for await (const event of events) {
    checkAbort(options.signal);
    if (event.error) throw new Error(event.error);
    if (event.chunk) response += event.chunk;
    if (event.done) {
      if (!response.trim()) throw new Error("Miryn returned an empty reply. Please retry.");
      options.ready?.(event.conversation_id);
      await revealResponse(response, options);
      checkAbort(options.signal);
      return event.conversation_id;
    }
  }
  throw new Error("The connection ended before Miryn finished. Please retry.");
}
