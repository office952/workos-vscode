/**
 * Employees page — canonical reflection of backend data.
 *
 * Rules:
 *  - NO mock data.
 *  - NO local cost computation. `cost_ora_calculat` and
 *    `valid_for_cost_engine` come straight from the backend.
 *  - UI only displays / edits / visually validates.
 *  - All writes go to `/api/v1/entities/employees`.
 */
import { useCallback, useEffect, useMemo, useState } from "react";
import {
  Users,
  Search,
  Plus,
  Pencil,
  Trash2,
  CheckCircle2,
  AlertTriangle,
  RefreshCw,
  Save,
  X,
  ChevronRight,
  Info,
  Database,
  UserCheck,
  UserX,
  Briefcase,
  Building2,
} from "lucide-react";
import { Badge } from "@/components/ui/badge";
import {
  employeesApi,
  type EmployeeDTO,
  type EmployeePayload,
} from "@/api/costEngine";
import { EmployeeOperationalPanel } from "@/features/operational-registry/EmployeeOperationalPanel";
import { InternalCostNotice, chromeBanner } from "@/components/workos/design-system";
import EmployeeMobileAccessBadge from "@/components/workos/employees/EmployeeMobileAccessBadge";
import EmployeeAdminOperationalSummary from "@/components/workos/employees/EmployeeAdminOperationalSummary";
import {
  employeeAuthRoleLabel,
  employeeMatchesMobileQuickFilter,
  employeeSearchHaystack,
  getEmployeeMobileAccessDisplay,
} from "@/lib/employeeAdminAccess";

// ------------------------------------------------------------
// Canonical option lists (labels only — backend stores the values)
// ------------------------------------------------------------
const STATUS_OPTIONS: { value: string; label: string }[] = [
  { value: "active", label: "Activ" },
  { value: "inactive", label: "Inactiv" },
  { value: "ended", label: "Încheiat" },
  { value: "on_leave", label: "Concediu" },
  { value: "sick", label: "Medical" },
  { value: "training", label: "Training" },
];

const EMPLOYEE_TYPE_OPTIONS: { value: string; label: string }[] = [
  { value: "productive", label: "Productiv" },
  { value: "indirect", label: "Indirect" },
  { value: "administrativ", label: "Administrativ" },
];

const QUICK_STATUS_FILTERS: { value: string; label: string }[] = [
  { value: "all", label: "Toți" },
  { value: "active", label: "Activi" },
  { value: "inactive", label: "Inactivi" },
  { value: "ended", label: "Încheiați" },
];

const QUICK_MOBILE_FILTERS: { value: "all" | "mobile" | "no_mobile"; label: string }[] = [
  { value: "all", label: "Acces mobil: toți" },
  { value: "mobile", label: "Cu acces mobil" },
  { value: "no_mobile", label: "Fără acces mobil" },
];

function statusLabel(v: string | null | undefined): string {
  return STATUS_OPTIONS.find((s) => s.value === v)?.label ?? (v ?? "—");
}

function typeLabel(v: string | null | undefined): string {
  return EMPLOYEE_TYPE_OPTIONS.find((s) => s.value === v)?.label ?? (v ?? "—");
}

function fmtMoney(n: number | null | undefined): string {
  if (n === null || n === undefined || Number.isNaN(n)) return "—";
  return n.toLocaleString("ro-RO", {
    minimumFractionDigits: 2,
    maximumFractionDigits: 2,
  });
}

function fmtNumber(n: number | null | undefined): string {
  if (n === null || n === undefined || Number.isNaN(n)) return "—";
  return n.toLocaleString("ro-RO", { maximumFractionDigits: 2 });
}

// ------------------------------------------------------------
// Editable form state — mirrors backend payload
// ------------------------------------------------------------
interface FormState {
  name: string;
  role: string;
  department: string;
  status: string;
  employee_type: string;
  cost_lunar_firma: string;
  monthly_internal_pay_amount: string;
  ore_lucru_luna: string;
  ore_productive_luna: string;
  skills: string; // comma separated
  machines: string; // comma separated
  data_angajare: string; // yyyy-mm-dd
  end_date: string; // yyyy-mm-dd — resignation / termination
  observatii: string;
}

const EMPTY_FORM: FormState = {
  name: "",
  role: "",
  department: "",
  status: "active",
  employee_type: "productive",
  cost_lunar_firma: "",
  monthly_internal_pay_amount: "",
  ore_lucru_luna: "",
  ore_productive_luna: "",
  skills: "",
  machines: "",
  data_angajare: "",
  end_date: "",
  observatii: "",
};

function toFormState(e: EmployeeDTO): FormState {
  return {
    name: e.name ?? "",
    role: e.role ?? "",
    department: e.department ?? "",
    status: e.status ?? "active",
    employee_type: e.employee_type ?? "productive",
    cost_lunar_firma:
      e.cost_lunar_firma === null || e.cost_lunar_firma === undefined
        ? ""
        : String(e.cost_lunar_firma),
    monthly_internal_pay_amount:
      e.monthly_internal_pay_amount === null || e.monthly_internal_pay_amount === undefined
        ? ""
        : String(e.monthly_internal_pay_amount),
    ore_lucru_luna:
      e.ore_lucru_luna === null || e.ore_lucru_luna === undefined
        ? ""
        : String(e.ore_lucru_luna),
    ore_productive_luna:
      e.ore_productive_luna === null || e.ore_productive_luna === undefined
        ? ""
        : String(e.ore_productive_luna),
    skills: (e.skills ?? []).join(", "),
    machines: (e.machines ?? []).join(", "),
    data_angajare: e.data_angajare ? e.data_angajare.slice(0, 10) : "",
    end_date: e.end_date ? e.end_date.slice(0, 10) : "",
    observatii: e.observatii ?? "",
  };
}

function parseList(raw: string): string[] | null {
  const items = raw
    .split(",")
    .map((s) => s.trim())
    .filter(Boolean);
  return items.length > 0 ? items : null;
}

