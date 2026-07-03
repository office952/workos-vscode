import { useCallback, useEffect, useMemo, useState } from "react";
import { Link, useLocation } from "react-router-dom";
import { CalendarRange, ClipboardList, Clock3, Send, UserCheck, XCircle } from "lucide-react";
import EmployeeRequestStatusFilters from "@/components/workos/employee-mobile/EmployeeRequestStatusFilters";
import {
  EmployeeMobileEmptyState,
  EmployeeMobileErrorState,
  EmployeeMobileLoadingState,
  EmployeeMobileStatusBadge,
  EmployeeMobileSuccessState,
} from "@/components/workos/employee-mobile/EmployeeMobileStates";
import {
  buildEmployeeRequestCreatePayload,
  CANCELLABLE_REQUEST_STATUSES,
  cancelEmployeeRequest,
  createEmployeeRequest,
  EMPTY_EMPLOYEE_REQUEST_FORM,
  EMPLOYEE_REQUEST_TYPES,
  type EmployeeRequestDTO,
  type EmployeeRequestFormState,
  type EmployeeRequestStatus,
  type EmployeeRequestType,
  listEmployeeRequests,
} from "@/api/employeeMobileRequests";
import {
  countRequestsByFilter,
  filterRequestsByStatus,
  getSelfRequestsEmptyMessage,
  groupRequestsByStatus,
  LIST_DISPLAY_LIMIT,
  STATUS_GROUP_LABELS,
  type EmployeeRequestStatusFilter,
} from "@/lib/employeeRequestListUi";
import {
  formatDateTime,
  formatDisplayDate,
  REQUEST_STATUS_LABELS,
  REQUEST_TYPE_LABELS,
  requestStatusBadgeVariant,
} from "@/lib/employeeMobileUiHelpers";
import { cn } from "@/lib/utils";
import { useAuth } from "@/contexts/AuthContext";
import { canAccessRequestReviewWorkspace } from "@/lib/employeeMobileAccess";

export function EmployeeMobileRequestsTabs() {
  const location = useLocation();
  const { user } = useAuth();
  const showReviewTab = canAccessRequestReviewWorkspace(user?.role);
  const onSelf = location.pathname.includes("/employee-app/requests");
  const onReview = location.pathname.includes("/employee-app/review");
  const tabClass = (active: boolean) =>
    cn(
      "flex-1 text-center px-3 py-2 text-[11px] font-medium rounded-lg border transition-colors",
      active
        ? "bg-blue-900/30 text-blue-200 border-blue-700/50"
        : "bg-[#0A1020] text-slate-400 border-[#243044] hover:border-slate-600",
    );

  if (!showReviewTab) {
    return null;
  }

  return (
    <nav
      className="flex gap-2"
      data-testid="employee-mobile-requests-tabs"
      aria-label="Cereri navigation"
    >
      <Link to="/employee-app/requests" className={cn(tabClass(onSelf), "inline-flex items-center justify-center gap-1.5")}>
        <ClipboardList className="w-3.5 h-3.5 shrink-0" aria-hidden />
        Cererile mele
      </Link>
      <Link to="/employee-app/review" className={cn(tabClass(onReview), "inline-flex items-center justify-center gap-1.5")}>
        <UserCheck className="w-3.5 h-3.5 shrink-0" aria-hidden />
        Review manager
      </Link>
    </nav>
  );
}

