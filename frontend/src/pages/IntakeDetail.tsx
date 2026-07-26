import { useState, useCallback, useMemo, useEffect } from "react";
import { useParams, useNavigate, Link } from "react-router-dom";
import {
  type IntakeStatus,
  type DeliveryType,
  deliveryTypeLabels,
  type IntakeIdentity,
  getTemplateByFamilyId,
  productTemplates,
  type ProductTemplate,
  type StockStatus,
  isPlateMaterial,
  getAvailableSheets,
  checkSheetFit,
  type PhysicalSheet,
  type FitCheckResult,
} from "@/lib/mockData";
import { useBackendData } from "@/hooks/useBackendData";
import {
  lookupCUI,
  searchAddresses,
  clientCUIMap,
  type SmartBillCompany,
  type MapSuggestion,
} from "@/lib/smartbillMock";
import {
  getMaterialSheetAssist,
  listProductTemplateAssist,
  lookupFiscalProvider,
  suggestProductTemplates,
  type FiscalLookupResponse,
  type MaterialSheetAssistItem,
  type ProductTemplateSuggestionItem,
} from "@/api/intakeAssist";
import {
  buildSheetQualityInvalidSummaryUrl,
  buildSheetQualityMaterialUrl,
} from "@/utils/inventorySheetQualityLinks";
import Product001IntakeSpecEditor from "@/components/workos/Product001IntakeSpecEditor";
import { intakesApi, type ClientEntity, createClientEntity, updateClient, lookupClientsByTaxId, buildClientCreateFromFiscalNormalized, buildClientUpdateFromFiscalNormalized } from "@/lib/api";
import {
  isLitereVolumetriceFamily,
  parseIntakeProductSpec,
  type IntakeProductSpec,
} from "@/lib/intakeProductSpec";
import {
  formatIntakeProductFamilyLabel,
  isUnresolvedIntakeProductFamily,
} from "@/lib/intakeProductFamilyDisplay";
import {
  buildQuoteWizardNavStateFromIntake,
  navigateToQuotesList,
} from "@/lib/commercialSpineNavigation";
import { TPL_VOLUMETRIC_LETTERS } from "@/lib/volumetricQuoteInput";
import {
  auditUiToSiteAudit,
  parseSiteAuditJson,
  siteAuditToAuditUi,
  terrainSummaryLabel,
} from "@/lib/intakeSiteAudit";
import {
  evaluateIntakeReadyPrerequisites,
  shouldShowVolumetricProductForm,
} from "@/lib/intakeReadiness";
import {
  markIntakeReadyForQuote,
  patchIntakeByCode,
  persistConfirmedTemplate,
  persistSiteAudit,
  resolveIntakeDbId,
} from "@/lib/intakePersistence";
import { SectionHeader } from "@/components/workos/SharedComponents";
import FlowBreadcrumb, { intakeDetailBreadcrumb } from "@/components/workos/FlowBreadcrumb";
import NextStepPanel from "@/components/workos/NextStepPanel";
import IntakeActionSummary from "@/components/workos/IntakeActionSummary";
import { TemplateWorkspaceRouter } from "@/components/workos/templateIntakeWorkspace";
import {
  buildIntakeActionSummary,
  INTAKE_SECTION_IDS,
} from "@/lib/intakeActionSummary";
import {
  parseIntakeDimensionNumbers,
  parseIntakeDimensionsStruct,
} from "@/lib/intakeDetailDimensions";
import {
  getIntakeDetailRenderIssues,
  intakeWorkspaceDiagnosticLabel,
  resolveIntakeWorkspaceShell,
  shouldShowIntakeWorkspaceDiagnostic,
} from "@/lib/intakeDetailRouting";
import {
  hasIntakeStatusReadinessConflict,
  shouldUseVolumetricIntakePage,
} from "@/lib/volumetricIntakeRoute";
import {
  filterReadinessMissingForDisplay,
  getDeliveryStageNote,
  requiresTerrainAudit,
} from "@/lib/intakeDeliverySemantics";
import {
  intakeTerrainGatesActive,
  STAGE0_SPEC_MESSAGE,
  STAGE0_WORK_TYPE_GUIDANCE,
} from "@/lib/intakeGateStages";
import IntakeWorkTypePicker from "@/components/workos/IntakeWorkTypePicker";
import { productFamiliesApi, type ProductFamily } from "@/api/productFamilies";
import { resolveWorkTypeFamilyId } from "@/lib/intakeQuickStartWorkTypes";
import {
  ArrowLeft,
  Search,
  Building2,
  CheckCircle2,
  XCircle,
  AlertTriangle,
  Loader2,
  MapPin,
  Camera,
  Wrench,
  Link2,
  MessageSquare,
  Smartphone,
  Image,
  Shield,
  Info,
  ChevronRight,
  Truck,
  Hash,
  Package,
  Clock,
  Layers,
  Cog,
  BoxSelect,
  HardHat,
  Zap,
  Cable,
} from "lucide-react";

// --- Status Badge ---
const statusConfig: Record<IntakeStatus, { label: string; cls: string }> = {
  new: { label: "Nou", cls: "bg-slate-700/60 text-slate-300 border-slate-600" },
  in_review: { label: "În Analiză", cls: "bg-blue-900/40 text-blue-300 border-blue-700" },
  needs_info: { label: "Lipsă Info", cls: "bg-amber-900/40 text-amber-300 border-amber-700" },
  ready_for_quote: { label: "Gata pt. Ofertă", cls: "bg-emerald-900/40 text-emerald-300 border-emerald-700" },
  blocked: { label: "Blocat", cls: "bg-red-900/40 text-red-300 border-red-700" },
  cancelled: { label: "Anulat", cls: "bg-slate-800/60 text-slate-400 border-slate-600" },
};

