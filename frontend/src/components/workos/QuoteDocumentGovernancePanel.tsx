import { useEffect, useState } from "react";
import { AlertTriangle, ShieldCheck } from "lucide-react";
import { getQuoteAcceptanceGuard, type QuoteAcceptanceGuardResponse } from "@/api/orders";
import { getSnapshotEligibility, type SnapshotEligibilityResponse } from "@/api/quoteOutputSnapshotGovernance";
import DocumentGovernanceTerminologyCard from "@/components/workos/DocumentGovernanceTerminologyCard";

interface QuoteDocumentGovernancePanelProps {
  quoteId: number | null;
  quoteCode: string;
  visible: boolean;
}

const guardStatusLabel: Record<string, string> = {
  eligible: "Eligibil",
  blocked: "Blocat",
  needs_acknowledgement: "Necesită confirmare",
};

const eligibilityLabel: Record<string, string> = {
  eligible: "Eligibil",
  blocked: "Blocat",
  needs_review: "Necesită revizuire",
  missing: "Lipsă",
};

function badgeClassForStatus(status: string): string {
  if (status === "eligible") {
    return "border-emerald-700/50 bg-emerald-900/30 text-emerald-300";
  }
  if (status === "needs_acknowledgement" || status === "needs_review") {
    return "border-amber-700/50 bg-amber-900/30 text-amber-300";
  }
  if (status === "blocked" || status === "missing") {
    return "border-red-700/50 bg-red-900/30 text-red-300";
  }
  return "border-slate-600 bg-slate-800/70 text-slate-300";
}

export default function QuoteDocumentGovernancePanel({
  quoteId,
  quoteCode,
  visible,
}: QuoteDocumentGovernancePanelProps) {
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [guard, setGuard] = useState<QuoteAcceptanceGuardResponse | null>(null);
  const [eligibility, setEligibility] = useState<SnapshotEligibilityResponse | null>(null);

  useEffect(() => {
    let cancelled = false;

    if (!visible || !quoteId) {
      setLoading(false);
      setError(null);
      setGuard(null);
      setEligibility(null);
      return;
    }

    setLoading(true);
    setError(null);

    Promise.all([
      getQuoteAcceptanceGuard(quoteId),
      getSnapshotEligibility(quoteId),
    ])
      .then(([guardResult, eligibilityResult]) => {
        if (cancelled) return;
        setGuard(guardResult);
        setEligibility(eligibilityResult);
      })
      .catch((err: unknown) => {
        if (cancelled) return;
        setError(err instanceof Error ? err.message : "Nu s-a putut încărca statusul de governance");
      })
      .finally(() => {
        if (!cancelled) {
          setLoading(false);
        }
      });

    return () => {
      cancelled = true;
    };
  }, [quoteId, visible]);

  if (!visible || !quoteId) return null;

  return (
    <div className="bg-wo-surface-raised border border-wo-border-subtle rounded-lg p-4" data-testid="quote-document-governance-panel">
      <div className="flex items-center gap-2 mb-2">
        <ShieldCheck className="w-4 h-4 text-blue-400" />
        <p className="text-[12px] font-semibold text-blue-300">Document Governance (read-only)</p>
      </div>

      <p className="text-[11px] text-slate-400">
        Quote {quoteCode}: UI citește doar statusuri canonice de guvernanță. Nu rulează conversii, aprobări sau generări automate.
      </p>

      {loading && <p className="mt-2 text-[11px] text-slate-500">Se încarcă starea de governance...</p>}

      {error && (
        <div className="mt-2 flex items-start gap-2 rounded border border-red-800/40 bg-red-900/20 px-2.5 py-2">
          <AlertTriangle className="mt-0.5 h-3.5 w-3.5 shrink-0 text-red-300" />
          <p className="text-[11px] text-red-300">{error}</p>
        </div>
      )}

      {!loading && !error && guard && eligibility && (
        <div className="mt-3 space-y-2 text-[11px]">
          <div className="flex items-center justify-between rounded border border-wo-border-strong bg-wo-surface-raised px-2.5 py-2">
            <span className="text-slate-400">Quote acceptance guard</span>
            <span className={`rounded border px-2 py-0.5 font-semibold ${badgeClassForStatus(guard.overall_status)}`}>
              {guardStatusLabel[guard.overall_status] ?? guard.overall_status}
            </span>
          </div>

          <div className="flex items-center justify-between rounded border border-wo-border-strong bg-wo-surface-raised px-2.5 py-2">
            <span className="text-slate-400">Output snapshot eligibility</span>
            <span className={`rounded border px-2 py-0.5 font-semibold ${badgeClassForStatus(eligibility.eligibility_status)}`}>
              {eligibilityLabel[eligibility.eligibility_status] ?? eligibility.eligibility_status}
            </span>
          </div>

          <div className="rounded border border-wo-border-strong bg-wo-surface-raised px-2.5 py-2 text-slate-300">
            <p>
              Snapshot aprobat: {eligibility.approved_snapshot_code ?? "neatașat"}
            </p>
            <p className="mt-0.5">
              Guard-uri evaluate: {guard.guards.length} · Blockers: {eligibility.blockers.length} · Warnings: {eligibility.warnings.length}
            </p>
          </div>
        </div>
      )}

      <DocumentGovernanceTerminologyCard />
    </div>
  );
}