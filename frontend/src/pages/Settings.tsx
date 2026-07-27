/**
 * Settings page.
 *
 * Reflects canonical backend data:
 *   - "Societate" tab: static company identity (kept from existing mock).
 *   - "Plăți Repetitive" tab: live data from /api/v1/entities/recurring-payments.
 *   - "CostEngine" tab: live data from /api/v1/cost-engine/config
 *                       + aggregated /api/v1/cost-engine/base-config.
 *
 * Rules:
 *  - No local cost/overhead math. Backend fields are displayed as-is.
 *  - UI only displays / edits / visually validates.
 */
import { useCallback, useEffect, useMemo, useState } from "react";
import { Link } from "react-router-dom";
import {
  companySettings,
  type CompanySettings,
} from "@/lib/mockData";
import {
  ReadinessPanel,
  chromeBanner,
  chromeForm,
  chromeTab,
  type ReadinessItem,
} from "@/components/workos/design-system";
import {
  Settings as SettingsIcon,
  Building2,
  CreditCard,
  Phone,
  Mail,
  Globe,
  MapPin,
  Landmark,
  FileText,
  CheckCircle2,
  XCircle,
  Calendar,
  DollarSign,
  ChevronRight,
  Receipt,
  Calculator,
  Plus,
  Pencil,
  Trash2,
  Save,
  X,
  RefreshCw,
  AlertTriangle,
  Loader2,
} from "lucide-react";
import {
  recurringPaymentsApi,
  costEngineApi,
  type RecurringPaymentDTO,
  type RecurringPaymentPayload,
  type CostEngineConfigDTO,
  type CostEngineConfigPayload,
  type CostEngineBaseConfigDTO,
} from "@/api/costEngine";
import {
  clearSmartBillToken,
  getSmartBillConfig,
  getSmartBillProviderHealth,
  IntegrationsHttpError,
  testSmartBillConfig,
  updateSmartBillConfig,
  type SmartBillConfigMasked,
  type SmartBillConfigTestResult,
  type SmartbillProviderHealthResponse,
} from "@/api/integrations";
import { buildSheetQualityInvalidSummaryUrl } from "@/utils/inventorySheetQualityLinks";
import {
  getCompanyCommercialSettings,
  updateCompanyCommercialSettings,
} from "@/api/companyCommercialSettings";
import { DEFAULT_VAT_PCT, DEFAULT_EUR_TO_RON_RATE } from "@/lib/companyCommercialSettings";

// ------------------------------------------------------------
// Shared helpers
// ------------------------------------------------------------
function fmtMoney(n: number | null | undefined, digits = 2): string {
  if (n === null || n === undefined || Number.isNaN(n)) return "—";
  return n.toLocaleString("ro-RO", {
    minimumFractionDigits: digits,
    maximumFractionDigits: digits,
  });
}

function fmtNumber(n: number | null | undefined): string {
  if (n === null || n === undefined || Number.isNaN(n)) return "—";
  return n.toLocaleString("ro-RO", { maximumFractionDigits: 2 });
}

function parseNumberOrNull(raw: string): number | null {
  if (!raw || !raw.trim()) return null;
  const n = Number(raw.replace(",", "."));
  return Number.isFinite(n) ? n : null;
}

// ============================================================
// Top-level Settings shell
// ============================================================
type TabKey = "company" | "payments" | "cost_engine" | "integrations";

export default function Settings() {
  const [activeTab, setActiveTab] = useState<TabKey>("company");
  const sheetQualityInvalidUrl = buildSheetQualityInvalidSummaryUrl();

  return (
    <div className="space-y-4">
      {/* Header */}
      <div className="flex items-center justify-between">
        <div className="flex items-center gap-2">
          <SettingsIcon className="w-5 h-5 text-muted-foreground" />
          <h1 className="text-[18px] font-bold text-foreground">Setări</h1>
        </div>
      </div>

      {/* Tabs */}
      <div className="flex items-center gap-1 bg-card border border-border rounded-lg p-1 w-fit flex-wrap">
        <TabButton
          active={activeTab === "company"}
          onClick={() => setActiveTab("company")}
          icon={<Building2 className="w-3.5 h-3.5" />}
          label="Societate"
        />
        <TabButton
          active={activeTab === "payments"}
          onClick={() => setActiveTab("payments")}
          icon={<Receipt className="w-3.5 h-3.5" />}
          label="Plăți Repetitive"
        />
        <TabButton
          active={activeTab === "cost_engine"}
          onClick={() => setActiveTab("cost_engine")}
          icon={<Calculator className="w-3.5 h-3.5" />}
          label="Cost Intern"
        />
        <TabButton
          active={activeTab === "integrations"}
          onClick={() => setActiveTab("integrations")}
          icon={<Globe className="w-3.5 h-3.5" />}
          label="Integrări"
        />
      </div>

      <div className={`flex items-center justify-between gap-2 rounded-lg px-3 py-2 ${chromeBanner.info}`}>
        <p className="text-[11px]">
          Pentru analize operaționale pe formate de sheet invalide, folosește Inventory Sheet Quality.
        </p>
        <Link
          to={sheetQualityInvalidUrl}
          className="whitespace-nowrap text-[11px] font-semibold underline underline-offset-2 text-blue-800 hover:text-blue-950 dark:text-blue-200 dark:hover:text-blue-100"
        >
          Open Sheet Quality
        </Link>
      </div>

      {activeTab === "company" && (
        <div className={`flex items-start gap-2 rounded-lg px-3 py-2 ${chromeBanner.warning}`}>
          <AlertTriangle className="mt-0.5 h-4 w-4 shrink-0 text-amber-700 dark:text-amber-300" />
          <p className="text-[11px]">
            Tabul "Societate" afișează profil local static. Nu este sincronizat cu o sursă live backend în acest build.
          </p>
        </div>
      )}

      {activeTab === "company" && (
        <div className="space-y-4">
          <CompanyCommercialVatPanel />
          <CompanyCommercialFxPanel />
          <CompanyTab settings={companySettings} />
        </div>
      )}
      {activeTab === "payments" && <RecurringPaymentsTab />}
      {activeTab === "cost_engine" && <CostEngineTab />}
      {activeTab === "integrations" && <IntegrationsTab />}
    </div>
  );
}

function TabButton({
  active,
  onClick,
  icon,
  label,
}: {
  active: boolean;
  onClick: () => void;
  icon: React.ReactNode;
  label: string;
}) {
  return (
    <button
      onClick={onClick}
      className={`rounded-md px-4 py-2 text-[12px] font-semibold transition-colors ${
        active ? chromeTab.active : chromeTab.inactive
      }`}
    >
      <span className="flex items-center gap-2">
        {icon}
        {label}
      </span>
    </button>
  );
}

// ============================================================
// COMPANY TAB (unchanged — static identity card)
// ============================================================
function InfoRow({
  label,
  value,
  icon,
}: {
  label: string;
  value: string;
  icon?: React.ReactNode;
}) {
  return (
    <div>
      <p className={`${chromeForm.label} mb-1 flex items-center gap-1`}>
        {icon}
        {label}
      </p>
      <p className="text-[13px] text-foreground">{value || "—"}</p>
    </div>
  );
}

function CompanyCommercialVatPanel() {
  const [vatPct, setVatPct] = useState(String(DEFAULT_VAT_PCT));
  const [loading, setLoading] = useState(true);
  const [saving, setSaving] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [success, setSuccess] = useState<string | null>(null);

  useEffect(() => {
    let alive = true;
    setLoading(true);
    getCompanyCommercialSettings()
      .then((data) => {
        if (!alive) return;
        setVatPct(String(data.default_vat_pct));
      })
      .catch((err: unknown) => {
        if (!alive) return;
        setError(err instanceof Error ? err.message : "Eroare la citire TVA");
      })
      .finally(() => {
        if (alive) setLoading(false);
      });
    return () => {
      alive = false;
    };
  }, []);

  async function handleSave() {
    setError(null);
    setSuccess(null);
    const parsed = Number(vatPct);
    if (!Number.isFinite(parsed) || parsed < 0 || parsed > 100) {
      setError("TVA trebuie să fie între 0 și 100.");
      return;
    }
    setSaving(true);
    try {
      const data = await updateCompanyCommercialSettings({ default_vat_pct: parsed });
      setVatPct(String(data.default_vat_pct));
      setSuccess("TVA implicit salvat. Ofertele noi vor folosi această valoare.");
    } catch (err: unknown) {
      setError(err instanceof Error ? err.message : "Eroare la salvare TVA");
    } finally {
      setSaving(false);
    }
  }

  return (
    <div className="bg-card border border-border rounded-lg p-5">
      <div className="flex items-center gap-2 mb-3">
        <Receipt className="w-4 h-4 text-emerald-600 dark:text-emerald-600 dark:text-emerald-400" />
        <span className="text-[14px] font-bold text-foreground">TVA implicit (registry intern)</span>
      </div>
      <p className="text-[11px] text-muted-foreground mb-4">
        Sursa TVA pentru oferte. Ofertele salvează snapshot-ul TVA la generare; documentele istorice
        nu se actualizează când schimbi această valoare.
      </p>
      <div className="flex flex-wrap items-end gap-3">
        <div>
          <label className={chromeForm.label}>
            TVA implicit pentru oferte (%)
          </label>
          <input
            type="number"
            min={0}
            max={100}
            step={0.5}
            disabled={loading || saving}
            value={vatPct}
            onChange={(e) => setVatPct(e.target.value)}
            className={`w-32 ${chromeForm.input}`}
            data-testid="settings-default-vat-pct"
          />
        </div>
        <button
          type="button"
          onClick={handleSave}
          disabled={loading || saving}
          className="inline-flex items-center gap-2 px-3 py-2 rounded bg-blue-600/80 hover:bg-blue-600 text-[12px] font-semibold text-white disabled:opacity-50"
        >
          {saving ? <Loader2 className="w-3.5 h-3.5 animate-spin" /> : <Save className="w-3.5 h-3.5" />}
          Salvează TVA
        </button>
      </div>
      {error && <p className="text-[11px] text-red-600 dark:text-red-400 mt-2">{error}</p>}
      {success && <p className="text-[11px] text-emerald-600 dark:text-emerald-400 mt-2">{success}</p>}
    </div>
  );
}

