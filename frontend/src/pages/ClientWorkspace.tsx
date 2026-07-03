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
  new: { label: "Nou", cls: "bg-slate-700/60 text-slate-300 border-slate-600" },
  in_review: { label: "În Analiză", cls: "bg-blue-900/40 text-blue-300 border-blue-700" },
  needs_info: { label: "Lipsă Info", cls: "bg-amber-900/40 text-amber-300 border-amber-700" },
  ready_for_quote: { label: "Gata pt. Ofertă", cls: "bg-emerald-900/40 text-emerald-300 border-emerald-700" },
  blocked: { label: "Blocat", cls: "bg-red-900/40 text-red-300 border-red-700" },
  cancelled: { label: "Anulat", cls: "bg-slate-800/60 text-slate-400 border-slate-600" },
};

const quoteStatusConfig: Record<QuoteStatus, { label: string; cls: string }> = {
  draft: { label: "Draft", cls: "bg-slate-700/60 text-slate-300 border-slate-600" },
  priced: { label: "Priced", cls: "bg-purple-900/40 text-purple-300 border-purple-700" },
  sent: { label: "Trimis", cls: "bg-blue-900/40 text-blue-300 border-blue-700" },
  viewed: { label: "Vizualizat", cls: "bg-cyan-900/40 text-cyan-300 border-cyan-700" },
  negotiating: { label: "Negociere", cls: "bg-amber-900/40 text-amber-300 border-amber-700" },
  accepted: { label: "Acceptat", cls: "bg-emerald-900/40 text-emerald-300 border-emerald-700" },
  rejected: { label: "Respins", cls: "bg-red-900/40 text-red-300 border-red-700" },
  expired: { label: "Expirat", cls: "bg-slate-800/60 text-slate-400 border-slate-600" },
};

const orderStatusConfig: Record<OrderStatus, { label: string; cls: string }> = {
  created: { label: "Creat", cls: "bg-slate-700/60 text-slate-300 border-slate-600" },
  confirmed: { label: "Confirmat", cls: "bg-blue-900/40 text-blue-300 border-blue-700" },
  locked: { label: "Înghețat", cls: "bg-purple-900/40 text-purple-300 border-purple-700" },
  in_execution: { label: "În Execuție", cls: "bg-emerald-900/40 text-emerald-300 border-emerald-700" },
  completed: { label: "Finalizat", cls: "bg-emerald-900/50 text-emerald-200 border-emerald-600" },
  cancelled: { label: "Anulat", cls: "bg-red-900/40 text-red-300 border-red-700" },
};

const paymentConfig: Record<string, { label: string; cls: string }> = {
  pending: { label: "Neplătit", cls: "text-red-400 bg-red-900/20 border-red-800/30" },
  partial: { label: "Avans", cls: "text-amber-400 bg-amber-900/20 border-amber-800/30" },
  paid: { label: "Plătit", cls: "text-emerald-400 bg-emerald-900/20 border-emerald-800/30" },
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
      className="inline-flex items-center gap-1 px-2 py-1 text-[10px] font-medium rounded border border-blue-700/50 bg-blue-900/15 text-blue-300 hover:bg-blue-900/30 hover:border-blue-600 transition-colors"
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
      className="inline-flex items-center gap-1 px-2 py-1 text-[10px] font-medium rounded border border-slate-700/40 bg-slate-800/20 text-slate-600 cursor-not-allowed"
    >
      <Ban className="w-2.5 h-2.5" />
      {label}
    </span>
  );
}

