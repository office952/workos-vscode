import { useEffect, useMemo, useState } from "react";
import { useParams, useNavigate } from "react-router-dom";
import {
  executionDetailPath,
  orderDetailPath,
  quoteDetailPath,
} from "@/lib/commercialSpineNavigation";
import { resolveIntakeEditPath } from "@/lib/volumetricIntakeRoute";
import { useBackendData } from "@/hooks/useBackendData";
import type { IntakeRequest, Quote, Order } from "@/lib/mockData";
import {
  getClientFiscalDisplayLabel,
  getClientFiscalDisplayStatus,
  listClients,
  type ClientEntity,
  type ClientFiscalDisplayStatus,
} from "@/lib/api";
import { ClientFiscalVerifyPanel } from "@/components/clients/ClientFiscalVerifyPanel";
import {
  ClientActiveChip,
  ClientFiscalStatusBadge,
  ClientRegistryChip,
} from "@/components/clients/ClientFiscalStatusBadge";
import {
  Building2,
  Phone,
  Mail,
  AlertTriangle,
  Inbox,
  FileText,
  ClipboardList,
  Plus,
  ArrowLeft,
  Activity,
  Clock,
  CheckCircle2,
  XCircle,
  Send,
  Lock,
  TrendingUp,
  Calendar,
  ChevronRight,
  ExternalLink,
  Receipt,
  FolderOpen,
  MessageSquare,
  History,
  AlertCircle,
  Ban,
  Eye,
  ArrowRightCircle,
  ShieldAlert,
  Banknote,
  FileCheck,
  ShieldCheck,
  MapPin,
} from "lucide-react";

// ============================================================
// HELPERS
// ============================================================
function formatCurrency(val: number) {
  return val.toLocaleString("ro-RO", { minimumFractionDigits: 2, maximumFractionDigits: 2 });
}

function formatDate(dateStr: string) {
  const d = new Date(dateStr);
  return d.toLocaleDateString("ro-RO", { day: "2-digit", month: "short", year: "numeric" });
}

function formatDateTime(dateStr: string) {
  const d = new Date(dateStr);
  return d.toLocaleDateString("ro-RO", { day: "2-digit", month: "short", hour: "2-digit", minute: "2-digit" });
}

// ============================================================
// STATUS CONFIGS
// ============================================================
type IntakeStatus = "new" | "in_review" | "needs_info" | "ready_for_quote" | "blocked" | "cancelled";
type QuoteStatus = "draft" | "priced" | "sent" | "viewed" | "negotiating" | "accepted" | "rejected" | "expired";
type OrderStatus = "created" | "confirmed" | "locked" | "in_execution" | "completed" | "cancelled";

const intakeStatusConfig: Record<IntakeStatus, { label: string; cls: string }> = {
  new: { label: "Nou", cls: "bg-wo-surface-inset text-wo-text-secondary border-wo-border-strong" },
  in_review: { label: "În Analiză", cls: "bg-wo-info-muted text-wo-info border-wo-info/35" },
  needs_info: { label: "Lipsă Info", cls: "bg-wo-warning-muted text-wo-warning border-wo-warning/35" },
  ready_for_quote: { label: "Gata pt. Ofertă", cls: "bg-wo-success-muted text-wo-success border-wo-success/35" },
  blocked: { label: "Blocat", cls: "bg-wo-error-muted text-wo-error border-wo-error/35" },
  cancelled: { label: "Anulat", cls: "bg-wo-surface-inset text-wo-text-muted border-wo-border-subtle" },
};

const quoteStatusConfig: Record<QuoteStatus, { label: string; cls: string }> = {
  draft: { label: "Draft", cls: "bg-wo-surface-inset text-wo-text-secondary border-wo-border-strong" },
  priced: { label: "Priced", cls: "bg-purple-50 text-purple-800 border-purple-200 dark:bg-purple-900/40 dark:text-purple-300 dark:border-purple-700" },
  sent: { label: "Trimis", cls: "bg-wo-info-muted text-wo-info border-wo-info/35" },
  viewed: { label: "Vizualizat", cls: "bg-cyan-50 text-cyan-800 border-cyan-200 dark:bg-cyan-900/40 dark:text-cyan-300 dark:border-cyan-700" },
  negotiating: { label: "Negociere", cls: "bg-wo-warning-muted text-wo-warning border-wo-warning/35" },
  accepted: { label: "Acceptat", cls: "bg-wo-success-muted text-wo-success border-wo-success/35" },
  rejected: { label: "Respins", cls: "bg-wo-error-muted text-wo-error border-wo-error/35" },
  expired: { label: "Expirat", cls: "bg-wo-surface-inset text-wo-text-muted border-wo-border-subtle" },
};

const orderStatusConfig: Record<OrderStatus, { label: string; cls: string }> = {
  created: { label: "Creat", cls: "bg-wo-surface-inset text-wo-text-secondary border-wo-border-strong" },
  confirmed: { label: "Confirmat", cls: "bg-wo-info-muted text-wo-info border-wo-info/35" },
  locked: { label: "Înghețat", cls: "bg-purple-50 text-purple-800 border-purple-200 dark:bg-purple-900/40 dark:text-purple-300 dark:border-purple-700" },
  in_execution: { label: "În Execuție", cls: "bg-wo-success-muted text-wo-success border-wo-success/35" },
  completed: { label: "Finalizat", cls: "bg-wo-success-muted text-wo-success border-wo-success/35" },
  cancelled: { label: "Anulat", cls: "bg-wo-error-muted text-wo-error border-wo-error/35" },
};

const paymentConfig: Record<string, { label: string; cls: string }> = {
  pending: { label: "Neplătit", cls: "text-wo-error bg-wo-error-muted border-wo-error/35" },
  partial: { label: "Avans", cls: "text-wo-warning bg-wo-warning-muted border-wo-warning/35" },
  paid: { label: "Plătit", cls: "text-wo-success bg-wo-success-muted border-wo-success/35" },
};

function StatusBadge({ label, cls }: { label: string; cls: string }) {
  return (
    <span className={`inline-flex items-center px-2 py-0.5 text-[10px] font-semibold rounded border ${cls}`}>
      {label}
    </span>
  );
}

// Action button variants
function ActionButton({ label, onClick, icon }: { label: string; onClick: () => void; icon?: React.ReactNode }) {
  return (
    <button
      onClick={(e) => { e.stopPropagation(); onClick(); }}
      className="inline-flex items-center gap-1 px-2 py-1 text-[10px] font-medium rounded border border-wo-info/40 bg-wo-info-muted text-wo-info hover:bg-wo-hover hover:border-wo-info/50 transition-colors"
    >
      {icon}
      {label}
    </button>
  );
}

function DisabledActionButton({ label, reason }: { label: string; reason: string }) {
  return (
    <span
      title={reason}
      className="inline-flex items-center gap-1 px-2 py-1 text-[10px] font-medium rounded border border-wo-border-subtle bg-wo-surface-inset text-wo-text-dim cursor-not-allowed"
    >
      <Ban className="w-2.5 h-2.5" />
      {label}
    </span>
  );
}

function ReadOnlyBadge({ label }: { label: string }) {
  return (
    <span className="inline-flex items-center gap-1 px-2 py-1 text-[10px] font-medium rounded border border-wo-border-subtle bg-wo-surface-inset text-wo-text-muted">
      <Eye className="w-2.5 h-2.5" />
      {label}
    </span>
  );
}

