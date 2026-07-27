/* eslint-disable @typescript-eslint/no-explicit-any */
import { useState, useEffect } from "react";
import { X, Plus, Search, UserPlus, CheckCircle2, AlertTriangle, Boxes } from "lucide-react";
import {
  clientsApi,
  intakesApi,
  productTemplateAvailabilityApi,
  type ClientEntity,
  type IntakeRequestEntity,
  type ProductTemplateAvailabilityItem,
} from "@/lib/api";
import InfoHint from "@/components/workos/templateIntakeWorkspace/InfoHint";
import { INTAKE_DELIVERY_OPTIONS } from "@/lib/intakeDeliverySemantics";
import { formatApiErrorFromUnknown, canCreateIntakeRequest } from "@/lib/apiError";
import { useAuth } from "@/contexts/AuthContext";
import { ensureIntakeV6WorkspaceForIntakeRequest } from "@/lib/intakeV6/intakeV6Api";
import {
  getAnalyzerFirstScopePresentation,
  getProductTemplateScopePresentation,
} from "@/lib/productTemplateScopePresentation";
import {
  INTAKE_V6_ANALYSIS_SOURCES,
  canCreateIntakeV6WorkspaceFromSource,
  getIntakeV6AnalysisSourceStatusLabel,
  type IntakeV6AnalysisSourceMethodId,
} from "@/lib/intakeV6/intakeV6AnalysisSourceTypes";

interface NewIntakeDialogProps {
  open: boolean;
  onClose: () => void;
  onCreated: (intakeCode: string, productFamily?: string | null, workspaceId?: string | null, templateCode?: string | null) => void;
}

type Step = "method" | "template" | "details";

type ClientMode = "existing" | "new_temp" | "new_fiscal";
const ANALYZER_MODE = "analyzer_first";

type TemplateHintPresentation = {
  categoryLabel: string;
  familyLabel: string;
  badgeLabel: string;
  badgeClassName: string;
  description: string;
  workIntakeLabel: string;
  directRootLabel: string;
};

function getTemplateHintPresentation(template: ProductTemplateAvailabilityItem): TemplateHintPresentation {
  const scope = getProductTemplateScopePresentation(template);

  return {
    categoryLabel: "Product Template",
    familyLabel: scope.familyLabel,
    badgeLabel: scope.statusLabel,
    badgeClassName: scope.isDirectRootAllowed
      ? "text-emerald-800 dark:text-emerald-300 bg-emerald-500/15 border-emerald-600/30 dark:border-emerald-500/30"
      : "text-amber-900 dark:text-amber-300 bg-amber-500/15 border-amber-600/30 dark:border-amber-500/30",
    description: scope.shortDescription,
    workIntakeLabel: scope.workIntakeLabel,
    directRootLabel: scope.rootDirectLabel,
  };
}

const OFFER_METHODS: Array<{
  id: IntakeV6AnalysisSourceMethodId;
  label: string;
  description: string;
  statusLabel: string;
  enabled: boolean;
}> = INTAKE_V6_ANALYSIS_SOURCES.map((source) => ({
  id: source.methodId,
  label: source.label,
  description: source.description,
  statusLabel: getIntakeV6AnalysisSourceStatusLabel(source.status),
  enabled: canCreateIntakeV6WorkspaceFromSource(source),
}));

const WORK_INTAKE_NEW_REQUEST_SOURCE = "work_intake_new_request";

const CHANNELS = [
  { value: "email", label: "Email" },
  { value: "phone", label: "Telefon" },
  { value: "walk_in", label: "Walk-in" },
  { value: "web_form", label: "Formular Web" },
];

const PRIORITIES = [
  { value: "low", label: "Scăzută" },
  { value: "normal", label: "Normală" },
  { value: "high", label: "Ridicată" },
  { value: "urgent", label: "Urgentă" },
];

type IntakeCreateForm = {
  description: string;
  channel: string;
  priority: IntakeRequestEntity["priority"];
  delivery_type: string;
};

