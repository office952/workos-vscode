/**
 * Plăți angajați — master-detail: listă tranșă + panou detalii/înregistrare (live backend).
 * Nu configurează salarii, pontaj sau avansuri/datorii.
 */
import { useCallback, useEffect, useMemo, useRef, useState } from "react";
import { Link } from "react-router-dom";
import {
  Banknote,
  AlertTriangle,
  Info,
  Loader2,
  ChevronLeft,
  ChevronRight,
  Calendar,
  CheckCircle2,
  Clock,
  Search,
} from "lucide-react";
import { Badge } from "@/components/ui/badge";
import { Alert, AlertDescription } from "@/components/ui/alert";
import { SourceBadge, StatusBadge } from "@/components/workos/design-system";
import { employeePaymentsApi } from "@/api/employeePayments";
import { mapPaymentSituationResponse } from "@/lib/employeePaymentLiveMapper";
import {
  formatMonthKey,
  parseMonthKey,
  shiftMonthKey,
  slotStatusLabel,
  type EmployeePaymentSituation,
  type MonthPaymentSummary,
  type PaymentSlotKey,
  type PaymentSlotSituation,
  type SlotPaymentStatus,
} from "@/lib/employeePaymentSituationDemo";

const MONTH_NAMES_RO = [
  "Ianuarie", "Februarie", "Martie", "Aprilie", "Mai", "Iunie",
  "Iulie", "August", "Septembrie", "Octombrie", "Noiembrie", "Decembrie",
];

type PaymentFilter = "all" | SlotPaymentStatus;
type SortKey = "name" | "remaining";

function monthLabel(key: string): string {
  const { year, month } = parseMonthKey(key);
  return `${MONTH_NAMES_RO[month - 1]} ${year}`;
}

function slotForRow(row: EmployeePaymentSituation, activeSlot: PaymentSlotKey): PaymentSlotSituation {
  return activeSlot === "15" ? row.slot15 : row.slot30;
}

function formatRon(amount: number): string {
  return `${amount.toLocaleString("ro-RO")} RON`;
}

function slotTabLabel(slot: PaymentSlotKey): string {
  return slot === "15" ? "Tranșa 15" : "Tranșa 30 / final lună";
}

function shortPontaj(summary: string): string {
  if (summary.startsWith("Incomplet")) return "Incomplet";
  if (summary.startsWith("OK")) return "OK";
  return "Lipsă";
}

function shortAdvances(summary: string): string {
  if (summary === "Sold 0 RON") return "Sold 0 RON";
  const match = summary.match(/Sold activ ([\d.,]+)/);
  return match ? `Sold ${match[1]} RON` : summary;
}

