import { describe, expect, it } from "vitest";
import {
  OwnerDecisionResolutionError,
  RESOLUTION_NOTE_MIN_LENGTH,
  resolutionErrorHeadline,
} from "./executionOwnerDecisionRelease";

describe("executionOwnerDecisionRelease", () => {
  it("exposes backend note minimum length", () => {
    expect(RESOLUTION_NOTE_MIN_LENGTH).toBe(3);
  });

  it("maps permission denied to operator-friendly headline", () => {
    const err = new OwnerDecisionResolutionError(
      403,
      "owner_decision_resolve_forbidden",
      "Forbidden",
      null,
    );
    expect(resolutionErrorHeadline(err)).toMatch(/permisiune/i);
  });

  it("maps note required error", () => {
    const err = new OwnerDecisionResolutionError(
      422,
      "owner_decision_note_required",
      "Note required",
      null,
    );
    expect(resolutionErrorHeadline(err)).toMatch(/Nota de rezolvare/i);
  });
});