function parseNumberOrNull(raw: string): number | null {
  if (!raw || !raw.trim()) return null;
  const n = Number(raw.replace(",", "."));
  return Number.isFinite(n) ? n : null;
}

interface ValidationResult {
  fieldErrors: Record<string, string>;
  warnings: string[];
}

/**
 * Visual-only validation. Backend is the source of truth, but we want to
 * surface obvious mistakes before sending the request. This does NOT compute
 * cost — it only checks presence / ranges that the backend also enforces.
 */
function validateForm(f: FormState): ValidationResult {
  const fieldErrors: Record<string, string> = {};
  const warnings: string[] = [];

  if (!f.name.trim()) fieldErrors.name = "Numele este obligatoriu.";

  const cost = parseNumberOrNull(f.cost_lunar_firma);
  const oreLucru = parseNumberOrNull(f.ore_lucru_luna);
  const oreProd = parseNumberOrNull(f.ore_productive_luna);

  if (f.employee_type === "productive") {
    if (cost === null || cost <= 0)
      fieldErrors.cost_lunar_firma =
        "Cost lunar firmă este obligatoriu (> 0) pentru angajați productivi.";
    // Ore productive = Company Calendar − concediu aprobat (nu se introduc manual).
  } else {
    if (cost !== null && cost < 0)
      fieldErrors.cost_lunar_firma = "Cost lunar firmă nu poate fi negativ.";
  }
  if (oreProd !== null && oreProd < 0)
    fieldErrors.ore_productive_luna = "Orele productive nu pot fi negative.";

  if (oreLucru !== null && oreLucru < 0)
    fieldErrors.ore_lucru_luna = "Orele de lucru nu pot fi negative.";

  const internalPay = parseNumberOrNull(f.monthly_internal_pay_amount);
  if (internalPay !== null && internalPay < 0)
    fieldErrors.monthly_internal_pay_amount =
      "Suma lunară internă nu poate fi negativă.";

  if (oreLucru !== null && oreProd !== null && oreProd > oreLucru) {
    warnings.push(
      "Orele productive depășesc orele totale de lucru — verifică valorile."
    );
  }

  return { fieldErrors, warnings };
}

function formToPayload(f: FormState): EmployeePayload {
  return {
    name: f.name.trim(),
    role: f.role.trim() || null,
    department: f.department.trim() || null,
    status: f.status || null,
    employee_type: f.employee_type || null,
    cost_lunar_firma: parseNumberOrNull(f.cost_lunar_firma),
    monthly_internal_pay_amount: parseNumberOrNull(f.monthly_internal_pay_amount),
    ore_lucru_luna: parseNumberOrNull(f.ore_lucru_luna),
    ore_productive_luna: parseNumberOrNull(f.ore_productive_luna),
    skills: parseList(f.skills),
    machines: parseList(f.machines),
    data_angajare: f.data_angajare ? `${f.data_angajare}T00:00:00` : null,
    end_date: f.end_date ? `${f.end_date}T00:00:00` : null,
    observatii: f.observatii.trim() || null,
  };
}

// ------------------------------------------------------------
// Validation badge shown in the list + detail
// ------------------------------------------------------------
function ValidityBadge({ valid }: { valid: boolean }) {
  if (valid) {
    return (
      <span className="inline-flex items-center gap-1 text-[10px] font-semibold text-wo-success bg-wo-success-muted border border-wo-success/35 rounded px-1.5 py-0.5">
        <CheckCircle2 className="w-3 h-3" />
        Cost intern valid
      </span>
    );
  }
  return (
    <span className="inline-flex items-center gap-1 text-[10px] font-semibold text-wo-warning bg-wo-warning-muted border border-wo-warning/35 rounded px-1.5 py-0.5">
      <AlertTriangle className="w-3 h-3" />
      Date incomplete
    </span>
  );
}

function EmployeeStatusBadge({ status }: { status: string }) {
  const label = statusLabel(status);
  const isActive = status === "active";
  return (
    <span
      className={`inline-flex items-center gap-1 text-[10px] font-semibold rounded-full border px-2 py-0.5 ${
        isActive
          ? "text-wo-success bg-wo-success-muted border-wo-success/35"
          : "text-wo-text-secondary bg-wo-surface-inset border-wo-border-strong"
      }`}
    >
      {isActive ? (
        <UserCheck className="w-3 h-3 shrink-0" aria-hidden />
      ) : (
        <UserX className="w-3 h-3 shrink-0" aria-hidden />
      )}
      {label}
    </span>
  );
}

