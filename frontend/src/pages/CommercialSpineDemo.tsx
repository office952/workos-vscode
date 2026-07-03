import { useEffect, useState } from "react";
import { Link } from "react-router-dom";
import {
  AlertTriangle,
  CheckCircle2,
  ExternalLink,
  FileText,
  Package,
  Activity,
  Database,
  Info,
} from "lucide-react";
import {
  probeCommercialSpineDemo,
  DEMO_PRIMARY_QUOTE,
  DEMO_WARN_QUOTE,
  DEMO_TEMPLATE,
  type CommercialSpineDemoProbeResult,
  type DemoScenarioSnapshot,
} from "@/lib/commercialSpineDemoProbe";

function StatusPill({ ok, label }: { ok: boolean; label: string }) {
  return (
    <span
      className={`inline-flex items-center gap-1 px-2 py-0.5 rounded-full text-[10px] font-semibold border ${
        ok
          ? "bg-emerald-900/40 text-emerald-300 border-emerald-700/50"
          : "bg-slate-800/60 text-slate-400 border-slate-600"
      }`}
    >
      {ok ? <CheckCircle2 className="w-3 h-3" /> : <AlertTriangle className="w-3 h-3" />}
      {label}
    </span>
  );
}

function MetricRow({ label, value }: { label: string; value: string }) {
  return (
    <div className="flex justify-between gap-4 text-[11px]">
      <span className="text-slate-500 shrink-0">{label}</span>
      <span className="text-slate-200 font-mono text-right break-all">{value}</span>
    </div>
  );
}