export default function EmployeePayments() {
  const now = new Date();
  const [monthKey, setMonthKey] = useState(
    formatMonthKey(now.getFullYear(), now.getMonth() + 1)
  );
  const [situations, setSituations] = useState<EmployeePaymentSituation[]>([]);
  const [summary, setSummary] = useState<MonthPaymentSummary>({
    calculated: 0,
    paid: 0,
    remaining: 0,
    partialOrUnpaidSlots: 0,
  });
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [saving, setSaving] = useState(false);
  const [activeSlot, setActiveSlot] = useState<PaymentSlotKey>("15");
  const [paymentFilter, setPaymentFilter] = useState<PaymentFilter>("all");
  const [searchQuery, setSearchQuery] = useState("");
  const [sortBy, setSortBy] = useState<SortKey>("remaining");
  const [selectedEmployeeId, setSelectedEmployeeId] = useState<string | null>(null);
  const [formAmount, setFormAmount] = useState("");
  const [formDate, setFormDate] = useState(now.toISOString().slice(0, 10));
  const [formNotes, setFormNotes] = useState("");
  const [formError, setFormError] = useState<string | null>(null);

  const loadSituation = useCallback(async () => {
    setLoading(true);
    setError(null);
    try {
      const { year, month } = parseMonthKey(monthKey);
      const data = await employeePaymentsApi.getSituation(year, month);
      const mapped = mapPaymentSituationResponse(data, monthKey);
      setSituations(mapped.situations);
      setSummary(mapped.summary);
    } catch (err) {
      setSituations([]);
      setSummary({ calculated: 0, paid: 0, remaining: 0, partialOrUnpaidSlots: 0 });
      setError(err instanceof Error ? err.message : "Nu s-a putut încărca situația plăților.");
    } finally {
      setLoading(false);
    }
  }, [monthKey]);

  useEffect(() => {
    void loadSituation();
  }, [loadSituation]);

  const filteredRows = useMemo(() => {
    let rows = [...situations];
    if (paymentFilter !== "all") {
      rows = rows.filter((row) => {
        if (row.missingBase) return paymentFilter === "neplatit";
        return slotForRow(row, activeSlot).status === paymentFilter;
      });
    }
    const q = searchQuery.trim().toLowerCase();
    if (q) {
      rows = rows.filter((r) => r.employeeName.toLowerCase().includes(q));
    }
    rows.sort((a, b) => {
      if (sortBy === "name") {
        return a.employeeName.localeCompare(b.employeeName, "ro");
      }
      const remA = slotForRow(a, activeSlot).remainingAmount;
      const remB = slotForRow(b, activeSlot).remainingAmount;
      return remB - remA;
    });
    return rows;
  }, [situations, paymentFilter, activeSlot, searchQuery, sortBy]);

  const effectiveSelectedId = useMemo(() => {
    if (filteredRows.length === 0) return null;
    if (
      selectedEmployeeId &&
      filteredRows.some((r) => r.employeeId === selectedEmployeeId)
    ) {
      return selectedEmployeeId;
    }
    return filteredRows[0].employeeId;
  }, [filteredRows, selectedEmployeeId]);

  const selectedRow = useMemo(
    () => filteredRows.find((r) => r.employeeId === effectiveSelectedId) ?? null,
    [filteredRows, effectiveSelectedId]
  );

  const selectedSlotData = selectedRow ? slotForRow(selectedRow, activeSlot) : null;

  const paymentFormResetKey = `${effectiveSelectedId ?? ""}:${activeSlot}:${selectedSlotData?.remainingAmount ?? 0}:${selectedSlotData?.paidAmount ?? 0}`;

  useEffect(() => {
    if (!selectedRow || !selectedSlotData) return;
    setFormAmount(
      String(
        selectedSlotData.remainingAmount > 0 ? selectedSlotData.remainingAmount : 0
      )
    );
    setFormError(null);
  }, [paymentFormResetKey, selectedRow, selectedSlotData]);

  const handleSaveRecording = async (amountPaid: number) => {
    if (!selectedRow || !selectedSlotData) return;
    const amount = amountPaid;
    if (!Number.isFinite(amount) || amount <= 0) {
      setFormError("Sumă invalidă.");
      return;
    }
    if (amount > selectedSlotData.remainingAmount && selectedSlotData.remainingAmount > 0) {
      setFormError("Sumă mai mare decât rămasul de plată.");
      return;
    }
    const { year, month } = parseMonthKey(monthKey);
    setSaving(true);
    setFormError(null);
    try {
      await employeePaymentsApi.createPayment({
        employee_id: Number(selectedRow.employeeId),
        year,
        month,
        slot: activeSlot,
        amount_paid: amount,
        payment_date: formDate,
        notes: formNotes.trim() || undefined,
      });
      setFormNotes("");
      await loadSituation();
    } catch (err) {
      setFormError(err instanceof Error ? err.message : "Nu s-a putut salva plata.");
    } finally {
      setSaving(false);
    }
  };

  if (loading) {
    return (
      <div className="flex items-center justify-center h-64 gap-2 text-slate-400 text-sm">
        <Loader2 className="w-5 h-5 animate-spin" />
        Se încarcă situația plăților...
      </div>
    );
  }

  if (error) {
    return (
      <Alert className="bg-red-900/20 border-red-700/50 text-red-100">
        <AlertTriangle className="h-4 w-4 text-red-400" />
        <AlertDescription className="text-[12px]">{error}</AlertDescription>
      </Alert>
    );
  }

  return (
    <div className="space-y-4 w-full max-w-[1400px]">
      <header>
        <div className="flex items-center gap-2 flex-wrap">
          <Banknote className="w-5 h-5 text-emerald-400" />
          <h1 className="text-[20px] font-bold text-slate-100">Plăți angajați</h1>
          <SourceBadge source={situations.length === 0 ? "empty" : "db"} />
          <Badge className="text-[9px] bg-slate-800 text-slate-400 border-slate-600">
            Manual
          </Badge>
          <Badge className="text-[9px] bg-slate-800 text-slate-400 border-slate-600">
            Fără stat de plată fiscal
          </Badge>
        </div>
        <p className="text-[13px] text-slate-400 mt-1 pl-7">
          Situație plăți — tranșe 15 și 30. Înregistrare sumă plătită, nu configurare salarii.
        </p>
      </header>

      <Alert className="bg-[#111827] border-[#1E293B] text-slate-300">
        <Info className="h-4 w-4 text-slate-400" />
        <AlertDescription className="text-[12px]">
          Sumele afișate sunt pentru evidență operațională. Pagina nu configurează salarii și nu
          reprezintă stat de plată fiscal.
        </AlertDescription>
      </Alert>

      <div className="flex items-center gap-3">
        <Calendar className="w-4 h-4 text-slate-500" />
        <button
          type="button"
          onClick={() => setMonthKey((k) => shiftMonthKey(k, -1))}
          className="p-1.5 rounded border border-[#2A3548] text-slate-400 hover:text-white"
          aria-label="Luna anterioară"
        >
          <ChevronLeft className="w-4 h-4" />
        </button>
        <span className="text-[14px] font-semibold text-slate-200 min-w-[140px] text-center">
          {monthLabel(monthKey)}
        </span>
        <button
          type="button"
          onClick={() => setMonthKey((k) => shiftMonthKey(k, 1))}
          className="p-1.5 rounded border border-[#2A3548] text-slate-400 hover:text-white"
          aria-label="Luna următoare"
        >
          <ChevronRight className="w-4 h-4" />
        </button>
      </div>

      <PaymentSummaryCards summary={summary} />

      <PaymentSlotTabs activeSlot={activeSlot} onChange={setActiveSlot} />

      <div
        className="grid grid-cols-1 lg:grid-cols-[minmax(0,3fr)_minmax(0,2fr)] gap-4 items-start"
        data-testid="employee-payments-master-detail"
      >
        <section aria-label="Lista angajați tranșă" className="space-y-2 min-w-0">
          <div className="flex flex-wrap items-center gap-2 mb-2">
            <PaymentFilterChips value={paymentFilter} onChange={setPaymentFilter} />
            <div className="flex items-center gap-2 ml-auto flex-wrap">
              <div className="relative">
                <Search className="w-3.5 h-3.5 text-slate-500 absolute left-2.5 top-1/2 -translate-y-1/2" />
                <input
                  type="search"
                  placeholder="Caută angajat"
                  value={searchQuery}
                  onChange={(e) => setSearchQuery(e.target.value)}
                  className="pl-8 pr-3 py-1.5 text-[12px] bg-[#0B1220] border border-[#2A3548] rounded text-slate-200 w-[140px]"
                />
              </div>
              <select
                value={sortBy}
                onChange={(e) => setSortBy(e.target.value as SortKey)}
                className="text-[12px] bg-[#0B1220] border border-[#2A3548] rounded px-2 py-1.5 text-slate-300"
                aria-label="Sortare"
              >
                <option value="remaining">Sortare: sumă rămasă</option>
                <option value="name">Sortare: nume</option>
              </select>
            </div>
          </div>

          {filteredRows.length === 0 ? (
            <p className="text-[13px] text-slate-500 py-8 text-center border border-[#1E293B] rounded-lg">
              Niciun angajat pentru filtrele selectate.
            </p>
          ) : (
            filteredRows.map((row) => {
              const slotData = slotForRow(row, activeSlot);
              return (
                <EmployeeListRow
                  key={row.employeeId}
                  row={row}
                  slotData={slotData}
                  selected={row.employeeId === effectiveSelectedId}
                  onSelect={() => setSelectedEmployeeId(row.employeeId)}
                />
              );
            })
          )}
        </section>

        <aside
          aria-label="Detalii angajat selectat"
          className="lg:sticky lg:top-4 min-w-0"
        >
          {selectedRow && selectedSlotData ? (
            <EmployeePaymentDetailPanel
              row={selectedRow}
              slotData={selectedSlotData}
              activeSlot={activeSlot}
              monthKey={monthKey}
              formAmount={formAmount}
              saving={saving}
              formDate={formDate}
              formNotes={formNotes}
              formError={formError}
              onAmountChange={setFormAmount}
              onDateChange={setFormDate}
              onNotesChange={setFormNotes}
              onSave={handleSaveRecording}
            />
          ) : (
            <div className="bg-[#111827] border border-[#1E293B] rounded-lg p-6 text-center text-slate-500 text-[13px]">
              Selectați un angajat din listă sau ajustați filtrele.
            </div>
          )}
        </aside>
      </div>
    </div>
  );
}

