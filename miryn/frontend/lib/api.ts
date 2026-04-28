import type {
  Conversation,
  EvolutionLogEntry,
  IdentityUpdatePayload,
  ImportStatus,
  Identity,
  MemorySnapshot,
  NotificationPreferences,
  OnboardingPayload,
  Session,
  User,
} from "@/lib/types";

const API_URL = process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000";

type AuthSession = {
  access_token: string;
  refresh_token?: string | null;
  is_new?: boolean;
};

class ApiClient {
  private token: string | null = null;
  private refreshTokenValue: string | null = null;
  private refreshRequest: Promise<AuthSession> | null = null;

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

  setSession(session: AuthSession | null) {
    this.setToken(session?.access_token ?? null);
    this.setRefreshToken(session?.refresh_token ?? null);
  }

  clearToken() {
    this.setSession(null);
  }

  loadToken() {
    if (typeof window !== "undefined") {
      this.token = localStorage.getItem("miryn_token");
      this.refreshTokenValue = localStorage.getItem("miryn_refresh_token");
    }
  }

  private setRefreshToken(token: string | null) {
    this.refreshTokenValue = token;
    if (typeof window !== "undefined") {
      if (token) {
        localStorage.setItem("miryn_refresh_token", token);
      } else {
        localStorage.removeItem("miryn_refresh_token");
      }
    }
  }

  private async parseError(res: Response): Promise<string> {
    try {
      const data = (await res.json()) as unknown;
      if (typeof data === "string") return data;
      if (data && typeof data === "object") {
        const detail = "detail" in data ? (data as { detail?: unknown }).detail : undefined;
        const message = "message" in data ? (data as { message?: unknown }).message : undefined;

        if (Array.isArray(detail) && detail.length > 0 && typeof detail[0] === "object" && detail[0] && "msg" in detail[0]) {
          return String((detail[0] as { msg?: unknown }).msg ?? res.statusText);
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
    const requestId =
      typeof crypto !== "undefined" && "randomUUID" in crypto
        ? crypto.randomUUID()
        : `${Date.now()}-${Math.random().toString(16).slice(2)}`;
    const isFormData = typeof FormData !== "undefined" && options.body instanceof FormData;
    if (!isFormData && !headers.has("Content-Type")) {
      headers.set("Content-Type", "application/json");
    }
    headers.set("X-Request-ID", requestId);

    if (this.token) {
      headers.set("Authorization", `Bearer ${this.token}`);
    }

    const res = await fetch(`${API_URL}${endpoint}`, {
      ...options,
      headers,
    });

    if (!res.ok) {
      const responseRequestId = res.headers.get("X-Request-ID") || requestId;
      if (res.status === 401 && !triedRefresh && endpoint !== "/auth/refresh" && this.refreshTokenValue) {
        try {
          const refreshed = await this.refreshSession();
          this.setSession(refreshed);
          return this.request(endpoint, options, true);
        } catch {
          this.clearToken();
          throw new Error(`Session expired. Please log in again. [req ${responseRequestId}]`);
        }
      }

      const message = await this.parseError(res);
      if (res.status === 401) {
        this.clearToken();
        throw new Error(`Session expired. Please log in again. [req ${responseRequestId}]`);
      }
      throw new Error(`${message || "Request failed"} [req ${responseRequestId}]`);
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

  private async refreshSession(): Promise<AuthSession> {
    if (this.refreshRequest) {
      return this.refreshRequest;
    }

    if (!this.refreshTokenValue) {
      throw new Error("Missing refresh token");
    }

    this.refreshRequest = fetch(`${API_URL}/auth/refresh`, {
      method: "POST",
      headers: {
        "Content-Type": "application/json",
      },
      body: JSON.stringify({ refresh_token: this.refreshTokenValue }),
    })
      .then(async (res) => {
        if (!res.ok) {
          const message = await this.parseError(res);
          throw new Error(message || "Session expired");
        }
        return res.json() as Promise<AuthSession>;
      })
      .finally(() => {
        this.refreshRequest = null;
      });

    return this.refreshRequest;
  }

  async ensureAuthenticated() {
    this.loadToken();
    if (this.token) {
      return true;
    }
    if (!this.refreshTokenValue) {
      return false;
    }

    try {
      const refreshed = await this.refreshSession();
      this.setSession(refreshed);
      return true;
    } catch {
      this.clearToken();
      return false;
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
    }) as Promise<AuthSession>;
  }

  async googleLogin(idToken: string) {
    return this.request("/auth/google", {
      method: "POST",
      body: JSON.stringify({ id_token: idToken }),
    }) as Promise<AuthSession>;
  }

  async refreshToken() {
    return this.refreshSession();
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

  async getMe() {
    return this.request("/auth/me") as Promise<User>;
  }

  async updatePassword(currentPassword: string, newPassword: string) {
    return this.request("/auth/password", {
      method: "PATCH",
      body: JSON.stringify({ current_password: currentPassword, new_password: newPassword }),
    });
  }

  async getSessions() {
    return this.request("/auth/sessions") as Promise<Session[]>;
  }

  async deleteAccount() {
    return this.request("/auth/account", {
      method: "DELETE",
    });
  }

  async logout() {
    this.clearToken();
  }

  async listConversations() {
    return this.request("/chat/conversations") as Promise<Conversation[]>;
  }

  async updateConversationTitle(id: string, title: string) {
    return this.request(`/chat/conversations/${id}/title`, {
      method: "PATCH",
      body: JSON.stringify({ title }),
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

    let res = await fetch(`${API_URL}/chat/stream`, {
      method: "POST",
      headers: {
        "Content-Type": "application/json",
        Authorization: `Bearer ${this.token}`,
      },
      body: JSON.stringify({ message, conversation_id: conversationId }),
    });

    if (res.status === 401 && this.refreshTokenValue) {
      try {
        const refreshed = await this.refreshSession();
        this.setSession(refreshed);
        res = await fetch(`${API_URL}/chat/stream`, {
          method: "POST",
          headers: {
            "Content-Type": "application/json",
            Authorization: `Bearer ${this.token}`,
          },
          body: JSON.stringify({ message, conversation_id: conversationId }),
        });
      } catch {
        this.setSession(null);
        throw new Error("Session expired. Please log in again.");
      }
    }

    if (!res.ok) {
      if (res.status === 401) {
        this.clearToken();
        throw new Error("Session expired. Please log in again.");
      }
      throw new Error(await res.text());
    }

    const reader = res.body?.getReader();
    if (!reader) {
      throw new Error("Stream unavailable");
    }

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

  async getIdentity(): Promise<Identity> {
    return this.request("/identity/") as Promise<Identity>;
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

  async updateNotificationPreferences(prefs: NotificationPreferences) {
    return this.request("/notifications/preferences", {
      method: "PATCH",
      body: JSON.stringify(prefs),
    });
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

  async importChatGPT(file: File) {
    if (!this.token) this.loadToken();
    const form = new FormData();
    form.append("file", file);
    const res = await fetch(`${API_URL}/import/chatgpt`, {
      method: "POST",
      headers: {
        Authorization: `Bearer ${this.token}`,
      },
      body: form,
    });
    if (!res.ok) {
      const message = await this.parseError(res);
      throw new Error(message || "Import failed");
    }
    return res.json();
  }

  async getImportStatus() {
    return this.request("/import/status") as Promise<ImportStatus>;
  }
}

export const api = new ApiClient();
