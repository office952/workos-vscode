import { useState, useMemo } from "react";
import { useNavigate } from "react-router-dom";
import { useBackendData } from "@/hooks/useBackendData";
import type { Quote, Order } from "@/lib/mockData";
import {
  FileText,
  Search,
  Filter,
  Ban,
  FileSignature,
  Stamp,
  ChevronRight,
  ExternalLink,
  X,
  Inbox,
  ClipboardList,
  Users,
  Activity,
  FileCheck,
  Shield,
  Truck,
  Wrench,
  Printer,
  BookOpen,
  Eye,
  Download,
  Send,
  CheckCircle2,
  Info,
  AlertCircle,
} from "lucide-react";

// ============================================================
// TYPES
// ============================================================
type DocType =
  | "oferta_comerciala"
  | "confirmare_comanda"
  | "contract"
  | "anexa_contract"
  | "factura_proforma"
  | "factura_fiscala"
  | "aviz"
  | "pv_predare_primire"
  | "pv_montaj"
  | "pv_receptie"
  | "certificat_garantie"
  | "certificat_conformitate"
  | "bun_de_tipar"
  | "fisa_tehnica"
  | "situatie_lucrari"
  | "nota_service"
  | "document_transport";

type DocStatus = "draft" | "generat" | "de_trimis" | "trimis" | "semnat" | "acceptat" | "expirat" | "arhivat";

type LinkedEntityType = "oferta" | "comanda" | "contract" | "factura";

interface MockDocument {
  id: string;
  code: string;
  type: DocType;
  typeLabel: string;
  version: number;
  client: string;
  linkedEntity: { type: string; id: string; route?: string; entityCategory: LinkedEntityType };
  status: DocStatus;
  statusLabel: string;
  signedAt?: string;
  generatedAt: string;
  lastSentAt?: string;
  responsible: string;
  notes?: string;
}

// ============================================================
// CONFIGS
// ============================================================
const docTypeLabels: Record<DocType, { label: string; icon: React.ReactNode }> = {
  oferta_comerciala: { label: "Ofertă comercială", icon: <FileText className="w-3.5 h-3.5 text-purple-400" /> },
  confirmare_comanda: { label: "Confirmare comandă", icon: <ClipboardList className="w-3.5 h-3.5 text-emerald-400" /> },
  contract: { label: "Contract", icon: <FileSignature className="w-3.5 h-3.5 text-blue-400" /> },
  anexa_contract: { label: "Anexă contract", icon: <BookOpen className="w-3.5 h-3.5 text-blue-300" /> },
  factura_proforma: { label: "Factură proformă", icon: <FileCheck className="w-3.5 h-3.5 text-amber-400" /> },
  factura_fiscala: { label: "Factură fiscală", icon: <FileCheck className="w-3.5 h-3.5 text-amber-500" /> },
  aviz: { label: "Aviz", icon: <Truck className="w-3.5 h-3.5 text-slate-400" /> },
  pv_predare_primire: { label: "PV predare-primire", icon: <Stamp className="w-3.5 h-3.5 text-emerald-400" /> },
  pv_montaj: { label: "PV montaj", icon: <Wrench className="w-3.5 h-3.5 text-cyan-400" /> },
  pv_receptie: { label: "PV recepție", icon: <CheckCircle2 className="w-3.5 h-3.5 text-emerald-400" /> },
  certificat_garantie: { label: "Certificat garanție", icon: <Shield className="w-3.5 h-3.5 text-blue-400" /> },
  certificat_conformitate: { label: "Certificat conformitate", icon: <Shield className="w-3.5 h-3.5 text-emerald-400" /> },
  bun_de_tipar: { label: "Bun de tipar", icon: <Printer className="w-3.5 h-3.5 text-purple-400" /> },
  fisa_tehnica: { label: "Fișă tehnică", icon: <BookOpen className="w-3.5 h-3.5 text-slate-400" /> },
  situatie_lucrari: { label: "Situație lucrări", icon: <Activity className="w-3.5 h-3.5 text-emerald-400" /> },
  nota_service: { label: "Notă service", icon: <Wrench className="w-3.5 h-3.5 text-amber-400" /> },
  document_transport: { label: "Document transport", icon: <Truck className="w-3.5 h-3.5 text-blue-400" /> },
};

