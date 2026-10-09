import type {
  AuthConfig,
  ComparePayload,
  CompareReport,
  Conversation,
  DemoPersonaCard,
  DemoPersonaDetail,
  EvolutionLogEntry,
  IdentityUpdatePayload,
  ImportStatus,
  Identity,
  MemorySnapshot,
  Message,
  NotificationPreferences,
  OnboardingPayload,
  SanctuaryCheckinResponse,
  SanctuaryPersona,
  Session,
  User,
} from "@/lib/types";

const configuredApiUrl = process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000";
// ponytail: use one loopback host in local development; mixed localhost/127 DNS can resolve to different address families.
const API_URL = typeof window !== "undefined" && window.location.hostname === "127.0.0.1"
  ? configuredApiUrl.replace(/^http:\/\/localhost(?=:)/, "http://127.0.0.1")
  : configuredApiUrl;

type AuthSession = {
  access_token: string;
  refresh_token?: string | null;
  is_new?: boolean;
};

class ApiClient {
  private token: string | null = null;
  private refreshTokenValue: string | null = null;
  private refreshRequest: Promise<AuthSession> | null = null;
  private requestCache = new Map<string, { expiresAt: number; value: unknown }>();
  private posthogInitialized = false;

  constructor() {
    if (typeof window !== "undefined") {
      this.loadToken();
    }
  }

  private capture(event: string, properties?: Record<string, unknown>) {
    if (typeof window === "undefined") return;
    try {
      const ph = (window as Window & { posthog?: { capture?: (event: string, properties?: Record<string, unknown>) => void } }).posthog;
      if (ph?.capture) {
        ph.capture(event, properties);
      }
    } catch {
      // silently fail
    }
  }