// ============================================================
// TABS
// ============================================================
type TabId = "overview" | "cereri" | "oferte" | "comenzi" | "facturi" | "documente" | "note" | "timeline";

const tabs: { id: TabId; label: string; icon: React.ReactNode }[] = [
  { id: "overview", label: "Overview", icon: <Activity className="w-3.5 h-3.5" /> },
  { id: "cereri", label: "Cereri", icon: <Inbox className="w-3.5 h-3.5" /> },
  { id: "oferte", label: "Oferte", icon: <FileText className="w-3.5 h-3.5" /> },
  { id: "comenzi", label: "Comenzi", icon: <ClipboardList className="w-3.5 h-3.5" /> },
  { id: "facturi", label: "Facturi", icon: <Receipt className="w-3.5 h-3.5" /> },
  { id: "documente", label: "Documente", icon: <FolderOpen className="w-3.5 h-3.5" /> },
  { id: "note", label: "Note", icon: <MessageSquare className="w-3.5 h-3.5" /> },
  { id: "timeline", label: "Timeline", icon: <History className="w-3.5 h-3.5" /> },
];

// ============================================================
// MAIN COMPONENT
// ============================================================
type ClientWorkspaceInfo = {
  name: string;
  contactPerson: string;
  cui?: string;
  address?: string;
  city?: string;
  identityType?: ClientEntity["identity_type"];
  fiscalStatus: ClientFiscalDisplayStatus;
  hasFiscalData: boolean;
  hasEntityRecord: boolean;
  entityId?: number;
  channel?: string;
};

export default function ClientWorkspace() {
  const { clientName } = useParams<{ clientName: string }>();
  const navigate = useNavigate();
  const { intakes, quotes, orders, loading } = useBackendData();
  const [activeTab, setActiveTab] = useState<TabId>("overview");
  const [clientEntity, setClientEntity] = useState<ClientEntity | null>(null);
  const [entityLoading, setEntityLoading] = useState(true);

  const decodedName = decodeURIComponent(clientName || "");

  useEffect(() => {
    let cancelled = false;
    setEntityLoading(true);
    listClients()
      .then((rows) => {
        if (cancelled) return;
        const match =
          rows.find((row) => row.name === decodedName) ??
          rows.find((row) => row.name.toLowerCase() === decodedName.toLowerCase());
        setClientEntity(match ?? null);
      })
      .catch(() => {
        if (!cancelled) setClientEntity(null);
      })
      .finally(() => {
        if (!cancelled) setEntityLoading(false);
      });
    return () => {
      cancelled = true;
    };
  }, [decodedName]);

  // Filter data for this client
  const clientIntakes = useMemo(
    () => intakes.filter((i) => i.client === decodedName),
    [intakes, decodedName]
  );
  const clientQuotes = useMemo(
    () => quotes.filter((q) => q.client === decodedName),
    [quotes, decodedName]
  );
  const clientOrders = useMemo(
    () => orders.filter((o) => o.client === decodedName),
    [orders, decodedName]
  );

  const clientInfo = useMemo((): ClientWorkspaceInfo => {
    const firstIntake = clientIntakes[0];
    const firstQuote = clientQuotes[0];
    if (clientEntity) {
      const fiscalStatus = getClientFiscalDisplayStatus(clientEntity);
      return {
        name: clientEntity.name,
        contactPerson:
          clientEntity.contact_person ||
          firstIntake?.contactPerson ||
          firstQuote?.contactPerson ||
          "—",
        cui: clientEntity.cui || firstIntake?.identity?.cui,
        address: clientEntity.address,
        city: clientEntity.city,
        identityType: clientEntity.identity_type,
        fiscalStatus,
        hasFiscalData: fiscalStatus === "saved",
        hasEntityRecord: true,
        entityId: clientEntity.id,
        channel: firstIntake?.channel,
      };
    }

    const intakeFiscal = firstIntake?.identity?.type === "fiscal";
    const cui = firstIntake?.identity?.cui;
    const fiscalStatus: ClientFiscalDisplayStatus =
      intakeFiscal && cui ? "saved" : intakeFiscal && !cui ? "missing_cui" : "non_fiscal";

    return {
      name: decodedName,
      contactPerson: firstIntake?.contactPerson || firstQuote?.contactPerson || "—",
      cui,
      fiscalStatus,
      hasFiscalData: fiscalStatus === "saved",
      hasEntityRecord: false,
      channel: firstIntake?.channel,
    };
  }, [clientEntity, clientIntakes, clientQuotes, decodedName]);

  // KPIs
  const kpis = useMemo(() => {
    const activeIntakes = clientIntakes.filter((i) =>
      ["new", "in_review", "needs_info", "ready_for_quote"].includes(i.status)
    ).length;
    const openQuotes = clientQuotes.filter((q) =>
      ["draft", "priced", "sent", "viewed", "negotiating"].includes(q.status)
    ).length;
    const activeOrders = clientOrders.filter((o) =>
      ["created", "confirmed", "locked", "in_execution"].includes(o.status)
    ).length;
    const totalRevenue = clientOrders.reduce((sum, o) => sum + o.totalAmount, 0);
    const blockedItems = clientIntakes.filter((i) => i.status === "blocked").length +
      clientOrders.filter((o) => o.status === "cancelled").length;
    return { activeIntakes, openQuotes, activeOrders, totalRevenue, blockedItems };
  }, [clientIntakes, clientQuotes, clientOrders]);

  if (loading || entityLoading) {
    return (
      <div className="flex items-center justify-center py-20">
        <div className="animate-spin rounded-full h-10 w-10 border-b-2 border-wo-info" />
      </div>
    );
  }

  if (!decodedName) {
    return (
      <div className="text-center py-20 text-wo-text-muted">Client negăsit.</div>
    );
  }

  return (
    <div className="space-y-3">
      {/* Back button */}
      <button
        onClick={() => navigate("/clients")}
        className="inline-flex items-center gap-1.5 text-[12px] text-wo-text-muted hover:text-wo-text-primary transition-colors"
      >
        <ArrowLeft className="w-3.5 h-3.5" />
        Înapoi la Clienți
      </button>

      {/* CLIENT HEADER */}
      <div className="bg-wo-surface-raised border border-wo-border-subtle rounded-xl p-4">
        <div className="flex items-start justify-between gap-4">
          {/* Left: Client identity */}
          <div className="flex items-start gap-3">
            <div className="w-10 h-10 rounded-lg bg-wo-info-muted flex items-center justify-center shrink-0">
              <Building2 className="w-5 h-5 text-wo-info" />
            </div>
            <div>
              <div className="flex items-center gap-2">
                <h1 className="text-[17px] font-bold text-wo-text-primary">{clientInfo.name}</h1>
                <ClientActiveChip />
                <ClientFiscalStatusBadge status={clientInfo.fiscalStatus} />
                {clientInfo.hasEntityRecord && (
                  <ClientRegistryChip label={`Registru entități #${clientInfo.entityId}`} />
                )}
              </div>
              <div className="flex items-center gap-4 mt-1 text-[11px] text-wo-text-muted flex-wrap">
                {clientInfo.cui && <span className="font-mono text-wo-text-secondary">CUI: {clientInfo.cui}</span>}
                {(clientInfo.address || clientInfo.city) && (
                  <span className="flex items-center gap-1">
                    <MapPin className="w-3 h-3" />
                    {[clientInfo.address, clientInfo.city].filter(Boolean).join(", ")}
                  </span>
                )}
                <span className="flex items-center gap-1"><Phone className="w-3 h-3" />{clientInfo.contactPerson}</span>
                {clientInfo.channel && <span className="flex items-center gap-1"><Mail className="w-3 h-3" />{clientInfo.channel}</span>}
              </div>
            </div>
          </div>

          {/* Right: KPI indicators */}
          <div className="flex items-center gap-2">
            <div className="text-center px-3 py-1.5 rounded-lg bg-wo-surface-inset border border-wo-border-subtle">
              <p className="text-[15px] font-bold text-wo-info">{kpis.activeIntakes}</p>
              <p className="text-[9px] text-wo-text-dim uppercase tracking-wide">Cereri</p>
            </div>
            <div className="text-center px-3 py-1.5 rounded-lg bg-wo-surface-inset border border-wo-border-subtle">
              <p className="text-[15px] font-bold text-purple-700 dark:text-purple-400">{kpis.openQuotes}</p>
              <p className="text-[9px] text-wo-text-dim uppercase tracking-wide">Oferte</p>
            </div>
            <div className="text-center px-3 py-1.5 rounded-lg bg-wo-surface-inset border border-wo-border-subtle">
              <p className="text-[15px] font-bold text-wo-success">{kpis.activeOrders}</p>
              <p className="text-[9px] text-wo-text-dim uppercase tracking-wide">Comenzi</p>
            </div>
            {kpis.blockedItems > 0 && (
              <div className="text-center px-3 py-1.5 rounded-lg bg-wo-error-muted border border-wo-error/35">
                <p className="text-[15px] font-bold text-wo-error">{kpis.blockedItems}</p>
                <p className="text-[9px] text-wo-error uppercase tracking-wide">Blocate</p>
              </div>
            )}
            {kpis.totalRevenue > 0 && (
              <div className="text-center px-3 py-1.5 rounded-lg bg-wo-surface-inset border border-wo-border-subtle">
                <p className="text-[13px] font-bold text-wo-text-primary">{formatCurrency(kpis.totalRevenue)}</p>
                <p className="text-[9px] text-wo-text-dim uppercase tracking-wide">RON Total</p>
              </div>
            )}
          </div>
        </div>

        {/* Quick Actions */}
        <div className="flex items-center gap-2 mt-3 pt-3 border-t border-wo-border-subtle">
          <button
            onClick={() => navigate("/intake")}
            className="inline-flex items-center gap-1.5 px-3 py-1.5 text-[11px] font-medium rounded border border-wo-info/40 bg-wo-info-muted text-wo-info hover:bg-wo-hover transition-colors"
          >
            <Plus className="w-3 h-3" />
            Cerere nouă
          </button>
          <DisabledActionButton label="Ofertă nouă" reason="Necesită flow backend — crearea ofertei se face din pagina Oferte" />
          <DisabledActionButton label="Emite document" reason="Modulul de documente nu este implementat" />
          <DisabledActionButton label="Adaugă notă" reason="Modulul de note nu este implementat" />
          <DisabledActionButton label="Atașează fișier" reason="Upload de fișiere nu este implementat" />
        </div>
      </div>

      {/* TABS */}
      <div className="flex items-center gap-0.5 border-b border-wo-border-subtle">
        {tabs.map((tab) => (
          <button
            key={tab.id}
            onClick={() => setActiveTab(tab.id)}
            className={`inline-flex items-center gap-1.5 px-3 py-2 text-[12px] font-medium transition-colors border-b-2 ${
              activeTab === tab.id
                ? "text-wo-info border-wo-info bg-wo-info-muted"
                : "text-wo-text-muted border-transparent hover:text-wo-text-primary hover:bg-wo-hover"
            }`}
          >
            {tab.icon}
            {tab.label}
          </button>
        ))}
      </div>

      {/* TAB CONTENT */}
      <div>
        {activeTab === "overview" && (
          <OverviewTab
            intakes={clientIntakes}
            quotes={clientQuotes}
            orders={clientOrders}
            clientInfo={clientInfo}
            clientEntity={clientEntity}
            onClientEntityUpdated={setClientEntity}
            navigate={navigate}
          />
        )}
        {activeTab === "cereri" && <CereriTab intakes={clientIntakes} quotes={clientQuotes} navigate={navigate} />}
        {activeTab === "oferte" && <OferteTab quotes={clientQuotes} orders={clientOrders} navigate={navigate} />}
        {activeTab === "comenzi" && <ComenziTab orders={clientOrders} navigate={navigate} />}
        {activeTab === "facturi" && <FacturiTab />}
        {activeTab === "documente" && <DocumenteTab />}
        {activeTab === "note" && <NoteTab />}
        {activeTab === "timeline" && <TimelineTab intakes={clientIntakes} quotes={clientQuotes} orders={clientOrders} navigate={navigate} />}
      </div>
    </div>
  );
}