const docStatusConfig: Record<DocStatus, { label: string; cls: string }> = {
  draft: { label: "Draft", cls: "bg-slate-700/60 text-slate-300 border-slate-600" },
  generat: { label: "Generat", cls: "bg-blue-900/40 text-blue-300 border-blue-700" },
  de_trimis: { label: "De trimis", cls: "bg-amber-900/40 text-amber-300 border-amber-700" },
  trimis: { label: "Trimis", cls: "bg-cyan-900/40 text-cyan-300 border-cyan-700" },
  semnat: { label: "Semnat", cls: "bg-emerald-900/40 text-emerald-300 border-emerald-700" },
  acceptat: { label: "Acceptat", cls: "bg-emerald-900/50 text-emerald-200 border-emerald-600" },
  expirat: { label: "Expirat", cls: "bg-red-900/40 text-red-300 border-red-700" },
  arhivat: { label: "Arhivat", cls: "bg-slate-800/60 text-slate-400 border-slate-600" },
};

// ============================================================
// HELPERS
// ============================================================
function formatDate(dateStr: string) {
  const d = new Date(dateStr);
  return d.toLocaleDateString("ro-RO", { day: "2-digit", month: "short", year: "numeric" });
}

function StatusBadge({ label, cls }: { label: string; cls: string }) {
  return (
    <span className={`inline-flex items-center px-2 py-0.5 text-[10px] font-semibold rounded border ${cls}`}>
      {label}
    </span>
  );
}

function DisabledActionBtn({ label, reason, icon }: { label: string; reason: string; icon?: React.ReactNode }) {
  return (
    <button
      disabled
      title={reason}
      className="group relative inline-flex items-center gap-1 px-2 py-1 text-[10px] font-medium rounded border border-slate-700/40 bg-slate-800/20 text-slate-600 cursor-not-allowed"
    >
      {icon || <Ban className="w-2.5 h-2.5" />}
      {label}
      <span className="absolute bottom-full left-1/2 -translate-x-1/2 mb-1 px-2 py-1 text-[9px] bg-slate-900 border border-slate-700 text-slate-400 rounded whitespace-nowrap opacity-0 group-hover:opacity-100 transition-opacity pointer-events-none z-50">
        {reason}
      </span>
    </button>
  );
}

// ============================================================
// MOCK DATA GENERATION from real quotes/orders
// ============================================================
function generateMockDocuments(quotes: Quote[], orders: Order[]): MockDocument[] {
  const docs: MockDocument[] = [];
  let idx = 1;

  for (const q of quotes) {
    docs.push({
      id: `DOC-${String(idx++).padStart(4, "0")}`,
      code: `OF-${q.id.replace("QT-", "")}`,
      type: "oferta_comerciala",
      typeLabel: "Ofertă comercială",
      version: q.version,
      client: q.client,
      linkedEntity: { type: "Ofertă", id: q.id, route: "/quotes", entityCategory: "oferta" },
      status: q.status === "accepted" ? "semnat" : q.status === "sent" ? "trimis" : q.status === "draft" ? "draft" : "generat",
      statusLabel: q.status === "accepted" ? "Semnat" : q.status === "sent" ? "Trimis" : q.status === "draft" ? "Draft" : "Generat",
      generatedAt: q.createdAt,
      lastSentAt: q.status === "sent" || q.status === "accepted" ? q.createdAt : undefined,
      signedAt: q.status === "accepted" ? q.createdAt : undefined,
      responsible: q.contactPerson || "Lipsă",
    });
  }

  for (const o of orders) {
    docs.push({
      id: `DOC-${String(idx++).padStart(4, "0")}`,
      code: `CC-${o.id.replace("ORD-", "")}`,
      type: "confirmare_comanda",
      typeLabel: "Confirmare comandă",
      version: 1,
      client: o.client,
      linkedEntity: { type: "Comandă", id: o.id, route: "/orders", entityCategory: "comanda" },
      status: o.status === "locked" || o.status === "in_execution" || o.status === "completed" ? "semnat" : "generat",
      statusLabel: o.status === "locked" || o.status === "in_execution" || o.status === "completed" ? "Semnat" : "Generat",
      generatedAt: o.createdAt,
      signedAt: o.lockedAt || undefined,
      responsible: o.client,
    });

    if (o.paymentStatus === "partial" || o.paymentStatus === "paid") {
      docs.push({
        id: `DOC-${String(idx++).padStart(4, "0")}`,
        code: `FP-${o.id.replace("ORD-", "")}`,
        type: "factura_proforma",
        typeLabel: "Factură proformă",
        version: 1,
        client: o.client,
        linkedEntity: { type: "Comandă", id: o.id, route: "/orders", entityCategory: "factura" },
        status: o.paymentStatus === "paid" ? "acceptat" : "trimis",
        statusLabel: o.paymentStatus === "paid" ? "Acceptat" : "Trimis",
        generatedAt: o.createdAt,
        lastSentAt: o.createdAt,
        responsible: o.client,
      });
    }

    if (o.status === "completed" || o.status === "in_execution") {
      docs.push({
        id: `DOC-${String(idx++).padStart(4, "0")}`,
        code: `PV-${o.id.replace("ORD-", "")}`,
        type: "pv_predare_primire",
        typeLabel: "PV predare-primire",
        version: 1,
        client: o.client,
        linkedEntity: { type: "Comandă", id: o.id, route: "/orders", entityCategory: "comanda" },
        status: o.status === "completed" ? "semnat" : "draft",
        statusLabel: o.status === "completed" ? "Semnat" : "Draft",
        generatedAt: o.createdAt,
        signedAt: o.status === "completed" ? o.createdAt : undefined,
        responsible: o.client,
      });
    }
  }

  return docs.sort((a, b) => b.generatedAt.localeCompare(a.generatedAt));
}

