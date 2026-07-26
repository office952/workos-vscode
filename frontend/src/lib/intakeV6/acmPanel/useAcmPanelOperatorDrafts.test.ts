import { act, renderHook } from "@testing-library/react";
import { afterEach, beforeEach, describe, expect, it, vi } from "vitest";
import { ACM_PANEL_FIELD_COMMIT_DEBOUNCE_MS } from "./commitSemantics";
import { useAcmPanelOperatorDrafts } from "./useAcmPanelOperatorDrafts";

describe("useAcmPanelOperatorDrafts", () => {
  beforeEach(() => {
    vi.useFakeTimers();
  });
  afterEach(() => {
    vi.useRealTimers();
  });

  function setup(canonical: { l1_mm?: number; l2_mm?: number } = { l1_mm: 60, l2_mm: 25 }) {
    const commits: Array<Array<{ field: string; value: number | 1 | 2 }>> = [];
    const hook = renderHook(() =>
      useAcmPanelOperatorDrafts({
        canonical,
        onCommitUpdates: (updates) => {
          commits.push(updates.map((u) => ({ field: u.field, value: u.value as number })));
        },
      }),
    );
    return { ...hook, commits };
  }

  it("typing 6 then 65 commits once with 65", () => {
    const { result, commits } = setup({ l1_mm: 60 });
    act(() => {
      result.current.getFieldProps("l1_mm").onChange("6");
    });
    act(() => {
      result.current.getFieldProps("l1_mm").onChange("65");
    });
    act(() => {
      vi.advanceTimersByTime(ACM_PANEL_FIELD_COMMIT_DEBOUNCE_MS + 10);
    });
    expect(commits).toHaveLength(1);
    expect(commits[0]).toEqual([{ field: "l1_mm", value: 65 }]);
  });

  it("paste 75 commits once after debounce", () => {
    const { result, commits } = setup();
    act(() => {
      result.current.getFieldProps("l1_mm").onChange("75");
    });
    act(() => {
      vi.advanceTimersByTime(ACM_PANEL_FIELD_COMMIT_DEBOUNCE_MS + 10);
    });
    expect(commits).toEqual([[{ field: "l1_mm", value: 75 }]]);
  });

  it("blur before debounce commits once", () => {
    const { result, commits } = setup();
    act(() => {
      result.current.getFieldProps("l1_mm").onChange("70");
    });
    act(() => {
      result.current.getFieldProps("l1_mm").onBlur();
    });
    act(() => {
      vi.advanceTimersByTime(ACM_PANEL_FIELD_COMMIT_DEBOUNCE_MS + 10);
    });
    expect(commits).toHaveLength(1);
    expect(commits[0]).toEqual([{ field: "l1_mm", value: 70 }]);
  });

  it("Enter before debounce commits once", () => {
    const { result, commits } = setup();
    act(() => {
      result.current.getFieldProps("l1_mm").onChange("71");
    });
    act(() => {
      result.current.getFieldProps("l1_mm").onEnter();
    });
    act(() => {
      vi.advanceTimersByTime(ACM_PANEL_FIELD_COMMIT_DEBOUNCE_MS + 10);
    });
    expect(commits).toHaveLength(1);
  });

  it("debounce then blur does not double-commit", () => {
    const { result, commits } = setup();
    act(() => {
      result.current.getFieldProps("l1_mm").onChange("72");
    });
    act(() => {
      vi.advanceTimersByTime(ACM_PANEL_FIELD_COMMIT_DEBOUNCE_MS + 10);
    });
    act(() => {
      result.current.getFieldProps("l1_mm").onBlur();
    });
    expect(commits).toHaveLength(1);
  });

  it("same value yields zero commits", () => {
    const { result, commits } = setup({ l1_mm: 60 });
    act(() => {
      result.current.getFieldProps("l1_mm").onChange("60");
    });
    act(() => {
      result.current.getFieldProps("l1_mm").onBlur();
    });
    expect(commits).toHaveLength(0);
  });

  it("invalid numeric yields zero commits and blocked flush", () => {
    const { result, commits } = setup();
    act(() => {
      result.current.getFieldProps("fold_count").onChange("9");
    });
    let flush;
    act(() => {
      flush = result.current.flushAll();
    });
    expect(flush!.status).toBe("blocked_invalid");
    expect(commits).toHaveLength(0);
  });

  it("empty temporary on blur yields zero commits", () => {
    const { result, commits } = setup();
    act(() => {
      result.current.getFieldProps("l1_mm").onChange("");
    });
    act(() => {
      result.current.getFieldProps("l1_mm").onBlur();
    });
    expect(commits).toHaveLength(0);
  });

  it("two fields rapid — flushAll commits both in one call", () => {
    const { result, commits } = setup();
    act(() => {
      result.current.getFieldProps("l1_mm").onChange("61");
      result.current.getFieldProps("l2_mm").onChange("26");
    });
    let flush;
    act(() => {
      flush = result.current.flushAll();
    });
    expect(flush!.status).toBe("committed");
    expect(commits).toHaveLength(1);
    expect(commits[0]).toEqual(
      expect.arrayContaining([
        { field: "l1_mm", value: 61 },
        { field: "l2_mm", value: 26 },
      ]),
    );
  });

  it("takePendingUpdates does not commit; caller owns apply", () => {
    const { result, commits } = setup();
    act(() => {
      result.current.getFieldProps("l1_mm").onChange("66");
    });
    const snap = result.current.takePendingUpdates();
    expect(snap.status).toBe("committed");
    expect(snap.updates).toEqual([{ field: "l1_mm", value: 66 }]);
    expect(commits).toHaveLength(0);
  });

  it("cleanup cancels debounce and does not commit", () => {
    const { result, commits, unmount } = setup();
    act(() => {
      result.current.getFieldProps("l1_mm").onChange("80");
    });
    unmount();
    act(() => {
      vi.advanceTimersByTime(ACM_PANEL_FIELD_COMMIT_DEBOUNCE_MS + 50);
    });
    expect(commits).toHaveLength(0);
  });

  it("stale debounce after blur is cancelled", () => {
    const { result, commits } = setup();
    act(() => {
      result.current.getFieldProps("l1_mm").onChange("81");
    });
    act(() => {
      result.current.getFieldProps("l1_mm").onBlur();
    });
    act(() => {
      vi.advanceTimersByTime(ACM_PANEL_FIELD_COMMIT_DEBOUNCE_MS + 10);
    });
    expect(commits).toHaveLength(1);
  });
});