// ============================================================
// OVERVIEW TAB — Control Panel
// ============================================================
function OverviewTab({
  intakes,
  quotes,
  orders,
  clientInfo,
  clientEntity,
  onClientEntityUpdated,
  navigate,
}: {
  intakes: IntakeRequest[];
  quotes: Quote[];
  orders: Order[];
  clientInfo: ClientWorkspaceInfo;
  clientEntity: ClientEntity | null;
  onClientEntityUpdated: (client: ClientEntity) => void;
  navigate: ReturnType<typeof useNavigate>;
}) {
  const activeIntakes = intakes.filter((i) => ["new", "in_review", "needs_info", "ready_for_quote"].includes(i.status));
  const blockedIntakes = intakes.filter((i) => i.status === "blocked");
  const activeQuotes = quotes.filter((q) => ["draft", "priced", "sent", "viewed", "negotiating"].includes(q.status));
  const activeOrders = orders.filter((o) => ["created", "confirmed", "locked", "in_execution"].includes(o.status));
  const completedOrders = orders.filter((o) => o.status === "completed");
  const acceptedQuotes = quotes.filter((q) => q.status === "accepted");
  const rejectedQuotes = quotes.filter((q) => q.status === "rejected");
  const readyForQuote = intakes.filter((i) => i.status === "ready_for_quote");
  const unpaidOrders = orders.filter((o) => o.paymentStatus === "pending" && o.status !== "cancelled");
  const totalCommercialValue = quotes.filter((q) => q.status === "accepted").reduce((s, q) => s + q.grandTotal, 0) +
    orders.reduce((s, o) => s + o.totalAmount, 0);

  // Alerts / Missing data
  const alerts: { icon: React.ReactNode; text: string; severity: "warning" | "error" | "info" }[] = [];
  if (clientInfo.fiscalStatus === "missing_cui") {
    alerts.push({
      icon: <ShieldAlert className="w-3.5 h-3.5" />,
      text: "Client fiscal fără CUI salvat",
      severity: "error",
    });
  } else if (clientInfo.fiscalStatus === "non_fiscal") {
    alerts.push({
      icon: <ShieldAlert className="w-3.5 h-3.5" />,
      text: getClientFiscalDisplayLabel("non_fiscal"),
      severity: "warning",
    });
  }
  if (!clientInfo.hasEntityRecord && clientInfo.fiscalStatus === "saved") {
    alerts.push({
      icon: <AlertTriangle className="w-3.5 h-3.5" />,
      text: "CUI vizibil din activitate comercială, dar clientul nu este în registrul entități",
      severity: "info",
    });
  }
  if (blockedIntakes.length > 0) {
    alerts.push({ icon: <AlertCircle className="w-3.5 h-3.5" />, text: `${blockedIntakes.length} cerere(i) blocată(e)`, severity: "error" });
  }
  if (unpaidOrders.length > 0) {
    alerts.push({ icon: <Banknote className="w-3.5 h-3.5" />, text: `${unpaidOrders.length} comandă(i) neplătită(e)`, severity: "warning" });
  }

  // Next Actions — specific, with clear enabled/disabled/read-only states
  interface NextAction {
    icon: React.ReactNode;
    label: string;
    state: "active" | "disabled" | "read-only";
    reason?: string;
    action?: () => void;
  }
  const nextActions: NextAction[] = [];

  if (clientEntity && clientInfo.fiscalStatus !== "saved") {
    nextActions.push({
      icon: <ShieldCheck className="w-3.5 h-3.5 text-wo-info" />,
      label: "Verifică date fiscale",
      state: "read-only",
    });
  }
  if (readyForQuote.length > 0) {
    nextActions.push({
      icon: <FileText className="w-3.5 h-3.5 text-purple-700 dark:text-purple-400" />,
      label: `Creează ofertă pentru ${readyForQuote[0].id}`,
      state: "disabled",
      reason: "Crearea ofertei se face din pagina Oferte — flow backend necesar",
    });
  }
  for (const o of activeOrders.slice(0, 2)) {
    if (o.jobId) {
      nextActions.push({
        icon: <Activity className="w-3.5 h-3.5 text-wo-success" />,
        label: `Urmărește execuția ${o.id} → ${o.jobId}`,
        state: "active",
        action: () => navigate(`/execution/${o.id}`),
      });
    }
  }
  if (unpaidOrders.length > 0) {
    nextActions.push({
      icon: <Banknote className="w-3.5 h-3.5 text-wo-warning" />,
      label: `Emite factură pentru ${unpaidOrders[0].id}`,
      state: "disabled",
      reason: "Modulul de facturare nu este implementat",
    });
  }
  nextActions.push({
    icon: <MessageSquare className="w-3.5 h-3.5 text-wo-text-muted" />,
    label: "Adaugă notă internă",
    state: "disabled",
    reason: "Modulul de note nu este implementat",
  });
  nextActions.push({
    icon: <FolderOpen className="w-3.5 h-3.5 text-wo-text-muted" />,
    label: "Atașează fișier / contract",
    state: "disabled",
    reason: "Upload de fișiere nu este implementat",
  });

  // Recent activity
  const recentItems = useMemo(() => {
    const items: { type: string; id: string; label: string; date: string; route?: string; status?: string }[] = [];
    for (const i of intakes) {
      items.push({
        type: "Cerere",
        id: i.id,
        label: i.description.slice(0, 45),
        date: i.updatedAt || i.createdAt,
        route: resolveIntakeEditPath({
          id: i.id,
          confirmedTemplateCode: i.confirmedTemplateCode,
          productFamily: i.productFamily,
        }),
        status: intakeStatusConfig[i.status as IntakeStatus]?.label,
      });
    }
    for (const q of quotes) {
      items.push({ type: "Ofertă", id: q.id, label: `${formatCurrency(q.grandTotal)} RON`, date: q.createdAt, route: quoteDetailPath(q.id), status: quoteStatusConfig[q.status as QuoteStatus]?.label });
    }
    for (const o of orders) {
      items.push({ type: "Comandă", id: o.id, label: o.productSummary, date: o.createdAt, route: orderDetailPath(o.id), status: orderStatusConfig[o.status as OrderStatus]?.label });
    }
    return items.sort((a, b) => b.date.localeCompare(a.date)).slice(0, 6);
  }, [intakes, quotes, orders]);

  return (
    <div className="space-y-3">
      <div className="bg-wo-surface-raised border border-wo-border-subtle rounded-lg p-4">
        <h3 className="text-[12px] font-semibold text-wo-text-secondary mb-3 flex items-center gap-2">
          <ShieldCheck className="w-4 h-4 text-wo-info" />
          Identificare fiscală
        </h3>
        <div className="grid grid-cols-1 md:grid-cols-2 gap-3 text-[12px]">
          <div>
            <p className="text-[10px] text-wo-text-muted uppercase">Status</p>
            <p className="text-wo-text-primary">{getClientFiscalDisplayLabel(clientInfo.fiscalStatus)}</p>
          </div>
          <div>
            <p className="text-[10px] text-wo-text-muted uppercase">CUI</p>
            <p className="text-wo-text-primary font-mono">{clientInfo.cui || "—"}</p>
          </div>
          <div>
            <p className="text-[10px] text-wo-text-muted uppercase">Tip identitate</p>
            <p className="text-wo-text-primary">
              {clientInfo.identityType === "fiscal"
                ? "Fiscal"
                : clientInfo.identityType === "temp"
                ? "Temporar"
                : clientInfo.fiscalStatus === "saved"
                ? "Fiscal (din activitate)"
                : "Nespecificat"}
            </p>
          </div>
          <div>
            <p className="text-[10px] text-wo-text-muted uppercase">Adresă / Oraș</p>
            <p className="text-wo-text-primary">
              {[clientInfo.address, clientInfo.city].filter(Boolean).join(", ") || "—"}
            </p>
          </div>
        </div>
      </div>

      {clientEntity && (
        <ClientFiscalVerifyPanel
          clientEntity={clientEntity}
          onClientUpdated={onClientEntityUpdated}
        />
      )}

      {/* Alerts / Missing Data */}
      {alerts.length > 0 && (
        <div className="bg-wo-surface-raised border border-wo-border-subtle rounded-lg p-3">
          <h3 className="text-[11px] font-semibold text-wo-text-muted uppercase tracking-wide mb-2 flex items-center gap-1.5">
            <AlertTriangle className="w-3.5 h-3.5 text-wo-warning" />
            Alerte & Date Lipsă
          </h3>
          <div className="space-y-1">
            {alerts.map((alert, idx) => (
              <div key={idx} className={`flex items-center gap-2 px-2 py-1.5 rounded text-[11px] ${
                alert.severity === "error" ? "bg-wo-error-muted text-wo-error" :
                alert.severity === "warning" ? "bg-wo-warning-muted text-wo-warning" :
                "bg-wo-surface-inset text-wo-text-muted"
              }`}>
                {alert.icon}
                {alert.text}
              </div>
            ))}
          </div>
        </div>
      )}

      <div className="grid grid-cols-2 gap-3">
        {/* Work in Progress */}
        <div className="bg-wo-surface-raised border border-wo-border-subtle rounded-lg p-4">
          <h3 className="text-[12px] font-semibold text-wo-text-secondary mb-3 flex items-center gap-2">
            <Activity className="w-4 h-4 text-wo-info" />
            Work in Progress
          </h3>
          <div className="space-y-1.5">
            {activeIntakes.length > 0 ? (
              activeIntakes.map((i) => (
                <div
                  key={i.id}
                  onClick={() =>
                    navigate(
                      resolveIntakeEditPath({
                        id: i.id,
                        confirmedTemplateCode: i.confirmedTemplateCode,
                        productFamily: i.productFamily,
                      })
                    )
                  }
                  className="flex items-center justify-between px-2 py-1.5 rounded hover:bg-wo-hover cursor-pointer"
                >
                  <div className="flex items-center gap-2">
                    <Inbox className="w-3.5 h-3.5 text-wo-info" />
                    <span className="text-[11px] font-mono text-wo-info">{i.id}</span>
                    <StatusBadge label={intakeStatusConfig[i.status as IntakeStatus]?.label} cls={intakeStatusConfig[i.status as IntakeStatus]?.cls} />
                  </div>
                  <ChevronRight className="w-3 h-3 text-wo-text-dim" />
                </div>
              ))
            ) : (
              <p className="text-[11px] text-wo-text-dim px-2">Nu există cereri active.</p>
            )}
            {activeQuotes.length > 0 && activeQuotes.map((q) => (
              <div key={q.id} onClick={() => navigate(quoteDetailPath(q.id))} className="flex items-center justify-between px-2 py-1.5 rounded hover:bg-wo-hover cursor-pointer">
                <div className="flex items-center gap-2">
                  <FileText className="w-3.5 h-3.5 text-purple-700 dark:text-purple-400" />
                  <span className="text-[11px] font-mono text-purple-700 dark:text-purple-400">{q.id}</span>
                  <StatusBadge label={quoteStatusConfig[q.status as QuoteStatus]?.label} cls={quoteStatusConfig[q.status as QuoteStatus]?.cls} />
                  <span className="text-[10px] text-wo-text-muted">{formatCurrency(q.grandTotal)} RON</span>
                </div>
                <ChevronRight className="w-3 h-3 text-wo-text-dim" />
              </div>
            ))}
            {activeOrders.length > 0 && activeOrders.map((o) => (
              <div key={o.id} onClick={() => o.jobId ? navigate(executionDetailPath(o.id)) : navigate(orderDetailPath(o.id))} className="flex items-center justify-between px-2 py-1.5 rounded hover:bg-wo-hover cursor-pointer">
                <div className="flex items-center gap-2">
                  <ClipboardList className="w-3.5 h-3.5 text-wo-success" />
                  <span className="text-[11px] font-mono text-wo-success">{o.id}</span>
                  <StatusBadge label={orderStatusConfig[o.status as OrderStatus]?.label} cls={orderStatusConfig[o.status as OrderStatus]?.cls} />
                  {o.jobId && <span className="text-[10px] text-wo-text-muted">→ {o.jobId}</span>}
                </div>
                <ChevronRight className="w-3 h-3 text-wo-text-dim" />
              </div>
            ))}
            {blockedIntakes.length > 0 && (
              <div className="mt-2 pt-2 border-t border-wo-border-subtle">
                <p className="text-[10px] text-wo-error uppercase font-semibold mb-1">Blocate</p>
                {blockedIntakes.map((i) => (
                  <div
                    key={i.id}
                    onClick={() =>
                      navigate(
                        resolveIntakeEditPath({
                          id: i.id,
                          confirmedTemplateCode: i.confirmedTemplateCode,
                          productFamily: i.productFamily,
                        })
                      )
                    }
                    className="flex items-center gap-2 px-2 py-1 rounded hover:bg-wo-error-muted cursor-pointer"
                  >
                    <AlertCircle className="w-3 h-3 text-wo-error" />
                    <span className="text-[11px] font-mono text-wo-error">{i.id}</span>
                    <span className="text-[10px] text-wo-error truncate">{i.notes || "Blocat"}</span>
                  </div>
                ))}
              </div>
            )}
          </div>
        </div>

        {/* Commercial Status */}
        <div className="bg-wo-surface-raised border border-wo-border-subtle rounded-lg p-4">
          <h3 className="text-[12px] font-semibold text-wo-text-secondary mb-3 flex items-center gap-2">
            <TrendingUp className="w-4 h-4 text-wo-success" />
            Status Comercial
          </h3>
          <div className="space-y-2">
            <div className="flex items-center justify-between text-[12px]">
              <span className="text-wo-text-muted">Valoare comercială totală</span>
              <span className="font-bold text-wo-text-primary">{totalCommercialValue > 0 ? `${formatCurrency(totalCommercialValue)} RON` : "—"}</span>
            </div>
            <div className="flex items-center justify-between text-[12px]">
              <span className="text-wo-text-muted">Oferte acceptate</span>
              <span className="font-semibold text-wo-success">{acceptedQuotes.length}</span>
            </div>
            <div className="flex items-center justify-between text-[12px]">
              <span className="text-wo-text-muted">Oferte respinse</span>
              <span className="font-semibold text-wo-error">{rejectedQuotes.length}</span>
            </div>
            <div className="flex items-center justify-between text-[12px]">
              <span className="text-wo-text-muted">Comenzi finalizate</span>
              <span className="font-semibold text-wo-success">{completedOrders.length}</span>
            </div>
            <div className="flex items-center justify-between text-[12px]">
              <span className="text-wo-text-muted">Comenzi neplătite</span>
              <span className={`font-semibold ${unpaidOrders.length > 0 ? "text-wo-error" : "text-wo-text-dim"}`}>
                {unpaidOrders.length > 0 ? unpaidOrders.length : "—"}
              </span>
            </div>
            <div className="flex items-center justify-between text-[12px]">
              <span className="text-wo-text-muted">Facturi emise</span>
              <span className="text-wo-text-dim text-[11px]">Indisponibil</span>
            </div>
            <div className="flex items-center justify-between text-[12px]">
              <span className="text-wo-text-muted">Contracte active</span>
              <span className="text-wo-text-dim text-[11px]">Indisponibil</span>
            </div>
          </div>
        </div>

        {/* Next Actions */}
        <div className="bg-wo-surface-raised border border-wo-border-subtle rounded-lg p-4">
          <h3 className="text-[12px] font-semibold text-wo-text-secondary mb-3 flex items-center gap-2">
            <ArrowRightCircle className="w-4 h-4 text-wo-warning" />
            Acțiuni Următoare
          </h3>
          <div className="space-y-1">
            {nextActions.map((action, idx) => (
              <div
                key={idx}
                onClick={action.state === "active" ? action.action : undefined}
                title={action.state === "disabled" ? action.reason : undefined}
                className={`flex items-center gap-2 px-2.5 py-2 rounded text-[11px] transition-colors ${
                  action.state === "active"
                    ? "text-wo-info hover:bg-wo-hover cursor-pointer"
                    : action.state === "read-only"
                    ? "text-wo-text-muted"
                    : "text-wo-text-dim cursor-not-allowed"
                }`}
              >
                {action.icon}
                <span className="flex-1">{action.label}</span>
                {action.state === "active" && <ChevronRight className="w-3 h-3 text-wo-info" />}
                {action.state === "disabled" && (
                  <span className="text-[9px] px-1.5 py-0.5 rounded bg-wo-surface-inset border border-wo-border-subtle text-wo-text-dim">indisponibil</span>
                )}
                {action.state === "read-only" && (
                  <span className="text-[9px] px-1.5 py-0.5 rounded bg-wo-surface-inset border border-wo-border-subtle text-wo-text-dim">read-only</span>
                )}
              </div>
            ))}
          </div>
        </div>

        {/* Recent Activity */}
        <div className="bg-wo-surface-raised border border-wo-border-subtle rounded-lg p-4">
          <h3 className="text-[12px] font-semibold text-wo-text-secondary mb-3 flex items-center gap-2">
            <Clock className="w-4 h-4 text-wo-text-muted" />
            Activitate Recentă
          </h3>
          {recentItems.length === 0 ? (
            <p className="text-[11px] text-wo-text-dim">Nicio activitate înregistrată.</p>
          ) : (
            <div className="space-y-1">
              {recentItems.map((item, idx) => (
                <div
                  key={idx}
                  onClick={() => item.route && navigate(item.route)}
                  className="flex items-center gap-2 px-2 py-1.5 rounded hover:bg-wo-hover cursor-pointer transition-colors"
                >
                  <span className="text-[9px] font-semibold text-wo-text-dim uppercase w-[48px] shrink-0">{item.type}</span>
                  <span className="text-[11px] text-wo-info font-mono w-[64px] shrink-0">{item.id}</span>
                  <span className="text-[10px] text-wo-text-muted truncate flex-1">{item.label}</span>
                  {item.status && <span className="text-[9px] text-wo-text-dim">{item.status}</span>}
                  <span className="text-[10px] text-wo-text-dim shrink-0">{formatDateTime(item.date)}</span>
                </div>
              ))}
            </div>
          )}
        </div>
      </div>
    </div>
  );
}

