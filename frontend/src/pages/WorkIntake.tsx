import { useEffect, useMemo, useState } from "react";
import { useNavigate } from "react-router-dom";
import { type IntakeRequest, type IntakeStatus, type DeliveryType, deliveryTypeLabels } from "@/lib/mockData";
import { useBackendData } from "@/hooks/useBackendData";
import { SectionHeader } from "@/components/workos/SharedComponents";
import { SourceBadge, StatusBadge } from "@/components/workos/design-system";
import NewIntakeDialog from "@/components/workos/NewIntakeDialog";
import { navigateToQuoteDetail } from "@/lib/commercialSpineNavigation";
import { createDraftQuoteFromIntake, updateIntakeStatus } from "@/lib/dataStore";
import { formatIntakeProductFamilyLabel } from "@/lib/intakeProductFamilyDisplay";
import { patchIntakeByCode } from "@/lib/intakePersistence";
import {
  intakePrimaryEditLabel,
  resolveIntakeEditPath,
} from "@/lib/volumetricIntakeRoute";
import { paginateWorkIntakeList } from "@/lib/workIntakeListPagination";
import { useAuth } from "@/contexts/AuthContext";
import { canCreateIntakeRequest } from "@/lib/apiError";
import {
  Inbox,
  Search,
  Eye,
  Clock,
  AlertTriangle,
  CheckCircle2,
  XCircle,
  Phone,
  Mail,
  Globe,
  User,
  ChevronRight,
  ArrowRight,
  MessageSquare,
  FileEdit,
  Truck,
  Plus,
} from "lucide-react";

const statusConfig: Record<IntakeStatus, { label: string; cls: string; icon: React.ReactNode }> = {
  new: { label: "Nou", cls: "bg-slate-700/60 text-slate-300 border-slate-600", icon: <Inbox className="w-3 h-3" /> },
  in_review: { label: "În Analiză", cls: "bg-blue-900/40 text-blue-300 border-blue-700", icon: <Eye className="w-3 h-3" /> },
  needs_info: { label: "Lipsă Info", cls: "bg-amber-900/40 text-amber-300 border-amber-700", icon: <AlertTriangle className="w-3 h-3" /> },
  ready_for_quote: { label: "Gata pt. Ofertă", cls: "bg-emerald-900/40 text-emerald-300 border-emerald-700", icon: <CheckCircle2 className="w-3 h-3" /> },
  blocked: { label: "Blocat", cls: "bg-red-900/40 text-red-300 border-red-700", icon: <XCircle className="w-3 h-3" /> },
  cancelled: { label: "Anulat", cls: "bg-slate-800/60 text-slate-400 border-slate-600", icon: <XCircle className="w-3 h-3" /> },
};

const channelIcon: Record<string, React.ReactNode> = {
  email: <Mail className="w-3 h-3" />,
  phone: <Phone className="w-3 h-3" />,
  walk_in: <User className="w-3 h-3" />,
  web_form: <Globe className="w-3 h-3" />,
};

function IntakeStatusBadge({ status }: { status: IntakeStatus }) {
  const cfg = statusConfig[status];
  if (!cfg) {
    return (
      <StatusBadge domain="intake" status={status} className="text-[11px]" />
    );
  }
  return (
    <StatusBadge
      domain="intake"
      status={status}
      label={cfg.label}
      icon={cfg.icon}
      className="text-[11px]"
    />
  );
}

function PipelineCard({ status, count, active }: { status: IntakeStatus; count: number; active: boolean }) {
  const cfg = statusConfig[status];
  return (
    <div className={`bg-[#1A2236] border rounded-lg p-3 transition-all cursor-pointer ${
      active ? "border-blue-500/50 ring-1 ring-blue-500/30" : "border-[#2A3548] hover:border-slate-500"
    }`}>
      <div className="flex items-center gap-2 mb-1">
        <span className={`${cfg.cls.includes("text-blue") ? "text-blue-400" : cfg.cls.includes("text-emerald") ? "text-emerald-400" : cfg.cls.includes("text-amber") ? "text-amber-400" : cfg.cls.includes("text-red") ? "text-red-400" : "text-slate-400"}`}>
          {cfg.icon}
        </span>
        <span className="text-[12px] font-semibold text-slate-200">{cfg.label}</span>
      </div>
      <p className="text-[24px] font-bold text-slate-100">{count}</p>
    </div>
  );
}

