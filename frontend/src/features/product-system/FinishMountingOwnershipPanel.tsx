import { Link } from "react-router-dom";
import {
  FINISH_MOUNTING_OWNERSHIP_LAW_RO,
  FINISH_OWNERSHIP_SUMMARY_RO,
  FINISH_RUNTIME_MAP,
  INSTALLATION_TEMPLATE_OWNERSHIP_SETTINGS,
  LEGACY_FINISAJE_ALIAS_CODES,
  LETTERS_OWNERSHIP_OWNER_GATES,
  MOUNTING_FIELD_MODEL_V1,
  MOUNTING_OWNERSHIP_SUMMARY_RO,
  MOUNTING_RUNTIME_MAP_NARROWED,
  PACKAGING_OWNERSHIP_SETTINGS,
  PACKAGING_OWNERSHIP_SUMMARY_RO,
  RUNTIME_RESPONSIBILITY_CODES,
  SNAPSHOT_LEGACY_VERSION,
  SNAPSHOT_WRITER_VERSION,
  TEMPLATE_OWNERSHIP_SUMMARY_RO,
  ownershipRowsByResponsibility,
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

function GateStatusPill({ status }: { status: "APPROVED" | "NOT_APPROVED" | "NOT_PLANNED" }) {
  if (status === "APPROVED") {
    return (
      <span className="rounded border border-emerald-800/40 px-1.5 py-0.5 text-[9px] font-semibold text-emerald-200">
        APPROVED
      </span>
    );
  }
  if (status === "NOT_PLANNED") {
    return (
      <span className="rounded border border-slate-600 px-1.5 py-0.5 text-[9px] font-semibold text-slate-400">
        NOT PLANNED
      </span>
    );
  }
  return (
    <span className="rounded border border-red-800/40 px-1.5 py-0.5 text-[9px] font-semibold text-red-300">
      NOT APPROVED
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
      <ul className="grid grid-cols-1 gap-2 sm:grid-cols-2">
        {rows.map((row) => (
          <li
            key={row.id}
            data-testid={`ownership-row-${row.id}`}
            className="min-w-0 rounded-md border border-slate-800/60 bg-slate-950/30 px-2.5 py-2"
          >
            <div className="flex flex-wrap items-start justify-between gap-2">
              <div className="min-w-0">
                <p className="break-words text-[12px] font-medium text-slate-100">{row.labelRo}</p>
                <p className="mt-0.5 break-all font-mono text-[10px] text-slate-500">{row.fieldKey}</p>
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
            <p className="mt-1 break-words text-[11px] text-slate-300">{row.ownerDetailRo}</p>
            <p className="mt-0.5 break-words text-[11px] text-slate-500">{row.noteRo}</p>
            {row.activation_gate !== "none" ? (
              <p className="mt-1 break-all text-[10px] text-amber-200/80">Gate: {row.activation_gate}</p>
            ) : null}
          </li>
        ))}
      </ul>
    </div>
  );
}

export function FinishMountingOwnershipPanel() {
  const surfaceRows = ownershipRowsByResponsibility("SURFACE_FINISH");
  const supportRows = ownershipRowsByResponsibility("STRUCTURE_SUPPORT");
  const legacyRows = ownershipRowsByResponsibility("LEGACY_ALIAS");
  const soldRows = ownershipRowsByResponsibility("SOLD_DEFERRED");

  return (
    <section
      data-testid="finish-mounting-ownership-panel"
      className="space-y-4 rounded-xl border border-slate-800/70 bg-[#0D1321]/40 px-4 py-4 text-sm text-slate-200"
    >
      <div>
        <p className="text-[11px] font-semibold uppercase tracking-wide text-slate-500">
          Responsabilități FINISH / MOUNTING / logistică
        </p>
        <p className="mt-1 text-[12px] text-slate-400">
          Desfacem bucket-ul mixt. Nu scoatem nimic din produs. Sold chip-uri rămân amânate.
        </p>
        <ul className="mt-2 space-y-0.5 text-[11px] text-slate-500" data-testid="ownership-law-lines">
          {FINISH_MOUNTING_OWNERSHIP_LAW_RO.map((line) => (
            <li key={line}>{line}</li>
          ))}
        </ul>
      </div>

      <div
        data-testid="responsibility-codes"
        className="flex flex-wrap gap-2 text-[10px] font-mono text-slate-300"
      >
        {(
          [
            ["surface", RUNTIME_RESPONSIBILITY_CODES.surfaceFinish],
            ["template", RUNTIME_RESPONSIBILITY_CODES.installationTemplate],
            ["packaging", RUNTIME_RESPONSIBILITY_CODES.packaging],
            ["support", RUNTIME_RESPONSIBILITY_CODES.support],
          ] as const
        ).map(([id, code]) => (
          <span
            key={id}
            data-testid={`responsibility-code-${id}`}
            className="max-w-full break-all rounded border border-slate-700 bg-slate-950/50 px-2 py-1"
          >
            {code}
          </span>
        ))}
      </div>

      <div
        data-testid="finish-ownership-summary"
        className="rounded-lg border border-amber-900/30 bg-amber-950/10 px-3 py-2 text-[12px] text-amber-100/90"
      >
        <p className="font-semibold text-amber-100">Surface FINISH</p>
        <p>{FINISH_OWNERSHIP_SUMMARY_RO.soldStatusRo}</p>
        <p>{FINISH_OWNERSHIP_SUMMARY_RO.targetOwnerRo}</p>
        <p>{FINISH_OWNERSHIP_SUMMARY_RO.catalogsRo}</p>
        <p className="text-amber-200/70">{FINISH_OWNERSHIP_SUMMARY_RO.runtimeBucketRo}</p>
        <p className="mt-1 break-all font-mono text-[10px] text-amber-200/60">
          {`FINISH → {${FINISH_RUNTIME_MAP.join(", ")}}`}
        </p>
      </div>

      <OwnershipRows
        title="1. Surface FINISH — responsabilitate curentă"
        rows={surfaceRows}
        testId="finish-ownership-rows"
      />

      <div
        data-testid="template-ownership-summary"
        className="rounded-lg border border-cyan-900/30 bg-cyan-950/10 px-3 py-2 text-[12px] text-cyan-100/90"
      >
        <p className="font-semibold text-cyan-100">Șablon montaj</p>
        <p>{TEMPLATE_OWNERSHIP_SUMMARY_RO.runtimeCodeRo}</p>
        <p>{TEMPLATE_OWNERSHIP_SUMMARY_RO.roleRo}</p>
        <p className="text-cyan-200/70">{TEMPLATE_OWNERSHIP_SUMMARY_RO.inactiveRo}</p>
      </div>

      <OwnershipRows
        title="2. Installation template — sablon_montaj"
        rows={INSTALLATION_TEMPLATE_OWNERSHIP_SETTINGS}
        testId="template-ownership-rows"
      />

      <div
        data-testid="packaging-ownership-summary"
        className="rounded-lg border border-sky-900/30 bg-sky-950/10 px-3 py-2 text-[12px] text-sky-100/90"
      >
        <p className="font-semibold text-sky-100">Ambalare / logistică</p>
        <p>{PACKAGING_OWNERSHIP_SUMMARY_RO.runtimeCodeRo}</p>
        <p>{PACKAGING_OWNERSHIP_SUMMARY_RO.roleRo}</p>
        <p className="text-sky-200/70">{PACKAGING_OWNERSHIP_SUMMARY_RO.mountingLeakRo}</p>
      </div>

      <OwnershipRows
        title="3. Packaging / logistics — ambalare_livrare_montaj"
        rows={PACKAGING_OWNERSHIP_SETTINGS}
        testId="packaging-ownership-rows"
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
        <p className="break-words text-emerald-200/80">{MOUNTING_OWNERSHIP_SUMMARY_RO.mapGateRo}</p>
        <p className="mt-1 break-all font-mono text-[10px] text-slate-500">
          {`MOUNTING → {${MOUNTING_RUNTIME_MAP_NARROWED.join(", ")}}`}
        </p>
      </div>

      <div data-testid="mounting-field-model" className="space-y-1.5 text-[11px]">
        <p className="font-semibold uppercase tracking-wide text-slate-500">Model câmpuri montaj V1</p>
        <div className="grid grid-cols-1 gap-1.5 sm:grid-cols-2">
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
              className="flex min-w-0 flex-wrap items-center justify-between gap-2 rounded border border-slate-800/50 px-2 py-1.5"
            >
              <span className="break-all font-mono text-slate-300">{key}</span>
              <StatusPill status={meta.status} />
              <span className="w-full break-words text-slate-500">{meta.labelRo}</span>
            </div>
          ))}
        </div>
      </div>

      <OwnershipRows
        title="4. Support — structura_suport"
        rows={supportRows}
        testId="mounting-ownership-rows"
      />

      <div
        data-testid="legacy-compatibility-block"
        className="rounded-lg border border-amber-900/40 bg-amber-950/15 px-3 py-2 text-[12px]"
      >
        <p className="font-semibold text-amber-100">Compatibilitate legacy</p>
        <p className="text-amber-100/90">
          Alias agregat legacy pentru snapshoturi vechi — nu modelul canonic curent.
        </p>
        <p className="mt-1 break-all font-mono text-[10px] text-amber-200/70">
          {LEGACY_FINISAJE_ALIAS_CODES.join(" · ")}
        </p>
        <p className="mt-1 text-[11px] text-slate-400">
          Writer: {SNAPSHOT_WRITER_VERSION} · Reader legacy: {SNAPSHOT_LEGACY_VERSION}
        </p>
      </div>

      <OwnershipRows
        title="5. Legacy alias — citire snapshot vechi"
        rows={legacyRows}
        testId="legacy-ownership-rows"
      />

      <OwnershipRows
        title="Sold chips — amânate"
        rows={soldRows}
        testId="sold-deferred-ownership-rows"
      />

      <div data-testid="ownership-owner-gates" className="space-y-2">
        <p className="text-[11px] font-semibold uppercase tracking-wide text-slate-500">
          Owner gates
        </p>
        <ul className="grid grid-cols-1 gap-1.5 sm:grid-cols-2">
          {LETTERS_OWNERSHIP_OWNER_GATES.map((gate) => (
            <li
              key={gate.id}
              data-testid={`ownership-gate-${gate.id}`}
              className="min-w-0 rounded-md border border-slate-800/50 bg-slate-950/40 px-2.5 py-2 text-[11px]"
            >
              <div className="flex flex-wrap items-center justify-between gap-2">
                <p className="break-all font-mono text-[10px] text-slate-300">{gate.id}</p>
                <GateStatusPill status={gate.status} />
              </div>
              <p className="mt-1 break-words text-slate-200">{gate.labelRo}</p>
              <p className="break-words text-slate-500">{gate.meaningRo}</p>
            </li>
          ))}
        </ul>
      </div>

      <div
        className="sticky bottom-0 z-10 flex flex-wrap gap-3 border-t border-slate-800/60 bg-[#0D1321]/95 py-2 text-[12px] backdrop-blur-sm"
        data-testid="ownership-action-links"
      >
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