// ============================================================
// CERERI TAB — with cross-links to quote/order if exists
// ============================================================
function CereriTab({ intakes, quotes, navigate }: { intakes: IntakeRequest[]; quotes: Quote[]; navigate: ReturnType<typeof useNavigate> }) {
  const [search, setSearch] = useState("");
  const filtered = intakes.filter(
    (i) => !search || i.id.toLowerCase().includes(search.toLowerCase()) || i.description.toLowerCase().includes(search.toLowerCase())
  );

  // Build intake→quote map
  const intakeToQuote = useMemo(() => {
    const map = new Map<string, Quote>();
    for (const q of quotes) {
      if (q.intakeId) map.set(q.intakeId, q);
    }
    return map;
  }, [quotes]);

  return (
    <div className="space-y-3">
      <div className="flex items-center justify-between">
        <div className="flex items-center gap-2 bg-wo-surface-raised rounded-lg px-3 py-1.5 border border-wo-border-subtle w-64">
          <input
            type="text"
            placeholder="Caută cerere..."
            value={search}
            onChange={(e) => setSearch(e.target.value)}
            className="bg-transparent text-[12px] text-wo-text-primary placeholder:text-wo-text-dim outline-none w-full"
          />
        </div>
        <button
          onClick={() => navigate("/intake")}
          className="inline-flex items-center gap-1.5 px-3 py-1.5 text-[11px] font-medium rounded border border-wo-info/40 bg-wo-info-muted text-wo-info hover:bg-wo-hover transition-colors"
        >
          <Plus className="w-3 h-3" />
          Cerere nouă
        </button>
      </div>

      {filtered.length === 0 ? (
        <EmptyState message="Nu există cereri pentru acest client." />
      ) : (
        <div className="space-y-1.5">
          {filtered.map((intake) => {
            const cfg = intakeStatusConfig[intake.status as IntakeStatus];
            const linkedQuote = intakeToQuote.get(intake.id);
            return (
              <div
                key={intake.id}
                className="bg-wo-surface-raised border border-wo-border-subtle rounded-lg px-4 py-3 hover:border-wo-info/40 transition-all"
              >
                <div className="flex items-center justify-between">
                  <div className="flex items-center gap-2">
                    <span className="text-[12px] font-mono font-semibold text-wo-info">{intake.id}</span>
                    <StatusBadge label={cfg.label} cls={cfg.cls} />
                    <span className="text-[11px] text-wo-text-muted">{intake.productFamily}</span>
                    <span className="text-[10px] text-wo-text-dim">• {intake.channel}</span>
                  </div>
                  <div className="flex items-center gap-3">
                    <span className="text-[11px] text-wo-text-dim">{formatDate(intake.createdAt)}</span>
                    <span className="text-[11px] text-wo-text-muted">{intake.assignedTo}</span>
                  </div>
                </div>
                <p className="text-[11px] text-wo-text-muted mt-1 truncate">{intake.description}</p>
                {/* Cross-links and actions */}
                <div className="flex items-center gap-2 mt-2">
                  <ActionButton
                    label="Vezi cererea"
                    onClick={() =>
                      navigate(
                        resolveIntakeEditPath({
                          id: intake.id,
                          confirmedTemplateCode: intake.confirmedTemplateCode,
                          productFamily: intake.productFamily,
                        })
                      )
                    }
                    icon={<Eye className="w-2.5 h-2.5" />}
                  />
                  {linkedQuote ? (
                    <ActionButton label={`Ofertă: ${linkedQuote.id}`} onClick={() => navigate(quoteDetailPath(linkedQuote.id))} icon={<FileText className="w-2.5 h-2.5" />} />
                  ) : intake.status === "ready_for_quote" ? (
                    <DisabledActionButton label="Creează ofertă" reason="Crearea ofertei necesită flow backend" />
                  ) : null}
                  {intake.status === "blocked" && intake.notes && (
                    <span className="text-[10px] text-wo-error ml-2">⚠ {intake.notes.slice(0, 40)}</span>
                  )}
                </div>
              </div>
            );
          })}
        </div>
      )}
    </div>
  );
}

