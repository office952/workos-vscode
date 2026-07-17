import { Link } from "react-router-dom";
import {
  FINISH_OWNERSHIP_SETTINGS,
  FINISH_OWNERSHIP_SUMMARY_RO,
  FINISH_MOUNTING_OWNERSHIP_LAW_RO,
  LETTERS_OWNERSHIP_OWNER_GATES,
  MOUNTING_FIELD_MODEL_V1,
  MOUNTING_OWNERSHIP_SETTINGS,
  MOUNTING_OWNERSHIP_SUMMARY_RO,
  ownershipStatusLabelRo,
  type OwnershipSettingRecord,
} from "@/lib/lettersFinishMountingOwnership";

function StatusPill({ status }: { status: OwnershipSettingRecord["runtime_status"] }) {
  const tone =
    status === "CURRENT"
      ? "border-emerald-800/50 bg-emerald-950/20 text-emerald-200"
      : status === "TARGET"
        ? "border-violet-800/50 bg-violet-950/20 text-violet-200"
        : status === "COMPATIBILITY_ALIAS"
          ? "border-amber-800/50 bg-amber-950/20 text-amber-200"
          : status === "BLOCKED"
            ? "border-red-800/50 bg-red-950/20 text-red-200"
            : "border-slate-700 bg-slate-900/40 text-slate-400";
  return (
    <span className={`rounded border px-1.5 py-0.5 text-[9px] font-semibold uppercase tracking-wide ${tone}`}>
      {ownershipStatusLabelRo(status)}
    </span>
  );
}

function OwnershipRows({
  title,
  rows,
  testId,
}: {
  title: string;
  rows: readonly OwnershipSettingRecord[];
  testId: string;
}) {
  return (
    <div data-testid={testId} className="space-y-2">
      <p className="text-[11px] font-semibold uppercase tracking-wide text-slate-500">{title}</p>
      <ul className="space-y-2">
        {rows.map((row) => (
          <li
            key={row.id}
            data-testid={`ownership-row-${row.id}`}
            className="rounded-md border border-slate-800/60 bg-slate-950/30 px-2.5 py-2"
          >
            <div className="flex flex-wrap items-start justify-between gap-2">
              <div className="min-w-0">
                <p className="text-[12px] font-medium text-slate-100">{row.labelRo}</p>
                <p className="mt-0.5 font-mono text-[10px] text-slate-500">{row.fieldKey}</p>
              </div>
              <div className="flex flex-wrap items-center gap-1">
                <StatusPill status={row.runtime_status} />
                {row.current_or_target === "TARGET" ? (
                  <span className="rounded border border-violet-800/40 px-1.5 py-0.5 text-[9px] text-violet-300">
                    ȚINTĂ
                  </span>
                ) : null}
              </div>
            </div>
            <p className="mt-1 text-[11px] text-slate-300">{row.ownerDetailRo}</p>
            <p className="mt-0.5 text-[11px] text-slate-500">{row.noteRo}</p>
            {row.activation_gate !== "none" ? (
              <p className="mt-1 text-[10px] text-amber-200/80">Gate: {row.activation_gate}</p>
            ) : null}
          </li>
        ))}
      </ul>
    </div>
  );
}