  private identifyUser(userId: string, properties?: Record<string, unknown>) {
    if (typeof window === "undefined") return;
    try {
      const ph = (window as Window & { posthog?: { capture?: (event: string, properties?: Record<string, unknown>) => void; identify?: (userId: string, properties?: Record<string, unknown>) => void } }).posthog;
      if (ph?.identify) {
        ph.identify(userId, properties);
      }
    } catch {
      // silently fail
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
    if (session?.is_new) {
      this.capture("signup");
    }
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

  private async request(endpoint: string, options: RequestInit = {}, triedRefresh = false, includeHeaders = false): Promise<unknown> {
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
          return this.request(endpoint, options, true, includeHeaders);
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
      return includeHeaders ? { data: null, headers: res.headers } : null;
    }

    const text = await res.text();
    if (!text) {
      return null;
    }

    let data: unknown;
    try {
      data = JSON.parse(text);
    } catch {
      data = text;
    }
    return includeHeaders ? { data, headers: res.headers } : data;
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

  async signup(email: string, password: string, fullName?: string) {
    return this.request("/auth/signup", {
      method: "POST",
      body: JSON.stringify({ email, password, full_name: fullName?.trim() || null }),
    });
  }

  async getAuthConfig(): Promise<AuthConfig> {
    return this.request("/auth/config") as Promise<AuthConfig>;
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

  async setConversationPinned(id: string, pinned: boolean) {
    return this.request(`/chat/conversations/${id}/pin`, {
      method: "PATCH",
      body: JSON.stringify({ pinned }),
    });
  }

  async deleteConversation(id: string) {
    return this.request(`/chat/conversations/${id}`, {
      method: "DELETE",
    });
  }

  async clearConversations() {
    return this.request("/chat/conversations", {
      method: "DELETE",
    });
  }

  async sendMessage(message: string, conversationId?: string) {
    this.capture("chat_message_sent", { has_conversation: !!conversationId });
    return this.request("/chat/", {
      method: "POST",
      body: JSON.stringify({ message, conversation_id: conversationId }),
    });
  }

  async *streamMessage(message: string, conversationId?: string, signal?: AbortSignal): AsyncGenerator<{ chunk?: string; error?: string; done?: boolean; conversation_id?: string }> {
    if (!this.token) {
      this.loadToken();
    }

    const send = () => fetch(`${API_URL}/chat/stream`, {
      method: "POST",
      headers: {
        "Content-Type": "application/json",
        ...(this.token ? { Authorization: `Bearer ${this.token}` } : {}),
      },
      body: JSON.stringify({ message, conversation_id: conversationId }),
      signal,
    });
    let res: Response;
    try { res = await send(); }
    catch (error) {
      if (signal?.aborted) throw error;
      throw new Error("Could not connect to Miryn. Check your connection and retry.");
    }

    if ((res.status === 401 || res.status === 403) && this.refreshTokenValue && !signal?.aborted) {
      try {
        const refreshed = await this.refreshSession();
        this.setSession(refreshed);
        res = await send();
      } catch {
        this.setSession(null);
        throw new Error("Session expired. Please log in again.");
      }
    }

    if (!res.ok) {
      if (res.status === 401 || res.status === 403) {
        this.clearToken();
        throw new Error("Session expired. Please log in again.");
      }
      throw new Error((await this.parseError(res)) || "Message could not be sent.");
    }

    const reader = res.body?.getReader();
    if (!reader) {
      throw new Error("Stream unavailable");
    }

    const decoder = new TextDecoder();
    let buffer = "";
    try {
      while (true) {
        let result: ReadableStreamReadResult<Uint8Array>;
        try { result = await reader.read(); }
        catch (error) {
          if (signal?.aborted) throw error;
          throw new Error("The reply was interrupted. You can retry your message.");
        }
        const { done, value } = result;
        if (done) break;
        buffer = (buffer + decoder.decode(value, { stream: true })).replace(/\r\n/g, "\n");
        const frames = buffer.split("\n\n");
        buffer = frames.pop() || "";
        for (const frame of frames) {
          const data = frame.split("\n").filter((line) => line.startsWith("data:")).map((line) => line.slice(5).trimStart()).join("\n");
          if (data) yield JSON.parse(data);
        }
      }
    } finally {
      reader.releaseLock();
    }
  }

  async *chatEvents(signal?: AbortSignal): AsyncGenerator<Record<string, unknown>> {
    if (!this.token) {
      this.loadToken();
    }

    const send = () => fetch(`${API_URL}/chat/events/stream`, {
      headers: {
        Accept: "text/event-stream",
        ...(this.token ? { Authorization: `Bearer ${this.token}` } : {}),
      },
      signal,
    });
    let res: Response;
    try {
      res = await send();
    } catch (error) {
      if (signal?.aborted) throw error;
      throw new Error("Could not connect to Miryn events.");
    }

    if ((res.status === 401 || res.status === 403) && this.refreshTokenValue && !signal?.aborted) {
      try {
        const refreshed = await this.refreshSession();
        this.setSession(refreshed);
        res = await send();
      } catch {
        this.setSession(null);
        throw new Error("Session expired. Please log in again.");
      }
    }

    if (!res.ok) {
      if (res.status === 401 || res.status === 403) {
        this.clearToken();
        throw new Error("Session expired. Please log in again.");
      }
      throw new Error((await this.parseError(res)) || "Event stream unavailable.");
    }

    const reader = res.body?.getReader();
    if (!reader) {
      throw new Error("Event stream unavailable");
    }

    const decoder = new TextDecoder();
    let buffer = "";
    try {
      while (true) {
        const { done, value } = await reader.read();
        if (done) break;
        buffer = (buffer + decoder.decode(value, { stream: true })).replace(/\r\n/g, "\n");
        const frames = buffer.split("\n\n");
        buffer = frames.pop() || "";
        for (const frame of frames) {
          const data = frame
            .split("\n")
            .filter((line) => line.startsWith("data:"))
            .map((line) => line.slice(5).trimStart())
            .join("\n");
          if (data) yield JSON.parse(data) as Record<string, unknown>;
        }
      }
    } finally {
      reader.releaseLock();
    }
  }

  async getChatHistory(conversationId: string, options: { before?: string } = {}): Promise<{ messages: Message[]; hasMore: boolean }> {
    const params = new URLSearchParams({ conversation_id: conversationId, limit: "50" });
    if (options.before) params.set("before", options.before);
    const result = await this.request(`/chat/history?${params}`, {}, false, true) as { data: Message[]; headers: Headers };
    return { messages: result.data || [], hasMore: result.headers.get("X-Has-More") === "true" };
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

  private getCached<T>(key: string): T | null {
    const hit = this.requestCache.get(key);
    if (!hit) return null;
    if (Date.now() > hit.expiresAt) {
      this.requestCache.delete(key);
      return null;
    }
    return hit.value as T;
  }

  private setCached(key: string, value: unknown, ttlMs = 20000) {
    this.requestCache.set(key, { value, expiresAt: Date.now() + ttlMs });
  }

  async getDemoPersonas(): Promise<DemoPersonaCard[]> {
    const response = await this.request("/analytics/demo/personas") as { personas?: DemoPersonaCard[] };
    return response.personas || [];
  }

  async seedDemoPersonas() {
    return this.request("/analytics/demo/seed", {
      method: "POST",
    }) as Promise<{ seeded_at: string; demo_password: string; personas: DemoPersonaCard[] }>;
  }

  async quickDemoLogin(email: string, password: string) {
    const session = await this.login(email, password);
    this.setSession(session);
    return session;
  }

  async getDemoPersonaDetail(userId: string): Promise<DemoPersonaDetail> {
    const key = `persona:${userId}`;
    const cached = this.getCached<DemoPersonaDetail>(key);
    if (cached) return cached;
    const detail = await (this.request(`/analytics/demo/persona/${userId}`) as Promise<DemoPersonaDetail>);
    this.setCached(key, detail, 30000);
    return detail;
  }

  async compareUsers(leftUserId: string, rightUserId: string): Promise<ComparePayload> {
    const params = new URLSearchParams({ left_user_id: leftUserId, right_user_id: rightUserId }).toString();
    const key = `compare:${params}`;
    const cached = this.getCached<ComparePayload>(key);
    if (cached) return cached;
    const payload = await (this.request(`/analytics/compare?${params}`) as Promise<ComparePayload>);
    this.setCached(key, payload, 15000);
    return payload;
  }

  async getComparisonReport(leftUserId: string, rightUserId: string): Promise<CompareReport> {
    const params = new URLSearchParams({ left_user_id: leftUserId, right_user_id: rightUserId }).toString();
    const key = `report:${params}`;
    const cached = this.getCached<CompareReport>(key);
    if (cached) return cached;
    const report = await (this.request(`/analytics/report?${params}`) as Promise<CompareReport>);
    this.setCached(key, report, 30000);
    return report;
  }

  async deleteMemory(id: string) {
    return this.request(`/memory/${id}`, {
      method: "DELETE",
    });
  }

  async purgeEpisodicMemory() {
    return this.request("/memory/purge/episodic", {
      method: "DELETE",
    });
  }

  async exportData(): Promise<Blob> {
    if (!this.token) this.loadToken();
    const res = await fetch(`${API_URL}/memory/export`, {
      headers: {
        Authorization: `Bearer ${this.token}`,
      },
    });
    if (!res.ok) {
      const err = await this.parseError(res);
      throw new Error(err || "Export failed");
    }
    return res.blob();
  }

  async createMemory(payload: { content: string; memory_tier?: "core" | "episodic" | "transient"; importance_score?: number }) {
    return this.request("/memory/", {
      method: "POST",
      body: JSON.stringify(payload),
    });
  }

  async getSanctuaryPersona(): Promise<SanctuaryPersona> {
    return this.request("/chat/sanctuary/persona") as Promise<SanctuaryPersona>;
  }

  async getSanctuaryData(): Promise<SanctuaryPersona> {
    return this.getSanctuaryPersona();
  }

  async postSanctuaryCheckin(payload: { emotion: string; energy?: string; notes?: string }): Promise<SanctuaryCheckinResponse> {
    return this.request("/chat/sanctuary/checkin", {
      method: "POST",
      body: JSON.stringify(payload),
    }) as Promise<SanctuaryCheckinResponse>;
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