// ============================================================
// OFERTE TAB — with cross-links to order if exists
// ============================================================
function OferteTab({ quotes, orders, navigate }: { quotes: Quote[]; orders: Order[]; navigate: ReturnType<typeof useNavigate> }) {
  const [search, setSearch] = useState("");
  const filtered = quotes.filter(
    (q) => !search || q.id.toLowerCase().includes(search.toLowerCase()) || q.notes.toLowerCase().includes(search.toLowerCase())
  );

  // Build quote→order map
  const quoteToOrder = useMemo(() => {
    const map = new Map<string, Order>();
    for (const o of orders) {
      if (o.quoteId) map.set(o.quoteId, o);
    }
    return map;
  }, [orders]);

  return (
    <div className="space-y-3">
      <div className="flex items-center justify-between">
        <div className="flex items-center gap-2 bg-wo-surface-raised rounded-lg px-3 py-1.5 border border-wo-border-subtle w-64">
          <input
            type="text"
            placeholder="Caută ofertă..."
            value={search}
            onChange={(e) => setSearch(e.target.value)}
            className="bg-transparent text-[12px] text-wo-text-primary placeholder:text-wo-text-dim outline-none w-full"
          />
        </div>
        <DisabledActionButton label="Ofertă nouă" reason="Crearea ofertei se face din pagina Oferte — necesită flow backend" />
      </div>

      {filtered.length === 0 ? (
        <EmptyState message="Nu există oferte pentru acest client." />
      ) : (
        <div className="space-y-1.5">
          {filtered.map((quote) => {
            const cfg = quoteStatusConfig[quote.status as QuoteStatus];
            const linkedOrder = quoteToOrder.get(quote.id);
            return (
              <div
                key={quote.id}
                className="bg-wo-surface-raised border border-wo-border-subtle rounded-lg px-4 py-3 hover:border-purple-300 dark:hover:border-purple-600/30 transition-all"
              >
                <div className="flex items-center justify-between">
                  <div className="flex items-center gap-2">
                    <span className="text-[12px] font-mono font-semibold text-purple-700 dark:text-purple-400">{quote.id}</span>
                    <StatusBadge label={cfg.label} cls={cfg.cls} />
                    <span className="text-[10px] text-wo-text-dim">v{quote.version}</span>
                    {quote.intakeId && (
                      <span className="text-[10px] text-wo-text-dim">← Cerere: {quote.intakeId}</span>
                    )}
                  </div>
                  <div className="flex items-center gap-3">
                    <span className="text-[13px] font-bold text-wo-text-primary">{formatCurrency(quote.grandTotal)} RON</span>
                  </div>
                </div>
                <div className="flex items-center gap-4 mt-1.5 text-[11px]">
                  <span className="text-wo-text-muted">Marjă: {quote.marginPct}%</span>
                  <span className="text-wo-text-muted">Discount: {quote.discountPct}%</span>
                  <span className="text-wo-text-muted flex items-center gap-1">
                    <Calendar className="w-3 h-3" />
                    Valabil: {formatDate(quote.validUntil)}
                  </span>
                  {linkedOrder && (
                    <span className="text-wo-success font-semibold">→ Comandă: {linkedOrder.id}</span>
                  )}
                </div>
                {quote.notes && <p className="text-[10px] text-wo-text-dim mt-1 truncate">{quote.notes}</p>}
                {/* Actions */}
                <div className="flex items-center gap-2 mt-2">
                  <ActionButton label="Vezi oferta" onClick={() => navigate(quoteDetailPath(quote.id))} icon={<Eye className="w-2.5 h-2.5" />} />
                  <DisabledActionButton label="Document comercial" reason="Generarea documentului necesită flow backend" />
                  {linkedOrder ? (
                    <ActionButton label={`Comandă: ${linkedOrder.id}`} onClick={() => navigate(orderDetailPath(linkedOrder.id))} icon={<ClipboardList className="w-2.5 h-2.5" />} />
                  ) : quote.status === "accepted" ? (
                    <DisabledActionButton label="Transformă în comandă" reason="Comanda a fost deja creată sau flow indisponibil" />
                  ) : (
                    <DisabledActionButton label="Transformă în comandă" reason={`Necesită status 'Acceptat' — actual: ${cfg.label}`} />
                  )}
                </div>
              </div>
            );
          })}
        </div>
      )}
    </div>
  );
}