function CompanyCommercialFxPanel() {
  const [rate, setRate] = useState(String(DEFAULT_EUR_TO_RON_RATE));
  const [loading, setLoading] = useState(true);
  const [saving, setSaving] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [success, setSuccess] = useState<string | null>(null);

  useEffect(() => {
    let alive = true;
    setLoading(true);
    getCompanyCommercialSettings()
      .then((data) => {
        if (!alive) return;
        setRate(String(data.eur_to_ron_rate));
      })
      .catch((err: unknown) => {
        if (!alive) return;
        setError(err instanceof Error ? err.message : "Eroare la citire curs EUR/RON");
      })
      .finally(() => {
        if (alive) setLoading(false);
      });
    return () => {
      alive = false;
    };
  }, []);

  async function handleSave() {
    setError(null);
    setSuccess(null);
    const parsed = Number(rate);
    if (!Number.isFinite(parsed) || parsed <= 0) {
      setError("Cursul EUR/RON trebuie să fie numeric și mai mare decât 0.");
      return;
    }
    setSaving(true);
    try {
      const data = await updateCompanyCommercialSettings({ eur_to_ron_rate: parsed });
      setRate(String(data.eur_to_ron_rate));
      setSuccess("Curs EUR/RON salvat. Comenzile noi vor folosi această valoare.");
    } catch (err: unknown) {
      setError(err instanceof Error ? err.message : "Eroare la salvare curs EUR/RON");
    } finally {
      setSaving(false);
    }
  }

  return (
    <div className="bg-card border border-border rounded-lg p-5">
      <div className="flex items-center gap-2 mb-3">
        <Receipt className="w-4 h-4 text-cyan-600 dark:text-cyan-600 dark:text-cyan-400" />
        <span className="text-[14px] font-bold text-foreground">Curs EUR/RON</span>
      </div>
      <p className="text-[11px] text-muted-foreground mb-4">
        Curs EUR/RON folosit la conversia ofertelor în comenzi. Momentan se completează manual.
        Preluarea automată a cursului va fi tratată separat.
      </p>
      <div className="flex flex-wrap items-end gap-3">
        <div>
          <label className={chromeForm.label}>
            Curs EUR/RON (RON pentru 1 EUR)
          </label>
          <input
            type="number"
            min={0.0001}
            step={0.0001}
            disabled={loading || saving}
            value={rate}
            onChange={(e) => setRate(e.target.value)}
            className={`w-40 ${chromeForm.input}`}
            data-testid="settings-eur-to-ron-rate"
          />
        </div>
        <button
          type="button"
          onClick={handleSave}
          disabled={loading || saving}
          className="inline-flex items-center gap-2 px-3 py-2 rounded bg-blue-600/80 hover:bg-blue-600 text-[12px] font-semibold text-white disabled:opacity-50"
        >
          {saving ? <Loader2 className="w-3.5 h-3.5 animate-spin" /> : <Save className="w-3.5 h-3.5" />}
          Salvează curs
        </button>
      </div>
      {error && <p className="text-[11px] text-red-600 dark:text-red-400 mt-2">{error}</p>}
      {success && <p className="text-[11px] text-emerald-600 dark:text-emerald-400 mt-2">{success}</p>}
    </div>
  );
}

function CompanyTab({ settings }: { settings: CompanySettings }) {
  return (
    <div className="grid grid-cols-1 lg:grid-cols-2 gap-4">
      <div className="bg-card border border-border rounded-lg p-5">
        <div className="flex items-center gap-2 mb-4">
          <Building2 className="w-4 h-4 text-blue-600 dark:text-blue-600 dark:text-blue-400" />
          <span className="text-[14px] font-bold text-foreground">Date Societate</span>
        </div>
        <div className="space-y-4">
          <InfoRow label="Denumire" value={settings.name} icon={<Building2 className="w-3 h-3" />} />
          <div className="grid grid-cols-2 gap-4">
            <InfoRow label="CUI" value={settings.cui} icon={<FileText className="w-3 h-3" />} />
            <InfoRow label="Reg. Comerțului" value={settings.regCom} icon={<FileText className="w-3 h-3" />} />
          </div>
          <InfoRow label="Adresă" value={settings.address} icon={<MapPin className="w-3 h-3" />} />
          <div className="grid grid-cols-2 gap-4">
            <InfoRow label="Oraș" value={settings.city} />
            <InfoRow label="Cod Poștal" value={settings.postalCode} />
          </div>
          <div>
            <p className={`${chromeForm.label} mb-1`}>Plătitor TVA</p>
            <span
              className={`inline-flex items-center gap-1 text-[12px] font-semibold ${
                settings.vatPayer ? "text-emerald-600 dark:text-emerald-400" : "text-muted-foreground"
              }`}
            >
              {settings.vatPayer ? (
                <CheckCircle2 className="w-3.5 h-3.5" />
              ) : (
                <XCircle className="w-3.5 h-3.5" />
              )}
              {settings.vatPayer ? "Da" : "Nu"}
            </span>
          </div>
          <InfoRow label="Administrator" value={settings.adminContact} />
        </div>
      </div>

      <div className="space-y-4">
        <div className="bg-card border border-border rounded-lg p-5">
          <div className="flex items-center gap-2 mb-4">
            <Phone className="w-4 h-4 text-blue-600 dark:text-blue-600 dark:text-blue-400" />
            <span className="text-[14px] font-bold text-foreground">Contact</span>
          </div>
          <div className="space-y-4">
            <InfoRow label="Telefon" value={settings.phone} icon={<Phone className="w-3 h-3" />} />
            <InfoRow label="Email" value={settings.email} icon={<Mail className="w-3 h-3" />} />
            <InfoRow label="Website" value={settings.website} icon={<Globe className="w-3 h-3" />} />
          </div>
        </div>

        <div className="bg-card border border-border rounded-lg p-5">
          <div className="flex items-center gap-2 mb-4">
            <Landmark className="w-4 h-4 text-blue-600 dark:text-blue-600 dark:text-blue-400" />
            <span className="text-[14px] font-bold text-foreground">Date Bancare</span>
          </div>
          <div className="space-y-4">
            <InfoRow label="Bancă" value={settings.bankName} icon={<Landmark className="w-3 h-3" />} />
            <InfoRow label="IBAN" value={settings.iban} icon={<CreditCard className="w-3 h-3" />} />
          </div>
        </div>
      </div>
    </div>
  );
}

