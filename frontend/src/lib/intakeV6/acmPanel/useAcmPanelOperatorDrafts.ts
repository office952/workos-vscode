/**
 * Local draft + debounce + flush for AcmPanel numeric fields.
 * Unmount cancels debounce only — never starts async persist from cleanup.
 */

import { useCallback, useEffect, useRef, useState } from "react";
import {
  ACM_PANEL_FIELD_COMMIT_DEBOUNCE_MS,
  canonicalNumberToDraftText,
  emptyFlushResult,
  parseAcmPanelNumericDraft,
  valuesEqualForCommit,
  type AcmPanelDraftNumericField,
  type AcmPanelFieldUpdate,
  type AcmPanelFlushResult,
} from "./commitSemantics";
import type { AcmOperatorFieldKey } from "./operatorPatch";

export type AcmPanelDraftFieldStatus =
  | "clean"
  | "editing"
  | "pending_commit"
  | "invalid";

export type AcmPanelDraftFieldState = {
  text: string;
  status: AcmPanelDraftFieldStatus;
  error: string | null;
  epoch: number;
};

export type AcmPanelCanonicalNumbers = Partial<
  Record<AcmPanelDraftNumericField, number | null | undefined>
>;

export type UseAcmPanelOperatorDraftsArgs = {
  canonical: AcmPanelCanonicalNumbers;
  onCommitUpdates: (updates: AcmPanelFieldUpdate[]) => void;
  debounceMs?: number;
};

function draftErrorMessage(field: AcmOperatorFieldKey): string {
  if (field === "fold_count") return "Fold count trebuie să fie 1 sau 2.";
  return "Valoare numerică invalidă.";
}