function PaymentSummaryCards({ summary }: { summary: MonthPaymentSummary }) {
  return (
    <div className="grid grid-cols-2 md:grid-cols-4 gap-3">
      <div className="bg-[#1A2236] border border-[#2A3548] rounded-lg p-3">
        <p className="text-[10px] text-slate-500 uppercase mb-1">Calculat luna aceasta</p>
        <p className="text-xl font-bold text-slate-100">
          {summary.calculated.toLocaleString("ro-RO")}{" "}
          <span className="text-xs text-slate-500">RON</span>
        </p>
      </div>
      <div className="bg-[#1A2236] border border-emerald-800/30 rounded-lg p-3">
        <p className="text-[10px] text-slate-500 uppercase mb-1">Plătit</p>
        <p className="text-xl font-bold text-emerald-400 flex items-center gap-1">
          <CheckCircle2 className="w-4 h-4" />
          {summary.paid.toLocaleString("ro-RO")} RON
        </p>
      </div>
      <div className="bg-[#1A2236] border border-[#2A3548] rounded-lg p-3">
        <p className="text-[10px] text-slate-500 uppercase mb-1">Rămas</p>
        <p className="text-xl font-bold text-slate-100">
          {summary.remaining.toLocaleString("ro-RO")} RON
        </p>
      </div>
      <div className="bg-[#1A2236] border border-amber-800/30 rounded-lg p-3">
        <p className="text-[10px] text-slate-500 uppercase mb-1">Situație</p>
        <p className="text-xl font-bold text-amber-400 flex items-center gap-1">
          <Clock className="w-4 h-4" />
          {summary.partialOrUnpaidSlots} tranșe neplătite / parțiale
        </p>
      </div>
    </div>
  );
}

