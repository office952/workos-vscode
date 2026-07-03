import { beforeAll, beforeEach, describe, expect, it, vi } from 'vitest';

import { installCsrfFetchHeaderSupport, readCookieValue } from './csrf';

const mockFetch = vi.fn(async () => new Response('{}', { status: 200 }));

function setCookie(name: string, value: string) {
  document.cookie = `${name}=${encodeURIComponent(value)}; path=/`;
}

describe('csrf helpers', () => {
  it('reads cookie value safely', () => {
    const value = readCookieValue('csrf_token', 'a=1; csrf_token=token-123; x=9');
    expect(value).toBe('token-123');
  });

  it('returns null for missing cookie', () => {
    expect(readCookieValue('csrf_token', 'a=1; b=2')).toBeNull();
  });
});

describe('csrf fetch header support', () => {
  beforeAll(() => {
    vi.stubGlobal('fetch', mockFetch as unknown as typeof fetch);
    installCsrfFetchHeaderSupport();
  });

  beforeEach(() => {
    mockFetch.mockClear();
    document.cookie = 'csrf_token=; Max-Age=0; path=/';
    document.cookie = 'other_cookie=1; path=/';
  });

  it('injects X-CSRF-Token for mutating cookie-capable request', async () => {
    setCookie('csrf_token', 'csrf-abc');

    await fetch('/api/v1/entities/orders', {
      method: 'POST',
      credentials: 'include',
      headers: {
        'Content-Type': 'application/json',
      },
      body: JSON.stringify({ test: true }),
    });

    const firstCall = mockFetch.mock.calls[0] as unknown[] | undefined;
    expect(firstCall).toBeDefined();
    const options = (firstCall && firstCall.length > 1 ? firstCall[1] : {}) as RequestInit;
    const headers = new Headers(options.headers);

    expect(headers.get('x-csrf-token')).toBe('csrf-abc');
  });

  it('does not inject for bearer-auth requests', async () => {
    setCookie('csrf_token', 'csrf-abc');

    await fetch('/api/v1/entities/orders', {
      method: 'POST',
      credentials: 'include',
      headers: {
        Authorization: 'Bearer test-token',
      },
    });

    const firstCall = mockFetch.mock.calls[0] as unknown[] | undefined;
    expect(firstCall).toBeDefined();
    const options = (firstCall && firstCall.length > 1 ? firstCall[1] : {}) as RequestInit;
    const headers = new Headers(options.headers);

    expect(headers.get('x-csrf-token')).toBeNull();
  });

  it('does not inject for token exchange boundary', async () => {
    setCookie('csrf_token', 'csrf-abc');

    await fetch('/api/v1/auth/token/exchange', {
      method: 'POST',
      credentials: 'include',
    });

    const firstCall = mockFetch.mock.calls[0] as unknown[] | undefined;
    expect(firstCall).toBeDefined();
    const options = (firstCall && firstCall.length > 1 ? firstCall[1] : {}) as RequestInit;
    const headers = new Headers(options.headers);

    expect(headers.get('x-csrf-token')).toBeNull();
  });

  it('does not inject for non-mutating methods', async () => {
    setCookie('csrf_token', 'csrf-abc');

    await fetch('/api/v1/system/version', {
      method: 'GET',
      credentials: 'include',
    });

    const firstCall = mockFetch.mock.calls[0] as unknown[] | undefined;
    expect(firstCall).toBeDefined();
    const options = (firstCall && firstCall.length > 1 ? firstCall[1] : {}) as RequestInit;
    const headers = new Headers(options.headers);

    expect(headers.get('x-csrf-token')).toBeNull();
  });
});
