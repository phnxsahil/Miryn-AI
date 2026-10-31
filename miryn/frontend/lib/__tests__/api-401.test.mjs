// Regression tests for 401 handling in lib/api.ts (node --test).
//
// Covers the smoke-test bug where a wrong password at login showed
// "Session expired": credential endpoints (/auth/login, /auth/signup,
// /auth/google) must surface the backend's message, must not trigger a
// token-refresh retry, and must not clear an existing stored session,
// while 401s on authenticated endpoints keep the old session-expired
// behavior.
//
// Run: npm run build:test-401 && node --test lib/__tests__/api-401.test.mjs
// (build:test-401 transpiles lib/api.ts with tsc; see package.json)

import { test, beforeEach } from "node:test";
import assert from "node:assert/strict";
import { createRequire } from "node:module";

const require = createRequire(import.meta.url);

function makeLocalStorage() {
  const store = new Map();
  return {
    getItem: (k) => (store.has(k) ? store.get(k) : null),
    setItem: (k, v) => void store.set(k, String(v)),
    removeItem: (k) => void store.delete(k),
    _store: store,
  };
}

let api;
let localStorageStub;
let fetchCalls;

beforeEach(async () => {
  localStorageStub = makeLocalStorage();
  fetchCalls = [];
  globalThis.window = { localStorage: localStorageStub, location: { hostname: "localhost" } };
  globalThis.localStorage = localStorageStub;
  globalThis.fetch = async (url, options = {}) => {
    fetchCalls.push({ url: String(url), options });
    return fetchCalls.response;
  };
  delete require.cache[require.resolve("./api-compiled/api.js")];
  api = require("./api-compiled/api.js").api;
});

function res(status, body, statusText = "") {
  return {
    ok: status >= 200 && status < 300,
    status,
    statusText,
    headers: { get: () => null },
    json: async () => body,
    text: async () => JSON.stringify(body),
  };
}

test("login 401 surfaces the backend credential error, not 'Session expired'", async () => {
  fetchCalls.response = res(401, { detail: "Invalid email or password" });
  await assert.rejects(
    () => api.login("sahil@example.com", "wrong-password"),
    (err) => {
      assert.match(err.message, /Invalid email or password/);
      assert.doesNotMatch(err.message, /Session expired/);
      return true;
    }
  );
});

test("login 401 does not clear an existing stored session and does not attempt refresh", async () => {
  localStorageStub.setItem("miryn_token", "existing-access");
  localStorageStub.setItem("miryn_refresh_token", "existing-refresh");
  fetchCalls.response = res(401, { detail: "Invalid email or password" });
  await assert.rejects(() => api.login("sahil@example.com", "wrong-password"));
  assert.equal(localStorageStub.getItem("miryn_token"), "existing-access");
  assert.equal(localStorageStub.getItem("miryn_refresh_token"), "existing-refresh");
  assert.equal(fetchCalls.length, 1);
  assert.ok(fetchCalls[0].url.includes("/auth/login"));
  assert.ok(!fetchCalls.some((c) => c.url.includes("/auth/refresh")), "no refresh retry on credential endpoints");
});

test("signup 401 keeps its own message", async () => {
  fetchCalls.response = res(401, { detail: "Signup unavailable" });
  await assert.rejects(
    () => api.signup("sahil@example.com", "pw"),
    (err) => {
      assert.match(err.message, /Signup unavailable/);
      assert.doesNotMatch(err.message, /Session expired/);
      return true;
    }
  );
});

test("google login 401 keeps its own message", async () => {
  fetchCalls.response = res(401, { detail: "Google token rejected" });
  await assert.rejects(
    () => api.googleLogin("bad-token"),
    (err) => {
      assert.match(err.message, /Google token rejected/);
      assert.doesNotMatch(err.message, /Session expired/);
      return true;
    }
  );
});

test("authenticated endpoint 401 with no refresh token still clears session and reports expiry", async () => {
  localStorageStub.setItem("miryn_token", "existing-access");
  fetchCalls.response = res(401, { detail: "token expired" });
  await assert.rejects(
    () => api.getAuthConfig(),
    (err) => {
      assert.match(err.message, /Session expired/);
      return true;
    }
  );
  assert.equal(localStorageStub.getItem("miryn_token"), null);
});

test("authenticated endpoint 401 with failing refresh clears session", async () => {
  localStorageStub.setItem("miryn_token", "existing-access");
  localStorageStub.setItem("miryn_refresh_token", "existing-refresh");
  globalThis.fetch = async (url) => {
    fetchCalls.push({ url: String(url) });
    return res(401, { detail: "expired" });
  };
  await assert.rejects(
    () => api.getAuthConfig(),
    (err) => {
      assert.match(err.message, /Session expired/);
      return true;
    }
  );
  assert.equal(localStorageStub.getItem("miryn_token"), null);
  assert.equal(localStorageStub.getItem("miryn_refresh_token"), null);
  assert.ok(fetchCalls.some((c) => c.url.includes("/auth/refresh")), "refresh was attempted for non-credential endpoint");
});