function IntegrationsTab() {
  const [config, setConfig] = useState<SmartBillConfigMasked | null>(null);
  const [health, setHealth] = useState<SmartbillProviderHealthResponse | null>(null);
  const [testResult, setTestResult] = useState<SmartBillConfigTestResult | null>(null);

  const [enabled, setEnabled] = useState(false);
  const [baseUrl, setBaseUrl] = useState("");
  const [username, setUsername] = useState("");
  const [token, setToken] = useState("");
  const [lookupPath, setLookupPath] = useState("/fiscal-lookup");
  const [timeoutSeconds, setTimeoutSeconds] = useState("5");

  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [saving, setSaving] = useState(false);
  const [testing, setTesting] = useState(false);

  const hydrateFormFromConfig = useCallback((data: SmartBillConfigMasked) => {
    setConfig(data);
    setEnabled(data.enabled);
    setBaseUrl(data.base_url || "");
    setLookupPath(data.lookup_path || "/fiscal-lookup");
    setTimeoutSeconds(String(data.timeout_seconds || 5));
    setUsername("");
    setToken("");
  }, []);

  const loadHealth = useCallback(async () => {
    const data = await getSmartBillProviderHealth();
    setHealth(data);
  }, []);

  const loadAll = useCallback(async () => {
    setLoading(true);
    setError(null);
    try {
      const [cfg, h] = await Promise.all([getSmartBillConfig(), getSmartBillProviderHealth()]);
      hydrateFormFromConfig(cfg);
      setHealth(h);
    } catch (err) {
      setConfig(null);
      setHealth(null);
      if (err instanceof IntegrationsHttpError) {
        setError(err.message);
      } else {
        setError(err instanceof Error ? err.message : "Provider diagnostic unavailable");
      }
    } finally {
      setLoading(false);
    }
  }, [hydrateFormFromConfig]);

  useEffect(() => {
    void loadAll();
  }, [loadAll]);

  const handleSaveConfig = useCallback(async () => {
    setSaving(true);
    setError(null);
    try {
      const payload = {
        enabled,
        base_url: baseUrl.trim() ? baseUrl.trim() : null,
        username: username.trim() ? username.trim() : null,
        token: token.trim() ? token.trim() : null,
        lookup_path: lookupPath.trim() || "/fiscal-lookup",
        timeout_seconds: Number(timeoutSeconds),
      };

      const updated = await updateSmartBillConfig(payload);
      hydrateFormFromConfig(updated);
      await loadHealth();

      // Security rule: never keep token in frontend state after save.
      setToken("");
      setTestResult(null);
    } catch (err) {
      if (err instanceof IntegrationsHttpError) {
        setError(err.message);
      } else {
        setError(err instanceof Error ? err.message : "Save failed");
      }
    } finally {
      setSaving(false);
    }
  }, [enabled, baseUrl, username, token, lookupPath, timeoutSeconds, hydrateFormFromConfig, loadHealth]);

  const handleTestConfig = useCallback(async () => {
    setTesting(true);
    setError(null);
    try {
      const result = await testSmartBillConfig();
      setTestResult(result);
      const cfg = await getSmartBillConfig();
      hydrateFormFromConfig(cfg);
      await loadHealth();
    } catch (err) {
      if (err instanceof IntegrationsHttpError) {
        setError(err.message);
      } else {
        setError(err instanceof Error ? err.message : "Test failed");
      }
    } finally {
      setTesting(false);
    }
  }, [hydrateFormFromConfig, loadHealth]);

  const handleClearToken = useCallback(async () => {
    setSaving(true);
    setError(null);
    try {
      const updated = await clearSmartBillToken();
      hydrateFormFromConfig(updated);
      await loadHealth();
      setToken("");
      setTestResult(null);
    } catch (err) {
      if (err instanceof IntegrationsHttpError) {
        setError(err.message);
      } else {
        setError(err instanceof Error ? err.message : "Token clear failed");
      }
    } finally {
      setSaving(false);
    }
  }, [hydrateFormFromConfig, loadHealth]);

  const statusTone: Record<SmartbillProviderHealthResponse["status"], string> = {
    disabled: "text-muted-foreground border-slate-600 bg-muted/60",
    not_configured: "text-amber-700 dark:text-amber-300 border-amber-300 dark:border-amber-700 bg-amber-50 dark:bg-amber-900/20",
    configured: "text-emerald-700 dark:text-emerald-300 border-emerald-300 dark:border-emerald-700 bg-emerald-50 dark:bg-emerald-900/20",
    invalid_config: "text-red-700 dark:text-red-300 border-red-300 dark:border-red-700 bg-red-50 dark:bg-red-900/20",
  };

  // Build readiness items from health state
  const readinessItems: ReadinessItem[] = useMemo(() => {
    const items: ReadinessItem[] = [
      {
        id: "smartbill-provider",
        label: "SmartBill Provider",
        status: !health
          ? "pending"
          : health.status === "configured"
            ? "pass"
            : health.status === "invalid_config"
              ? "fail"
              : health.status === "not_configured"
                ? "warning"
                : "pending",
        detail: health ? `Status: ${health.status}` : "Se verifică...",
      },
      {
        id: "smartbill-enabled",
        label: "SmartBill Activat",
        status: config?.enabled ? "pass" : "warning",
        detail: config?.enabled ? "Provider activ" : "Provider dezactivat",
      },
      {
        id: "smartbill-credentials",
        label: "Credențiale configurate",
        status: !config
          ? "pending"
          : config.username_present && config.token_present
            ? "pass"
            : !config.username_present && !config.token_present
              ? "fail"
              : "warning",
        detail: config
          ? `Username: ${config.username_present ? "✓" : "✗"}, Token: ${config.token_present ? "✓" : "✗"}`
          : "Se verifică...",
      },
    ];
    return items;
  }, [health, config]);

  return (
    <div className="space-y-4">
      <div className="flex items-center justify-between">
        <div>
          <h2 className="text-[14px] font-bold text-foreground">Provider Diagnostics</h2>
          <p className="text-[11px] text-muted-foreground">
            Configuratie administrabila din UI, cu secrete protejate in backend.
          </p>
        </div>
        <div className="flex items-center gap-2">
          <button
            onClick={() => void loadAll()}
            className="inline-flex items-center gap-2 px-3 py-2 text-[12px] font-semibold rounded-lg border border-wo-border-strong bg-card text-muted-foreground hover:text-foreground"
          >
            <RefreshCw className="w-3.5 h-3.5" />
            Refresh
          </button>
        </div>
      </div>

      {/* System Readiness Panel */}
      <ReadinessPanel
        title="Stare Integrări"
        subtitle="Verificare automată a conexiunilor externe"
        items={readinessItems}
        icon={<Globe className="w-4 h-4" />}
      />

      {loading && (
        <div className="bg-card border border-border rounded-lg p-4 text-[12px] text-muted-foreground">
          Se încarcă diagnosticul SmartBill...
        </div>
      )}

      {error && !loading && (
        <div className="flex items-start gap-2 px-3 py-3 bg-red-100 border border-red-200 dark:bg-red-900/20 dark:border-red-800/40 rounded-lg">
          <XCircle className="w-4 h-4 text-red-600 dark:text-red-400 mt-0.5 shrink-0" />
          <p className="text-[12px] text-red-700 dark:text-red-300">Provider diagnostic unavailable: {error}</p>
        </div>
      )}

      {config && !loading && (
        <div className="bg-card border border-border rounded-lg p-5 space-y-4">
          <div className="flex items-center justify-between gap-3 flex-wrap">
            <div className="flex items-center gap-2">
              <Globe className="w-4 h-4 text-blue-600 dark:text-blue-600 dark:text-blue-400" />
              <span className="text-[14px] font-bold text-foreground">SmartBill Config</span>
            </div>
            <span className="px-2.5 py-1 rounded-lg border text-[11px] font-semibold text-muted-foreground border-slate-600 bg-muted/60">
              source: {config.source}
            </span>
          </div>

          <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
            <label className="bg-wo-surface-inset border border-wo-border-strong rounded-lg p-3 block">
              <p className="text-[10px] font-semibold uppercase tracking-wide text-wo-text-secondary mb-2">Enabled</p>
              <input type="checkbox" checked={enabled} onChange={(e) => setEnabled(e.target.checked)} />
            </label>

            <label className="bg-wo-surface-inset border border-wo-border-strong rounded-lg p-3 block">
              <p className="text-[10px] font-semibold uppercase tracking-wide text-wo-text-secondary mb-2">Base URL</p>
              <input
                value={baseUrl}
                onChange={(e) => setBaseUrl(e.target.value)}
                className="w-full rounded-md bg-card border border-wo-border-strong px-2 py-2 text-[12px] text-foreground"
                placeholder="https://api.smartbill.ro"
              />
            </label>

            <label className="bg-wo-surface-inset border border-wo-border-strong rounded-lg p-3 block">
              <p className="text-[10px] font-semibold uppercase tracking-wide text-wo-text-secondary mb-2">Username</p>
              <input
                value={username}
                onChange={(e) => setUsername(e.target.value)}
                className="w-full rounded-md bg-card border border-wo-border-strong px-2 py-2 text-[12px] text-foreground"
                placeholder={config.username_present ? `Current: ${config.username_hint || "configured"}` : "billing@example.com"}
              />
            </label>

            <label className="bg-wo-surface-inset border border-wo-border-strong rounded-lg p-3 block">
              <p className="text-[10px] font-semibold uppercase tracking-wide text-wo-text-secondary mb-2">Token (write-only)</p>
              <input
                type="password"
                value={token}
                onChange={(e) => setToken(e.target.value)}
                className="w-full rounded-md bg-card border border-wo-border-strong px-2 py-2 text-[12px] text-foreground"
                placeholder={config.token_present ? "Token already configured" : "Paste new token"}
                autoComplete="new-password"
              />
            </label>

            <label className="bg-wo-surface-inset border border-wo-border-strong rounded-lg p-3 block">
              <p className="text-[10px] font-semibold uppercase tracking-wide text-wo-text-secondary mb-2">Lookup path</p>
              <input
                value={lookupPath}
                onChange={(e) => setLookupPath(e.target.value)}
                className="w-full rounded-md bg-card border border-wo-border-strong px-2 py-2 text-[12px] text-foreground"
                placeholder="/fiscal-lookup"
              />
            </label>

            <label className="bg-wo-surface-inset border border-wo-border-strong rounded-lg p-3 block">
              <p className="text-[10px] font-semibold uppercase tracking-wide text-wo-text-secondary mb-2">Timeout seconds</p>
              <input
                value={timeoutSeconds}
                onChange={(e) => setTimeoutSeconds(e.target.value)}
                className="w-full rounded-md bg-card border border-wo-border-strong px-2 py-2 text-[12px] text-foreground"
                placeholder="5"
                inputMode="numeric"
              />
            </label>
          </div>

          <div className="flex flex-wrap gap-2">
            <button
              disabled={saving}
              onClick={() => void handleSaveConfig()}
              className="inline-flex items-center gap-2 px-3 py-2 text-[12px] font-semibold rounded-lg border border-emerald-700 bg-emerald-50 dark:bg-emerald-900/20 text-emerald-700 dark:text-emerald-300 disabled:opacity-60"
            >
              <Save className="w-3.5 h-3.5" />
              {saving ? "Saving..." : "Save config"}
            </button>

            <button
              disabled={testing}
              onClick={() => void handleTestConfig()}
              className="inline-flex items-center gap-2 px-3 py-2 text-[12px] font-semibold rounded-lg border border-blue-700 bg-blue-50 dark:bg-blue-900/20 text-blue-700 dark:text-blue-300 disabled:opacity-60"
            >
              <RefreshCw className="w-3.5 h-3.5" />
              {testing ? "Testing..." : "Test connection (local)"}
            </button>

            <button
              disabled={saving || !config.token_present}
              onClick={() => void handleClearToken()}
              className="inline-flex items-center gap-2 px-3 py-2 text-[12px] font-semibold rounded-lg border border-red-300 dark:border-red-700 bg-red-50 dark:bg-red-900/20 text-red-700 dark:text-red-300 disabled:opacity-60"
            >
              <Trash2 className="w-3.5 h-3.5" />
              Clear token
            </button>
          </div>

          <div className="bg-wo-surface-inset border border-wo-border-strong rounded-lg p-4 text-[12px] text-muted-foreground space-y-1">
            <p>token_present: {String(config.token_present)}</p>
            <p>username_present: {String(config.username_present)}</p>
            <p>username_hint: {config.username_hint || "—"}</p>
            <p>last_test_status: {config.last_test_status || "not_run"}</p>
            <p>last_test_at: {config.last_test_at || "—"}</p>
            <p>last_test_message: {config.last_test_message || "—"}</p>
            <p>
              Provider live validated at: {config.last_test_status === "success" ? config.last_test_at || "unknown" : "not verified"}
            </p>
          </div>

          <div className="bg-amber-100 border border-amber-200 dark:bg-amber-900/15 dark:border-amber-800/30 rounded-lg p-3 text-[12px] text-amber-700 dark:text-amber-300">
            Configuratia completa nu garanteaza ca providerul raspunde corect. Verificarea reala se face prin lookup controlat / UAT.
          </div>

          {testResult && (
            <div className="bg-wo-surface-inset border border-wo-border-strong rounded-lg p-4 text-[12px] text-muted-foreground space-y-1">
              <p>test.status: {testResult.status}</p>
              <p>test.ok: {String(testResult.ok)}</p>
              <p>test.mode: {testResult.mode}</p>
              <p>test.source: {testResult.source}</p>
              <p>test.message: {testResult.message}</p>
              {testResult.warnings.length > 0 && (
                <ul className="list-disc list-inside text-amber-700 dark:text-amber-300">
                  {testResult.warnings.map((w) => (
                    <li key={w}>{w}</li>
                  ))}
                </ul>
              )}
            </div>
          )}
        </div>
      )}

      {health && !loading && (
        <div className="bg-card border border-border rounded-lg p-5 space-y-4">
          <div className="flex items-center justify-between gap-3 flex-wrap">
            <div className="flex items-center gap-2">
              <Globe className="w-4 h-4 text-blue-600 dark:text-blue-600 dark:text-blue-400" />
              <span className="text-[14px] font-bold text-foreground">SmartBill Health</span>
            </div>
            <span className={`px-2.5 py-1 rounded-lg border text-[11px] font-semibold ${statusTone[health.status]}`}>
              {health.status}
            </span>
          </div>

          <p className="text-[12px] text-muted-foreground">source: {health.source}</p>

          <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
            <div className="bg-wo-surface-inset border border-wo-border-strong rounded-lg p-4 space-y-3">
              <div className="grid grid-cols-2 gap-3">
                <InfoRow label="Enabled" value={health.enabled ? "true" : "false"} />
                <InfoRow label="Configured" value={health.configured ? "true" : "false"} />
              </div>
              <InfoRow label="Base URL host" value={health.masked.base_url_host || "—"} />
              <InfoRow label="Username hint" value={health.masked.username_hint || "—"} />
              <InfoRow label="Lookup path" value={health.settings.lookup_path} />
              <InfoRow label="Timeout seconds" value={health.settings.timeout_seconds === null ? "—" : String(health.settings.timeout_seconds)} />
            </div>

            <div className="bg-wo-surface-inset border border-wo-border-strong rounded-lg p-4 space-y-3">
              <p className="text-[10px] text-muted-foreground uppercase tracking-wide">Present fields</p>
              <ul className="space-y-1 text-[12px] text-muted-foreground">
                <li>base_url: {String(health.present_fields.base_url)}</li>
                <li>username: {String(health.present_fields.username)}</li>
                <li>token: {String(health.present_fields.token)}</li>
                <li>lookup_path: {String(health.present_fields.lookup_path)}</li>
                <li>timeout_seconds: {String(health.present_fields.timeout_seconds)}</li>
              </ul>
            </div>
          </div>

          <div className="bg-wo-surface-inset border border-wo-border-strong rounded-lg p-4">
            <p className="text-[10px] font-semibold uppercase tracking-wide text-wo-text-secondary mb-2">Missing fields</p>
            {health.missing_fields.length > 0 ? (
              <div className="flex flex-wrap gap-2">
                {health.missing_fields.map((field) => (
                  <span key={field} className="px-2 py-1 text-[11px] rounded border border-amber-200 bg-amber-100 text-amber-700 dark:border-amber-700 dark:bg-amber-900/20 dark:text-amber-300">
                    {field}
                  </span>
                ))}
              </div>
            ) : (
              <p className="text-[12px] text-muted-foreground">Niciun câmp obligatoriu lipsă.</p>
            )}
          </div>

          <div className="bg-wo-surface-inset border border-wo-border-strong rounded-lg p-4">
            <p className="text-[10px] font-semibold uppercase tracking-wide text-wo-text-secondary mb-2">Live validation</p>
            <p className="text-[12px] text-muted-foreground">{health.live_validation.message}</p>
          </div>

          {health.warnings.length > 0 && (
            <div className={`flex items-start gap-2 px-3 py-3 rounded-lg ${chromeBanner.warning}`}>
              <AlertTriangle className="w-4 h-4 mt-0.5 shrink-0" />
              <div className="text-[12px] space-y-1">
                {health.warnings.map((warning) => (
                  <p key={warning}>{warning}</p>
                ))}
              </div>
            </div>
          )}
        </div>
      )}
    </div>
  );
}