export default function WorkIntake() {
  const navigate = useNavigate();
  const { user } = useAuth();
  const { intakes: intakeRequests, loading, error, source, sourcesDetail, refresh } = useBackendData();
  const intakeSource = sourcesDetail.intakes ?? source;
  const canMutateIntake = intakeSource === "db" || intakeSource === "empty";
  const canCreateIntake = canCreateIntakeRequest(
    typeof user?.role === "string" ? user.role : undefined
  );
  const [selectedStatus, setSelectedStatus] = useState<IntakeStatus | "all">("all");
  const [selectedRequest, setSelectedRequest] = useState<IntakeRequest | null>(null);
  const [searchQuery, setSearchQuery] = useState("");
  const [newDialogOpen, setNewDialogOpen] = useState(false);
  const [statusActionLoading, setStatusActionLoading] = useState(false);
  const [draftQuoteError, setDraftQuoteError] = useState<string | null>(null);
  const [draftQuoteLoading, setDraftQuoteLoading] = useState(false);
  const [listPage, setListPage] = useState(1);

  const filtered = useMemo(() => {
    return intakeRequests.filter((r) => {
      if (selectedStatus !== "all" && r.status !== selectedStatus) return false;
      if (searchQuery.trim()) {
        const q = searchQuery.toLowerCase();
        return (
          r.client.toLowerCase().includes(q) ||
          r.id.toLowerCase().includes(q) ||
          r.description.toLowerCase().includes(q)
        );
      }
      return true;
    });
  }, [intakeRequests, searchQuery, selectedStatus]);

  const listPagination = useMemo(
    () => paginateWorkIntakeList(filtered, listPage),
    [filtered, listPage]
  );

  useEffect(() => {
    setListPage(1);
  }, [searchQuery, selectedStatus]);

  useEffect(() => {
    if (listPage !== listPagination.page) {
      setListPage(listPagination.page);
    }
  }, [listPage, listPagination.page]);

  useEffect(() => {
    if (selectedRequest && !filtered.some((r) => r.id === selectedRequest.id)) {
      setSelectedRequest(null);
      setDraftQuoteError(null);
    }
  }, [filtered, selectedRequest]);

  if (loading && intakeRequests.length === 0) {
    return (
      <div className="flex items-center justify-center h-64">
        <div className="text-center">
          <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-blue-500 mx-auto mb-2"></div>
          <p className="text-[12px] text-slate-500">Încărcare cereri...</p>
        </div>
      </div>
    );
  }

  const pipelineStatuses: IntakeStatus[] = ["new", "in_review", "needs_info", "ready_for_quote", "blocked"];
  const pipelineCounts = pipelineStatuses.map((s) => ({
    status: s,
    count: intakeRequests.filter((r) => r.status === s).length,
  }));

  return (
    <div className="space-y-4">
      {/* Header */}
      <div className="flex items-center justify-between">
        <div className="flex items-center gap-2">
          <Inbox className="w-5 h-5 text-orange-400" />
          <h1 className="text-[18px] font-bold text-slate-100">Work Intake</h1>
          <SourceBadge source={intakeSource} />
          <span className="text-[10px] text-slate-500 bg-slate-800 px-2 py-0.5 rounded-full ml-1">
            {intakeRequests.length} cereri
          </span>
        </div>
        <button
          onClick={() => setNewDialogOpen(true)}
          disabled={!canMutateIntake || !canCreateIntake}
          title={
            !canCreateIntake
              ? "Crearea cererilor necesită cont admin/manager/sales — folosește http://127.0.0.1:3001"
              : undefined
          }
          className="flex items-center gap-1.5 px-3 py-2 bg-emerald-600 hover:bg-emerald-500 text-white rounded-lg text-[12px] font-bold transition-colors shadow-lg shadow-emerald-900/20 disabled:opacity-50 disabled:cursor-not-allowed"
        >
          <Plus className="w-3.5 h-3.5" />
          Cerere Nouă
        </button>
      </div>

      <NewIntakeDialog
        open={newDialogOpen}
        onClose={() => setNewDialogOpen(false)}
        onCreated={async (code, productFamily) => {
          await refresh();
          navigate(
            resolveIntakeEditPath({
              id: code,
              productFamily: productFamily ?? null,
            })
          );
        }}
      />

      {error && source !== "mock" && (
        <div className="flex items-center gap-2 px-3 py-2 bg-red-900/20 border border-red-800/40 rounded-lg">
          <AlertTriangle className="w-4 h-4 text-red-400 shrink-0" />
          <p className="text-[12px] text-red-300">
            Datele operaționale nu au putut fi încărcate din backend: {error}
          </p>
        </div>
      )}

      {!canMutateIntake && (
        <div className="flex items-start gap-2 px-3 py-2 bg-amber-900/15 border border-amber-800/30 rounded-lg">
          <AlertTriangle className="w-4 h-4 text-amber-400 mt-0.5 shrink-0" />
          <p className="text-[11px] text-amber-300/90">
            Acțiunile de creare/modificare intake sunt disponibile doar pe sursă backend live.
          </p>
        </div>
      )}

      {canMutateIntake && !canCreateIntake && (
        <div className="flex items-start gap-2 px-3 py-2 bg-amber-900/15 border border-amber-800/30 rounded-lg">
          <AlertTriangle className="w-4 h-4 text-amber-400 mt-0.5 shrink-0" />
          <p className="text-[11px] text-amber-300/90">
            Contul curent ({typeof user?.role === "string" ? user.role : "necunoscut"}) nu poate crea cereri Work Intake.
            Folosește aplicația operator/comercial pe{" "}
            <a href="http://127.0.0.1:3001" className="underline text-amber-200">
              http://127.0.0.1:3001
            </a>
            .
          </p>
        </div>
      )}

      {/* Pipeline */}
      <div className="grid grid-cols-2 md:grid-cols-5 gap-3">
        {pipelineCounts.map((p) => (
          <div
            key={p.status}
            onClick={() => {
              setSelectedStatus(selectedStatus === p.status ? "all" : p.status);
              setListPage(1);
            }}
          >
            <PipelineCard status={p.status} count={p.count} active={selectedStatus === p.status} />
          </div>
        ))}
      </div>

      {/* Search + Filter */}
      <div className="flex items-center gap-3">
        <div className="flex items-center gap-2 bg-[#111827] border border-[#1E293B] rounded-lg px-3 py-2 flex-1 max-w-md focus-within:border-blue-500/50">
          <Search className="w-4 h-4 text-slate-500" />
          <input
            id="work-intake-search"
            name="work-intake-search"
            type="text"
            value={searchQuery}
            onChange={(e) => {
              setSearchQuery(e.target.value);
              setListPage(1);
            }}
            placeholder="Caută client, ID, descriere..."
            className="bg-transparent text-[13px] text-slate-200 placeholder:text-slate-600 outline-none w-full"
          />
        </div>
        {selectedStatus !== "all" && (
          <button onClick={() => setSelectedStatus("all")} className="text-[11px] text-slate-400 hover:text-slate-200 transition-colors">
            Resetează filtru
          </button>
        )}
        <span className="text-[11px] text-slate-500 ml-auto">
          {filtered.length} rezultate · {listPagination.rangeLabel}
        </span>
      </div>

      <div
        className="grid grid-cols-1 lg:grid-cols-3 gap-4 items-start"
        data-testid="work-intake-list-layout"
      >
        {/* Request List */}
        <div className="lg:col-span-2 space-y-2">
          {listPagination.items.map((req) => (
            <div
              key={req.id}
              role="button"
              tabIndex={0}
              onClick={() => {
                setSelectedRequest(req);
                setDraftQuoteError(null);
              }}
              onKeyDown={(e) => {
                if (e.key === "Enter" || e.key === " ") {
                  e.preventDefault();
                  setSelectedRequest(req);
                  setDraftQuoteError(null);
                }
              }}
              className={`bg-[#111827] border rounded-lg p-3 cursor-pointer transition-all ${
                selectedRequest?.id === req.id ? "border-blue-500/50 ring-1 ring-blue-500/30" : "border-[#1E293B] hover:border-slate-500"
              }`}
              data-testid={`work-intake-row-${req.id}`}
            >
              <div className="flex items-center gap-3">
                <div className="flex-1 min-w-0">
                  <div className="flex items-center gap-2 mb-1">
                    <span className="text-[12px] font-mono text-blue-400">{req.id}</span>
                    <IntakeStatusBadge status={req.status} />
                    <span className={`px-1.5 py-0.5 text-[10px] font-bold rounded ${
                      req.priority === "urgent" ? "bg-red-600 text-white" :
                      req.priority === "high" ? "bg-amber-600 text-white" :
                      "bg-slate-700 text-slate-300"
                    }`}>
                      {req.priority.toUpperCase()}
                    </span>
                  </div>
                  <p className="text-[13px] font-semibold text-slate-200">{req.client}</p>
                  <p className="text-[11px] text-slate-400 truncate mt-0.5">{req.description}</p>
                  <div className="flex items-center gap-3 mt-1.5 text-[10px] text-slate-500">
                    <span className="flex items-center gap-1">{channelIcon[req.channel]} {req.channel}</span>
                    <span>{formatIntakeProductFamilyLabel(req.productFamily)}</span>
                    <span>Qty: {req.quantity}</span>
                    <span className="flex items-center gap-1"><Truck className="w-3 h-3" />{deliveryTypeLabels[req.deliveryType]}</span>
                    <span>{req.assignedTo !== "—" ? req.assignedTo : "Neasignat"}</span>
                  </div>
                </div>
                <ChevronRight className="w-4 h-4 text-slate-600 shrink-0" />
              </div>
            </div>
          ))}
          {filtered.length === 0 && (
            <div className="bg-[#111827] border border-[#1E293B] rounded-lg p-8 text-center text-slate-500 text-[13px]">
              Nicio cerere găsită.
            </div>
          )}

          {filtered.length > 0 && (
            <div
              className="flex flex-wrap items-center justify-between gap-2 pt-2 border-t border-[#1E293B]/80"
              data-testid="work-intake-pagination"
            >
              <p className="text-[11px] text-slate-500" data-testid="work-intake-pagination-range">
                {listPagination.rangeLabel}
              </p>
              <p className="text-[11px] text-slate-400" data-testid="work-intake-pagination-page">
                {listPagination.pageLabel}
              </p>
              <div className="flex items-center gap-2">
                <button
                  type="button"
                  data-testid="work-intake-pagination-prev"
                  disabled={listPagination.page <= 1}
                  onClick={() => setListPage((p) => Math.max(1, p - 1))}
                  className="px-3 py-1.5 text-[11px] font-semibold rounded-lg border border-[#2A3548] text-slate-300 hover:border-slate-500 disabled:opacity-40 disabled:cursor-not-allowed"
                >
                  Anterior
                </button>
                <button
                  type="button"
                  data-testid="work-intake-pagination-next"
                  disabled={listPagination.page >= listPagination.totalPages}
                  onClick={() =>
                    setListPage((p) => Math.min(listPagination.totalPages, p + 1))
                  }
                  className="px-3 py-1.5 text-[11px] font-semibold rounded-lg border border-[#2A3548] text-slate-300 hover:border-slate-500 disabled:opacity-40 disabled:cursor-not-allowed"
                >
                  Următor
                </button>
              </div>
            </div>
          )}
        </div>

        {/* Detail Panel — sticky on large screens while main content scrolls */}
        <div
          className="space-y-4 lg:sticky lg:top-4 lg:max-h-[calc(100vh-2rem)] lg:overflow-y-auto lg:self-start"
          data-testid="work-intake-detail-panel"
        >
          {selectedRequest ? (
            <>
              <div className="bg-[#111827] border border-[#1E293B] rounded-lg p-4">
                <div className="flex items-center justify-between mb-3">
                  <span className="text-[12px] font-mono text-blue-400">{selectedRequest.id}</span>
                  <IntakeStatusBadge status={selectedRequest.status} />
                </div>
                <h3 className="text-[16px] font-bold text-slate-100">{selectedRequest.client}</h3>
                <p className="text-[12px] text-slate-400 mt-1">{selectedRequest.contactPerson}</p>

                <div className="mt-4 space-y-3">
                  <div>
                    <p className="text-[10px] text-slate-500 uppercase tracking-wide mb-1">Descriere</p>
                    <p className="text-[12px] text-slate-300 leading-relaxed">{selectedRequest.description}</p>
                  </div>
                  <div className="grid grid-cols-2 gap-3">
                    <div>
                      <p className="text-[10px] text-slate-500 uppercase tracking-wide mb-1">Dimensiuni</p>
                      <p className="text-[12px] text-slate-300 font-mono">{selectedRequest.dimensions}</p>
                    </div>
                    <div>
                      <p className="text-[10px] text-slate-500 uppercase tracking-wide mb-1">Cantitate</p>
                      <p className="text-[12px] text-slate-300">{selectedRequest.quantity} buc</p>
                    </div>
                  </div>
                  <div className="grid grid-cols-2 gap-3">
                    <div>
                      <p className="text-[10px] text-slate-500 uppercase tracking-wide mb-1">Familie Produs</p>
                      <p className="text-[12px] text-slate-300">
                        {formatIntakeProductFamilyLabel(selectedRequest.productFamily)}
                      </p>
                    </div>
                    <div>
                      <p className="text-[10px] text-slate-500 uppercase tracking-wide mb-1">Canal</p>
                      <p className="text-[12px] text-slate-300 flex items-center gap-1">{channelIcon[selectedRequest.channel]} {selectedRequest.channel}</p>
                    </div>
                  </div>
                  <div>
                    <p className="text-[10px] text-slate-500 uppercase tracking-wide mb-1">Asignat</p>
                    <p className="text-[12px] text-slate-300">{selectedRequest.assignedTo}</p>
                  </div>
                </div>

                {/* Delivery Type Selector */}
                <div className="mt-4 bg-[#1A2236] border border-[#2A3548] rounded-lg p-3">
                  <div className="flex items-center gap-2 mb-2">
                    <Truck className="w-3.5 h-3.5 text-blue-400" />
                    <p className="text-[10px] text-slate-500 uppercase tracking-wide font-semibold">
                      Tip Livrare
                    </p>
                  </div>
                  <div className="flex flex-wrap gap-1.5">
                    {(Object.keys(deliveryTypeLabels) as DeliveryType[]).map((dt) => {
                      const isActive = selectedRequest.deliveryType === dt;
                      return (
                        <button
                          key={dt}
                          disabled={!canMutateIntake || statusActionLoading}
                          onClick={async () => {
                            if (!canMutateIntake) return;
                            setStatusActionLoading(true);
                            try {
                              await patchIntakeByCode(selectedRequest.id, {
                                delivery_type: dt,
                              });
                              await refresh();
                            } finally {
                              setStatusActionLoading(false);
                            }
                          }}
                          className={`inline-flex items-center gap-1 px-2.5 py-1.5 text-[11px] font-semibold rounded-lg border transition-colors cursor-pointer ${
                            isActive
                              ? "bg-blue-600/20 text-blue-300 border-blue-500/50 ring-1 ring-blue-500/30"
                              : "bg-[#0D1321] text-slate-500 border-[#2A3548] hover:border-slate-500 hover:text-slate-400"
                          }`}
                        >
                          {isActive && <CheckCircle2 className="w-3 h-3" />}
                          {deliveryTypeLabels[dt]}
                        </button>
                      );
                    })}
                  </div>
                </div>

                {selectedRequest.notes && (
                  <div className="mt-3 bg-[#1A2236] rounded-lg p-3">
                    <p className="text-[10px] text-slate-500 uppercase tracking-wide mb-1 flex items-center gap-1">
                      <MessageSquare className="w-3 h-3" /> Note
                    </p>
                    <p className="text-[12px] text-slate-300">{selectedRequest.notes}</p>
                  </div>
                )}
              </div>

              {/* Timeline */}
              <div className="bg-[#111827] border border-[#1E293B] rounded-lg p-4">
                <SectionHeader title="Timeline" icon={<Clock className="w-4 h-4" />} />
                <div className="relative pl-6 space-y-3">
                  <div className="relative">
                    <div className="absolute left-[-20px] top-1 w-3 h-3 rounded-full bg-emerald-500" />
                    <p className="text-[11px] text-slate-300">Creat</p>
                    <p className="text-[10px] text-slate-500">{new Date(selectedRequest.createdAt).toLocaleString("ro-RO")}</p>
                  </div>
                  <div className="absolute left-[-16px] top-3 w-px h-[calc(100%-12px)] bg-[#2A3548]" />
                  <div className="relative">
                    <div className="absolute left-[-20px] top-1 w-3 h-3 rounded-full bg-blue-500" />
                    <p className="text-[11px] text-slate-300">Ultima actualizare</p>
                    <p className="text-[10px] text-slate-500">{new Date(selectedRequest.updatedAt).toLocaleString("ro-RO")}</p>
                  </div>
                </div>
              </div>

              {/* Actions */}
              <div className="bg-[#111827] border border-[#1E293B] rounded-lg p-4">
                <SectionHeader title="Acțiuni" icon={<ArrowRight className="w-4 h-4" />} />
                <div className="space-y-2">
                  {/* Primary action: open dedicated instrumentation page */}
                  {selectedRequest.status !== "cancelled" && (
                    <button
                      data-testid="work-intake-primary-edit"
                      onClick={() =>
                        navigate(resolveIntakeEditPath(selectedRequest))
                      }
                      className="w-full flex items-center justify-center gap-2 px-4 py-2.5 bg-blue-600 hover:bg-blue-500 text-white rounded-lg text-[12px] font-bold transition-colors"
                    >
                      <FileEdit className="w-3.5 h-3.5" />{" "}
                      {intakePrimaryEditLabel(
                        selectedRequest.confirmedTemplateCode,
                        selectedRequest.productFamily
                      )}
                    </button>
                  )}
                  {selectedRequest.status === "new" && (
                    <button
                      disabled={!canMutateIntake || statusActionLoading}
                      onClick={async () => {
                        if (!canMutateIntake) return;
                        setStatusActionLoading(true);
                        try {
                          await updateIntakeStatus(selectedRequest.id, "in_review");
                          await refresh();
                        } finally {
                          setStatusActionLoading(false);
                        }
                      }}
                      className="w-full flex items-center justify-center gap-2 px-4 py-2 bg-slate-700 hover:bg-slate-600 text-slate-200 rounded-lg text-[12px] font-semibold transition-colors disabled:opacity-50"
                    >
                      <Eye className="w-3.5 h-3.5" /> Preia în Analiză
                    </button>
                  )}
                  {selectedRequest.status === "in_review" && (() => {
                    const missingFields: string[] = [];
                    if (selectedRequest.assignedTo === "—" || selectedRequest.assignedTo.trim() === "") missingFields.push("Persoană asignată");
                    if (!selectedRequest.description.trim()) missingFields.push("Descriere produs");
                    if (!selectedRequest.dimensions.trim() || selectedRequest.dimensions === "Diverse") missingFields.push("Dimensiuni exacte");
                    if (!selectedRequest.notes.trim()) missingFields.push("Note / observații");
                    const canSendToQuote = missingFields.length === 0;

                    return (
                      <>
                        <div className="relative group">
                          <button
                            disabled={!canSendToQuote || !canMutateIntake || statusActionLoading}
                            onClick={() =>
                              navigate(resolveIntakeEditPath(selectedRequest))
                            }
                            className={`w-full flex items-center justify-center gap-2 px-4 py-2 rounded-lg text-[12px] font-semibold transition-colors ${
                              canSendToQuote
                                ? "bg-emerald-600 hover:bg-emerald-500 text-white"
                                : "bg-slate-700/60 text-slate-500 cursor-not-allowed"
                            }`}
                          >
                            <CheckCircle2 className="w-3.5 h-3.5" /> Marchează Gata pt. Ofertă
                          </button>
                          {!canSendToQuote && (
                            <div className="hidden group-hover:block absolute z-20 bottom-full left-0 right-0 mb-2 bg-[#1A2236] border border-red-800/40 rounded-lg p-3 shadow-xl">
                              <div className="flex items-center gap-1.5 mb-2">
                                <AlertTriangle className="w-3.5 h-3.5 text-red-400 shrink-0" />
                                <p className="text-[11px] text-red-300 font-semibold">
                                  Câmpuri obligatorii lipsă:
                                </p>
                              </div>
                              <ul className="space-y-1">
                                {missingFields.map((f) => (
                                  <li key={f} className="flex items-center gap-1.5 text-[10px] text-red-300/80">
                                    <XCircle className="w-3 h-3 text-red-400 shrink-0" />
                                    {f}
                                  </li>
                                ))}
                              </ul>
                              <p className="text-[9px] text-slate-500 mt-2 border-t border-slate-700 pt-2">
                                Completați câmpurile lipsă prin "Instrumentează Comanda"
                              </p>
                            </div>
                          )}
                        </div>
                        {!canSendToQuote && (
                          <div className="flex items-start gap-1.5 px-2 py-1.5 bg-red-900/10 border border-red-800/20 rounded-lg">
                            <AlertTriangle className="w-3 h-3 text-red-400 mt-0.5 shrink-0" />
                            <p className="text-[10px] text-red-300/80">
                              {missingFields.length} câmp(uri) obligatoriu(e) lipsă — hover pe buton pentru detalii
                            </p>
                          </div>
                        )}
                        <button
                          disabled={!canMutateIntake || statusActionLoading}
                          onClick={async () => {
                            if (!canMutateIntake) return;
                            setStatusActionLoading(true);
                            try {
                              await updateIntakeStatus(selectedRequest.id, "needs_info");
                              await refresh();
                            } finally {
                              setStatusActionLoading(false);
                            }
                          }}
                          className="w-full flex items-center justify-center gap-2 px-4 py-2 bg-amber-600 hover:bg-amber-500 text-white rounded-lg text-[12px] font-semibold transition-colors disabled:opacity-50"
                        >
                          <AlertTriangle className="w-3.5 h-3.5" /> Solicită Info Suplimentar
                        </button>
                      </>
                    );
                  })()}
                  {selectedRequest.status === "needs_info" && (
                    <button
                      disabled={!canMutateIntake || statusActionLoading}
                      onClick={async () => {
                        if (!canMutateIntake) return;
                        setStatusActionLoading(true);
                        try {
                          await updateIntakeStatus(selectedRequest.id, "in_review");
                          await refresh();
                        } finally {
                          setStatusActionLoading(false);
                        }
                      }}
                      className="w-full flex items-center justify-center gap-2 px-4 py-2 bg-blue-600 hover:bg-blue-500 text-white rounded-lg text-[12px] font-semibold transition-colors disabled:opacity-50"
                    >
                      <Eye className="w-3.5 h-3.5" /> Revino la Analiză
                    </button>
                  )}
                  {selectedRequest.status === "ready_for_quote" && (
                    <>
                      <button
                        data-testid="work-intake-create-draft-quote"
                        onClick={async () => {
                          if (!canMutateIntake || draftQuoteLoading) return;
                          setDraftQuoteError(null);
                          setDraftQuoteLoading(true);
                          try {
                            const result = await createDraftQuoteFromIntake(selectedRequest);
                            if (result.ok === false) {
                              setDraftQuoteError(result.error);
                            } else {
                              await refresh();
                              navigateToQuoteDetail(navigate, result.quoteCode);
                            }
                          } finally {
                            setDraftQuoteLoading(false);
                          }
                        }}
                        disabled={!canMutateIntake || draftQuoteLoading}
                        className="w-full flex items-center justify-center gap-2 px-4 py-2 bg-emerald-600 hover:bg-emerald-500 text-white rounded-lg text-[12px] font-semibold transition-colors disabled:opacity-50"
                      >
                        <ArrowRight className="w-3.5 h-3.5" />{" "}
                        {draftQuoteLoading ? "Se creează oferta…" : "Creează Ofertă Draft"}
                      </button>
                      {draftQuoteError && (
                        <p
                          className="text-[11px] text-red-300/90 px-1"
                          data-testid="work-intake-draft-quote-error"
                        >
                          {draftQuoteError}
                        </p>
                      )}
                    </>
                  )}
                </div>
              </div>
            </>
          ) : (
            <div className="bg-[#111827] border border-[#1E293B] rounded-lg p-8 text-center">
              <Inbox className="w-8 h-8 text-slate-600 mx-auto mb-2" />
              <p className="text-[13px] text-slate-500">Selectează o cerere pentru detalii</p>
            </div>
          )}
        </div>
      </div>
    </div>
  );
}