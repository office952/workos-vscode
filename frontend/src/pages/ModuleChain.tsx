import { ModuleNodeCard, SectionHeader } from "@/components/workos/SharedComponents";
import { GitBranch, ArrowRight, Ban, Wifi, WifiOff, RefreshCw, Loader2, AlertTriangle, BookOpen } from "lucide-react";
import { useModuleChainData } from "@/hooks/useModuleChainData";
import {
  HONESTY_ARCHITECTURE_NODES,
  HONESTY_HANDOFFS,
  HONESTY_RESOURCE_BOUNDARIES,
  coverageBadgeClass,
  coverageLabelRo,
} from "@/lib/truthPagesHonestyBaseline";

function runtimeLabelRo(
  aggregateStatus: string,
  isLive: boolean,
  loading: boolean,
  error: string | null
): { label: string; className: string } {
  if (loading) {
    return { label: "SE ÎNCARCĂ", className: "bg-slate-700/60 text-slate-300 border-slate-600" };
  }
  if (!isLive || error) {
    return { label: "INDISPONIBIL", className: "bg-red-900/30 text-red-300 border-red-800" };
  }
  if (aggregateStatus === "ok") {
    return { label: "VERIFICAT", className: "bg-emerald-900/40 text-emerald-300 border-emerald-700" };
  }
  if (aggregateStatus === "warning" || aggregateStatus === "degraded") {
    return { label: "DEGRADAT", className: "bg-amber-900/40 text-amber-300 border-amber-700" };
  }
  if (aggregateStatus === "fail") {
    return { label: "DEGRADAT", className: "bg-red-900/40 text-red-300 border-red-700" };
  }
  return { label: "NEVERIFICAT", className: "bg-slate-700/60 text-slate-300 border-slate-600" };
}