function PaymentSlotTabs({
  activeSlot,
  onChange,
}: {
  activeSlot: PaymentSlotKey;
  onChange: (slot: PaymentSlotKey) => void;
}) {
  const tabs: { key: PaymentSlotKey; label: string }[] = [
    { key: "15", label: "Tranșa 15" },
    { key: "30", label: "Tranșa 30 / final lună" },
  ];
  return (
    <div className="flex gap-1 border-b border-[#1E293B]">
      {tabs.map((tab) => (
        <button
          key={tab.key}
          type="button"
          onClick={() => onChange(tab.key)}
          className={`px-4 py-2 text-[13px] font-medium border-b-2 -mb-px transition-colors ${
            activeSlot === tab.key
              ? "border-blue-500 text-blue-400"
              : "border-transparent text-slate-400 hover:text-slate-200"
          }`}
        >
          {tab.label}
        </button>
      ))}
    </div>
  );
}

function PaymentFilterChips({
  value,
  onChange,
}: {
  value: PaymentFilter;
  onChange: (v: PaymentFilter) => void;
}) {
  const chips: { key: PaymentFilter; label: string }[] = [
    { key: "all", label: "Toți" },
    { key: "neplatit", label: "Neplătiți" },
    { key: "partial", label: "Parțial" },
    { key: "platit", label: "Plătiți" },
  ];
  return (
    <div className="flex flex-wrap gap-1.5">
      {chips.map((chip) => (
        <button
          key={chip.key}
          type="button"
          onClick={() => onChange(chip.key)}
          className={`px-3 py-1 rounded-full text-[11px] border transition-colors ${
            value === chip.key
              ? "bg-blue-600/20 border-blue-500/50 text-blue-300"
              : "border-[#2A3548] text-slate-400 hover:text-slate-200"
          }`}
        >
          {chip.label}
        </button>
      ))}
    </div>
  );
}