function ScenarioCard({
  title,
  description,
  scenario,
  expectedRequiresAck,
}: {
  title: string;
  description: string;
  scenario: DemoScenarioSnapshot;
  expectedRequiresAck: boolean;
}) {
  const quoteLink = `/quotes/${encodeURIComponent(scenario.quoteCode)}`;
  const orderLink = scenario.orderCode
    ? `/orders/${encodeURIComponent(scenario.orderCode)}`
    : null;
  const executionLink =
    scenario.orderDbId != null ? `/execution/${scenario.orderDbId}` : null;

  return (
    <div
      className="bg-[#111827] border border-[#1E293B] rounded-lg p-4 space-y-3"
      data-testid={`demo-scenario-${expectedRequiresAck ? "warn" : "ready"}`}
    >
      <div>
        <h3 className="text-[14px] font-bold text-slate-100">{title}</h3>
        <p className="text-[11px] text-slate-400 mt-1">{description}</p>
      </div>

      <div className="flex flex-wrap gap-2">
        <StatusPill ok={scenario.available} label={scenario.available ? "Fixture in DB" : "Fixture missing"} />
        {scenario.available && (
          <StatusPill
            ok={scenario.canCreateCommercialQuote === true}
            label="can_create_commercial_quote"
          />
        )}
        {scenario.available && (
          <StatusPill
            ok={scenario.requiresAcknowledgement === expectedRequiresAck}
            label={`requires_ack=${String(expectedRequiresAck)}`}
          />
        )}
        {scenario.orderCode ? (
          <StatusPill ok label="Order exists" />
        ) : (
          <StatusPill ok={false} label="No order yet" />
        )}
        {scenario.executionPlanExists ? (
          <StatusPill ok label={`Plan (${scenario.executionPlanTaskCount ?? 0} tasks)`} />
        ) : scenario.orderDbId ? (
          <StatusPill ok={false} label="Plan not generated" />
        ) : null}
      </div>

      <div className="bg-[#0B111E] border border-[#1E293B] rounded px-3 py-2 space-y-1.5">
        <MetricRow label="Quote" value={scenario.quoteCode} />
        <MetricRow label="readiness_overlay" value="null" />
        {scenario.quoteStatus && <MetricRow label="quote_status" value={scenario.quoteStatus} />}
        {scenario.canCreateCommercialQuote != null && (
          <MetricRow
            label="can_create_commercial_quote"
            value={String(scenario.canCreateCommercialQuote)}
          />
        )}
        {scenario.requiresAcknowledgement != null && (
          <MetricRow
            label="requires_acknowledgement"
            value={String(scenario.requiresAcknowledgement)}
          />
        )}
        {scenario.available && scenario.acknowledgementPending.length > 0 && (
          <>
            <MetricRow
              label="ack_pending_count"
              value={String(scenario.acknowledgementPending.length)}
            />
            <MetricRow
              label="acknowledgement_pending"
              value={scenario.acknowledgementPending.join(", ")}
            />
          </>
        )}
        {scenario.orderCode && <MetricRow label="order_code" value={scenario.orderCode} />}
        {scenario.unavailableReason && (
          <p className="text-[10px] text-amber-400 pt-1">{scenario.unavailableReason}</p>
        )}
      </div>

      <div className="flex flex-wrap gap-2">
        <Link
          to={quoteLink}
          data-testid={`demo-link-quote-${expectedRequiresAck ? "warn" : "ready"}`}
          className="inline-flex items-center gap-1.5 px-3 py-1.5 text-[11px] font-semibold rounded border border-blue-700/50 text-blue-300 hover:bg-blue-950/30"
        >
          <FileText className="w-3.5 h-3.5" />
          Open Quote
          <ExternalLink className="w-3 h-3 opacity-60" />
        </Link>
        {orderLink ? (
          <Link
            to={orderLink}
            data-testid={`demo-link-order-${expectedRequiresAck ? "warn" : "ready"}`}
            className="inline-flex items-center gap-1.5 px-3 py-1.5 text-[11px] font-semibold rounded border border-purple-700/50 text-purple-300 hover:bg-purple-950/30"
          >
            <Package className="w-3.5 h-3.5" />
            Open Order
            <ExternalLink className="w-3 h-3 opacity-60" />
          </Link>
        ) : (
          <span className="text-[10px] text-slate-500 self-center">
            Convert from quote first to open order.
          </span>
        )}
        {executionLink ? (
          <Link
            to={executionLink}
            data-testid={`demo-link-execution-${expectedRequiresAck ? "warn" : "ready"}`}
            className="inline-flex items-center gap-1.5 px-3 py-1.5 text-[11px] font-semibold rounded border border-cyan-700/50 text-cyan-300 hover:bg-cyan-950/30"
          >
            <Activity className="w-3.5 h-3.5" />
            Open Execution
            <ExternalLink className="w-3 h-3 opacity-60" />
          </Link>
        ) : null}
      </div>

      {expectedRequiresAck ? (
        <p className="text-[10px] text-amber-300/90 border-t border-[#1E293B] pt-2">
          Next: open quote → check acknowledgement control → convert → order → execution plan 201.
        </p>
      ) : (
        <p className="text-[10px] text-slate-500 border-t border-[#1E293B] pt-2">
          Next: open quote → convert when priced/accepted → order → execution plan 201.
        </p>
      )}
    </div>
  );
}

