import type { EvolutionLogEntry, IdentityUpdatePayload, MemorySnapshot, OnboardingPayload } from "@/lib/types";

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
        const detail = "detail" in data ? (data as any).detail : undefined;
        const message = "message" in data ? (data as any).message : undefined;
        
        if (Array.isArray(detail) && detail.length > 0 && detail[0].msg) {
          return detail[0].msg;
        }
        
        if (typeof detail === "string") return detail;
        if (typeof message === "string") return message;
        return String(detail || message || res.statusText);
      }
      return res.statusText;
    } catch {
      return res.statusText;
    }
  }

  private async request(endpoint: string, options: RequestInit = {}, triedRefresh = false): Promise<unknown> {
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
      if (res.status === 401 && !triedRefresh) {
        try {
          const refreshed = await this.refreshToken();
          if (refreshed?.access_token) {
            this.setToken(refreshed.access_token);
            return this.request(endpoint, options, true);
          }
        } catch {
          this.clearToken();
          throw new Error("Session expired. Please log in again.");
        }
      }

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

  async googleLogin(idToken: string) {
    return this.request("/auth/google", {
      method: "POST",
      body: JSON.stringify({ id_token: idToken }),
    });
  }

  async refreshToken() {
    return this.request("/auth/refresh", {
      method: "POST",
    });
  }

  async forgotPassword(email: string) {
    return this.request("/auth/forgot-password", {
      method: "POST",
      body: JSON.stringify({ email }),
    });
  }

  async resetPassword(token: string, newPassword: string) {
    return this.request("/auth/reset-password", {
      method: "POST",
      body: JSON.stringify({ token, new_password: newPassword }),
    });
  }

  async sendMessage(message: string, conversationId?: string) {
    return this.request("/chat/", {
      method: "POST",
      body: JSON.stringify({ message, conversation_id: conversationId }),
    });
  }

  async *streamMessage(message: string, conversationId?: string) {
    if (!this.token) {
      this.loadToken();
    }

    const res = await fetch(`${API_URL}/chat/stream`, {
      method: "POST",
      headers: {
        "Content-Type": "application/json",
        "Authorization": `Bearer ${this.token}`,
      },
      body: JSON.stringify({ message, conversation_id: conversationId }),
    });

    if (!res.ok) {
      throw new Error(await res.text());
    }

    const reader = res.body.getReader();
    const decoder = new TextDecoder();
    let buffer = "";
    while (true) {
      const { done, value } = await reader.read();
      if (done) break;
      buffer += decoder.decode(value, { stream: true });
      const lines = buffer.split("\n\n");
      buffer = lines.pop() || "";
      for (const line of lines) {
        if (!line.startsWith("data: ")) continue;
        const parsed = JSON.parse(line.slice(6));
        yield parsed;
      }
    }
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

  async getEvolution(): Promise<EvolutionLogEntry[]> {
    return this.request("/identity/evolution") as Promise<EvolutionLogEntry[]>;
  }

  async completeOnboarding(responses: OnboardingPayload) {
    return this.request("/onboarding/complete", {
      method: "POST",
      body: JSON.stringify(responses),
    });
  }

  async listPresets() {
    return this.request("/onboarding/presets");
  }

  async generateTool(intent: string) {
    return this.request("/tools/generate", {
      method: "POST",
      body: JSON.stringify({ intent, tool_type: "python" }),
    });
  }

  async listPendingTools() {
    return this.request("/tools/pending");
  }

  async approveTool(toolId: string) {
    return this.request("/tools/approve", {
      method: "POST",
      body: JSON.stringify({ tool_id: toolId }),
    });
  }

  async listNotifications() {
    return this.request("/notifications/");
  }

  async markNotificationRead(id: string) {
    return this.request(`/notifications/read/${id}`, {
      method: "POST",
    });
  }

  async getMemory(): Promise<MemorySnapshot> {
    return this.request("/memory/") as Promise<MemorySnapshot>;
  }

  async deleteMemory(id: string) {
    return this.request(`/memory/${id}`, {
      method: "DELETE",
    });
  }
}

export const api = new ApiClient();