function slotPaymentStatusKey(
  status: SlotPaymentStatus,
  missingBase?: boolean,
): string {
  if (missingBase) return "missing_base";
  switch (status) {
    case "platit":
      return "paid";
    case "partial":
      return "partial";
    default:
      return "unpaid";
  }
}

function PaymentStatusBadge({
  status,
  missingBase = false,
}: {
  status: SlotPaymentStatus;
  missingBase?: boolean;
}) {
  return (
    <StatusBadge
      domain="payment"
      status={slotPaymentStatusKey(status, missingBase)}
      label={slotStatusLabel(status)}
      className="text-[10px]"
    />
  );
}

function EmployeeListRow({
  row,
  slotData,
  selected,
  onSelect,
}: {
  row: EmployeePaymentSituation;
  slotData: PaymentSlotSituation;
  selected: boolean;
  onSelect: () => void;
}) {
  const attendanceIncomplete = row.attendanceSummary.startsWith("Incomplet");

  return (
    <button
      type="button"
      onClick={onSelect}
      className={`w-full text-left rounded-lg border p-3 transition-colors ${
        selected
          ? "border-blue-500/60 bg-blue-950/25 ring-1 ring-blue-500/30"
          : "border-[#1E293B] bg-[#111827] hover:border-[#2A3548] hover:bg-[#0f172a]"
      }`}
    >
      <div className="flex flex-wrap items-center justify-between gap-2 mb-1">
        <span className="text-[14px] font-semibold text-slate-100">{row.employeeName}</span>
        <PaymentStatusBadge status={row.missingBase ? "neplatit" : slotData.status} missingBase={row.missingBase} />
      </div>
      <div className="flex flex-wrap gap-x-4 gap-y-1 text-[11px] text-slate-500 mb-2">
        <span>
          Pontaj:{" "}
          <span className={attendanceIncomplete ? "text-amber-300" : "text-slate-400"}>
            {shortPontaj(row.attendanceSummary)}
          </span>
        </span>
        <span>
          Avansuri/Datorii:{" "}
          <span className="text-slate-400">{shortAdvances(row.advancesDebtsSummary)}</span>
        </span>
      </div>
      <div className="grid grid-cols-3 gap-2 text-[11px]">
        <div>
          <p className="text-slate-500 uppercase text-[9px]">Calculat</p>
          <p className="text-slate-200 font-medium">{formatRon(slotData.expectedAmount)}</p>
        </div>
        <div>
          <p className="text-slate-500 uppercase text-[9px]">Plătit</p>
          <p className="text-emerald-300 font-medium">{formatRon(slotData.paidAmount)}</p>
        </div>
        <div>
          <p className="text-slate-500 uppercase text-[9px]">Rămas</p>
          <p className="text-amber-200/90 font-medium">{formatRon(slotData.remainingAmount)}</p>
        </div>
      </div>
    </button>
  );
}

