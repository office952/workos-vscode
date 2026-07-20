import {
  buildLegacyReplacementSummary,
  legacyReplacementStatusLabel,
  LEGACY_TO_COMPONENT_FIRST_REPLACEMENT_MAP,
  resolveLegacyReplacementEntry,
  type LegacyReplacementMapEntry,
} from "./legacyToComponentFirstReplacementMap";

function StatusChip({
  label,
  tone,
  testId,
}: {
  label: string;
  tone: "emerald" | "amber" | "rose" | "slate" | "cyan";
  testId?: string;
}) {
  const toneClass =
    tone === "emerald"
      ? "border-emerald-800/40 bg-emerald-950/25 text-emerald-200"
      : tone === "amber"
        ? "border-amber-800/40 bg-amber-950/25 text-amber-200"
        : tone === "rose"
          ? "border-rose-800/40 bg-rose-950/25 text-rose-200"
          : tone === "cyan"
            ? "border-cyan-800/40 bg-cyan-950/25 text-cyan-200"
            : "border-slate-700 bg-slate-900 text-slate-400";

  return (
    <span
      data-testid={testId}
      className={`rounded border px-1.5 py-0.5 text-[9px] font-bold uppercase ${toneClass}`}
    >
      {label}
    </span>
  );
}

function readinessTone(readiness: LegacyReplacementMapEntry["deprecationReadiness"]) {
  switch (readiness) {
    case "mapped":
      return "emerald" as const;
    case "partial_mapping":
      return "amber" as const;
    case "needs_owner_decision":
      return "amber" as const;
    case "blocked_until_component_truth":
      return "rose" as const;
    case "keep_for_history":
      return "slate" as const;
    default:
      return "slate" as const;
  }
}

function riskTone(risk: LegacyReplacementMapEntry["risk"]) {
  if (risk === "high") return "rose" as const;
  if (risk === "medium") return "amber" as const;
  return "emerald" as const;
}

function ReplacementRow({
  entry,
  highlighted,
}: {
  entry: LegacyReplacementMapEntry;
  highlighted?: boolean;
}) {
  const looksLikeComponentFirst = entry.legacyCode.includes("COMP-LETTER");

  return (
    <tr
      data-testid={`product-system-legacy-replacement-row-${entry.legacyCode}`}
      data-highlighted={highlighted ? "true" : "false"}
      className={highlighted ? "bg-purple-950/20" : undefined}
    >
      <td className="px-2 py-2 align-top font-mono text-[10px] text-slate-200">{entry.legacyCode}</td>
      <td className="px-2 py-2 align-top text-[10px] text-slate-400">
        {entry.currentUse.replace(/_/g, " ")}
        {entry.usedBy.length > 0 ? (
          <p className="mt-1 font-mono text-[9px] text-slate-500">{entry.usedBy.join(", ")}</p>
        ) : null}
      </td>
      <td className="px-2 py-2 align-top font-mono text-[10px] text-cyan-200/90">
        {entry.replacementTargetCode ?? "—"}
      </td>
      <td className="px-2 py-2 align-top text-[10px] text-slate-400">
        {entry.migrationTruthAreas.slice(0, 3).join(" · ")}
        {entry.migrationTruthAreas.length > 3 ? " · …" : ""}
      </td>
      <td className="px-2 py-2 align-top">
        <StatusChip label={legacyReplacementStatusLabel(entry.deprecationReadiness)} tone={readinessTone(entry.deprecationReadiness)} />
      </td>
      <td className="px-2 py-2 align-top">
        <StatusChip label="NO DELETE" tone="rose" />
      </td>
      <td className="px-2 py-2 align-top">
        <StatusChip label={entry.risk.toUpperCase()} tone={riskTone(entry.risk)} />
      </td>
      <td className="px-2 py-2 align-top text-[10px] text-slate-500">
        {entry.ownerNoteRo}
        {looksLikeComponentFirst ? (
          <p
            data-testid={`product-system-legacy-not-component-warning-${entry.legacyCode}`}
            className="mt-1 font-semibold text-amber-200/90"
          >
            Legacy module, not TPL-COMP component template
          </p>
        ) : null}
      </td>
    </tr>
  );
}