// ============================================================
// Main component
// ============================================================
export default function Employees() {
  const [items, setItems] = useState<EmployeeDTO[]>([]);
  const [loading, setLoading] = useState(true);
  const [loadError, setLoadError] = useState<string | null>(null);

  const [search, setSearch] = useState("");
  const [statusFilter, setStatusFilter] = useState<string>("all");
  const [typeFilter, setTypeFilter] = useState<string>("all");
  const [mobileFilter, setMobileFilter] = useState<"all" | "mobile" | "no_mobile">("all");

  const [selectedId, setSelectedId] = useState<number | null>(null);
  const [mode, setMode] = useState<"view" | "edit" | "create">("view");
  const [form, setForm] = useState<FormState>(EMPTY_FORM);
  const [fieldErrors, setFieldErrors] = useState<Record<string, string>>({});
  const [formWarnings, setFormWarnings] = useState<string[]>([]);
  const [saving, setSaving] = useState(false);
  const [saveError, setSaveError] = useState<string | null>(null);
  const [deleting, setDeleting] = useState(false);

  const load = useCallback(async () => {
    setLoading(true);
    setLoadError(null);
    try {
      const res = await employeesApi.list({ limit: 500, sort: "name" });
      setItems(res.items);
    } catch (err) {
      setLoadError(err instanceof Error ? err.message : "Eroare la încărcare");
    } finally {
      setLoading(false);
    }
  }, []);

  useEffect(() => {
    void load();
  }, [load]);

  const selected = useMemo(
    () => items.find((e) => e.id === selectedId) ?? null,
    [items, selectedId]
  );

  // ---- Filtering ----
  const filtered = useMemo(() => {
    const q = search.trim().toLowerCase();
    return items.filter((e) => {
      if (statusFilter !== "all" && e.status !== statusFilter) return false;
      if (typeFilter !== "all" && e.employee_type !== typeFilter) return false;
      if (!employeeMatchesMobileQuickFilter(e, mobileFilter)) return false;
      if (q && !employeeSearchHaystack(e).includes(q)) return false;
      return true;
    });
  }, [items, search, statusFilter, typeFilter, mobileFilter]);

  // ---- KPIs (come from backend fields, no UI math) ----
  const kpis = useMemo(() => {
    const total = items.length;
    const valid = items.filter((e) => e.valid_for_cost_engine).length;
    const productive = items.filter((e) => e.employee_type === "productive").length;
    const active = items.filter((e) => e.status === "active").length;
    const mobileActive = items.filter((e) => e.has_mobile_access).length;
    return { total, valid, productive, active, mobileActive };
  }, [items]);

  // ---- Form handlers ----
  const startCreate = () => {
    setSelectedId(null);
    setMode("create");
    setForm(EMPTY_FORM);
    setFieldErrors({});
    setFormWarnings([]);
    setSaveError(null);
  };

  const startEdit = (e: EmployeeDTO) => {
    setSelectedId(e.id);
    setMode("edit");
    setForm(toFormState(e));
    setFieldErrors({});
    setFormWarnings([]);
    setSaveError(null);
  };

  const cancelForm = () => {
    setMode("view");
    setFieldErrors({});
    setFormWarnings([]);
    setSaveError(null);
    if (selected) setForm(toFormState(selected));
    else setForm(EMPTY_FORM);
  };

  const updateForm = <K extends keyof FormState>(key: K, value: FormState[K]) => {
    setForm((prev) => {
      const next = { ...prev, [key]: value };
      const v = validateForm(next);
      setFieldErrors(v.fieldErrors);
      setFormWarnings(v.warnings);
      return next;
    });
  };

  const submit = async () => {
    const v = validateForm(form);
    setFieldErrors(v.fieldErrors);
    setFormWarnings(v.warnings);
    if (Object.keys(v.fieldErrors).length > 0) return;

    setSaving(true);
    setSaveError(null);
    try {
      const payload = formToPayload(form);
      if (mode === "create") {
        const created = await employeesApi.create(payload);
        await load();
        setSelectedId(created.id);
        setMode("view");
      } else if (mode === "edit" && selectedId !== null) {
        const updated = await employeesApi.update(selectedId, payload);
        await load();
        setSelectedId(updated.id);
        setMode("view");
      }
    } catch (err) {
      setSaveError(err instanceof Error ? err.message : "Eroare la salvare");
    } finally {
      setSaving(false);
    }
  };

  const remove = async () => {
    if (selectedId === null) return;
    if (
      !window.confirm(
        "Închei contractul acestui angajat? Nu se șterge din istoric (pontaj/taskuri/costuri rămân legate). Status → Încheiat + data de azi.",
      )
    )
      return;
    setDeleting(true);
    try {
      await employeesApi.remove(selectedId);
      await load();
      setMode("view");
    } catch (err) {
      setSaveError(err instanceof Error ? err.message : "Eroare la încheiere");
    } finally {
      setDeleting(false);
    }
  };

  // ============================================================
  // Render
  // ============================================================
  return (
    <div className="space-y-5 pb-4">
      {/* Header first — hierarchy: title → KPIs → filters → list; boundary collapsed */}
      <div className="flex items-center justify-between flex-wrap gap-2">
        <div className="flex flex-col gap-1">
          <div className="flex items-center gap-2 flex-wrap">
            <Users className="w-5 h-5 text-wo-info" />
            <h1 className="text-[18px] font-bold text-wo-text-primary">Angajați operaționali</h1>
            <Badge className="gap-1 text-[10px] uppercase tracking-wide border-wo-success/35 bg-wo-success-muted text-wo-success hover:bg-wo-success-muted">
              <Database className="w-3 h-3" />
              LIVE DB
            </Badge>
            <Badge className="text-[10px] uppercase tracking-wide border-wo-info/35 bg-wo-info-muted text-wo-info hover:bg-wo-info-muted">
              OPERAȚIONAL
            </Badge>
            <span className="text-[10px] text-wo-text-muted bg-wo-surface-inset border border-wo-border-subtle px-2 py-0.5 rounded-full">
              {kpis.total} persoane
            </span>
          </div>
          <p className="text-[13px] text-wo-text-muted pl-7">
            Registry pentru execuție, operații, autorizări și alocări. Nu este evidență salarială.
          </p>
        </div>
        <div className="flex items-center gap-2">
          <button
            onClick={() => void load()}
            className="inline-flex items-center gap-1.5 px-3 py-1.5 text-[12px] text-wo-text-secondary bg-wo-surface-raised border border-wo-border-strong rounded-md hover:bg-wo-hover transition-colors"
          >
            <RefreshCw className="w-3.5 h-3.5" />
            Reîncarcă
          </button>
          <button
            onClick={startCreate}
            className="inline-flex items-center gap-1.5 px-3 py-1.5 text-[12px] font-semibold text-wo-info bg-wo-info-muted border border-wo-info/40 rounded-md hover:bg-wo-hover transition-colors"
          >
            <Plus className="w-3.5 h-3.5" />
            Adaugă angajat
          </button>
        </div>
      </div>

      <details
        className={`rounded-lg px-3 py-2 group ${chromeBanner.info}`}
        data-testid="employees-cost-boundary"
      >
        <summary className="cursor-pointer list-none text-[11px] font-semibold text-wo-text-primary flex items-center gap-2">
          <Info className="w-3.5 h-3.5 text-wo-info shrink-0" />
          Boundary cost intern — NU tarif client
          <span className="text-[10px] font-normal text-wo-text-muted group-open:hidden">
            (detalii)
          </span>
        </summary>
        <div className="mt-2 space-y-2">
          <InternalCostNotice
            message="Cost intern angajat — analytics / profitability. NU tarif client. Registry intern HR nu conduce oferta client. Nu inventăm salariu → tarif comercial."
            compact
          />
          <div className="flex flex-wrap items-center gap-2">
            <span className="rounded border border-wo-info/35 bg-wo-surface-raised px-2 py-0.5 text-[10px] text-wo-info">
              Cost Intern = analytics
            </span>
            <span className="rounded border border-wo-success/35 bg-wo-surface-raised px-2 py-0.5 text-[10px] text-wo-success">
              Nu Pricing Registry
            </span>
            <span className="rounded border border-wo-warning/35 bg-wo-surface-raised px-2 py-0.5 text-[10px] text-wo-warning">
              Nu Ofertă client
            </span>
          </div>
        </div>
      </details>

      {/* KPIs */}
      <div className="grid grid-cols-2 md:grid-cols-4 gap-3">
        <div className="bg-wo-surface-raised border border-wo-border-strong rounded-lg p-3">
          <p className="text-[10px] text-wo-text-muted uppercase tracking-wide mb-1">Total</p>
          <p className="text-[22px] font-bold text-wo-text-primary">{kpis.total}</p>
          <p className="text-[10px] text-wo-text-muted">angajați înregistrați</p>
        </div>
        <div className="bg-wo-surface-raised border border-wo-border-strong rounded-lg p-3">
          <p className="text-[10px] text-wo-text-muted uppercase tracking-wide mb-1">Activi</p>
          <p className="text-[22px] font-bold text-wo-success">{kpis.active}</p>
          <p className="text-[10px] text-wo-text-muted">status = activ</p>
        </div>
        <div className="bg-wo-surface-raised border border-wo-border-strong rounded-lg p-3">
          <p className="text-[10px] text-wo-text-muted uppercase tracking-wide mb-1">Productivi</p>
          <p className="text-[22px] font-bold text-wo-info">{kpis.productive}</p>
          <p className="text-[10px] text-wo-text-muted">intră în calcul cost intern</p>
        </div>
        <div className="bg-wo-surface-raised border border-wo-border-strong rounded-lg p-3">
          <p className="text-[10px] text-muted-foreground uppercase tracking-wide mb-1">Validați cost intern</p>
          <p className="text-[22px] font-bold text-foreground">
            {kpis.valid}
            <span className="text-[12px] text-muted-foreground"> / {kpis.total}</span>
          </p>
          <p className="text-[10px] text-muted-foreground">date complete pentru costare</p>
        </div>
      </div>

      {/* Filters */}
      <div className="space-y-2">
        <div className="flex items-center gap-3 flex-wrap">
          <div className="flex items-center gap-2 bg-card border border-border rounded-lg px-3 py-2 flex-1 max-w-md focus-within:border-blue-500/50">
            <Search className="w-4 h-4 text-muted-foreground" />
            <input
              type="text"
              value={search}
              onChange={(e) => setSearch(e.target.value)}
              placeholder="Caută nume, rol, departament, email, user..."
              className="bg-transparent text-[13px] text-foreground placeholder:text-wo-text-dim outline-none w-full"
              data-testid="employees-search-input"
            />
          </div>
          <select
            value={statusFilter}
            onChange={(e) => setStatusFilter(e.target.value)}
            className="bg-card border border-border rounded-md px-2 py-2 text-[12px] text-foreground"
            data-testid="employees-status-select"
          >
            <option value="all">Toate statusurile</option>
            {STATUS_OPTIONS.map((o) => (
              <option key={o.value} value={o.value}>
                {o.label}
              </option>
            ))}
          </select>
          <select
            value={typeFilter}
            onChange={(e) => setTypeFilter(e.target.value)}
            className="bg-card border border-border rounded-md px-2 py-2 text-[12px] text-foreground"
            data-testid="employees-type-select"
          >
            <option value="all">Toate tipurile</option>
            {EMPLOYEE_TYPE_OPTIONS.map((o) => (
              <option key={o.value} value={o.value}>
                {o.label}
              </option>
            ))}
          </select>
          <span className="text-[11px] text-muted-foreground ml-auto">
            {filtered.length} rezultate
          </span>
        </div>
        <div
          className="flex flex-wrap gap-1.5"
          role="group"
          aria-label="Filtru rapid status"
          data-testid="employees-quick-status-filters"
        >
          {QUICK_STATUS_FILTERS.map((option) => {
            const active = statusFilter === option.value;
            return (
              <button
                key={option.value}
                type="button"
                className={`px-2.5 py-1.5 text-[10px] font-medium rounded-full border transition-colors min-h-[30px] ${
                  active
                    ? "bg-wo-info-muted text-wo-info border-wo-info/40"
                    : "bg-wo-surface-raised text-wo-text-muted border-wo-border-strong hover:bg-wo-hover hover:text-wo-text-secondary"
                }`}
                data-testid={`employees-quick-filter-${option.value}`}
                aria-pressed={active}
                onClick={() => setStatusFilter(option.value)}
              >
                {option.label}
              </button>
            );
          })}
        </div>
        <div
          className="flex flex-wrap gap-1.5"
          role="group"
          aria-label="Filtru rapid acces mobil"
          data-testid="employees-quick-mobile-filters"
        >
          {QUICK_MOBILE_FILTERS.map((option) => {
            const active = mobileFilter === option.value;
            return (
              <button
                key={option.value}
                type="button"
                className={`px-2.5 py-1.5 text-[10px] font-medium rounded-full border transition-colors min-h-[30px] ${
                  active
                    ? "bg-wo-success-muted text-wo-success border-wo-success/40"
                    : "bg-wo-surface-raised text-wo-text-muted border-wo-border-strong hover:bg-wo-hover hover:text-wo-text-secondary"
                }`}
                data-testid={`employees-quick-mobile-filter-${option.value}`}
                aria-pressed={active}
                onClick={() => setMobileFilter(option.value)}
              >
                {option.label}
              </button>
            );
          })}
        </div>
      </div>

      {loadError && (
        <div className="space-y-2">
          <div className={`rounded-lg px-4 py-3 text-[12px] border ${
            loadError.includes("401") || loadError.includes("403") || loadError.toLowerCase().includes("unauthorized")
              ? "bg-wo-warning-muted border-wo-warning/35 text-wo-warning"
              : "bg-wo-error-muted border-wo-error/35 text-wo-error"
          }`}>
            <div className="flex items-start gap-2">
              <AlertTriangle className="w-4 h-4 mt-0.5 shrink-0" />
              <div className="space-y-1">
                <p className="font-semibold">
                  {loadError.includes("401") || loadError.includes("403") || loadError.toLowerCase().includes("unauthorized")
                    ? "Autentificare necesară"
                    : loadError.includes("fetch") || loadError.includes("network") || loadError.includes("Failed to fetch")
                      ? "Backend indisponibil"
                      : "Eroare la încărcarea angajaților"}
                </p>
                <p className="text-[11px] opacity-80">
                  {loadError.includes("401") || loadError.includes("403") || loadError.toLowerCase().includes("unauthorized")
                    ? "Sesiunea a expirat sau nu ai permisiuni. Reautentifică-te sau verifică setările de acces."
                    : loadError.includes("fetch") || loadError.includes("network") || loadError.includes("Failed to fetch")
                      ? "Nu s-a putut conecta la server. Verifică dacă backend-ul rulează și este accesibil."
                      : loadError}
                </p>
              </div>
            </div>
          </div>
          <div className="flex items-start gap-2 px-3 py-2 bg-blue-900/10 border border-blue-800/20 rounded-lg">
            <Info className="w-3.5 h-3.5 text-blue-600 dark:text-blue-400 mt-0.5 shrink-0" />
            <p className="text-[10px] text-blue-600/80 dark:text-blue-300/80">
              <strong>Sugestie:</strong> Modulul Angajați necesită backend live (nu funcționează cu date mock).
              Asigură-te că serverul FastAPI este pornit și accesibil.
            </p>
          </div>
        </div>
      )}

      <div className="grid grid-cols-1 lg:grid-cols-3 gap-4">
        {/* List */}
        <div className="lg:col-span-2 space-y-2">
          {loading && (
            <div
              className="bg-card border border-border rounded-lg p-8 text-center text-muted-foreground text-[13px]"
              data-testid="employees-loading"
            >
              Se încarcă angajații…
            </div>
          )}
          {!loading && filtered.length === 0 && (
            <div
              className="bg-card border border-border rounded-lg p-8 text-center space-y-2"
              data-testid="employees-empty"
            >
              <Users className="w-8 h-8 text-wo-text-dim mx-auto" aria-hidden />
              <p className="text-[13px] text-muted-foreground">
                {items.length === 0
                  ? "Niciun angajat înregistrat încă."
                  : "Niciun angajat nu corespunde filtrelor selectate."}
              </p>
            </div>
          )}
          {!loading &&
            filtered.map((e) => {
              const active = selectedId === e.id;
              return (
                <div
                  key={e.id}
                  data-testid={`employees-list-item-${e.id}`}
                  onClick={() => {
                    setSelectedId(e.id);
                    setMode("view");
                  }}
                  className={`bg-wo-surface-raised border rounded-xl p-3.5 cursor-pointer transition-all focus-within:ring-1 focus-within:ring-wo-info/40 ${
                    active
                      ? "border-wo-info/50 ring-1 ring-wo-info/30"
                      : "border-wo-border-subtle hover:border-wo-border-strong hover:bg-wo-hover"
                  }`}
                >
                  <div className="flex items-center gap-3">
                    <div className="w-10 h-10 rounded-full bg-wo-surface-inset border border-wo-border-strong flex items-center justify-center text-[13px] font-bold text-wo-text-secondary shrink-0">
                      {e.name
                        .split(" ")
                        .map((n) => n[0])
                        .slice(0, 2)
                        .join("")}
                    </div>
                    <div className="flex-1 min-w-0">
                      <div className="flex items-center gap-2 mb-1 flex-wrap">
                        <span className="text-[13px] font-semibold text-foreground">
                          {e.name}
                        </span>
                        <EmployeeStatusBadge status={e.status} />
                        <span className="text-[10px] text-muted-foreground bg-muted px-1.5 py-0.5 rounded">
                          {typeLabel(e.employee_type)}
                        </span>
                      </div>
                      <div className="flex items-center gap-2 text-[11px] text-muted-foreground flex-wrap">
                        <span className="inline-flex items-center gap-1">
                          <Briefcase className="w-3 h-3 shrink-0 text-muted-foreground" aria-hidden />
                          {e.role || "fără rol"}
                        </span>
                        <span className="text-wo-text-dim">·</span>
                        <span className="inline-flex items-center gap-1">
                          <Building2 className="w-3 h-3 shrink-0 text-muted-foreground" aria-hidden />
                          {e.department || "—"}
                        </span>
                      </div>
                      <div className="flex items-center gap-2 mt-1.5 flex-wrap">
                        <EmployeeMobileAccessBadge employee={e} compact />
                        <ValidityBadge valid={e.valid_for_cost_engine} />
                        <span className="text-[10px] text-wo-text-dim">
                          Cost orar: {fmtMoney(e.cost_ora_calculat)} /h
                        </span>
                      </div>
                    </div>
                    <ChevronRight className="w-4 h-4 text-wo-text-dim shrink-0" />
                  </div>
                </div>
              );
            })}
        </div>

        {/* Detail / Form */}
        <div className="space-y-4">
          {mode === "view" && selected && (
            <>
              <EmployeeDetail
                employee={selected}
                onEdit={() => startEdit(selected)}
                onDelete={remove}
                deleting={deleting}
              />
              <EmployeeAdminOperationalSummary employeeId={selected.id} />
              <EmployeeOperationalPanel employeeId={selected.id} readOnly />
            </>
          )}
          {mode === "view" && !selected && (
            <div className="bg-card border border-border rounded-lg p-8 text-center">
              <Users className="w-8 h-8 text-wo-text-dim mx-auto mb-2" />
              <p className="text-[13px] text-muted-foreground">
                Selectează un angajat sau adaugă unul nou.
              </p>
            </div>
          )}
          {(mode === "edit" || mode === "create") && (
            <>
              <EmployeeForm
                form={form}
                mode={mode}
                fieldErrors={fieldErrors}
                warnings={formWarnings}
                saving={saving}
                saveError={saveError}
                onChange={updateForm}
                onCancel={cancelForm}
                onSubmit={submit}
              />
              {mode === "edit" && selectedId != null && (
                <EmployeeOperationalPanel employeeId={selectedId} />
              )}
            </>
          )}
        </div>
      </div>
    </div>
  );
}

