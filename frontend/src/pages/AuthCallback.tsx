import { useEffect } from 'react';
import { authApi } from '../lib/auth';

export default function AuthCallback() {
  useEffect(() => {
    let cancelled = false;

    const finalizeAuth = async () => {
      try {
        const data = await authApi.getCurrentUser();
        if (!cancelled && (data?.id || data?.email || data?.name)) {
          window.location.href = '/';
          return;
        }
      } catch {
        // no-op: handled by fallback redirect below
      }

      if (!cancelled) {
        const msg = encodeURIComponent('Authentication session was not established');
        window.location.href = `/auth/error?msg=${msg}`;
      }
    };

    void finalizeAuth();
    return () => {
      cancelled = true;
    };
  }, []);

  return (
    <div className="min-h-screen flex items-center justify-center">
      <div className="text-center">
        <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-blue-600 mx-auto mb-4"></div>
        <p className="text-gray-600">Processing authentication...</p>
      </div>
    </div>
  );
}
