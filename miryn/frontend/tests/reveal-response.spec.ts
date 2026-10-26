import { test, expect } from '@playwright/test';
import { consumeReply, revealResponse } from '../lib/reveal-response';

async function* events(...items: object[]) { for (const item of items) yield item; }
function options() {
  const controller = new AbortController();
  const parts: string[] = [];
  return { controller, parts, signal: controller.signal, reducedMotion: () => false,
    append: (part: string) => parts.push(part), wait: async () => {} };
}

test('waits for done, then reveals words preserving whitespace and markdown', async () => {
  const o = options();
  async function* stream() {
    yield { chunk: 'Hello **world**.\n' };
    expect(o.parts).toEqual([]);
    yield { chunk: '\nNext line.  ' };
    expect(o.parts).toEqual([]);
    yield { done: true, conversation_id: 'test' };
  }
  expect(await consumeReply(stream(), o)).toBe('test');
  expect(o.parts.length).toBeGreaterThan(1);
  expect(o.parts.join('')).toBe('Hello **world**.\n\nNext line.  ');
});

test('reduced motion reveals once', async () => {
  const o = options();
  await consumeReply(events({chunk:'One two three.'},{done:true}), {...o, reducedMotion:()=>true});
  expect(o.parts).toEqual(['One two three.']);
});

test('error and incomplete streams expose no buffered content', async () => {
  for (const stream of [events({chunk:'discard'},{error:'Blocked response.'}), events({chunk:'unfinished'})]) {
    const o = options();
    await expect(consumeReply(stream, o)).rejects.toThrow();
    expect(o.parts).toEqual([]);
  }
});

test('empty done is an error', async () => {
  await expect(consumeReply(events({done:true}), options())).rejects.toThrow('empty reply');
});

test('stop during reveal cancels remaining words', async () => {
  const o = options();
  await expect(revealResponse('One two three.', {...o, wait:async()=>{o.controller.abort();}})).rejects.toThrow();
  expect(o.parts).toEqual(['One ']);
});

test('stop before response completion shows nothing', async () => {
  const o = options(); o.controller.abort();
  await expect(consumeReply(events({chunk:'No display'},{done:true}), o)).rejects.toThrow();
  expect(o.parts).toEqual([]);
});

test('preference change flushes remainder exactly once', async () => {
  const o = options(); let reduced=false;
  await revealResponse('One two three.', {...o, reducedMotion:()=>reduced, wait:async()=>{reduced=true;}});
  expect(o.parts).toEqual(['One ', 'two three.']);
});
