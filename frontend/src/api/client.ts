const API_BASE = "/api";

export class ApiError extends Error {
  constructor(
    public status: number,
    public code: string,
    message: string,
    public detail: Record<string, unknown> = {},
  ) {
    super(message);
  }

  get isNetwork(): boolean {
    return this.status === 0;
  }
}

type RequestOptions = {
  method?: "GET" | "POST" | "PUT" | "DELETE";
  body?: unknown;
  signal?: AbortSignal;
};

function errorFromBody(status: number, body: unknown): ApiError {
  const detail = (body as { detail?: unknown } | null)?.detail;
  if (detail && typeof detail === "object" && !Array.isArray(detail) && "code" in detail) {
    const d = detail as Record<string, unknown>;
    return new ApiError(status, String(d.code), String(d.message ?? d.code), d);
  }
  if (Array.isArray(detail)) {
    return new ApiError(status, "validation_error", "Некорректные данные запроса", { errors: detail });
  }
  if (status === 401) return new ApiError(status, "unauthorized", "Нужно войти");
  if (status === 403) return new ApiError(status, "forbidden", "Недостаточно прав");
  if (status === 404) return new ApiError(status, "not_found", "Не найдено");
  return new ApiError(status, "http_error", typeof detail === "string" ? detail : `Ошибка сервера (${status})`);
}

export async function api<T>(path: string, options: RequestOptions = {}): Promise<T> {
  let response: Response;
  try {
    response = await fetch(`${API_BASE}${path}`, {
      method: options.method ?? "GET",
      credentials: "same-origin",
      headers: options.body === undefined ? undefined : { "Content-Type": "application/json" },
      body: options.body === undefined ? undefined : JSON.stringify(options.body),
      signal: options.signal,
    });
  } catch (err) {
    if (err instanceof DOMException && err.name === "AbortError") throw err;
    throw new ApiError(0, "network_error", "Нет связи с сервером. Проверьте подключение и повторите.");
  }

  if (response.status === 204) return undefined as T;
  let body: unknown = null;
  const text = await response.text();
  if (text) {
    try {
      body = JSON.parse(text);
    } catch {
      body = null;
    }
  }
  if (!response.ok) throw errorFromBody(response.status, body);
  return body as T;
}