export function LegacyReplacementReadinessPanel({
  highlightLegacyCode,
  compact = false,
}: {
  highlightLegacyCode?: string | null;
  compact?: boolean;
}) {
  const summary = buildLegacyReplacementSummary();
  const entries = LEGACY_TO_COMPONENT_FIRST_REPLACEMENT_MAP;
  const highlighted = highlightLegacyCode
    ? normalizeHighlight(highlightLegacyCode)
    : null;

  return (
    <section
      data-testid="product-system-legacy-replacement-readiness"
      className="space-y-3 rounded-lg border border-[#1E293B] bg-[#111827] px-4 py-4"
    >
      <div>
        <div className="flex flex-wrap items-center gap-2">
          <h3 className="text-sm font-semibold text-slate-100">Legacy replacement readiness</h3>
          <StatusChip
            label="NOT READY FOR DELETE"
            tone="rose"
            testId="product-system-legacy-replacement-global-verdict"
          />
        </div>
        <p
          data-testid="product-system-legacy-replacement-subtext"
          className="mt-2 text-xs leading-relaxed text-slate-400"
        >
          Template-urile legacy sunt păstrate pentru produsul activ și istoric. Ele pot fi deprecated doar după ce
          component-first deține adevărul complet și runtime-ul este validat. Replacement path proposed · readonly
          mapping · no delete now · future deprecation candidate.
        </p>
      </div>

      <div className="grid grid-cols-2 gap-2 sm:grid-cols-4">
        <div
          data-testid="product-system-legacy-replacement-summary-mapped"
          className="rounded-md border border-[#2A3548]/55 bg-transparent px-2 py-1.5"
        >
          <p className="text-[10px] font-semibold uppercase text-slate-500">Legacy modules mapped</p>
          <p className="text-base font-bold tabular-nums text-slate-100">
            {entries.filter((e) => e.replacementTargetCode).length}/{summary.totalLegacyEntries}
          </p>
        </div>
        <div
          data-testid="product-system-legacy-replacement-summary-owner-decision"
          className="rounded-md border border-amber-800/30 bg-amber-950/10 px-2 py-1.5"
        >
          <p className="text-[10px] font-semibold uppercase text-slate-500">Need owner decision</p>
          <p className="text-base font-bold tabular-nums text-amber-200">{summary.partialCount + summary.ownerDecisionCount}</p>
        </div>
        <div
          data-testid="product-system-legacy-replacement-summary-active-root"
          className="rounded-md border border-emerald-800/30 bg-emerald-950/10 px-2 py-1.5"
        >
          <p className="text-[10px] font-semibold uppercase text-slate-500">Used by active root</p>
          <p className="text-base font-bold tabular-nums text-emerald-200">{summary.usedByActiveRootCount}</p>
        </div>
        <div
          data-testid="product-system-legacy-replacement-summary-delete-ready"
          className="rounded-md border border-rose-800/30 bg-rose-950/10 px-2 py-1.5"
        >
          <p className="text-[10px] font-semibold uppercase text-slate-500">Delete-ready now</p>
          <p
            data-testid="product-system-legacy-replacement-summary-delete-ready-count"
            className="text-base font-bold tabular-nums text-rose-200"
          >
            {summary.deletableNowCount}
          </p>
        </div>
      </div>

      {!compact ? (
        <div className="overflow-x-auto">
          <table
            data-testid="product-system-legacy-replacement-table"
            className="min-w-full border-collapse text-left"
          >
            <thead>
              <tr className="border-b border-slate-800 text-[10px] font-bold uppercase tracking-wide text-slate-500">
                <th className="px-2 py-2">Legacy template</th>
                <th className="px-2 py-2">Current use</th>
                <th className="px-2 py-2">Replacement target</th>
                <th className="px-2 py-2">Truth to migrate</th>
                <th className="px-2 py-2">Status</th>
                <th className="px-2 py-2">Delete now?</th>
                <th className="px-2 py-2">Risk</th>
                <th className="px-2 py-2">Owner note</th>
              </tr>
            </thead>
            <tbody>
              {entries.map((entry) => (
                <ReplacementRow
                  key={entry.legacyCode}
                  entry={entry}
                  highlighted={highlighted === entry.legacyCode.toUpperCase()}
                />
              ))}
            </tbody>
          </table>
        </div>
      ) : highlighted ? (
        <div className="overflow-x-auto">
          <table className="min-w-full border-collapse text-left">
            <tbody>
              <ReplacementRow entry={resolveLegacyReplacementEntry(highlighted)} highlighted />
            </tbody>
          </table>
        </div>
      ) : null}
    </section>
  );
}

function normalizeHighlight(code: string): string {
  return code.trim().toUpperCase();
}

export function ComponentFirstReplacementContextPanel() {
  return (
    <section
      data-testid="product-system-component-first-replacement-context"
      className="rounded-xl border border-cyan-900/40 bg-cyan-950/10 px-4 py-3"
    >
      <h3 className="text-sm font-semibold text-cyan-100">Ce înlocuiește component-first?</h3>
      <p className="mt-1 text-xs text-slate-400">
        Nu înlocuiește runtime acum. Este doar replacement map readonly — fără activare, fără Work Intake, fără
        Pricing.
      </p>
      <ul className="mt-3 space-y-1.5 text-xs text-slate-300">
        <li data-testid="product-system-component-first-replaces-face">FACE înlocuiește modulul legacy TPL-VOLUMETRIC-FACE_v1</li>
        <li data-testid="product-system-component-first-replaces-back">BACK înlocuiește modulul legacy TPL-VOLUMETRIC-BACK_v1</li>
        <li data-testid="product-system-component-first-replaces-return-cant">
          RETURN-CANT înlocuiește modulul legacy TPL-VOLUM-ALUMINIU_v1
        </li>
        <li data-testid="product-system-component-first-replaces-led">LED înlocuiește modulul legacy TPL-VOLUMETRIC-LED_v1</li>
        <li data-testid="product-system-component-first-replaces-finish">
          FINISH înlocuiește modulul legacy TPL-VOLUMETRIC-FINISH_v1
        </li>
        <li data-testid="product-system-component-first-replaces-mounting">
          MOUNTING înlocuiește modulul legacy TPL-METAL-PREMOUNT-STRUCTURE_v1
        </li>
      </ul>
    </section>
  );
}