// ============================================================
// RECURRING PAYMENTS TAB — backed by backend
// ============================================================
const PAYMENT_CATEGORIES: { value: string; label: string; cls: string }[] = [
  { value: "chirie", label: "Chirie", cls: "bg-purple-50 dark:bg-purple-900/40 text-purple-700 dark:text-purple-300 border-purple-200 dark:border-purple-700" },
  { value: "utilitati", label: "Utilități", cls: "bg-amber-50 dark:bg-amber-900/40 text-amber-700 dark:text-amber-300 border-amber-200 dark:border-amber-700" },
  { value: "leasing", label: "Leasing", cls: "bg-blue-50 dark:bg-blue-900/40 text-blue-700 dark:text-blue-300 border-blue-200 dark:border-blue-700" },
  { value: "asigurare", label: "Asigurare", cls: "bg-emerald-50 dark:bg-emerald-900/40 text-emerald-700 dark:text-emerald-300 border-emerald-200 dark:border-emerald-700" },
  { value: "abonament", label: "Abonament", cls: "bg-cyan-50 dark:bg-cyan-900/40 text-cyan-700 dark:text-cyan-300 border-cyan-200 dark:border-cyan-700" },
  { value: "servicii", label: "Servicii", cls: "bg-teal-50 dark:bg-teal-900/40 text-teal-700 dark:text-teal-300 border-teal-200 dark:border-teal-700" },
  { value: "alte_costuri", label: "Alte costuri", cls: "bg-wo-surface-inset text-muted-foreground border-wo-border-strong" },
];

const PAYMENT_PERIODICITY: { value: string; label: string }[] = [
  { value: "lunar", label: "Lunar" },
  { value: "trimestrial", label: "Trimestrial" },
  { value: "anual", label: "Anual" },
  { value: "ocazional", label: "Ocazional" },
];

const PAYMENT_STATUS: { value: string; label: string }[] = [
  { value: "active", label: "Activ" },
  { value: "paused", label: "Suspendat" },
  { value: "cancelled", label: "Anulat" },
];

const CURRENCIES = ["RON", "EUR", "USD"];

function categoryConfig(v: string) {
  return (
    PAYMENT_CATEGORIES.find((c) => c.value === v) ?? {
      value: v,
      label: v,
      cls: "bg-wo-surface-inset text-muted-foreground border-wo-border-strong",
    }
  );
}

function periodicityLabel(v: string): string {
  return PAYMENT_PERIODICITY.find((p) => p.value === v)?.label ?? v;
}

function statusLabel(v: string): string {
  return PAYMENT_STATUS.find((p) => p.value === v)?.label ?? v;
}

interface PaymentForm {
  name: string;
  category: string;
  amount: string;
  currency: string;
  periodicity: string;
  supplier: string;
  due_day: string;
  status: string;
  include_in_overhead: boolean;
  include_in_machine_cost: boolean;
  linked_machine_id: string;
  observatii: string;
}

const EMPTY_PAYMENT_FORM: PaymentForm = {
  name: "",
  category: "alte_costuri",
  amount: "",
  currency: "RON",
  periodicity: "lunar",
  supplier: "",
  due_day: "",
  status: "active",
  include_in_overhead: false,
  include_in_machine_cost: false,
  linked_machine_id: "",
  observatii: "",
};

function paymentToForm(p: RecurringPaymentDTO): PaymentForm {
  return {
    name: p.name ?? "",
    category: p.category ?? "alte_costuri",
    amount: p.amount === null || p.amount === undefined ? "" : String(p.amount),
    currency: p.currency ?? "RON",
    periodicity: p.periodicity ?? "lunar",
    supplier: p.supplier ?? "",
    due_day: p.due_day === null || p.due_day === undefined ? "" : String(p.due_day),
    status: p.status ?? "active",
    include_in_overhead: !!p.include_in_overhead,
    include_in_machine_cost: !!p.include_in_machine_cost,
    linked_machine_id: p.linked_machine_id ?? "",
    observatii: p.observatii ?? "",
  };
}

function validatePayment(f: PaymentForm): Record<string, string> {
  const errs: Record<string, string> = {};
  if (!f.name.trim()) errs.name = "Numele este obligatoriu.";
  const amount = parseNumberOrNull(f.amount);
  if (amount === null || amount <= 0)
    errs.amount = "Valoarea este obligatorie și trebuie > 0.";
  if (!f.currency.trim()) errs.currency = "Moneda este obligatorie.";
  if (!f.periodicity.trim()) errs.periodicity = "Periodicitatea este obligatorie.";
  const dueDay = parseNumberOrNull(f.due_day);
  if (dueDay !== null && (dueDay < 1 || dueDay > 31))
    errs.due_day = "Ziua scadentă trebuie să fie între 1 și 31.";
  if (f.include_in_machine_cost && !f.linked_machine_id.trim())
    errs.linked_machine_id =
      "Pentru alocare la cost utilaj, trebuie selectat un utilaj.";
  return errs;
}

