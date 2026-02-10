import { DefaultSession } from "next-auth";

declare module "next-auth" {
  interface Session {
    expiresAt?: number | null;
    user?: DefaultSession["user"] & {
      id?: string;
    };
  }

  interface User {
    id: string;
    email?: string | null;
    accessToken?: string;
    refreshToken?: string | null;
    expiresAt?: number | null;
  }
}

declare module "next-auth/jwt" {
  interface JWT {
    accessToken?: string;
    refreshToken?: string | null;
    expiresAt?: number | null;
  }
}