// ============================================================
// IDENTITY SECTION (Temp ID + Optional CUI)
// ============================================================
function IdentitySection({
  identity,
  initialCUI,
  companyData,
  onCompanyFound,
  allowMockLookup,
  source,
}: {
  identity: IntakeIdentity;
  initialCUI: string;
  companyData: SmartBillCompany | null;
  onCompanyFound: (data: SmartBillCompany) => void;
  allowMockLookup: boolean;
  source: string;
}) {
  const [cui, setCui] = useState(initialCUI);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [found, setFound] = useState(!!companyData);
  const [confirmed, setConfirmed] = useState(!!companyData);
  const [previewCompany, setPreviewCompany] = useState<SmartBillCompany | null>(companyData);
  const [lookupInfo, setLookupInfo] = useState<string | null>(null);
  const [requiresConfirm, setRequiresConfirm] = useState(false);
  const [fiscalPayload, setFiscalPayload] = useState<FiscalLookupResponse | null>(null);
  const [clientMatchStatus, setClientMatchStatus] = useState<
    "idle" | "loading" | "none" | "single" | "conflict" | "invalid"
  >("idle");
  const [matchedClient, setMatchedClient] = useState<ClientEntity | null>(null);
  const [persistedClient, setPersistedClient] = useState<ClientEntity | null>(null);
  const [persistLoading, setPersistLoading] = useState(false);
  const [persistError, setPersistError] = useState<string | null>(null);
  const [persistSuccess, setPersistSuccess] = useState<string | null>(null);

  useEffect(() => {
    if (companyData) {
      setPreviewCompany(companyData);
      setFound(true);
      setConfirmed(true);
      setRequiresConfirm(false);
    }
  }, [companyData]);

  const mapNormalizedToCompany = useCallback((normalized: NonNullable<FiscalLookupResponse["normalized"]>): SmartBillCompany => {
    return {
      cui: normalized.tax_id,
      name: normalized.company_name,
      address: normalized.address || "—",
      county: normalized.county || "—",
      city: normalized.city || "—",
      registrationNumber: normalized.registration_number || "—",
      isRO: normalized.country === "RO",
      isVATPayer: normalized.vat_payer,
      vatCode: normalized.tax_id,
      phone: "—",
      email: "—",
    };
  }, []);

  const applyPreviewToIntake = useCallback(() => {
    if (!previewCompany) return;
    onCompanyFound(previewCompany);
    setConfirmed(true);
    setRequiresConfirm(false);
    setLookupInfo("Date fiscale aplicate în draft după confirmare operator.");
  }, [onCompanyFound, previewCompany]);

  const resolveClientMatch = useCallback(async (taxId: string) => {
    setClientMatchStatus("loading");
    setMatchedClient(null);
    setPersistedClient(null);
    setPersistError(null);
    setPersistSuccess(null);
    try {
      const match = await lookupClientsByTaxId(taxId);
      if (match.status === "invalid_input") {
        setClientMatchStatus("invalid");
        return;
      }
      setClientMatchStatus(match.status);
      setMatchedClient(match.status === "single" ? match.matches[0] ?? null : null);
    } catch {
      setClientMatchStatus("invalid");
      setPersistError("Nu am putut verifica dacă există deja clientul cu acest CUI.");
    }
  }, []);

  const canPersistClient =
    !allowMockLookup &&
    Boolean(fiscalPayload?.normalized?.tax_id && fiscalPayload?.normalized?.company_name) &&
    clientMatchStatus !== "loading" &&
    clientMatchStatus !== "conflict" &&
    clientMatchStatus !== "invalid" &&
    !persistedClient;

  const handleSaveClient = useCallback(async () => {
    if (!fiscalPayload?.normalized || clientMatchStatus !== "none") return;
    setPersistLoading(true);
    setPersistError(null);
    setPersistSuccess(null);
    try {
      const payload = buildClientCreateFromFiscalNormalized(fiscalPayload.normalized);
      const created = await createClientEntity(payload);
      setPersistedClient(created);
      setMatchedClient(created);
      setClientMatchStatus("single");
      setPersistSuccess("Client salvat în sistem.");
    } catch (error) {
      setPersistError(error instanceof Error ? error.message : "Salvarea clientului a eșuat.");
    } finally {
      setPersistLoading(false);
    }
  }, [clientMatchStatus, fiscalPayload]);

  const handleUpdateClient = useCallback(async () => {
    if (!fiscalPayload?.normalized || !matchedClient || clientMatchStatus !== "single") return;
    setPersistLoading(true);
    setPersistError(null);
    setPersistSuccess(null);
    try {
      const updates = buildClientUpdateFromFiscalNormalized(matchedClient, fiscalPayload.normalized);
      const updated = await updateClient(matchedClient.id, updates);
      setPersistedClient(updated);
      setMatchedClient(updated);
      setPersistSuccess("Client actualizat în sistem.");
    } catch (error) {
      setPersistError(error instanceof Error ? error.message : "Actualizarea clientului a eșuat.");
    } finally {
      setPersistLoading(false);
    }
  }, [clientMatchStatus, fiscalPayload, matchedClient]);

  const handleLookup = useCallback(async () => {
    if (!cui.trim()) return;
    setLoading(true);
    setError(null);
    setFound(false);
    setConfirmed(false);
    setLookupInfo(null);
    setRequiresConfirm(false);
    setFiscalPayload(null);
    setClientMatchStatus("idle");
    setMatchedClient(null);
    setPersistedClient(null);
    setPersistError(null);
    setPersistSuccess(null);
    if (!allowMockLookup) {
      const result = await lookupFiscalProvider(cui.trim());
      setLoading(false);
      if (result.status === "contract-missing") {
        setError(
          result.message ||
            "Lookup fiscal backend indisponibil."
        );
      } else if (result.status === "error") {
        setError(result.message || "Eroare la interogarea fiscală backend.");
      } else {
        const payload = result.data;
        if (!payload) {
          setError("Lookup fiscal backend indisponibil pentru acest provider.");
          return;
        }

        if (payload.status === "found" && payload.normalized) {
          const mapped = mapNormalizedToCompany(payload.normalized);
          setPreviewCompany(mapped);
          setFound(true);
          setFiscalPayload(payload);
          setRequiresConfirm(Boolean(payload.requires_operator_confirmation));
          setLookupInfo(
            payload.warnings?.length
              ? `Date fiscale preluate (${payload.provider === "anaf" ? "ANAF" : "SmartBill"}). ${payload.warnings.join(" ")}`
              : `Date fiscale preluate din ${payload.provider === "anaf" ? "ANAF" : "SmartBill"}. Verifică și salvează clientul înainte de aplicare.`
          );
          void resolveClientMatch(payload.normalized.tax_id);
          return;
        }

        setPreviewCompany(null);
        setFiscalPayload(null);
        setClientMatchStatus("idle");
        setMatchedClient(null);
        if (payload.status === "not_configured") {
          setError("Interogarea fiscală nu este configurată pe backend pentru acest mediu.");
        } else if (payload.status === "invalid_input") {
          setError("CUI invalid. Introdu un CUI RO valid (cu sau fără prefix RO).");
        } else if (payload.status === "not_found") {
          setError("Nu a fost găsită nicio companie pentru CUI-ul introdus.");
        } else if (payload.status === "provider_timeout") {
          setError("Provider fiscal indisponibil temporar (timeout). Reîncearcă.");
        } else if (payload.status === "rate_limited") {
          setError("Provider fiscal a limitat cererile. Reîncearcă mai târziu.");
        } else {
          setError("Provider fiscal a returnat eroare. Verifică și reîncearcă.");
        }
      }
      return;
    }

    const result = await lookupCUI(cui);
    setLoading(false);
    if (result.success && result.data) {
      setPreviewCompany(result.data);
      setFound(true);
      setRequiresConfirm(true);
      setLookupInfo("Date fiscale preluate din mock demo. Necesită confirmare operator.");
    } else {
      setPreviewCompany(null);
      setError(result.error || "Eroare necunoscută");
    }
  }, [allowMockLookup, cui, mapNormalizedToCompany, resolveClientMatch]);

  const isFiscal = identity.type === "fiscal" || confirmed;

  return (
    <div
      className="bg-wo-surface-raised border border-wo-border-subtle rounded-lg p-5"
      data-testid="intake-identity-section"
    >
      <div className="flex items-center justify-between mb-4">
        <SectionHeader
          title="Identificare Client"
          icon={<Hash className="w-4 h-4 text-blue-400" />}
        />
        {isFiscal ? (
          <span className="px-2.5 py-1 text-[10px] font-bold bg-emerald-900/40 text-emerald-400 border border-emerald-700 rounded-lg flex items-center gap-1.5">
            <CheckCircle2 className="w-3 h-3" />
            CUI VERIFICAT
          </span>
        ) : (
          <span className="px-2.5 py-1 text-[10px] font-bold bg-amber-900/40 text-amber-400 border border-amber-700 rounded-lg flex items-center gap-1.5">
            <Hash className="w-3 h-3" />
            TEMP ID
          </span>
        )}
      </div>

      {/* Temp Ref display */}
      <div className="flex items-center gap-3 mb-4">
        <div className="bg-wo-surface-inset border border-wo-border-strong rounded-lg px-3 py-2">
          <p className="text-[10px] text-slate-500 uppercase tracking-wide mb-0.5">
            Referință Temporară
          </p>
          <p className="text-[13px] text-amber-400 font-mono font-bold">
            {identity.tempRef}
          </p>
        </div>
        {identity.resolvedAt && (
          <div className="bg-wo-surface-inset border border-emerald-800/30 rounded-lg px-3 py-2">
            <p className="text-[10px] text-slate-500 uppercase tracking-wide mb-0.5">
              Rezolvat la
            </p>
            <p className="text-[12px] text-emerald-400 font-mono">
              {new Date(identity.resolvedAt).toLocaleString("ro-RO")}
            </p>
          </div>
        )}
      </div>

      {/* Gate info */}
      {!isFiscal && (
        <div className="flex items-start gap-2 px-3 py-2 bg-amber-900/10 border border-amber-800/20 rounded-lg mb-4">
          <Info className="w-3.5 h-3.5 text-amber-400 mt-0.5 shrink-0" />
          <p className="text-[10px] text-amber-300/80">
            <strong>CUI opțional la intake.</strong> Cererea poate avansa până la ofertare cu Temp ID.
            CUI-ul devine <strong>obligatoriu</strong> la acceptarea ofertei și trimiterea în producție.
          </p>
        </div>
      )}

      {/* CUI Input — SmartBill Lookup */}
      <div className="bg-wo-surface-inset border border-wo-border-strong rounded-lg p-4">
        {!allowMockLookup && (
          <div className="flex items-start gap-2 mb-3 px-3 py-2 bg-amber-900/15 border border-amber-800/30 rounded-lg">
            <AlertTriangle className="w-3.5 h-3.5 text-amber-400 mt-0.5 shrink-0" />
            <p className="text-[10px] text-amber-300/90">
              Simulatorul SmartBill este dezactivat în live mode. Se folosește exclusiv boundary-ul backend.
            </p>
          </div>
        )}
        <p className="text-[11px] text-slate-400 font-semibold mb-2 flex items-center gap-1.5">
          <Building2 className="w-3.5 h-3.5 text-blue-400" />
          Identitate Fiscală — Interogare ANAF / SmartBill
          <span className="text-[9px] text-slate-600 font-normal ml-1">(opțional)</span>
        </p>
        <div className="flex items-center gap-3">
          <div className="flex items-center gap-2 bg-wo-surface-raised border border-wo-border-strong rounded-lg px-3 py-2.5 flex-1 max-w-sm focus-within:border-blue-500/50">
            <Search className="w-4 h-4 text-slate-500 shrink-0" />
            <input
              type="text"
              value={cui}
              disabled={loading}
              onChange={(e) => {
                setCui(e.target.value);
                setError(null);
                setFound(false);
              }}
              onKeyDown={(e) => e.key === "Enter" && handleLookup()}
              placeholder="Introdu CUI (ex: 14399840)"
              className="bg-transparent text-[13px] text-slate-200 placeholder:text-slate-600 outline-none w-full font-mono"
            />
          </div>
          <button
            onClick={handleLookup}
            disabled={loading || !cui.trim()}
            className="flex items-center gap-2 px-4 py-2.5 bg-blue-600 hover:bg-blue-500 disabled:bg-slate-700 disabled:text-slate-500 text-white rounded-lg text-[12px] font-semibold transition-colors"
          >
            {loading ? (
              <Loader2 className="w-4 h-4 animate-spin" />
            ) : (
              <Search className="w-4 h-4" />
            )}
            {loading ? "Interogare..." : source === "mock" ? "Interogare SmartBill (mock)" : "Interogare fiscală backend"}
          </button>
        </div>

        {error && (
          <div className="flex items-center gap-2 mt-3 px-3 py-2 bg-red-900/20 border border-red-800/40 rounded-lg">
            <XCircle className="w-4 h-4 text-red-400 shrink-0" />
            <p className="text-[12px] text-red-300">{error}</p>
          </div>
        )}

        {lookupInfo && (
          <div className="flex items-center gap-2 mt-3 px-3 py-2 bg-blue-900/20 border border-blue-800/40 rounded-lg">
            <Info className="w-4 h-4 text-blue-300 shrink-0" />
            <p className="text-[12px] text-blue-200">{lookupInfo}</p>
          </div>
        )}

        {found && previewCompany && (
          <div className="mt-4 bg-wo-surface-raised border border-emerald-800/30 rounded-lg p-4" data-testid="fiscal-lookup-preview">
            <div className="flex items-center gap-2 mb-3">
              <CheckCircle2 className="w-4 h-4 text-emerald-400" />
              <p className="text-[12px] text-emerald-400 font-semibold">
                Date fiscale identificate cu succes
              </p>
              {fiscalPayload && (
                <span className="ml-auto px-2 py-0.5 text-[10px] font-semibold rounded border border-blue-700/40 bg-blue-900/20 text-blue-300">
                  Date propuse din {fiscalPayload.provider === "anaf" ? "ANAF" : "SmartBill"}
                </span>
              )}
            </div>

            {requiresConfirm && (
              <div className="flex items-start gap-2 mb-3 px-3 py-2 bg-amber-900/20 border border-amber-800/40 rounded-lg">
                <AlertTriangle className="w-4 h-4 text-amber-300 mt-0.5 shrink-0" />
                <div className="text-[11px] text-amber-200">
                  Date preluate din provider. Verifică manual, salvează sau actualizează clientul, apoi confirmă aplicarea în intake.
                </div>
              </div>
            )}

            {fiscalPayload?.warnings?.length ? (
              <div className="flex items-start gap-2 mb-3 px-3 py-2 bg-amber-900/15 border border-amber-800/30 rounded-lg">
                <AlertTriangle className="w-4 h-4 text-amber-300 mt-0.5 shrink-0" />
                <div className="text-[11px] text-amber-200">{fiscalPayload.warnings.join(" ")}</div>
              </div>
            ) : null}

            <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
              <DataField label="Nume Firmă" value={previewCompany.name} />
              <DataField label="CUI" value={previewCompany.cui} mono />
              <DataField label="Cod TVA" value={previewCompany.vatCode} mono />
              <DataField
                label="Plătitor TVA"
                value={previewCompany.isVATPayer ? "Da" : "Nu"}
                highlight={previewCompany.isVATPayer}
              />
              <DataField label="Reg. Comerțului" value={previewCompany.registrationNumber} mono />
              <DataField label="Adresă Sediu" value={previewCompany.address} />
              <DataField label="Județ / Oraș" value={`${previewCompany.county}, ${previewCompany.city}`} />
              <DataField label="Contact" value={`${previewCompany.phone} · ${previewCompany.email}`} />
            </div>

            {!allowMockLookup && (
              <div className="mt-4 border-t border-wo-border-strong pt-4 space-y-3">
                <div className="text-[11px] text-slate-400">
                  {clientMatchStatus === "loading" && "Verific client existent după CUI..."}
                  {clientMatchStatus === "none" && "Client inexistent în sistem."}
                  {clientMatchStatus === "single" &&
                    (persistedClient
                      ? `Client salvat/selectat: ${persistedClient.name} (#${persistedClient.id}).`
                      : `Client existent găsit: ${matchedClient?.name ?? "—"} (#${matchedClient?.id ?? "—"}).`)}
                  {clientMatchStatus === "conflict" &&
                    "Conflict: mai mulți clienți cu același CUI. Rezolvare manuală necesară."}
                  {clientMatchStatus === "invalid" && "Nu am putut verifica existența clientului după CUI."}
                </div>

                {persistError && (
                  <div className="flex items-center gap-2 px-3 py-2 bg-red-900/20 border border-red-800/40 rounded-lg">
                    <XCircle className="w-4 h-4 text-red-400 shrink-0" />
                    <p className="text-[12px] text-red-300">{persistError}</p>
                  </div>
                )}

                {persistSuccess && (
                  <div className="flex items-center gap-2 px-3 py-2 bg-emerald-900/20 border border-emerald-800/40 rounded-lg">
                    <CheckCircle2 className="w-4 h-4 text-emerald-400 shrink-0" />
                    <p className="text-[12px] text-emerald-300">{persistSuccess}</p>
                  </div>
                )}

                <div className="flex flex-wrap gap-2 justify-end">
                  {clientMatchStatus === "none" && (
                    <button
                      type="button"
                      onClick={handleSaveClient}
                      disabled={!canPersistClient || persistLoading}
                      data-testid="fiscal-save-client-button"
                      className="px-3 py-2 bg-blue-600 hover:bg-blue-500 disabled:bg-slate-700 disabled:text-slate-500 text-white rounded-lg text-[12px] font-semibold transition-colors"
                    >
                      {persistLoading ? "Salvare..." : "Salvează client"}
                    </button>
                  )}
                  {clientMatchStatus === "single" && !persistedClient && (
                    <button
                      type="button"
                      onClick={handleUpdateClient}
                      disabled={!canPersistClient || persistLoading}
                      data-testid="fiscal-update-client-button"
                      className="px-3 py-2 bg-blue-600 hover:bg-blue-500 disabled:bg-slate-700 disabled:text-slate-500 text-white rounded-lg text-[12px] font-semibold transition-colors"
                    >
                      {persistLoading ? "Actualizare..." : "Actualizează client"}
                    </button>
                  )}
                  {requiresConfirm && (
                    <button
                      type="button"
                      onClick={applyPreviewToIntake}
                      disabled={!previewCompany}
                      className="px-3 py-2 bg-emerald-600 hover:bg-emerald-500 text-white rounded-lg text-[12px] font-semibold transition-colors"
                    >
                      Confirmă și aplică datele fiscale
                    </button>
                  )}
                </div>
              </div>
            )}

            {allowMockLookup && requiresConfirm && (
              <div className="mt-4 flex justify-end">
                <button
                  onClick={applyPreviewToIntake}
                  className="px-3 py-2 bg-emerald-600 hover:bg-emerald-500 text-white rounded-lg text-[12px] font-semibold transition-colors"
                >
                  Confirmă și aplică datele fiscale
                </button>
              </div>
            )}
          </div>
        )}
      </div>
    </div>
  );
}

function DataField({
  label,
  value,
  mono,
  highlight,
}: {
  label: string;
  value: string;
  mono?: boolean;
  highlight?: boolean;
}) {
  return (
    <div>
      <p className="text-[10px] text-slate-500 uppercase tracking-wide mb-0.5">
        {label}
      </p>
      <p
        className={`text-[12px] ${mono ? "font-mono" : ""} ${highlight ? "text-emerald-400 font-semibold" : "text-slate-200"}`}
      >
        {value}
      </p>
    </div>
  );
}

// ============================================================
// PRODUCT SYSTEM SECTION
// ============================================================
const stockStatusCls: Record<StockStatus, string> = {
  ok: "text-emerald-400",
  low: "text-amber-400",
  critical: "text-red-400",
  out_of_stock: "text-red-500",
};

const stockStatusLabel: Record<StockStatus, string> = {
  ok: "OK",
  low: "Stoc redus",
  critical: "Critic",
  out_of_stock: "Epuizat",
};

// --- Fit Check Badge ---
const fitCheckConfig: Record<FitCheckResult, { label: string; cls: string; icon: string }> = {
  fits: { label: "ÎNCAPE", cls: "text-emerald-400 bg-emerald-900/40 border-emerald-700", icon: "🟢" },
  limited: { label: "LIMITAT", cls: "text-amber-400 bg-amber-900/40 border-amber-700", icon: "🟡" },
  no_fit: { label: "NU ÎNCAPE", cls: "text-red-400 bg-red-900/40 border-red-700", icon: "🔴" },
};

function SheetBreakdown({ materialId }: { materialId: string }) {
  const sheets = getAvailableSheets(materialId);
  const fullSheets = sheets.filter((s) => s.type === "full_sheet");
  const remnants = sheets.filter((s) => s.type === "remnant");

  // Group full sheets by dimension
  const fullGroups = new Map<string, { sheet: PhysicalSheet; count: number }>();
  for (const s of fullSheets) {
    const key = `${s.widthMM}×${s.heightMM}`;
    const existing = fullGroups.get(key);
    if (existing) {
      existing.count++;
    } else {
      fullGroups.set(key, { sheet: s, count: 1 });
    }
  }

  return (
    <div className="mt-2 space-y-1">
      {Array.from(fullGroups.entries()).map(([key, { sheet, count }]) => (
        <div key={key} className="flex items-center gap-2 text-[10px]">
          <span className="w-2 h-2 rounded-full bg-emerald-500 shrink-0" />
          <span className="text-slate-300">
            {count}× Placă completă{" "}
            <span className="font-mono text-slate-200">
              {sheet.widthMM}×{sheet.heightMM}mm
            </span>
          </span>
          <span className="text-slate-600">
            ({((sheet.widthMM * sheet.heightMM) / 1_000_000).toFixed(2)} mp)
          </span>
        </div>
      ))}
      {remnants.map((r) => {
        const minSide = Math.min(r.widthMM, r.heightMM);
        const isStrip = minSide < 200;
        return (
          <div key={r.sheetId} className="flex items-center gap-2 text-[10px]">
            <span
              className={`w-2 h-2 rounded-full shrink-0 ${isStrip ? "bg-red-500" : "bg-amber-500"}`}
            />
            <span className="text-slate-300">
              1× {isStrip ? "Fâșie" : "Rest"}{" "}
              <span className="font-mono text-slate-200">
                {r.widthMM}×{r.heightMM}mm
              </span>
            </span>
            {r.label && (
              <span className="text-slate-600">({r.label})</span>
            )}
            {isStrip && (
              <span className="text-red-400 font-semibold">⚠ utilizabilitate limitată</span>
            )}
          </div>
        );
      })}
    </div>
  );
}

