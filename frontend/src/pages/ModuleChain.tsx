import { useState } from "react";
import { ModuleNodeCard, SectionHeader } from "@/components/workos/SharedComponents";
import {
  GitBranch,
  ArrowRight,
  Wifi,
  WifiOff,
  RefreshCw,
  Loader2,
  AlertTriangle,
  BookOpen,
  ExternalLink,
} from "lucide-react";
import { useModuleChainData } from "@/hooks/useModuleChainData";
import {
  CANONICAL_CONCEPTS,
  CANONICAL_ROUTES,
  CANONICAL_SPINE_LABELS_RO,
  MODULE_CHAIN_TABS,
  PRESENT_EVIDENCE,
  PRESENT_HANDOFFS,
  PRESENT_SUPPORT_SYSTEMS,
  PRESENT_SYSTEMS,
  STABILIZATION_PRODUCTS,
  presentStatusBadgeClass,
  type ModuleChainTabId,
} from "@/lib/currentTruthControlCenter";
import { Link } from "react-router-dom";

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
    return {
      label: "Backend disponibil",
      className: "bg-emerald-900/40 text-emerald-300 border-emerald-700",
    };
  }
  if (aggregateStatus === "warning" || aggregateStatus === "degraded") {
    return {
      label: "Backend cu avertisment",
      className: "bg-amber-900/40 text-amber-300 border-amber-700",
    };
  }
  if (aggregateStatus === "fail") {
    return {
      label: "Backend degradat",
      className: "bg-red-900/40 text-red-300 border-red-700",
    };
  }
  return { label: "NEVERIFICAT", className: "bg-slate-700/60 text-slate-300 border-slate-600" };
}

function SystemCard({
  system,
  testIdPrefix,
}: {
  system: (typeof PRESENT_SYSTEMS)[number];
  testIdPrefix: string;
}) {
  return (
    <div
      className="bg-[#1A2236] border border-[#2A3548] rounded-lg px-3 py-3 min-w-[220px] max-w-[280px] flex-1"
      data-testid={`${testIdPrefix}-${system.id}`}
    >
      <div className="flex items-start justify-between gap-2 mb-1">
        <div>
          <span className="text-[13px] font-semibold text-slate-100">{system.labelRo}</span>
          <p className="text-[10px] text-slate-500">{system.technicalName}</p>
        </div>
        <span
          className={`shrink-0 px-1.5 py-0.5 text-[9px] font-semibold rounded border ${presentStatusBadgeClass(system.status)}`}
        >
          {system.status}
        </span>
      </div>
      <p className="text-[11px] text-slate-300 leading-snug mb-2">{system.purposeRo}</p>
      <dl className="space-y-1 text-[10px] text-slate-400">
        <div>
          <dt className="text-slate-500 uppercase tracking-wide">Proprietar</dt>
          <dd className="text-slate-300">{system.owner}</dd>
        </div>
        <div>
          <dt className="text-slate-500 uppercase tracking-wide">Intrare</dt>
          <dd>{system.inputRo}</dd>
        </div>
        <div>
          <dt className="text-slate-500 uppercase tracking-wide">Ieșire</dt>
          <dd>{system.outputRo}</dd>
        </div>
        <div>
          <dt className="text-slate-500 uppercase tracking-wide">Consumator</dt>
          <dd>{system.consumerRo}</dd>
        </div>
        <div>
          <dt className="text-slate-500 uppercase tracking-wide">Limită actuală</dt>
          <dd className="text-amber-200/90">{system.limitationRo}</dd>
        </div>
        <div>
          <dt className="text-slate-500 uppercase tracking-wide">Verificare</dt>
          <dd className="flex items-center gap-1 text-blue-300">
            <ExternalLink className="w-3 h-3" />
            <a href={system.verifyRoute} className="hover:underline">
              {system.verifyRoute}
            </a>
          </dd>
        </div>
      </dl>
    </div>
  );
}