// ============================================================
// LIFECYCLE STAGES
// ============================================================
interface LifecycleStage {
  label: string;
  status: "existent" | "lipsa" | "draft" | "trimis" | "semnat" | "blocat" | "coming_soon";
}

function getLifecycleForOrder(order: Order, docs: MockDocument[]): LifecycleStage[] {
  const orderDocs = docs.filter((d) => d.linkedEntity.id === order.id);
  const hasConfirmation = orderDocs.some((d) => d.type === "confirmare_comanda");
  const hasProforma = orderDocs.some((d) => d.type === "factura_proforma");
  const hasPV = orderDocs.some((d) => d.type === "pv_predare_primire");

  return [
    { label: "Ofertă", status: order.quoteId ? "semnat" : "lipsa" },
    { label: "Accept client", status: order.quoteId ? "semnat" : "lipsa" },
    { label: "Confirmare comandă", status: hasConfirmation ? (order.lockedAt ? "semnat" : "draft") : "lipsa" },
    { label: "Contract / Anexă", status: "coming_soon" },
    { label: "Bun de tipar", status: "coming_soon" },
    { label: "Proces verbal", status: hasPV ? (order.status === "completed" ? "semnat" : "draft") : "lipsa" },
    { label: "Garanție", status: order.status === "completed" ? "draft" : "coming_soon" },
    { label: "Factură", status: hasProforma ? "trimis" : "lipsa" },
  ];
}

function getLifecycleForDocument(doc: MockDocument, orders: Order[], allDocs: MockDocument[]): LifecycleStage[] | null {
  // Find the related order for this document
  const relatedOrder = orders.find((o) => o.id === doc.linkedEntity.id);
  if (relatedOrder) {
    return getLifecycleForOrder(relatedOrder, allDocs);
  }
  // If linked to a quote, find order that references that quote
  const relatedOrderByQuote = orders.find((o) => o.quoteId === doc.linkedEntity.id);
  if (relatedOrderByQuote) {
    return getLifecycleForOrder(relatedOrderByQuote, allDocs);
  }
  return null;
}

const lifecycleStatusStyles: Record<string, { label: string; cls: string }> = {
  existent: { label: "Existent", cls: "text-blue-400 bg-blue-900/20 border-blue-800/30" },
  lipsa: { label: "Lipsă", cls: "text-slate-500 bg-slate-800/30 border-slate-700/30" },
  draft: { label: "Draft", cls: "text-amber-400 bg-amber-900/20 border-amber-800/30" },
  trimis: { label: "Trimis", cls: "text-cyan-400 bg-cyan-900/20 border-cyan-800/30" },
  semnat: { label: "Semnat", cls: "text-emerald-400 bg-emerald-900/20 border-emerald-800/30" },
  blocat: { label: "Blocat", cls: "text-red-400 bg-red-900/20 border-red-800/30" },
  coming_soon: { label: "Coming soon", cls: "text-slate-600 bg-slate-900/20 border-slate-800/30 italic" },
};