// ============================================================
// COMENZI TAB — with clear status, actions, cross-links
// ============================================================
function ComenziTab({ orders, navigate }: { orders: Order[]; navigate: ReturnType<typeof useNavigate> }) {
  const [search, setSearch] = useState("");
  const filtered = orders.filter(
    (o) => !search || o.id.toLowerCase().includes(search.toLowerCase()) || o.productSummary.toLowerCase().includes(search.toLowerCase())
  );

  return (
    <div className="space-y-3">
      <div className="flex items-center gap-2 bg-wo-surface-raised rounded-lg px-3 py-1.5 border border-wo-border-subtle w-64">
        <input
          type="text"
          placeholder="Caută comandă..."
          value={search}
          onChange={(e) => setSearch(e.target.value)}
          className="bg-transparent text-[12px] text-wo-text-primary placeholder:text-wo-text-dim outline-none w-full"
        />
      </div>

      {filtered.length === 0 ? (
        <EmptyState message="Nu există comenzi pentru acest client." />
      ) : (
        <div className="space-y-1.5">
          {filtered.map((order) => {
            const cfg = orderStatusConfig[order.status as OrderStatus];
            const payCfg = paymentConfig[order.paymentStatus];
            return (
              <div
                key={order.id}
                className="bg-wo-surface-raised border border-wo-border-subtle rounded-lg px-4 py-3 hover:border-wo-success/40 transition-all"
              >
                <div className="flex items-center justify-between">
                  <div className="flex items-center gap-2">
                    <span className="text-[12px] font-mono font-bold text-wo-success">{order.id}</span>
                    <StatusBadge label={cfg.label} cls={cfg.cls} />
                    {payCfg && <StatusBadge label={payCfg.label} cls={payCfg.cls} />}
                    <span className="text-[10px] text-wo-text-dim">← Ofertă: {order.quoteId}</span>
                  </div>
                  <span className="text-[13px] font-bold text-wo-text-primary">{formatCurrency(order.totalAmount)} RON</span>
                </div>
                <p className="text-[12px] text-wo-text-muted mt-1">{order.productSummary}</p>
                {/* Details row */}
                <div className="flex items-center gap-4 mt-2 text-[11px]">
                  <span className="text-wo-text-muted flex items-center gap-1">
                    <Calendar className="w-3 h-3" />
                    Livrare: {formatDate(order.promisedDelivery)}
                  </span>
                  <span className="text-wo-text-muted">
                    Execuție: {order.jobId ? (
                      <button onClick={() => navigate(`/execution/${order.id}`)} className="text-wo-info hover:text-wo-info font-mono ml-0.5">{order.jobId}</button>
                    ) : (
                      <span className="text-wo-text-dim">Lipsă</span>
                    )}
                  </span>
                  <span className="text-wo-text-muted">
                    Document: <span className="text-wo-text-dim">Lipsă</span>
                  </span>
                  <span className="text-wo-text-muted">
                    Factură: <span className="text-wo-text-dim">{order.paymentStatus === "paid" ? "Emisă" : order.paymentStatus === "partial" ? "Draft" : "Lipsă"}</span>
                  </span>
                </div>
                {order.notes && <p className="text-[10px] text-wo-text-dim mt-1">{order.notes}</p>}
                {/* Actions */}
                <div className="flex items-center gap-2 mt-2">
                  <ActionButton label="Vezi comanda" onClick={() => navigate(orderDetailPath(order.id))} icon={<Eye className="w-2.5 h-2.5" />} />
                  {order.jobId ? (
                    <ActionButton label="Execuție" onClick={() => navigate(executionDetailPath(order.id))} icon={<Activity className="w-2.5 h-2.5" />} />
                  ) : (
                    <DisabledActionButton label="Execuție" reason="Job-ul nu a fost încă creat" />
                  )}
                  <DisabledActionButton label="Document" reason="Modulul de documente nu este implementat" />
                  <DisabledActionButton label="Factură" reason="Modulul de facturare nu este implementat" />
                </div>
              </div>
            );
          })}
        </div>
      )}
    </div>
  );
}