export function useAcmPanelOperatorDrafts(args: UseAcmPanelOperatorDraftsArgs) {
  const debounceMs = args.debounceMs ?? ACM_PANEL_FIELD_COMMIT_DEBOUNCE_MS;
  const onCommitUpdatesRef = useRef(args.onCommitUpdates);
  onCommitUpdatesRef.current = args.onCommitUpdates;
  const canonicalRef = useRef(args.canonical);
  canonicalRef.current = args.canonical;

  const [fields, setFields] = useState<
    Partial<Record<AcmPanelDraftNumericField, AcmPanelDraftFieldState>>
  >({});
  const timersRef = useRef<Partial<Record<AcmPanelDraftNumericField, number>>>({});
  const epochsRef = useRef<Partial<Record<AcmPanelDraftNumericField, number>>>({});
  const fieldsRef = useRef(fields);
  fieldsRef.current = fields;

  const cancelDebounce = useCallback((field?: AcmPanelDraftNumericField) => {
    if (field) {
      const t = timersRef.current[field];
      if (t !== undefined) {
        window.clearTimeout(t);
        delete timersRef.current[field];
      }
      return;
    }
    for (const key of Object.keys(timersRef.current) as AcmPanelDraftNumericField[]) {
      const t = timersRef.current[key];
      if (t !== undefined) window.clearTimeout(t);
    }
    timersRef.current = {};
  }, []);

  const bumpEpoch = useCallback((field: AcmPanelDraftNumericField) => {
    const next = (epochsRef.current[field] ?? 0) + 1;
    epochsRef.current[field] = next;
    return next;
  }, []);

  const readDraftText = useCallback(
    (field: AcmPanelDraftNumericField): string => {
      const local = fieldsRef.current[field];
      if (local && local.status !== "clean") return local.text;
      return canonicalNumberToDraftText(canonicalRef.current[field]);
    },
    [],
  );

  const collectSnapshot = useCallback(
    (opts?: { treatIncompleteAsInvalid?: boolean }): {
      updates: AcmPanelFieldUpdate[];
      invalidFields: AcmOperatorFieldKey[];
    } => {
      const treatIncompleteAsInvalid = opts?.treatIncompleteAsInvalid ?? true;
      const updates: AcmPanelFieldUpdate[] = [];
      const invalidFields: AcmOperatorFieldKey[] = [];
      const keys = Object.keys(fieldsRef.current) as AcmPanelDraftNumericField[];
      for (const field of keys) {
        const state = fieldsRef.current[field];
        if (!state || state.status === "clean") continue;
        const parsed = parseAcmPanelNumericDraft(field, state.text);
        if (!parsed.ok) {
          if (
            treatIncompleteAsInvalid ||
            parsed.reason === "invalid" ||
            state.status === "invalid"
          ) {
            invalidFields.push(field);
          }
          continue;
        }
        const canonical = canonicalRef.current[field];
        if (valuesEqualForCommit(field, parsed.value, canonical)) continue;
        updates.push({ field, value: parsed.value });
      }
      return { updates, invalidFields };
    },
    [],
  );

  const markClean = useCallback((fieldKeys: AcmPanelDraftNumericField[]) => {
    setFields((prev) => {
      const next = { ...prev };
      for (const field of fieldKeys) {
        const canonical = canonicalRef.current[field];
        next[field] = {
          text: canonicalNumberToDraftText(canonical),
          status: "clean",
          error: null,
          epoch: epochsRef.current[field] ?? 0,
        };
      }
      return next;
    });
  }, []);

  const commitUpdatesInternal = useCallback(
    (updates: AcmPanelFieldUpdate[]): AcmPanelFlushResult => {
      if (!updates.length) return emptyFlushResult("nothing_to_commit");
      onCommitUpdatesRef.current(updates);
      markClean(updates.map((u) => u.field as AcmPanelDraftNumericField));
      return { status: "committed", updates, invalidFields: [] };
    },
    [markClean],
  );

  const markInvalidFields = useCallback(
    (invalidFields: AcmOperatorFieldKey[]) => {
      setFields((prev) => {
        const next = { ...prev };
        for (const field of invalidFields) {
          const f = field as AcmPanelDraftNumericField;
          const cur = next[f];
          next[f] = {
            text: cur?.text ?? readDraftText(f),
            status: "invalid",
            error: draftErrorMessage(f),
            epoch: bumpEpoch(f),
          };
        }
        return next;
      });
    },
    [bumpEpoch, readDraftText],
  );

  /**
   * Snapshot pending updates without writing. Used by confirm (combined patch).
   * status committed here means "ready with updates" — caller must apply patch + markClean.
   */
  const takePendingUpdates = useCallback((): AcmPanelFlushResult => {
    cancelDebounce();
    const snap = collectSnapshot({ treatIncompleteAsInvalid: true });
    if (snap.invalidFields.length) {
      markInvalidFields(snap.invalidFields);
      return {
        status: "blocked_invalid",
        updates: [],
        invalidFields: snap.invalidFields,
      };
    }
    if (!snap.updates.length) return emptyFlushResult("nothing_to_commit");
    return { status: "committed", updates: snap.updates, invalidFields: [] };
  }, [cancelDebounce, collectSnapshot, markInvalidFields]);

  /** Persist pending valid updates (navigation / section). One PUT via onCommitUpdates. */
  const flushAll = useCallback((): AcmPanelFlushResult => {
    cancelDebounce();
    const snap = collectSnapshot({ treatIncompleteAsInvalid: true });
    if (snap.invalidFields.length) {
      markInvalidFields(snap.invalidFields);
      return {
        status: "blocked_invalid",
        updates: [],
        invalidFields: snap.invalidFields,
      };
    }
    if (!snap.updates.length) return emptyFlushResult("nothing_to_commit");
    return commitUpdatesInternal(snap.updates);
  }, [cancelDebounce, collectSnapshot, commitUpdatesInternal, markInvalidFields]);

  const commitField = useCallback(
    (field: AcmPanelDraftNumericField): AcmPanelFlushResult => {
      cancelDebounce(field);
      const text = readDraftText(field);
      const local = fieldsRef.current[field];
      const parsed = parseAcmPanelNumericDraft(field, text);

      if (!parsed.ok) {
        if (parsed.reason === "empty" || parsed.reason === "incomplete") {
          // Revert visual to canonical; no PUT
          bumpEpoch(field);
          setFields((prev) => ({
            ...prev,
            [field]: {
              text: canonicalNumberToDraftText(canonicalRef.current[field]),
              status: "clean",
              error: null,
              epoch: epochsRef.current[field] ?? 0,
            },
          }));
          return emptyFlushResult("nothing_to_commit");
        }
        const epoch = bumpEpoch(field);
        setFields((prev) => ({
          ...prev,
          [field]: {
            text,
            status: "invalid",
            error: draftErrorMessage(field),
            epoch,
          },
        }));
        return {
          status: "blocked_invalid",
          updates: [],
          invalidFields: [field],
        };
      }

      if (valuesEqualForCommit(field, parsed.value, canonicalRef.current[field])) {
        bumpEpoch(field);
        setFields((prev) => ({
          ...prev,
          [field]: {
            text: canonicalNumberToDraftText(parsed.value),
            status: "clean",
            error: null,
            epoch: epochsRef.current[field] ?? 0,
          },
        }));
        return emptyFlushResult("nothing_to_commit");
      }

      void local;
      return commitUpdatesInternal([{ field, value: parsed.value }]);
    },
    [bumpEpoch, cancelDebounce, commitUpdatesInternal, readDraftText],
  );

  const scheduleDebounce = useCallback(
    (field: AcmPanelDraftNumericField, epoch: number) => {
      cancelDebounce(field);
      timersRef.current[field] = window.setTimeout(() => {
        if (epochsRef.current[field] !== epoch) return;
        commitField(field);
      }, debounceMs);
    },
    [cancelDebounce, commitField, debounceMs],
  );

  const onDraftChange = useCallback(
    (field: AcmPanelDraftNumericField, text: string) => {
      const epoch = bumpEpoch(field);
      const parsed = parseAcmPanelNumericDraft(field, text);
      let status: AcmPanelDraftFieldStatus = "editing";
      let error: string | null = null;
      if (parsed.ok) {
        status = "pending_commit";
      } else if (parsed.reason === "invalid") {
        status = "invalid";
        error = draftErrorMessage(field);
      } else {
        status = "editing";
      }
      setFields((prev) => ({
        ...prev,
        [field]: { text, status, error, epoch },
      }));
      if (parsed.ok) {
        scheduleDebounce(field, epoch);
      } else {
        cancelDebounce(field);
      }
    },
    [bumpEpoch, cancelDebounce, scheduleDebounce],
  );

  const getFieldProps = useCallback(
    (field: AcmPanelDraftNumericField) => {
      const local = fields[field];
      const text =
        local && local.status !== "clean"
          ? local.text
          : canonicalNumberToDraftText(args.canonical[field]);
      return {
        value: text,
        status: local?.status ?? ("clean" as AcmPanelDraftFieldStatus),
        error: local?.error ?? null,
        onChange: (next: string) => onDraftChange(field, next),
        onBlur: () => commitField(field),
        onEnter: () => commitField(field),
      };
    },
    [args.canonical, commitField, fields, onDraftChange],
  );

  const hasPending = useCallback(() => {
    return Object.values(fieldsRef.current).some(
      (f) => f && (f.status === "editing" || f.status === "pending_commit"),
    );
  }, []);

  const hasInvalid = useCallback(() => {
    return Object.values(fieldsRef.current).some((f) => f && f.status === "invalid");
  }, []);

  const getFirstInvalidField = useCallback((): AcmPanelDraftNumericField | null => {
    for (const [field, state] of Object.entries(fieldsRef.current) as Array<
      [AcmPanelDraftNumericField, AcmPanelDraftFieldState]
    >) {
      if (state?.status === "invalid") return field;
    }
    const snap = collectSnapshot({ treatIncompleteAsInvalid: true });
    return (snap.invalidFields[0] as AcmPanelDraftNumericField) ?? null;
  }, [collectSnapshot]);

  // Sync clean fields from canonical when props change (do not wipe active edits).
  useEffect(() => {
    setFields((prev) => {
      let changed = false;
      const next = { ...prev };
      for (const field of Object.keys(args.canonical) as AcmPanelDraftNumericField[]) {
        const cur = next[field];
        if (cur && cur.status !== "clean") continue;
        const text = canonicalNumberToDraftText(args.canonical[field]);
        if (!cur || cur.text !== text) {
          next[field] = {
            text,
            status: "clean",
            error: null,
            epoch: epochsRef.current[field] ?? 0,
          };
          changed = true;
        }
      }
      return changed ? next : prev;
    });
  }, [args.canonical]);

  // Unmount: cancel debounce only — never persist from cleanup.
  useEffect(() => {
    return () => {
      cancelDebounce();
    };
  }, [cancelDebounce]);

  // beforeunload warn only — no alternate write path.
  useEffect(() => {
    const onBeforeUnload = (event: BeforeUnloadEvent) => {
      if (hasPending() || hasInvalid()) {
        event.preventDefault();
        event.returnValue = "";
      }
    };
    window.addEventListener("beforeunload", onBeforeUnload);
    return () => window.removeEventListener("beforeunload", onBeforeUnload);
  }, [hasInvalid, hasPending]);

  return {
    getFieldProps,
    flushAll,
    takePendingUpdates,
    commitField,
    cancelDebounce,
    markClean,
    hasPending,
    hasInvalid,
    getFirstInvalidField,
    fields,
  };
}

export type AcmPanelOperatorDraftsApi = ReturnType<typeof useAcmPanelOperatorDrafts>;