function ProductSystemSection({
  template,
  pieceDimensionMM,
}: {
  template: ProductTemplate;
  /** Minimum dimension of the largest piece in mm (from intake dimensions) */
  pieceDimensionMM: number;
}) {
  const [expandedSheets, setExpandedSheets] = useState<Set<string>>(new Set());

  const toggleExpand = (matId: string) => {
    setExpandedSheets((prev) => {
      const next = new Set(prev);
      if (next.has(matId)) next.delete(matId);
      else next.add(matId);
      return next;
    });
  };

  // Check for issues: plate materials with fit problems, or non-plate with insufficient stock
  const hasIssues = template.requiredMaterials.some((m) => {
    if (isPlateMaterial(m.materialId)) {
      const fit = checkSheetFit(m.materialId, pieceDimensionMM);
      return fit.result === "no_fit" || fit.totalSheets === 0;
    }
    return m.stockStatus === "critical" || m.stockStatus === "out_of_stock";
  });

  return (
    <div className="bg-wo-surface-raised border border-wo-border-subtle rounded-lg p-5">
      <div className="flex items-center justify-between mb-4">
        <SectionHeader
          title="Informații Produs — ProductSystem"
          icon={<Package className="w-4 h-4 text-purple-400" />}
        />
        <div className="flex items-center gap-2">
          <Link
            to="/product-system"
            className="text-[10px] text-purple-400 hover:text-purple-300 transition-colors underline underline-offset-2"
          >
            Editează șabloanele →
          </Link>
          {hasIssues ? (
            <span className="px-2 py-0.5 text-[10px] font-bold bg-amber-900/40 text-amber-400 border border-amber-700 rounded flex items-center gap-1">
              <AlertTriangle className="w-3 h-3" />
              ATENȚIE MATERIALE
            </span>
          ) : (
            <span className="px-2 py-0.5 text-[10px] font-bold bg-emerald-900/40 text-emerald-400 border border-emerald-700 rounded flex items-center gap-1">
              <CheckCircle2 className="w-3 h-3" />
              MATERIALE OK
            </span>
          )}
        </div>
      </div>

      {/* Template info */}
      <div className="bg-wo-surface-inset border border-wo-border-strong rounded-lg p-4 mb-4">
        <div className="grid grid-cols-1 md:grid-cols-3 gap-4 mb-3">
          <div>
            <p className="text-[10px] text-slate-500 uppercase tracking-wide mb-0.5">
              Șablon Producție
            </p>
            <p className="text-[13px] text-purple-400 font-mono font-bold">
              {template.templateCode}
            </p>
          </div>
          <div>
            <p className="text-[10px] text-slate-500 uppercase tracking-wide mb-0.5">
              Familie
            </p>
            <p className="text-[13px] text-slate-200 font-semibold">
              {template.familyName}
            </p>
          </div>
          <div>
            <p className="text-[10px] text-slate-500 uppercase tracking-wide mb-0.5">
              Timp Estimat
            </p>
            <p className="text-[13px] text-slate-200 font-semibold flex items-center gap-1">
              <Clock className="w-3.5 h-3.5 text-blue-400" />
              {template.estimatedHours}h ({Math.ceil(template.estimatedHours / 8)} zile lucr.)
            </p>
          </div>
        </div>
        <p className="text-[11px] text-slate-400">{template.description}</p>
      </div>

      {/* Components */}
      <div className="mb-4">
        <p className="text-[11px] text-slate-400 font-semibold mb-2 flex items-center gap-1.5">
          <Layers className="w-3.5 h-3.5 text-blue-400" />
          Componente Principale
        </p>
        <div className="flex flex-wrap gap-2">
          {template.components.map((c, i) => (
            <span
              key={i}
              className="inline-flex items-center gap-1 px-2.5 py-1.5 text-[11px] font-medium bg-wo-surface-inset text-slate-300 border border-wo-border-strong rounded-lg"
            >
              <BoxSelect className="w-3 h-3 text-slate-500" />
              {c}
            </span>
          ))}
        </div>
      </div>

      {/* Operations routing */}
      <div className="mb-4">
        <p className="text-[11px] text-slate-400 font-semibold mb-2 flex items-center gap-1.5">
          <Cog className="w-3.5 h-3.5 text-blue-400" />
          Routing Operații Producție
        </p>
        <div className="bg-wo-surface-inset border border-wo-border-strong rounded-lg overflow-hidden">
          <div className="grid grid-cols-[40px_1fr_1fr_80px] gap-2 px-3 py-2 bg-wo-surface-raised text-[10px] text-slate-500 uppercase tracking-wide font-semibold">
            <span>#</span>
            <span>Operație</span>
            <span>Centru Lucru</span>
            <span className="text-right">Timp</span>
          </div>
          {template.operations.map((op) => (
            <div
              key={op.code + op.sequence}
              className="grid grid-cols-[40px_1fr_1fr_80px] gap-2 px-3 py-2 border-t border-wo-border-subtle text-[11px]"
            >
              <span className="text-slate-600 font-mono">{op.sequence}</span>
              <span className="text-slate-200">{op.name}</span>
              <span className="text-slate-400">{op.workcenter}</span>
              <span className="text-slate-300 text-right font-mono">
                {op.estimatedMinutes}min
              </span>
            </div>
          ))}
        </div>
      </div>

      {/* Materials + Sheet-Based Stock Check */}
      <div>
        <p className="text-[11px] text-slate-400 font-semibold mb-2 flex items-center gap-1.5">
          <Package className="w-3.5 h-3.5 text-blue-400" />
          Materiale Necesare — Check Disponibilitate (OC)
        </p>

        {/* Piece dimension info for nesting context */}
        <div className="flex items-center gap-2 mb-3 px-3 py-2 bg-wo-surface-inset border border-wo-border-strong rounded-lg">
          <Info className="w-3.5 h-3.5 text-blue-400 shrink-0" />
          <p className="text-[10px] text-slate-400">
            <strong className="text-slate-300">Dimensiune piesă referință:</strong>{" "}
            <span className="font-mono text-blue-400">{pieceDimensionMM}mm</span>{" "}
            — folosită pentru verificarea încadrării pe plăci disponibile (Fit Check)
          </p>
        </div>

        <div className="bg-wo-surface-inset border border-wo-border-strong rounded-lg overflow-hidden">
          {/* Header — different for plate vs non-plate */}
          <div className="grid grid-cols-[1fr_120px_120px] gap-2 px-3 py-2 bg-wo-surface-raised text-[10px] text-slate-500 uppercase tracking-wide font-semibold">
            <span>Material</span>
            <span className="text-center">Plăci / Stoc</span>
            <span className="text-right">Fit Check</span>
          </div>

          {template.requiredMaterials.map((mat) => {
            const isPlate = isPlateMaterial(mat.materialId);
            const sheets = isPlate ? getAvailableSheets(mat.materialId) : [];
            const fitResult = isPlate
              ? checkSheetFit(mat.materialId, pieceDimensionMM)
              : null;
            const isExpanded = expandedSheets.has(mat.materialId);
            const fullCount = sheets.filter((s) => s.type === "full_sheet").length;
            const remnantCount = sheets.filter((s) => s.type === "remnant").length;

            return (
              <div key={mat.materialId} className="border-t border-wo-border-subtle">
                <div className="grid grid-cols-[1fr_120px_120px] gap-2 px-3 py-2.5 text-[11px]">
                  <div>
                    <span className="text-slate-200">{mat.name}</span>
                    {isPlate && (
                      <button
                        onClick={() => toggleExpand(mat.materialId)}
                        className="ml-2 text-[9px] text-blue-400 hover:text-blue-300 underline underline-offset-2 transition-colors"
                      >
                        {isExpanded ? "ascunde plăci ▲" : "vezi plăci ▼"}
                      </button>
                    )}
                    {!isPlate && (
                      <span className="ml-2 text-[9px] text-slate-600">
                        (necesar: {mat.quantity} {mat.unit} · stoc: {mat.stockCurrent} {mat.unit})
                      </span>
                    )}
                  </div>

                  <div className="text-center">
                    {isPlate ? (
                      <div className="flex flex-col items-center">
                        <span className="text-slate-200 font-mono font-bold">
                          {sheets.length} plăci
                        </span>
                        <span className="text-[9px] text-slate-500">
                          {fullCount} complete · {remnantCount} resturi
                        </span>
                      </div>
                    ) : (
                      <span
                        className={`font-mono font-bold ${
                          mat.stockCurrent < mat.quantity
                            ? "text-red-400"
                            : "text-emerald-400"
                        }`}
                      >
                        {mat.stockCurrent} {mat.unit}
                      </span>
                    )}
                  </div>

                  <div className="flex justify-end items-center">
                    {isPlate && fitResult ? (
                      <span
                        className={`inline-flex items-center gap-1 px-2 py-0.5 text-[10px] font-bold rounded border ${fitCheckConfig[fitResult.result].cls}`}
                      >
                        {fitCheckConfig[fitResult.result].icon}{" "}
                        {fitCheckConfig[fitResult.result].label}
                      </span>
                    ) : (
                      <span
                        className={`text-right font-semibold ${stockStatusCls[mat.stockStatus]}`}
                      >
                        {mat.stockCurrent < mat.quantity
                          ? "⚠ INSUFICIENT"
                          : stockStatusLabel[mat.stockStatus]}
                      </span>
                    )}
                  </div>
                </div>

                {/* Expanded sheet breakdown */}
                {isPlate && isExpanded && (
                  <div className="px-4 pb-3">
                    <SheetBreakdown materialId={mat.materialId} />
                    {fitResult && fitResult.result === "no_fit" && (
                      <div className="flex items-center gap-2 mt-2 px-2 py-1.5 bg-red-900/20 border border-red-800/30 rounded">
                        <XCircle className="w-3 h-3 text-red-400 shrink-0" />
                        <p className="text-[10px] text-red-300">
                          Nicio placă disponibilă nu poate acomoda piesa de{" "}
                          <strong>{pieceDimensionMM}mm</strong>. Necesită comandă plăci noi.
                        </p>
                      </div>
                    )}
                    {fitResult && fitResult.result === "limited" && (
                      <div className="flex items-center gap-2 mt-2 px-2 py-1.5 bg-amber-900/15 border border-amber-800/30 rounded">
                        <AlertTriangle className="w-3 h-3 text-amber-400 shrink-0" />
                        <p className="text-[10px] text-amber-300">
                          Piesa încape doar pe plăci complete. Resturile sunt prea mici (min side &lt; {pieceDimensionMM}mm).
                        </p>
                      </div>
                    )}
                  </div>
                )}
              </div>
            );
          })}
        </div>

        {hasIssues && (
          <div className="flex items-start gap-2 mt-3 px-3 py-2 bg-amber-900/10 border border-amber-800/20 rounded-lg">
            <AlertTriangle className="w-3.5 h-3.5 text-amber-400 mt-0.5 shrink-0" />
            <p className="text-[10px] text-amber-300/80">
              <strong>Atenție:</strong> Unele materiale au probleme de disponibilitate sau încadrare.
              Verificați detaliile per material și contactați <strong>Operational Core</strong> pentru reaprovizionare.
            </p>
          </div>
        )}
      </div>

      {/* Nesting info notice */}
      <div className="flex items-start gap-2 mt-4 px-3 py-2 bg-blue-900/10 border border-blue-800/20 rounded-lg">
        <Info className="w-3.5 h-3.5 text-blue-400 mt-0.5 shrink-0" />
        <p className="text-[10px] text-blue-300/80">
          <strong>Stoc pe plăci fizice:</strong> Materialele tip placă sunt afișate cu dimensiunile reale ale fiecărei plăci din stoc.
          Fit Check verifică dacă piesa de <strong>{pieceDimensionMM}mm</strong> încape pe plăcile disponibile.
          Nesting-ul complet (optimizare tăiere 2D) se realizează în modulul <strong>NestingEngine</strong> la lansarea în producție.
        </p>
      </div>

      {/* PS notice */}
      <div className="flex items-start gap-2 mt-3 px-3 py-2 bg-purple-900/10 border border-purple-800/20 rounded-lg">
        <Info className="w-3.5 h-3.5 text-purple-400 mt-0.5 shrink-0" />
        <p className="text-[10px] text-purple-300/80">
          Datele sunt preluate din <strong>ProductSystem</strong> pe baza familiei de produs selectate.
          Configurația finală (dimensiuni exacte, materiale specifice) se definește la nivel de ofertă.
        </p>
      </div>
    </div>
  );
}

function NoTemplateSection({ familyName }: { familyName: string }) {
  return (
    <div className="bg-wo-surface-raised border border-wo-border-subtle rounded-lg p-5">
      <SectionHeader
        title="Informații Produs — ProductSystem"
        icon={<Package className="w-4 h-4 text-purple-400" />}
      />
      <div className="flex items-center gap-2 mt-3 px-3 py-2 bg-amber-900/10 border border-amber-800/20 rounded-lg">
        <AlertTriangle className="w-3.5 h-3.5 text-amber-400 shrink-0" />
        <p className="text-[11px] text-amber-300/80">
          Nu s-a găsit un șablon de producție pentru familia <strong>"{familyName}"</strong>.
          Contactați echipa ProductSystem pentru configurare.
        </p>
      </div>
    </div>
  );
}

function InvalidIntakeDataSection({
  intakeCode,
  issues,
  productFamily,
  confirmedTemplateCode,
  status,
  onBack,
}: {
  intakeCode: string;
  issues: string[];
  productFamily: string | null | undefined;
  confirmedTemplateCode: string | null | undefined;
  status: string | null | undefined;
  onBack: () => void;
}) {
  return (
    <div
      className="flex flex-col items-center justify-center h-full gap-4 px-6"
      data-testid="invalid-intake-data"
    >
      <AlertTriangle className="w-12 h-12 text-amber-500" />
      <p className="text-[14px] text-slate-300 text-center max-w-lg">
        Cererea există, dar datele sunt incomplete sau invalide pentru afișare.
      </p>
      <p className="text-[11px] text-slate-500 text-center max-w-md">
        Cod: <span className="font-mono text-blue-400">{intakeCode}</span>
        {" · "}
        Familie: <span className="font-mono">{productFamily || "—"}</span>
        {" · "}
        Template: <span className="font-mono">{confirmedTemplateCode || "—"}</span>
        {" · "}
        Status: <span className="font-mono">{status || "—"}</span>
      </p>
      <p className="text-[11px] text-amber-300/80 text-center max-w-md">
        Probleme detectate: {issues.join(", ")}
      </p>
      <button
        type="button"
        onClick={onBack}
        className="flex items-center gap-2 px-4 py-2 bg-blue-600 hover:bg-blue-500 text-white rounded-lg text-[12px] font-semibold transition-colors"
      >
        <ArrowLeft className="w-4 h-4" />
        Înapoi la Work Intake
      </button>
    </div>
  );
}

function IntakeWorkspaceDiagnosticBadge({ shell }: { shell: ReturnType<typeof resolveIntakeWorkspaceShell> }) {
  if (!shouldShowIntakeWorkspaceDiagnostic()) return null;
  return (
    <p
      className="text-[10px] font-mono text-slate-600 border border-slate-800 rounded px-2 py-0.5"
      data-testid="intake-workspace-diagnostic"
    >
      {intakeWorkspaceDiagnosticLabel(shell)}
    </p>
  );
}

function UnresolvedWorkTypeSection({
  onChooseWorkType,
  workTypePickerOpen,
  workTypePicker,
  selectingWorkType,
}: {
  onChooseWorkType: () => void;
  workTypePickerOpen: boolean;
  workTypePicker: React.ReactNode;
  selectingWorkType: boolean;
}) {
  return (
    <div
      id={INTAKE_SECTION_IDS.template}
      className="bg-wo-surface-raised border border-wo-border-subtle rounded-lg p-5 scroll-mt-4"
      data-testid="unresolved-work-type-section"
    >
      <SectionHeader
        title="Tip lucrare — nespecificat"
        icon={<Package className="w-4 h-4 text-amber-400" />}
      />
      <div
        className="mt-3 rounded-lg border border-amber-800/40 bg-amber-950/20 px-3 py-3 space-y-1"
        data-testid="unresolved-work-type-guidance"
      >
        <p className="text-[12px] font-semibold text-amber-200">
          Tipul lucrării nu este ales încă.
        </p>
        <p className="text-[11px] text-amber-300/90 leading-relaxed">
          {STAGE0_WORK_TYPE_GUIDANCE}
        </p>
      </div>
      <div className="mt-3 grid grid-cols-1 sm:grid-cols-2 gap-3 text-[12px]">
        <div className="rounded-lg border border-wo-border-strong bg-wo-surface-inset px-3 py-2">
          <p className="text-[10px] uppercase tracking-wide text-slate-500">Tip lucrare</p>
          <p className="text-slate-200 font-semibold">neales</p>
        </div>
        <div className="rounded-lg border border-wo-border-strong bg-wo-surface-inset px-3 py-2">
          <p className="text-[10px] uppercase tracking-wide text-slate-500">Template</p>
          <p className="text-slate-200 font-semibold">neconfirmat</p>
        </div>
        <div className="rounded-lg border border-wo-border-strong bg-wo-surface-inset px-3 py-2">
          <p className="text-[10px] uppercase tracking-wide text-slate-500">Specificație</p>
          <p className="text-slate-200 font-semibold">neîncepută</p>
        </div>
        <div className="rounded-lg border border-wo-border-strong bg-wo-surface-inset px-3 py-2">
          <p className="text-[10px] uppercase tracking-wide text-slate-500">Stare</p>
          <p className="text-slate-200 font-semibold">Nou / incomplet</p>
        </div>
      </div>
      <p className="mt-3 text-[11px] text-slate-400" data-testid="stage0-spec-message">
        {STAGE0_SPEC_MESSAGE}
      </p>
      <button
        type="button"
        onClick={onChooseWorkType}
        data-testid="choose-work-type-cta"
        disabled={selectingWorkType}
        className="mt-3 inline-flex items-center gap-1.5 px-3 py-2 text-[12px] font-semibold rounded-lg bg-blue-600 hover:bg-blue-500 text-white border border-blue-500/40 transition-colors disabled:opacity-50"
      >
        {selectingWorkType ? "Se salvează…" : "Alege tip lucrare"}
      </button>
      {workTypePickerOpen && (
        <div className="mt-4 pt-4 border-t border-wo-border-subtle" data-testid="unresolved-work-type-picker">
          {workTypePicker}
        </div>
      )}
    </div>
  );
}

