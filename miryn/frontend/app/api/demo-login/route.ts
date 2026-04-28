import { NextResponse } from "next/server";

const API_URL = process.env.API_URL || process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000";
const DEMO_TIMEOUT_MS = 10_000;
const DEMO_RATE_LIMIT_WINDOW_MS = 60 * 60 * 1000;
const DEMO_RATE_LIMIT_MAX_REQUESTS = 3;
const API_URL_FALLBACKS = [
  API_URL,
  process.env.API_URL,
  process.env.NEXT_PUBLIC_API_URL,
  "http://127.0.0.1:8000",
  "http://localhost:8000",
].filter((url, idx, arr): url is string => Boolean(url) && arr.indexOf(url) === idx);
const demoRequestBuckets = new Map<string, number[]>();

const getErrorMessage = (error: unknown, fallback: string) => {
  if (error instanceof Error && error.message) return error.message;
  if (typeof error === "string") return error;
  return fallback;
};

const getClientKey = (request: Request) =>
  request.headers.get("x-forwarded-for")?.split(",")[0]?.trim() ||
  request.headers.get("x-real-ip") ||
  "unknown";

const isDemoRateLimited = (request: Request) => {
  const now = Date.now();
  const clientKey = getClientKey(request);
  const recentRequests = (demoRequestBuckets.get(clientKey) || []).filter(
    (timestamp) => now - timestamp < DEMO_RATE_LIMIT_WINDOW_MS,
  );

  if (recentRequests.length >= DEMO_RATE_LIMIT_MAX_REQUESTS) {
    demoRequestBuckets.set(clientKey, recentRequests);
    return true;
  }

  recentRequests.push(now);
  demoRequestBuckets.set(clientKey, recentRequests);
  return false;
};

async function fetchWithTimeout(url: string, init: RequestInit) {
  const controller = new AbortController();
  const timeout = setTimeout(() => controller.abort(), DEMO_TIMEOUT_MS);

  try {
    return await fetch(url, { ...init, signal: controller.signal });
  } finally {
    clearTimeout(timeout);
  }
}

async function loginDemo(baseUrl: string, demoEmail: string, demoPassword: string) {
  return fetchWithTimeout(`${baseUrl}/auth/login`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ email: demoEmail, password: demoPassword }),
  });
}

export async function POST(request: Request) {
  if (isDemoRateLimited(request)) {
    return NextResponse.json(
      { error: "Too many demo account requests. Please try again later." },
      { status: 429 },
    );
  }

  const nonce = `${Date.now()}-${Math.random().toString(36).slice(2, 10)}`;
  const demoEmail = `demo+${nonce}@miryndemo.com`;
  const demoPassword = `MirynDemo!${nonce}`;

  let lastError = "Demo login failed";
  let lastStatus = 500;
  let signupCompleted = false;

  for (const baseUrl of API_URL_FALLBACKS) {
    try {
      if (!signupCompleted) {
        const signupResponse = await fetchWithTimeout(`${baseUrl}/auth/signup`, {
          method: "POST",
          headers: { "Content-Type": "application/json" },
          body: JSON.stringify({ email: demoEmail, password: demoPassword }),
        });

        if (!signupResponse.ok) {
          lastStatus = signupResponse.status || 500;
          lastError = (await signupResponse.text()) || "Demo signup failed";
          continue;
        }

        signupCompleted = true;
      }

      let loginResponse = await loginDemo(baseUrl, demoEmail, demoPassword);

      if (!loginResponse.ok) {
        const firstLoginError = (await loginResponse.text()) || "Demo login failed";
        loginResponse = await loginDemo(baseUrl, demoEmail, demoPassword);
        if (!loginResponse.ok) {
          lastStatus = loginResponse.status || 500;
          lastError = (await loginResponse.text()) || firstLoginError;
          continue;
        }
      }

      const data = await loginResponse.json();
      return NextResponse.json({ ...data, is_new: true });
    } catch (error: unknown) {
      lastError =
        error instanceof DOMException && error.name === "AbortError"
          ? "Demo login timed out"
          : getErrorMessage(error, "Demo login failed");
      lastStatus = 500;
    }
  }

  return NextResponse.json({ error: lastError }, { status: lastStatus });
}
