const MUTATING_METHODS = new Set(['POST', 'PUT', 'PATCH', 'DELETE']);
const CSRF_COOKIE_NAME = 'csrf_token';
const CSRF_HEADER_NAME = 'X-CSRF-Token';
const CSRF_EXCLUDED_PATHS = new Set(['/api/v1/auth/token/exchange']);
const FETCH_PATCH_FLAG = '__workosCsrfFetchPatched';

function getCookieSource(): string {
  if (typeof document === 'undefined') {
    return '';
  }
  return document.cookie || '';
}

export function readCookieValue(name: string, cookieSource = getCookieSource()): string | null {
  if (!cookieSource || !name) {
    return null;
  }

  const pairs = cookieSource.split(';');
  const prefix = `${name}=`;

  for (const rawPair of pairs) {
    const pair = rawPair.trim();
    if (!pair.startsWith(prefix)) {
      continue;
    }
    const value = pair.slice(prefix.length);
    if (!value) {
      return null;
    }
    try {
      return decodeURIComponent(value);
    } catch {
      return value;
    }
  }

  return null;
}

function isMutatingMethod(method: string): boolean {
  return MUTATING_METHODS.has(method.toUpperCase());
}

function hasBearerAuthorization(headers: Headers): boolean {
  const auth = headers.get('authorization');
  if (!auth) {
    return false;
  }
  return auth.trim().toLowerCase().startsWith('bearer ');
}

function resolveRequestPath(input: RequestInfo | URL): string {
  try {
    if (typeof input === 'string') {
      return new URL(input, globalThis.location?.origin || 'http://localhost').pathname;
    }
    if (input instanceof URL) {
      return input.pathname;
    }
    if (typeof Request !== 'undefined' && input instanceof Request) {
      return new URL(input.url, globalThis.location?.origin || 'http://localhost').pathname;
    }
  } catch {
    return '';
  }
  return '';
}

function isCookieCapableRequest(credentials: RequestCredentials | undefined): boolean {
  if (!credentials) {
    return true;
  }
  return credentials !== 'omit';
}

function shouldAttachCsrfHeader(params: {
  method: string;
  path: string;
  credentials: RequestCredentials | undefined;
  headers: Headers;
  csrfToken: string | null;
}): boolean {
  const { method, path, credentials, headers, csrfToken } = params;

  if (!isMutatingMethod(method)) {
    return false;
  }

  if (CSRF_EXCLUDED_PATHS.has(path)) {
    return false;
  }

  if (!isCookieCapableRequest(credentials)) {
    return false;
  }

  if (!csrfToken) {
    return false;
  }

  if (hasBearerAuthorization(headers)) {
    return false;
  }

  if (headers.has('x-csrf-token')) {
    return false;
  }

  return true;
}

export function installCsrfFetchHeaderSupport(): void {
  if (typeof globalThis.fetch !== 'function') {
    return;
  }

  const patchedGlobal = globalThis as typeof globalThis & {
    [FETCH_PATCH_FLAG]?: boolean;
  };

  if (patchedGlobal[FETCH_PATCH_FLAG]) {
    return;
  }

  const originalFetch = globalThis.fetch.bind(globalThis);

  globalThis.fetch = ((input: RequestInfo | URL, init?: RequestInit) => {
    const method = (init?.method || (typeof Request !== 'undefined' && input instanceof Request ? input.method : 'GET')).toUpperCase();
    const credentials = init?.credentials || (typeof Request !== 'undefined' && input instanceof Request ? input.credentials : undefined);
    const headers = new Headers(init?.headers || (typeof Request !== 'undefined' && input instanceof Request ? input.headers : undefined));
    const path = resolveRequestPath(input);
    const csrfToken = readCookieValue(CSRF_COOKIE_NAME);

    if (
      shouldAttachCsrfHeader({
        method,
        path,
        credentials,
        headers,
        csrfToken,
      })
    ) {
      headers.set(CSRF_HEADER_NAME, csrfToken as string);
    }

    return originalFetch(input, {
      ...init,
      headers,
    });
  }) as typeof fetch;

  patchedGlobal[FETCH_PATCH_FLAG] = true;
}