function BackendAssistSection({
  loading,
  error,
  templateSuggestions,
  materialItems,
  materialAssistAvailable,
  materialBlockers,
  onApplySuggestion,
  appliedSuggestionId,
  confirmedTemplateCode,
  confirmingSuggestion,
}: {
  loading: boolean;
  error: string | null;
  templateSuggestions: ProductTemplateSuggestionItem[];
  materialItems: MaterialSheetAssistItem[];
  materialAssistAvailable: boolean;
  materialBlockers: string[];
  onApplySuggestion: (suggestion: ProductTemplateSuggestionItem) => void;
  appliedSuggestionId: string | null;
  confirmedTemplateCode?: string | null;
  confirmingSuggestion?: boolean;
}) {
  const blockersSheetQualityUrl = buildSheetQualityInvalidSummaryUrl();

  return (
    <div
      id={INTAKE_SECTION_IDS.template}
      className="bg-wo-surface-raised border border-wo-border-subtle rounded-lg p-5 scroll-mt-4"
    >
      <SectionHeader
        title="Asistență Intake — Contract Backend"
        icon={<Package className="w-4 h-4 text-purple-400" />}
      />

      <div className="flex items-start gap-2 mt-3 px-3 py-2 bg-blue-900/10 border border-blue-800/20 rounded-lg">
        <Info className="w-3.5 h-3.5 text-blue-400 mt-0.5 shrink-0" />
        <p className="text-[10px] text-blue-300/80">
          Asistența este doar orientativă. Nu creează oferte/comenzi și nu modifică ProductSystem, Inventory sau CostEngine.
          Orice sugestie necesită confirmare explicită operator.
        </p>
      </div>

      {loading && (
        <div className="flex items-center gap-2 mt-3 px-3 py-2 bg-slate-900/40 border border-slate-700 rounded-lg text-[11px] text-slate-300">
          <Loader2 className="w-3.5 h-3.5 animate-spin" />
          Se încarcă asistența backend...
        </div>
      )}

      {error && (
        <div className="flex items-start gap-2 mt-3 px-3 py-2 bg-red-900/20 border border-red-800/40 rounded-lg text-[11px] text-red-300">
          <AlertTriangle className="w-3.5 h-3.5 mt-0.5 shrink-0" />
          {error}
        </div>
      )}

      {confirmedTemplateCode && (
        <div className="mt-4 flex items-center gap-2 px-3 py-2 bg-emerald-900/15 border border-emerald-800/40 rounded-lg">
          <CheckCircle2 className="w-4 h-4 text-emerald-400 shrink-0" />
          <p className="text-[12px] text-emerald-300">
            Template confirmat:{" "}
            <span className="font-mono font-semibold">{confirmedTemplateCode}</span>
          </p>
        </div>
      )}

      <div className="mt-4">
        <p className="text-[11px] font-semibold text-slate-300 mb-2">Sugestii Product Template</p>
        {templateSuggestions.length === 0 ? (
          <div className="px-3 py-2 bg-amber-900/15 border border-amber-800/30 rounded-lg text-[11px] text-amber-300/90">
            Requires backend contract: nu există sugestii eligibile pentru acest intake.
          </div>
        ) : (
          <div className="space-y-2">
            {templateSuggestions.map((item) => {
              const applied = appliedSuggestionId === item.template_id;
              return (
                <div key={item.template_id} className="px-3 py-2 bg-wo-surface-inset border border-wo-border-strong rounded-lg">
                  <div className="flex items-center justify-between gap-3">
                    <div>
                      <p className="text-[12px] text-wo-text-primary font-semibold">{item.template_name}</p>
                      <p className="text-[10px] text-slate-400">{item.family} · confidence {item.confidence}</p>
                    </div>
                    <button
                      onClick={() => onApplySuggestion(item)}
                      disabled={confirmingSuggestion}
                      className={`px-3 py-1.5 rounded text-[10px] font-bold transition-colors disabled:opacity-50 ${
                        applied
                          ? "bg-emerald-900/30 text-emerald-300 border border-emerald-700"
                          : "bg-blue-600 hover:bg-blue-500 text-white"
                      }`}
                    >
                      {applied ? "Confirmat" : confirmingSuggestion ? "Se salvează…" : "Confirmă sugestia"}
                    </button>
                  </div>
                  {item.match_reasons.length > 0 && (
                    <p className="mt-1 text-[10px] text-slate-400">{item.match_reasons.join("; ")}</p>
                  )}
                </div>
              );
            })}
          </div>
        )}
      </div>

      <div className="mt-4">
        <p className="text-[11px] font-semibold text-slate-300 mb-2">Material / Sheet Assist</p>
        {!materialAssistAvailable && (
          <div className="px-3 py-2 bg-amber-900/15 border border-amber-800/30 rounded-lg text-[11px] text-amber-300/90 mb-2">
            Requires backend contract: {materialBlockers[0] || "sheet format contract missing"}
            <div className="mt-1">
              <Link
                to={blockersSheetQualityUrl}
                className="text-[10px] font-semibold text-blue-300 hover:text-blue-200 underline underline-offset-2"
              >
                Deschide Inventory Sheet Quality (invalid + would_block)
              </Link>
            </div>
          </div>
        )}
        <div className="space-y-1">
          {materialItems.slice(0, 6).map((item) => (
            <div key={item.material_id} className="px-3 py-2 bg-wo-surface-inset border border-wo-border-strong rounded-lg flex items-center justify-between gap-3">
              <div className="min-w-0">
                <p className="text-[11px] text-slate-200">{item.material_name}</p>
                <p className="text-[10px] text-slate-500">{item.category} · {item.status}</p>
                {item.sheet_format?.type === "sheet" && item.sheet_format.width && item.sheet_format.height && (
                  <p className="text-[10px] text-slate-500">
                    sheet {item.sheet_format.width} x {item.sheet_format.height} {item.sheet_format.unit}
                  </p>
                )}
                {item.fit_reason && <p className="text-[10px] text-slate-400 truncate">{item.fit_reason}</p>}
              </div>
              <div className="flex flex-col items-end gap-1">
                <span className="text-[10px] text-slate-400">fit: {item.fit_status}</span>
                <Link
                  to={buildSheetQualityMaterialUrl(item.material_id)}
                  className="text-[10px] font-semibold text-blue-300 hover:text-blue-200 underline underline-offset-2"
                >
                  Open Sheet Quality
                </Link>
              </div>
            </div>
          ))}
        </div>
      </div>
    </div>
  );
}

// ============================================================
// AUDIT TEREN SECTION — Redesigned for Totem/Install workflows
// ============================================================
type SurfaceType = "" | "concrete" | "asphalt" | "earth" | "paving" | "other";
type FoundationResponsibility = "" | "us" | "client" | "existing";

interface AuditState {
  address: string;
  addressSelected: boolean;
  mapsOpened: boolean;
  addressConfirmed: boolean;
  photosStatus: "none" | "link_sent" | "received";
  photoLink: string;
  // Technical fields — redesigned
  techPowerSource: string;
  surfaceType: SurfaceType;
  foundationResponsibility: FoundationResponsibility;
  foundationClientConfirmed: boolean;
  existingFoundationDims: string;
  heavyEquipmentAccess: string; // "" | "yes" | "no"
}