// ============================================================
// MAIN COMPONENT
// ============================================================
export default function DocumentCenter() {
  const navigate = useNavigate();
  const { quotes, orders, loading } = useBackendData();
  const [search, setSearch] = useState("");
  const [filterType, setFilterType] = useState<string>("all");
  const [filterStatus, setFilterStatus] = useState<string>("all");
  const [filterClient, setFilterClient] = useState<string>("all");
  const [filterLinkedTo, setFilterLinkedTo] = useState<string>("all");
  const [selectedDoc, setSelectedDoc] = useState<MockDocument | null>(null);

  // Generate mock documents from real data
  const documents = useMemo(() => generateMockDocuments(quotes, orders), [quotes, orders]);

  // Get unique clients
  const clients = useMemo(() => {
    const set = new Set(documents.map((d) => d.client));
    return Array.from(set).sort();
  }, [documents]);

  // Filter documents
  const filtered = useMemo(() => {
    return documents.filter((d) => {
      if (search && !d.code.toLowerCase().includes(search.toLowerCase()) && !d.client.toLowerCase().includes(search.toLowerCase()) && !d.typeLabel.toLowerCase().includes(search.toLowerCase())) return false;
      if (filterType !== "all" && d.type !== filterType) return false;
      if (filterStatus !== "all" && d.status !== filterStatus) return false;
      if (filterClient !== "all" && d.client !== filterClient) return false;
      if (filterLinkedTo !== "all" && d.linkedEntity.entityCategory !== filterLinkedTo) return false;
      return true;
    });
  }, [documents, search, filterType, filterStatus, filterClient, filterLinkedTo]);

  // Overview KPIs
  const kpis = useMemo(() => {
    const total = documents.length;
    const draft = documents.filter((d) => d.status === "draft").length;
    const deTrimis = documents.filter((d) => d.status === "de_trimis" || d.status === "generat").length;
    const deSemnat = documents.filter((d) => d.status === "trimis").length;
    const expirate = documents.filter((d) => d.status === "expirat").length;
    const arhivate = documents.filter((d) => d.status === "arhivat").length;
    return { total, draft, deTrimis, deSemnat, expirate, arhivate };
  }, [documents]);

  // Lifecycle for selected doc
  const lifecycle = useMemo(() => {
    if (!selectedDoc) return null;
    return getLifecycleForDocument(selectedDoc, orders, documents);
  }, [selectedDoc, orders, documents]);

  if (loading) {
    return (
      <div className="flex items-center justify-center py-20">
        <div className="animate-spin rounded-full h-10 w-10 border-b-2 border-blue-500" />
      </div>
    );
  }

  return (
    <div className="space-y-4">
      {/* HEADER */}
      <div className="flex items-start justify-between">
        <div>
          <h1 className="text-[20px] font-bold text-slate-100 flex items-center gap-2">
            <FileText className="w-5 h-5 text-blue-400" />
            Document Center
          </h1>
          <p className="text-[12px] text-slate-500 mt-0.5">
            Documente comerciale, contracte, facturi și acte operaționale.
          </p>
        </div>
        <div className="flex items-center gap-2">
          <DisabledActionBtn label="Generează document" reason="Necesită flow backend — generare automată indisponibilă în această versiune" icon={<FileText className="w-2.5 h-2.5" />} />
          <DisabledActionBtn label="Încarcă" reason="Necesită flow backend — upload de fișiere indisponibil în această versiune" icon={<Inbox className="w-2.5 h-2.5" />} />
          <DisabledActionBtn label="Șabloane" reason="Indisponibil în această versiune — management șabloane în pregătire" icon={<BookOpen className="w-2.5 h-2.5" />} />
          <DisabledActionBtn label="Export" reason="Indisponibil în această versiune — export bulk în pregătire" icon={<Download className="w-2.5 h-2.5" />} />
        </div>
      </div>

      {/* OVERVIEW CARDS */}
      <div className="grid grid-cols-7 gap-2">
        <KpiCard label="Total" value={kpis.total} color="text-slate-200" />
        <KpiCard label="Draft" value={kpis.draft} color="text-amber-400" />
        <KpiCard label="De trimis" value={kpis.deTrimis} color="text-blue-400" />
        <KpiCard label="De semnat" value={kpis.deSemnat} color="text-cyan-400" />
        <KpiCard label="Expirate" value={kpis.expirate} color="text-red-400" />
        <KpiCardComingSoon label="Lipsesc" />
        <KpiCard label="Arhivate" value={kpis.arhivate} color="text-slate-500" />
      </div>

      {/* COMMAND BAR */}
      <div className="bg-[#111827] border border-[#1E293B] rounded-lg px-4 py-3 flex items-center gap-3 flex-wrap">
        <div className="flex items-center gap-2 bg-[#0D1321] rounded-md px-3 py-1.5 border border-[#1E293B] w-56">
          <Search className="w-3.5 h-3.5 text-slate-500" />
          <input
            type="text"
            placeholder="Caută document..."
            value={search}
            onChange={(e) => setSearch(e.target.value)}
            className="bg-transparent text-[12px] text-slate-200 placeholder:text-slate-600 outline-none w-full"
          />
        </div>
        <select
          value={filterClient}
          onChange={(e) => setFilterClient(e.target.value)}
          className="bg-[#0D1321] border border-[#1E293B] rounded-md px-2 py-1.5 text-[11px] text-slate-300 outline-none"
        >
          <option value="all">Toți clienții</option>
          {clients.map((c) => <option key={c} value={c}>{c}</option>)}
        </select>
        <select
          value={filterType}
          onChange={(e) => setFilterType(e.target.value)}
          className="bg-[#0D1321] border border-[#1E293B] rounded-md px-2 py-1.5 text-[11px] text-slate-300 outline-none"
        >
          <option value="all">Toate tipurile</option>
          {Object.entries(docTypeLabels).map(([key, val]) => (
            <option key={key} value={key}>{val.label}</option>
          ))}
        </select>
        <select
          value={filterStatus}
          onChange={(e) => setFilterStatus(e.target.value)}
          className="bg-[#0D1321] border border-[#1E293B] rounded-md px-2 py-1.5 text-[11px] text-slate-300 outline-none"
        >
          <option value="all">Toate statusurile</option>
          {Object.entries(docStatusConfig).map(([key, val]) => (
            <option key={key} value={key}>{val.label}</option>
          ))}
        </select>
        <select
          value={filterLinkedTo}
          onChange={(e) => setFilterLinkedTo(e.target.value)}
          className="bg-[#0D1321] border border-[#1E293B] rounded-md px-2 py-1.5 text-[11px] text-slate-300 outline-none"
        >
          <option value="all">Legat de: toate</option>
          <option value="oferta">Ofertă</option>
          <option value="comanda">Comandă</option>
          <option value="contract">Contract</option>
          <option value="factura">Factură</option>
        </select>
        <div className="ml-auto text-[11px] text-slate-600 flex items-center gap-1">
          <Filter className="w-3 h-3" />
          {filtered.length} / {documents.length} documente
        </div>
      </div>

      {/* MAIN CONTENT: Table + Side Panel */}
      <div className="flex gap-3">
        {/* TABLE */}
        <div className="flex-1 min-w-0">
          {filtered.length === 0 ? (
            <div className="bg-[#111827] border border-[#1E293B] rounded-lg p-8 text-center">
              <FileText className="w-8 h-8 text-slate-700 mx-auto mb-2" />
              <p className="text-[12px] text-slate-500">Nu există documente care să corespundă filtrelor.</p>
            </div>
          ) : (
            <div className="bg-[#111827] border border-[#1E293B] rounded-lg overflow-hidden">
              {/* Table header */}
              <div className="grid grid-cols-[140px_1fr_130px_90px_80px_80px_100px] gap-2 px-4 py-2 border-b border-[#1E293B] text-[9px] font-bold uppercase tracking-wider text-slate-600">
                <span>Cod / Tip</span>
                <span>Client</span>
                <span>Legat de</span>
                <span>Status</span>
                <span>Generat</span>
                <span>Trimis</span>
                <span>Acțiuni</span>
              </div>
              {/* Table rows */}
              {filtered.map((doc) => (
                <div
                  key={doc.id}
                  className={`grid grid-cols-[140px_1fr_130px_90px_80px_80px_100px] gap-2 px-4 py-2.5 border-b border-[#1E293B]/50 hover:bg-slate-800/30 transition-colors ${
                    selectedDoc?.id === doc.id ? "bg-blue-900/10 border-l-2 border-l-blue-500" : ""
                  }`}
                >
                  <div className="flex items-center gap-1.5 min-w-0">
                    {docTypeLabels[doc.type]?.icon}
                    <div className="min-w-0">
                      <p className="text-[11px] font-mono font-semibold text-slate-200 truncate">{doc.code}</p>
                      <p className="text-[9px] text-slate-600 truncate">{doc.typeLabel} v{doc.version}</p>
                    </div>
                  </div>
                  <div className="flex items-center">
                    <span className="text-[11px] text-slate-400 truncate">{doc.client}</span>
                  </div>
                  <div className="flex items-center">
                    {doc.linkedEntity.route ? (
                      <button
                        onClick={(e) => { e.stopPropagation(); navigate(doc.linkedEntity.route!); }}
                        className="text-[10px] text-blue-400 hover:text-blue-300 truncate flex items-center gap-1"
                      >
                        <ExternalLink className="w-2.5 h-2.5 shrink-0" />
                        {doc.linkedEntity.type}: {doc.linkedEntity.id}
                      </button>
                    ) : (
                      <span className="text-[10px] text-slate-600 truncate">{doc.linkedEntity.type}: {doc.linkedEntity.id}</span>
                    )}
                  </div>
                  <div className="flex items-center">
                    <StatusBadge label={docStatusConfig[doc.status].label} cls={docStatusConfig[doc.status].cls} />
                  </div>
                  <div className="flex items-center">
                    <span className="text-[10px] text-slate-500">{formatDate(doc.generatedAt)}</span>
                  </div>
                  <div className="flex items-center">
                    <span className="text-[10px] text-slate-600">{doc.lastSentAt ? formatDate(doc.lastSentAt) : "Lipsă"}</span>
                  </div>
                  <div className="flex items-center gap-1">
                    <RowAction icon={<Eye className="w-3 h-3" />} label="Vezi" reason="Vizualizare PDF necesită flow backend" />
                    <RowAction icon={<Download className="w-3 h-3" />} label="Descarcă" reason="Download necesită flow backend" />
                    <RowAction icon={<Send className="w-3 h-3" />} label="Trimite" reason="Trimitere email necesită flow backend" />
                    <RowAction icon={<CheckCircle2 className="w-3 h-3" />} label="Semnat" reason="Marcare semnat necesită flow backend" />
                    <button
                      onClick={() => setSelectedDoc(doc)}
                      title="Detalii document"
                      className="p-1 rounded text-blue-400 hover:bg-blue-900/20 hover:text-blue-300 transition-colors"
                    >
                      <Info className="w-3 h-3" />
                    </button>
                  </div>
                </div>
              ))}
            </div>
          )}
        </div>

        {/* SIDE PANEL: Lifecycle + Detail Drawer */}
        <div className="w-[320px] shrink-0 space-y-3">
          {/* Lifecycle Panel — shows for selected doc */}
          {selectedDoc && lifecycle ? (
            <LifecyclePanel
              title={`Lifecycle: ${selectedDoc.linkedEntity.id}`}
              subtitle={selectedDoc.client}
              stages={lifecycle}
            />
          ) : selectedDoc && !lifecycle ? (
            <div className="bg-[#111827] border border-[#1E293B] rounded-lg p-3">
              <h3 className="text-[11px] font-semibold text-slate-300 mb-2 flex items-center gap-1.5">
                <Activity className="w-3.5 h-3.5 text-emerald-400" />
                Lifecycle Documente
              </h3>
              <p className="text-[10px] text-slate-600">
                Nu se poate determina ciclul de viață pentru acest document. Selectează un document legat de o comandă.
              </p>
            </div>
          ) : orders.length > 0 ? (
            <div className="bg-[#111827] border border-[#1E293B] rounded-lg p-3">
              <h3 className="text-[11px] font-semibold text-slate-300 mb-2 flex items-center gap-1.5">
                <Activity className="w-3.5 h-3.5 text-emerald-400" />
                Lifecycle Documente
              </h3>
              <p className="text-[10px] text-slate-600 mb-2">Selectează un document din tabel pentru a vedea ciclul de viață complet.</p>
              <div className="space-y-1">
                {orders.slice(0, 4).map((o) => {
                  const stages = getLifecycleForOrder(o, documents);
                  const completedCount = stages.filter((s) => s.status === "semnat" || s.status === "trimis").length;
                  return (
                    <div key={o.id} className="flex items-center gap-2 px-2 py-1.5 rounded bg-[#0D1321]">
                      <ClipboardList className="w-3 h-3 text-emerald-400 shrink-0" />
                      <span className="text-[10px] font-mono text-emerald-400">{o.id}</span>
                      <span className="text-[9px] text-slate-600 truncate flex-1">{o.productSummary}</span>
                      <span className="text-[9px] text-slate-500">{completedCount}/{stages.length}</span>
                    </div>
                  );
                })}
              </div>
            </div>
          ) : null}

          {/* Detail Drawer */}
          {selectedDoc && (
            <DetailDrawer doc={selectedDoc} navigate={navigate} onClose={() => setSelectedDoc(null)} />
          )}
        </div>
      </div>
    </div>
  );
}

