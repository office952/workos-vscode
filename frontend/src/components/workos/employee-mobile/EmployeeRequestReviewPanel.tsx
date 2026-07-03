import { useCallback, useEffect, useMemo, useState, type ReactNode } from "react";
import {
  CalendarRange,
  CheckCircle2,
  Clock3,
  FileText,
  User,
  UserCheck,
  XCircle,
} from "lucide-react";
import {
  approveEmployeeRequest,
  getEmployeeRequestForReview,
  listEmployeeRequestsForReview,
  rejectEmployeeRequest,
  type EmployeeRequestReviewDTO,
} from "@/api/employeeRequestReview";
import EmployeeRequestStatusFilters from "@/components/workos/employee-mobile/EmployeeRequestStatusFilters";
import {
  EmployeeMobileEmptyState,
  EmployeeMobileErrorState,
  EmployeeMobileLoadingState,
  EmployeeMobileStatusBadge,
  EmployeeMobileSuccessState,
} from "@/components/workos/employee-mobile/EmployeeMobileStates";
import { cn } from "@/lib/utils";
import {
  countRequestsByFilter,
  filterRequestsByStatus,
  getReviewEmptyMessage,
  groupRequestsByStatus,
  LIST_DISPLAY_LIMIT,
  REVIEW_DEFAULT_STATUS_FILTER,
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

function DetailRow({
  icon: Icon,
  label,
  children,
}: {
  icon: typeof User;
  label: string;
  children: ReactNode;
}) {
  return (
    <div className="flex items-start gap-2.5">
      <Icon className="w-4 h-4 shrink-0 text-slate-500 mt-0.5" aria-hidden />
      <div className="min-w-0 flex-1">
        <p className="text-[10px] uppercase tracking-wide text-slate-500">{label}</p>
        <p className="text-[12px] text-slate-200 leading-relaxed">{children}</p>
      </div>
    </div>
  );
}

export default function EmployeeRequestReviewPanel() {
  const [requests, setRequests] = useState<EmployeeRequestReviewDTO[]>([]);
  const [listLoading, setListLoading] = useState(true);
  const [listError, setListError] = useState<string | null>(null);
  const [statusFilter, setStatusFilter] = useState<EmployeeRequestStatusFilter>(
    REVIEW_DEFAULT_STATUS_FILTER,
  );
  const [selectedId, setSelectedId] = useState<number | null>(null);
  const [detail, setDetail] = useState<EmployeeRequestReviewDTO | null>(null);
  const [detailLoading, setDetailLoading] = useState(false);
  const [reviewNote, setReviewNote] = useState("");
  const [actionError, setActionError] = useState<string | null>(null);
  const [successMessage, setSuccessMessage] = useState<string | null>(null);
  const [acting, setActing] = useState<"approve" | "reject" | null>(null);

  const loadList = useCallback(async () => {
    setListLoading(true);
    setListError(null);
    try {
      const rows = await listEmployeeRequestsForReview();
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
    void loadList();
  }, [loadList]);

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
    () =>
      statusFilter === "all" ? groupRequestsByStatus(displayedRequests) : [],
    [displayedRequests, statusFilter],
  );
  const showLimitNotice = filteredRequests.length > LIST_DISPLAY_LIMIT;
  const listEmptyMessage = getReviewEmptyMessage(statusFilter, requests.length);

  const loadDetail = useCallback(async (requestId: number) => {
    setDetailLoading(true);
    setActionError(null);
    try {
      const row = await getEmployeeRequestForReview(requestId);
      setDetail(row);
      setReviewNote(row.review_note ?? "");
    } catch (err) {
      setActionError(err instanceof Error ? err.message : "Nu am putut încărca detaliul.");
      setDetail(null);
    } finally {
      setDetailLoading(false);
    }
  }, []);

  const handleSelect = (requestId: number) => {
    setSelectedId(requestId);
    setSuccessMessage(null);
    void loadDetail(requestId);
  };

  const handleApprove = async () => {
    if (selectedId == null || detail?.status !== "submitted") return;
    setActing("approve");
    setActionError(null);
    setSuccessMessage(null);
    try {
      await approveEmployeeRequest(selectedId, reviewNote);
      setSuccessMessage("Cererea a fost aprobată.");
      setSelectedId(null);
      setDetail(null);
      setReviewNote("");
      await loadList();
    } catch (err) {
      setActionError(err instanceof Error ? err.message : "Aprobarea a eșuat.");
    } finally {
      setActing(null);
    }
  };

  const handleReject = async () => {
    if (selectedId == null || detail?.status !== "submitted") return;
    setActing("reject");
    setActionError(null);
    setSuccessMessage(null);
    try {
      await rejectEmployeeRequest(selectedId, reviewNote);
      setSuccessMessage("Cererea a fost respinsă.");
      setSelectedId(null);
      setDetail(null);
      setReviewNote("");
      await loadList();
    } catch (err) {
      setActionError(err instanceof Error ? err.message : "Respingerea a eșuat.");
    } finally {
      setActing(null);
    }
  };

  const canReview = detail?.status === "submitted";

  const renderReviewItem = (item: EmployeeRequestReviewDTO) => {
    const dateRange =
      item.start_date || item.end_date
        ? [formatDisplayDate(item.start_date), formatDisplayDate(item.end_date)]
            .filter(Boolean)
            .join(" – ")
        : null;
    const isSelected = selectedId === item.id;
    const isPending = item.status === "submitted";
    const summaryLine = [item.description, item.reason].filter(Boolean).join(" · ");

    return (
      <li key={item.id}>
        <button
          type="button"
          className={cn(
            "w-full text-left rounded-2xl border p-3.5 space-y-2 transition-all active:scale-[0.99]",
            isSelected
              ? "border-blue-600/50 bg-blue-950/25 ring-1 ring-blue-700/30"
              : isPending
                ? "border-amber-700/45 bg-amber-950/10 hover:border-amber-600/55"
                : "border-[#243044] bg-[#0A1020] hover:border-slate-600",
          )}
          data-testid={`employee-mobile-review-item-${item.id}`}
          onClick={() => handleSelect(item.id)}
        >
          <div className="flex items-start justify-between gap-2">
            <p className="text-[13px] font-semibold text-slate-100 leading-snug line-clamp-2">
              {item.title || REQUEST_TYPE_LABELS[item.request_type]}
            </p>
            <EmployeeMobileStatusBadge
              label={REQUEST_STATUS_LABELS[item.status]}
              variant={requestStatusBadgeVariant(item.status)}
            />
          </div>

          <div className="flex items-center gap-1.5 text-[11px] text-slate-200">
            <User className="w-3.5 h-3.5 shrink-0 text-slate-400" aria-hidden />
            <span className="font-medium truncate">{item.employee_name}</span>
          </div>

          <p className="text-[10px] text-slate-500">{REQUEST_TYPE_LABELS[item.request_type]}</p>

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

          {summaryLine && (
            <p className="text-[11px] text-slate-500 line-clamp-2">{summaryLine}</p>
          )}
        </button>
      </li>
    );
  };

  return (
    <div className="space-y-5" data-testid="employee-mobile-review-panel">
      <div className="space-y-3">
        <div className="flex items-start gap-3">
          <div
            className="flex h-10 w-10 shrink-0 items-center justify-center rounded-xl bg-amber-500/15 text-amber-400 ring-1 ring-amber-500/20"
            aria-hidden
          >
            <UserCheck className="w-5 h-5" />
          </div>
          <div className="min-w-0 flex-1 space-y-1">
            <div className="flex items-center justify-between gap-2 flex-wrap">
              <h2 className="text-[16px] font-semibold text-slate-100">Review cereri</h2>
              <EmployeeMobileStatusBadge
                label="Manager/Admin"
                variant="review"
                testId="employee-mobile-review-badge"
              />
            </div>
            <p className="text-[12px] text-slate-400 leading-relaxed">
              Aprobă sau respinge cererile angajaților. Propria cerere se gestionează în tab-ul
              Cererile mele.
            </p>
          </div>
        </div>

        {pendingCount > 0 && (
          <div
            className="rounded-xl border border-amber-800/40 bg-amber-950/20 px-3 py-2 flex items-center gap-2"
            data-testid="employee-mobile-review-pending-banner"
          >
            <Clock3 className="w-4 h-4 shrink-0 text-amber-400" aria-hidden />
            <p className="text-[11px] text-amber-200">
              {pendingCount === 1
                ? "1 cerere în așteptare de review"
                : `${pendingCount} cereri în așteptare de review`}
            </p>
          </div>
        )}

        <p
          className="text-[10px] text-slate-500 leading-relaxed"
          data-testid="employee-mobile-review-disclaimer"
        >
          Aprobarea schimbă doar statusul cererii. Nu modifică pontajul sau plățile.
        </p>
      </div>

      <section className="rounded-2xl border border-[#1E293B] bg-[#111827] p-4 space-y-3">
        <h3 className="text-[13px] font-semibold text-slate-200">Inbox review</h3>

        {!listError && (
          <EmployeeRequestStatusFilters
            filter={statusFilter}
            onFilterChange={setStatusFilter}
            counts={statusCounts}
            onRefresh={() => void loadList()}
            refreshing={listLoading}
            testIdPrefix="employee-mobile-review"
            highlightPendingFilter
          />
        )}

        {listLoading && (
          <EmployeeMobileLoadingState
            message="Se încarcă cererile…"
            testId="employee-mobile-review-loading"
          />
        )}

        {!listLoading && listError && (
          <EmployeeMobileErrorState message={listError} testId="employee-mobile-review-error" />
        )}

        {!listLoading && !listError && filteredRequests.length === 0 && (
          <EmployeeMobileEmptyState
            message={listEmptyMessage}
            testId="employee-mobile-review-empty"
          />
        )}

        {!listLoading && !listError && displayedRequests.length > 0 && (
          <>
            {statusFilter === "all" ? (
              <div className="space-y-4" data-testid="employee-mobile-review-list">
                {groupedDisplayedRequests.map((group) => (
                  <div key={group.status} data-testid={`employee-mobile-review-group-${group.status}`}>
                    <p className="text-[10px] font-semibold uppercase tracking-wide text-slate-500 mb-2">
                      {STATUS_GROUP_LABELS[group.status]} ({group.items.length})
                    </p>
                    <ul className="space-y-2.5">{group.items.map((item) => renderReviewItem(item))}</ul>
                  </div>
                ))}
              </div>
            ) : (
              <ul className="space-y-2.5" data-testid="employee-mobile-review-list">
                {displayedRequests.map((item) => renderReviewItem(item))}
              </ul>
            )}
            {showLimitNotice && (
              <p
                className="text-[10px] text-slate-500"
                data-testid="employee-mobile-review-limit-notice"
              >
                Se afișează primele {LIST_DISPLAY_LIMIT} de cereri.
              </p>
            )}
          </>
        )}
      </section>

      {successMessage && (
        <EmployeeMobileSuccessState
          message={successMessage}
          testId="employee-mobile-review-success"
        />
      )}

      {selectedId != null && (
        <section
          className="rounded-2xl border border-[#1E293B] bg-[#111827] p-4 space-y-4"
          data-testid="employee-mobile-review-detail"
        >
          <h3 className="text-[13px] font-semibold text-slate-200">Detaliu cerere</h3>

          {detailLoading && (
            <EmployeeMobileLoadingState
              message="Se încarcă detaliul…"
              testId="employee-mobile-review-detail-loading"
            />
          )}

          {!detailLoading && detail && (
            <div className="space-y-3">
              <div className="flex items-start justify-between gap-2">
                <p className="text-[14px] font-semibold text-slate-100 leading-snug">
                  {detail.title || REQUEST_TYPE_LABELS[detail.request_type]}
                </p>
                <EmployeeMobileStatusBadge
                  label={REQUEST_STATUS_LABELS[detail.status]}
                  variant={requestStatusBadgeVariant(detail.status)}
                />
              </div>

              <div className="space-y-3 rounded-xl border border-[#243044] bg-[#0A1020]/60 p-3">
                <DetailRow icon={User} label="Angajat">
                  {detail.employee_name}
                  {detail.employee_department ? ` · ${detail.employee_department}` : ""}
                </DetailRow>
                <DetailRow icon={FileText} label="Tip cerere">
                  {REQUEST_TYPE_LABELS[detail.request_type]}
                </DetailRow>
                {(detail.start_date || detail.end_date) && (
                  <DetailRow icon={CalendarRange} label="Perioadă">
                    {[formatDisplayDate(detail.start_date), formatDisplayDate(detail.end_date)]
                      .filter(Boolean)
                      .join(" – ") || "—"}
                  </DetailRow>
                )}
                {formatDateTime(detail.submitted_at ?? detail.created_at) && (
                  <DetailRow icon={Clock3} label="Trimis">
                    {formatDateTime(detail.submitted_at ?? detail.created_at)}
                  </DetailRow>
                )}
                {detail.description && (
                  <DetailRow icon={FileText} label="Descriere">
                    {detail.description}
                  </DetailRow>
                )}
                {detail.reason && (
                  <DetailRow icon={FileText} label="Motiv">
                    {detail.reason}
                  </DetailRow>
                )}
                {detail.request_type === "advance" && detail.amount != null && (
                  <DetailRow icon={FileText} label="Sumă">
                    {detail.amount} {detail.currency ?? "RON"}
                  </DetailRow>
                )}
              </div>

              {!canReview && (
                <p
                  className="rounded-lg border border-amber-800/40 bg-amber-950/20 px-3 py-2 text-amber-200/90 text-[11px]"
                  data-testid="employee-mobile-review-not-reviewable"
                >
                  Cererea nu mai poate fi revizuită.
                </p>
              )}

              {canReview && (
                <>
                  <label className="block space-y-1.5">
                    <span className="text-[11px] font-medium text-slate-400">Notă review (opțional)</span>
                    <textarea
                      className="w-full rounded-xl border border-[#243044] bg-[#0A1020] px-3 py-2.5 text-[12px] text-slate-100 min-h-[80px] focus:border-blue-700/50 focus:outline-none"
                      value={reviewNote}
                      placeholder="Ex.: aprobat conform programului echipei"
                      data-testid="employee-mobile-review-note"
                      disabled={acting != null}
                      onChange={(e) => setReviewNote(e.target.value)}
                    />
                  </label>
                  <div className="flex flex-col sm:flex-row gap-2 pt-1">
                    <button
                      type="button"
                      className="inline-flex flex-1 items-center justify-center gap-2 rounded-xl bg-emerald-700 hover:bg-emerald-600 active:bg-emerald-800 text-[13px] font-semibold text-white py-3 disabled:opacity-50 transition-colors"
                      data-testid="employee-mobile-review-approve"
                      disabled={acting != null}
                      onClick={() => void handleApprove()}
                    >
                      <CheckCircle2 className="w-4 h-4 shrink-0" aria-hidden />
                      {acting === "approve" ? "Se aprobă…" : "Aprobă"}
                    </button>
                    <button
                      type="button"
                      className="inline-flex flex-1 items-center justify-center gap-2 rounded-xl bg-red-800 hover:bg-red-700 active:bg-red-900 text-[13px] font-semibold text-white py-3 disabled:opacity-50 transition-colors"
                      data-testid="employee-mobile-review-reject"
                      disabled={acting != null}
                      onClick={() => void handleReject()}
                    >
                      <XCircle className="w-4 h-4 shrink-0" aria-hidden />
                      {acting === "reject" ? "Se respinge…" : "Respinge"}
                    </button>
                  </div>
                </>
              )}
            </div>
          )}

          {actionError && (
            <div
              className="rounded-xl border border-red-900/40 bg-red-950/25 px-3 py-2 flex items-start gap-2"
              data-testid="employee-mobile-review-action-error"
            >
              <XCircle className="w-4 h-4 shrink-0 text-red-400 mt-0.5" aria-hidden />
              <p className="text-[12px] text-red-200">{actionError}</p>
            </div>
          )}
        </section>
      )}
    </div>
  );
}

export { REQUEST_TYPE_LABELS };