export default function NewIntakeDialog({ open, onClose, onCreated }: NewIntakeDialogProps) {
  const analyzerFirstPresentation = getAnalyzerFirstScopePresentation();
  const { user } = useAuth();
  const canCreateIntake = canCreateIntakeRequest(
    typeof user?.role === "string" ? user.role : undefined
  );
  const [step, setStep] = useState<Step>("method");
  const [mode, setMode] = useState<ClientMode>("existing");
  const [submitting, setSubmitting] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const [clients, setClients] = useState<ClientEntity[]>([]);
  const [clientSearch, setClientSearch] = useState("");
  const [selectedClient, setSelectedClient] = useState<ClientEntity | null>(null);
  const [loadingClients, setLoadingClients] = useState(false);
  const [visibleTemplates, setVisibleTemplates] = useState<ProductTemplateAvailabilityItem[]>([]);
  const [loadingTemplates, setLoadingTemplates] = useState(false);
  const [templateLoadError, setTemplateLoadError] = useState<string | null>(null);
  const [selectedOfferMethod, setSelectedOfferMethod] = useState<IntakeV6AnalysisSourceMethodId | null>(null);
  const [selectedTemplateCode, setSelectedTemplateCode] = useState<string | null>(null);

  const [newClient, setNewClient] = useState({
    name: "",
    cui: "",
    contact_person: "",
    phone: "",
    email: "",
    address: "",
    city: "",
  });

  const [intake, setIntake] = useState<IntakeCreateForm>({
    description: "",
    channel: "email",
    priority: "normal",
    delivery_type: "delivery_standard",
  });

  useEffect(() => {
    if (!open) return;
    setLoadingClients(true);
    clientsApi
      .list({}, { sort: "-created_at", limit: 200 })
      .then((rows) => setClients(rows))
      .catch((err) => {
        console.warn("[NewIntakeDialog] failed to load clients", err);
        setClients([]);
      })
      .finally(() => setLoadingClients(false));
  }, [open]);

  useEffect(() => {
    if (!open) return;
    setLoadingTemplates(true);
    setTemplateLoadError(null);
    productTemplateAvailabilityApi
      .list({ offerable_only: false, include_runtime_modules: false, include_archived: true })
      .then((response) => {
        const visible = response.items.filter(
          (template) =>
            template.quote_offerable ||
            template.product_system_role === "candidate_product" ||
            template.display_group === "candidate_products"
        );
        setVisibleTemplates(visible);
        setSelectedTemplateCode((current) => current ?? null);
      })
      .catch((err) => {
        console.warn("[NewIntakeDialog] failed to load offerable templates", err);
        setVisibleTemplates([]);
        setTemplateLoadError(
          "Template-urile candidate din Product System nu au putut fi încărcate."
        );
      })
      .finally(() => setLoadingTemplates(false));
  }, [open]);

  useEffect(() => {
    if (!open) {
      setTimeout(() => {
        setStep("method");
        setMode("existing");
        setSelectedClient(null);
        setClientSearch("");
        setSelectedOfferMethod(null);
        setSelectedTemplateCode(null);
        setError(null);
        setSubmitting(false);
        setNewClient({
          name: "",
          cui: "",
          contact_person: "",
          phone: "",
          email: "",
          address: "",
          city: "",
        });
        setIntake({
          description: "",
          channel: "email",
          priority: "normal",
          delivery_type: "delivery_standard",
        });
      }, 200);
    }
  }, [open]);

  if (!open) return null;

  const filteredClients = clientSearch.trim()
    ? clients.filter((c) => {
        const q = clientSearch.toLowerCase();
        return (
          c.name.toLowerCase().includes(q) ||
          (c.cui ?? "").toLowerCase().includes(q) ||
          (c.contact_person ?? "").toLowerCase().includes(q)
        );
      })
    : clients.slice(0, 20);

  const canProceedFromClient = () => {
    if (mode === "existing") return !!selectedClient;
    if (mode === "new_fiscal") return newClient.name.trim().length > 0 && newClient.cui.trim().length > 0;
    if (mode === "new_temp") return newClient.name.trim().length > 0;
    return false;
  };

  const selectedTemplate = visibleTemplates.find((template) => template.template_code === selectedTemplateCode) ?? null;
  const canProceedFromMethod = () => !!selectedOfferMethod;
  const canProceedFromTemplate = () => !loadingTemplates && !templateLoadError;
  const canSubmit = () => canProceedFromClient() && canProceedFromTemplate() && intake.description.trim().length > 0;

  const resolvedFamilyId = selectedTemplate?.family_id ?? "";

  const clientDisplayName =
    mode === "existing" ? selectedClient?.name : newClient.name.trim() || "—";

  const handleSubmit = async () => {
    if (!canSubmit()) return;
    if (!canCreateIntake) {
      setError(
        "Contul curent nu poate crea cereri Work Intake. Deschide aplicația operator/comercial pe http://127.0.0.1:3001."
      );
      return;
    }
    if (!selectedOfferMethod) {
      setError("Selectează modalitatea de ofertare înainte de a crea cererea.");
      return;
    }
    setSubmitting(true);
    setError(null);
    try {
      let clientEntity: ClientEntity;
      if (mode === "existing" && selectedClient) {
        clientEntity = selectedClient;
      } else {
        const identity_type = mode === "new_fiscal" ? "fiscal" : "temp";
        const temp_ref = mode === "new_temp" ? `TEMP-${Date.now().toString(36).toUpperCase()}` : undefined;
        clientEntity = await clientsApi.create({
          name: newClient.name.trim(),
          identity_type,
          temp_ref,
          cui: mode === "new_fiscal" ? newClient.cui.trim() : undefined,
          contact_person: newClient.contact_person.trim() || undefined,
          phone: newClient.phone.trim() || undefined,
          email: newClient.email.trim() || undefined,
          address: newClient.address.trim() || undefined,
          city: newClient.city.trim() || undefined,
        });
      }

      const code = `IR-${Date.now().toString(36).toUpperCase()}`;

      await intakesApi.create({
        code,
        client_id: clientEntity.id,
        client_name: clientEntity.name,
        contact_person: clientEntity.contact_person ?? "—",
        channel: intake.channel,
        product_family: resolvedFamilyId,
        description: intake.description.trim(),
        dimensions: "—",
        quantity: 1,
        status: "new",
        assigned_to: "—",
        notes: "",
        priority: intake.priority,
        delivery_type: intake.delivery_type,
        confirmed_template_code: selectedTemplate?.template_code,
        confirmed_template_name: selectedTemplate?.description ?? selectedTemplate?.template_code,
      });

      const workspace = await ensureIntakeV6WorkspaceForIntakeRequest(code, {
        offer_method: selectedOfferMethod,
        analyzer_mode: ANALYZER_MODE,
        template_hint_code: selectedTemplate?.template_code,
        source: WORK_INTAKE_NEW_REQUEST_SOURCE,
      });

      onCreated(code, resolvedFamilyId, workspace.id, selectedTemplate?.template_code ?? null);
      onClose();
    } catch (err: unknown) {
      console.error("[NewIntakeDialog] submit failed", err);
      const message = formatApiErrorFromUnknown(err, "Eroare la crearea cererii. Încearcă din nou.");
      if (message.includes("Invalid product_family/family_id")) {
        setError(`Tipul de lucrare selectat nu mai este valid în registry-ul backend: ${message}`);
      } else {
        setError(message);
      }
      setSubmitting(false);
    }
  };

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/60 backdrop-blur-sm p-4">
      <div className="bg-wo-surface-inset border border-wo-border-strong rounded-xl shadow-2xl w-full max-w-3xl max-h-[90vh] flex flex-col overflow-hidden">
        <div className="flex items-center justify-between px-5 py-3 border-b border-wo-border-strong">
          <div className="flex items-center gap-2">
            <Plus className="w-4 h-4 text-emerald-500" />
            <h2 className="text-[15px] font-bold text-wo-text-primary tracking-tight">Cerere nouă</h2>
            <span className="text-[10px] font-medium text-wo-text-muted bg-wo-surface-raised border border-wo-border-strong px-2 py-0.5 rounded">
              Pas {step === "method" ? "1" : step === "template" ? "2" : "3"}/3
            </span>
          </div>
          <button
            onClick={onClose}
            className="text-wo-text-muted hover:text-wo-text-primary transition-colors"
            aria-label="Închide"
          >
            <X className="w-4 h-4" />
          </button>
        </div>

        <div className="flex-1 overflow-y-auto p-5">
          {step === "method" && (
            <div className="space-y-4">
              <div>
                <h3 className="text-[14px] font-bold text-wo-text-primary">Alege modalitatea de ofertare</h3>
                <p className="text-[12px] text-wo-text-muted mt-1.5 leading-relaxed">
                  Selectează cum începe cererea comercială. Prima metodă activă pornește workspace-ul modular Intake V6.
                </p>
              </div>
              <div className="space-y-2">
                {OFFER_METHODS.map((method) => (
                  <button
                    key={method.id}
                    type="button"
                    disabled={!method.enabled}
                    onClick={() => method.enabled && setSelectedOfferMethod(method.id)}
                    className={`w-full text-left rounded-lg border px-4 py-3 transition-colors ${
                      selectedOfferMethod === method.id
                        ? "bg-blue-600/15 border-blue-500/50"
                        : "bg-wo-surface-raised border-wo-border-strong hover:border-wo-border-strong hover:bg-wo-hover"
                    } ${method.enabled ? "" : "opacity-55 cursor-not-allowed"}`}
                  >
                    <div className="flex items-start justify-between gap-3">
                      <div>
                        <p className="text-[13px] font-bold text-wo-text-primary">{method.label}</p>
                        <p className="text-[11px] text-wo-text-muted mt-1 leading-relaxed">{method.description}</p>
                      </div>
                      <span className="shrink-0 text-[10px] font-semibold text-emerald-800 dark:text-emerald-300 bg-emerald-500/15 border border-emerald-600/30 dark:border-emerald-500/30 rounded px-2 py-0.5">
                        {method.statusLabel}
                      </span>
                    </div>
                  </button>
                ))}
              </div>
            </div>
          )}

          {step === "template" && (
            <div className="space-y-4">
              <div>
                <h3 className="text-[14px] font-bold text-wo-text-primary">Hint Product System opțional</h3>
                <p className="text-[12px] text-wo-text-muted mt-1.5 leading-relaxed">
                  Analyzer-ul pornește primul. Alege un hint doar dacă operatorul știe deja familia probabilă.
                </p>
              </div>
              <section className="space-y-2">
                <div className="flex items-center gap-1.5">
                  <Boxes className="w-3.5 h-3.5 text-blue-500" />
                  <h4 className="text-[12px] font-bold text-wo-text-secondary">Template hint</h4>
                </div>
                <div className="space-y-2" data-testid="template-hint-list">
                  {loadingTemplates ? (
                    <p className="text-[11px] text-wo-text-muted p-4 text-center">Se încarcă template-urile candidate...</p>
                  ) : visibleTemplates.length === 0 ? (
                    <p className="text-[11px] text-wo-text-muted p-4 text-center border border-wo-border-strong rounded-lg bg-wo-surface-raised">
                      Nu există template-uri candidate disponibile.
                    </p>
                  ) : (
                    <button
                      type="button"
                      onClick={() => setSelectedTemplateCode(null)}
                      className={`w-full text-left rounded-lg border px-4 py-3 transition-colors ${
                        selectedTemplateCode === null
                          ? "bg-blue-600/15 border-blue-500/50"
                          : "bg-wo-surface-raised border-wo-border-strong hover:border-wo-border-strong hover:bg-wo-hover"
                      }`}
                      data-testid="analyzer-first-no-template-hint"
                    >
                      <div className="flex items-start justify-between gap-3">
                        <div>
                          <p className="text-[13px] font-bold text-wo-text-primary">Analyzer-first</p>
                          <p className="text-[11px] text-wo-text-muted mt-1 leading-relaxed">
                            {analyzerFirstPresentation.shortDescription}
                          </p>
                        </div>
                        <span className="shrink-0 text-[10px] font-semibold text-blue-800 dark:text-blue-300 bg-blue-500/15 border border-blue-600/30 dark:border-blue-500/30 rounded px-2 py-0.5">
                          {analyzerFirstPresentation.statusLabel}
                        </span>
                      </div>
                    </button>
                  )}
                  {!loadingTemplates && visibleTemplates.length > 0 ? (
                    visibleTemplates.map((template) => {
                      const presentation = getTemplateHintPresentation(template);

                      return (
                        <button
                          key={template.template_code}
                          type="button"
                          onClick={() => setSelectedTemplateCode(template.template_code)}
                          className={`w-full text-left rounded-lg border px-4 py-3 transition-colors ${
                            selectedTemplateCode === template.template_code
                              ? "bg-blue-600/15 border-blue-500/50"
                              : "bg-wo-surface-raised border-wo-border-strong hover:border-wo-border-strong hover:bg-wo-hover"
                          }`}
                        >
                          <div className="flex items-start justify-between gap-3">
                            <div className="min-w-0">
                              <p className="text-[13px] font-mono font-bold text-wo-text-primary break-all">{template.template_code}</p>
                              <p className="text-[10px] uppercase tracking-wide text-wo-text-dim mt-1">
                                {presentation.categoryLabel}
                              </p>
                              <p className="text-[11px] text-wo-text-secondary mt-1">{presentation.familyLabel}</p>
                              <p className="text-[11px] text-wo-text-muted mt-1 leading-relaxed">{presentation.description}</p>
                              <div className="mt-2 flex flex-wrap gap-2 text-[10px]">
                                <span className="rounded border border-wo-border-strong bg-wo-surface-inset px-2 py-0.5 text-wo-text-secondary">
                                  {presentation.workIntakeLabel}
                                </span>
                                <span className="rounded border border-wo-border-strong bg-wo-surface-inset px-2 py-0.5 text-wo-text-muted">
                                  {presentation.directRootLabel}
                                </span>
                              </div>
                              {template.has_modules ? (
                                <p className="text-[10px] text-wo-text-muted mt-2">Module interne gestionate automat: {template.module_codes.length}</p>
                              ) : null}
                            </div>
                            <span
                              className={`shrink-0 rounded border px-2 py-0.5 text-[10px] font-semibold ${presentation.badgeClassName}`}
                            >
                              {presentation.badgeLabel}
                            </span>
                          </div>
                        </button>
                      );
                    })
                  ) : null}
                </div>
              </section>
            </div>
          )}

          {step === "details" && (
            <div className="space-y-4">
              <p className="text-[12px] text-wo-text-muted leading-relaxed">
                Alege un client existent sau creează unul nou.
                <InfoHint label="Despre client temporar">
                  Clientul temporar poate fi convertit ulterior la identitate fiscală (CUI) înainte de acceptarea
                  ofertei.
                </InfoHint>
              </p>

              <div className="grid grid-cols-3 gap-2">
                {(
                  [
                    { v: "existing" as const, label: "Client Existent", icon: <Search className="w-3.5 h-3.5" /> },
                    { v: "new_temp" as const, label: "Client Temporar", icon: <UserPlus className="w-3.5 h-3.5" /> },
                    { v: "new_fiscal" as const, label: "Client Fiscal (CUI)", icon: <UserPlus className="w-3.5 h-3.5" /> },
                  ]
                ).map((m) => (
                  <button
                    key={m.v}
                    onClick={() => {
                      setMode(m.v);
                      setSelectedClient(null);
                    }}
                    className={`flex items-center justify-center gap-1.5 px-3 py-2 text-[11px] font-semibold rounded-lg border transition-colors ${
                      mode === m.v
                        ? "bg-blue-600/20 text-blue-800 dark:text-blue-300 border-blue-500/50"
                        : "bg-wo-surface-raised text-wo-text-muted border-wo-border-strong hover:bg-wo-hover hover:text-wo-text-secondary"
                    }`}
                  >
                    {m.icon}
                    {m.label}
                  </button>
                ))}
              </div>

              {mode === "existing" && (
                <div className="space-y-2">
                  <div className="flex items-center gap-2 bg-wo-surface-raised border border-wo-border-strong rounded-lg px-3 py-2 focus-within:border-blue-500/50">
                    <Search className="w-4 h-4 text-wo-text-dim" />
                    <input
                      id="new-intake-client-search"
                      name="new-intake-client-search"
                      type="text"
                      value={clientSearch}
                      onChange={(e) => setClientSearch(e.target.value)}
                      placeholder="Caută după nume, CUI, persoană contact..."
                      className="bg-transparent text-[12px] text-wo-text-primary placeholder:text-wo-text-dim outline-none w-full"
                    />
                  </div>
                  <div className="max-h-60 overflow-y-auto border border-wo-border-strong rounded-lg bg-wo-surface-raised">
                    {loadingClients ? (
                      <p className="text-[11px] text-wo-text-muted p-4 text-center">Se încarcă clienții...</p>
                    ) : filteredClients.length === 0 ? (
                      <div className="p-4 text-center">
                        <p className="text-[11px] text-wo-text-muted">
                          {clients.length === 0
                            ? "Nu există clienți în baza de date. Alege „Client Temporar\" pentru a crea unul rapid."
                            : "Niciun client găsit."}
                        </p>
                      </div>
                    ) : (
                      <ul>
                        {filteredClients.map((c) => (
                          <li key={c.id}>
                            <button
                              onClick={() => setSelectedClient(c)}
                              className={`w-full text-left px-3 py-2 border-b border-wo-border-strong last:border-b-0 transition-colors ${
                                selectedClient?.id === c.id
                                  ? "bg-blue-600/15"
                                  : "hover:bg-wo-hover"
                              }`}
                            >
                              <div className="flex items-center justify-between">
                                <div>
                                  <p className="text-[12px] font-semibold text-wo-text-primary">{c.name}</p>
                                  <p className="text-[10px] text-wo-text-muted">
                                    {c.identity_type === "fiscal" ? `CUI: ${c.cui ?? "—"}` : `TEMP: ${c.temp_ref ?? "—"}`}
                                    {c.contact_person ? ` · ${c.contact_person}` : ""}
                                  </p>
                                </div>
                                {selectedClient?.id === c.id && (
                                  <CheckCircle2 className="w-4 h-4 text-emerald-400" />
                                )}
                              </div>
                            </button>
                          </li>
                        ))}
                      </ul>
                    )}
                  </div>
                </div>
              )}

              {(mode === "new_temp" || mode === "new_fiscal") && (
                <div className="space-y-3">
                  <div>
                    <label
                      className="text-[10px] text-wo-text-dim uppercase tracking-wide block mb-1"
                      htmlFor="new-intake-client-name"
                    >
                      Nume Client <span className="text-red-500">*</span>
                    </label>
                    <input
                      id="new-intake-client-name"
                      name="new-intake-client-name"
                      value={newClient.name}
                      onChange={(e) => setNewClient({ ...newClient, name: e.target.value })}
                      placeholder="SC Exemplu SRL sau Ion Popescu"
                      className="w-full bg-wo-surface-raised border border-wo-border-strong rounded-lg px-3 py-2 text-[12px] text-wo-text-primary placeholder:text-wo-text-dim outline-none focus:border-blue-500/50"
                    />
                  </div>
                  {mode === "new_fiscal" && (
                    <div>
                      <label
                        className="text-[10px] text-wo-text-dim uppercase tracking-wide block mb-1"
                        htmlFor="new-intake-client-cui"
                      >
                        CUI <span className="text-red-500">*</span>
                      </label>
                      <input
                        id="new-intake-client-cui"
                        name="new-intake-client-cui"
                        value={newClient.cui}
                        onChange={(e) => setNewClient({ ...newClient, cui: e.target.value })}
                        placeholder="RO12345678"
                        className="w-full bg-wo-surface-raised border border-wo-border-strong rounded-lg px-3 py-2 text-[12px] text-wo-text-primary placeholder:text-wo-text-dim outline-none focus:border-blue-500/50"
                      />
                    </div>
                  )}
                  <div className="grid grid-cols-2 gap-3">
                    <div>
                      <label
                        className="text-[10px] text-wo-text-dim uppercase tracking-wide block mb-1"
                        htmlFor="new-intake-client-contact"
                      >
                        Persoană Contact
                      </label>
                      <input
                        id="new-intake-client-contact"
                        name="new-intake-client-contact"
                        value={newClient.contact_person}
                        onChange={(e) => setNewClient({ ...newClient, contact_person: e.target.value })}
                        placeholder="Numele persoanei"
                        className="w-full bg-wo-surface-raised border border-wo-border-strong rounded-lg px-3 py-2 text-[12px] text-wo-text-primary placeholder:text-wo-text-dim outline-none focus:border-blue-500/50"
                      />
                    </div>
                    <div>
                      <label
                        className="text-[10px] text-wo-text-dim uppercase tracking-wide block mb-1"
                        htmlFor="new-intake-client-phone"
                      >
                        Telefon
                      </label>
                      <input
                        id="new-intake-client-phone"
                        name="new-intake-client-phone"
                        value={newClient.phone}
                        onChange={(e) => setNewClient({ ...newClient, phone: e.target.value })}
                        placeholder="07xx xxx xxx"
                        className="w-full bg-wo-surface-raised border border-wo-border-strong rounded-lg px-3 py-2 text-[12px] text-wo-text-primary placeholder:text-wo-text-dim outline-none focus:border-blue-500/50"
                      />
                    </div>
                  </div>
                </div>
              )}
              <div className="space-y-5 pt-2">
              <div className="flex items-center justify-between gap-3 bg-wo-surface-raised border border-wo-border-strong rounded-lg px-3 py-2.5">
                <div className="min-w-0">
                  <p className="text-[10px] text-wo-text-dim uppercase tracking-wide">Template Product System</p>
                  <p className="text-[13px] font-semibold text-wo-text-primary truncate">{selectedTemplate?.template_code ?? "Analyzer-first"}</p>
                  <p className="text-[10px] text-wo-text-muted mt-0.5 truncate">{selectedTemplate?.family_name ?? "Fără template final înainte de SVG"}</p>
                </div>
                <button
                  type="button"
                  onClick={() => setStep("template")}
                  className="shrink-0 text-[11px] font-semibold text-blue-700 dark:text-blue-400 hover:text-blue-800 dark:hover:text-blue-300"
                >
                  Schimbă hint
                </button>
              </div>

              <section className="space-y-3">
                <h3 className="text-[12px] font-bold text-wo-text-primary">Date cerere</h3>
                <div className="grid grid-cols-1 md:grid-cols-2 gap-3">
                  <div>
                    <label
                      className="text-[10px] text-wo-text-dim uppercase tracking-wide block mb-1"
                      htmlFor="new-intake-channel"
                    >
                      Canal <span className="text-red-500">*</span>
                    </label>
                    <select
                      id="new-intake-channel"
                      name="new-intake-channel"
                      aria-label="Canal"
                      value={intake.channel}
                      onChange={(e) => setIntake({ ...intake, channel: e.target.value })}
                      className="w-full bg-wo-surface-raised border border-wo-border-strong rounded-lg px-3 py-2 text-[12px] text-wo-text-primary outline-none focus:border-blue-500/50"
                    >
                      {CHANNELS.map((c) => (
                        <option key={c.value} value={c.value}>
                          {c.label}
                        </option>
                      ))}
                    </select>
                  </div>
                  <div>
                    <label
                      className="text-[10px] text-wo-text-dim uppercase tracking-wide block mb-1"
                      htmlFor="new-intake-priority"
                    >
                      Prioritate
                    </label>
                    <select
                      id="new-intake-priority"
                      name="new-intake-priority"
                      aria-label="Prioritate"
                      value={intake.priority}
                      onChange={(e) =>
                        setIntake({ ...intake, priority: e.target.value as IntakeRequestEntity["priority"] })
                      }
                      className="w-full bg-wo-surface-raised border border-wo-border-strong rounded-lg px-3 py-2 text-[12px] text-wo-text-primary outline-none focus:border-blue-500/50"
                    >
                      {PRIORITIES.map((p) => (
                        <option key={p.value} value={p.value}>
                          {p.label}
                        </option>
                      ))}
                    </select>
                  </div>
                  <div>
                    <label
                      className="text-[10px] text-wo-text-dim uppercase tracking-wide block mb-1"
                      htmlFor="new-intake-delivery-type"
                    >
                      Tip livrare
                    </label>
                    <select
                      id="new-intake-delivery-type"
                      name="new-intake-delivery-type"
                      aria-label="Tip livrare"
                      value={intake.delivery_type}
                      onChange={(e) => setIntake({ ...intake, delivery_type: e.target.value })}
                      className="w-full bg-wo-surface-raised border border-wo-border-strong rounded-lg px-3 py-2 text-[12px] text-wo-text-primary outline-none focus:border-blue-500/50"
                    >
                      {INTAKE_DELIVERY_OPTIONS.map((d) => (
                        <option key={d.value} value={d.value}>
                          {d.label}
                        </option>
                      ))}
                    </select>
                  </div>
                  <div className="md:col-span-2">
                    <label
                      className="text-[10px] text-wo-text-dim uppercase tracking-wide block mb-1"
                      htmlFor="new-intake-description"
                    >
                      Descriere scurtă <span className="text-red-500">*</span>
                    </label>
                    <textarea
                      id="new-intake-description"
                      name="new-intake-description"
                      value={intake.description}
                      onChange={(e) => setIntake({ ...intake, description: e.target.value })}
                      placeholder="Ex: Litere volumetrice pentru fațadă, 12 caractere, montaj inclus..."
                      rows={3}
                      className="w-full bg-wo-surface-raised border border-wo-border-strong rounded-lg px-3 py-2 text-[12px] text-wo-text-primary placeholder:text-wo-text-dim outline-none focus:border-blue-500/50 resize-none"
                    />
                  </div>
                </div>
              </section>
              </div>
            </div>
          )}

          {(templateLoadError || error) && (
            <div className="mt-3 flex items-start gap-2 px-3 py-2 bg-red-50 dark:bg-red-900/20 border border-red-200 dark:border-red-800/40 rounded-lg">
              <AlertTriangle className="w-3.5 h-3.5 text-red-600 dark:text-red-400 mt-0.5 shrink-0" />
              <p className="text-[11px] text-red-700 dark:text-red-300">{error ?? templateLoadError}</p>
            </div>
          )}
        </div>

        <div className="flex items-center justify-between px-5 py-3 border-t border-wo-border-strong bg-wo-surface-inset">
          <button
            onClick={step === "details" ? () => setStep("template") : step === "template" ? () => setStep("method") : onClose}
            className="text-[12px] font-semibold text-wo-text-muted hover:text-wo-text-primary transition-colors"
            disabled={submitting}
          >
            {step === "method" ? "Anulează" : "← Înapoi"}
          </button>
          <div className="flex flex-col items-end gap-1">
            {step === "details" && !canSubmit() && !submitting && (
              <p
                className="text-[10px] text-amber-800 dark:text-amber-400/90"
                data-testid="create-intake-missing-requirements"
              >
                Completează: client, descriere
              </p>
            )}
            <div className="flex items-center gap-2">
              {step === "method" ? (
                <button
                  onClick={() => setStep("template")}
                  disabled={!canProceedFromMethod()}
                  className={`px-4 py-2 text-[12px] font-bold rounded-lg transition-colors ${
                    canProceedFromMethod()
                      ? "bg-blue-600 hover:bg-blue-500 text-white"
                      : "bg-wo-surface-raised text-wo-text-dim border border-wo-border-strong cursor-not-allowed"
                  }`}
                >
                  Continuă →
                </button>
              ) : step === "template" ? (
                <button
                  onClick={() => setStep("details")}
                  disabled={!canProceedFromTemplate()}
                  className={`px-4 py-2 text-[12px] font-bold rounded-lg transition-colors ${
                    canProceedFromTemplate()
                      ? "bg-blue-600 hover:bg-blue-500 text-white"
                      : "bg-wo-surface-raised text-wo-text-dim border border-wo-border-strong cursor-not-allowed"
                  }`}
                >
                  Continuă →
                </button>
              ) : (
                <button
                  onClick={handleSubmit}
                  disabled={!canSubmit() || submitting}
                  className={`px-4 py-2 text-[12px] font-bold rounded-lg transition-colors flex items-center gap-2 ${
                    canSubmit() && !submitting
                      ? "bg-emerald-600 hover:bg-emerald-500 text-white"
                      : "bg-wo-surface-raised text-wo-text-dim border border-wo-border-strong cursor-not-allowed"
                  }`}
                >
                  {submitting ? (
                    <>
                      <div className="animate-spin rounded-full h-3 w-3 border-b-2 border-white"></div>
                      Se creează...
                    </>
                  ) : (
                    <>
                      <Plus className="w-3.5 h-3.5" />
                      Creează Cerere
                    </>
                  )}
                </button>
              )}
            </div>
          </div>
        </div>
      </div>
    </div>
  );
}
