import NextAuth from "next-auth";
import CredentialsProvider from "next-auth/providers/credentials";
import type { JWT } from "next-auth/jwt";

const API_URL = process.env.NEXT_PUBLIC_API_URL;
const REQUEST_TIMEOUT_MS = 10_000;

if (!API_URL) {
  throw new Error("NEXT_PUBLIC_API_URL is not configured");
}

type AuthSuccess = {
  access_token: string;
  refresh_token?: string;
  expires_in?: number;
  user?: { id?: string; email?: string };
};

type RefreshResponse = {
  access_token: string;
  refresh_token?: string;
  expires_in?: number;
};

async function refreshAccessToken(token: JWT): Promise<JWT> {
  if (!token.refreshToken) {
    return {
      ...token,
      accessToken: undefined,
      expiresAt: null,
      error: "RefreshAccessTokenError",
    };
  }

  try {
    const response = await fetch(`${API_URL}/auth/refresh`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ refresh_token: token.refreshToken }),
    });

    if (!response.ok) {
      throw new Error("Failed to refresh access token");
    }

    const payload = (await response.json()) as RefreshResponse;
    return {
      ...token,
      accessToken: payload.access_token,
      refreshToken: payload.refresh_token ?? token.refreshToken,
      expiresAt: payload.expires_in ? Date.now() + payload.expires_in * 1000 : null,
      error: undefined,
    };
  } catch (error: any) {
    console.error("Access token refresh failed", { message: error?.message || "unknown" });
    return {
      ...token,
      accessToken: undefined,
      expiresAt: null,
      error: "RefreshAccessTokenError",
    };
  }
}

const handler = NextAuth({
  providers: [
    CredentialsProvider({
      name: "Credentials",
      credentials: {
        email: { label: "Email", type: "text" },
        password: { label: "Password", type: "password" },
      },
      async authorize(credentials) {
        if (!credentials?.email || !credentials?.password) {
          return null;
        }

        const controller = new AbortController();
        const timeout = setTimeout(() => controller.abort(), REQUEST_TIMEOUT_MS);
        try {
          const response = await fetch(`${API_URL}/auth/login`, {
            method: "POST",
            headers: { "Content-Type": "application/json" },
            body: JSON.stringify({
              email: credentials.email,
              password: credentials.password,
            }),
            signal: controller.signal,
          });

          const payload = (await response.json().catch(() => null)) as
            | AuthSuccess
            | { detail?: string; message?: string }
            | null;

          clearTimeout(timeout);

          if (!response.ok || !payload || !("access_token" in payload)) {
            return null;
          }

          const expiresAt = payload.expires_in
            ? Date.now() + payload.expires_in * 1000
            : null;

          return {
            id: payload.user?.id || credentials.email,
            email: credentials.email,
            accessToken: payload.access_token,
            refreshToken: payload.refresh_token || null,
            expiresAt,
          } as any;
        } catch (error: any) {
          clearTimeout(timeout);
          const safeMessage = typeof error?.message === "string" ? error.message : "Unknown error";
          const safeName = typeof error?.name === "string" ? error.name : "Error";
          console.error("NextAuth authorize failed", { name: safeName, message: safeMessage });
          return null;
        }
      },
    }),
  ],
  pages: {
    signIn: "/login",
    error: "/login",
  },
  session: { strategy: "jwt" },
  callbacks: {
    async jwt({ token, user }) {
      if (user) {
        token.accessToken = (user as any).accessToken;
        token.refreshToken = (user as any).refreshToken;
        token.expiresAt = (user as any).expiresAt;
        token.error = undefined;
        return token;
      }

      if (!token.expiresAt || !token.accessToken) {
        return token;
      }

      const bufferMs = 60_000;
      if (Date.now() < (token.expiresAt as number) - bufferMs) {
        return token;
      }

      return refreshAccessToken(token);
    },
    async session({ session, token }) {
      if (token?.error) {
        (session as any).error = token.error;
      }
      return session;
    },
  },
});

export { handler as GET, handler as POST };