function EmployeePaymentDetailPanel({
  row,
  slotData,
  activeSlot,
  monthKey,
  formAmount,
  formDate,
  formNotes,
  formError,
  saving,
  onAmountChange,
  onDateChange,
  onNotesChange,
  onSave,
}: {
  row: EmployeePaymentSituation;
  slotData: PaymentSlotSituation;
  activeSlot: PaymentSlotKey;
  monthKey: string;
  formAmount: string;
  formDate: string;
  formNotes: string;
  formError: string | null;
  saving: boolean;
  onAmountChange: (v: string) => void;
  onDateChange: (v: string) => void;
  onNotesChange: (v: string) => void;
  onSave: (amountPaid: number) => void;
}) {
  const attendanceIncomplete = row.attendanceSummary.startsWith("Incomplet");
  const d = slotData.details;
  const isPaid = slotData.status === "platit";
  const canRecord =
    !row.missingBase && slotData.expectedAmount > 0 && slotData.remainingAmount > 0;

  const employeeHistory = slotData.history ?? [];
  const activeHistory = employeeHistory.filter((r) => r.status !== "cancelled");
  const cancelledHistory = employeeHistory.filter((r) => r.status === "cancelled");
  const amountInputRef = useRef<HTMLInputElement>(null);

  if (row.missingBase) {
    return (
      <div className="bg-[#111827] border border-amber-800/40 rounded-lg p-5 space-y-4">
        <h2 className="text-[16px] font-semibold text-slate-100">{row.employeeName}</h2>
        <p className="text-[12px] text-amber-300/90 flex items-center gap-1.5">
          <AlertTriangle className="w-4 h-4 shrink-0" />
          Lipsește suma lunară în profilul angajatului.
        </p>
        <Link
          to="/employees"
          className="inline-block text-[12px] px-3 py-1.5 rounded border border-[#2A3548] text-slate-300 hover:text-white"
        >
          Deschide profil angajat
        </Link>
      </div>
    );
  }

  return (
    <div className="bg-[#111827] border border-[#1E293B] rounded-lg p-5 space-y-5">
      <div className="flex flex-wrap items-start justify-between gap-2">
        <div>
          <h2 className="text-[16px] font-semibold text-slate-100">{row.employeeName}</h2>
          <p className="text-[12px] text-slate-500 mt-1">{slotTabLabel(activeSlot)}</p>
        </div>
        <PaymentStatusBadge status={slotData.status} />
      </div>

      <div className="grid grid-cols-3 gap-3 text-[12px]">
        <DetailItem label="Calculat" value={formatRon(slotData.expectedAmount)} />
        <DetailItem label="Plătit" value={formatRon(slotData.paidAmount)} emphasis="emerald" />
        <DetailItem label="Rămas" value={formatRon(slotData.remainingAmount)} emphasis="amber" />
      </div>

      <div>
        <p className="text-[10px] text-slate-500 uppercase mb-2">Breakdown</p>
        <div className="grid grid-cols-2 gap-2 text-[12px]">
          <DetailItem label="Bază calculată" value={formatRon(d.bazaCalculata)} />
          <DetailItem
            label="Ajustare pontaj"
            value={d.ajustarePontaj > 0 ? `−${formatRon(d.ajustarePontaj)}` : formatRon(0)}
          />
          <DetailItem label="Ore suplimentare" value={formatRon(d.oreSuplimentare)} />
          <DetailItem label="Avansuri / datorii" value={formatRon(d.avansuriDatorii)} />
          <DetailItem label="Plăți existente" value={formatRon(slotData.paidAmount)} />
          <DetailItem label="Rămas" value={formatRon(slotData.remainingAmount)} />
        </div>
      </div>

      <div className="space-y-1 text-[12px]">
        <p className="text-[10px] text-slate-500 uppercase">Pontaj</p>
        <p className="text-slate-300">{row.attendanceSummary}</p>
        {attendanceIncomplete && (
          <Badge className="text-[9px] bg-red-900/30 text-red-300 border-red-800/50">
            Pontaj incomplet
          </Badge>
        )}
      </div>

      <div className="space-y-1 text-[12px]">
        <p className="text-[10px] text-slate-500 uppercase">Avansuri / Datorii</p>
        <p className="text-slate-300">{row.advancesDebtsSummary}</p>
        {d.avansuriDatorii > 0 && (
          <p className="text-slate-400 text-[11px]">
            Reținere sugerată în calcul: {formatRon(d.avansuriDatorii)}
          </p>
        )}
        <p className="text-slate-500 text-[11px]">
          Nu se închide automat din această pagină.
        </p>
      </div>

      <div>
        <p className="text-[10px] text-slate-500 uppercase mb-2">
          Istoric plăți — {monthLabel(monthKey)} · {slotTabLabel(activeSlot)}
        </p>
        {activeHistory.length === 0 && cancelledHistory.length === 0 ? (
          <p className="text-[11px] text-slate-500">Nicio plată înregistrată pentru această tranșă.</p>
        ) : (
          <ul className="divide-y divide-[#1E293B] text-[11px]">
            {activeHistory.map((entry) => (
              <HistoryRow key={entry.id} entry={entry} />
            ))}
            {cancelledHistory.map((entry) => (
              <HistoryRow key={entry.id} entry={entry} cancelled />
            ))}
          </ul>
        )}
      </div>

      <section aria-label="Înregistrare plată" className="border-t border-[#1E293B] pt-4 space-y-3">
        <h3 className="text-[13px] font-semibold text-slate-200">Înregistrează plată</h3>

        {isPaid || slotData.remainingAmount <= 0 ? (
          <p className="text-[12px] text-emerald-300 flex items-center gap-1.5">
            <CheckCircle2 className="w-4 h-4" />
            Tranșa este plătită.
          </p>
        ) : (
          <>
            <ReadonlyField label="Sumă rămasă" value={formatRon(slotData.remainingAmount)} />
            <label className="block space-y-1 text-[12px]">
              <span className="text-slate-400">Sumă plătită acum</span>
              <input
                ref={amountInputRef}
                type="number"
                min={0}
                step="1"
                value={formAmount}
                onChange={(e) => onAmountChange(e.target.value)}
                className="w-full bg-[#0B1220] border border-[#2A3548] rounded px-3 py-2 text-slate-100"
              />
            </label>
            <label className="block space-y-1 text-[12px]">
              <span className="text-slate-400">Data plății</span>
              <input
                type="date"
                value={formDate}
                onChange={(e) => onDateChange(e.target.value)}
                className="w-full bg-[#0B1220] border border-[#2A3548] rounded px-3 py-2 text-slate-100"
              />
            </label>
            <label className="block space-y-1 text-[12px]">
              <span className="text-slate-400">Observații</span>
              <textarea
                value={formNotes}
                onChange={(e) => onNotesChange(e.target.value)}
                rows={2}
                className="w-full bg-[#0B1220] border border-[#2A3548] rounded px-3 py-2 text-slate-100 resize-none"
              />
            </label>
            {formError && <p className="text-red-400 text-[11px]">{formError}</p>}
            <button
              type="button"
              onClick={() =>
                onSave(Number(amountInputRef.current?.value ?? formAmount))
              }
              disabled={!canRecord || saving}
              className="w-full text-[12px] px-3 py-2 rounded bg-blue-600 text-white hover:bg-blue-500 disabled:opacity-40 disabled:cursor-not-allowed"
            >
              {saving ? "Se salvează..." : "Salvează plata"}
            </button>
          </>
        )}
      </section>
    </div>
  );
}

