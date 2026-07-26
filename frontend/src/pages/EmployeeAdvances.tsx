/**
 * Avansuri / Împrumuturi / Datorii — Evidență internă (ledger)
 *
 * EVIDENȚĂ INTERNĂ — NU este document fiscal/contabil.
 */
import { useMemo, useState, type ReactNode } from "react";
import {
  Wallet,
  AlertTriangle,
  Search,
  Info,
  Plus,
  Loader2,
  HandCoins,
  CreditCard,
  Ban,
  ArrowDownCircle,
  ArrowUpCircle,
  Wrench,
} from "lucide-react";
import { Badge } from "@/components/ui/badge";
import { Alert, AlertDescription } from "@/components/ui/alert";
import {
  Dialog,
  DialogContent,
  DialogFooter,
  DialogHeader,
  DialogTitle,
} from "@/components/ui/dialog";
import { useOperationalEmployees } from "@/hooks/useOperationalEmployees";
import { useEmployeeBalances } from "@/hooks/useEmployeeBalances";
import type { BalanceTransactionStatus, BalanceTransactionType } from "@/api/employeeBalances";

type FilterType = "all" | BalanceTransactionType;

const TYPE_OPTIONS: { value: BalanceTransactionType; label: string }[] = [
  { value: "advance", label: "Avans" },
  { value: "loan", label: "Împrumut" },
  { value: "retention", label: "Reținere" },
  { value: "repayment", label: "Achitare" },
  { value: "compensation", label: "Compensare" },
  { value: "adjustment", label: "Corecție" },
];

const TYPE_CONFIG: Record<
  BalanceTransactionType,
  { label: string; cls: string; icon: ReactNode }
> = {
  advance: {
    label: "Avans",
    cls: "bg-blue-900/40 text-blue-300 border-blue-700",
    icon: <HandCoins className="w-4 h-4" />,
  },
  loan: {
    label: "Împrumut",
    cls: "bg-purple-900/40 text-purple-300 border-purple-700",
    icon: <CreditCard className="w-4 h-4" />,
  },
  retention: {
    label: "Reținere",
    cls: "bg-red-900/40 text-red-300 border-red-700",
    icon: <Ban className="w-4 h-4" />,
  },
  repayment: {
    label: "Achitare",
    cls: "bg-emerald-900/40 text-emerald-300 border-emerald-700",
    icon: <ArrowDownCircle className="w-4 h-4" />,
  },
  compensation: {
    label: "Compensare",
    cls: "bg-cyan-900/40 text-cyan-300 border-cyan-700",
    icon: <ArrowUpCircle className="w-4 h-4" />,
  },
  adjustment: {
    label: "Corecție",
    cls: "bg-amber-900/40 text-amber-300 border-amber-700",
    icon: <Wrench className="w-4 h-4" />,
  },
};

const STATUS_CONFIG: Record<BalanceTransactionStatus, { label: string; cls: string }> = {
  active: { label: "Activ", cls: "bg-amber-900/40 text-amber-300 border-amber-700" },
  settled: { label: "Închis", cls: "bg-emerald-900/40 text-emerald-300 border-emerald-700" },
  cancelled: { label: "Anulat", cls: "bg-slate-700/60 text-slate-400 border-slate-600" },
};

function typeLabel(t: BalanceTransactionType): string {
  return TYPE_OPTIONS.find((o) => o.value === t)?.label ?? t;
}

