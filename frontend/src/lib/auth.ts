import { getAPIBaseURL } from './config';

function getAuthUrl(path: string): string {
  const baseUrl = getAPIBaseURL();
  return `${baseUrl}${path}`;
}

async function parseJsonSafely(response: Response): Promise<unknown> {
  const text = await response.text();
  if (!text) return null;
  try {
    return JSON.parse(text) as unknown;
  } catch {
    return text;
  }
}

function getCurrentPath(): string {
  const { pathname, search, hash } = window.location;
  return `${pathname}${search}${hash}` || '/dashboard';
}

class RPApi {
  async getCurrentUser() {
    const response = await fetch(getAuthUrl('/api/v1/auth/me'), {
      method: 'GET',
      credentials: 'include',
      headers: { Accept: 'application/json' },
    });

    if (response.status === 401) return null;

    if (!response.ok) {
      const payload = await parseJsonSafely(response);
      const message = typeof payload === 'object' && payload && 'detail' in payload
        ? String((payload as { detail?: unknown }).detail)
        : 'Failed to get user info';
      throw new Error(message);
    }

    return await response.json();
  }

  login(fromUrl?: string) {
    const target = encodeURIComponent(fromUrl || getCurrentPath());
    window.location.assign(getAuthUrl(`/api/v1/auth/login?from_url=${target}`));
  }

  async logout() {
    const response = await fetch(getAuthUrl('/api/v1/auth/logout'), {
      method: 'GET',
      credentials: 'include',
      headers: { Accept: 'application/json' },
    });

    const payload = await parseJsonSafely(response);

    if (!response.ok) {
      const message = typeof payload === 'object' && payload && 'detail' in payload
        ? String((payload as { detail?: unknown }).detail)
        : 'Failed to logout';
      throw new Error(message);
    }

    const redirectUrl = typeof payload === 'object' && payload && 'redirect_url' in payload
      ? String((payload as { redirect_url?: unknown }).redirect_url || '')
      : '';

    return { redirectUrl };
  }
}

export const authApi = new RPApi();
