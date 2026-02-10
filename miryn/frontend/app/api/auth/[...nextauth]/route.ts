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

type AuthUser = {
  id: string;
  email: string;
  accessToken: string;
  refreshToken: string | null;
  expiresAt: number | null;
};

type ExtendedJWT = JWT & {
  accessToken?: string;
  refreshToken?: string | null;
  expiresAt?: number | null;
  error?: string;
};

const isAuthUser = (user: unknown): user is AuthUser => {
  if (!user || typeof user !== "object") return false;
  return "accessToken" in user && "refreshToken" in user;
};

async function refreshAccessToken(token: ExtendedJWT): Promise<ExtendedJWT> {
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
  } catch (error: unknown) {
    const message =
      error instanceof Error && error.message ? error.message : "unknown";
    console.error("Access token refresh failed", { message });
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
      async authorize(credentials): Promise<AuthUser | null> {
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
          };
        } catch (error: unknown) {
          clearTimeout(timeout);
          const safeMessage =
            error instanceof Error && error.message ? error.message : "Unknown error";
          const safeName =
            error instanceof Error && error.name ? error.name : "Error";
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
      const nextToken = token as ExtendedJWT;

      if (user && isAuthUser(user)) {
        nextToken.accessToken = user.accessToken;
        nextToken.refreshToken = user.refreshToken;
        nextToken.expiresAt = user.expiresAt;
        nextToken.error = undefined;
        return nextToken;
      }

      if (!nextToken.expiresAt || !nextToken.accessToken) {
        return nextToken;
      }

      const bufferMs = 60_000;
      if (Date.now() < nextToken.expiresAt - bufferMs) {
        return nextToken;
      }

      return refreshAccessToken(nextToken);
    },
    async session({ session, token }) {
      const nextToken = token as ExtendedJWT;
      if (nextToken?.error) {
        (session as { error?: string }).error = nextToken.error;
      }
      return session;
    },
  },
});

export { handler as GET, handler as POST };