// ============================================================
// FACTURI TAB
// ============================================================
function FacturiTab() {
  return (
    <div className="bg-wo-surface-raised border border-wo-border-subtle rounded-lg p-6 text-center">
      <Receipt className="w-8 h-8 text-wo-text-dim mx-auto mb-3" />
      <p className="text-[13px] text-wo-text-muted font-medium">Nu există facturi asociate acestui client.</p>
      <p className="text-[11px] text-wo-text-dim mt-1">Modulul de facturare nu este implementat în această versiune.</p>
      <div className="mt-3">
        <DisabledActionButton label="Emite factură" reason="Modulul de facturare nu este implementat" />
      </div>
    </div>
  );
}

// ============================================================
// DOCUMENTE TAB
// ============================================================
function DocumenteTab() {
  return (
    <div className="bg-wo-surface-raised border border-wo-border-subtle rounded-lg p-6 text-center">
      <FolderOpen className="w-8 h-8 text-wo-text-dim mx-auto mb-3" />
      <p className="text-[13px] text-wo-text-muted font-medium">Nu există documente atașate acestui client.</p>
      <p className="text-[11px] text-wo-text-dim mt-1">Upload/download de fișiere și contracte nu este implementat.</p>
      <div className="mt-3 flex items-center justify-center gap-2">
        <DisabledActionButton label="Adaugă document" reason="Upload de fișiere nu este implementat" />
        <DisabledActionButton label="Adaugă contract" reason="Modulul de contracte nu este implementat" />
      </div>
    </div>
  );
}

// ============================================================
// NOTE TAB
// ============================================================
function NoteTab() {
  return (
    <div className="bg-wo-surface-raised border border-wo-border-subtle rounded-lg p-6 text-center">
      <MessageSquare className="w-8 h-8 text-wo-text-dim mx-auto mb-3" />
      <p className="text-[13px] text-wo-text-muted font-medium">Nu există note interne pentru acest client.</p>
      <p className="text-[11px] text-wo-text-dim mt-1">Adăugarea de note necesită flow backend.</p>
      <div className="mt-3">
        <DisabledActionButton label="Adaugă notă" reason="Modulul de note nu este implementat" />
      </div>
    </div>
  );
}

