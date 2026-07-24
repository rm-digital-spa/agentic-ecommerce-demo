import { NextResponse } from "next/server";
import { buildSessionCookieValue, sessionCookieOptions, SESSION_COOKIE } from "@/lib/session";

const API_URL = process.env.API_URL || "http://localhost:8000";

export async function POST(request: Request) {
  const body = await request.json().catch(() => null);
  const username = typeof body?.username === "string" ? body.username : "";
  const password = typeof body?.password === "string" ? body.password : "";

  if (!username || !password) {
    return NextResponse.json(
      { error: "Username and password are required" },
      { status: 400 },
    );
  }

  const basic = Buffer.from(`${username}:${password}`).toString("base64");
  const verifyResponse = await fetch(`${API_URL}/`, {
    headers: { Authorization: `Basic ${basic}` },
  });

  if (!verifyResponse.ok) {
    return NextResponse.json(
      { error: "Invalid username or password" },
      { status: 401 },
    );
  }

  const cookieValue = await buildSessionCookieValue(username, password);
  const response = NextResponse.json({ username });
  response.cookies.set(SESSION_COOKIE, cookieValue, sessionCookieOptions);
  return response;
}