// ============================================================
// Detail panel (read-only view of backend-provided fields)
// ============================================================
function EmployeeDetail({
  employee: e,
  onEdit,
  onDelete,
  deleting,
}: {
  employee: EmployeeDTO;
  onEdit: () => void;
  onDelete: () => void;
  deleting: boolean;
}) {
  const mobileAccess = getEmployeeMobileAccessDisplay(e);

  return (
    <div
      className="bg-card border border-border rounded-lg p-4 space-y-3"
      data-testid="employee-detail-panel"
    >
      <div className="flex items-start gap-3">
        <div className="w-11 h-11 rounded-full bg-wo-surface-inset border border-wo-border-strong flex items-center justify-center text-[14px] font-bold text-wo-text-secondary">
          {e.name
            .split(" ")
            .map((n) => n[0])
            .slice(0, 2)
            .join("")}
        </div>
        <div className="flex-1 min-w-0">
          <h3 className="text-[15px] font-bold text-foreground">{e.name}</h3>
          <div className="flex items-center gap-1.5 mt-1 flex-wrap">
            <span className="text-[10px] text-muted-foreground bg-muted px-1.5 py-0.5 rounded">
              {typeLabel(e.employee_type)}
            </span>
            <span className="text-[10px] text-muted-foreground bg-muted px-1.5 py-0.5 rounded">
              {statusLabel(e.status)}
            </span>
            <ValidityBadge valid={e.valid_for_cost_engine} />
          </div>
        </div>
        <div className="flex items-center gap-1">
          <button
            onClick={onEdit}
            className="p-1.5 text-muted-foreground hover:text-foreground bg-wo-surface-raised border border-wo-border-strong rounded-md hover:border-slate-500 transition-colors"
            title="Editează"
          >
            <Pencil className="w-3.5 h-3.5" />
          </button>
          {e.status !== "ended" && e.status !== "inactive" && (
            <button
              onClick={onDelete}
              disabled={deleting}
              className="p-1.5 text-red-600 hover:text-red-500 dark:text-red-400 dark:hover:text-red-300 bg-wo-surface-raised border border-wo-border-strong rounded-md hover:border-red-600/60 transition-colors disabled:opacity-50"
              title="Încheie angajarea (fără ștergere)"
              data-testid="employee-end-employment"
            >
              <Trash2 className="w-3.5 h-3.5" />
            </button>
          )}
        </div>
      </div>

      <div className="grid grid-cols-2 gap-3">
        <Field label="Rol">{e.role || "—"}</Field>
        <Field label="Departament">{e.department || "—"}</Field>
      </div>

      <div
        className="bg-wo-surface-raised rounded-lg p-3 space-y-2.5"
        data-testid="employee-detail-mobile-access"
      >
        <p className="text-[10px] text-muted-foreground uppercase tracking-wide">Acces Employee Mobile</p>
        <div className="flex items-center gap-2 flex-wrap">
          <EmployeeMobileAccessBadge employee={e} />
        </div>
        <p className="text-[11px] text-muted-foreground leading-relaxed">{mobileAccess.description}</p>
        {e.user_id && (
          <Field label="User legat (WorkOS)">
            <span className="font-mono text-[11px] break-all">{e.user_id}</span>
          </Field>
        )}
        {e.auth_email && (
          <Field label="Email cont">{e.auth_email}</Field>
        )}
        {e.auth_role && (
          <Field label="Rol autentificare">{employeeAuthRoleLabel(e.auth_role)}</Field>
        )}
        <p className="text-[10px] text-muted-foreground italic">
          Employee Mobile folosește același cont WorkOS — fără creare automată de conturi din această
          pagină.
        </p>
      </div>

      <div className="bg-wo-surface-raised rounded-lg p-3 space-y-2">
        <p className="text-[10px] text-muted-foreground uppercase tracking-wide">
          Plată internă
        </p>
        <Field label="Sumă lunară internă pentru plată (RON)">
          {fmtMoney(e.monthly_internal_pay_amount)}
        </Field>
        <p className="text-[10px] text-muted-foreground italic">
          Folosită ulterior pentru calculul tranșelor 15/30 în Plăți angajați. Nu
          reprezintă costul total al firmei.
        </p>
      </div>

      <div className="bg-wo-surface-raised rounded-lg p-3 space-y-2">
        <p className="text-[10px] text-muted-foreground uppercase tracking-wide">
          Date cost intern
        </p>
        <div className="grid grid-cols-2 gap-2">
          <Field label="Cost lunar firmă (RON)">
            {fmtMoney(e.cost_lunar_firma)}
          </Field>
          <Field label="Ore productive / lună (calculat)">
            {fmtNumber(e.ore_productive_luna)}
          </Field>
          <Field label="Ore lucru / lună">
            {fmtNumber(e.ore_lucru_luna)}
          </Field>
          <Field label="Cost oră calculat (RON/h)">
            <span className="font-mono text-wo-success">
              {fmtMoney(e.cost_ora_calculat)}
            </span>
          </Field>
        </div>
        <p className="text-[10px] text-muted-foreground italic">
          Ore productive = calendar firmă (L–V 8h − sărbători − concediu
          aprobat). Cost oră = cost_lunar_firma / ore_productive. Frontend-ul
          nu recalculează.
        </p>
      </div>

      {(e.skills?.length ?? 0) > 0 && (
        <div>
          <p className="text-[10px] text-muted-foreground uppercase tracking-wide mb-1">
            Skills
          </p>
          <div className="flex flex-wrap gap-1">
            {(e.skills ?? []).map((s) => (
              <span
                key={s}
                className="px-2 py-0.5 text-[10px] bg-muted text-muted-foreground rounded border border-border"
              >
                {s}
              </span>
            ))}
          </div>
        </div>
      )}

      {(e.machines?.length ?? 0) > 0 && (
        <div>
          <p className="text-[10px] text-muted-foreground uppercase tracking-wide mb-1">
            Utilaje
          </p>
          <div className="flex flex-wrap gap-1">
            {(e.machines ?? []).map((m) => (
              <span
                key={m}
                className="px-2 py-0.5 text-[10px] bg-muted text-muted-foreground rounded border border-border"
              >
                {m}
              </span>
            ))}
          </div>
        </div>
      )}

      <div className="grid grid-cols-2 gap-3">
        <Field label="Data angajării">
          {e.data_angajare
            ? new Date(e.data_angajare).toLocaleDateString("ro-RO")
            : "—"}
        </Field>
        <Field label="Data încheierii">
          {e.end_date ? new Date(e.end_date).toLocaleDateString("ro-RO") : "—"}
        </Field>
      </div>
      <Field label="Eligibil asignare">
        {e.is_assignable === false ? "Nu (inactiv / după end_date)" : "Da"}
      </Field>
      {e.ore_productive_luna_source && (
        <p className="text-[10px] text-muted-foreground italic" data-testid="employee-hours-source">
          Ore productive: {fmtNumber(e.ore_productive_luna)} h · sursă{" "}
          {e.ore_productive_luna_source}
        </p>
      )}

      {e.observatii && (
        <div className="bg-wo-surface-raised rounded-lg p-3">
          <p className="text-[10px] text-muted-foreground uppercase tracking-wide mb-1">
            Observații
          </p>
          <p className="text-[12px] text-muted-foreground whitespace-pre-wrap">
            {e.observatii}
          </p>
        </div>
      )}
    </div>
  );
}