function ReadOnlyBadge({ label }: { label: string }) {
  return (
    <span className="inline-flex items-center gap-1 px-2 py-1 text-[10px] font-medium rounded border border-slate-700/30 bg-slate-800/10 text-slate-500">
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
        <div className="animate-spin rounded-full h-10 w-10 border-b-2 border-blue-500" />
      </div>
    );
  }

  if (!decodedName) {
    return (
      <div className="text-center py-20 text-slate-500">Client negăsit.</div>
    );
  }

  return (
    <div className="space-y-3">
      {/* Back button */}
      <button
        onClick={() => navigate("/clients")}
        className="inline-flex items-center gap-1.5 text-[12px] text-slate-500 hover:text-slate-300 transition-colors"
      >
        <ArrowLeft className="w-3.5 h-3.5" />
        Înapoi la Clienți
      </button>

      {/* CLIENT HEADER */}
      <div className="bg-[#111827] border border-[#1E293B] rounded-xl p-4">
        <div className="flex items-start justify-between gap-4">
          {/* Left: Client identity */}
          <div className="flex items-start gap-3">
            <div className="w-10 h-10 rounded-lg bg-blue-600/15 flex items-center justify-center shrink-0">
              <Building2 className="w-5 h-5 text-blue-400" />
            </div>
            <div>
              <div className="flex items-center gap-2">
                <h1 className="text-[17px] font-bold text-slate-100">{clientInfo.name}</h1>
                <span className="px-2 py-0.5 text-[9px] font-semibold rounded bg-emerald-900/30 text-emerald-400 border border-emerald-800/30">
                  Activ
                </span>
                <span
                  className={`inline-flex items-center gap-1 px-1.5 py-0.5 text-[9px] font-semibold rounded border ${
                    clientInfo.fiscalStatus === "saved"
                      ? "bg-emerald-900/30 text-emerald-400 border-emerald-800/30"
                      : clientInfo.fiscalStatus === "missing_cui"
                      ? "bg-red-900/30 text-red-400 border-red-800/30"
                      : "bg-amber-900/30 text-amber-400 border-amber-800/30"
                  }`}
                >
                  {clientInfo.fiscalStatus === "saved" ? (
                    <CheckCircle2 className="w-2.5 h-2.5" />
                  ) : (
                    <AlertTriangle className="w-2.5 h-2.5" />
                  )}
                  {getClientFiscalDisplayLabel(clientInfo.fiscalStatus)}
                </span>
                {clientInfo.hasEntityRecord && (
                  <span className="px-1.5 py-0.5 text-[9px] font-semibold rounded bg-blue-900/30 text-blue-300 border border-blue-800/30">
                    Registru entități #{clientInfo.entityId}
                  </span>
                )}
              </div>
              <div className="flex items-center gap-4 mt-1 text-[11px] text-slate-500 flex-wrap">
                {clientInfo.cui && <span className="font-mono text-slate-300">CUI: {clientInfo.cui}</span>}
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
            <div className="text-center px-3 py-1.5 rounded-lg bg-[#0D1321] border border-[#1E293B]">
              <p className="text-[15px] font-bold text-blue-400">{kpis.activeIntakes}</p>
              <p className="text-[9px] text-slate-600 uppercase tracking-wide">Cereri</p>
            </div>
            <div className="text-center px-3 py-1.5 rounded-lg bg-[#0D1321] border border-[#1E293B]">
              <p className="text-[15px] font-bold text-purple-400">{kpis.openQuotes}</p>
              <p className="text-[9px] text-slate-600 uppercase tracking-wide">Oferte</p>
            </div>
            <div className="text-center px-3 py-1.5 rounded-lg bg-[#0D1321] border border-[#1E293B]">
              <p className="text-[15px] font-bold text-emerald-400">{kpis.activeOrders}</p>
              <p className="text-[9px] text-slate-600 uppercase tracking-wide">Comenzi</p>
            </div>
            {kpis.blockedItems > 0 && (
              <div className="text-center px-3 py-1.5 rounded-lg bg-red-950/30 border border-red-900/30">
                <p className="text-[15px] font-bold text-red-400">{kpis.blockedItems}</p>
                <p className="text-[9px] text-red-600 uppercase tracking-wide">Blocate</p>
              </div>
            )}
            {kpis.totalRevenue > 0 && (
              <div className="text-center px-3 py-1.5 rounded-lg bg-[#0D1321] border border-[#1E293B]">
                <p className="text-[13px] font-bold text-slate-200">{formatCurrency(kpis.totalRevenue)}</p>
                <p className="text-[9px] text-slate-600 uppercase tracking-wide">RON Total</p>
              </div>
            )}
          </div>
        </div>

        {/* Quick Actions */}
        <div className="flex items-center gap-2 mt-3 pt-3 border-t border-[#1E293B]">
          <button
            onClick={() => navigate("/intake")}
            className="inline-flex items-center gap-1.5 px-3 py-1.5 text-[11px] font-medium rounded border border-blue-700/50 bg-blue-900/20 text-blue-300 hover:bg-blue-900/40 transition-colors"
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
      <div className="flex items-center gap-0.5 border-b border-[#1E293B]">
        {tabs.map((tab) => (
          <button
            key={tab.id}
            onClick={() => setActiveTab(tab.id)}
            className={`inline-flex items-center gap-1.5 px-3 py-2 text-[12px] font-medium transition-colors border-b-2 ${
              activeTab === tab.id
                ? "text-blue-400 border-blue-500 bg-blue-900/10"
                : "text-slate-500 border-transparent hover:text-slate-300 hover:bg-slate-800/30"
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
      icon: <ShieldCheck className="w-3.5 h-3.5 text-blue-400" />,
      label: "Verifică date fiscale",
      state: "read-only",
    });
  }
  if (readyForQuote.length > 0) {
    nextActions.push({
      icon: <FileText className="w-3.5 h-3.5 text-purple-400" />,
      label: `Creează ofertă pentru ${readyForQuote[0].id}`,
      state: "disabled",
      reason: "Crearea ofertei se face din pagina Oferte — flow backend necesar",
    });
  }
  for (const o of activeOrders.slice(0, 2)) {
    if (o.jobId) {
      nextActions.push({
        icon: <Activity className="w-3.5 h-3.5 text-emerald-400" />,
        label: `Urmărește execuția ${o.id} → ${o.jobId}`,
        state: "active",
        action: () => navigate(`/execution/${o.id}`),
      });
    }
  }
  if (unpaidOrders.length > 0) {
    nextActions.push({
      icon: <Banknote className="w-3.5 h-3.5 text-amber-400" />,
      label: `Emite factură pentru ${unpaidOrders[0].id}`,
      state: "disabled",
      reason: "Modulul de facturare nu este implementat",
    });
  }
  nextActions.push({
    icon: <MessageSquare className="w-3.5 h-3.5 text-slate-500" />,
    label: "Adaugă notă internă",
    state: "disabled",
    reason: "Modulul de note nu este implementat",
  });
  nextActions.push({
    icon: <FolderOpen className="w-3.5 h-3.5 text-slate-500" />,
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
      <div className="bg-[#111827] border border-[#1E293B] rounded-lg p-4">
        <h3 className="text-[12px] font-semibold text-slate-300 mb-3 flex items-center gap-2">
          <ShieldCheck className="w-4 h-4 text-blue-400" />
          Identificare fiscală
        </h3>
        <div className="grid grid-cols-1 md:grid-cols-2 gap-3 text-[12px]">
          <div>
            <p className="text-[10px] text-slate-500 uppercase">Status</p>
            <p className="text-slate-200">{getClientFiscalDisplayLabel(clientInfo.fiscalStatus)}</p>
          </div>
          <div>
            <p className="text-[10px] text-slate-500 uppercase">CUI</p>
            <p className="text-slate-200 font-mono">{clientInfo.cui || "—"}</p>
          </div>
          <div>
            <p className="text-[10px] text-slate-500 uppercase">Tip identitate</p>
            <p className="text-slate-200">
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
            <p className="text-[10px] text-slate-500 uppercase">Adresă / Oraș</p>
            <p className="text-slate-200">
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
        <div className="bg-[#111827] border border-[#1E293B] rounded-lg p-3">
          <h3 className="text-[11px] font-semibold text-slate-400 uppercase tracking-wide mb-2 flex items-center gap-1.5">
            <AlertTriangle className="w-3.5 h-3.5 text-amber-500" />
            Alerte & Date Lipsă
          </h3>
          <div className="space-y-1">
            {alerts.map((alert, idx) => (
              <div key={idx} className={`flex items-center gap-2 px-2 py-1.5 rounded text-[11px] ${
                alert.severity === "error" ? "bg-red-950/20 text-red-400" :
                alert.severity === "warning" ? "bg-amber-950/20 text-amber-400" :
                "bg-slate-800/30 text-slate-400"
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
        <div className="bg-[#111827] border border-[#1E293B] rounded-lg p-4">
          <h3 className="text-[12px] font-semibold text-slate-300 mb-3 flex items-center gap-2">
            <Activity className="w-4 h-4 text-blue-400" />
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
                  className="flex items-center justify-between px-2 py-1.5 rounded hover:bg-slate-800/40 cursor-pointer"
                >
                  <div className="flex items-center gap-2">
                    <Inbox className="w-3.5 h-3.5 text-blue-400" />
                    <span className="text-[11px] font-mono text-blue-400">{i.id}</span>
                    <StatusBadge label={intakeStatusConfig[i.status as IntakeStatus]?.label} cls={intakeStatusConfig[i.status as IntakeStatus]?.cls} />
                  </div>
                  <ChevronRight className="w-3 h-3 text-slate-700" />
                </div>
              ))
            ) : (
              <p className="text-[11px] text-slate-600 px-2">Nu există cereri active.</p>
            )}
            {activeQuotes.length > 0 && activeQuotes.map((q) => (
              <div key={q.id} onClick={() => navigate(quoteDetailPath(q.id))} className="flex items-center justify-between px-2 py-1.5 rounded hover:bg-slate-800/40 cursor-pointer">
                <div className="flex items-center gap-2">
                  <FileText className="w-3.5 h-3.5 text-purple-400" />
                  <span className="text-[11px] font-mono text-purple-400">{q.id}</span>
                  <StatusBadge label={quoteStatusConfig[q.status as QuoteStatus]?.label} cls={quoteStatusConfig[q.status as QuoteStatus]?.cls} />
                  <span className="text-[10px] text-slate-500">{formatCurrency(q.grandTotal)} RON</span>
                </div>
                <ChevronRight className="w-3 h-3 text-slate-700" />
              </div>
            ))}
            {activeOrders.length > 0 && activeOrders.map((o) => (
              <div key={o.id} onClick={() => o.jobId ? navigate(executionDetailPath(o.id)) : navigate(orderDetailPath(o.id))} className="flex items-center justify-between px-2 py-1.5 rounded hover:bg-slate-800/40 cursor-pointer">
                <div className="flex items-center gap-2">
                  <ClipboardList className="w-3.5 h-3.5 text-emerald-400" />
                  <span className="text-[11px] font-mono text-emerald-400">{o.id}</span>
                  <StatusBadge label={orderStatusConfig[o.status as OrderStatus]?.label} cls={orderStatusConfig[o.status as OrderStatus]?.cls} />
                  {o.jobId && <span className="text-[10px] text-slate-500">→ {o.jobId}</span>}
                </div>
                <ChevronRight className="w-3 h-3 text-slate-700" />
              </div>
            ))}
            {blockedIntakes.length > 0 && (
              <div className="mt-2 pt-2 border-t border-[#1E293B]">
                <p className="text-[10px] text-red-500 uppercase font-semibold mb-1">Blocate</p>
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
                    className="flex items-center gap-2 px-2 py-1 rounded hover:bg-red-950/20 cursor-pointer"
                  >
                    <AlertCircle className="w-3 h-3 text-red-400" />
                    <span className="text-[11px] font-mono text-red-400">{i.id}</span>
                    <span className="text-[10px] text-red-500/70 truncate">{i.notes || "Blocat"}</span>
                  </div>
                ))}
              </div>
            )}
          </div>
        </div>

        {/* Commercial Status */}
        <div className="bg-[#111827] border border-[#1E293B] rounded-lg p-4">
          <h3 className="text-[12px] font-semibold text-slate-300 mb-3 flex items-center gap-2">
            <TrendingUp className="w-4 h-4 text-emerald-400" />
            Status Comercial
          </h3>
          <div className="space-y-2">
            <div className="flex items-center justify-between text-[12px]">
              <span className="text-slate-400">Valoare comercială totală</span>
              <span className="font-bold text-slate-200">{totalCommercialValue > 0 ? `${formatCurrency(totalCommercialValue)} RON` : "—"}</span>
            </div>
            <div className="flex items-center justify-between text-[12px]">
              <span className="text-slate-400">Oferte acceptate</span>
              <span className="font-semibold text-emerald-400">{acceptedQuotes.length}</span>
            </div>
            <div className="flex items-center justify-between text-[12px]">
              <span className="text-slate-400">Oferte respinse</span>
              <span className="font-semibold text-red-400">{rejectedQuotes.length}</span>
            </div>
            <div className="flex items-center justify-between text-[12px]">
              <span className="text-slate-400">Comenzi finalizate</span>
              <span className="font-semibold text-emerald-400">{completedOrders.length}</span>
            </div>
            <div className="flex items-center justify-between text-[12px]">
              <span className="text-slate-400">Comenzi neplătite</span>
              <span className={`font-semibold ${unpaidOrders.length > 0 ? "text-red-400" : "text-slate-600"}`}>
                {unpaidOrders.length > 0 ? unpaidOrders.length : "—"}
              </span>
            </div>
            <div className="flex items-center justify-between text-[12px]">
              <span className="text-slate-400">Facturi emise</span>
              <span className="text-slate-600 text-[11px]">Indisponibil</span>
            </div>
            <div className="flex items-center justify-between text-[12px]">
              <span className="text-slate-400">Contracte active</span>
              <span className="text-slate-600 text-[11px]">Indisponibil</span>
            </div>
          </div>
        </div>

        {/* Next Actions */}
        <div className="bg-[#111827] border border-[#1E293B] rounded-lg p-4">
          <h3 className="text-[12px] font-semibold text-slate-300 mb-3 flex items-center gap-2">
            <ArrowRightCircle className="w-4 h-4 text-amber-400" />
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
                    ? "text-blue-300 hover:bg-blue-900/20 cursor-pointer"
                    : action.state === "read-only"
                    ? "text-slate-500"
                    : "text-slate-600 cursor-not-allowed"
                }`}
              >
                {action.icon}
                <span className="flex-1">{action.label}</span>
                {action.state === "active" && <ChevronRight className="w-3 h-3 text-blue-500" />}
                {action.state === "disabled" && (
                  <span className="text-[9px] px-1.5 py-0.5 rounded bg-slate-800 border border-slate-700/50 text-slate-600">indisponibil</span>
                )}
                {action.state === "read-only" && (
                  <span className="text-[9px] px-1.5 py-0.5 rounded bg-slate-800 border border-slate-700/50 text-slate-600">read-only</span>
                )}
              </div>
            ))}
          </div>
        </div>

        {/* Recent Activity */}
        <div className="bg-[#111827] border border-[#1E293B] rounded-lg p-4">
          <h3 className="text-[12px] font-semibold text-slate-300 mb-3 flex items-center gap-2">
            <Clock className="w-4 h-4 text-slate-400" />
            Activitate Recentă
          </h3>
          {recentItems.length === 0 ? (
            <p className="text-[11px] text-slate-600">Nicio activitate înregistrată.</p>
          ) : (
            <div className="space-y-1">
              {recentItems.map((item, idx) => (
                <div
                  key={idx}
                  onClick={() => item.route && navigate(item.route)}
                  className="flex items-center gap-2 px-2 py-1.5 rounded hover:bg-slate-800/40 cursor-pointer transition-colors"
                >
                  <span className="text-[9px] font-semibold text-slate-600 uppercase w-[48px] shrink-0">{item.type}</span>
                  <span className="text-[11px] text-blue-400 font-mono w-[64px] shrink-0">{item.id}</span>
                  <span className="text-[10px] text-slate-400 truncate flex-1">{item.label}</span>
                  {item.status && <span className="text-[9px] text-slate-600">{item.status}</span>}
                  <span className="text-[10px] text-slate-700 shrink-0">{formatDateTime(item.date)}</span>
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
        <div className="flex items-center gap-2 bg-[#111827] rounded-lg px-3 py-1.5 border border-[#1E293B] w-64">
          <input
            type="text"
            placeholder="Caută cerere..."
            value={search}
            onChange={(e) => setSearch(e.target.value)}
            className="bg-transparent text-[12px] text-slate-200 placeholder:text-slate-600 outline-none w-full"
          />
        </div>
        <button
          onClick={() => navigate("/intake")}
          className="inline-flex items-center gap-1.5 px-3 py-1.5 text-[11px] font-medium rounded border border-blue-700/50 bg-blue-900/20 text-blue-300 hover:bg-blue-900/40 transition-colors"
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
                className="bg-[#111827] border border-[#1E293B] rounded-lg px-4 py-3 hover:border-blue-600/30 transition-all"
              >
                <div className="flex items-center justify-between">
                  <div className="flex items-center gap-2">
                    <span className="text-[12px] font-mono font-semibold text-blue-400">{intake.id}</span>
                    <StatusBadge label={cfg.label} cls={cfg.cls} />
                    <span className="text-[11px] text-slate-500">{intake.productFamily}</span>
                    <span className="text-[10px] text-slate-600">• {intake.channel}</span>
                  </div>
                  <div className="flex items-center gap-3">
                    <span className="text-[11px] text-slate-600">{formatDate(intake.createdAt)}</span>
                    <span className="text-[11px] text-slate-500">{intake.assignedTo}</span>
                  </div>
                </div>
                <p className="text-[11px] text-slate-400 mt-1 truncate">{intake.description}</p>
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
                    <span className="text-[10px] text-red-400 ml-2">⚠ {intake.notes.slice(0, 40)}</span>
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
        <div className="flex items-center gap-2 bg-[#111827] rounded-lg px-3 py-1.5 border border-[#1E293B] w-64">
          <input
            type="text"
            placeholder="Caută ofertă..."
            value={search}
            onChange={(e) => setSearch(e.target.value)}
            className="bg-transparent text-[12px] text-slate-200 placeholder:text-slate-600 outline-none w-full"
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
                className="bg-[#111827] border border-[#1E293B] rounded-lg px-4 py-3 hover:border-purple-600/30 transition-all"
              >
                <div className="flex items-center justify-between">
                  <div className="flex items-center gap-2">
                    <span className="text-[12px] font-mono font-semibold text-purple-400">{quote.id}</span>
                    <StatusBadge label={cfg.label} cls={cfg.cls} />
                    <span className="text-[10px] text-slate-600">v{quote.version}</span>
                    {quote.intakeId && (
                      <span className="text-[10px] text-slate-600">← Cerere: {quote.intakeId}</span>
                    )}
                  </div>
                  <div className="flex items-center gap-3">
                    <span className="text-[13px] font-bold text-slate-200">{formatCurrency(quote.grandTotal)} RON</span>
                  </div>
                </div>
                <div className="flex items-center gap-4 mt-1.5 text-[11px]">
                  <span className="text-slate-500">Marjă: {quote.marginPct}%</span>
                  <span className="text-slate-500">Discount: {quote.discountPct}%</span>
                  <span className="text-slate-500 flex items-center gap-1">
                    <Calendar className="w-3 h-3" />
                    Valabil: {formatDate(quote.validUntil)}
                  </span>
                  {linkedOrder && (
                    <span className="text-emerald-400 font-semibold">→ Comandă: {linkedOrder.id}</span>
                  )}
                </div>
                {quote.notes && <p className="text-[10px] text-slate-600 mt-1 truncate">{quote.notes}</p>}
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
      <div className="flex items-center gap-2 bg-[#111827] rounded-lg px-3 py-1.5 border border-[#1E293B] w-64">
        <input
          type="text"
          placeholder="Caută comandă..."
          value={search}
          onChange={(e) => setSearch(e.target.value)}
          className="bg-transparent text-[12px] text-slate-200 placeholder:text-slate-600 outline-none w-full"
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
                className="bg-[#111827] border border-[#1E293B] rounded-lg px-4 py-3 hover:border-emerald-600/30 transition-all"
              >
                <div className="flex items-center justify-between">
                  <div className="flex items-center gap-2">
                    <span className="text-[12px] font-mono font-bold text-emerald-400">{order.id}</span>
                    <StatusBadge label={cfg.label} cls={cfg.cls} />
                    {payCfg && <StatusBadge label={payCfg.label} cls={payCfg.cls} />}
                    <span className="text-[10px] text-slate-600">← Ofertă: {order.quoteId}</span>
                  </div>
                  <span className="text-[13px] font-bold text-slate-200">{formatCurrency(order.totalAmount)} RON</span>
                </div>
                <p className="text-[12px] text-slate-400 mt-1">{order.productSummary}</p>
                {/* Details row */}
                <div className="flex items-center gap-4 mt-2 text-[11px]">
                  <span className="text-slate-500 flex items-center gap-1">
                    <Calendar className="w-3 h-3" />
                    Livrare: {formatDate(order.promisedDelivery)}
                  </span>
                  <span className="text-slate-500">
                    Execuție: {order.jobId ? (
                      <button onClick={() => navigate(`/execution/${order.id}`)} className="text-blue-400 hover:text-blue-300 font-mono ml-0.5">{order.jobId}</button>
                    ) : (
                      <span className="text-slate-600">Lipsă</span>
                    )}
                  </span>
                  <span className="text-slate-500">
                    Document: <span className="text-slate-600">Lipsă</span>
                  </span>
                  <span className="text-slate-500">
                    Factură: <span className="text-slate-600">{order.paymentStatus === "paid" ? "Emisă" : order.paymentStatus === "partial" ? "Draft" : "Lipsă"}</span>
                  </span>
                </div>
                {order.notes && <p className="text-[10px] text-slate-600 mt-1">{order.notes}</p>}
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
    <div className="bg-[#111827] border border-[#1E293B] rounded-lg p-6 text-center">
      <Receipt className="w-8 h-8 text-slate-700 mx-auto mb-3" />
      <p className="text-[13px] text-slate-400 font-medium">Nu există facturi asociate acestui client.</p>
      <p className="text-[11px] text-slate-600 mt-1">Modulul de facturare nu este implementat în această versiune.</p>
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
    <div className="bg-[#111827] border border-[#1E293B] rounded-lg p-6 text-center">
      <FolderOpen className="w-8 h-8 text-slate-700 mx-auto mb-3" />
      <p className="text-[13px] text-slate-400 font-medium">Nu există documente atașate acestui client.</p>
      <p className="text-[11px] text-slate-600 mt-1">Upload/download de fișiere și contracte nu este implementat.</p>
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
    <div className="bg-[#111827] border border-[#1E293B] rounded-lg p-6 text-center">
      <MessageSquare className="w-8 h-8 text-slate-700 mx-auto mb-3" />
      <p className="text-[13px] text-slate-400 font-medium">Nu există note interne pentru acest client.</p>
      <p className="text-[11px] text-slate-600 mt-1">Adăugarea de note necesită flow backend.</p>
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
        icon: <Inbox className="w-3.5 h-3.5 text-blue-400" />,
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
          icon: <FileCheck className="w-3.5 h-3.5 text-emerald-400" />,
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
          icon: <AlertCircle className="w-3.5 h-3.5 text-red-400" />,
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
        icon: <FileText className="w-3.5 h-3.5 text-purple-400" />,
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
          icon: <Send className="w-3.5 h-3.5 text-blue-400" />,
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
          icon: <CheckCircle2 className="w-3.5 h-3.5 text-emerald-400" />,
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
          icon: <XCircle className="w-3.5 h-3.5 text-red-400" />,
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
        icon: <ClipboardList className="w-3.5 h-3.5 text-emerald-400" />,
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
          icon: <Lock className="w-3.5 h-3.5 text-purple-400" />,
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
          icon: <Activity className="w-3.5 h-3.5 text-emerald-400" />,
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
          icon: <CheckCircle2 className="w-3.5 h-3.5 text-emerald-400" />,
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
    <div className="bg-[#111827] border border-[#1E293B] rounded-lg overflow-hidden">
      {events.map((event, idx) => (
        <div
          key={idx}
          onClick={() => event.route && navigate(event.route)}
          className={`flex items-center gap-3 px-4 py-2.5 hover:bg-slate-800/30 cursor-pointer transition-colors ${
            idx < events.length - 1 ? "border-b border-[#1E293B]/50" : ""
          }`}
        >
          <div className="shrink-0">{event.icon}</div>
          <span className="text-[9px] font-bold uppercase tracking-wider text-slate-600 w-[56px] shrink-0">{event.typeLabel}</span>
          <span className="text-[11px] font-mono text-slate-500 w-[64px] shrink-0">{event.entityId}</span>
          <span className="text-[11px] text-slate-300 flex-1 truncate">{event.label}</span>
          {event.status && (
            <span className="text-[9px] px-1.5 py-0.5 rounded bg-slate-800 border border-slate-700/50 text-slate-500 shrink-0">{event.status}</span>
          )}
          <span className="text-[10px] text-slate-700 shrink-0 w-[90px] text-right">{formatDateTime(event.date)}</span>
          <ExternalLink className="w-3 h-3 text-slate-700 shrink-0" />
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
    <div className="bg-[#111827] border border-[#1E293B] rounded-lg p-6 text-center">
      <p className="text-[12px] text-slate-500">{message}</p>
    </div>
  );
}