export default function EmployeeMobileRequestsPanel({
  filterStyle = "pills",
}: {
  filterStyle?: "pills" | "segmented";
} = {}) {
  const [requests, setRequests] = useState<EmployeeRequestDTO[]>([]);
  const [listLoading, setListLoading] = useState(true);
  const [listError, setListError] = useState<string | null>(null);
  const [statusFilter, setStatusFilter] = useState<EmployeeRequestStatusFilter>("all");
  const [form, setForm] = useState<EmployeeRequestFormState>(EMPTY_EMPLOYEE_REQUEST_FORM);
  const [formError, setFormError] = useState<string | null>(null);
  const [submitting, setSubmitting] = useState(false);
  const [successMessage, setSuccessMessage] = useState<string | null>(null);
  const [cancellingId, setCancellingId] = useState<number | null>(null);

  const loadRequests = useCallback(async () => {
    setListLoading(true);
    setListError(null);
    try {
      const rows = await listEmployeeRequests();
      setRequests(rows);
    } catch (err) {
      const message = err instanceof Error ? err.message : "Nu am putut încărca cererile.";
      setListError(message);
      setRequests([]);
    } finally {
      setListLoading(false);
    }
  }, []);

  useEffect(() => {
    void loadRequests();
  }, [loadRequests]);

  const statusCounts = useMemo(() => countRequestsByFilter(requests), [requests]);
  const pendingCount = statusCounts.submitted;
  const filteredRequests = useMemo(
    () => filterRequestsByStatus(requests, statusFilter),
    [requests, statusFilter],
  );
  const displayedRequests = useMemo(
    () => filteredRequests.slice(0, LIST_DISPLAY_LIMIT),
    [filteredRequests],
  );
  const groupedDisplayedRequests = useMemo(
    () => (statusFilter === "all" ? groupRequestsByStatus(displayedRequests) : []),
    [displayedRequests, statusFilter],
  );
  const showLimitNotice = filteredRequests.length > LIST_DISPLAY_LIMIT;
  const listEmptyMessage = getSelfRequestsEmptyMessage(statusFilter, requests.length);

  const updateForm = (patch: Partial<EmployeeRequestFormState>) => {
    setForm((prev) => ({ ...prev, ...patch }));
    setFormError(null);
    setSuccessMessage(null);
  };

  const handleSubmit = async (event: React.FormEvent) => {
    event.preventDefault();
    setFormError(null);
    setSuccessMessage(null);

    if (!form.title.trim()) {
      setFormError("Titlul este obligatoriu.");
      return;
    }

    if (form.request_type === "advance") {
      const amount = Number(form.amount);
      if (!Number.isFinite(amount) || amount <= 0) {
        setFormError("Pentru avans, suma trebuie să fie mai mare decât zero.");
        return;
      }
    }

    const payload = buildEmployeeRequestCreatePayload(form);
    setSubmitting(true);
    try {
      await createEmployeeRequest(payload);
      setForm(EMPTY_EMPLOYEE_REQUEST_FORM);
      setSuccessMessage("Cererea a fost trimisă. O vei găsi în listă cu status „În așteptare”.");
      await loadRequests();
    } catch (err) {
      setFormError(err instanceof Error ? err.message : "Trimiterea cererii a eșuat.");
    } finally {
      setSubmitting(false);
    }
  };

  const handleCancel = async (requestId: number) => {
    setCancellingId(requestId);
    setListError(null);
    try {
      await cancelEmployeeRequest(requestId);
      await loadRequests();
    } catch (err) {
      setListError(err instanceof Error ? err.message : "Anularea cererii a eșuat.");
    } finally {
      setCancellingId(null);
    }
  };

  const showAdvanceAmount = form.request_type === "advance";

  const renderRequestItem = (item: EmployeeRequestDTO) => {
    const dateRange =
      item.start_date || item.end_date
        ? [formatDisplayDate(item.start_date), formatDisplayDate(item.end_date)]
            .filter(Boolean)
            .join(" – ")
        : null;
    const canCancel = CANCELLABLE_REQUEST_STATUSES.includes(item.status);
    const isPending = item.status === "submitted" || item.status === "draft";
    const reviewedAt = formatDateTime(item.reviewed_at);

    return (
      <li
        key={item.id}
        className={cn(
          "rounded-xl border p-3.5 space-y-2 transition-colors",
          isPending
            ? "border-amber-700/45 bg-amber-950/10"
            : "border-[#243044] bg-[#0A1020]",
        )}
        data-testid={`employee-mobile-request-item-${item.id}`}
      >
        <div className="flex items-start justify-between gap-2">
          <div className="space-y-1 min-w-0">
            <p className="text-[12px] font-semibold text-slate-100 truncate">
              {item.title || REQUEST_TYPE_LABELS[item.request_type]}
            </p>
            <p className="text-[10px] text-slate-500">{REQUEST_TYPE_LABELS[item.request_type]}</p>
          </div>
          <EmployeeMobileStatusBadge
            label={REQUEST_STATUS_LABELS[item.status]}
            variant={requestStatusBadgeVariant(item.status)}
          />
        </div>
        {dateRange && (
          <div className="flex items-center gap-1.5 text-[11px] text-slate-400">
            <CalendarRange className="w-3.5 h-3.5 shrink-0" aria-hidden />
            <span>{dateRange}</span>
          </div>
        )}
        {item.request_type === "advance" && item.amount != null && (
          <p className="text-[11px] text-slate-400">
            Sumă: {item.amount} {item.currency ?? "RON"}
          </p>
        )}
        {formatDateTime(item.submitted_at ?? item.created_at) && (
          <div className="flex items-center gap-1.5 text-[10px] text-slate-500">
            <Clock3 className="w-3.5 h-3.5 shrink-0" aria-hidden />
            <span>Trimis: {formatDateTime(item.submitted_at ?? item.created_at)}</span>
          </div>
        )}
        {(item.status === "approved" || item.status === "rejected") && reviewedAt && (
          <p className="text-[10px] text-slate-500">
            {item.status === "approved" ? "Aprobat" : "Respins"}: {reviewedAt}
          </p>
        )}
        {item.review_note && (item.status === "approved" || item.status === "rejected") && (
          <p className="text-[11px] text-slate-400 line-clamp-2">Notă review: {item.review_note}</p>
        )}
        {canCancel && (
          <button
            type="button"
            className="inline-flex items-center gap-1 text-[11px] px-2.5 py-1.5 rounded-lg border border-amber-800/50 text-amber-300 hover:bg-amber-900/20 disabled:opacity-50 min-h-[32px]"
            data-testid={`employee-mobile-request-cancel-${item.id}`}
            disabled={cancellingId === item.id}
            onClick={() => void handleCancel(item.id)}
          >
            <XCircle className="w-3.5 h-3.5 shrink-0" aria-hidden />
            {cancellingId === item.id ? "Se anulează…" : "Anulează"}
          </button>
        )}
      </li>
    );
  };

  return (
    <div className="space-y-5" data-testid="employee-mobile-requests-panel">
      <EmployeeMobileRequestsTabs />
      <div className="space-y-2">
        <div className="flex items-center justify-between gap-2 flex-wrap">
          <div className="flex items-center gap-2">
            <ClipboardList className="w-4 h-4 text-emerald-400 shrink-0" aria-hidden />
            <h2 className="text-[15px] font-semibold text-slate-100">Cererile mele</h2>
          </div>
          <EmployeeMobileStatusBadge label="Self-only" variant="live" testId="employee-mobile-requests-self-badge" />
        </div>
        <p className="text-[12px] text-slate-400 leading-relaxed">
          Trimite cereri pentru tine. După trimitere, statusul devine „În așteptare” până la review.
          Cererile sunt legate automat de contul tău.
        </p>
        <p className="sr-only" data-testid="employee-mobile-requests-no-employee-id">
          Cererile sunt legate automat de contul tău.
        </p>
      </div>

      {pendingCount > 0 && (
        <div
          className="rounded-xl border border-amber-800/40 bg-amber-950/20 px-3 py-2 flex items-center gap-2"
          data-testid="employee-mobile-requests-pending-banner"
        >
          <Clock3 className="w-4 h-4 shrink-0 text-amber-400" aria-hidden />
          <p className="text-[11px] text-amber-200">
            {pendingCount === 1
              ? "1 cerere în așteptare de review"
              : `${pendingCount} cereri în așteptare de review`}
          </p>
        </div>
      )}

      <section className="rounded-xl border border-[#1E293B] bg-[#111827] p-4 space-y-3">
        {!listError && (
          <EmployeeRequestStatusFilters
            filter={statusFilter}
            onFilterChange={setStatusFilter}
            counts={statusCounts}
            onRefresh={() => void loadRequests()}
            refreshing={listLoading}
            testIdPrefix="employee-mobile-requests"
            highlightPendingFilter
            filterStyle={filterStyle}
          />
        )}

        {listLoading && (
          <EmployeeMobileLoadingState
            message="Se încarcă cererile…"
            testId="employee-mobile-requests-loading"
          />
        )}

        {!listLoading && listError && (
          <EmployeeMobileErrorState message={listError} testId="employee-mobile-requests-error" />
        )}

        {!listLoading && !listError && filteredRequests.length === 0 && (
          <EmployeeMobileEmptyState
            message={listEmptyMessage}
            testId="employee-mobile-requests-empty"
          />
        )}

        {!listLoading && !listError && displayedRequests.length > 0 && (
          <>
            {statusFilter === "all" ? (
              <div className="space-y-4" data-testid="employee-mobile-requests-list">
                {groupedDisplayedRequests.map((group) => (
                  <div key={group.status} data-testid={`employee-mobile-requests-group-${group.status}`}>
                    <p className="text-[10px] font-semibold uppercase tracking-wide text-slate-500 mb-2">
                      {STATUS_GROUP_LABELS[group.status]} ({group.items.length})
                    </p>
                    <ul className="space-y-3">{group.items.map((item) => renderRequestItem(item))}</ul>
                  </div>
                ))}
              </div>
            ) : (
              <ul className="space-y-3" data-testid="employee-mobile-requests-list">
                {displayedRequests.map((item) => renderRequestItem(item))}
              </ul>
            )}
            {showLimitNotice && (
              <p
                className="text-[10px] text-slate-500"
                data-testid="employee-mobile-requests-limit-notice"
              >
                Se afișează primele {LIST_DISPLAY_LIMIT} de cereri.
              </p>
            )}
          </>
        )}
      </section>

      <section className="rounded-xl border border-[#1E293B] bg-[#111827] p-4 space-y-3">
        <h3 className="text-[13px] font-medium text-slate-200">Cerere nouă</h3>

        {successMessage && (
          <EmployeeMobileSuccessState
            message={successMessage}
            testId="employee-mobile-requests-success"
          />
        )}

        {formError && (
          <EmployeeMobileErrorState
            message={formError}
            testId="employee-mobile-requests-form-error"
          />
        )}

        <form className="space-y-3" onSubmit={(e) => void handleSubmit(e)}>
          <label className="block space-y-1">
            <span className="text-[11px] text-slate-400">Tip cerere *</span>
            <select
              className="w-full rounded-lg border border-[#243044] bg-[#0A1020] px-3 py-2 text-[12px] text-slate-100"
              value={form.request_type}
              data-testid="employee-mobile-request-type"
              onChange={(e) =>
                updateForm({ request_type: e.target.value as EmployeeRequestType })
              }
            >
              {EMPLOYEE_REQUEST_TYPES.map((type) => (
                <option key={type} value={type}>
                  {REQUEST_TYPE_LABELS[type]}
                </option>
              ))}
            </select>
          </label>

          <label className="block space-y-1">
            <span className="text-[11px] text-slate-400">Titlu *</span>
            <input
              type="text"
              className="w-full rounded-lg border border-[#243044] bg-[#0A1020] px-3 py-2 text-[12px] text-slate-100"
              value={form.title}
              data-testid="employee-mobile-request-title"
              onChange={(e) => updateForm({ title: e.target.value })}
            />
          </label>

          <label className="block space-y-1">
            <span className="text-[11px] text-slate-400">Descriere</span>
            <textarea
              className="w-full rounded-lg border border-[#243044] bg-[#0A1020] px-3 py-2 text-[12px] text-slate-100 min-h-[72px]"
              value={form.description}
              data-testid="employee-mobile-request-description"
              onChange={(e) => updateForm({ description: e.target.value })}
            />
          </label>

          <div className="grid grid-cols-2 gap-3">
            <label className="block space-y-1">
              <span className="text-[11px] text-slate-400">De la</span>
              <input
                type="date"
                className="w-full rounded-lg border border-[#243044] bg-[#0A1020] px-3 py-2 text-[12px] text-slate-100"
                value={form.start_date}
                data-testid="employee-mobile-request-start-date"
                onChange={(e) => updateForm({ start_date: e.target.value })}
              />
            </label>
            <label className="block space-y-1">
              <span className="text-[11px] text-slate-400">Până la</span>
              <input
                type="date"
                className="w-full rounded-lg border border-[#243044] bg-[#0A1020] px-3 py-2 text-[12px] text-slate-100"
                value={form.end_date}
                data-testid="employee-mobile-request-end-date"
                onChange={(e) => updateForm({ end_date: e.target.value })}
              />
            </label>
          </div>

          {showAdvanceAmount && (
            <label className="block space-y-1">
              <span className="text-[11px] text-slate-400">Sumă avans</span>
              <input
                type="number"
                min="0"
                step="0.01"
                className="w-full rounded-lg border border-[#243044] bg-[#0A1020] px-3 py-2 text-[12px] text-slate-100"
                value={form.amount}
                data-testid="employee-mobile-request-amount"
                onChange={(e) => updateForm({ amount: e.target.value })}
              />
            </label>
          )}

          <label className="block space-y-1">
            <span className="text-[11px] text-slate-400">Motiv</span>
            <input
              type="text"
              className="w-full rounded-lg border border-[#243044] bg-[#0A1020] px-3 py-2 text-[12px] text-slate-100"
              value={form.reason}
              data-testid="employee-mobile-request-reason"
              onChange={(e) => updateForm({ reason: e.target.value })}
            />
          </label>

          <button
            type="submit"
            className="inline-flex w-full items-center justify-center gap-2 rounded-xl bg-blue-700 hover:bg-blue-600 active:bg-blue-800 text-[12px] font-medium text-white py-3 disabled:opacity-50 transition-colors"
            data-testid="employee-mobile-request-submit"
            disabled={submitting}
          >
            <Send className="w-4 h-4 shrink-0" aria-hidden />
            {submitting ? "Se trimite…" : "Trimite cererea"}
          </button>
        </form>
      </section>
    </div>
  );
}

export { REQUEST_TYPE_LABELS };