function Field({
  label,
  children,
}: {
  label: string;
  children: React.ReactNode;
}) {
  return (
    <div>
      <p className="text-[10px] text-muted-foreground uppercase tracking-wide mb-1">
        {label}
      </p>
      <div className="text-[12px] text-foreground">{children}</div>
    </div>
  );
}

// ============================================================
// Form panel (create / edit)
// ============================================================
function EmployeeForm({
  form,
  mode,
  fieldErrors,
  warnings,
  saving,
  saveError,
  onChange,
  onCancel,
  onSubmit,
}: {
  form: FormState;
  mode: "edit" | "create";
  fieldErrors: Record<string, string>;
  warnings: string[];
  saving: boolean;
  saveError: string | null;
  onChange: <K extends keyof FormState>(key: K, value: FormState[K]) => void;
  onCancel: () => void;
  onSubmit: () => void;
}) {
  const hasErrors = Object.keys(fieldErrors).length > 0;

  return (
    <form
      onSubmit={(e) => {
        e.preventDefault();
        onSubmit();
      }}
      className="bg-card border border-border rounded-lg p-4 space-y-3"
    >
      <div className="flex items-center justify-between">
        <h3 className="text-[14px] font-bold text-foreground">
          {mode === "create" ? "Angajat nou" : "Editează angajat"}
        </h3>
        <button
          type="button"
          onClick={onCancel}
          className="p-1 text-muted-foreground hover:text-foreground"
          title="Închide"
        >
          <X className="w-4 h-4" />
        </button>
      </div>

      <TextField
        label="Nume *"
        value={form.name}
        onChange={(v) => onChange("name", v)}
        error={fieldErrors.name}
      />

      <div className="grid grid-cols-2 gap-2">
        <TextField
          label="Rol"
          value={form.role}
          onChange={(v) => onChange("role", v)}
        />
        <TextField
          label="Departament"
          value={form.department}
          onChange={(v) => onChange("department", v)}
        />
      </div>

      <div className="grid grid-cols-2 gap-2">
        <SelectField
          label="Status"
          value={form.status}
          onChange={(v) => onChange("status", v)}
          options={STATUS_OPTIONS}
        />
        <SelectField
          label="Tip angajat"
          value={form.employee_type}
          onChange={(v) => onChange("employee_type", v)}
          options={EMPLOYEE_TYPE_OPTIONS}
        />
      </div>

      <div className="bg-wo-surface-raised rounded-lg p-3 space-y-2">
        <p className="text-[10px] text-muted-foreground uppercase tracking-wide">
          Plată internă
        </p>
        <TextField
          label="Sumă lunară internă pentru plată (RON)"
          value={form.monthly_internal_pay_amount}
          onChange={(v) => onChange("monthly_internal_pay_amount", v)}
          type="number"
          error={fieldErrors.monthly_internal_pay_amount}
          hint="Folosită ulterior pentru calculul tranșelor 15/30 în Plăți angajați. Nu reprezintă costul total al firmei."
        />
      </div>

      <div className="bg-wo-surface-raised rounded-lg p-3 space-y-2">
        <p className="text-[10px] text-muted-foreground uppercase tracking-wide">
          Date cost intern
        </p>
        <TextField
          label="Cost lunar firmă (RON) *"
          value={form.cost_lunar_firma}
          onChange={(v) => onChange("cost_lunar_firma", v)}
          type="number"
          error={fieldErrors.cost_lunar_firma}
          hint="Cost total suportat de firmă lunar (salariu + taxe + beneficii)."
        />
        <div className="grid grid-cols-2 gap-2">
          <TextField
            label="Ore lucru / lună"
            value={form.ore_lucru_luna}
            onChange={(v) => onChange("ore_lucru_luna", v)}
            type="number"
            error={fieldErrors.ore_lucru_luna}
          />
          <TextField
            label="Ore productive / lună (opțional / legacy)"
            value={form.ore_productive_luna}
            onChange={(v) => onChange("ore_productive_luna", v)}
            type="number"
            error={fieldErrors.ore_productive_luna}
            hint="Nu e necesar — CostEngine folosește calendarul firmei."
          />
        </div>
        <p className="text-[10px] text-muted-foreground italic">
          Ore productive lunare se calculează automat (calendar − concediu).
          Costul oră este calculat de backend.
        </p>
      </div>

      <TextField
        label="Skills (separate prin virgulă)"
        value={form.skills}
        onChange={(v) => onChange("skills", v)}
      />
      <TextField
        label="Utilaje (separate prin virgulă)"
        value={form.machines}
        onChange={(v) => onChange("machines", v)}
      />

      <div className="grid grid-cols-2 gap-2">
        <TextField
          label="Data angajării (start)"
          value={form.data_angajare}
          onChange={(v) => onChange("data_angajare", v)}
          type="date"
          hint="Capacitate Cost Intern doar după această dată."
        />
        <TextField
          label="Data încheierii (end)"
          value={form.end_date}
          onChange={(v) => onChange("end_date", v)}
          type="date"
          hint="Demisie/încetare — nu șterge istoricul."
        />
      </div>

      <TextareaField
        label="Observații"
        value={form.observatii}
        onChange={(v) => onChange("observatii", v)}
      />

      {warnings.length > 0 && (
        <div className="bg-wo-warning-muted border border-wo-warning/35 text-wo-warning text-[11px] rounded-md px-3 py-2 space-y-1">
          {warnings.map((w) => (
            <div key={w} className="flex items-start gap-1.5">
              <AlertTriangle className="w-3 h-3 mt-0.5 shrink-0" />
              <span>{w}</span>
            </div>
          ))}
        </div>
      )}

      {saveError && (
        <div className="bg-red-100 border border-red-200 text-red-700 dark:bg-red-900/30 dark:border-red-700/50 dark:text-red-300 text-[12px] rounded-md px-3 py-2">
          {saveError}
        </div>
      )}

      <div className="flex items-center gap-2 pt-2">
        <button
          type="submit"
          disabled={saving || hasErrors}
          className="inline-flex items-center gap-1.5 px-3 py-1.5 text-[12px] font-semibold text-wo-info bg-wo-info-muted border border-wo-info/40 rounded-md hover:bg-wo-hover transition-colors disabled:opacity-50 disabled:cursor-not-allowed"
        >
          <Save className="w-3.5 h-3.5" />
          {saving ? "Se salvează..." : mode === "create" ? "Creează" : "Salvează"}
        </button>
        <button
          type="button"
          onClick={onCancel}
          className="px-3 py-1.5 text-[12px] text-muted-foreground bg-wo-surface-raised border border-wo-border-strong rounded-md hover:border-slate-500"
        >
          Anulează
        </button>
      </div>
    </form>
  );
}