// ============================================================
// ROW ACTION (disabled with tooltip)
// ============================================================
function RowAction({ icon, label, reason }: { icon: React.ReactNode; label: string; reason: string }) {
  return (
    <button
      disabled
      title={`${label}: ${reason}`}
      className="p-1 rounded text-slate-700 cursor-not-allowed hover:text-slate-600"
    >
      {icon}
    </button>
  );
}

// ============================================================
// KPI CARD
// ============================================================
function KpiCard({ label, value, color }: { label: string; value: number; color: string }) {
  return (
    <div className="bg-[#111827] border border-[#1E293B] rounded-lg px-3 py-2.5 text-center">
      <p className={`text-[18px] font-bold ${color}`}>{value}</p>
      <p className="text-[9px] text-slate-600 uppercase tracking-wide mt-0.5">{label}</p>
    </div>
  );
}

function KpiCardComingSoon({ label }: { label: string }) {
  return (
    <div className="bg-[#111827] border border-slate-700/30 rounded-lg px-3 py-2.5 text-center" title="Detecție documente lipsă în pregătire">
      <div className="flex items-center justify-center gap-1">
        <AlertCircle className="w-3.5 h-3.5 text-slate-600" />
      </div>
      <p className="text-[9px] text-slate-600 uppercase tracking-wide mt-1">{label}</p>
      <p className="text-[8px] text-slate-700 italic mt-0.5">în pregătire</p>
    </div>
  );
}