export default function CommercialSpineDemo() {
  const [probe, setProbe] = useState<CommercialSpineDemoProbeResult | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    let alive = true;
    setLoading(true);
    probeCommercialSpineDemo()
      .then((result) => {
        if (!alive) return;
        setProbe(result);
        setError(null);
      })
      .catch((err: unknown) => {
        if (!alive) return;
        setError(err instanceof Error ? err.message : "Probe failed");
      })
      .finally(() => {
        if (alive) setLoading(false);
      });
    return () => {
      alive = false;
    };
  }, []);

  return (
    <div className="max-w-4xl mx-auto space-y-4" data-testid="commercial-spine-demo-page">
      <div className="bg-amber-900/20 border border-amber-700/50 rounded-lg px-4 py-3 flex gap-2">
        <AlertTriangle className="w-5 h-5 text-amber-400 shrink-0" />
        <div>
          <p
            className="text-[12px] font-bold text-amber-200"
            data-testid="commercial-spine-demo-internal-label"
          >
            Internal Demo — not production workflow
          </p>
          <p className="text-[11px] text-amber-300/80 mt-0.5">
            Dev/onboarding only. TPL-VOLUMETRIC-LETTERS commercial spine traceability. Not a public
            sales demo.
          </p>
        </div>
      </div>

      <div>
        <h1 className="text-[20px] font-bold text-slate-100">Internal Commercial Spine Demo</h1>
        <p className="text-[13px] text-slate-400 mt-1">
          {DEMO_TEMPLATE} quote → order → execution plan
        </p>
      </div>

      <div className="bg-[#111827] border border-[#1E293B] rounded-lg p-4 space-y-2" data-testid="demo-proof-summary">
        <h2 className="text-[13px] font-semibold text-slate-200">Current proof summary</h2>
        <ul className="text-[11px] text-slate-400 space-y-1 list-disc list-inside">
          <li>
            <span className="text-slate-300">Ready path:</span> quote → order → execution plan{" "}
            <span className="font-mono text-emerald-400">201</span> ({DEMO_PRIMARY_QUOTE})
          </li>
          <li>
            <span className="text-slate-300">Warn-ack path:</span> warning → acknowledgement → quote
            → order → execution plan <span className="font-mono text-emerald-400">201</span> (
            {DEMO_WARN_QUOTE})
          </li>
          <li>
            <span className="text-slate-300">readiness_overlay:</span>{" "}
            <span className="font-mono text-slate-300">null</span> on both fixtures
          </li>
        </ul>
      </div>

      <div className="bg-[#111827] border border-[#1E293B] rounded-lg p-4 space-y-2" data-testid="demo-command-panel">
        <div className="flex items-center gap-2">
          <Database className="w-4 h-4 text-blue-400" />
          <h2 className="text-[13px] font-semibold text-slate-200">Setup</h2>
        </div>
        <pre className="text-[10px] font-mono text-slate-400 bg-[#0B111E] border border-[#1E293B] rounded p-3 overflow-x-auto whitespace-pre-wrap">
{`# Set DATABASE_URL to your local dev.db (see docs/demo/COMMERCIAL_SPINE_DEMO.md)
$env:APP_ENV='development'
cd backend
.\\.venv\\Scripts\\python.exe scripts/seed_commercial_e2e_fixture.py

cd frontend
npm run dev   # :3000 with API proxy

# Re-seed before E2E if fixtures were converted
npm run test:e2e:commercial-live
npm run test:e2e:commercial-warn-ack
npm run test:e2e:commercial-spine-demo
npm run test:e2e:commercial`}
        </pre>
        <p className="text-[10px] text-slate-500 flex items-start gap-1">
          <Info className="w-3 h-3 shrink-0 mt-0.5" />
          Re-seed before E2E if fixture quotes were already converted. Status below is probed from
          live backend API — no local manifest file reads.
        </p>
      </div>

      {loading && (
        <p className="text-[12px] text-slate-500">Probing fixture status from backend…</p>
      )}
      {error && (
        <p className="text-[12px] text-red-400">Probe error: {error}</p>
      )}
      {probe && !probe.backendHealthy && (
        <p className="text-[12px] text-amber-400">
          Backend unavailable: {probe.backendReason}
        </p>
      )}

      {probe && (
        <div className="grid grid-cols-1 lg:grid-cols-2 gap-4">
          <ScenarioCard
            title="A. Ready quote scenario"
            description="Primary fixture — no acknowledgement required before convert."
            scenario={probe.primary}
            expectedRequiresAck={false}
          />
          <ScenarioCard
            title="B. Warning acknowledgement scenario"
            description="WARN fixture — convert gated until operator acknowledges commercial warnings."
            scenario={probe.warn}
            expectedRequiresAck={true}
          />
        </div>
      )}

      <div
        className="bg-[#111827] border border-[#1E293B] rounded-lg p-4 space-y-2"
        data-testid="demo-caveat-panel"
      >
        <h2 className="text-[13px] font-semibold text-slate-200">Caveats</h2>
        <ul className="text-[11px] text-slate-500 space-y-1 list-disc list-inside">
          <li>{DEMO_TEMPLATE} only — unsupported templates remain unsupported</li>
          <li>Fixture-based dev data — not production seed</li>
          <li>Does not prove CostEngine formulas, inventory, or status lifecycle</li>
          <li>Conversion and execution are real backend paths, not mocked in demo probe</li>
          <li>Not in production sidebar — internal/dev walkthrough only</li>
        </ul>
      </div>

      <div className="text-[10px] text-slate-600 border-t border-[#1E293B] pt-3">
        Proven in commits 43635cf, 717b4d7, bedc25f, 821bd37 (demo). Does not prove other
        templates or public sales readiness.
      </div>
    </div>
  );
}