function DetailItem({
  label,
  value,
  emphasis,
}: {
  label: string;
  value: string;
  emphasis?: "emerald" | "amber";
}) {
  const valueCls =
    emphasis === "emerald"
      ? "text-emerald-300 font-semibold"
      : emphasis === "amber"
        ? "text-amber-200/90 font-semibold"
        : "text-slate-200";
  return (
    <div>
      <p className="text-slate-500 text-[10px] uppercase">{label}</p>
      <p className={valueCls}>{value}</p>
    </div>
  );
}

function HistoryRow({ entry, cancelled }: { entry: RecordedPaymentEntry; cancelled?: boolean }) {
  return (
    <li className="py-2 flex flex-wrap justify-between gap-2">
      <div>
        <span className="text-slate-400">{entry.paymentDate}</span>
        {entry.notes && <span className="text-slate-500 block">{entry.notes}</span>}
      </div>
      <div className="flex items-center gap-2">
        <span className={cancelled ? "text-slate-500 line-through" : "text-emerald-300"}>
          {entry.amountPaid.toLocaleString("ro-RO")} RON
        </span>
        <span className="text-slate-500">{cancelled ? "Anulată" : "Confirmată"}</span>
      </div>
    </li>
  );
}

function ReadonlyField({ label, value }: { label: string; value: string }) {
  return (
    <div className="text-[12px]">
      <p className="text-slate-500 text-[11px]">{label}</p>
      <p className="text-slate-200 font-medium">{value}</p>
    </div>
  );
}
