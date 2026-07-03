import { describe, expect, it } from "vitest";
import { formatApiErrorDetail, formatApiErrorResponse, formatApiErrorFromUnknown, canCreateIntakeRequest } from "./apiError";

describe("formatApiErrorDetail", () => {
  it("returns plain string detail", () => {
    expect(formatApiErrorDetail("simple error")).toBe("simple error");
  });

  it("returns message from object detail", () => {
    expect(formatApiErrorDetail({ message: "Readable message" })).toBe(
      "Readable message"
    );
  });

  it("returns error code when message is missing", () => {
    expect(formatApiErrorDetail({ error: "permission_denied" })).toBe(
      "permission_denied"
    );
  });

  it("prefers message over error", () => {
    expect(
      formatApiErrorDetail({
        error: "permission_denied",
        message: "Role does not have permission",
      })
    ).toBe("Role does not have permission");
  });

  it("handles nested detail.message", () => {
    expect(formatApiErrorDetail({ detail: { message: "Nested" } })).toBe(
      "Nested"
    );
  });

  it("formats array details without object object", () => {
    const result = formatApiErrorDetail([
      { message: "First" },
      { error: "second_error" },
    ]);
    expect(result).toBe("First; second_error");
    expect(result).not.toContain("[object Object]");
  });

  it("returns fallback for null/undefined", () => {
    expect(formatApiErrorDetail(null)).toBe("A apărut o eroare.");
    expect(formatApiErrorDetail(undefined)).toBe("A apărut o eroare.");
    expect(formatApiErrorDetail(null, "Custom fallback")).toBe("Custom fallback");
  });

  it("formats attendance-style FastAPI detail", () => {
    expect(
      formatApiErrorDetail({
        error: "attendance_operator_required",
        role: "employee_mobile",
        message:
          "Employee attendance access requires role 'admin' or 'operator'.",
      })
    ).toBe("Employee attendance access requires role 'admin' or 'operator'.");
  });
});

describe("formatApiErrorResponse", () => {
  it("extracts detail from JSON response body", async () => {
    const res = new Response(
      JSON.stringify({
        detail: {
          error: "permission_denied",
          message: "Role 'employee_mobile' does not have permission 'inventory.view'",
        },
      }),
      { status: 403 }
    );

    await expect(formatApiErrorResponse(res)).resolves.toBe(
      "Role 'employee_mobile' does not have permission 'inventory.view'"
    );
  });

  it("falls back to HTTP status when body has no detail", async () => {
    const res = new Response(JSON.stringify({ ok: false }), { status: 500 });
    await expect(formatApiErrorResponse(res)).resolves.toBe("HTTP 500");
  });
});

describe("formatApiErrorFromUnknown", () => {
  it("maps intake.create permission_denied for employee_mobile", () => {
    const message = formatApiErrorFromUnknown({
      message: "Request failed with status code 403",
      response: {
        status: 403,
        data: {
          detail: {
            error: "permission_denied",
            permission: "intake.create",
            role: "employee_mobile",
            message: "Role 'employee_mobile' does not have permission 'intake.create'",
          },
        },
      },
    });
    expect(message).toContain("Contul Employee Mobile nu poate crea cereri Work Intake");
    expect(message).toContain("3001");
  });

  it("ignores generic axios status message when detail exists", () => {
    const message = formatApiErrorFromUnknown({
      message: "Request failed with status code 403",
      response: {
        status: 403,
        data: {
          detail: {
            error: "permission_denied",
            permission: "intake.create",
            role: "admin",
            message: "unexpected backend block",
          },
        },
      },
    });
    expect(message).toBe("unexpected backend block");
  });
});

describe("canCreateIntakeRequest", () => {
  it("allows admin manager sales only", () => {
    expect(canCreateIntakeRequest("admin")).toBe(true);
    expect(canCreateIntakeRequest("manager")).toBe(true);
    expect(canCreateIntakeRequest("sales")).toBe(true);
    expect(canCreateIntakeRequest("employee_mobile")).toBe(false);
    expect(canCreateIntakeRequest("operator")).toBe(false);
  });
});