// ============================================================
// Small input primitives (shared within file)
// ============================================================
function TextField({
  label,
  value,
  onChange,
  type = "text",
  error,
  hint,
}: {
  label: string;
  value: string;
  onChange: (v: string) => void;
  type?: string;
  error?: string;
  hint?: string;
}) {
  return (
    <div>
      <label className="block text-[10px] text-muted-foreground uppercase tracking-wide mb-1">
        {label}
      </label>
      <input
        type={type}
        value={value}
        onChange={(e) => onChange(e.target.value)}
        step={type === "number" ? "0.01" : undefined}
        className={`w-full bg-background border rounded-md px-2 py-1.5 text-[12px] text-foreground placeholder:text-wo-text-dim outline-none ${
          error
            ? "border-red-600/60 focus:border-red-500"
            : "border-border focus:border-blue-500/50"
        }`}
      />
      {hint && !error && (
        <p className="text-[10px] text-muted-foreground mt-1">{hint}</p>
      )}
      {error && <p className="text-[10px] text-red-600 dark:text-red-400 mt-1">{error}</p>}
    </div>
  );
}

function TextareaField({
  label,
  value,
  onChange,
}: {
  label: string;
  value: string;
  onChange: (v: string) => void;
}) {
  return (
    <div>
      <label className="block text-[10px] text-muted-foreground uppercase tracking-wide mb-1">
        {label}
      </label>
      <textarea
        value={value}
        rows={3}
        onChange={(e) => onChange(e.target.value)}
        className="w-full bg-background border border-border rounded-md px-2 py-1.5 text-[12px] text-foreground placeholder:text-wo-text-dim outline-none focus:border-blue-500/50 resize-y"
      />
    </div>
  );
}

function SelectField({
  label,
  value,
  onChange,
  options,
}: {
  label: string;
  value: string;
  onChange: (v: string) => void;
  options: { value: string; label: string }[];
}) {
  return (
    <div>
      <label className="block text-[10px] text-muted-foreground uppercase tracking-wide mb-1">
        {label}
      </label>
      <select
        value={value}
        onChange={(e) => onChange(e.target.value)}
        className="w-full bg-background border border-border rounded-md px-2 py-1.5 text-[12px] text-foreground outline-none focus:border-blue-500/50"
      >
        {options.map((o) => (
          <option key={o.value} value={o.value}>
            {o.label}
          </option>
        ))}
      </select>
    </div>
  );
}