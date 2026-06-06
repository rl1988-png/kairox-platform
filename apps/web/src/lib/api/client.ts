import type { ApiErrorBody } from '@kairox/shared';

const API_URL = process.env.NEXT_PUBLIC_API_URL ?? 'http://localhost:8000';

let accessToken: string | null = null;
let csrfToken: string | null = null;

export function setAccessToken(token: string | null) {
  accessToken = token;
}

export function getAccessToken() {
  return accessToken;
}

export function setCsrfToken(token: string | null) {
  csrfToken = token;
}

export function getCsrfToken() {
  return csrfToken;
}

export class ApiError extends Error {
  constructor(
    public code: string,
    message: string,
    public status: number,
    public details?: Record<string, unknown>,
  ) {
    super(message);
  }
}

interface RequestOptions extends Omit<RequestInit, 'body'> {
  body?: unknown;
  auth?: boolean;
  csrf?: boolean;
}

export async function apiRequest<T>(path: string, options: RequestOptions = {}): Promise<T> {
  const { body, auth = true, csrf = false, headers: customHeaders, ...rest } = options;

  const headers: Record<string, string> = {
    'Content-Type': 'application/json',
    ...(customHeaders as Record<string, string>),
  };

  if (auth && accessToken) {
    headers.Authorization = `Bearer ${accessToken}`;
  }

  if (csrf && csrfToken) {
    headers['X-CSRF-Token'] = csrfToken;
  }

  const response = await fetch(`${API_URL}${path}`, {
    ...rest,
    headers,
    credentials: 'include',
    body: body !== undefined ? JSON.stringify(body) : undefined,
  });

  if (!response.ok) {
    const errorBody = (await response.json().catch(() => null)) as ApiErrorBody | null;
    if (errorBody?.error) {
      throw new ApiError(
        errorBody.error.code,
        errorBody.error.message,
        response.status,
        errorBody.error.details,
      );
    }
    throw new ApiError('UNKNOWN', response.statusText, response.status);
  }

  if (response.status === 204) return undefined as T;
  return response.json() as Promise<T>;
}

export function applyAuthResponse(data: {
  access_token: string;
  csrf_token: string;
}): void {
  setAccessToken(data.access_token);
  setCsrfToken(data.csrf_token);
}

export function clearAuthState(): void {
  setAccessToken(null);
  setCsrfToken(null);
}
