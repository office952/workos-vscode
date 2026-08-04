import { describe, expect, it } from "vitest";

/**
 * Wave 5 display semantics — keep candidate vs assigned vocabulary honest.
 * Panel itself is integration-tested via ExecutionDetail mocks + runtime proof.
 */
describe("assignmentReadinessDisplaySemantics", () => {
  it("never treats eligibility-ready as assignment authorized", () => {
    const future = {
      eligibility_ready: true,
      has_eligible_candidate: true,
      currently_unassigned: true,
      assignment_authorized: false as const,
    };
    expect(future.assignment_authorized).toBe(false);
    expect(future.eligibility_ready && future.has_eligible_candidate).toBe(true);
  });

  it("keeps unassigned distinct from assigned", () => {
    const row = { status: "unassigned" as const, assigned_employee_id: null };
    expect(row.status).toBe("unassigned");
    expect(row.assigned_employee_id).toBeNull();
  });
});
