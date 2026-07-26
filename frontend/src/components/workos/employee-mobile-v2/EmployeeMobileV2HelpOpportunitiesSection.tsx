/**
 * Employee Mobile V2 — Ajutor opportunities (Phase 3).
 * Accept/decline follow backend can_accept_help; no claim mapping.
 */
import { useCallback, useEffect, useState } from "react";
import {
  CollaborationApiError,
  acceptMobileHelpRequest,
  declineMobileHelpRequest,
  fetchMobileHelpOpportunities,
} from "@/api/collaboration";
import {
  EmployeeMobileEmptyState,
  EmployeeMobileErrorState,
  EmployeeMobileLoadingState,
} from "@/components/workos/employee-mobile/EmployeeMobileStates";
import { emV2Controls, emV2SectionLabelClass } from "@/lib/employeeMobileV2DesignTokens";
import { cn } from "@/lib/utils";

export type HelpOpportunityRow = {
  task_id: string;
  order_id: number;
  title?: string;
  display_label?: string;
  order_code?: string;
  help_request_id?: number;
  can_accept_help?: boolean;
  pool?: string;
  targeted_employee_id?: number | null;
  [key: string]: unknown;
};

export default function EmployeeMobileV2HelpOpportunitiesSection({
  onAccepted,
}: {
  onAccepted?: () => Promise<void> | void;
}) {
  const [rows, setRows] = useState<HelpOpportunityRow[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [busyId, setBusyId] = useState<number | null>(null);
  const [actionError, setActionError] = useState<string | null>(null);

  const reload = useCallback(async () => {
    setLoading(true);
    setError(null);
    try {
      const data = await fetchMobileHelpOpportunities();
      setRows(Array.isArray(data) ? (data as HelpOpportunityRow[]) : []);
    } catch (e) {
      setError(e instanceof Error ? e.message : "Nu am putut încărca Ajutor.");
      setRows([]);
    } finally {
      setLoading(false);
    }
  }, []);

  useEffect(() => {
    void reload();
  }, [reload]);

  const runAction = async (
    helpRequestId: number,
    orderId: number,
    action: "accept" | "decline",
  ) => {
    setBusyId(helpRequestId);
    setActionError(null);
    try {
      if (action === "accept") {
        await acceptMobileHelpRequest(orderId, helpRequestId);
      } else {
        await declineMobileHelpRequest(orderId, helpRequestId);
      }
      await reload();
      await onAccepted?.();
    } catch (e) {
      if (e instanceof CollaborationApiError) {
        setActionError(`${e.code}: ${e.message}`);
      } else if (e instanceof Error) {
        setActionError(e.message);
      } else {
        setActionError("Acțiunea a eșuat.");
      }
    } finally {
      setBusyId(null);
    }
  };

  return (
    <section
      className="space-y-2"
      data-testid="employee-mobile-v2-help-opportunities"
    >
      <div className="flex items-center justify-between gap-2 px-1">
        <h2 className={cn(emV2SectionLabelClass(), "mb-0")}>Ajutor solicitat</h2>
        <button
          type="button"
          className="text-[11px] text-slate-500 underline"
          onClick={() => void reload()}
        >
          Reîncarcă
        </button>
      </div>

      {loading ? <EmployeeMobileLoadingState testId="employee-mobile-v2-help-loading" /> : null}
      {!loading && error ? (
        <EmployeeMobileErrorState message={error} testId="employee-mobile-v2-help-error" />
      ) : null}
      {!loading && !error && rows.length === 0 ? (
        <EmployeeMobileEmptyState
          message="Nicio cerere de ajutor deschisă pentru tine."
          testId="employee-mobile-v2-help-empty"
        />
      ) : null}

      {actionError ? (
        <p className="px-1 text-[12px] text-rose-600" role="alert">
          {actionError}
        </p>
      ) : null}

      <ul className="space-y-2">
        {rows.map((row) => {
          const helpId = Number(row.help_request_id || 0);
          const title =
            String(row.display_label || row.title || row.task_id || "Task").trim();
          const isTargeted = row.targeted_employee_id != null;
          const canAccept = row.can_accept_help === true;
          return (
            <li
              key={`${row.order_id}-${row.task_id}-${helpId}`}
              className="rounded-xl border border-slate-200 bg-white px-3 py-2.5 shadow-sm"
              data-testid={`employee-mobile-v2-help-row-${helpId}`}
            >
              <div className="flex items-start justify-between gap-2">
                <div>
                  <p className="text-[14px] font-semibold text-slate-900 leading-snug">
                    {title}
                  </p>
                  <p className="text-[11px] text-slate-500 mt-0.5">
                    {row.order_code || `Comandă #${row.order_id}`} ·{" "}
                    {isTargeted ? "Țintit" : "Broadcast"}
                  </p>
                </div>
                <span className="shrink-0 rounded-full border border-amber-200 bg-amber-50 px-2 py-0.5 text-[10px] font-semibold uppercase text-amber-800">
                  Ajutor
                </span>
              </div>
              <div className="mt-2 flex flex-wrap gap-2">
                {canAccept ? (
                  <button
                    type="button"
                    disabled={busyId === helpId || helpId <= 0}
                    className={cn(emV2Controls.primaryAction, "min-h-[40px]")}
                    data-testid={`employee-mobile-v2-help-accept-${helpId}`}
                    onClick={() => void runAction(helpId, row.order_id, "accept")}
                  >
                    Acceptă
                  </button>
                ) : null}
                {isTargeted && canAccept ? (
                  <button
                    type="button"
                    disabled={busyId === helpId || helpId <= 0}
                    className={cn(emV2Controls.secondaryAction, "min-h-[40px]")}
                    data-testid={`employee-mobile-v2-help-decline-${helpId}`}
                    onClick={() => void runAction(helpId, row.order_id, "decline")}
                  >
                    Refuză
                  </button>
                ) : null}
              </div>
            </li>
          );
        })}
      </ul>
    </section>
  );
}
