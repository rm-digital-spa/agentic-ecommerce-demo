/**
 * fetch wrapper that calls the same-origin backend proxy (which attaches the
 * server-held session credentials) and redirects to /login on 401.
 */
export async function apiFetch(path: string, options: RequestInit = {}): Promise<Response> {
  const response = await fetch(`/api/backend${path}`, options);

  if (
    response.status === 401 &&
    typeof window !== "undefined" &&
    window.location.pathname !== "/login"
  ) {
    window.location.href = "/login";
  }

  return response;
}
