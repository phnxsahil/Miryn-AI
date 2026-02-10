import { NextResponse } from "next/server";

const API_URL = process.env.API_URL || process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000";
const DEMO_TIMEOUT_MS = 10_000;

const getErrorMessage = (error: unknown, fallback: string) => {
  if (error instanceof Error && error.message) return error.message;
  if (typeof error === "string") return error;
  return fallback;
};

export async function POST() {
  if (process.env.ENABLE_DEMO !== "true") {
    return NextResponse.json({ error: "Demo login is disabled" }, { status: 403 });
  }

  const demoEmail = process.env.DEMO_EMAIL;
  const demoPassword = process.env.DEMO_PASSWORD;

  if (!demoEmail || !demoPassword) {
    return NextResponse.json({ error: "Demo credentials are not configured" }, { status: 500 });
  }

  const controller = new AbortController();
  const timeout = setTimeout(() => controller.abort(), DEMO_TIMEOUT_MS);

  try {
    const response = await fetch(`${API_URL}/auth/login`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ email: demoEmail, password: demoPassword }),
      signal: controller.signal,
    });

    if (!response.ok) {
      const error = await response.text();
      return NextResponse.json({ error: error || "Demo login failed" }, { status: response.status });
    }

    const data = await response.json();
    return NextResponse.json(data);
  } catch (error: unknown) {
    const message =
      error instanceof DOMException && error.name === "AbortError"
        ? "Demo login timed out"
        : getErrorMessage(error, "Demo login failed");
    return NextResponse.json({ error: message }, { status: 500 });
  } finally {
    clearTimeout(timeout);
  }
}