export function FinishMountingOwnershipPanel() {
  return (
    <section
      data-testid="finish-mounting-ownership-panel"
      className="space-y-4 rounded-xl border border-slate-800/70 bg-[#0D1321]/40 px-4 py-4 text-sm text-slate-200"
    >
      <div>
        <p className="text-[11px] font-semibold uppercase tracking-wide text-slate-500">
          Ownership FINISH / MOUNTING
        </p>
        <p className="mt-1 text-[12px] text-slate-400">
          Contracte întâi. Activarea mai târziu. Nu se schimbă ieșirile sold curente.
        </p>
        <ul className="mt-2 space-y-0.5 text-[11px] text-slate-500" data-testid="ownership-law-lines">
          {FINISH_MOUNTING_OWNERSHIP_LAW_RO.map((line) => (
            <li key={line}>{line}</li>
          ))}
        </ul>
      </div>

      <div
        data-testid="finish-ownership-summary"
        className="rounded-lg border border-amber-900/30 bg-amber-950/10 px-3 py-2 text-[12px] text-amber-100/90"
      >
        <p className="font-semibold text-amber-100">FINISH</p>
        <p>{FINISH_OWNERSHIP_SUMMARY_RO.soldStatusRo}</p>
        <p>{FINISH_OWNERSHIP_SUMMARY_RO.targetOwnerRo}</p>
        <p>{FINISH_OWNERSHIP_SUMMARY_RO.catalogsRo}</p>
        <p className="text-amber-200/70">{FINISH_OWNERSHIP_SUMMARY_RO.runtimeBucketRo}</p>
      </div>

      <OwnershipRows
        title="C. FINISH — ownership (current / target)"
        rows={FINISH_OWNERSHIP_SETTINGS}
        testId="finish-ownership-rows"
      />

      <div
        data-testid="mounting-ownership-summary"
        className="rounded-lg border border-slate-700/60 bg-slate-950/40 px-3 py-2 text-[12px] text-slate-200"
      >
        <p className="font-semibold text-slate-100">MOUNTING</p>
        <p>{MOUNTING_OWNERSHIP_SUMMARY_RO.linkedSupportRo}</p>
        <p>{MOUNTING_OWNERSHIP_SUMMARY_RO.soldStatusRo}</p>
        <p>{MOUNTING_OWNERSHIP_SUMMARY_RO.methodFieldRo}</p>
        <p>{MOUNTING_OWNERSHIP_SUMMARY_RO.solutionFieldRo}</p>
        <p>{MOUNTING_OWNERSHIP_SUMMARY_RO.aliasFieldRo}</p>
        <p className="text-amber-200/80">{MOUNTING_OWNERSHIP_SUMMARY_RO.mapGateRo}</p>
      </div>

      <div data-testid="mounting-field-model" className="space-y-1.5 text-[11px]">
        <p className="font-semibold uppercase tracking-wide text-slate-500">Model câmpuri montaj V1</p>
        {(
          [
            ["mounting_scope", MOUNTING_FIELD_MODEL_V1.mounting_scope],
            ["mounting_system", MOUNTING_FIELD_MODEL_V1.mounting_system],
            ["mounting_solution", MOUNTING_FIELD_MODEL_V1.mounting_solution],
            ["metal_support_required", MOUNTING_FIELD_MODEL_V1.metal_support_required],
            ["mounting_method", MOUNTING_FIELD_MODEL_V1.mounting_method],
          ] as const
        ).map(([key, meta]) => (
          <div
            key={key}
            className="flex flex-wrap items-center justify-between gap-2 rounded border border-slate-800/50 px-2 py-1.5"
          >
            <span className="font-mono text-slate-300">{key}</span>
            <StatusPill status={meta.status} />
            <span className="w-full text-slate-500">{meta.labelRo}</span>
          </div>
        ))}
      </div>

      <OwnershipRows
        title="D. MOUNTING — ownership (current / target / alias)"
        rows={MOUNTING_OWNERSHIP_SETTINGS}
        testId="mounting-ownership-rows"
      />

      <div data-testid="ownership-owner-gates" className="space-y-2">
        <p className="text-[11px] font-semibold uppercase tracking-wide text-slate-500">
          Owner gates — neaprobate
        </p>
        <ul className="space-y-1.5">
          {LETTERS_OWNERSHIP_OWNER_GATES.map((gate) => (
            <li
              key={gate.id}
              data-testid={`ownership-gate-${gate.id}`}
              className="rounded-md border border-red-900/30 bg-red-950/10 px-2.5 py-2 text-[11px]"
            >
              <p className="font-mono text-[10px] text-red-200">{gate.id}</p>
              <p className="text-slate-200">{gate.labelRo}</p>
              <p className="text-slate-500">{gate.meaningRo}</p>
              <p className="mt-0.5 font-semibold text-red-300/90">NOT APPROVED</p>
            </li>
          ))}
        </ul>
      </div>

      <div className="flex flex-wrap gap-3 text-[12px]" data-testid="ownership-action-links">
        <Link to="/intake-v6" className="text-blue-400 hover:text-blue-300">
          Intake V6
        </Link>
        <Link to="/product-system/blueprint-dossier" className="text-blue-400 hover:text-blue-300">
          Blueprint Dossier
        </Link>
        <Link to="/modules" className="text-blue-400 hover:text-blue-300">
          Modules
        </Link>
        <Link to="/governance" className="text-blue-400 hover:text-blue-300">
          Governance
        </Link>
      </div>
    </section>
  );
}