export default function ModuleChain() {
  const {
    modules,
    contractHandoffs,
    aggregateStatus,
    generatedAt,
    loading,
    error,
    isLive,
    refetch,
  } = useModuleChainData(30000);

  const runtimeBadge = runtimeLabelRo(aggregateStatus, isLive, loading, error);

  return (
    <div className="space-y-6" data-testid="module-chain-page">
      <div>
        <div className="flex items-center gap-2 mb-1 flex-wrap">
          <GitBranch className="w-5 h-5 text-blue-400" />
          <h1 className="text-[18px] font-bold text-slate-100">Harta sistemelor</h1>
          <span className="text-[11px] text-slate-500 font-normal" data-testid="module-chain-alias">
            Module Chain
          </span>
          <span
            className={`ml-auto flex items-center gap-1.5 px-2 py-0.5 text-[10px] font-semibold rounded border ${
              isLive
                ? "bg-slate-800/80 text-slate-300 border-slate-600"
                : "bg-amber-900/30 text-amber-400 border-amber-700"
            }`}
            data-testid="module-chain-runtime-source"
          >
            {isLive ? <Wifi className="w-3 h-3" /> : <WifiOff className="w-3 h-3" />}
            {isLive ? "Health API" : "Health indisponibil"}
          </span>
          <button
            onClick={refetch}
            className="p-1 rounded hover:bg-slate-700/50 text-slate-400 hover:text-slate-200 transition-colors"
            title="Reîmprospătează verificările runtime"
            type="button"
          >
            <RefreshCw className="w-3.5 h-3.5" />
          </button>
        </div>
        <p className="text-[12px] text-slate-500">
          Cum sunt conectate sistemele, paginile și contractele — proiecție read-only, acoperire parțială.
        </p>
      </div>

      <div
        className="flex items-start gap-2 px-3 py-2.5 bg-amber-900/15 border border-amber-800/40 rounded-lg"
        data-testid="module-chain-honesty-banner"
      >
        <AlertTriangle className="w-4 h-4 text-amber-400 mt-0.5 shrink-0" />
        <p className="text-[12px] text-amber-200/95 leading-relaxed">
          Această hartă este o proiecție read-only a documentației și verificărilor disponibile. Acoperirea este
          parțială și nu reprezintă un editor al proceselor.
        </p>
      </div>

      {/* A. Architecture */}
      <section className="bg-[#111827] border border-[#1E293B] rounded-lg p-4" data-testid="module-chain-architecture">
        <SectionHeader
          title="Structura sistemelor"
          icon={<GitBranch className="w-4 h-4 text-blue-400" />}
        />
        <p className="text-[11px] text-slate-500 mb-3">
          Baseline aprobat (nu acoperire completă). Nodurile fără dovezi suficiente apar ca NEVALIDAT / ACOPERIRE
          PARȚIALĂ.
        </p>
        <div className="flex flex-wrap gap-2 mb-4">
          {HONESTY_ARCHITECTURE_NODES.map((node) => (
            <div
              key={node.id}
              className="bg-[#1A2236] border border-[#2A3548] rounded-lg px-3 py-2 min-w-[160px] max-w-[220px]"
              data-testid={`arch-node-${node.id}`}
            >
              <div className="flex items-center gap-2 mb-1">
                <span className="text-[13px] font-semibold text-slate-100">{node.labelRo}</span>
              </div>
              <p className="text-[10px] text-slate-500 mb-1.5">{node.technicalAlias}</p>
              <span
                className={`inline-block px-1.5 py-0.5 text-[9px] font-semibold rounded border ${coverageBadgeClass(node.coverage)}`}
              >
                {coverageLabelRo(node.coverage)}
              </span>
              <p className="text-[10px] text-slate-500 mt-1.5 leading-snug">{node.note}</p>
            </div>
          ))}
        </div>

        <p className="text-[11px] font-semibold text-slate-400 mb-2">Limite de resurse (separate)</p>
        <div className="flex flex-wrap gap-2 mb-4">
          {HONESTY_RESOURCE_BOUNDARIES.map((node) => (
            <div
              key={node.id}
              className="bg-[#151c2c] border border-[#2A3548]/80 rounded-lg px-3 py-2 min-w-[140px]"
              data-testid={`resource-node-${node.id}`}
            >
              <p className="text-[12px] font-medium text-slate-200">{node.labelRo}</p>
              <p className="text-[10px] text-slate-500">{node.technicalAlias}</p>
              <span
                className={`inline-block mt-1 px-1.5 py-0.5 text-[9px] font-semibold rounded border ${coverageBadgeClass(node.coverage)}`}
              >
                {coverageLabelRo(node.coverage)}
              </span>
            </div>
          ))}
        </div>

        <SectionHeader title="Transferuri (baseline)" icon={<ArrowRight className="w-4 h-4" />} />
        <div className="space-y-2 mt-2">
          {HONESTY_HANDOFFS.map((h) => (
            <div
              key={`${h.fromId}-${h.toId}`}
              className="bg-[#1A2236] border border-[#2A3548] rounded-lg p-3"
              data-testid={`handoff-${h.fromId}-${h.toId}`}
            >
              <div className="flex items-center gap-2 flex-wrap mb-1">
                <span className="text-[13px] font-bold text-blue-400">{h.fromLabel}</span>
                <ArrowRight className="w-3.5 h-3.5 text-slate-600" />
                <span className="text-[13px] font-bold text-blue-400">{h.toLabel}</span>
                <span
                  className={`ml-auto px-1.5 py-0.5 text-[9px] font-semibold rounded border ${
                    h.status === "baseline"
                      ? "bg-emerald-900/30 text-emerald-300 border-emerald-700"
                      : "bg-amber-900/30 text-amber-300 border-amber-700"
                  }`}
                >
                  {h.status === "baseline" ? "BASELINE" : "ACOPERIRE PARȚIALĂ"}
                </span>
              </div>
              <p className="text-[11px] text-slate-400">{h.note}</p>
              <p className="text-[10px] text-slate-500 mt-1 flex items-center gap-1">
                <BookOpen className="w-3 h-3" />
                Sursă: {h.source}
              </p>
            </div>
          ))}
        </div>
      </section>

      {/* B. Runtime — separate */}
      <section className="bg-[#111827] border border-[#1E293B] rounded-lg p-4" data-testid="module-chain-runtime">
        <div className="flex items-center gap-2 mb-2 flex-wrap">
          <SectionHeader title="Stare runtime" icon={<Wifi className="w-4 h-4 text-slate-400" />} />
          <span className={`px-2 py-0.5 text-[10px] font-semibold rounded border ${runtimeBadge.className}`}>
            {runtimeBadge.label}
          </span>
        </div>
        <p className="text-[11px] text-slate-500 mb-3">
          Separat de arhitectură. Afișează doar verificări reale din{" "}
          <code className="text-slate-400">GET /api/v1/system/health</code>. Fără verificare mapată = Neverificat —
          nu „activ” implicit.
        </p>
        {error && (
          <div
            className="mb-3 px-3 py-2 rounded border border-red-800/40 bg-red-900/20 text-[11px] text-red-300"
            data-testid="module-chain-runtime-error"
          >
            Date runtime indisponibile: {error}
          </div>
        )}
        {generatedAt && isLive && (
          <p className="text-[10px] text-slate-600 mb-3">
            Ultima verificare: {new Date(generatedAt).toLocaleString("ro-RO")}
          </p>
        )}
        {loading ? (
          <div className="flex items-center justify-center py-8 gap-2 text-slate-400">
            <Loader2 className="w-5 h-5 animate-spin" />
            <span className="text-[13px]">Se încarcă verificările runtime...</span>
          </div>
        ) : (
          <div className="flex items-center gap-0 min-w-max overflow-x-auto pb-1">
            {modules.map((node, idx) => (
              <ModuleNodeCard key={node.id} node={node} isLast={idx === modules.length - 1} />
            ))}
          </div>
        )}
      </section>

      {/* C. Evidence / legacy contract detail (reference) */}
      <section className="bg-[#111827] border border-[#1E293B] rounded-lg p-4" data-testid="module-chain-evidence">
        <SectionHeader
          title="Contracte detaliate (referință tehnică)"
          count={contractHandoffs.length}
          icon={<ArrowRight className="w-4 h-4" />}
        />
        <p className="text-[11px] text-slate-500 mb-3">
          Detalii de payload / interdicții — referință arhitecturală locală, nu stare live. Nu înlocuiesc documentele
          aprobate.
        </p>
        <div className="space-y-3">
          {contractHandoffs.map((handoff, idx) => (
            <div key={idx} className="bg-[#1A2236] border border-[#2A3548] rounded-lg p-3">
              <div className="flex items-center gap-3 mb-2">
                <span className="text-[13px] font-bold text-blue-400">{handoff.from}</span>
                <ArrowRight className="w-4 h-4 text-slate-600" />
                <span className="text-[13px] font-bold text-blue-400">{handoff.to}</span>
                <span className="ml-auto px-1.5 py-0.5 text-[9px] font-semibold rounded border bg-slate-700/50 text-slate-300 border-slate-600">
                  REFERINȚĂ
                </span>
              </div>
              <div className="grid grid-cols-1 md:grid-cols-2 gap-3">
                <div>
                  <p className="text-[10px] text-slate-500 uppercase tracking-wide mb-1">Payload</p>
                  <p className="text-[11px] text-slate-300 leading-relaxed">{handoff.payloadSummary}</p>
                </div>
                <div>
                  <p className="text-[10px] text-slate-500 uppercase tracking-wide mb-1 flex items-center gap-1">
                    <Ban className="w-3 h-3 text-red-400" /> Interzis
                  </p>
                  <div className="flex flex-wrap gap-1">
                    {handoff.forbidden.map((f, i) => (
                      <span
                        key={i}
                        className="px-1.5 py-0.5 text-[10px] bg-red-900/30 text-red-400 border border-red-800/40 rounded"
                      >
                        {f}
                      </span>
                    ))}
                  </div>
                </div>
              </div>
            </div>
          ))}
        </div>
      </section>
    </div>
  );
}
