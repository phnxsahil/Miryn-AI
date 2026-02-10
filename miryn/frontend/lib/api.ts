import type { IdentityUpdatePayload, OnboardingPayload } from "@/lib/types";

const API_URL = process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000";

class ApiClient {
  private token: string | null = null;

  constructor() {
    if (typeof window !== "undefined") {
      this.loadToken();
    }
  }

  setToken(token: string | null) {
    this.token = token;
    if (typeof window !== "undefined") {
      if (token) {
        localStorage.setItem("miryn_token", token);
      } else {
        localStorage.removeItem("miryn_token");
      }
    }
  }

  clearToken() {
    this.setToken(null);
  }

  loadToken() {
    if (typeof window !== "undefined") {
      const token = localStorage.getItem("miryn_token");
      if (token) this.token = token;
    }
  }

  private async parseError(res: Response): Promise<string> {
    try {
      const data = (await res.json()) as unknown;
      if (typeof data === "string") return data;
      if (data && typeof data === "object") {
        const detail = "detail" in data ? (data as { detail?: string }).detail : undefined;
        const message = "message" in data ? (data as { message?: string }).message : undefined;
        return detail || message || res.statusText;
      }
      return res.statusText;
    } catch {
      return res.statusText;
    }
  }

  private async request(endpoint: string, options: RequestInit = {}): Promise<unknown> {
    if (!this.token) {
      this.loadToken();
    }

    const headers = new Headers(options.headers);
    headers.set("Content-Type", "application/json");

    if (this.token) {
      headers.set("Authorization", `Bearer ${this.token}`);
    }

    const res = await fetch(`${API_URL}${endpoint}`, {
      ...options,
      headers,
    });

    if (!res.ok) {
      const message = await this.parseError(res);
      if (res.status === 401) {
        this.clearToken();
        throw new Error("Session expired. Please log in again.");
      }
      throw new Error(message || "Request failed");
    }

    if (res.status === 204) {
      return null;
    }

    const text = await res.text();
    if (!text) {
      return null;
    }

    try {
      return JSON.parse(text);
    } catch {
      return text;
    }
  }

  async signup(email: string, password: string) {
    return this.request("/auth/signup", {
      method: "POST",
      body: JSON.stringify({ email, password }),
    });
  }

  async login(email: string, password: string) {
    return this.request("/auth/login", {
      method: "POST",
      body: JSON.stringify({ email, password }),
    });
  }

  async sendMessage(message: string, conversationId?: string) {
    return this.request("/chat/", {
      method: "POST",
      body: JSON.stringify({ message, conversation_id: conversationId }),
    });
  }

  async getChatHistory(conversationId: string) {
    const params = new URLSearchParams({ conversation_id: conversationId }).toString();
    return this.request(`/chat/history?${params}`);
  }

  async getIdentity() {
    return this.request("/identity/");
  }

  async updateIdentity(payload: IdentityUpdatePayload) {
    return this.request("/identity/", {
      method: "PATCH",
      body: JSON.stringify(payload),
    });
  }

  async completeOnboarding(responses: OnboardingPayload) {
    return this.request("/onboarding/complete", {
      method: "POST",
      body: JSON.stringify(responses),
    });
  }
}

export const api = new ApiClient();