function AuditTerenSection({
  audit,
  onAuditChange,
  isTotemFamily,
  autoHeight,
}: {
  audit: AuditState;
  onAuditChange: (update: Partial<AuditState>) => void;
  /** Whether the product family is Totemuri/Pyloni — shows extra fields */
  isTotemFamily: boolean;
  /** Auto-deduced height from product dimensions (mm → m) */
  autoHeight: number | null;
}) {
  const [addressQuery, setAddressQuery] = useState(audit.address);
  const [suggestions, setSuggestions] = useState<MapSuggestion[]>([]);
  const [showSuggestions, setShowSuggestions] = useState(false);

  const isAddressComplete = audit.addressConfirmed && audit.address.length > 0;
  const isPhotosComplete = audit.photosStatus === "received";

  // Tech completeness depends on context
  const isTechComplete = (() => {
    // Power source is always required
    if (audit.techPowerSource === "") return false;
    if (isTotemFamily) {
      // Totem-specific: surface type, foundation, heavy equipment access
      if (audit.surfaceType === "") return false;
      if (audit.foundationResponsibility === "") return false;
      if (audit.foundationResponsibility === "client" && !audit.foundationClientConfirmed) return false;
      if (audit.foundationResponsibility === "existing" && audit.existingFoundationDims.trim() === "") return false;
      if (audit.heavyEquipmentAccess === "") return false;
    }
    return true;
  })();

  const totalChecks = 3;
  const completedCount =
    (isAddressComplete ? 1 : 0) +
    (isPhotosComplete ? 1 : 0) +
    (isTechComplete ? 1 : 0);

  const allComplete = completedCount === totalChecks;

  const handleAddressInput = (val: string) => {
    setAddressQuery(val);
    onAuditChange({ address: val, addressSelected: false, mapsOpened: false, addressConfirmed: false });
    const results = searchAddresses(val);
    setSuggestions(results);
    setShowSuggestions(results.length > 0);
  };

  const selectAddress = (suggestion: MapSuggestion) => {
    setAddressQuery(suggestion.description);
    onAuditChange({ address: suggestion.description, addressSelected: true, mapsOpened: false, addressConfirmed: false });
    setShowSuggestions(false);
  };

  const googleMapsUrl = audit.address
    ? `https://www.google.com/maps/search/?api=1&query=${encodeURIComponent(audit.address)}`
    : "";

  const handleOpenMaps = () => {
    if (googleMapsUrl) {
      window.open(googleMapsUrl, "_blank", "noopener,noreferrer");
      onAuditChange({ mapsOpened: true });
    }
  };

  const handleConfirmAddress = () => {
    onAuditChange({ addressConfirmed: true });
  };

  const generatePhotoLink = () => {
    const link = `https://upload.workos.ro/${Date.now().toString(36)}`;
    onAuditChange({ photosStatus: "link_sent", photoLink: link });
  };

  const simulatePhotosReceived = () => {
    onAuditChange({ photosStatus: "received" });
  };

  // Photo labels depend on product family
  const photoLabels = isTotemFamily
    ? ["Locul de montaj", "Suprafață / Teren", "Perspectivă zonă"]
    : ["Fațadă frontală", "Detaliu suport", "Perspectivă laterală"];

  return (
    <div
      id={INTAKE_SECTION_IDS.terrain}
      className="bg-wo-surface-raised border border-wo-border-subtle rounded-lg p-5 scroll-mt-4"
      data-testid="intake-audit-teren-section"
    >
      <div className="flex items-center justify-between mb-4">
        <SectionHeader
          title="Detalii Tehnice Client"
          icon={<Shield className="w-4 h-4 text-red-400" />}
        />
        <div className="flex items-center gap-2">
          <div className="flex gap-1">
            {Array.from({ length: totalChecks }).map((_, i) => (
              <div
                key={i}
                className={`w-3 h-3 rounded-full transition-colors ${
                  i < completedCount ? "bg-emerald-500" : "bg-slate-700"
                }`}
              />
            ))}
          </div>
          <span
            className={`text-[12px] font-bold ${allComplete ? "text-emerald-400" : "text-red-400"}`}
          >
            {completedCount}/{totalChecks}
          </span>
        </div>
      </div>

      {!allComplete && (
        <div className="flex items-center gap-2 px-3 py-2 bg-red-900/15 border border-red-800/30 rounded-lg mb-4">
          <AlertTriangle className="w-4 h-4 text-red-400 shrink-0" />
          <p className="text-[11px] text-red-300">
            <strong>BLOCAJ:</strong> Fluxul nu poate avansa până la completarea
            tuturor celor {totalChecks} verificări.
          </p>
        </div>
      )}

      <div className="space-y-4">
        {/* 1. Adresă Montaj */}
        <div
          className={`bg-wo-surface-inset border rounded-lg p-4 ${isAddressComplete ? "border-emerald-800/40" : "border-red-800/30"}`}
        >
          <div className="flex items-center justify-between mb-2">
            <div className="flex items-center gap-2">
              <MapPin
                className={`w-4 h-4 ${isAddressComplete ? "text-emerald-400" : "text-red-400"}`}
              />
              <p className="text-[13px] font-semibold text-slate-200">
                Adresă Montaj
              </p>
            </div>
            {isAddressComplete ? (
              <span className="px-2 py-0.5 text-[10px] font-bold bg-emerald-900/40 text-emerald-400 border border-emerald-700 rounded">
                COMPLETAT
              </span>
            ) : (
              <span className="px-2 py-0.5 text-[10px] font-bold bg-red-900/40 text-red-400 border border-red-700 rounded animate-pulse">
                OBLIGATORIU
              </span>
            )}
          </div>
          <div className="space-y-3">
            <div className="relative">
              <div className="flex items-center gap-2 bg-wo-surface-raised border border-wo-border-strong rounded-lg px-3 py-2.5 focus-within:border-blue-500/50">
                <MapPin className="w-4 h-4 text-slate-500 shrink-0" />
                <input
                  type="text"
                  value={addressQuery}
                  onChange={(e) => handleAddressInput(e.target.value)}
                  onFocus={() => suggestions.length > 0 && setShowSuggestions(true)}
                  onBlur={() => setTimeout(() => setShowSuggestions(false), 200)}
                  placeholder="Caută adresa de montaj (Google Maps)..."
                  className="bg-transparent text-[13px] text-slate-200 placeholder:text-slate-600 outline-none w-full"
                  disabled={audit.addressConfirmed}
                />
                {isAddressComplete && (
                  <CheckCircle2 className="w-4 h-4 text-emerald-400 shrink-0" />
                )}
              </div>
              {showSuggestions && (
                <div className="absolute z-10 top-full left-0 right-0 mt-1 bg-wo-surface-raised border border-wo-border-strong rounded-lg shadow-xl overflow-hidden">
                  {suggestions.map((s) => (
                    <button
                      key={s.placeId}
                      onMouseDown={() => selectAddress(s)}
                      className="w-full flex items-center gap-3 px-3 py-2.5 hover:bg-[#253048] transition-colors text-left"
                    >
                      <MapPin className="w-3.5 h-3.5 text-blue-400 shrink-0" />
                      <div>
                        <p className="text-[12px] text-slate-200">{s.mainText}</p>
                        <p className="text-[10px] text-slate-500">{s.secondaryText}</p>
                      </div>
                    </button>
                  ))}
                </div>
              )}
            </div>

            {audit.addressSelected && !audit.addressConfirmed && (
              <div className="flex items-center gap-3 text-[11px] text-slate-400">
                <div className="flex items-center gap-1.5">
                  <div className="w-5 h-5 rounded-full bg-emerald-600 flex items-center justify-center text-[10px] font-bold text-white">1</div>
                  <span className="text-emerald-400 font-medium">Adresă selectată</span>
                </div>
                <div className="w-4 h-px bg-slate-600" />
                <div className="flex items-center gap-1.5">
                  <div className={`w-5 h-5 rounded-full flex items-center justify-center text-[10px] font-bold ${audit.mapsOpened ? "bg-emerald-600 text-white" : "bg-slate-700 text-slate-400"}`}>2</div>
                  <span className={audit.mapsOpened ? "text-emerald-400 font-medium" : "text-slate-500"}>Validat pe Maps</span>
                </div>
                <div className="w-4 h-px bg-slate-600" />
                <div className="flex items-center gap-1.5">
                  <div className="w-5 h-5 rounded-full bg-slate-700 flex items-center justify-center text-[10px] font-bold text-slate-400">3</div>
                  <span className="text-slate-500">Confirmat</span>
                </div>
              </div>
            )}

            {audit.addressSelected && !audit.addressConfirmed && (
              <div className="bg-wo-surface-raised border border-wo-border-strong rounded-lg p-3 space-y-2">
                <div>
                  <p className="text-[10px] text-slate-500 uppercase tracking-wide mb-1">
                    Link Google Maps
                  </p>
                  <a
                    href={googleMapsUrl}
                    target="_blank"
                    rel="noopener noreferrer"
                    onClick={() => onAuditChange({ mapsOpened: true })}
                    className="text-[12px] text-blue-400 hover:text-blue-300 font-mono break-all underline underline-offset-2"
                  >
                    {googleMapsUrl}
                  </a>
                </div>
                <div className="flex items-center gap-2 pt-1">
                  <button
                    onClick={handleOpenMaps}
                    className="flex items-center gap-2 px-3 py-2 bg-blue-600 hover:bg-blue-500 text-white rounded-lg text-[12px] font-semibold transition-colors"
                  >
                    <MapPin className="w-3.5 h-3.5" />
                    Validează pe Google Maps
                  </button>
                  {audit.mapsOpened && (
                    <button
                      onClick={handleConfirmAddress}
                      className="flex items-center gap-2 px-3 py-2 bg-emerald-600 hover:bg-emerald-500 text-white rounded-lg text-[12px] font-semibold transition-colors animate-pulse"
                    >
                      <CheckCircle2 className="w-3.5 h-3.5" />
                      Confirm Adresă ✓
                    </button>
                  )}
                </div>
                {!audit.mapsOpened && (
                  <p className="text-[10px] text-amber-400/80 flex items-center gap-1">
                    <AlertTriangle className="w-3 h-3" />
                    Deschide link-ul Maps pentru a verifica locația înainte de confirmare
                  </p>
                )}
              </div>
            )}

            {audit.addressConfirmed && (
              <div className="bg-wo-surface-raised border border-emerald-800/30 rounded-lg p-3">
                <div className="flex items-center justify-between">
                  <div className="flex items-center gap-2">
                    <CheckCircle2 className="w-4 h-4 text-emerald-400" />
                    <p className="text-[12px] text-emerald-400 font-semibold">
                      Adresă validată pe Google Maps și confirmată
                    </p>
                  </div>
                  <button
                    onClick={() => {
                      setAddressQuery("");
                      onAuditChange({ addressSelected: false, mapsOpened: false, addressConfirmed: false, address: "" });
                    }}
                    className="text-[10px] text-slate-500 hover:text-slate-300 transition-colors underline"
                  >
                    Resetează
                  </button>
                </div>
                <a
                  href={googleMapsUrl}
                  target="_blank"
                  rel="noopener noreferrer"
                  className="text-[11px] text-blue-400/70 hover:text-blue-300 font-mono break-all mt-1 block"
                >
                  {googleMapsUrl}
                </a>
              </div>
            )}
          </div>
        </div>

        {/* 2. Poze Locație Montaj */}
        <div
          className={`bg-wo-surface-inset border rounded-lg p-4 ${isPhotosComplete ? "border-emerald-800/40" : "border-red-800/30"}`}
        >
          <div className="flex items-center justify-between mb-2">
            <div className="flex items-center gap-2">
              <Camera
                className={`w-4 h-4 ${isPhotosComplete ? "text-emerald-400" : "text-red-400"}`}
              />
              <p className="text-[13px] font-semibold text-slate-200">
                Poze Locație Montaj
              </p>
            </div>
            {isPhotosComplete ? (
              <span className="px-2 py-0.5 text-[10px] font-bold bg-emerald-900/40 text-emerald-400 border border-emerald-700 rounded">
                PRIMIT
              </span>
            ) : audit.photosStatus === "link_sent" ? (
              <span className="px-2 py-0.5 text-[10px] font-bold bg-amber-900/40 text-amber-400 border border-amber-700 rounded">
                AȘTEPTARE
              </span>
            ) : (
              <span className="px-2 py-0.5 text-[10px] font-bold bg-red-900/40 text-red-400 border border-red-700 rounded animate-pulse">
                OBLIGATORIU
              </span>
            )}
          </div>

          {audit.photosStatus === "none" && (
            <div className="space-y-2">
              <p className="text-[11px] text-slate-400">
                Generează un link unic pentru client. Acesta va putea încărca
                pozele cu locul de montaj direct de pe telefon.
              </p>
              {isTotemFamily && (
                <div className="flex items-start gap-2 px-3 py-2 bg-blue-900/10 border border-blue-800/20 rounded-lg">
                  <Info className="w-3.5 h-3.5 text-blue-400 mt-0.5 shrink-0" />
                  <p className="text-[10px] text-blue-300/80">
                    <strong>Totem:</strong> Clientul trebuie să fotografieze locul exact de montaj,
                    suprafața terenului (beton/pământ) și o perspectivă de ansamblu a zonei.
                  </p>
                </div>
              )}
              <div className="flex gap-2">
                <button
                  onClick={generatePhotoLink}
                  className="flex items-center gap-2 px-3 py-2 bg-blue-600 hover:bg-blue-500 text-white rounded-lg text-[12px] font-semibold transition-colors"
                >
                  <Link2 className="w-3.5 h-3.5" />
                  Generează Link Unic
                </button>
              </div>
            </div>
          )}

          {audit.photosStatus === "link_sent" && (
            <div className="space-y-3">
              <div className="bg-wo-surface-raised border border-wo-border-strong rounded-lg p-3">
                <p className="text-[10px] text-slate-500 uppercase tracking-wide mb-1">
                  Link Upload
                </p>
                <p className="text-[12px] text-blue-400 font-mono break-all">
                  {audit.photoLink}
                </p>
              </div>
              <div className="flex items-center gap-2">
                <button className="flex items-center gap-2 px-3 py-2 bg-emerald-700 hover:bg-emerald-600 text-white rounded-lg text-[11px] font-semibold transition-colors">
                  <Smartphone className="w-3.5 h-3.5" />
                  Trimite SMS
                </button>
                <button className="flex items-center gap-2 px-3 py-2 bg-emerald-700 hover:bg-emerald-600 text-white rounded-lg text-[11px] font-semibold transition-colors">
                  <MessageSquare className="w-3.5 h-3.5" />
                  Trimite WhatsApp
                </button>
              </div>
              <div className="flex items-center gap-2 px-3 py-2 bg-amber-900/15 border border-amber-800/30 rounded-lg">
                <Loader2 className="w-3.5 h-3.5 text-amber-400 animate-spin" />
                <p className="text-[11px] text-amber-300">
                  Așteptare poze de la client...
                </p>
                <button
                  onClick={simulatePhotosReceived}
                  className="ml-auto px-2 py-1 bg-slate-700 hover:bg-slate-600 text-slate-300 rounded text-[10px] font-medium transition-colors"
                >
                  Simulează Primire Poze
                </button>
              </div>
            </div>
          )}

          {audit.photosStatus === "received" && (
            <div className="space-y-2">
              <p className="text-[11px] text-emerald-400 font-medium">
                3 poze primite de la client
              </p>
              <div className="flex gap-2">
                {photoLabels.map((label, i) => (
                  <div
                    key={i}
                    className="flex-1 bg-wo-surface-raised border border-wo-border-strong rounded-lg p-3 flex flex-col items-center gap-1.5"
                  >
                    <div className="w-full aspect-[4/3] bg-slate-700/50 rounded flex items-center justify-center">
                      <Image className="w-6 h-6 text-slate-500" />
                    </div>
                    <p className="text-[10px] text-slate-400 text-center">
                      {label}
                    </p>
                  </div>
                ))}
              </div>
            </div>
          )}
        </div>

        {/* 3. Detalii Tehnice Client */}
        <div
          className={`bg-wo-surface-inset border rounded-lg p-4 ${isTechComplete ? "border-emerald-800/40" : "border-red-800/30"}`}
        >
          <div className="flex items-center justify-between mb-3">
            <div className="flex items-center gap-2">
              <Wrench
                className={`w-4 h-4 ${isTechComplete ? "text-emerald-400" : "text-red-400"}`}
              />
              <p className="text-[13px] font-semibold text-slate-200">
                Detalii Tehnice Teren
              </p>
            </div>
            {isTechComplete ? (
              <span className="px-2 py-0.5 text-[10px] font-bold bg-emerald-900/40 text-emerald-400 border border-emerald-700 rounded">
                COMPLETAT
              </span>
            ) : (
              <span className="px-2 py-0.5 text-[10px] font-bold bg-red-900/40 text-red-400 border border-red-700 rounded animate-pulse">
                OBLIGATORIU
              </span>
            )}
          </div>

          {/* Auto-deduced height for totems */}
          {isTotemFamily && autoHeight !== null && (
            <div className="flex items-center gap-2 mb-4 px-3 py-2.5 bg-purple-900/15 border border-purple-800/30 rounded-lg">
              <Package className="w-4 h-4 text-purple-400 shrink-0" />
              <div>
                <p className="text-[11px] text-purple-300 font-semibold">
                  Înălțime totem dedusă din specificații: <span className="font-mono text-purple-200">{autoHeight}m</span>
                </p>
                <p className="text-[9px] text-purple-400/70">
                  Extras automat din dimensiunile produsului. Nu necesită introducere manuală.
                </p>
              </div>
            </div>
          )}

          <div className="space-y-4">
            {/* Row 1: Power Source + Heavy Equipment Access */}
            <div className="grid grid-cols-1 md:grid-cols-2 gap-3">
              <div>
                <label className="text-[10px] text-slate-500 uppercase tracking-wide block mb-1 flex items-center gap-1">
                  <Zap className="w-3 h-3" />
                  Sursă curent disponibilă
                </label>
                <select
                  value={audit.techPowerSource}
                  onChange={(e) =>
                    onAuditChange({ techPowerSource: e.target.value })
                  }
                  className="w-full bg-wo-surface-raised border border-wo-border-strong rounded-lg px-3 py-2 text-[13px] text-slate-200 outline-none focus:border-blue-500/50"
                >
                  <option value="">— Selectează —</option>
                  <option value="220V">220V monofazat</option>
                  <option value="solar">Solar / Off-grid</option>
                  <option value="none">Nu există</option>
                </select>
              </div>

              {isTotemFamily && (
                <div>
                  <label className="text-[10px] text-slate-500 uppercase tracking-wide block mb-1 flex items-center gap-1">
                    <HardHat className="w-3 h-3" />
                    Acces utilaje grele (macara)
                  </label>
                  <select
                    value={audit.heavyEquipmentAccess}
                    onChange={(e) =>
                      onAuditChange({ heavyEquipmentAccess: e.target.value })
                    }
                    className="w-full bg-wo-surface-raised border border-wo-border-strong rounded-lg px-3 py-2 text-[13px] text-slate-200 outline-none focus:border-blue-500/50"
                  >
                    <option value="">— Selectează —</option>
                    <option value="yes">Da — acces liber pentru macara</option>
                    <option value="no">Nu — acces restricționat</option>
                  </select>
                  {audit.heavyEquipmentAccess === "no" && (
                    <p className="text-[10px] text-amber-400 mt-1 flex items-center gap-1">
                      <AlertTriangle className="w-3 h-3" />
                      Montajul poate necesita soluții alternative (nacela, montaj manual). Cost suplimentar posibil.
                    </p>
                  )}
                </div>
              )}
            </div>

            {/* Cable provision notice */}
            <div className="flex items-start gap-2 px-3 py-2 bg-wo-surface-raised border border-wo-border-strong rounded-lg">
              <Cable className="w-3.5 h-3.5 text-blue-400 mt-0.5 shrink-0" />
              <p className="text-[10px] text-slate-400">
                <strong className="text-slate-300">Alimentare electrică:</strong> Se includ standard{" "}
                <span className="font-mono text-blue-400 font-bold">5 ml</span> cablu de alimentare.
                Clientul are responsabilitatea de a trasa cablajul electric până în dreptul punctului de montaj.
              </p>
            </div>

            {/* Totem-specific fields */}
            {isTotemFamily && (
              <>
                {/* Surface Type */}
                <div>
                  <label className="text-[10px] text-slate-500 uppercase tracking-wide block mb-2">
                    Tip suprafață montaj
                  </label>
                  <div className="flex flex-wrap gap-2">
                    {([
                      { value: "concrete" as SurfaceType, label: "Beton / Asfalt", icon: "🏗️" },
                      { value: "earth" as SurfaceType, label: "Pământ / Iarbă", icon: "🌱" },
                      { value: "paving" as SurfaceType, label: "Pavaj / Dale", icon: "🧱" },
                      { value: "other" as SurfaceType, label: "Altul", icon: "❓" },
                    ]).map((opt) => {
                      const isActive = audit.surfaceType === opt.value;
                      return (
                        <button
                          key={opt.value}
                          onClick={() => onAuditChange({ surfaceType: opt.value })}
                          className={`inline-flex items-center gap-1.5 px-3 py-2 text-[12px] font-semibold rounded-lg border transition-colors ${
                            isActive
                              ? "bg-blue-600/20 text-blue-300 border-blue-500/50 ring-1 ring-blue-500/30"
                              : "bg-wo-surface-inset text-slate-500 border-wo-border-strong hover:border-slate-500 hover:text-slate-300"
                          }`}
                        >
                          <span>{opt.icon}</span>
                          {isActive && <CheckCircle2 className="w-3.5 h-3.5" />}
                          {opt.label}
                        </button>
                      );
                    })}
                  </div>
                </div>

                {/* Foundation Responsibility */}
                <div>
                  <label className="text-[10px] text-slate-500 uppercase tracking-wide block mb-2">
                    Fundație — Responsabilitate
                  </label>
                  <div className="space-y-2">
                    {([
                      {
                        value: "us" as FoundationResponsibility,
                        label: "Fundație realizată de noi",
                        desc: "Se adaugă automat în ofertă ca serviciu suplimentar",
                        cls: "border-blue-800/30",
                      },
                      {
                        value: "client" as FoundationResponsibility,
                        label: "Fundație realizată de client (in-house)",
                        desc: "Clientul își asumă crearea fundației conform specificațiilor noastre",
                        cls: "border-amber-800/30",
                      },
                      {
                        value: "existing" as FoundationResponsibility,
                        label: "Fundație existentă",
                        desc: "Se montează pe fundație existentă — necesită verificare dimensiuni",
                        cls: "border-emerald-800/30",
                      },
                    ]).map((opt) => {
                      const isActive = audit.foundationResponsibility === opt.value;
                      return (
                        <div key={opt.value}>
                          <button
                            onClick={() =>
                              onAuditChange({
                                foundationResponsibility: opt.value,
                                foundationClientConfirmed: false,
                                existingFoundationDims: "",
                              })
                            }
                            className={`w-full flex items-start gap-3 px-3 py-2.5 rounded-lg border transition-colors text-left ${
                              isActive
                                ? `bg-wo-surface-raised ${opt.cls} ring-1 ring-blue-500/20`
                                : "bg-wo-surface-inset border-wo-border-strong hover:border-slate-500"
                            }`}
                          >
                            <div
                              className={`w-4 h-4 rounded-full border-2 mt-0.5 shrink-0 flex items-center justify-center ${
                                isActive ? "border-blue-400" : "border-slate-600"
                              }`}
                            >
                              {isActive && (
                                <div className="w-2 h-2 rounded-full bg-blue-400" />
                              )}
                            </div>
                            <div>
                              <p className={`text-[12px] font-semibold ${isActive ? "text-slate-200" : "text-slate-400"}`}>
                                {opt.label}
                              </p>
                              <p className="text-[10px] text-slate-500">{opt.desc}</p>
                            </div>
                          </button>

                          {/* Client confirmation checkbox */}
                          {isActive && opt.value === "client" && (
                            <div className="ml-7 mt-2 px-3 py-2 bg-amber-900/10 border border-amber-800/20 rounded-lg">
                              <label className="flex items-start gap-2 cursor-pointer">
                                <input
                                  type="checkbox"
                                  checked={audit.foundationClientConfirmed}
                                  onChange={(e) =>
                                    onAuditChange({ foundationClientConfirmed: e.target.checked })
                                  }
                                  className="mt-0.5 accent-amber-500"
                                />
                                <span className="text-[11px] text-amber-300">
                                  <strong>Confirm:</strong> Clientul își asumă responsabilitatea creării fundației
                                  conform specificațiilor tehnice furnizate de noi. Fundația trebuie finalizată
                                  înainte de data de montaj.
                                </span>
                              </label>
                              {!audit.foundationClientConfirmed && (
                                <p className="text-[10px] text-red-400 mt-1 ml-5 flex items-center gap-1">
                                  <AlertTriangle className="w-3 h-3" />
                                  Confirmarea este obligatorie pentru a avansa
                                </p>
                              )}
                            </div>
                          )}

                          {/* Existing foundation dimensions */}
                          {isActive && opt.value === "existing" && (
                            <div className="ml-7 mt-2 px-3 py-2 bg-emerald-900/10 border border-emerald-800/20 rounded-lg">
                              <label className="text-[10px] text-slate-500 uppercase tracking-wide block mb-1">
                                Dimensiuni fundație existentă (mm)
                              </label>
                              <input
                                type="text"
                                value={audit.existingFoundationDims}
                                onChange={(e) =>
                                  onAuditChange({ existingFoundationDims: e.target.value })
                                }
                                placeholder="ex: 800×800×600mm"
                                className="w-full max-w-xs bg-wo-surface-raised border border-wo-border-strong rounded-lg px-3 py-2 text-[13px] text-slate-200 placeholder:text-slate-600 outline-none focus:border-blue-500/50 font-mono"
                              />
                              {audit.existingFoundationDims.trim() === "" && (
                                <p className="text-[10px] text-red-400 mt-1 flex items-center gap-1">
                                  <AlertTriangle className="w-3 h-3" />
                                  Dimensiunile sunt obligatorii pentru verificare compatibilitate
                                </p>
                              )}
                            </div>
                          )}
                        </div>
                      );
                    })}
                  </div>
                </div>
              </>
            )}
          </div>

          <div className="flex items-start gap-2 mt-4 px-3 py-2 bg-blue-900/10 border border-blue-800/20 rounded-lg">
            <Info className="w-3.5 h-3.5 text-blue-400 mt-0.5 shrink-0" />
            <p className="text-[10px] text-blue-300/80">
              Aceste câmpuri descriu <strong>terenul, accesul și responsabilitățile clientului</strong>.
              Câmpurile tehnice de produs (dimensiuni, materiale, configurație) sunt definite în secțiunea{" "}
              <strong>ProductSystem</strong> de mai sus.
            </p>
          </div>
        </div>
      </div>

      {/* Gate Result */}
      <div className="mt-4">
        {allComplete ? (
          <div className="flex items-center gap-2 px-4 py-3 bg-emerald-900/20 border border-emerald-800/40 rounded-lg">
            <CheckCircle2 className="w-5 h-5 text-emerald-400" />
            <div>
              <p className="text-[13px] text-emerald-400 font-semibold">
                Detalii Tehnice Client — Complet
              </p>
              <p className="text-[11px] text-emerald-300/70">
                Toate verificările sunt finalizate. Comanda poate avansa către
                ofertare.
              </p>
            </div>
          </div>
        ) : (
          <div className="flex items-center gap-2 px-4 py-3 bg-red-900/15 border border-red-800/30 rounded-lg">
            <XCircle className="w-5 h-5 text-red-400" />
            <div>
              <p className="text-[13px] text-red-400 font-semibold">
                Detalii Tehnice Client — Incomplet
              </p>
              <p className="text-[11px] text-red-300/70">
                {totalChecks - completedCount} verificare(i) rămase. Fluxul este blocat.
              </p>
            </div>
          </div>
        )}
      </div>
    </div>
  );
}

