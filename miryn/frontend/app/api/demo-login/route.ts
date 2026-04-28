import { NextResponse } from "next/server";

const API_URL = process.env.API_URL || process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000";
const DEMO_TIMEOUT_MS = 10_000;
const API_URL_FALLBACKS = [
  API_URL,
  process.env.API_URL,
  process.env.NEXT_PUBLIC_API_URL,
  "http://127.0.0.1:8000",
  "http://localhost:8000",
].filter((url, idx, arr): url is string => Boolean(url) && arr.indexOf(url) === idx);

const getErrorMessage = (error: unknown, fallback: string) => {
  if (error instanceof Error && error.message) return error.message;
  if (typeof error === "string") return error;
  return fallback;
};

export async function POST() {
  const nonce = `${Date.now()}-${Math.random().toString(36).slice(2, 10)}`;
  const demoEmail = `demo+${nonce}@miryndemo.com`;
  const demoPassword = `MirynDemo!${nonce}`;

  let lastError = "Demo login failed";

  for (const baseUrl of API_URL_FALLBACKS) {
    const controller = new AbortController();
    const timeout = setTimeout(() => controller.abort(), DEMO_TIMEOUT_MS);

    try {
      const signupResponse = await fetch(`${baseUrl}/auth/signup`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ email: demoEmail, password: demoPassword }),
        signal: controller.signal,
      });

      if (!signupResponse.ok) {
        lastError = (await signupResponse.text()) || "Demo signup failed";
        continue;
      }

      const loginResponse = await fetch(`${baseUrl}/auth/login`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ email: demoEmail, password: demoPassword }),
        signal: controller.signal,
      });

      if (!loginResponse.ok) {
        lastError = (await loginResponse.text()) || "Demo login failed";
        continue;
      }

      const data = await loginResponse.json();
      return NextResponse.json({ ...data, is_new: true });
    } catch (error: unknown) {
      lastError =
        error instanceof DOMException && error.name === "AbortError"
          ? "Demo login timed out"
          : getErrorMessage(error, "Demo login failed");
    } finally {
      clearTimeout(timeout);
    }
  }

  return NextResponse.json({ error: lastError }, { status: 500 });
}