export default function EmployeeAdvances() {
  const { employees, loading: employeesLoading, error: employeesError } = useOperationalEmployees();
  const {
    summary,
    transactions,
    loading: balancesLoading,
    transactionsLoading,
    error: balancesError,
    loadTransactions,
    createTransaction,
    cancelTransaction,
  } = useEmployeeBalances();

  const [filterType, setFilterType] = useState<FilterType>("all");
  const [filterEmployee, setFilterEmployee] = useState<string>("all");
  const [filterStatus, setFilterStatus] = useState<string>("all");
  const [searchQuery, setSearchQuery] = useState("");

  const [formOpen, setFormOpen] = useState(false);
  const [formSaving, setFormSaving] = useState(false);
  const [formError, setFormError] = useState<string | null>(null);
  const [formEmployeeId, setFormEmployeeId] = useState<number | "">("");
  const [formType, setFormType] = useState<BalanceTransactionType>("advance");
  const [formDate, setFormDate] = useState(new Date().toISOString().slice(0, 10));
  const [formAmount, setFormAmount] = useState("");
  const [formCurrency, setFormCurrency] = useState("RON");
  const [formNotes, setFormNotes] = useState("");

  const activeEmployees = useMemo(
    () => employees.filter((e) => e.status === "active"),
    [employees]
  );

  const loading = employeesLoading || balancesLoading;
  const error = employeesError ?? balancesError;

  const filteredTransactions = useMemo(() => {
    return transactions.filter((tx) => {
      if (filterType !== "all" && tx.transaction_type !== filterType) return false;
      if (filterEmployee !== "all" && tx.employee_id !== Number(filterEmployee)) return false;
      if (filterStatus !== "all" && tx.status !== filterStatus) return false;
      if (searchQuery.trim()) {
        const q = searchQuery.toLowerCase();
        return (
          (tx.employee_name ?? "").toLowerCase().includes(q) ||
          (tx.notes ?? "").toLowerCase().includes(q) ||
          typeLabel(tx.transaction_type).toLowerCase().includes(q)
        );
      }
      return true;
    });
  }, [transactions, filterType, filterEmployee, filterStatus, searchQuery]);

  const totals = summary?.totals;
  const currency = summary?.currency ?? "RON";

  const openForm = () => {
    setFormError(null);
    setFormEmployeeId(activeEmployees[0]?.id ?? "");
    setFormType("advance");
    setFormDate(new Date().toISOString().slice(0, 10));
    setFormAmount("");
    setFormCurrency(currency);
    setFormNotes("");
    setFormOpen(true);
  };

  const applyFilters = () => {
    void loadTransactions({
      employee_id: filterEmployee !== "all" ? Number(filterEmployee) : undefined,
      status: filterStatus !== "all" ? filterStatus : undefined,
      transaction_type: filterType !== "all" ? filterType : undefined,
    });
  };

  const handleSave = async () => {
    setFormError(null);
    if (!formEmployeeId) {
      setFormError("Selectează un angajat.");
      return;
    }
    const amount = Number(formAmount);
    if (!Number.isFinite(amount) || amount <= 0) {
      setFormError("Suma trebuie să fie mai mare decât 0.");
      return;
    }
    setFormSaving(true);
    try {
      await createTransaction({
        employee_id: Number(formEmployeeId),
        transaction_date: formDate,
        transaction_type: formType,
        amount,
        currency: formCurrency.trim() || "RON",
        notes: formNotes.trim() || undefined,
      });
      setFormOpen(false);
      applyFilters();
    } catch (err) {
      setFormError(err instanceof Error ? err.message : "Nu s-a putut salva tranzacția.");
    } finally {
      setFormSaving(false);
    }
  };

  const handleCancel = async (id: number) => {
    try {
      await cancelTransaction(id);
      applyFilters();
    } catch {
      /* surface via hook error on next load */
    }
  };

  if (loading) {
    return (
      <div className="flex items-center justify-center h-64 gap-2 text-slate-400 text-sm">
        <Loader2 className="w-5 h-5 animate-spin" />
        Se încarcă evidența internă...
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

  const hasAnyTransactions = (totals?.transaction_count ?? 0) > 0;

  return (
    <div className="space-y-4">
      <div className="flex items-center justify-between flex-wrap gap-2">
        <div className="flex flex-col gap-1">
          <div className="flex items-center gap-2 flex-wrap">
            <Wallet className="w-5 h-5 text-amber-400" />
            <h1 className="text-[18px] font-bold text-slate-100">Avansuri / Datorii</h1>
            <Badge className="text-[10px] uppercase tracking-wide bg-emerald-900/50 text-emerald-300 border-emerald-600/60">
              LIVE DB
            </Badge>
            <Badge className="text-[10px] uppercase tracking-wide bg-blue-900/40 text-blue-300 border-blue-700/60">
              MANUAL
            </Badge>
          </div>
          <p className="text-[13px] text-slate-300 pl-7">
            Evidență internă — avansuri, împrumuturi și rețineri pe angajat.
          </p>
        </div>
        <button
          type="button"
          onClick={openForm}
          className="flex items-center gap-2 px-3 py-2 text-[12px] font-semibold rounded-md bg-blue-600 hover:bg-blue-500 text-white"
        >
          <Plus className="w-4 h-4" />
          Adaugă tranzacție
        </button>
      </div>

      <Alert className="bg-amber-900/20 border-amber-700/50 text-amber-100">
        <Info className="h-4 w-4 text-amber-400" />
        <AlertDescription className="text-[12px] text-amber-100/90">
          Avansurile, împrumuturile și reținerile sunt evidență internă. Compensarea cu plăți se face
          doar prin confirmare operator. Nu este contabilitate oficială.
        </AlertDescription>
      </Alert>

      <div className="grid grid-cols-2 md:grid-cols-4 gap-3">
        <div className="bg-wo-surface-raised border border-amber-800/30 rounded-lg p-3">
          <p className="text-[10px] text-slate-500 uppercase tracking-wide mb-1">Sold total activ</p>
          <p className="text-[22px] font-bold text-amber-400">
            {(totals?.active_balance ?? 0).toLocaleString("ro-RO")}{" "}
            <span className="text-[12px] text-slate-500">{currency}</span>
          </p>
        </div>
        <div className="bg-wo-surface-raised border border-wo-border-strong rounded-lg p-3">
          <p className="text-[10px] text-slate-500 uppercase tracking-wide mb-1">Avansuri (ledger)</p>
          <p className="text-[22px] font-bold text-blue-400">
            {(totals?.advance_total ?? 0).toLocaleString("ro-RO")} {currency}
          </p>
        </div>
        <div className="bg-wo-surface-raised border border-wo-border-strong rounded-lg p-3">
          <p className="text-[10px] text-slate-500 uppercase tracking-wide mb-1">Împrumuturi (ledger)</p>
          <p className="text-[22px] font-bold text-purple-400">
            {(totals?.loan_total ?? 0).toLocaleString("ro-RO")} {currency}
          </p>
        </div>
        <div className="bg-wo-surface-raised border border-wo-border-strong rounded-lg p-3">
          <p className="text-[10px] text-slate-500 uppercase tracking-wide mb-1">Rețineri (ledger)</p>
          <p className="text-[22px] font-bold text-red-400">
            {(totals?.retention_total ?? 0).toLocaleString("ro-RO")} {currency}
          </p>
        </div>
      </div>

      {!hasAnyTransactions && (
        <Alert className="bg-wo-surface-raised border-wo-border-subtle text-slate-300">
          <AlertDescription className="text-[12px]">
            Nu există avansuri, datorii sau rețineri active. Adaugă prima tranzacție internă.
          </AlertDescription>
        </Alert>
      )}

      <div className="flex items-center gap-3 flex-wrap">
        <div className="flex items-center gap-1 bg-wo-surface-raised border border-wo-border-subtle rounded-md p-0.5">
          <button
            type="button"
            onClick={() => setFilterType("all")}
            className={`px-3 py-1.5 text-[11px] font-semibold rounded transition-colors ${
              filterType === "all"
                ? "bg-wo-surface-raised text-slate-100 border border-wo-border-strong"
                : "text-slate-500 hover:text-slate-300"
            }`}
          >
            Toate
          </button>
          {TYPE_OPTIONS.slice(0, 3).map((t) => (
            <button
              key={t.value}
              type="button"
              onClick={() => setFilterType(t.value)}
              className={`px-3 py-1.5 text-[11px] font-semibold rounded transition-colors ${
                filterType === t.value
                  ? "bg-wo-surface-raised text-slate-100 border border-wo-border-strong"
                  : "text-slate-500 hover:text-slate-300"
              }`}
            >
              {t.label}
            </button>
          ))}
        </div>

        <select
          value={filterEmployee}
          onChange={(e) => setFilterEmployee(e.target.value)}
          className="bg-wo-surface-raised border border-wo-border-subtle rounded-md px-2 py-2 text-[12px] text-slate-200"
        >
          <option value="all">Toți angajații</option>
          {activeEmployees.map((emp) => (
            <option key={emp.id} value={emp.id}>{emp.name}</option>
          ))}
        </select>

        <select
          value={filterStatus}
          onChange={(e) => setFilterStatus(e.target.value)}
          className="bg-wo-surface-raised border border-wo-border-subtle rounded-md px-2 py-2 text-[12px] text-slate-200"
        >
          <option value="all">Toate statusurile</option>
          <option value="active">Activ</option>
          <option value="settled">Închis</option>
          <option value="cancelled">Anulat</option>
        </select>

        <div className="flex items-center gap-2 bg-wo-surface-raised border border-wo-border-subtle rounded-lg px-3 py-2 flex-1 max-w-xs focus-within:border-blue-500/50">
          <Search className="w-4 h-4 text-slate-500" />
          <input
            type="text"
            value={searchQuery}
            onChange={(e) => setSearchQuery(e.target.value)}
            placeholder="Caută..."
            className="bg-transparent text-[12px] text-slate-200 placeholder:text-slate-600 outline-none w-full"
          />
        </div>
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-3 gap-4">
        <div className="lg:col-span-2 space-y-2">
          <h2 className="text-[13px] font-semibold text-slate-300 uppercase tracking-wide">
            Tranzacții
          </h2>
          {transactionsLoading ? (
            <div className="text-[12px] text-slate-500 flex items-center gap-2">
              <Loader2 className="w-4 h-4 animate-spin" /> Se încarcă...
            </div>
          ) : filteredTransactions.length === 0 ? (
            <div className="bg-wo-surface-raised border border-wo-border-subtle rounded-lg p-8 text-center">
              <Wallet className="w-8 h-8 text-slate-600 mx-auto mb-2" />
              <p className="text-[13px] text-slate-500">Nicio tranzacție pentru filtrul curent.</p>
            </div>
          ) : (
            filteredTransactions.map((tx) => {
              const typeCfg = TYPE_CONFIG[tx.transaction_type];
              const statusCfg = STATUS_CONFIG[tx.status];
              return (
                <div
                  key={tx.id}
                  className="bg-wo-surface-raised border border-wo-border-subtle rounded-lg px-4 py-3"
                >
                  <div className="flex items-center gap-3">
                    <div className={`p-2 rounded-lg border ${typeCfg.cls}`}>{typeCfg.icon}</div>
                    <div className="flex-1 min-w-0">
                      <div className="flex items-center gap-2 mb-0.5 flex-wrap">
                        <span className="text-[13px] font-semibold text-slate-200">
                          {tx.employee_name ?? `Angajat ${tx.employee_id}`}
                        </span>
                        <span className={`px-2 py-0.5 text-[10px] font-semibold rounded border ${typeCfg.cls}`}>
                          {typeCfg.label}
                        </span>
                        <span className={`px-2 py-0.5 text-[10px] font-semibold rounded border ${statusCfg.cls}`}>
                          {statusCfg.label}
                        </span>
                      </div>
                      <p className="text-[10px] text-slate-500">
                        {tx.transaction_date}
                        {tx.notes ? ` · ${tx.notes}` : ""}
                      </p>
                    </div>
                    <div className="text-right">
                      <p className="text-[16px] font-bold text-slate-100">
                        {tx.amount.toLocaleString("ro-RO")} {tx.currency}
                      </p>
                      <p className="text-[10px] text-slate-500">
                        impact sold: {tx.signed_amount.toLocaleString("ro-RO")}
                      </p>
                    </div>
                    {tx.status === "active" && (
                      <button
                        type="button"
                        onClick={() => handleCancel(tx.id)}
                        className="text-[11px] text-amber-400 hover:text-amber-300 px-2 py-1 border border-amber-800/50 rounded"
                      >
                        Anulează
                      </button>
                    )}
                  </div>
                </div>
              );
            })
          )}
        </div>

        <div>
          <h2 className="text-[13px] font-semibold text-slate-300 uppercase tracking-wide mb-2">
            Sumar sold / angajat
          </h2>
          <div className="space-y-2 max-h-[480px] overflow-y-auto">
            {(summary?.employees ?? []).map((row) => (
              <div
                key={row.employee_id}
                className="bg-wo-surface-raised border border-wo-border-subtle rounded-lg px-3 py-2"
              >
                <div className="flex justify-between items-start gap-2">
                  <div>
                    <p className="text-[13px] font-semibold text-slate-200">{row.employee_name}</p>
                    <p className="text-[10px] text-slate-500">{row.transaction_count} tranzacții</p>
                  </div>
                  <p className="text-[14px] font-bold text-amber-400">
                    {row.active_balance.toLocaleString("ro-RO")} {currency}
                  </p>
                </div>
              </div>
            ))}
          </div>
        </div>
      </div>

      <Dialog open={formOpen} onOpenChange={setFormOpen}>
        <DialogContent className="bg-wo-surface-raised border-wo-border-subtle text-slate-100 max-w-md">
          <DialogHeader>
            <DialogTitle>Adaugă tranzacție internă</DialogTitle>
          </DialogHeader>
          <div className="space-y-3 text-[12px]">
            <label className="block space-y-1">
              <span className="text-slate-400">Angajat</span>
              <select
                value={formEmployeeId}
                onChange={(e) => setFormEmployeeId(Number(e.target.value))}
                className="w-full bg-wo-surface-inset border border-wo-border-subtle rounded px-2 py-2"
              >
                {activeEmployees.map((emp) => (
                  <option key={emp.id} value={emp.id}>{emp.name}</option>
                ))}
              </select>
            </label>
            <label className="block space-y-1">
              <span className="text-slate-400">Tip tranzacție</span>
              <select
                value={formType}
                onChange={(e) => setFormType(e.target.value as BalanceTransactionType)}
                className="w-full bg-wo-surface-inset border border-wo-border-subtle rounded px-2 py-2"
              >
                {TYPE_OPTIONS.map((o) => (
                  <option key={o.value} value={o.value}>{o.label}</option>
                ))}
              </select>
            </label>
            <label className="block space-y-1">
              <span className="text-slate-400">Dată</span>
              <input
                type="date"
                value={formDate}
                onChange={(e) => setFormDate(e.target.value)}
                className="w-full bg-wo-surface-inset border border-wo-border-subtle rounded px-2 py-2"
              />
            </label>
            <div className="grid grid-cols-2 gap-2">
              <label className="block space-y-1">
                <span className="text-slate-400">Sumă</span>
                <input
                  type="number"
                  min="0"
                  step="0.01"
                  value={formAmount}
                  onChange={(e) => setFormAmount(e.target.value)}
                  className="w-full bg-wo-surface-inset border border-wo-border-subtle rounded px-2 py-2"
                />
              </label>
              <label className="block space-y-1">
                <span className="text-slate-400">Monedă</span>
                <input
                  type="text"
                  value={formCurrency}
                  onChange={(e) => setFormCurrency(e.target.value)}
                  className="w-full bg-wo-surface-inset border border-wo-border-subtle rounded px-2 py-2"
                />
              </label>
            </div>
            <label className="block space-y-1">
              <span className="text-slate-400">Observații</span>
              <textarea
                value={formNotes}
                onChange={(e) => setFormNotes(e.target.value)}
                rows={3}
                className="w-full bg-wo-surface-inset border border-wo-border-subtle rounded px-2 py-2"
              />
            </label>
            {formError && <p className="text-red-400 text-[11px]">{formError}</p>}
          </div>
          <DialogFooter>
            <button
              type="button"
              onClick={() => setFormOpen(false)}
              className="px-3 py-2 text-[12px] text-slate-400"
            >
              Anulează
            </button>
            <button
              type="button"
              disabled={formSaving}
              onClick={() => void handleSave()}
              className="px-3 py-2 text-[12px] font-semibold bg-blue-600 hover:bg-blue-500 rounded text-white disabled:opacity-50"
            >
              {formSaving ? "Se salvează..." : "Salvează"}
            </button>
          </DialogFooter>
        </DialogContent>
      </Dialog>
    </div>
  );
}