export default function ModuleChain() {
  const [activeTab, setActiveTab] = useState<ModuleChainTabId>("system_map");
  const { modules, aggregateStatus, generatedAt, loading, error, isLive, refetch, health } =
    useModuleChainData(30000);

  const runtimeBadge = runtimeLabelRo(aggregateStatus, isLive, loading, error);
  const checksCount = health ? Object.keys(health.checks || {}).length : 0;
  const dbVerified = checksCount > 0 && Boolean(health?.checks?.database);

  return (
    <div className="space-y-4" data-testid="module-chain-page">
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
            {isLive ? "Health API (agregat)" : "Health indisponibil"}
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
          Control center — adevărul prezent al sistemelor WorkOS. Proiecție read-only.
        </p>
      </div>

      <div
        className="flex items-start gap-2 px-3 py-2.5 bg-amber-900/15 border border-amber-800/40 rounded-lg"
        data-testid="module-chain-honesty-banner"
      >
        <AlertTriangle className="w-4 h-4 text-amber-400 mt-0.5 shrink-0" />
        <p className="text-[12px] text-amber-200/95 leading-relaxed">
          Această hartă descrie ce există acum: status, contracte active, proprietar și limitări. Dovezile
          istorice (inclusiv PROVEN_V1) sunt în tab-ul Surse și dovezi — nu sunt status de sănătate.
        </p>
      </div>

      <div
        className="flex items-center gap-1 bg-[#111827] border border-[#1E293B] rounded-lg p-1 overflow-x-auto"
        data-testid="module-chain-tabs"
        role="tablist"
        aria-label="Harta sistemelor — secțiuni"
      >
        {MODULE_CHAIN_TABS.map((tab) => (
          <button
            key={tab.id}
            type="button"
            role="tab"
            aria-selected={activeTab === tab.id}
            data-testid={`module-chain-tab-${tab.id}`}
            onClick={() => setActiveTab(tab.id)}
            className={`flex items-center gap-1.5 px-3 py-2 text-[12px] font-medium rounded-md transition-colors whitespace-nowrap ${
              activeTab === tab.id
                ? "bg-blue-600/20 text-blue-400 border border-blue-600/30"
                : "text-slate-400 hover:text-slate-200 hover:bg-slate-800/50 border border-transparent"
            }`}
          >
            {tab.labelRo}
          </button>
        ))}
      </div>

      {activeTab === "system_map" && (
        <section
          className="bg-[#111827] border border-[#1E293B] rounded-lg p-4 space-y-4"
          data-testid="module-chain-architecture"
          role="tabpanel"
        >
          <SectionHeader title="Spine activ" icon={<GitBranch className="w-4 h-4 text-blue-400" />} />
          <p className="text-[11px] text-slate-500" data-testid="canonical-spine-label">
            Fluxul activ unic: {CANONICAL_SPINE_LABELS_RO.join(" → ")}
          </p>
          <div className="flex flex-wrap gap-2" data-testid="canonical-spine-systems">
            {PRESENT_SYSTEMS.map((system) => (
              <SystemCard key={system.id} system={system} testIdPrefix="arch-node" />
            ))}
          </div>
          <p className="text-[11px] font-semibold text-slate-400">Sisteme suport (în afara spine-ului)</p>
          <div className="flex flex-wrap gap-2">
            {PRESENT_SUPPORT_SYSTEMS.map((system) => (
              <SystemCard key={system.id} system={system} testIdPrefix="support-node" />
            ))}
          </div>

          <div className="border-t border-[#1E293B] pt-4 space-y-3" data-testid="canonical-concept-map">
            <SectionHeader title="Vocabular Product System (distinct)" icon={<BookOpen className="w-4 h-4 text-violet-400" />} />
            <p className="text-[11px] text-slate-500">
              Familie ≠ Șablon produs ≠ Componentă ≠ Mini-modul ≠ Capability. Scope stabilizare doar Litere + Logo + ACM.
            </p>
            <div className="grid grid-cols-1 md:grid-cols-2 gap-2">
              {CANONICAL_CONCEPTS.map((concept) => (
                <div
                  key={concept.id}
                  className="bg-[#1A2236] border border-[#2A3548] rounded-lg p-3"
                  data-testid={`concept-node-${concept.id}`}
                >
                  <div className="flex items-start justify-between gap-2 mb-1">
                    <div>
                      <p className="text-[13px] font-bold text-slate-100">{concept.nameRo}</p>
                      <p className="text-[10px] text-slate-500">{concept.technicalName}</p>
                    </div>
                    <span className="px-1.5 py-0.5 text-[9px] font-semibold rounded border border-violet-700/50 text-violet-300 whitespace-nowrap">
                      {concept.status}
                    </span>
                  </div>
                  <p className="text-[11px] text-slate-300 mb-1">{concept.definitionRo}</p>
                  <p className="text-[10px] text-slate-500">Owner: {concept.ownerRo}</p>
                  <p className="text-[10px] text-amber-400/90 mt-1">{concept.notRo}</p>
                  <Link
                    to={concept.verifyRoute}
                    className="inline-flex items-center gap-1 text-[10px] text-blue-400 hover:text-blue-300 mt-2"
                  >
                    <ExternalLink className="w-3 h-3" />
                    {concept.verifyRoute}
                  </Link>
                </div>
              ))}
            </div>
          </div>

          <div className="border-t border-[#1E293B] pt-4 space-y-2" data-testid="stabilization-scope">
            <p className="text-[11px] font-semibold text-slate-400">Scope stabilizare activ</p>
            <div className="space-y-2">
              {STABILIZATION_PRODUCTS.map((product) => (
                <div
                  key={product.id}
                  className="bg-[#1A2236] border border-[#2A3548] rounded-lg p-3 text-[11px]"
                  data-testid={`stabilization-${product.id}`}
                >
                  <div className="flex flex-wrap items-center gap-2 mb-1">
                    <span className="font-bold text-slate-100">{product.familyLabelRo}</span>
                    <code className="text-[10px] text-slate-400">{product.templateCode}</code>
                    <span
                      className={`ml-auto px-1.5 py-0.5 text-[9px] font-semibold rounded border ${presentStatusBadgeClass(
                        product.usageStatus === "ACTIVE" ? "CONFIRMAT" : "PARTIAL"
                      )}`}
                    >
                      {product.usageStatus}
                    </span>
                  </div>
                  <p className="text-slate-400">{product.limitationRo}</p>
                </div>
              ))}
            </div>
          </div>

          <div
            className="border-t border-[#1E293B] pt-3 flex flex-wrap gap-3 text-[11px]"
            data-testid="canonical-route-links"
          >
            <Link to={CANONICAL_ROUTES.inventory} className="text-blue-400 hover:text-blue-300 inline-flex items-center gap-1">
              <ExternalLink className="w-3 h-3" /> Inventory {CANONICAL_ROUTES.inventory}
            </Link>
            <Link to={CANONICAL_ROUTES.pricing} className="text-blue-400 hover:text-blue-300 inline-flex items-center gap-1">
              <ExternalLink className="w-3 h-3" /> Pricing {CANONICAL_ROUTES.pricing}
            </Link>
            <Link to={CANONICAL_ROUTES.dossier} className="text-blue-400 hover:text-blue-300 inline-flex items-center gap-1">
              <ExternalLink className="w-3 h-3" /> Dossier {CANONICAL_ROUTES.dossier}
            </Link>
          </div>

          <p
            className="text-[11px] text-slate-500 border border-slate-700/60 rounded-md px-3 py-2"
            data-testid="legacy-spine-notice"
          >
            Referință istorică OC→TK — nu reprezintă fluxul activ. Vezi Surse și dovezi.
          </p>
        </section>
      )}

      {activeTab === "handoffs" && (
        <section className="space-y-4" data-testid="module-chain-handoffs" role="tabpanel">
          <div className="bg-[#111827] border border-[#1E293B] rounded-lg p-4">
            <SectionHeader
              title="Contracte și transferuri active"
              icon={<ArrowRight className="w-4 h-4" />}
            />
            <p className="text-[11px] text-slate-500 mb-3">
              Handoff-uri din spine-ul activ. Fără lanț OC→TK ca flux paralel.
            </p>
            <div className="space-y-2">
              {PRESENT_HANDOFFS.map((h) => (
                <div
                  key={h.id}
                  className="bg-[#1A2236] border border-[#2A3548] rounded-lg p-3"
                  data-testid={`handoff-${h.producerId}-${h.consumerId}`}
                >
                  <div className="flex items-center gap-2 flex-wrap mb-1">
                    <span className="text-[13px] font-bold text-blue-400">{h.producerRo}</span>
                    <ArrowRight className="w-3.5 h-3.5 text-slate-600" />
                    <span className="text-[13px] font-bold text-blue-400">{h.consumerRo}</span>
                    <span
                      className={`ml-auto px-1.5 py-0.5 text-[9px] font-semibold rounded border ${presentStatusBadgeClass(h.status)}`}
                    >
                      {h.status}
                    </span>
                  </div>
                  <dl className="grid grid-cols-1 md:grid-cols-2 gap-2 text-[11px] text-slate-400 mt-2">
                    <div>
                      <dt className="text-[10px] text-slate-500 uppercase">Contract ieșire</dt>
                      <dd className="text-slate-300">{h.outputContractRo}</dd>
                    </div>
                    <div>
                      <dt className="text-[10px] text-slate-500 uppercase">Punct de aplicare</dt>
                      <dd>{h.enforcementRo}</dd>
                    </div>
                    <div className="md:col-span-2">
                      <dt className="text-[10px] text-slate-500 uppercase">Verificare</dt>
                      <dd className="flex items-center gap-1">
                        <BookOpen className="w-3 h-3" />
                        {h.verificationRo}
                      </dd>
                    </div>
                  </dl>
                </div>
              ))}
            </div>
          </div>
        </section>
      )}

      {activeTab === "runtime" && (
        <section
          className="bg-[#111827] border border-[#1E293B] rounded-lg p-4"
          data-testid="module-chain-runtime"
          role="tabpanel"
        >
          <div className="flex items-center gap-2 mb-2 flex-wrap">
            <SectionHeader title="Stare runtime" icon={<Wifi className="w-4 h-4 text-slate-400" />} />
            <span
              className={`px-2 py-0.5 text-[10px] font-semibold rounded border ${runtimeBadge.className}`}
              data-testid="module-chain-runtime-aggregate"
            >
              {runtimeBadge.label}
            </span>
          </div>
          <p className="text-[11px] text-slate-500 mb-3">
            Doar verificări din <code className="text-slate-400">GET /api/v1/system/health</code>. Statusul
            agregat nu înseamnă DB verificată. Fără check mapat = Neverificat — nu „LIVE”.
          </p>
          <div
            className="grid grid-cols-1 sm:grid-cols-3 gap-2 mb-3 text-[11px]"
            data-testid="module-chain-runtime-distinctions"
          >
            <div className="bg-[#1A2236] border border-[#2A3548] rounded-md px-3 py-2">
              <p className="text-slate-500 text-[10px] uppercase">Backend</p>
              <p className="text-slate-200">{runtimeBadge.label}</p>
            </div>
            <div className="bg-[#1A2236] border border-[#2A3548] rounded-md px-3 py-2">
              <p className="text-slate-500 text-[10px] uppercase">DB</p>
              <p className="text-slate-200">
                {dbVerified ? "DB verificată (check mapat)" : "DB neverificată"}
              </p>
            </div>
            <div className="bg-[#1A2236] border border-[#2A3548] rounded-md px-3 py-2">
              <p className="text-slate-500 text-[10px] uppercase">Checks publice</p>
              <p className="text-slate-200">{checksCount === 0 ? "Goale / redacted" : `${checksCount} check-uri`}</p>
            </div>
          </div>
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
      )}

      {activeTab === "evidence" && (
        <section
          className="bg-[#111827] border border-[#1E293B] rounded-lg p-4"
          data-testid="module-chain-evidence"
          role="tabpanel"
        >
          <SectionHeader title="Surse și dovezi" icon={<BookOpen className="w-4 h-4 text-blue-400" />} />
          <p className="text-[11px] text-slate-500 mb-3">
            Dovezi și istoric — separate de statusul prezent. PROVEN_V1 = calificare dovadă, nu sănătate
            sistem.
          </p>
          <div className="space-y-2">
            {PRESENT_EVIDENCE.map((ev) => (
              <div
                key={ev.id}
                className="bg-[#1A2236] border border-[#2A3548] rounded-md px-3 py-2 text-[11px]"
                data-testid={`evidence-${ev.id}`}
              >
                <div className="flex flex-wrap items-center gap-2 mb-1">
                  <span className="text-[9px] uppercase tracking-wide text-slate-500 border border-slate-600 px-1.5 py-0.5 rounded">
                    {ev.category}
                  </span>
                  <span className="text-slate-200 font-medium">{ev.title}</span>
                  <span className="text-[10px] text-slate-500">{ev.date}</span>
                  <span
                    className={`ml-auto px-1.5 py-0.5 rounded border text-[9px] ${
                      ev.stillCurrentRuntime
                        ? "border-emerald-800/50 text-emerald-300"
                        : "border-slate-600 text-slate-400"
                    }`}
                  >
                    {ev.stillCurrentRuntime ? "Relevant runtime acum" : "Istoric / nu status runtime"}
                  </span>
                </div>
                <p className="text-slate-400 mb-1">{ev.provesRo}</p>
                <p className="text-slate-500 font-mono text-[10px]">{ev.source}</p>
              </div>
            ))}
          </div>
        </section>
      )}
    </div>
  );
}
