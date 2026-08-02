import { useEffect, useMemo, useState } from "react";
import { useNavigate } from "react-router-dom";
import { type IntakeRequest, type IntakeStatus, type DeliveryType, deliveryTypeLabels } from "@/lib/mockData";
import { useBackendData } from "@/hooks/useBackendData";
import { SectionHeader } from "@/components/workos/SharedComponents";
import {
  AlertBanner,
  chromeBanner,
  PageShell,
  SourceBadge,
  StatusBadge,
} from "@/components/workos/design-system";
import FlowBreadcrumb, { intakeBreadcrumb } from "@/components/workos/FlowBreadcrumb";
import CommercialFlowStrip from "@/components/workos/CommercialFlowStrip";
import NextStepPanel from "@/components/workos/NextStepPanel";
import TechnicalDetailsDisclosure from "@/components/workos/TechnicalDetailsDisclosure";
import NewIntakeDialog from "@/components/workos/NewIntakeDialog";
import { navigateToQuoteDetail } from "@/lib/commercialSpineNavigation";
import { intakeListNextStepHint } from "@/lib/commercialFlowUi";
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
  new: {
    label: "Nou",
    cls: "bg-slate-100 text-slate-700 border-slate-300 dark:bg-slate-700/60 dark:text-slate-300 dark:border-slate-600",
    icon: <Inbox className="w-3 h-3" />,
  },
  in_review: {
    label: "În Analiză",
    cls: "bg-blue-50 text-blue-700 border-blue-200 dark:bg-blue-900/40 dark:text-blue-300 dark:border-blue-700",
    icon: <Eye className="w-3 h-3" />,
  },
  needs_info: {
    label: "Lipsă Info",
    cls: "bg-amber-50 text-amber-800 border-amber-200 dark:bg-amber-900/40 dark:text-amber-300 dark:border-amber-700",
    icon: <AlertTriangle className="w-3 h-3" />,
  },
  ready_for_quote: {
    label: "Gata pt. Ofertă",
    cls: "bg-emerald-50 text-emerald-800 border-emerald-200 dark:bg-emerald-900/40 dark:text-emerald-300 dark:border-emerald-700",
    icon: <CheckCircle2 className="w-3 h-3" />,
  },
  blocked: {
    label: "Blocat",
    cls: "bg-red-50 text-red-800 border-red-200 dark:bg-red-900/40 dark:text-red-300 dark:border-red-700",
    icon: <XCircle className="w-3 h-3" />,
  },
  cancelled: {
    label: "Anulat",
    cls: "bg-slate-100 text-slate-500 border-slate-300 dark:bg-slate-800/60 dark:text-slate-400 dark:border-slate-600",
    icon: <XCircle className="w-3 h-3" />,
  },
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
    <div className={`bg-wo-surface-raised border rounded-lg p-3 transition-all cursor-pointer ${
      active ? "border-blue-500/50 ring-1 ring-blue-500/30" : "border-wo-border-strong hover:border-slate-500"
    }`}>
      <div className="flex items-center gap-2 mb-1">
        <span className={`${cfg.cls.includes("text-blue") ? "text-blue-400" : cfg.cls.includes("text-emerald") ? "text-emerald-400" : cfg.cls.includes("text-amber") ? "text-amber-400" : cfg.cls.includes("text-red") ? "text-red-400" : "text-slate-400"}`}>
          {cfg.icon}
        </span>
        <span className="text-[12px] font-semibold text-wo-text-primary">{cfg.label}</span>
      </div>
      <p className="text-[24px] font-bold text-wo-text-primary">{count}</p>
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

  const listNextStep = intakeListNextStepHint(selectedRequest?.status ?? "all");

  return (
    <div className="space-y-4" data-testid="work-intake-page">
      <FlowBreadcrumb items={intakeBreadcrumb()} />
      <CommercialFlowStrip active="cereri" />

      <PageShell
        compact
        title="Cereri"
        subtitle="Cerere → Produs → Ofertă → Comandă. Selectează o cerere pentru pasul următor."
        actions={
          <div className="flex items-center gap-2">
            <SourceBadge source={intakeSource} />
            <span className="text-[10px] font-medium text-wo-text-muted bg-wo-surface-raised border border-wo-border-strong px-2 py-0.5 rounded-full">
              {intakeRequests.length} cereri
            </span>
            <button
              onClick={() => setNewDialogOpen(true)}
              disabled={!canMutateIntake || !canCreateIntake}
              title={
                !canCreateIntake
                  ? "Crearea cererilor necesită cont admin/manager/sales — folosește http://127.0.0.1:3001"
                  : undefined
              }
              className="flex items-center gap-1.5 px-3 py-2 bg-emerald-600 hover:bg-emerald-500 text-white rounded-lg text-[12px] font-bold transition-colors disabled:opacity-50 disabled:cursor-not-allowed"
            >
              <Plus className="w-3.5 h-3.5" />
              Cerere Nouă
            </button>
          </div>
        }
      >
      <NewIntakeDialog
        open={newDialogOpen}
        onClose={() => setNewDialogOpen(false)}
        onCreated={async (code, productFamily, workspaceId, templateCode) => {
          await refresh();
          navigate(
            resolveIntakeEditPath({
              id: code,
              confirmedTemplateCode: templateCode ?? null,
              productFamily: productFamily ?? null,
              workspaceId: workspaceId ?? null,
            })
          );
        }}
      />

      {error && source !== "mock" && (
        <AlertBanner variant="error" compact title="Date indisponibile">
          Datele operaționale nu au putut fi încărcate din backend: {error}
        </AlertBanner>
      )}

      {!canMutateIntake && (
        <div className={`flex items-start gap-2 px-3 py-1.5 rounded-lg text-[11px] ${chromeBanner.warning}`}>
          <AlertTriangle className="w-3.5 h-3.5 mt-0.5 shrink-0" />
          <p>Acțiunile de creare/modificare sunt disponibile doar pe sursă backend live.</p>
        </div>
      )}

      {canMutateIntake && !canCreateIntake && (
        <div className={`flex items-start gap-2 px-3 py-1.5 rounded-lg text-[11px] ${chromeBanner.warning}`}>
          <AlertTriangle className="w-3.5 h-3.5 mt-0.5 shrink-0" />
          <p>
            Contul curent ({typeof user?.role === "string" ? user.role : "necunoscut"}) nu poate crea cereri.
            Folosește aplicația operator/comercial pe{" "}
            <a href="http://127.0.0.1:3001" className="underline font-medium">
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
        <div className="flex items-center gap-2 bg-wo-surface-raised border border-wo-border-subtle rounded-lg px-3 py-2 flex-1 max-w-md focus-within:border-blue-500/50">
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
            className="bg-transparent text-[13px] text-wo-text-primary placeholder:text-slate-600 outline-none w-full"
          />
        </div>
        {selectedStatus !== "all" && (
          <button onClick={() => setSelectedStatus("all")} className="text-[11px] text-slate-400 hover:text-wo-text-primary transition-colors">
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
              className={`bg-wo-surface-raised border rounded-lg p-3 cursor-pointer transition-all ${
                selectedRequest?.id === req.id ? "border-blue-500/50 ring-1 ring-blue-500/30" : "border-wo-border-subtle hover:border-slate-500"
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
                      "bg-wo-surface-inset text-wo-text-secondary border border-wo-border-strong"
                    }`}>
                      {req.priority.toUpperCase()}
                    </span>
                  </div>
                  <p className="text-[13px] font-semibold text-wo-text-primary">{req.client}</p>
                  <p className="text-[11px] text-wo-text-muted truncate mt-0.5">{req.description}</p>
                  <div className="flex items-center gap-3 mt-1.5 text-[10px] text-wo-text-dim">
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
            <div className="bg-wo-surface-raised border border-wo-border-subtle rounded-lg p-8 text-center text-slate-500 text-[13px]">
              Nicio cerere găsită.
            </div>
          )}

          {filtered.length > 0 && (
            <div
              className="flex flex-wrap items-center justify-between gap-2 pt-2 border-t border-wo-border-subtle/80"
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
                  className="px-3 py-1.5 text-[11px] font-semibold rounded-lg border border-wo-border-strong text-slate-300 hover:border-slate-500 disabled:opacity-40 disabled:cursor-not-allowed"
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
                  className="px-3 py-1.5 text-[11px] font-semibold rounded-lg border border-wo-border-strong text-slate-300 hover:border-slate-500 disabled:opacity-40 disabled:cursor-not-allowed"
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
              <div className="bg-wo-surface-raised border border-wo-border-subtle rounded-lg p-4">
                <div className="flex items-center justify-between mb-3">
                  <span className="text-[12px] font-mono text-blue-400">{selectedRequest.id}</span>
                  <IntakeStatusBadge status={selectedRequest.status} />
                </div>
                <h3 className="text-[16px] font-bold text-wo-text-primary">{selectedRequest.client}</h3>
                <p className="text-[12px] text-wo-text-secondary mt-1">{selectedRequest.contactPerson}</p>

                <div className="mt-4 space-y-3">
                  <div>
                    <p className="text-[10px] text-wo-text-muted uppercase tracking-wide mb-1">Descriere</p>
                    <p className="text-[12px] text-wo-text-primary leading-relaxed">{selectedRequest.description}</p>
                  </div>
                  <div className="grid grid-cols-2 gap-3">
                    <div>
                      <p className="text-[10px] text-wo-text-muted uppercase tracking-wide mb-1">Dimensiuni</p>
                      <p className="text-[12px] text-wo-text-primary font-mono">{selectedRequest.dimensions}</p>
                    </div>
                    <div>
                      <p className="text-[10px] text-wo-text-muted uppercase tracking-wide mb-1">Cantitate</p>
                      <p className="text-[12px] text-wo-text-primary">{selectedRequest.quantity} buc</p>
                    </div>
                  </div>
                  <div className="grid grid-cols-2 gap-3">
                    <div>
                      <p className="text-[10px] text-wo-text-muted uppercase tracking-wide mb-1">Familie Produs</p>
                      <p className="text-[12px] text-wo-text-primary">
                        {formatIntakeProductFamilyLabel(selectedRequest.productFamily)}
                      </p>
                    </div>
                    <div>
                      <p className="text-[10px] text-wo-text-muted uppercase tracking-wide mb-1">Canal</p>
                      <p className="text-[12px] text-wo-text-primary flex items-center gap-1">{channelIcon[selectedRequest.channel]} {selectedRequest.channel}</p>
                    </div>
                  </div>
                  <div>
                    <p className="text-[10px] text-wo-text-muted uppercase tracking-wide mb-1">Asignat</p>
                    <p className="text-[12px] text-wo-text-primary">{selectedRequest.assignedTo}</p>
                  </div>
                </div>

                {/* Delivery Type Selector */}
                <div className="mt-4 bg-wo-surface-raised border border-wo-border-strong rounded-lg p-3">
                  <div className="flex items-center gap-2 mb-2">
                    <Truck className="w-3.5 h-3.5 text-blue-400" />
                    <p className="text-[10px] text-wo-text-muted uppercase tracking-wide font-semibold">
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
                              : "bg-wo-surface-inset text-slate-500 border-wo-border-strong hover:border-slate-500 hover:text-slate-400"
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
                  <div className="mt-3 bg-wo-surface-raised rounded-lg p-3">
                    <p className="text-[10px] text-wo-text-muted uppercase tracking-wide mb-1 flex items-center gap-1">
                      <MessageSquare className="w-3 h-3" /> Note
                    </p>
                    <p className="text-[12px] text-wo-text-primary">{selectedRequest.notes}</p>
                  </div>
                )}
              </div>

              <NextStepPanel
                title={listNextStep.title}
                description={listNextStep.description}
                primaryAction={
                  selectedRequest.status !== "cancelled" && listNextStep.primaryLabel
                    ? {
                        label:
                          selectedRequest.status === "ready_for_quote"
                            ? "Deschide oferte"
                            : intakePrimaryEditLabel(
                                selectedRequest.confirmedTemplateCode,
                                selectedRequest.productFamily,
                              ) || listNextStep.primaryLabel,
                        onClick:
                          selectedRequest.status === "ready_for_quote"
                            ? undefined
                            : () => navigate(resolveIntakeEditPath(selectedRequest)),
                        to:
                          selectedRequest.status === "ready_for_quote"
                            ? "/quotes"
                            : undefined,
                      }
                    : listNextStep.primaryLabel && listNextStep.primaryTo
                      ? {
                          label: listNextStep.primaryLabel,
                          to: listNextStep.primaryTo,
                        }
                      : undefined
                }
                secondaryAction={
                  listNextStep.secondaryLabel && listNextStep.secondaryTo
                    ? {
                        label: listNextStep.secondaryLabel,
                        to: listNextStep.secondaryTo,
                        variant: "secondary",
                      }
                    : {
                        label: "Vezi produse",
                        to: "/product-system/products",
                        variant: "ghost",
                      }
                }
              />

              {/* Actions */}
              <div className="bg-wo-surface-raised border border-wo-border-subtle rounded-lg p-4">
                <SectionHeader title="Acțiuni" icon={<ArrowRight className="w-4 h-4" />} />
                <div className="space-y-2">
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
                      className="w-full flex items-center justify-center gap-2 px-4 py-2 bg-wo-surface-inset hover:bg-wo-hover text-wo-text-primary border border-wo-border-strong rounded-lg text-[12px] font-semibold transition-colors disabled:opacity-50"
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
                                : "bg-wo-surface-inset text-wo-text-muted border border-wo-border-strong cursor-not-allowed"
                            }`}
                          >
                            <CheckCircle2 className="w-3.5 h-3.5" /> Marchează Gata pt. Ofertă
                          </button>
                          {!canSendToQuote && (
                            <div className="hidden group-hover:block absolute z-20 bottom-full left-0 right-0 mb-2 bg-wo-surface-raised border border-red-200 dark:border-red-800/40 rounded-lg p-3 shadow-xl">
                              <div className="flex items-center gap-1.5 mb-2">
                                <AlertTriangle className="w-3.5 h-3.5 text-red-600 dark:text-red-400 shrink-0" />
                                <p className="text-[11px] text-red-700 dark:text-red-300 font-semibold">
                                  Câmpuri obligatorii lipsă:
                                </p>
                              </div>
                              <ul className="space-y-1">
                                {missingFields.map((f) => (
                                  <li key={f} className="flex items-center gap-1.5 text-[10px] text-red-700/80 dark:text-red-300/80">
                                    <XCircle className="w-3 h-3 text-red-500 shrink-0" />
                                    {f}
                                  </li>
                                ))}
                              </ul>
                              <p className="text-[9px] text-wo-text-muted mt-2 border-t border-wo-border-subtle pt-2">
                                Completați câmpurile lipsă din spațiul cererii.
                              </p>
                            </div>
                          )}
                        </div>
                        {!canSendToQuote && (
                          <div className={`flex items-start gap-1.5 px-2 py-1.5 rounded-lg ${chromeBanner.error}`}>
                            <AlertTriangle className="w-3 h-3 mt-0.5 shrink-0" />
                            <p className="text-[10px]">
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
                        {draftQuoteLoading ? "Se creează oferta…" : "Creează ofertă (ciornă)"}
                      </button>
                      {draftQuoteError && (
                        <p
                          className="text-[11px] text-red-700 dark:text-red-300 px-1"
                          data-testid="work-intake-draft-quote-error"
                        >
                          {draftQuoteError}
                        </p>
                      )}
                    </>
                  )}
                </div>
              </div>

              <TechnicalDetailsDisclosure testId="work-intake-technical-details">
                <div className="flex items-center gap-2 mb-2">
                  <Clock className="w-3.5 h-3.5" />
                  <span className="font-semibold text-wo-text-secondary">Istoric / diagnostic</span>
                </div>
                <p>Creat: {new Date(selectedRequest.createdAt).toLocaleString("ro-RO")}</p>
                <p>Actualizat: {new Date(selectedRequest.updatedAt).toLocaleString("ro-RO")}</p>
                <p className="font-mono text-[10px]">status={selectedRequest.status}</p>
                {selectedRequest.confirmedTemplateCode ? (
                  <p className="font-mono text-[10px]">
                    template={selectedRequest.confirmedTemplateCode}
                  </p>
                ) : null}
                <p className="font-mono text-[10px]">source={intakeSource}</p>
              </TechnicalDetailsDisclosure>
            </>
          ) : (
            <div className="bg-wo-surface-raised border border-wo-border-subtle rounded-lg p-6 space-y-3">
              <div className="text-center">
                <Inbox className="w-8 h-8 text-wo-text-dim mx-auto mb-2" />
                <p className="text-[13px] text-wo-text-muted">Selectează o cerere pentru detalii</p>
              </div>
              <NextStepPanel
                title="Flux comercial"
                description="Alege o cerere din listă, configurează produsul, apoi creează oferta. Comanda apare după acceptare."
                primaryAction={{ label: "Vezi produse", to: "/product-system/products" }}
                secondaryAction={{ label: "Vezi oferte", to: "/quotes", variant: "ghost" }}
              />
            </div>
          )}
        </div>
      </div>
      </PageShell>
    </div>
  );
}