function paymentFormToPayload(f: PaymentForm): RecurringPaymentPayload {
  return {
    name: f.name.trim(),
    category: f.category || "alte_costuri",
    amount: parseNumberOrNull(f.amount),
    currency: f.currency || "RON",
    periodicity: f.periodicity || "lunar",
    supplier: f.supplier.trim() || null,
    due_day:
      parseNumberOrNull(f.due_day) === null
        ? null
        : Math.round(parseNumberOrNull(f.due_day) as number),
    status: f.status || "active",
    include_in_overhead: !!f.include_in_overhead,
    include_in_machine_cost: !!f.include_in_machine_cost,
    linked_machine_id: f.linked_machine_id.trim() || null,
    observatii: f.observatii.trim() || null,
  };
}

function CategoryBadge({ category }: { category: string }) {
  const cfg = categoryConfig(category);
  return (
    <span
      className={`inline-flex items-center px-2 py-0.5 text-[10px] font-semibold rounded border ${cfg.cls}`}
    >
      {cfg.label}
    </span>
  );
}

function RecurringPaymentsTab() {
  const [items, setItems] = useState<RecurringPaymentDTO[]>([]);
  const [loading, setLoading] = useState(true);
  const [loadError, setLoadError] = useState<string | null>(null);

  const [categoryFilter, setCategoryFilter] = useState<string>("all");
  const [selectedId, setSelectedId] = useState<number | null>(null);
  const [mode, setMode] = useState<"view" | "edit" | "create">("view");
  const [form, setForm] = useState<PaymentForm>(EMPTY_PAYMENT_FORM);
  const [errors, setErrors] = useState<Record<string, string>>({});
  const [saving, setSaving] = useState(false);
  const [saveError, setSaveError] = useState<string | null>(null);
  const [deleting, setDeleting] = useState(false);

  const load = useCallback(async () => {
    setLoading(true);
    setLoadError(null);
    try {
      const res = await recurringPaymentsApi.list({ limit: 500, sort: "name" });
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

  const filtered = useMemo(() => {
    if (categoryFilter === "all") return items;
    return items.filter((p) => p.category === categoryFilter);
  }, [items, categoryFilter]);

  const selected = useMemo(
    () => items.find((p) => p.id === selectedId) ?? null,
    [items, selectedId]
  );

  // Totals purely from backend-provided `monthly_equivalent`.
  const totals = useMemo(() => {
    const active = items.filter((p) => p.status === "active");
    const monthlyByCcy: Record<string, number> = {};
    for (const p of active) {
      const key = p.currency ?? "RON";
      const eq = p.monthly_equivalent ?? 0;
      monthlyByCcy[key] = (monthlyByCcy[key] ?? 0) + eq;
    }
    return {
      total: items.length,
      active: active.length,
      overhead: items.filter((p) => p.include_in_overhead).length,
      machine: items.filter((p) => p.include_in_machine_cost).length,
      monthlyByCcy,
    };
  }, [items]);

  const startCreate = () => {
    setSelectedId(null);
    setMode("create");
    setForm(EMPTY_PAYMENT_FORM);
    setErrors({});
    setSaveError(null);
  };

  const startEdit = (p: RecurringPaymentDTO) => {
    setSelectedId(p.id);
    setMode("edit");
    setForm(paymentToForm(p));
    setErrors({});
    setSaveError(null);
  };

  const cancelForm = () => {
    setMode("view");
    setErrors({});
    setSaveError(null);
    if (selected) setForm(paymentToForm(selected));
    else setForm(EMPTY_PAYMENT_FORM);
  };

  const updateField = <K extends keyof PaymentForm>(
    key: K,
    value: PaymentForm[K]
  ) => {
    setForm((prev) => {
      const next = { ...prev, [key]: value } as PaymentForm;
      setErrors(validatePayment(next));
      return next;
    });
  };

  const submit = async () => {
    const errs = validatePayment(form);
    setErrors(errs);
    if (Object.keys(errs).length > 0) return;
    setSaving(true);
    setSaveError(null);
    try {
      const payload = paymentFormToPayload(form);
      if (mode === "create") {
        const created = await recurringPaymentsApi.create(payload);
        await load();
        setSelectedId(created.id);
        setMode("view");
      } else if (mode === "edit" && selectedId !== null) {
        const updated = await recurringPaymentsApi.update(selectedId, payload);
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
    if (!window.confirm("Sigur vrei să ștergi această plată?")) return;
    setDeleting(true);
    try {
      await recurringPaymentsApi.remove(selectedId);
      setSelectedId(null);
      setMode("view");
      await load();
    } catch (err) {
      setSaveError(err instanceof Error ? err.message : "Eroare la ștergere");
    } finally {
      setDeleting(false);
    }
  };

  return (
    <div className="space-y-4">
      {/* KPIs */}
      <div className="grid grid-cols-2 md:grid-cols-4 gap-3">
        <div className="bg-wo-surface-raised border border-wo-border-strong rounded-lg p-3">
          <p className="text-[10px] text-muted-foreground uppercase tracking-wide mb-1">Total lunar (RON)</p>
          <p className="text-[22px] font-bold text-foreground">
            {fmtMoney(totals.monthlyByCcy.RON ?? 0, 0)}
          </p>
          <p className="text-[10px] text-muted-foreground">
            calculat de backend (monthly_equivalent)
          </p>
        </div>
        <div className="bg-wo-surface-raised border border-wo-border-strong rounded-lg p-3">
          <p className="text-[10px] text-muted-foreground uppercase tracking-wide mb-1">Alte valute (lunar)</p>
          <p className="text-[13px] text-foreground font-mono break-all">
            {Object.entries(totals.monthlyByCcy)
              .filter(([k]) => k !== "RON")
              .map(([k, v]) => `${fmtMoney(v, 0)} ${k}`)
              .join(" · ") || "—"}
          </p>
          <p className="text-[10px] text-muted-foreground">fără conversie valutară</p>
        </div>
        <div className="bg-wo-surface-raised border border-wo-border-strong rounded-lg p-3">
          <p className="text-[10px] text-muted-foreground uppercase tracking-wide mb-1">Plăți active</p>
          <p className="text-[22px] font-bold text-foreground">
            {totals.active}
            <span className="text-[12px] text-muted-foreground"> / {totals.total}</span>
          </p>
          <p className="text-[10px] text-muted-foreground">status = activ</p>
        </div>
        <div className="bg-wo-surface-raised border border-wo-border-strong rounded-lg p-3">
          <p className="text-[10px] text-muted-foreground uppercase tracking-wide mb-1">În overhead / utilaj</p>
          <p className="text-[22px] font-bold text-foreground">
            {totals.overhead}
            <span className="text-[12px] text-muted-foreground"> · {totals.machine}</span>
          </p>
          <p className="text-[10px] text-muted-foreground">alocate în calcul cost intern</p>
        </div>
      </div>

      {/* Filter + actions */}
      <div className="flex items-center gap-2 flex-wrap">
        <button
          onClick={() => setCategoryFilter("all")}
          className={`px-3 py-1.5 rounded-lg text-[11px] font-semibold border transition-colors ${
            categoryFilter === "all"
              ? "bg-blue-600/20 text-blue-600 dark:text-blue-400 border-blue-500/50"
              : "bg-card text-muted-foreground border-border hover:border-wo-border-strong"
          }`}
        >
          Toate ({items.length})
        </button>
        {PAYMENT_CATEGORIES.map((cat) => {
          const count = items.filter((p) => p.category === cat.value).length;
          if (count === 0) return null;
          return (
            <button
              key={cat.value}
              onClick={() =>
                setCategoryFilter(categoryFilter === cat.value ? "all" : cat.value)
              }
              className={`px-3 py-1.5 rounded-lg text-[11px] font-semibold border transition-colors ${
                categoryFilter === cat.value
                  ? "bg-blue-600/20 text-blue-600 dark:text-blue-400 border-blue-500/50"
                  : "bg-card text-muted-foreground border-border hover:border-wo-border-strong"
              }`}
            >
              {cat.label} ({count})
            </button>
          );
        })}
        <div className="ml-auto flex items-center gap-2">
          <button
            onClick={() => void load()}
            className="inline-flex items-center gap-1.5 px-3 py-1.5 text-[12px] text-muted-foreground bg-wo-surface-raised border border-wo-border-strong rounded-md hover:border-wo-border-strong"
          >
            <RefreshCw className="w-3.5 h-3.5" />
            Reîncarcă
          </button>
          <button
            onClick={startCreate}
            className="inline-flex items-center gap-1.5 px-3 py-1.5 text-[12px] font-semibold text-white bg-blue-600 rounded-md hover:bg-blue-500"
          >
            <Plus className="w-3.5 h-3.5" />
            Adaugă plată
          </button>
        </div>
      </div>

      {loadError && (
        <div className="bg-red-100 border border-red-200 dark:bg-red-900/30 dark:border-red-700/50 text-red-700 dark:text-red-300 text-[12px] rounded-md px-3 py-2">
          {loadError}
        </div>
      )}

      <div className="grid grid-cols-1 lg:grid-cols-3 gap-4">
        {/* List */}
        <div className="lg:col-span-2 space-y-2">
          {loading && (
            <div className="bg-card border border-border rounded-lg p-8 text-center text-muted-foreground text-[13px]">
              Se încarcă...
            </div>
          )}
          {!loading && filtered.length === 0 && (
            <div className="bg-card border border-border rounded-lg p-8 text-center text-muted-foreground text-[13px]">
              Nicio plată înregistrată.
            </div>
          )}
          {!loading &&
            filtered.map((p) => {
              const active = selectedId === p.id;
              return (
                <div
                  key={p.id}
                  onClick={() => {
                    setSelectedId(p.id);
                    setMode("view");
                  }}
                  className={`bg-card border rounded-lg p-3 cursor-pointer transition-all ${
                    active
                      ? "border-blue-500/50 ring-1 ring-blue-500/30"
                      : "border-border hover:border-wo-border-strong"
                  }`}
                >
                  <div className="flex items-center gap-3">
                    <div className="flex-1 min-w-0">
                      <div className="flex items-center gap-2 mb-0.5 flex-wrap">
                        <span className="text-[13px] font-semibold text-foreground">
                          {p.name}
                        </span>
                        <CategoryBadge category={p.category} />
                        {p.status !== "active" && (
                          <span className="text-[10px] text-muted-foreground bg-muted px-1.5 py-0.5 rounded">
                            {statusLabel(p.status)}
                          </span>
                        )}
                        {p.include_in_overhead && (
                          <span className="text-[10px] text-blue-600 dark:text-blue-300 bg-blue-900/30 border border-blue-700/50 px-1.5 py-0.5 rounded">
                            overhead
                          </span>
                        )}
                        {p.include_in_machine_cost && (
                          <span className="text-[10px] text-amber-700 dark:text-amber-300 bg-amber-50 dark:bg-amber-900/30 border border-amber-700/50 px-1.5 py-0.5 rounded">
                            utilaj
                          </span>
                        )}
                      </div>
                      <div className="flex items-center gap-3 text-[10px] text-muted-foreground flex-wrap">
                        <span className="font-bold text-muted-foreground">
                          {fmtMoney(p.amount)} {p.currency}
                        </span>
                        <span>•</span>
                        <span>{periodicityLabel(p.periodicity)}</span>
                        {p.due_day && (
                          <>
                            <span>•</span>
                            <span>Scadent: ziua {p.due_day}</span>
                          </>
                        )}
                        {p.supplier && (
                          <>
                            <span>•</span>
                            <span>{p.supplier}</span>
                          </>
                        )}
                        <span>•</span>
                        <span className="font-mono">
                          ~{fmtMoney(p.monthly_equivalent)} {p.currency}/lună
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
            <PaymentDetail
              payment={selected}
              onEdit={() => startEdit(selected)}
              onDelete={remove}
              deleting={deleting}
            />
          )}
          {mode === "view" && !selected && (
            <div className="bg-card border border-border rounded-lg p-8 text-center">
              <DollarSign className="w-8 h-8 text-wo-text-dim mx-auto mb-2" />
              <p className="text-[13px] text-muted-foreground">
                Selectează o plată pentru detalii sau adaugă una nouă.
              </p>
            </div>
          )}
          {(mode === "edit" || mode === "create") && (
            <PaymentForm
              form={form}
              mode={mode}
              errors={errors}
              saving={saving}
              saveError={saveError}
              onChange={updateField}
              onCancel={cancelForm}
              onSubmit={submit}
            />
          )}
        </div>
      </div>
    </div>
  );
}

function PaymentDetail({
  payment: p,
  onEdit,
  onDelete,
  deleting,
}: {
  payment: RecurringPaymentDTO;
  onEdit: () => void;
  onDelete: () => void;
  deleting: boolean;
}) {
  return (
    <div className="bg-card border border-border rounded-lg p-4 space-y-3">
      <div className="flex items-start gap-2">
        <div className="flex-1 min-w-0">
          <div className="flex items-center gap-2 mb-1 flex-wrap">
            <CategoryBadge category={p.category} />
            <span
              className={`text-[11px] font-medium ${
                p.status === "active" ? "text-emerald-600 dark:text-emerald-400" : "text-muted-foreground"
              }`}
            >
              {p.status === "active" ? "● Activ" : `○ ${statusLabel(p.status)}`}
            </span>
          </div>
          <h3 className="text-[16px] font-bold text-foreground">{p.name}</h3>
        </div>
        <div className="flex items-center gap-1 shrink-0">
          <button
            onClick={onEdit}
            className="p-1.5 text-muted-foreground hover:text-foreground bg-wo-surface-raised border border-wo-border-strong rounded-md hover:border-wo-border-strong"
            title="Editează"
          >
            <Pencil className="w-3.5 h-3.5" />
          </button>
          <button
            onClick={onDelete}
            disabled={deleting}
            className="p-1.5 text-red-600 dark:text-red-400 hover:text-red-500 dark:hover:text-red-300 bg-wo-surface-raised border border-wo-border-strong rounded-md hover:border-red-600/60 disabled:opacity-50"
            title="Șterge"
          >
            <Trash2 className="w-3.5 h-3.5" />
          </button>
        </div>
      </div>

      <div className="bg-wo-surface-raised rounded-lg p-3 text-center">
        <p className="text-[28px] font-bold text-foreground">
          {fmtMoney(p.amount)}
        </p>
        <p className="text-[12px] text-muted-foreground">
          {p.currency} / {periodicityLabel(p.periodicity).toLowerCase()}
        </p>
        <p className="text-[11px] text-muted-foreground mt-1 font-mono">
          ~ {fmtMoney(p.monthly_equivalent)} {p.currency} echivalent lunar
        </p>
      </div>

      <div className="grid grid-cols-2 gap-3">
        <InfoRow
          label="Furnizor"
          value={p.supplier ?? "—"}
          icon={<Building2 className="w-3 h-3" />}
        />
        <InfoRow
          label="Zi scadentă"
          value={p.due_day ? `Ziua ${p.due_day}` : "—"}
          icon={<Calendar className="w-3 h-3" />}
        />
      </div>

      <div className="grid grid-cols-2 gap-3">
        <div>
          <p className="text-[10px] text-muted-foreground uppercase tracking-wide mb-1">
            În overhead
          </p>
          <span
            className={`text-[12px] font-semibold ${
              p.include_in_overhead ? "text-emerald-600 dark:text-emerald-400" : "text-muted-foreground"
            }`}
          >
            {p.include_in_overhead ? "Da" : "Nu"}
          </span>
        </div>
        <div>
          <p className="text-[10px] text-muted-foreground uppercase tracking-wide mb-1">
            Alocat utilaj
          </p>
          <span
            className={`text-[12px] font-semibold ${
              p.include_in_machine_cost ? "text-emerald-600 dark:text-emerald-400" : "text-muted-foreground"
            }`}
          >
            {p.include_in_machine_cost
              ? p.linked_machine_id ?? "Da"
              : "Nu"}
          </span>
        </div>
      </div>

      {p.observatii && (
        <div className="bg-wo-surface-raised rounded-lg p-3">
          <p className="text-[10px] text-muted-foreground uppercase tracking-wide mb-1 flex items-center gap-1">
            <FileText className="w-3 h-3" /> Observații
          </p>
          <p className="text-[12px] text-muted-foreground whitespace-pre-wrap">
            {p.observatii}
          </p>
        </div>
      )}
    </div>
  );
}

function PaymentForm({
  form,
  mode,
  errors,
  saving,
  saveError,
  onChange,
  onCancel,
  onSubmit,
}: {
  form: PaymentForm;
  mode: "edit" | "create";
  errors: Record<string, string>;
  saving: boolean;
  saveError: string | null;
  onChange: <K extends keyof PaymentForm>(key: K, value: PaymentForm[K]) => void;
  onCancel: () => void;
  onSubmit: () => void;
}) {
  const hasErrors = Object.keys(errors).length > 0;
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
          {mode === "create" ? "Plată nouă" : "Editează plată"}
        </h3>
        <button
          type="button"
          onClick={onCancel}
          className="p-1 text-muted-foreground hover:text-foreground"
        >
          <X className="w-4 h-4" />
        </button>
      </div>

      <TextField
        label="Nume *"
        value={form.name}
        onChange={(v) => onChange("name", v)}
        error={errors.name}
      />

      <div className="grid grid-cols-2 gap-2">
        <SelectField
          label="Categorie"
          value={form.category}
          onChange={(v) => onChange("category", v)}
          options={PAYMENT_CATEGORIES.map((c) => ({
            value: c.value,
            label: c.label,
          }))}
        />
        <SelectField
          label="Status"
          value={form.status}
          onChange={(v) => onChange("status", v)}
          options={PAYMENT_STATUS}
        />
      </div>

      <div className="grid grid-cols-3 gap-2">
        <TextField
          label="Sumă *"
          value={form.amount}
          onChange={(v) => onChange("amount", v)}
          type="number"
          error={errors.amount}
        />
        <SelectField
          label="Monedă"
          value={form.currency}
          onChange={(v) => onChange("currency", v)}
          options={CURRENCIES.map((c) => ({ value: c, label: c }))}
        />
        <SelectField
          label="Periodicitate"
          value={form.periodicity}
          onChange={(v) => onChange("periodicity", v)}
          options={PAYMENT_PERIODICITY}
        />
      </div>

      <div className="grid grid-cols-2 gap-2">
        <TextField
          label="Furnizor"
          value={form.supplier}
          onChange={(v) => onChange("supplier", v)}
        />
        <TextField
          label="Ziua scadentă (1-31)"
          value={form.due_day}
          onChange={(v) => onChange("due_day", v)}
          type="number"
          error={errors.due_day}
        />
      </div>

      <div className="bg-wo-surface-raised rounded-lg p-3 space-y-2">
        <p className="text-[10px] text-muted-foreground uppercase tracking-wide">
          Alocare cost intern
        </p>
        <label className="flex items-center gap-2 text-[12px] text-foreground">
          <input
            type="checkbox"
            checked={form.include_in_overhead}
            onChange={(e) => onChange("include_in_overhead", e.target.checked)}
            className="rounded"
          />
          Inclus în overhead companie
        </label>
        <label className="flex items-center gap-2 text-[12px] text-foreground">
          <input
            type="checkbox"
            checked={form.include_in_machine_cost}
            onChange={(e) => onChange("include_in_machine_cost", e.target.checked)}
            className="rounded"
          />
          Alocat unui utilaj (ex. leasing, mentenanță)
        </label>
        {form.include_in_machine_cost && (
          <TextField
            label="ID utilaj *"
            value={form.linked_machine_id}
            onChange={(v) => onChange("linked_machine_id", v)}
            error={errors.linked_machine_id}
            hint="ID-ul utilajului la care se alocă această plată."
          />
        )}
      </div>

      <TextareaField
        label="Observații"
        value={form.observatii}
        onChange={(v) => onChange("observatii", v)}
      />

      {saveError && (
        <div className="bg-red-100 border border-red-200 dark:bg-red-900/30 dark:border-red-700/50 text-red-700 dark:text-red-300 text-[12px] rounded-md px-3 py-2">
          {saveError}
        </div>
      )}

      <div className="flex items-center gap-2 pt-1">
        <button
          type="submit"
          disabled={saving || hasErrors}
          className="inline-flex items-center gap-1.5 px-3 py-1.5 text-[12px] font-semibold text-white bg-blue-600 rounded-md hover:bg-blue-500 disabled:opacity-50 disabled:cursor-not-allowed"
        >
          <Save className="w-3.5 h-3.5" />
          {saving ? "Se salvează..." : mode === "create" ? "Creează" : "Salvează"}
        </button>
        <button
          type="button"
          onClick={onCancel}
          className="px-3 py-1.5 text-[12px] text-muted-foreground bg-wo-surface-raised border border-wo-border-strong rounded-md hover:border-wo-border-strong"
        >
          Anulează
        </button>
      </div>
    </form>
  );
}

// ============================================================
// COST ENGINE TAB — config (PUT) + base-config (GET, readonly)
// ============================================================
interface CostEngineForm {
  moneda_implicita: string;
  ore_productive_luna_firma: string;
  overhead_profile_name: string;
  metoda_overhead: string;
  cost_ora_manopera_default: string;
  allow_manual_override: boolean;
}

const OVERHEAD_METHODS: { value: string; label: string }[] = [
  { value: "fix_per_ora", label: "Sumă fixă pe oră" },
  { value: "procent_manopera", label: "Procent din manoperă" },
  { value: "alocare_utilaj", label: "Alocare pe utilaj" },
];

function configToForm(c: CostEngineConfigDTO): CostEngineForm {
  return {
    moneda_implicita: c.moneda_implicita ?? "RON",
    ore_productive_luna_firma:
      c.ore_productive_luna_firma === null ||
      c.ore_productive_luna_firma === undefined
        ? ""
        : String(c.ore_productive_luna_firma),
    overhead_profile_name: c.overhead_profile_name ?? "default",
    metoda_overhead: c.metoda_overhead ?? "fix_per_ora",
    cost_ora_manopera_default:
      c.cost_ora_manopera_default === null ||
      c.cost_ora_manopera_default === undefined
        ? ""
        : String(c.cost_ora_manopera_default),
    allow_manual_override: !!c.allow_manual_override,
  };
}

function validateConfig(f: CostEngineForm): Record<string, string> {
  const errs: Record<string, string> = {};
  if (!f.moneda_implicita.trim())
    errs.moneda_implicita = "Moneda implicită este obligatorie.";
  const ore = parseNumberOrNull(f.ore_productive_luna_firma);
  if (ore !== null && ore < 0)
    errs.ore_productive_luna_firma = "Valoarea nu poate fi negativă.";
  const cost = parseNumberOrNull(f.cost_ora_manopera_default);
  if (cost !== null && cost < 0)
    errs.cost_ora_manopera_default = "Valoarea nu poate fi negativă.";
  if (!f.overhead_profile_name.trim())
    errs.overhead_profile_name = "Numele profilului este obligatoriu.";
  if (!f.metoda_overhead.trim())
    errs.metoda_overhead = "Metoda overhead este obligatorie.";
  return errs;
}

function configFormToPayload(f: CostEngineForm): CostEngineConfigPayload {
  return {
    moneda_implicita: f.moneda_implicita.trim() || "RON",
    ore_productive_luna_firma: parseNumberOrNull(f.ore_productive_luna_firma),
    overhead_profile_name: f.overhead_profile_name.trim() || "default",
    metoda_overhead: f.metoda_overhead.trim() || "fix_per_ora",
    cost_ora_manopera_default: parseNumberOrNull(f.cost_ora_manopera_default),
    allow_manual_override: !!f.allow_manual_override,
  };
}

function CostEngineTab() {
  const [config, setConfig] = useState<CostEngineConfigDTO | null>(null);
  const [baseConfig, setBaseConfig] = useState<CostEngineBaseConfigDTO | null>(
    null
  );
  const [loading, setLoading] = useState(true);
  const [loadError, setLoadError] = useState<string | null>(null);

  const [editing, setEditing] = useState(false);
  const [form, setForm] = useState<CostEngineForm | null>(null);
  const [errors, setErrors] = useState<Record<string, string>>({});
  const [saving, setSaving] = useState(false);
  const [saveError, setSaveError] = useState<string | null>(null);

  const load = useCallback(async () => {
    setLoading(true);
    setLoadError(null);
    try {
      const [cfg, base] = await Promise.all([
        costEngineApi.getConfig(),
        costEngineApi.getBaseConfig(),
      ]);
      setConfig(cfg);
      setBaseConfig(base);
      if (!editing) setForm(configToForm(cfg));
    } catch (err) {
      setLoadError(err instanceof Error ? err.message : "Eroare la încărcare");
    } finally {
      setLoading(false);
    }
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, []);

  useEffect(() => {
    void load();
  }, [load]);

  const startEdit = () => {
    if (!config) return;
    setForm(configToForm(config));
    setErrors({});
    setSaveError(null);
    setEditing(true);
  };

  const cancelEdit = () => {
    if (config) setForm(configToForm(config));
    setErrors({});
    setSaveError(null);
    setEditing(false);
  };

  const updateField = <K extends keyof CostEngineForm>(
    key: K,
    value: CostEngineForm[K]
  ) => {
    setForm((prev) => {
      if (!prev) return prev;
      const next = { ...prev, [key]: value } as CostEngineForm;
      setErrors(validateConfig(next));
      return next;
    });
  };

  const submit = async () => {
    if (!form) return;
    const errs = validateConfig(form);
    setErrors(errs);
    if (Object.keys(errs).length > 0) return;
    setSaving(true);
    setSaveError(null);
    try {
      const updated = await costEngineApi.updateConfig(
        configFormToPayload(form)
      );
      setConfig(updated);
      // Refresh base-config so derived values reflect new config.
      const base = await costEngineApi.getBaseConfig();
      setBaseConfig(base);
      setEditing(false);
    } catch (err) {
      setSaveError(err instanceof Error ? err.message : "Eroare la salvare");
    } finally {
      setSaving(false);
    }
  };

  return (
    <div className="space-y-4">
      <div className="flex items-center justify-between flex-wrap gap-2">
        <div className="flex items-center gap-2">
          <Calculator className="w-4 h-4 text-wo-info" />
          <h2 className="text-[14px] font-bold text-foreground">
            Configurație cost intern
          </h2>
        </div>
        <button
          onClick={() => void load()}
          className="inline-flex items-center gap-1.5 px-3 py-1.5 text-[12px] text-muted-foreground bg-wo-surface-raised border border-wo-border-strong rounded-md hover:border-wo-border-strong hover:bg-wo-hover"
        >
          <RefreshCw className="w-3.5 h-3.5" />
          Reîncarcă
        </button>
      </div>

      <div
        className={`rounded-lg px-3 py-2.5 space-y-2 ${chromeBanner.warning}`}
        data-testid="settings-cost-rate-honesty"
      >
        <div className="flex flex-wrap items-center gap-1.5">
          <span className="rounded border border-wo-warning/40 bg-wo-surface-raised px-1.5 py-0.5 text-[10px] font-semibold text-wo-warning">
            INTERNAL ONLY
          </span>
          <span className="rounded border border-wo-border-strong bg-wo-surface-inset px-1.5 py-0.5 text-[10px] font-semibold text-wo-text-secondary">
            NOT CLIENT PRICE
          </span>
          <span className="rounded border border-wo-info/40 bg-wo-info-muted px-1.5 py-0.5 text-[10px] font-semibold text-wo-info">
            FROZEN
          </span>
          <span className="rounded border border-wo-warning/40 bg-wo-warning-muted px-1.5 py-0.5 text-[10px] font-semibold text-wo-warning">
            NEEDS OWNER GO
          </span>
        </div>
        <p className="text-[11px] leading-relaxed">
          <code className="font-mono text-[10px]">labour_rate</code>
          {" / "}
          <code className="font-mono text-[10px]">machine_rate</code>
          {" / "}
          <code className="font-mono text-[10px]">workcenter</code> hourly și costurile oră manoperă /
          overhead sunt tarife de cost intern — nu preț client și nu ofertă comercială.
        </p>
      </div>

      {loadError && (
        <div className="bg-red-100 border border-red-200 dark:bg-red-900/30 dark:border-red-700/50 text-red-700 dark:text-red-300 text-[12px] rounded-md px-3 py-2">
          {loadError}
        </div>
      )}

      {loading && (
        <div className="bg-card border border-border rounded-lg p-8 text-center text-muted-foreground text-[13px]">
          Se încarcă...
        </div>
      )}

      {!loading && baseConfig && (
        <div className="bg-card border border-border rounded-lg p-4">
          <div className="flex items-center justify-between mb-3">
            <h3 className="text-[13px] font-bold text-foreground">
              Valori calculate (base-config)
            </h3>
            <span
              className={`inline-flex items-center gap-1 text-[10px] font-semibold px-1.5 py-0.5 rounded border ${
                baseConfig.valid
                  ? "text-emerald-700 dark:text-emerald-400 bg-emerald-50 dark:bg-emerald-900/30 border-emerald-700/50"
                  : "text-amber-700 dark:text-amber-400 bg-amber-50 dark:bg-amber-900/30 border-amber-700/50"
              }`}
            >
              {baseConfig.valid ? (
                <CheckCircle2 className="w-3 h-3" />
              ) : (
                <AlertTriangle className="w-3 h-3" />
              )}
              {baseConfig.valid ? "Config validă" : "Incompletă"}
            </span>
          </div>

          <div className="grid grid-cols-2 md:grid-cols-4 gap-3">
            <MetricCard
              label="Monedă"
              value={baseConfig.currency}
              mono={false}
            />
            <MetricCard
              label="Ore productive / lună"
              value={fmtNumber(baseConfig.total_productive_hours_month)}
              hint="sumă ore productive ale angajaților validați"
            />
            <MetricCard
              label="Cost mediu manoperă / h"
              value={fmtMoney(baseConfig.average_labour_hour_cost)}
              suffix={baseConfig.currency}
              hint="labour_rate intern · ≠ preț client · cost_lunar_firma / ore_productive_luna"
            />
            <MetricCard
              label="Overhead / h"
              value={fmtMoney(baseConfig.overhead_hour_cost)}
              suffix={baseConfig.currency}
              hint="cost intern / h · NOT CLIENT PRICE · overhead lunar / ore productive"
            />
            <MetricCard
              label="Overhead lunar"
              value={fmtMoney(baseConfig.monthly_overhead_cost)}
              suffix={baseConfig.currency}
              hint="sumă plăți incluse în overhead (echivalent lunar)"
            />
            <MetricCard
              label="Profil overhead"
              value={baseConfig.overhead_profile_name ?? "—"}
              mono={false}
            />
            <MetricCard
              label="Metodă overhead"
              value={
                OVERHEAD_METHODS.find(
                  (m) => m.value === baseConfig.metoda_overhead
                )?.label ??
                baseConfig.metoda_overhead ??
                "—"
              }
              mono={false}
            />
            <MetricCard
              label="Override manual permis"
              value={baseConfig.allow_manual_override ? "Da" : "Nu"}
              mono={false}
            />
          </div>

          {baseConfig.warnings.length > 0 && (
            <div className={`mt-3 text-[11px] rounded-md px-3 py-2 space-y-1 ${chromeBanner.warning}`}>
              {baseConfig.warnings.map((w, i) => (
                <div key={i} className="flex items-start gap-1.5">
                  <AlertTriangle className="w-3 h-3 mt-0.5 shrink-0" />
                  <span>{w}</span>
                </div>
              ))}
            </div>
          )}
          <p className="text-[10px] text-muted-foreground italic mt-3">
            Aceste valori sunt calculate exclusiv de backend (endpoint
            GET&nbsp;/api/v1/cost-engine/base-config). Frontend-ul le afișează
            fără recalcul. Nu sunt preț client.
          </p>
        </div>
      )}

      {!loading && config && form && (
        <div className="bg-card border border-border rounded-lg p-4">
          <div className="flex items-center justify-between mb-3">
            <h3 className="text-[13px] font-bold text-foreground">
              Parametri config (editabili)
            </h3>
            {!editing && (
              <button
                onClick={startEdit}
                className="inline-flex items-center gap-1.5 px-3 py-1.5 text-[12px] text-muted-foreground bg-wo-surface-raised border border-wo-border-strong rounded-md hover:border-wo-border-strong"
              >
                <Pencil className="w-3.5 h-3.5" />
                Editează
              </button>
            )}
          </div>

          {!editing && (
            <div className="grid grid-cols-2 md:grid-cols-3 gap-3">
              <InfoRow label="Monedă implicită" value={config.moneda_implicita} />
              <InfoRow
                label="Ore productive/lună (firmă)"
                value={
                  config.ore_productive_luna_firma === null ||
                  config.ore_productive_luna_firma === undefined
                    ? "—"
                    : fmtNumber(config.ore_productive_luna_firma)
                }
              />
              <InfoRow
                label="Profil overhead"
                value={config.overhead_profile_name}
              />
              <InfoRow
                label="Metodă overhead"
                value={
                  OVERHEAD_METHODS.find(
                    (m) => m.value === config.metoda_overhead
                  )?.label ?? config.metoda_overhead
                }
              />
              <InfoRow
                label="Cost oră manoperă default (INTERNAL ONLY)"
                value={
                  config.cost_ora_manopera_default === null ||
                  config.cost_ora_manopera_default === undefined
                    ? "—"
                    : `${fmtMoney(config.cost_ora_manopera_default)} ${config.moneda_implicita}`
                }
              />
              <InfoRow
                label="Override manual permis"
                value={config.allow_manual_override ? "Da" : "Nu"}
              />
            </div>
          )}

          {editing && (
            <form
              onSubmit={(e) => {
                e.preventDefault();
                void submit();
              }}
              className="space-y-3"
            >
              <div className="grid grid-cols-2 gap-2">
                <SelectField
                  label="Monedă implicită"
                  value={form.moneda_implicita}
                  onChange={(v) => updateField("moneda_implicita", v)}
                  options={CURRENCIES.map((c) => ({ value: c, label: c }))}
                />
                <TextField
                  label="Ore productive / lună (firmă)"
                  value={form.ore_productive_luna_firma}
                  onChange={(v) => updateField("ore_productive_luna_firma", v)}
                  type="number"
                  error={errors.ore_productive_luna_firma}
                  hint="Lăsați gol pentru a folosi suma ore_productive_luna ale angajaților."
                />
              </div>
              <div className="grid grid-cols-2 gap-2">
                <TextField
                  label="Profil overhead"
                  value={form.overhead_profile_name}
                  onChange={(v) => updateField("overhead_profile_name", v)}
                  error={errors.overhead_profile_name}
                />
                <SelectField
                  label="Metodă overhead"
                  value={form.metoda_overhead}
                  onChange={(v) => updateField("metoda_overhead", v)}
                  options={OVERHEAD_METHODS}
                />
              </div>
              <TextField
                label="Cost oră manoperă default (INTERNAL ONLY)"
                value={form.cost_ora_manopera_default}
                onChange={(v) => updateField("cost_ora_manopera_default", v)}
                type="number"
                error={errors.cost_ora_manopera_default}
                hint="Fallback cost intern — nu este preț client. Folosit dacă angajatul nu are date complete."
              />
              <label className="flex items-center gap-2 text-[12px] text-foreground">
                <input
                  type="checkbox"
                  checked={form.allow_manual_override}
                  onChange={(e) =>
                    updateField("allow_manual_override", e.target.checked)
                  }
                  className="rounded"
                />
                Permite override manual în calcul cost intern
              </label>

              {saveError && (
                <div className="bg-red-100 border border-red-200 dark:bg-red-900/30 dark:border-red-700/50 text-red-700 dark:text-red-300 text-[12px] rounded-md px-3 py-2">
                  {saveError}
                </div>
              )}

              <div className="flex items-center gap-2 pt-1">
                <button
                  type="submit"
                  disabled={saving || Object.keys(errors).length > 0}
                  className="inline-flex items-center gap-1.5 px-3 py-1.5 text-[12px] font-semibold text-white bg-blue-600 rounded-md hover:bg-blue-500 disabled:opacity-50 disabled:cursor-not-allowed"
                >
                  <Save className="w-3.5 h-3.5" />
                  {saving ? "Se salvează..." : "Salvează"}
                </button>
                <button
                  type="button"
                  onClick={cancelEdit}
                  className="px-3 py-1.5 text-[12px] text-muted-foreground bg-wo-surface-raised border border-wo-border-strong rounded-md hover:border-wo-border-strong"
                >
                  Anulează
                </button>
              </div>
            </form>
          )}
        </div>
      )}
    </div>
  );
}

function MetricCard({
  label,
  value,
  suffix,
  hint,
  mono = true,
}: {
  label: string;
  value: string;
  suffix?: string;
  hint?: string;
  mono?: boolean;
}) {
  return (
    <div className="bg-wo-surface-raised border border-wo-border-strong rounded-lg p-3">
      <p className={`${chromeForm.label} mb-1`}>
        {label}
      </p>
      <p
        className={`text-[18px] font-bold text-foreground ${
          mono ? "font-mono" : ""
        }`}
      >
        {value}
        {suffix && (
          <span className="text-[11px] text-muted-foreground ml-1">{suffix}</span>
        )}
      </p>
      {hint && <p className="text-[10px] text-muted-foreground mt-1">{hint}</p>}
    </div>
  );
}

// ============================================================
// Shared input primitives (used by Settings forms)
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
      <label className={chromeForm.label}>
        {label}
      </label>
      <input
        type={type}
        value={value}
        onChange={(e) => onChange(e.target.value)}
        step={type === "number" ? "0.01" : undefined}
        className={`w-full ${chromeForm.input} ${
          error
            ? "border-red-600/60 focus:border-red-500"
            : ""
        }`}
      />
      {hint && !error && (
        <p className={`${chromeForm.helper} mt-1 text-[10px]`}>{hint}</p>
      )}
      {error && <p className="mt-1 text-[10px] text-red-700 dark:text-red-400">{error}</p>}
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
      <label className={chromeForm.label}>
        {label}
      </label>
      <textarea
        value={value}
        rows={3}
        onChange={(e) => onChange(e.target.value)}
        className={`w-full resize-y ${chromeForm.input}`}
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
      <label className={chromeForm.label}>
        {label}
      </label>
      <select
        value={value}
        onChange={(e) => onChange(e.target.value)}
        className={`w-full ${chromeForm.input}`}
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