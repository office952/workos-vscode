/**
 * User-facing API error messages for employee request flows (self + review).
 * Does not change backend contracts.
 */
export type EmployeeRequestErrorContext = "self" | "review" | "manager-team";

function extractErrorCode(detail: unknown): string {
  if (typeof detail === "string") return detail;
  if (detail && typeof detail === "object") {
    const record = detail as Record<string, unknown>;
    if (typeof record.error === "string") return record.error;
    if (typeof record.message === "string") return record.message;
  }
  return "";
}

export function normalizeEmployeeRequestError(
  status: number,
  errorCode: string,
  context: EmployeeRequestErrorContext,
): string {
  const code = errorCode.toLowerCase();

  if (status === 401) {
    if (context === "manager-team") {
      return "Trebuie să fii autentificat pentru a vedea zona de manager.";
    }
    return "Sesiunea a expirat sau nu ești autentificat.";
  }

  if (status === 403) {
    if (context === "manager-team") {
      if (code.includes("manager_team_reader_required")) {
        return "Nu ai acces la vizualizarea echipei sau contul tău nu este configurat ca manager.";
      }
      if (code.includes("team_scope_violation")) {
        return "Angajatul selectat nu face parte din raportarea directă.";
      }
      return "Nu ai acces la vizualizarea echipei sau contul tău nu este configurat ca manager.";
    }
    if (context === "review") {
      if (code.includes("self_review_forbidden")) {
        return "Nu poți aproba sau respinge propria cerere.";
      }
      if (code.includes("employee_request_reviewer_required")) {
        return "Ai nevoie de rol manager sau admin pentru review cereri.";
      }
      if (code.includes("team_scope_violation")) {
        return "Nu poți revizui cereri în afara raportării directe.";
      }
      return "Nu ai acces la această zonă.";
    }

    if (code.includes("employee_link_missing")) {
      return "Contul tău nu este legat încă de un profil de angajat. Cere configurarea profilului pentru Employee Mobile.";
    }
    if (code.includes("employee_self_role_required")) {
      return "Rolul tău nu permite accesul la aplicația personală.";
    }
    return "Nu ai acces la această zonă.";
  }

  if (status === 409) {
    return "Cererea a fost deja procesată sau nu mai poate fi modificată.";
  }

  if (status === 422) {
    return "Datele trimise nu sunt valide pentru această acțiune.";
  }

  return "A apărut o eroare. Încearcă din nou.";
}

export async function throwEmployeeRequestApiError(
  res: Response,
  context: EmployeeRequestErrorContext,
): Promise<never> {
  let errorCode = "";
  try {
    const body = await res.json();
    errorCode = extractErrorCode(body?.detail);
  } catch {
    // ignore parse errors
  }

  if (import.meta.env.DEV && errorCode) {
    console.warn(`[employee-request:${context}] HTTP ${res.status}: ${errorCode}`);
  }

  throw new Error(normalizeEmployeeRequestError(res.status, errorCode, context));
}