// ============================================================
// MAIN PAGE
// ============================================================
export default function IntakeDetail() {
  const { id } = useParams<{ id: string }>();
  const navigate = useNavigate();
  const { intakes, loading, error, source, refresh } = useBackendData();

  const request = intakes.find((r) => r.id === id);

  const confirmedTemplateCode = request?.confirmedTemplateCode ?? null;
  const showProduct001Spec = request
    ? shouldShowVolumetricProductForm(
        confirmedTemplateCode,
        request.productFamily,
        isLitereVolumetriceFamily
      )
    : false;
  const workspaceShell = request
    ? resolveIntakeWorkspaceShell(
        confirmedTemplateCode,
        request.productFamily
      )
    : null;
  const useVolumetricPage = workspaceShell === "volumetric_modular";
  const productSpecInitial = useMemo(
    () => parseIntakeProductSpec(request?.productSpec),
    [request?.productSpec]
  );
  const siteAuditParsed = useMemo(
    () => parseSiteAuditJson(request?.siteAudit),
    [request?.siteAudit]
  );

  const handleSaveProductSpec = useCallback(
    async (
      spec: IntakeProductSpec | null,
      options?: { skipRefresh?: boolean }
    ) => {
      if (!request || source === "mock") {
        throw new Error("Salvarea specificației necesită cerere din baza de date live.");
      }
      const rows = await intakesApi.list({ code: request.id }, { limit: 1 });
      const row = rows[0];
      if (!row) {
        throw new Error("Cererea nu a fost găsită în baza de date.");
      }
      await intakesApi.update(row.id, { product_spec_json: spec });
      if (!options?.skipRefresh) {
        await refresh();
      }
    },
    [request, source, refresh]
  );

  // CUI state
  const initialCUI = request ? clientCUIMap[request.client] || "" : "";
  const [companyData, setCompanyData] = useState<SmartBillCompany | null>(null);

  const [selectedDeliveryType, setSelectedDeliveryType] = useState<DeliveryType>(
    request?.deliveryType ?? "delivery_standard"
  );
  const [assignedTo, setAssignedTo] = useState(request?.assignedTo ?? "—");
  const [persistError, setPersistError] = useState<string | null>(null);
  const [confirmingSuggestion, setConfirmingSuggestion] = useState(false);
  const [markReadyLoading, setMarkReadyLoading] = useState(false);
  const [markReadyMessage, setMarkReadyMessage] = useState<string | null>(null);
  const [intakeDbId, setIntakeDbId] = useState<number | null>(request?.dbId ?? null);

  const requiresInstallAudit = request
    ? requiresTerrainAudit({
        deliveryType: selectedDeliveryType,
        productFamily: request.productFamily,
      })
    : false;

  const handleOpenPreliminaryQuote = useCallback(() => {
    if (!request) return;
    navigateToQuotesList(
      navigate,
      buildQuoteWizardNavStateFromIntake(
        {
          id: request.id,
          client: request.client,
          status: request.status,
          deliveryType: selectedDeliveryType,
          productSpec: productSpecInitial,
          confirmedTemplateCode: confirmedTemplateCode?.trim() || TPL_VOLUMETRIC_LETTERS,
          siteAudit: siteAuditParsed,
        },
        { openWizard: true }
      )
    );
  }, [
    navigate,
    productSpecInitial,
    request,
    confirmedTemplateCode,
    selectedDeliveryType,
    siteAuditParsed,
  ]);

  useEffect(() => {
    if (!request) return;
    setSelectedDeliveryType(request.deliveryType ?? "delivery_standard");
    setAssignedTo(request.assignedTo ?? "—");
    setAudit((prev) => ({
      ...prev,
      ...siteAuditToAuditUi(request.siteAudit),
    }));
    if (request.dbId) setIntakeDbId(request.dbId);
  }, [request?.id, request?.updatedAt, request?.deliveryType, request?.assignedTo, request?.siteAudit, request?.dbId]);

  useEffect(() => {
    if (!request || source === "mock") return;
    void resolveIntakeDbId(request.id).then((id) => {
      if (id) setIntakeDbId(id);
    });
  }, [request?.id, source]);

  const persistIntakeField = useCallback(
    async (patch: Parameters<typeof patchIntakeByCode>[1]) => {
      if (!request || source === "mock") {
        setPersistError("Salvarea necesită cerere din baza de date live.");
        return false;
      }
      const dbId = intakeDbId ?? (await resolveIntakeDbId(request.id));
      if (!dbId) {
        setPersistError("Cererea nu a fost găsită în baza de date.");
        return false;
      }
      setIntakeDbId(dbId);
      try {
        await patchIntakeByCode(request.id, patch);
        setPersistError(null);
        await refresh();
        return true;
      } catch (err) {
        setPersistError(err instanceof Error ? err.message : "Eroare la salvare.");
        return false;
      }
    },
    [intakeDbId, refresh, request, source]
  );

  const handleDeliveryTypeChange = useCallback(
    async (dt: DeliveryType) => {
      setSelectedDeliveryType(dt);
      await persistIntakeField({ delivery_type: dt });
    },
    [persistIntakeField]
  );

  const handleAssignedBlur = useCallback(async () => {
    const trimmed = assignedTo.trim();
    const display = trimmed || "—";
    setAssignedTo(display);
    await persistIntakeField({ assigned_to: trimmed || null });
  }, [assignedTo, persistIntakeField]);

  // Determine if this is a totem/pylon family
  const isTotemFamily = request?.productFamily === "Totemuri / Pyloni";

  // Auto-deduce height for totems from dimensions (first number is typically height in mm)
  const autoHeight = useMemo(() => {
    if (!request || !isTotemFamily) return null;
    const numbers = parseIntakeDimensionNumbers(request.dimensions);
    if (!numbers || numbers.length === 0) return null;
    const parsed = numbers.map(Number).filter((n) => n > 0);
    if (parsed.length === 0) return null;
    // For totems, the first/largest dimension is typically height
    const maxDim = Math.max(...parsed);
    return maxDim >= 1000 ? maxDim / 1000 : maxDim; // convert mm to m
  }, [request, isTotemFamily]);

  // Audit state — redesigned
  const [audit, setAudit] = useState<AuditState>({
    address: "",
    addressSelected: false,
    mapsOpened: false,
    addressConfirmed: false,
    photosStatus: "none",
    photoLink: "",
    techPowerSource: "",
    surfaceType: "",
    foundationResponsibility: "",
    foundationClientConfirmed: false,
    existingFoundationDims: "",
    heavyEquipmentAccess: "",
  });

  const handleAuditChange = useCallback(
    (update: Partial<AuditState>) => {
      setAudit((prev) => {
        const next = { ...prev, ...update };
        if (request && source !== "mock") {
          const siteJson = auditUiToSiteAudit(next, request.siteAudit);
          void (async () => {
            const dbId = intakeDbId ?? (await resolveIntakeDbId(request.id));
            if (!dbId) return;
            setIntakeDbId(dbId);
            try {
              await persistSiteAudit(dbId, siteJson);
            } catch {
              /* non-blocking — operator can retry via save */
            }
          })();
        }
        return next;
      });
    },
    [intakeDbId, request, source]
  );

  const [assistLoading, setAssistLoading] = useState(false);
  const [assistError, setAssistError] = useState<string | null>(null);
  const [templateSuggestions, setTemplateSuggestions] = useState<ProductTemplateSuggestionItem[]>([]);
  const [materialAssistItems, setMaterialAssistItems] = useState<MaterialSheetAssistItem[]>([]);
  const [materialAssistAvailable, setMaterialAssistAvailable] = useState(false);
  const [materialAssistBlockers, setMaterialAssistBlockers] = useState<string[]>([]);
  const appliedSuggestionId = useMemo(() => {
    if (!confirmedTemplateCode) return null;
    const match = templateSuggestions.find(
      (s) => s.template_name === confirmedTemplateCode
    );
    return match?.template_id ?? confirmedTemplateCode;
  }, [confirmedTemplateCode, templateSuggestions]);

  // Audit completeness — context-aware
  const isAuditComplete = (() => {
    if (!audit.addressConfirmed || audit.address.length === 0) return false;
    if (audit.photosStatus !== "received") return false;
    if (audit.techPowerSource === "") return false;
    if (isTotemFamily) {
      if (audit.surfaceType === "") return false;
      if (audit.foundationResponsibility === "") return false;
      if (audit.foundationResponsibility === "client" && !audit.foundationClientConfirmed) return false;
      if (audit.foundationResponsibility === "existing" && audit.existingFoundationDims.trim() === "") return false;
      if (audit.heavyEquipmentAccess === "") return false;
    }
    return true;
  })();

  // Identity check: CUI is optional for quote, mandatory for production
  const hasFiscalIdentity = companyData !== null || (request?.identity.type === "fiscal");

  // Product template — resolve by canonical family_id (registry slug).
  // After Sprint #4, request.productFamily must hold a canonical family_id slug.
  // Legacy label-based matching has been removed; intakes with stale labels will
  // cleanly fall through to NoTemplateSection (handled below).
  const allowMockOperationalAssist = source === "mock";
  const productTemplate = useMemo(() => {
    if (!request || !allowMockOperationalAssist) return undefined;
    return getTemplateByFamilyId(request.productFamily);
  }, [allowMockOperationalAssist, request]);

  // Extract minimum piece dimension from request dimensions for nesting fit check
  const pieceDimensionMM = useMemo(() => {
    if (!request) return 250;
    const parsed = parseIntakeDimensionNumbers(request.dimensions).filter(
      (n) => n < 50000
    );
    if (parsed.length === 0) return 250;
    const meaningful = parsed.filter((n) => n >= 50);
    if (meaningful.length === 0) return parsed[0];
    return Math.min(...meaningful);
  }, [request]);

  const parsedDims = useMemo(
    () => (request ? parseIntakeDimensionsStruct(request.dimensions) : null),
    [request]
  );

  const workTypeUnresolved = request
    ? isUnresolvedIntakeProductFamily(request.productFamily)
    : false;

  const showTerrainGates = request
    ? intakeTerrainGatesActive(request.productFamily, selectedDeliveryType)
    : false;

  const deliveryStageNote = request
    ? getDeliveryStageNote({
        deliveryType: selectedDeliveryType,
        productFamily: request.productFamily,
        siteAudit: siteAuditParsed,
      })
    : null;

  const [workTypePickerOpen, setWorkTypePickerOpen] = useState(false);
  const [productFamilies, setProductFamilies] = useState<ProductFamily[]>([]);
  const [familiesLoading, setFamiliesLoading] = useState(false);
  const [selectingWorkType, setSelectingWorkType] = useState(false);

  useEffect(() => {
    if (!request || source === "mock" || !workTypeUnresolved) {
      setProductFamilies([]);
      setFamiliesLoading(false);
      return;
    }
    let cancelled = false;
    setFamiliesLoading(true);
    productFamiliesApi
      .list({ limit: 500, sort: "label" })
      .then((rows) => {
        if (!cancelled) setProductFamilies(rows.items);
      })
      .catch(() => {
        if (!cancelled) setProductFamilies([]);
      })
      .finally(() => {
        if (!cancelled) setFamiliesLoading(false);
      });
    return () => {
      cancelled = true;
    };
  }, [request?.id, source, workTypeUnresolved]);

  const handleSelectWorkType = useCallback(
    async (workTypeId: string) => {
      if (!request || source === "mock" || workTypeId === "generic") return;
      const familyId = resolveWorkTypeFamilyId(workTypeId, productFamilies);
      if (familyId === null) return;
      setSelectingWorkType(true);
      const ok = await persistIntakeField({ product_family: familyId });
      setSelectingWorkType(false);
      if (ok) {
        setWorkTypePickerOpen(false);
      }
    },
    [persistIntakeField, productFamilies, request, source]
  );

  useEffect(() => {
    let cancelled = false;
    async function loadAssist() {
      if (!request || source === "mock" || isUnresolvedIntakeProductFamily(request.productFamily)) {
        setTemplateSuggestions([]);
        setMaterialAssistItems([]);
        setMaterialAssistAvailable(false);
        setMaterialAssistBlockers([]);
        setAssistError(null);
        setAssistLoading(false);
        return;
      }

      setAssistLoading(true);
      setAssistError(null);

      const listRes = await listProductTemplateAssist({ family_id: request.productFamily, limit: 30 });
      const suggestionRes = await suggestProductTemplates({
        intake_id: request.id,
        title: request.productFamily,
        description: request.description,
        requested_product_type: request.productFamily,
        dimensions: parsedDims,
        quantity: request.quantity,
      });

      if (cancelled) return;

      const allSuggestions = suggestionRes.data?.suggestions?.length
        ? suggestionRes.data.suggestions
        : (listRes.data?.items || []).map((item) => ({
            template_id: item.id,
            template_name: item.name,
            family: item.family,
            confidence: "low" as const,
            match_reasons: ["fallback from product-templates assist list"],
            missing_inputs: [],
            warnings: item.warnings,
            requires_operator_confirmation: true,
          }));
      setTemplateSuggestions(allSuggestions);

      const materialRes = await getMaterialSheetAssist({
        product_template_id: allSuggestions[0]?.template_id || null,
        material_category: null,
        dimensions: parsedDims,
        quantity: request.quantity,
        constraints: { rotation_allowed: true, indoor_outdoor: "unknown" },
      });

      if (cancelled) return;

      setMaterialAssistItems(materialRes.data?.items || []);
      setMaterialAssistAvailable(materialRes.data?.assist_available || false);
      setMaterialAssistBlockers(materialRes.data?.blockers || []);

      if (listRes.status === "error" || suggestionRes.status === "error" || materialRes.status === "error") {
        setAssistError("Backend assist unavailable momentan. Nu se aplică fallback mock în live mode.");
      }
      if (listRes.status === "contract-missing" || suggestionRes.status === "contract-missing" || materialRes.status === "contract-missing") {
        setAssistError("Requires backend contract pentru Intake assist pe acest mediu.");
      }

      setAssistLoading(false);
    }

    void loadAssist();
    return () => {
      cancelled = true;
    };
  }, [parsedDims, request, source]);

  const handleConfirmVolumetricTemplate = useCallback(async () => {
    if (!request || source === "mock") {
      setPersistError("Confirmarea template-ului necesită backend live.");
      return;
    }
    setConfirmingSuggestion(true);
    try {
      const dbId = intakeDbId ?? (await resolveIntakeDbId(request.id));
      if (!dbId) throw new Error("Cererea nu a fost găsită în baza de date.");
      setIntakeDbId(dbId);
      await persistConfirmedTemplate(
        dbId,
        TPL_VOLUMETRIC_LETTERS,
        TPL_VOLUMETRIC_LETTERS
      );
      await refresh();
    } catch (err) {
      setPersistError(
        err instanceof Error ? err.message : "Nu s-a putut confirma template-ul."
      );
    } finally {
      setConfirmingSuggestion(false);
    }
  }, [intakeDbId, refresh, request, source]);

  const handleApplySuggestion = useCallback(
    async (item: ProductTemplateSuggestionItem) => {
      if (!request || source === "mock") {
        setPersistError("Confirmarea template-ului necesită backend live.");
        return;
      }
      const templateCode = item.template_name?.trim();
      if (!templateCode) return;
      setConfirmingSuggestion(true);
      try {
        const dbId = intakeDbId ?? (await resolveIntakeDbId(request.id));
        if (!dbId) throw new Error("Cererea nu a fost găsită în baza de date.");
        setIntakeDbId(dbId);
        await persistConfirmedTemplate(dbId, templateCode, item.template_name);
        await refresh();
      } catch (err) {
        setPersistError(
          err instanceof Error ? err.message : "Nu s-a putut confirma template-ul."
        );
      } finally {
        setConfirmingSuggestion(false);
      }
    },
    [intakeDbId, refresh, request, source]
  );

  const readiness = useMemo(() => {
    if (!request) return { canMarkReady: false, missing: [] as string[] };
    return evaluateIntakeReadyPrerequisites({
      description: request.description,
      dimensions: request.dimensions,
      assignedTo,
      deliveryType: selectedDeliveryType,
      confirmedTemplateCode,
      productSpec: productSpecInitial,
      siteAudit: siteAuditParsed,
      requiresInstallAudit,
    });
  }, [
    request,
    assignedTo,
    selectedDeliveryType,
    confirmedTemplateCode,
    productSpecInitial,
    siteAuditParsed,
    requiresInstallAudit,
  ]);

  const displayReadinessMissing = useMemo(
    () =>
      filterReadinessMissingForDisplay(readiness.missing, requiresInstallAudit),
    [readiness.missing, requiresInstallAudit]
  );

  const handleMarkReadyForQuote = useCallback(async () => {
    if (!request || !readiness.canMarkReady || source === "mock") return;
    setMarkReadyLoading(true);
    setMarkReadyMessage(null);
    try {
      const dbId = intakeDbId ?? (await resolveIntakeDbId(request.id));
      if (!dbId) throw new Error("Cererea nu a fost găsită.");
      const assigneeTrimmed = assignedTo.trim();
      if (assigneeTrimmed && assigneeTrimmed !== "—") {
        await persistIntakeField({ assigned_to: assigneeTrimmed });
      }
      await markIntakeReadyForQuote(dbId, request.status);
      setMarkReadyMessage("Cererea a fost marcată Gata pt. Ofertă.");
      await refresh();
    } catch (err) {
      setMarkReadyMessage(
        err instanceof Error ? err.message : "Nu s-a putut actualiza statusul."
      );
    } finally {
      setMarkReadyLoading(false);
    }
  }, [assignedTo, intakeDbId, persistIntakeField, readiness.canMarkReady, refresh, request, source]);

  const actionSummary = useMemo(() => {
    if (!request) return null;
    return buildIntakeActionSummary({
      status: request.status,
      productFamily: request.productFamily,
      confirmedTemplateCode,
      productSpec: productSpecInitial,
      showVolumetricForm: showProduct001Spec,
      readinessInput: {
        description: request.description,
        dimensions: request.dimensions,
        assignedTo,
        deliveryType: selectedDeliveryType,
        confirmedTemplateCode,
        productSpec: productSpecInitial,
        siteAudit: siteAuditParsed,
        requiresInstallAudit,
      },
      requiresInstallAudit,
    });
  }, [
    assignedTo,
    confirmedTemplateCode,
    productSpecInitial,
    request,
    requiresInstallAudit,
    selectedDeliveryType,
    showProduct001Spec,
    siteAuditParsed,
  ]);

  const scrollToIntakeSection = useCallback((sectionId: string) => {
    document.getElementById(sectionId)?.scrollIntoView({ behavior: "smooth", block: "start" });
  }, []);

  const handleActionSummaryPrimary = useCallback(() => {
    if (!actionSummary) return;
    switch (actionSummary.primaryAction) {
      case "confirm_template":
        if (
          useVolumetricPage &&
          (confirmedTemplateCode ?? "").trim() !== TPL_VOLUMETRIC_LETTERS
        ) {
          void handleConfirmVolumetricTemplate();
        } else {
          scrollToIntakeSection(INTAKE_SECTION_IDS.template);
        }
        break;
      case "complete_spec":
        scrollToIntakeSection(INTAKE_SECTION_IDS["product-spec"]);
        break;
      case "mark_ready":
        scrollToIntakeSection(INTAKE_SECTION_IDS["ready-actions"]);
        if (readiness.canMarkReady && request?.status !== "ready_for_quote") {
          void handleMarkReadyForQuote();
        }
        break;
      case "complete_analysis":
        scrollToIntakeSection(
          requiresInstallAudit
            ? INTAKE_SECTION_IDS.terrain
            : INTAKE_SECTION_IDS.template
        );
        break;
      default:
        break;
    }
  }, [
    actionSummary,
    confirmedTemplateCode,
    handleConfirmVolumetricTemplate,
    handleMarkReadyForQuote,
    readiness.canMarkReady,
    request?.status,
    requiresInstallAudit,
    scrollToIntakeSection,
    useVolumetricPage,
  ]);

  // Keep workspace mounted during background refresh (e.g. right-panel assignee/delivery save).
  if (loading && !request) {
    return (
      <div className="flex flex-col items-center justify-center h-full gap-3">
        <div className="animate-spin rounded-full h-10 w-10 border-b-2 border-blue-500"></div>
        <p className="text-[12px] text-slate-500">Se încarcă cererea...</p>
      </div>
    );
  }

  if (!request) {
    return (
      <div
        className="flex flex-col items-center justify-center h-full gap-4"
        data-testid="intake-not-found"
      >
        <XCircle className="w-12 h-12 text-slate-600" />
        <p className="text-[14px] text-slate-400 text-center max-w-md">
          Cererea <span className="font-mono text-blue-400">{id}</span> nu
          există sau nu a fost găsită.
        </p>
        <p className="text-[11px] text-slate-500 max-w-md text-center">
          Este posibil ca cererea să fi fost ștearsă, codul să fie incorect, sau să existe o problemă de sincronizare cu backend-ul.
        </p>
        <button
          onClick={() => navigate("/intake")}
          className="flex items-center gap-2 px-4 py-2 bg-blue-600 hover:bg-blue-500 text-white rounded-lg text-[12px] font-semibold transition-colors"
        >
          <ArrowLeft className="w-4 h-4" />
          Înapoi la Work Intake
        </button>
      </div>
    );
  }

  const renderIssues = getIntakeDetailRenderIssues(request);
  if (renderIssues.length > 0) {
    return (
      <InvalidIntakeDataSection
        intakeCode={request.id}
        issues={renderIssues}
        productFamily={request.productFamily}
        confirmedTemplateCode={confirmedTemplateCode}
        status={request.status}
        onBack={() => navigate("/intake")}
      />
    );
  }

  const sCfg =
    statusConfig[request.status] ?? {
      label: request.status,
      cls: "bg-slate-700/60 text-slate-300 border-slate-600",
    };

  const volumetricTemplateOk =
    (confirmedTemplateCode ?? "").trim() === TPL_VOLUMETRIC_LETTERS;
  const volumetricProductSpecOk = actionSummary?.productSpecOk ?? false;
  const statusConflict = hasIntakeStatusReadinessConflict(
    request.status,
    readiness.missing,
    volumetricTemplateOk,
    volumetricProductSpecOk
  );

  if (useVolumetricPage) {
    if (!actionSummary) {
      return (
        <InvalidIntakeDataSection
          intakeCode={request.id}
          issues={["lipsește sumar acțiuni pentru workspace modular"]}
          productFamily={request.productFamily}
          confirmedTemplateCode={confirmedTemplateCode}
          status={request.status}
          onBack={() => navigate("/intake")}
        />
      );
    }

    const installTerrainSection = requiresInstallAudit ? (
      <AuditTerenSection
        audit={audit}
        onAuditChange={handleAuditChange}
        isTotemFamily={false}
        autoHeight={null}
      />
    ) : null;

    return (
      <TemplateWorkspaceRouter
        enabled
        request={request}
        source={source}
        error={error}
        persistError={persistError}
        selectedDeliveryType={selectedDeliveryType}
        assignedTo={assignedTo}
        setAssignedTo={setAssignedTo}
        confirmedTemplateCode={confirmedTemplateCode}
        productSpecInitial={productSpecInitial}
        actionSummary={actionSummary!}
        readiness={readiness}
        statusConflict={statusConflict}
        requiresInstallAudit={requiresInstallAudit}
        markReadyLoading={markReadyLoading}
        markReadyMessage={markReadyMessage}
        confirmingTemplate={confirmingSuggestion}
        hasFiscalIdentity={hasFiscalIdentity}
        installTerrainSection={installTerrainSection}
        onDeliveryTypeChange={(dt) => void handleDeliveryTypeChange(dt)}
        onAssignedBlur={() => void handleAssignedBlur()}
        onSaveProductSpec={handleSaveProductSpec}
        intakeDbId={intakeDbId}
        siteAuditJson={siteAuditParsed}
        onMarkReadyForQuote={() => void handleMarkReadyForQuote()}
        onConfirmTemplate={() => void handleConfirmVolumetricTemplate()}
      />
    );
  }

  return (
    <div className="space-y-4 max-w-5xl">
      {/* Breadcrumb */}
      <FlowBreadcrumb items={intakeDetailBreadcrumb(request.id)} />

      <div className="flex items-center justify-between">
        <div className="flex items-center gap-3 flex-wrap">
          <h1 className="text-[20px] font-bold text-wo-text-primary">
            {request.id}
          </h1>
          {workspaceShell && (
            <IntakeWorkspaceDiagnosticBadge shell={workspaceShell} />
          )}
          <span
            className={`inline-flex items-center gap-1 px-2 py-0.5 text-[11px] font-semibold rounded border ${sCfg.cls}`}
          >
            {sCfg.label}
          </span>
          <span
            className={`px-1.5 py-0.5 text-[10px] font-bold rounded ${
              request.priority === "urgent"
                ? "bg-red-600 text-white"
                : request.priority === "high"
                  ? "bg-amber-600 text-white"
                  : "bg-slate-700 text-slate-300"
            }`}
          >
            {request.priority.toUpperCase()}
          </span>
        </div>
      </div>

      {actionSummary && !workTypeUnresolved && (
        <IntakeActionSummary
          model={actionSummary}
          onPrimaryAction={handleActionSummaryPrimary}
          onOpenPreliminaryQuote={
            showProduct001Spec ? handleOpenPreliminaryQuote : undefined
          }
          showProductForm={showProduct001Spec}
          requiresInstallAudit={requiresInstallAudit}
        />
      )}

      {error && source !== "mock" && (
        <div className="flex items-start gap-2 px-3 py-2 bg-red-900/20 border border-red-800/40 rounded-lg">
          <AlertTriangle className="w-4 h-4 text-red-400 mt-0.5 shrink-0" />
          <p className="text-[11px] text-red-300">
            Cererea a fost încărcată cu erori de backend: {error}
          </p>
        </div>
      )}

      {persistError && (
        <div className="flex items-start gap-2 px-3 py-2 bg-red-900/20 border border-red-800/40 rounded-lg">
          <AlertTriangle className="w-4 h-4 text-red-400 mt-0.5 shrink-0" />
          <p className="text-[11px] text-red-300">{persistError}</p>
        </div>
      )}

      {showTerrainGates && (
        <p className="text-[11px] text-slate-500">{terrainSummaryLabel(siteAuditParsed)}</p>
      )}

      {!workTypeUnresolved && !allowMockOperationalAssist && (
        <div className="flex items-start gap-2 px-3 py-2 bg-amber-900/15 border border-amber-800/30 rounded-lg">
          <AlertTriangle className="w-4 h-4 text-amber-400 mt-0.5 shrink-0" />
          <p className="text-[11px] text-amber-300/90">
            Live mode activ: asistența de template/foi din mockData este dezactivată până la contract backend dedicat.
          </p>
        </div>
      )}

      {/* Client Summary Bar */}
      <div className="bg-wo-surface-raised border border-wo-border-subtle rounded-lg p-4">
        <div className="grid grid-cols-2 md:grid-cols-5 gap-4">
          <div>
            <p className="text-[10px] text-slate-500 uppercase tracking-wide mb-0.5">
              Client
            </p>
            <p className="text-[13px] text-wo-text-primary font-semibold">
              {request.client}
            </p>
          </div>
          <div>
            <p className="text-[10px] text-slate-500 uppercase tracking-wide mb-0.5">
              Contact
            </p>
            <p className="text-[13px] text-slate-300">
              {request.contactPerson}
            </p>
          </div>
          <div>
            <p className="text-[10px] text-slate-500 uppercase tracking-wide mb-0.5">
              Tip lucrare
            </p>
            <p className="text-[13px] text-slate-300">
              {formatIntakeProductFamilyLabel(request.productFamily)}
            </p>
          </div>
          <div>
            <p className="text-[10px] text-slate-500 uppercase tracking-wide mb-0.5">
              Descriere
            </p>
            <p className="text-[12px] text-slate-400 truncate">
              {request.description}
            </p>
          </div>
          <div>
            <p className="text-[10px] text-slate-500 uppercase tracking-wide mb-0.5">
              Asignat
            </p>
            {source === "mock" ? (
              <p className="text-[13px] text-slate-300">{assignedTo}</p>
            ) : (
              <input
                type="text"
                value={assignedTo === "—" ? "" : assignedTo}
                onChange={(e) => setAssignedTo(e.target.value)}
                onBlur={() => void handleAssignedBlur()}
                placeholder="Nume operator responsabil"
                className="w-full bg-wo-surface-inset border border-wo-border-strong rounded px-2 py-1 text-[12px] text-slate-200"
              />
            )}
          </div>
        </div>
      </div>

      {/* Delivery Type Selector — Interactive */}
      <div className="bg-wo-surface-raised border border-wo-border-subtle rounded-lg p-4">
        <div className="flex items-center gap-2 mb-3">
          <Truck className="w-4 h-4 text-blue-400" />
          <p className="text-[13px] font-semibold text-slate-200">
            Tip Livrare
          </p>
        </div>
        <div className="flex flex-wrap gap-2">
          {(Object.keys(deliveryTypeLabels) as DeliveryType[]).map((dt) => {
            const isActive = selectedDeliveryType === dt;
            return (
              <button
                key={dt}
                onClick={() => void handleDeliveryTypeChange(dt)}
                className={`inline-flex items-center gap-1.5 px-3 py-2 text-[12px] font-semibold rounded-lg border transition-all ${
                  isActive
                    ? "bg-blue-600/20 text-blue-300 border-blue-500/50 ring-1 ring-blue-500/30"
                    : "bg-wo-surface-inset text-slate-500 border-wo-border-strong hover:border-slate-500 hover:text-slate-300"
                }`}
              >
                {isActive && <CheckCircle2 className="w-3.5 h-3.5" />}
                {deliveryTypeLabels[dt]}
              </button>
            );
          })}
        </div>
        {(deliveryStageNote || (requiresInstallAudit && !workTypeUnresolved)) && (
          <div
            className={`flex items-start gap-2 mt-3 px-3 py-2 rounded-lg ${
              workTypeUnresolved
                ? "bg-slate-900/40 border border-slate-700/40"
                : requiresInstallAudit
                  ? "bg-amber-900/10 border border-amber-800/20"
                  : "bg-slate-900/40 border border-slate-700/40"
            }`}
            data-testid="delivery-stage-note"
          >
            <Info
              className={`w-3.5 h-3.5 mt-0.5 shrink-0 ${
                requiresInstallAudit && !workTypeUnresolved
                  ? "text-amber-400"
                  : "text-slate-400"
              }`}
            />
            <p
              className={`text-[10px] ${
                requiresInstallAudit && !workTypeUnresolved
                  ? "text-amber-300/80"
                  : "text-slate-400"
              }`}
            >
              {requiresInstallAudit && !workTypeUnresolved ? (
                <>
                  <strong>Livrare + Montaj</strong> — necesită audit teren complet și adresă
                  de montaj validată pe Google Maps.
                </>
              ) : (
                deliveryStageNote
              )}
            </p>
          </div>
        )}
      </div>

      {/* Section 1: Identity (Temp ID + Optional CUI) — Stage 1+ only */}
      {!workTypeUnresolved && (
        <IdentitySection
          identity={request.identity}
          initialCUI={initialCUI}
          companyData={companyData}
          onCompanyFound={setCompanyData}
          allowMockLookup={allowMockOperationalAssist}
          source={source}
        />
      )}

      {/* Section 2: Product System Info — Sheet-Based Stock */}
      {workTypeUnresolved ? (
        <UnresolvedWorkTypeSection
          onChooseWorkType={() => setWorkTypePickerOpen((open) => !open)}
          workTypePickerOpen={workTypePickerOpen}
          selectingWorkType={selectingWorkType}
          workTypePicker={
            <IntakeWorkTypePicker
              selectedWorkTypeId={null}
              onSelect={(workTypeId) => void handleSelectWorkType(workTypeId)}
              registry={productFamilies}
              loading={familiesLoading}
            />
          }
        />
      ) : allowMockOperationalAssist ? (
        <div id={INTAKE_SECTION_IDS.template} className="scroll-mt-4">
          {productTemplate ? (
            <ProductSystemSection template={productTemplate} pieceDimensionMM={pieceDimensionMM} />
          ) : (
            <NoTemplateSection familyName={formatIntakeProductFamilyLabel(request.productFamily)} />
          )}
        </div>
      ) : (
        <BackendAssistSection
          loading={assistLoading}
          error={assistError}
          templateSuggestions={templateSuggestions}
          materialItems={materialAssistItems}
          materialAssistAvailable={materialAssistAvailable}
          materialBlockers={materialAssistBlockers}
          onApplySuggestion={(item) => void handleApplySuggestion(item)}
          appliedSuggestionId={appliedSuggestionId}
          confirmedTemplateCode={confirmedTemplateCode}
          confirmingSuggestion={confirmingSuggestion}
        />
      )}

      {/* Product 001 — per-customer specification (litere volumetrice) */}
      {showProduct001Spec && request && (
        <div id={INTAKE_SECTION_IDS["product-spec"]} className="scroll-mt-4">
          <Product001IntakeSpecEditor
            initialSpec={productSpecInitial}
            onSave={handleSaveProductSpec}
            readOnly={source === "mock"}
            showQuotePrepPanel
            onContinueToQuoteWizard={handleOpenPreliminaryQuote}
          />
        </div>
      )}

      {/* Section 3: Detalii Tehnice Client — install delivery only (Stage 1+) */}
      {showTerrainGates && (
        <AuditTerenSection
          audit={audit}
          onAuditChange={handleAuditChange}
          isTotemFamily={isTotemFamily}
          autoHeight={autoHeight}
        />
      )}

      {/* Bottom Action Bar */}
      <div
        id={INTAKE_SECTION_IDS["ready-actions"]}
        className="bg-wo-surface-raised border border-wo-border-subtle rounded-lg p-4 scroll-mt-4"
      >
        {workTypeUnresolved ? (
          <div className="flex items-center justify-between">
            <button
              onClick={() => navigate("/intake")}
              className="flex items-center gap-2 px-4 py-2 bg-slate-700 hover:bg-slate-600 text-slate-200 rounded-lg text-[12px] font-semibold transition-colors"
            >
              <ArrowLeft className="w-4 h-4" />
              Înapoi
            </button>
          </div>
        ) : (
          <>
        {!readiness.canMarkReady && request.status !== "ready_for_quote" && displayReadinessMissing.length > 0 && (
          <div className="mb-4 bg-red-900/15 border border-red-800/30 rounded-lg p-3">
            <div className="flex items-center gap-2 mb-2">
              <AlertTriangle className="w-4 h-4 text-red-400 shrink-0" />
              <p className="text-[12px] text-red-300 font-semibold">
                Nu se poate marca Gata pt. Ofertă — {displayReadinessMissing.length} condiție(i):
              </p>
            </div>
            <ul className="grid grid-cols-1 md:grid-cols-2 gap-1.5 ml-6">
              {displayReadinessMissing.map((f) => (
                <li key={f} className="flex items-center gap-1.5 text-[11px] text-red-300/80">
                  <XCircle className="w-3 h-3 text-red-400 shrink-0" />
                  {f}
                </li>
              ))}
            </ul>
          </div>
        )}

        <div className="flex items-center justify-between">
          <div className="flex items-center gap-3">
            <button
              onClick={() => navigate("/intake")}
              className="flex items-center gap-2 px-4 py-2 bg-slate-700 hover:bg-slate-600 text-slate-200 rounded-lg text-[12px] font-semibold transition-colors"
            >
              <ArrowLeft className="w-4 h-4" />
              Înapoi
            </button>
          </div>
          <div className="flex items-center gap-3">
            {!hasFiscalIdentity && (
              <span className="text-[11px] text-amber-400 flex items-center gap-1">
                <Hash className="w-3.5 h-3.5" />
                Temp ID — CUI opțional
              </span>
            )}
            {readiness.canMarkReady && request.status !== "ready_for_quote" && (
              <span className="text-[11px] text-emerald-400 flex items-center gap-1">
                <CheckCircle2 className="w-3.5 h-3.5" />
                Pregătit pentru marcare
              </span>
            )}
            <button
              disabled={
                !readiness.canMarkReady ||
                markReadyLoading ||
                request.status === "ready_for_quote" ||
                source === "mock"
              }
              onClick={() => void handleMarkReadyForQuote()}
              className={`flex items-center gap-2 px-5 py-2.5 rounded-lg text-[13px] font-bold transition-colors ${
                readiness.canMarkReady && request.status !== "ready_for_quote"
                  ? "bg-emerald-600 hover:bg-emerald-500 text-white"
                  : "bg-slate-700/60 text-slate-500 cursor-not-allowed"
              }`}
            >
              <CheckCircle2 className="w-4 h-4" />
              {markReadyLoading ? "Se salvează…" : "Marchează Gata pt. Ofertă"}
            </button>
          </div>
        </div>
        {markReadyMessage && (
          <p className="text-[11px] text-emerald-400 mt-2">{markReadyMessage}</p>
        )}
        <div className="flex items-start gap-2 mt-3 px-3 py-2 bg-blue-900/10 border border-blue-800/20 rounded-lg">
          <Info className="w-3.5 h-3.5 text-blue-400 mt-0.5 shrink-0" />
          <p className="text-[10px] text-blue-300/80">
            <strong>Gata pt. Ofertă</strong> = cererea este completă pentru ofertare (date persistate).
            Oferta comercială finală are gate separat (<code>can_create_commercial_quote</code>).
            CUI-ul devine obligatoriu la acceptarea ofertei.
          </p>
        </div>
          </>
        )}
      </div>

      {/* Next Step Panel */}
      {request.status === "ready_for_quote" && !workTypeUnresolved && (
        <NextStepPanel
          title="Următorul pas: Ofertare preliminară"
          description="Cererea este marcată Gata pt. Ofertă. Deschide workspace-ul de ofertare sau lista Oferte."
          primaryAction={{
            label: showProduct001Spec ? "Deschide ofertare preliminară" : "Mergi la Oferte",
            onClick: showProduct001Spec
              ? handleOpenPreliminaryQuote
              : undefined,
            to: showProduct001Spec ? undefined : "/quotes",
          }}
        />
      )}
      {request.status === "new" && workTypeUnresolved && (
        <NextStepPanel
          title="Următorul pas: Alege tipul lucrării"
          description={STAGE0_WORK_TYPE_GUIDANCE}
        />
      )}
      {request.status === "new" && !workTypeUnresolved && (
        <NextStepPanel
          title="Următorul pas: Completează analiza"
          description="Cererea este nouă. Completează toate câmpurile obligatorii (Audit Teren, Descriere, Dimensiuni) pentru a o marca ca pregătită pentru ofertă."
          reason="Toate câmpurile obligatorii trebuie completate."
        />
      )}
      {request.status === "in_review" && (
        <NextStepPanel
          title="În analiză"
          description="Cererea este în curs de analiză. Verifică specificațiile și completează informațiile lipsă."
        />
      )}
      {request.status === "needs_info" && (
        <NextStepPanel
          title="Informații lipsă"
          description="Cererea necesită informații suplimentare de la client. Contactează clientul pentru a obține datele necesare."
          reason="Nu se poate avansa fără informațiile solicitate."
        />
      )}
    </div>
  );
}