// ============================================================
// LIFECYCLE PANEL
// ============================================================
function LifecyclePanel({ title, subtitle, stages }: { title: string; subtitle: string; stages: LifecycleStage[] }) {
  const completed = stages.filter((s) => s.status === "semnat" || s.status === "trimis" || s.status === "existent").length;
  const total = stages.length;

  return (
    <div className="bg-[#111827] border border-[#1E293B] rounded-lg p-3">
      <div className="flex items-center justify-between mb-1">
        <h3 className="text-[11px] font-semibold text-slate-300 flex items-center gap-1.5">
          <Activity className="w-3.5 h-3.5 text-emerald-400" />
          {title}
        </h3>
        <span className="text-[9px] text-slate-500">{completed}/{total} completate</span>
      </div>
      <p className="text-[10px] text-slate-600 mb-3">{subtitle}</p>

      {/* Progress bar */}
      <div className="h-1.5 bg-slate-800 rounded-full mb-3 overflow-hidden">
        <div
          className="h-full bg-emerald-500/60 rounded-full transition-all"
          style={{ width: `${(completed / total) * 100}%` }}
        />
      </div>

      <div className="space-y-1">
        {stages.map((stage, idx) => {
          const style = lifecycleStatusStyles[stage.status];
          return (
            <div key={idx} className="flex items-center justify-between px-2 py-1.5 rounded bg-[#0D1321]">
              <div className="flex items-center gap-2">
                <span className="text-[9px] text-slate-700 w-3">{idx + 1}.</span>
                <span className="text-[11px] text-slate-400">{stage.label}</span>
              </div>
              <span className={`text-[9px] px-1.5 py-0.5 rounded border font-semibold ${style.cls}`}>
                {style.label}
              </span>
            </div>
          );
        })}
      </div>
    </div>
  );
}

