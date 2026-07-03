import { useCallback, useState } from "react";
import {
  AlertTriangle,
  Building2,
  CheckCircle2,
  Loader2,
  Search,
  ShieldCheck,
  XCircle,
} from "lucide-react";
import { lookupFiscalProvider } from "@/api/intakeAssist";
import type { ClientEntity } from "@/lib/api";
import {
  buildClientUpdateFromFiscalNormalized,
  lookupClientsByTaxId,
  updateClient,
} from "@/lib/api";

interface ClientFiscalVerifyPanelProps {
  clientEntity: ClientEntity;
  onClientUpdated: (client: ClientEntity) => void;
}

export function ClientFiscalVerifyPanel({
  clientEntity,
  onClientUpdated,
}: ClientFiscalVerifyPanelProps) {
  const [cui, setCui] = useState(clientEntity.cui ?? "");
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [lookupInfo, setLookupInfo] = useState<string | null>(null);
  const [preview, setPreview] = useState<{
    companyName: string;
    taxId: string;
    address?: string | null;
    city?: string | null;
    county?: string | null;
    provider: string;
    warnings?: string[];
  } | null>(null);
  const [matchStatus, setMatchStatus] = useState<
    "idle" | "loading" | "none" | "single" | "conflict" | "invalid"
  >("idle");
  const [persistLoading, setPersistLoading] = useState(false);
  const [persistError, setPersistError] = useState<string | null>(null);
  const [persistSuccess, setPersistSuccess] = useState<string | null>(null);

  const resolveClientMatch = useCallback(async (taxId: string) => {
    setMatchStatus("loading");
    setPersistError(null);
    setPersistSuccess(null);
    try {
      const match = await lookupClientsByTaxId(taxId);
      if (match.status === "invalid_input") {
        setMatchStatus("invalid");
        return;
      }
      setMatchStatus(match.status);
    } catch {
      setMatchStatus("invalid");
      setPersistError("Nu am putut verifica dacă există deja clientul cu acest CUI.");
    }
  }, []);

  const handleLookup = useCallback(async () => {
    if (!cui.trim()) return;
    setLoading(true);
    setError(null);
    setLookupInfo(null);
    setPreview(null);
    setMatchStatus("idle");
    setPersistError(null);
    setPersistSuccess(null);

    const result = await lookupFiscalProvider(cui.trim());
    setLoading(false);

    if (result.status === "contract-missing" || result.status === "error") {
      setError(result.message || "Eroare la interogarea fiscală backend.");
      return;
    }

    const payload = result.data;
    if (!payload) {
      setError("Lookup fiscal backend indisponibil pentru acest provider.");
      return;
    }

    if (payload.status === "found" && payload.normalized) {
      const normalized = payload.normalized;
      setPreview({
        companyName: normalized.company_name,
        taxId: normalized.tax_id,
        address: normalized.address,
        city: normalized.city,
        county: normalized.county,
        provider: payload.provider,
        warnings: payload.warnings,
      });
      setLookupInfo(
        payload.warnings?.length
          ? `Date preluate (${payload.provider === "anaf" ? "ANAF" : "SmartBill"}). ${payload.warnings.join(" ")}`
          : `Date preluate din ${payload.provider === "anaf" ? "ANAF" : "SmartBill"}. Confirmă actualizarea clientului.`
      );
      void resolveClientMatch(normalized.tax_id);
      return;
    }

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
  }, [cui, resolveClientMatch]);

  const handleUpdateClient = useCallback(async () => {
    if (!preview || matchStatus === "conflict" || matchStatus === "invalid") return;
    setPersistLoading(true);
    setPersistError(null);
    setPersistSuccess(null);
    try {
      const updates = buildClientUpdateFromFiscalNormalized(clientEntity, {
        tax_id: preview.taxId,
        company_name: preview.companyName,
        address: preview.address,
        city: preview.city,
        county: preview.county,
      });
      const updated = await updateClient(clientEntity.id, updates);
      onClientUpdated(updated);
      setPersistSuccess("Client actualizat în sistem.");
    } catch (err) {
      setPersistError(err instanceof Error ? err.message : "Actualizarea clientului a eșuat.");
    } finally {
      setPersistLoading(false);
    }
  }, [clientEntity, matchStatus, onClientUpdated, preview]);

  const canUpdate =
    Boolean(preview) &&
    matchStatus !== "loading" &&
    matchStatus !== "conflict" &&
    matchStatus !== "invalid" &&
    !persistLoading;

  return (
    <div
      className="bg-[#111827] border border-[#1E293B] rounded-lg p-4"
      data-testid="client-fiscal-verify-panel"
    >
      <h3 className="text-[12px] font-semibold text-slate-300 mb-3 flex items-center gap-2">
        <ShieldCheck className="w-4 h-4 text-blue-400" />
        Verificare date fiscale
      </h3>

      <div className="flex items-center gap-3 mb-3">
        <div className="flex items-center gap-2 bg-[#0D1321] border border-[#2A3548] rounded-lg px-3 py-2 flex-1 max-w-sm focus-within:border-blue-500/50">
          <Search className="w-4 h-4 text-slate-500 shrink-0" />
          <input
            type="text"
            value={cui}
            disabled={loading}
            onChange={(e) => {
              setCui(e.target.value);
              setError(null);
              setPreview(null);
            }}
            onKeyDown={(e) => e.key === "Enter" && handleLookup()}
            placeholder="CUI client"
            className="bg-transparent text-[13px] text-slate-200 placeholder:text-slate-600 outline-none w-full font-mono"
          />
        </div>
        <button
          onClick={handleLookup}
          disabled={loading || !cui.trim()}
          className="flex items-center gap-2 px-4 py-2 bg-blue-600 hover:bg-blue-500 disabled:bg-slate-700 disabled:text-slate-500 text-white rounded-lg text-[12px] font-semibold transition-colors"
        >
          {loading ? <Loader2 className="w-4 h-4 animate-spin" /> : <Search className="w-4 h-4" />}
          {loading ? "Interogare..." : "Verifică fiscal"}
        </button>
      </div>

      {error && (
        <div className="flex items-center gap-2 mb-3 px-3 py-2 bg-red-900/20 border border-red-800/40 rounded-lg">
          <XCircle className="w-4 h-4 text-red-400 shrink-0" />
          <p className="text-[12px] text-red-300">{error}</p>
        </div>
      )}

      {lookupInfo && (
        <div className="flex items-center gap-2 mb-3 px-3 py-2 bg-blue-900/20 border border-blue-800/40 rounded-lg">
          <Building2 className="w-4 h-4 text-blue-300 shrink-0" />
          <p className="text-[12px] text-blue-200">{lookupInfo}</p>
        </div>
      )}

      {preview && (
        <div className="bg-[#0D1321] border border-emerald-800/30 rounded-lg p-4 space-y-3">
          <div className="flex items-center gap-2">
            <CheckCircle2 className="w-4 h-4 text-emerald-400" />
            <p className="text-[12px] text-emerald-400 font-semibold">Preview date fiscale</p>
          </div>

          {preview.warnings?.length ? (
            <div className="flex items-start gap-2 px-3 py-2 bg-amber-900/15 border border-amber-800/30 rounded-lg">
              <AlertTriangle className="w-4 h-4 text-amber-300 mt-0.5 shrink-0" />
              <p className="text-[11px] text-amber-200">{preview.warnings.join(" ")}</p>
            </div>
          ) : null}

          <div className="grid grid-cols-1 md:grid-cols-2 gap-3 text-[12px]">
            <div>
              <p className="text-[10px] text-slate-500 uppercase">Nume firmă</p>
              <p className="text-slate-200">{preview.companyName}</p>
            </div>
            <div>
              <p className="text-[10px] text-slate-500 uppercase">CUI</p>
              <p className="text-slate-200 font-mono">{preview.taxId}</p>
            </div>
            <div>
              <p className="text-[10px] text-slate-500 uppercase">Adresă</p>
              <p className="text-slate-200">{preview.address || "—"}</p>
            </div>
            <div>
              <p className="text-[10px] text-slate-500 uppercase">Oraș</p>
              <p className="text-slate-200">{preview.city || "—"}</p>
            </div>
          </div>

          <div className="text-[11px] text-slate-400 border-t border-[#2A3548] pt-3">
            {matchStatus === "loading" && "Verific client existent după CUI..."}
            {matchStatus === "single" && "Client existent confirmat după CUI."}
            {matchStatus === "none" && "Niciun client existent cu acest CUI — actualizarea se aplică clientului curent."}
            {matchStatus === "conflict" &&
              "Conflict: mai mulți clienți cu același CUI. Rezolvare manuală necesară înainte de actualizare."}
            {matchStatus === "invalid" && "Nu am putut verifica existența clientului după CUI."}
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

          <button
            onClick={handleUpdateClient}
            disabled={!canUpdate}
            className="inline-flex items-center gap-2 px-4 py-2 bg-emerald-700 hover:bg-emerald-600 disabled:bg-slate-700 disabled:text-slate-500 text-white rounded-lg text-[12px] font-semibold transition-colors"
          >
            {persistLoading ? <Loader2 className="w-4 h-4 animate-spin" /> : <CheckCircle2 className="w-4 h-4" />}
            {persistLoading ? "Actualizare..." : "Actualizează client"}
          </button>
        </div>
      )}
    </div>
  );
}