// ============================================================
// TIMELINE TAB — operational history
// ============================================================
function TimelineTab({
  intakes,
  quotes,
  orders,
  navigate,
}: {
  intakes: IntakeRequest[];
  quotes: Quote[];
  orders: Order[];
  navigate: ReturnType<typeof useNavigate>;
}) {
  const events = useMemo(() => {
    const items: { date: string; type: string; typeLabel: string; icon: React.ReactNode; label: string; entityId: string; status?: string; route?: string }[] = [];

    for (const i of intakes) {
      items.push({
        date: i.createdAt,
        type: "intake",
        typeLabel: "CERERE",
        icon: <Inbox className="w-3.5 h-3.5 text-wo-info" />,
        label: `Cerere creată — ${i.productFamily}`,
        entityId: i.id,
        status: intakeStatusConfig[i.status as IntakeStatus]?.label,
        route: resolveIntakeEditPath({
          id: i.id,
          confirmedTemplateCode: i.confirmedTemplateCode,
          productFamily: i.productFamily,
        }),
      });
      if (i.status === "ready_for_quote" && i.updatedAt && i.updatedAt !== i.createdAt) {
        items.push({
          date: i.updatedAt,
          type: "intake",
          typeLabel: "CERERE",
          icon: <FileCheck className="w-3.5 h-3.5 text-wo-success" />,
          label: `Cerere pregătită pentru ofertare`,
          entityId: i.id,
          status: "Gata pt. Ofertă",
          route: resolveIntakeEditPath({
            id: i.id,
            confirmedTemplateCode: i.confirmedTemplateCode,
            productFamily: i.productFamily,
          }),
        });
      }
      if (i.status === "blocked") {
        items.push({
          date: i.updatedAt || i.createdAt,
          type: "intake",
          typeLabel: "CERERE",
          icon: <AlertCircle className="w-3.5 h-3.5 text-wo-error" />,
          label: `Cerere blocată${i.notes ? ` — ${i.notes.slice(0, 40)}` : ""}`,
          entityId: i.id,
          status: "Blocat",
          route: resolveIntakeEditPath({
            id: i.id,
            confirmedTemplateCode: i.confirmedTemplateCode,
            productFamily: i.productFamily,
          }),
        });
      }
    }

    for (const q of quotes) {
      items.push({
        date: q.createdAt,
        type: "quote",
        typeLabel: "OFERTĂ",
        icon: <FileText className="w-3.5 h-3.5 text-purple-700 dark:text-purple-400" />,
        label: `Ofertă creată — ${formatCurrency(q.grandTotal)} RON (v${q.version})`,
        entityId: q.id,
        status: quoteStatusConfig[q.status as QuoteStatus]?.label,
        route: "/quotes",
      });
      if (q.status === "sent") {
        items.push({
          date: q.createdAt,
          type: "quote",
          typeLabel: "OFERTĂ",
          icon: <Send className="w-3.5 h-3.5 text-wo-info" />,
          label: `Ofertă trimisă clientului`,
          entityId: q.id,
          status: "Trimis",
          route: "/quotes",
        });
      }
      if (q.status === "accepted") {
        items.push({
          date: q.createdAt,
          type: "quote",
          typeLabel: "OFERTĂ",
          icon: <CheckCircle2 className="w-3.5 h-3.5 text-wo-success" />,
          label: `Ofertă acceptată — ${formatCurrency(q.grandTotal)} RON`,
          entityId: q.id,
          status: "Acceptat",
          route: "/quotes",
        });
      }
      if (q.status === "rejected") {
        items.push({
          date: q.createdAt,
          type: "quote",
          typeLabel: "OFERTĂ",
          icon: <XCircle className="w-3.5 h-3.5 text-wo-error" />,
          label: `Ofertă respinsă`,
          entityId: q.id,
          status: "Respins",
          route: "/quotes",
        });
      }
    }

    for (const o of orders) {
      items.push({
        date: o.createdAt,
        type: "order",
        typeLabel: "COMANDĂ",
        icon: <ClipboardList className="w-3.5 h-3.5 text-wo-success" />,
        label: `Comandă creată — ${o.productSummary}`,
        entityId: o.id,
        status: orderStatusConfig[o.status as OrderStatus]?.label,
        route: "/orders",
      });
      if (o.lockedAt) {
        items.push({
          date: o.lockedAt,
          type: "order",
          typeLabel: "COMANDĂ",
          icon: <Lock className="w-3.5 h-3.5 text-purple-700 dark:text-purple-400" />,
          label: `Comandă înghețată (snapshot v${o.snapshotVersion})`,
          entityId: o.id,
          status: "Înghețat",
          route: "/orders",
        });
      }
      if (o.status === "in_execution" && o.jobId) {
        items.push({
          date: o.createdAt,
          type: "execution",
          typeLabel: "EXECUȚIE",
          icon: <Activity className="w-3.5 h-3.5 text-wo-success" />,
          label: `Comandă în execuție — ${o.jobId}`,
          entityId: o.id,
          status: "În Execuție",
          route: `/execution/${o.id}`,
        });
      }
      if (o.status === "completed") {
        items.push({
          date: o.createdAt,
          type: "order",
          typeLabel: "COMANDĂ",
          icon: <CheckCircle2 className="w-3.5 h-3.5 text-wo-success" />,
          label: `Comandă finalizată — ${formatCurrency(o.totalAmount)} RON`,
          entityId: o.id,
          status: "Finalizat",
          route: "/orders",
        });
      }
    }

    return items.sort((a, b) => b.date.localeCompare(a.date));
  }, [intakes, quotes, orders]);

  if (events.length === 0) {
    return <EmptyState message="Nicio activitate înregistrată pentru acest client." />;
  }

  return (
    <div className="bg-wo-surface-raised border border-wo-border-subtle rounded-lg overflow-hidden">
      {events.map((event, idx) => (
        <div
          key={idx}
          onClick={() => event.route && navigate(event.route)}
          className={`flex items-center gap-3 px-4 py-2.5 hover:bg-wo-hover cursor-pointer transition-colors ${
            idx < events.length - 1 ? "border-b border-wo-border-subtle/50" : ""
          }`}
        >
          <div className="shrink-0">{event.icon}</div>
          <span className="text-[9px] font-bold uppercase tracking-wider text-wo-text-dim w-[56px] shrink-0">{event.typeLabel}</span>
          <span className="text-[11px] font-mono text-wo-text-muted w-[64px] shrink-0">{event.entityId}</span>
          <span className="text-[11px] text-wo-text-secondary flex-1 truncate">{event.label}</span>
          {event.status && (
            <span className="text-[9px] px-1.5 py-0.5 rounded bg-wo-surface-inset border border-wo-border-subtle text-wo-text-muted shrink-0">{event.status}</span>
          )}
          <span className="text-[10px] text-wo-text-dim shrink-0 w-[90px] text-right">{formatDateTime(event.date)}</span>
          <ExternalLink className="w-3 h-3 text-wo-text-dim shrink-0" />
        </div>
      ))}
    </div>
  );
}

// ============================================================
// EMPTY STATE
// ============================================================
function EmptyState({ message }: { message: string }) {
  return (
    <div className="bg-wo-surface-raised border border-wo-border-subtle rounded-lg p-6 text-center">
      <p className="text-[12px] text-wo-text-muted">{message}</p>
    </div>
  );
}