// ============================================================
// DETAIL DRAWER
// ============================================================
function DetailDrawer({ doc, navigate, onClose }: { doc: MockDocument; navigate: ReturnType<typeof useNavigate>; onClose: () => void }) {
  return (
    <div className="bg-[#111827] border border-[#1E293B] rounded-lg p-4">
      <div className="flex items-center justify-between mb-3">
        <h3 className="text-[13px] font-semibold text-slate-200 flex items-center gap-2">
          {docTypeLabels[doc.type]?.icon}
          {doc.code}
        </h3>
        <button onClick={onClose} className="text-slate-600 hover:text-slate-400">
          <X className="w-3.5 h-3.5" />
        </button>
      </div>

      {/* Document info */}
      <div className="space-y-2 mb-4">
        <InfoRow label="Cod document" value={doc.code} />
        <InfoRow label="Tip document" value={doc.typeLabel} />
        <InfoRow label="Versiune" value={`v${doc.version}`} />
        <InfoRow label="Client" value={doc.client} />
        <InfoRow label="Status">
          <StatusBadge label={docStatusConfig[doc.status].label} cls={docStatusConfig[doc.status].cls} />
        </InfoRow>
        <InfoRow label="Dată generare" value={formatDate(doc.generatedAt)} />
        <InfoRow label="Dată trimitere" value={doc.lastSentAt ? formatDate(doc.lastSentAt) : "Lipsă"} />
        <InfoRow label="Responsabil" value={doc.responsible} />
        <InfoRow label="Semnare/Acceptare" value={doc.signedAt ? formatDate(doc.signedAt) : "Lipsă"} />
      </div>

      {/* Linked entity */}
      <div className="border-t border-[#1E293B] pt-3 mb-3">
        <p className="text-[10px] text-slate-600 uppercase font-semibold mb-1.5">Entitate legată</p>
        {doc.linkedEntity.route ? (
          <button
            onClick={() => navigate(doc.linkedEntity.route!)}
            className="flex items-center gap-1.5 text-[11px] text-blue-400 hover:text-blue-300"
          >
            <ExternalLink className="w-3 h-3" />
            {doc.linkedEntity.type}: {doc.linkedEntity.id}
          </button>
        ) : (
          <span className="text-[11px] text-slate-600">{doc.linkedEntity.type}: {doc.linkedEntity.id} — rută indisponibilă</span>
        )}
      </div>

      {/* Istoric acțiuni */}
      <div className="border-t border-[#1E293B] pt-3 mb-3">
        <p className="text-[10px] text-slate-600 uppercase font-semibold mb-1.5">Istoric acțiuni</p>
        <p className="text-[10px] text-slate-600 italic">Indisponibil — necesită flow backend pentru tracking acțiuni.</p>
      </div>

      {/* Cross-links */}
      <div className="border-t border-[#1E293B] pt-3 mb-3">
        <p className="text-[10px] text-slate-600 uppercase font-semibold mb-1.5">Navigare</p>
        <div className="space-y-1">
          <CrossLink label="Client Workspace" route={`/clients/${encodeURIComponent(doc.client)}`} navigate={navigate} icon={<Users className="w-3 h-3" />} />
          <CrossLink label="Oferte" route="/quotes" navigate={navigate} icon={<FileText className="w-3 h-3" />} />
          <CrossLink label="Comenzi" route="/orders" navigate={navigate} icon={<ClipboardList className="w-3 h-3" />} />
          <CrossLink label="Execuție" route="/execution" navigate={navigate} icon={<Activity className="w-3 h-3" />} />
          <CrossLinkDisabled label="Contracte" reason="Modulul de contracte nu este implementat în această versiune" />
          <CrossLinkDisabled label="Facturi" reason="Modulul de facturare nu este implementat în această versiune" />
        </div>
      </div>

      {/* Actions */}
      <div className="border-t border-[#1E293B] pt-3">
        <p className="text-[10px] text-slate-600 uppercase font-semibold mb-1.5">Acțiuni disponibile</p>
        <div className="flex flex-wrap gap-1.5">
          <DisabledActionBtn label="Vezi PDF" reason="Necesită flow backend — vizualizare PDF indisponibilă" icon={<Eye className="w-2.5 h-2.5" />} />
          <DisabledActionBtn label="Descarcă" reason="Necesită flow backend — download indisponibil" icon={<Download className="w-2.5 h-2.5" />} />
          <DisabledActionBtn label="Trimite" reason="Necesită flow backend — trimitere email indisponibilă" icon={<Send className="w-2.5 h-2.5" />} />
          <DisabledActionBtn label="Marchează trimis" reason="Necesită flow backend — actualizare status indisponibilă" icon={<Send className="w-2.5 h-2.5" />} />
          <DisabledActionBtn label="Marchează semnat" reason="Necesită flow backend — actualizare status indisponibilă" icon={<CheckCircle2 className="w-2.5 h-2.5" />} />
          <DisabledActionBtn label="Încarcă semnat" reason="Necesită flow backend — upload fișiere indisponibil" icon={<Inbox className="w-2.5 h-2.5" />} />
          <DisabledActionBtn label="Regenerare" reason="Necesită flow backend — regenerare document indisponibilă" icon={<FileText className="w-2.5 h-2.5" />} />
          <DisabledActionBtn label="Arhivează" reason="Necesită flow backend — arhivare indisponibilă" icon={<Ban className="w-2.5 h-2.5" />} />
        </div>
      </div>

      {/* Notes */}
      <div className="border-t border-[#1E293B] pt-3 mt-3">
        <p className="text-[10px] text-slate-600 uppercase font-semibold mb-1">Note interne</p>
        <p className="text-[10px] text-slate-600 italic">Indisponibil — adăugarea de note necesită flow backend.</p>
      </div>
    </div>
  );
}

function InfoRow({ label, value, children }: { label: string; value?: string; children?: React.ReactNode }) {
  return (
    <div className="flex items-center justify-between">
      <span className="text-[10px] text-slate-600">{label}</span>
      {children || <span className="text-[11px] text-slate-300">{value}</span>}
    </div>
  );
}

function CrossLink({ label, route, navigate, icon }: { label: string; route: string; navigate: ReturnType<typeof useNavigate>; icon: React.ReactNode }) {
  return (
    <button
      onClick={() => navigate(route)}
      className="w-full flex items-center gap-2 px-2 py-1 rounded text-[11px] text-blue-400 hover:bg-blue-900/15 hover:text-blue-300 transition-colors text-left"
    >
      {icon}
      {label}
      <ChevronRight className="w-3 h-3 ml-auto text-slate-700" />
    </button>
  );
}

function CrossLinkDisabled({ label, reason }: { label: string; reason: string }) {
  return (
    <div title={reason} className="w-full flex items-center gap-2 px-2 py-1 rounded text-[11px] text-slate-600 cursor-not-allowed">
      <Ban className="w-3 h-3" />
      {label}
      <span className="ml-auto text-[9px] text-slate-700">indisponibil</span>
    </div>
  );
}