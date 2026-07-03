/**
 * Format FastAPI / API error payloads for human-readable UI messages.
 * Never surfaces `[object Object]` from structured `detail` objects.
 */

const DEFAULT_FALLBACK = "A apărut o eroare.";

export function formatApiErrorDetail(
  detail: unknown,
  fallback = DEFAULT_FALLBACK
): string {
  if (detail == null) {
    return fallback;
  }

  if (typeof detail === "string") {
    const trimmed = detail.trim();
    return trimmed || fallback;
  }

  if (typeof detail === "number" || typeof detail === "boolean") {
    return String(detail);
  }

  if (Array.isArray(detail)) {
    const parts = detail
      .map((item) => formatApiErrorDetail(item, ""))
      .filter((part) => part.length > 0);
    return parts.length > 0 ? parts.join("; ") : fallback;
  }

  if (typeof detail === "object") {
    const record = detail as Record<string, unknown>;

    if (typeof record.message === "string") {
      const message = record.message.trim();
      if (message) return message;
    }

    if (record.detail !== undefined) {
      const nested = formatApiErrorDetail(record.detail, "");
      if (nested) return nested;
    }

    if (typeof record.error === "string") {
      const error = record.error.trim();
      if (error) return error;
    }

    try {
      return JSON.stringify(detail);
    } catch {
      return fallback;
    }
  }

  return fallback;
}

export async function formatApiErrorResponse(
  res: Response,
  fallback?: string
): Promise<string> {
  const defaultFallback = fallback ?? `HTTP ${res.status}`;

  try {
    const body: unknown = await res.json();
    if (body && typeof body === "object") {
      const record = body as Record<string, unknown>;
      if ("detail" in record) {
        return formatApiErrorDetail(record.detail, defaultFallback);
      }
      if (typeof record.message === "string") {
        const message = record.message.trim();
        if (message) return message;
      }
    }
  } catch {
    try {
      const text = (await res.text()).trim();
      if (text) return text;
    } catch {
      // ignore
    }
  }

  return defaultFallback;
}

const INTAKE_CREATE_ROLES = new Set(["admin", "manager", "sales"]);

export function canCreateIntakeRequest(role: string | null | undefined): boolean {
  return INTAKE_CREATE_ROLES.has(String(role || "").trim().toLowerCase());
}

function permissionDeniedMessage(detail: Record<string, unknown>): string | null {
  if (detail.error !== "permission_denied") return null;
  const permission = String(detail.permission || "").trim();
  const role = String(detail.role || "").trim();

  if (permission === "intake.create") {
    if (role === "employee_mobile") {
      return (
        "Contul Employee Mobile nu poate crea cereri Work Intake. " +
        "Deschide aplicația operator/comercial pe http://127.0.0.1:3001 (backend admin :8002)."
      );
    }
    if (typeof detail.message === "string" && detail.message.trim()) {
      return detail.message.trim();
    }
    return (
      "Nu ai permisiunea să creezi cereri Work Intake. " +
      "Folosește un cont admin/manager/sales sau aplicația operator pe http://127.0.0.1:3001."
    );
  }

  if (permission === "client.create") {
    return (
      "Nu ai permisiunea să creezi clienți noi. " +
      "Folosește aplicația operator/comercial pe http://127.0.0.1:3001."
    );
  }

  if (typeof detail.message === "string" && detail.message.trim()) {
    return detail.message.trim();
  }

  if (permission) {
    return `Nu ai permisiunea necesară (${permission}).`;
  }

  return "Nu ai permisiunea pentru această acțiune.";
}

/** Extract human-readable message from SDK/axios-style thrown errors. */
export function formatApiErrorFromUnknown(
  error: unknown,
  fallback = DEFAULT_FALLBACK
): string {
  if (error == null) return fallback;

  if (typeof error === "string") {
    const trimmed = error.trim();
    return trimmed || fallback;
  }

  if (typeof error === "object") {
    const record = error as Record<string, unknown>;
    const response = record.response as Record<string, unknown> | undefined;
    const data = response?.data as Record<string, unknown> | undefined;
    const detail = data?.detail;

    if (detail && typeof detail === "object") {
      const permMessage = permissionDeniedMessage(detail as Record<string, unknown>);
      if (permMessage) return permMessage;
    }

    if (detail !== undefined) {
      const formatted = formatApiErrorDetail(detail, "");
      if (formatted) return formatted;
    }

    if (typeof record.message === "string") {
      const message = record.message.trim();
      if (message && !/^Request failed with status code \d+$/i.test(message)) {
        return message;
      }
    }
  }

  if (error instanceof Error) {
    const message = error.message.trim();
    if (message && !/^Request failed with status code \d+$/i.test(message)) {
      return message;
    }
  }

  return fallback;
}
