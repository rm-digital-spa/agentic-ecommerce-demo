/**
 * Node-runtime session helpers for Server Components and Route Handlers.
 * (Middleware can't use next/headers — see session-crypto.ts for that.)
 */
import { cookies } from "next/headers";
import {
  SESSION_COOKIE,
  signSession,
  verifySessionToken,
  type SessionPayload,
} from "./session-crypto";

export { SESSION_COOKIE };

const MAX_AGE_SECONDS = 60 * 60 * 8; // 8 hours

export async function getSession(): Promise<SessionPayload | null> {
  const store = await cookies();
  const token = store.get(SESSION_COOKIE)?.value;
  if (!token) return null;
  return verifySessionToken(token);
}

export const sessionCookieOptions = {
  httpOnly: true,
  secure: process.env.NODE_ENV === "production",
  sameSite: "lax" as const,
  path: "/",
  maxAge: MAX_AGE_SECONDS,
};

export async function buildSessionCookieValue(
  username: string,
  password: string,
): Promise<string> {
  const credentials = Buffer.from(`${username}:${password}`).toString("base64");
  return signSession({ username, credentials });
}
