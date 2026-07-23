import {
  buildFaceReadinessSummary,
  FACE_COMPONENT_TEMPLATE_CODE,
  FACE_CUT_PROCESS_DECISIONS,
  FACE_DOES_NOT_OWN,
  FACE_DOES_NOT_OWN_CONFIRMED,
  FACE_DOWNSTREAM_OUTPUTS,
  FACE_FORBIDDEN_OWNERSHIP,
  FACE_MATERIAL_FAMILY_DECISIONS,
  FACE_NESTING_BASIS_RULE,
  FACE_OWNER_TRUTH_FIELDS,
  FACE_READINESS_BLOCKERS,
  FACE_THICKNESS_DECISIONS,
  FACE_TRUTH_WORKSHOP_FIELDS,
  FACE_WORKSHOP_STATUS,
  type FaceTruthField,
  type FaceWorkshopFieldStatus,
} from "./candidateModuleProdusFaceTruthWorkshop";
import { CANONICAL_FINISH_RETIRED_PATHS } from "./canonicalFinishEnumMap";
import { FaceEstimatedPriceDraftPanel } from "./FaceEstimatedPriceDraftPanel";

function StatusChip({
  label,
  tone,
  testId,
}: {
  label: string;
  tone: "emerald" | "amber" | "rose" | "slate" | "cyan" | "violet";
  testId?: string;
}) {
  const toneClass =
    tone === "emerald"
      ? "border-emerald-800/40 bg-emerald-950/25 text-emerald-200"
      : tone === "cyan"
        ? "border-cyan-800/40 bg-cyan-950/25 text-cyan-200"
        : tone === "violet"
          ? "border-violet-800/40 bg-violet-950/25 text-violet-200"
          : tone === "amber"
            ? "border-amber-800/40 bg-amber-950/25 text-amber-200"
            : tone === "rose"
              ? "border-rose-800/40 bg-rose-950/25 text-rose-200"
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

function fieldStatusTone(status: FaceWorkshopFieldStatus) {
  if (status === "owner_confirmed") return "emerald" as const;
  if (status === "partial_confirmed") return "cyan" as const;
  if (status === "owner_input_required") return "amber" as const;
  if (status === "blocked_until_owner_decision") return "rose" as const;
  return "slate" as const;
}

function fieldStatusLabel(status: FaceWorkshopFieldStatus) {
  if (status === "owner_confirmed") return "OWNER CONFIRMED";
  if (status === "partial_confirmed") return "PARTIAL CONFIRMED";
  if (status === "owner_input_required") return "OWNER INPUT REQUIRED";
  if (status === "blocked_until_owner_decision") return "BLOCKED";
  if (status === "evidence_only") return "EVIDENCE ONLY";
  return status;
}

function TruthFieldRow({ field }: { field: FaceTruthField }) {
  return (
    <tr data-testid={`product-system-face-truth-field-${field.fieldKey}`}>
      <td className="px-2 py-2 align-top font-mono text-[10px] text-slate-200">{field.fieldKey}</td>
      <td className="px-2 py-2 align-top text-[10px] text-slate-300">{field.labelRo}</td>
      <td className="px-2 py-2 align-top">
        <StatusChip label={fieldStatusLabel(field.status)} tone={fieldStatusTone(field.status)} />
      </td>
      <td
        data-testid={`product-system-face-truth-value-${field.fieldKey}`}
        className="px-2 py-2 align-top text-[10px] font-semibold text-slate-200"
      >
        {field.value ?? "OWNER INPUT REQUIRED"}
      </td>
      <td className="px-2 py-2 align-top font-mono text-[9px] text-cyan-200/80">
        {field.truthPathPrefix ?? "—"}
      </td>
      <td className="px-2 py-2 align-top text-[10px] text-slate-400">{field.notesRo}</td>
    </tr>
  );
}

export function FaceTruthWorkshopPanel() {
  const summary = buildFaceReadinessSummary();

  return (
    <section
      data-testid="product-system-face-truth-workshop"
      className="space-y-4 rounded-xl border border-sky-900/40 bg-sky-950/10 px-4 py-4"
    >
      <div>
        <div className="flex flex-wrap items-center gap-2">
          <h4 className="text-sm font-semibold text-sky-100">FACE Component Truth Workshop</h4>
          <StatusChip label="READONLY" tone="slate" testId="product-system-face-truth-readonly-badge" />
          <StatusChip
            label="NOT READY FOR PRICING"
            tone="amber"
            testId="product-system-face-truth-not-ready-pricing-badge"
          />
        </div>
        <p className="mt-1 text-[10px] text-slate-500">
          {FACE_COMPONENT_TEMPLATE_CODE} · workshop status: {FACE_WORKSHOP_STATUS.replace(/_/g, " ")}
        </p>
      </div>

      <div
        data-testid="product-system-face-truth-guard-badges"
        className="flex flex-wrap gap-2"
      >
        <StatusChip
          label="Product Truth write blocked"
          tone="rose"
          testId="product-system-face-truth-product-truth-blocked"
        />
        <StatusChip
          label="FINISH workshop — separate slice"
          tone="violet"
          testId="product-system-face-truth-finish-depends-badge"
        />
        <StatusChip
          label="Owner decisions applied"
          tone="emerald"
          testId="product-system-face-truth-owner-decisions-badge"
        />
        {FACE_DOES_NOT_OWN_CONFIRMED ? (
          <StatusChip
            label="Does-not-own confirmed"
            tone="emerald"
            testId="product-system-face-truth-does-not-own-confirmed"
          />
        ) : null}
      </div>

      <div
        data-testid="product-system-face-truth-safety-copy"
        className="rounded-lg border border-slate-800/80 bg-slate-950/50 px-3 py-2 text-[10px] text-slate-400"
      >
        <p>No Product Truth live write</p>
        <p>No Pricing activation</p>
        <p>No Work Intake exposure</p>
        <p>No Save / Apply / Activate / Promote / Create quote</p>
        <p data-testid="product-system-face-truth-ready-for-pricing">Ready for pricing: NO</p>
      </div>

      <div className="grid gap-3 lg:grid-cols-2">
        <article
          data-testid="product-system-face-truth-owns"
          className="rounded-lg border border-emerald-900/30 bg-emerald-950/10 px-3 py-3"
        >
          <p className="text-[11px] font-bold uppercase text-emerald-200">FACE owns</p>
          <ul className="mt-2 space-y-1 text-[10px] text-slate-300">
            {FACE_OWNER_TRUTH_FIELDS.map((item) => (
              <li key={item}>• {item}</li>
            ))}
          </ul>
        </article>

        <article
          data-testid="product-system-face-truth-does-not-own"
          className="rounded-lg border border-rose-900/30 bg-rose-950/10 px-3 py-3"
        >
          <p className="text-[11px] font-bold uppercase text-rose-200">FACE does not own</p>
          <ul className="mt-2 space-y-1 text-[10px] text-slate-300">
            {FACE_DOES_NOT_OWN.map((item) => (
              <li key={item}>• {item}</li>
            ))}
          </ul>
        </article>
      </div>

      <article
        data-testid="product-system-face-truth-geometry-source"
        className="rounded-lg border border-cyan-900/30 bg-cyan-950/10 px-3 py-3"
      >
        <p className="text-[11px] font-bold uppercase text-cyan-200">Geometry / source</p>
        <p
          data-testid="product-system-face-truth-vector-litere"
          className="mt-2 text-[10px] font-semibold text-slate-200"
        >
          Vector Litere — layer role sursă față (nu Vector Logo)
        </p>
        <p className="mt-1 text-[10px] text-slate-400">
          SVG layer / vector contour din Intake V6. Handoff path exact pending — fără runtime bridge.
        </p>
        <p
          data-testid="product-system-face-truth-nesting-basis"
          className="mt-2 text-[10px] font-semibold text-cyan-200/90"
        >
          Nesting basis: {FACE_NESTING_BASIS_RULE}
        </p>
      </article>

      <article
        data-testid="product-system-face-truth-downstream-outputs"
        className="rounded-lg border border-violet-900/30 bg-violet-950/10 px-3 py-3"
      >
        <p className="text-[11px] font-bold uppercase text-violet-200">Downstream outputs</p>
        <div className="mt-2 space-y-2">
          {FACE_DOWNSTREAM_OUTPUTS.map((output) => (
            <div
              key={output.outputKey}
              data-testid={`product-system-face-truth-downstream-${output.outputKey}`}
              className="rounded border border-slate-800/60 bg-slate-950/30 px-2.5 py-2 text-[10px]"
            >
              <p className="font-semibold text-slate-200">{output.labelRo}</p>
              <p className="mt-0.5 text-slate-400">
                Consumer: {output.consumerComponent} · basis: {output.quantityBasis}
              </p>
              <p className="mt-0.5 text-slate-500">{output.notesRo}</p>
            </div>
          ))}
        </div>
        <p
          data-testid="product-system-face-truth-return-cant-perimeter"
          className="mt-2 text-[10px] text-amber-200/90"
        >
          RETURN-CANT consumes face perimeter / contour length for cant length.
        </p>
        <p
          data-testid="product-system-face-truth-finish-face-area"
          className="mt-1 text-[10px] text-amber-200/90"
        >
          FINISH consumes mp_face_area for face vinyl and print/laminate quantity basis.
        </p>
      </article>

      <article
        data-testid="product-system-face-truth-material-thickness"
        className="rounded-lg border border-amber-900/30 bg-amber-950/10 px-3 py-3"
      >
        <p className="text-[11px] font-bold uppercase text-amber-200">Material / thickness — owner confirmed</p>
        <div className="mt-2 space-y-2">
          {FACE_MATERIAL_FAMILY_DECISIONS.map((material) => (
            <div
              key={material.materialFamily}
              data-testid={`product-system-face-truth-material-${material.materialFamily.replace(/\s+/g, "-").toLowerCase()}`}
              className="rounded border border-slate-800/60 bg-slate-950/30 px-2.5 py-2 text-[10px]"
            >
              <div className="flex flex-wrap items-center gap-2">
                <span className="font-semibold text-slate-200">{material.materialFamily}</span>
                <StatusChip
                  label={material.allowedForFaceStandard ? "FACE YES" : "FACE NO"}
                  tone={material.allowedForFaceStandard ? "emerald" : "slate"}
                />
                <StatusChip label={material.status.replace(/_/g, " ").toUpperCase()} tone="emerald" />
              </div>
              <p className="mt-0.5 text-slate-500">{material.notesRo}</p>
            </div>
          ))}
        </div>
        <div className="mt-3" data-testid="product-system-face-truth-thickness-decisions">
          <p className="text-[10px] font-bold text-slate-400">Thickness decisions</p>
          <ul className="mt-1 space-y-1 text-[10px] text-slate-300">
            {FACE_THICKNESS_DECISIONS.map((entry) => (
              <li key={entry.materialFamily}>
                • {entry.materialFamily}: default {entry.defaultThicknessMm ?? "—"} mm
                {entry.optionalThicknessesMm.length > 0
                  ? ` · optional ${entry.optionalThicknessesMm.join("/")} mm`
                  : ""}
              </li>
            ))}
          </ul>
        </div>
        <div className="mt-3" data-testid="product-system-face-truth-cut-process-matrix">
          <p className="text-[10px] font-bold text-slate-400">Cut process matrix</p>
          <ul className="mt-1 space-y-1 text-[10px] text-slate-300">
            {FACE_CUT_PROCESS_DECISIONS.map((entry) => (
              <li key={`${entry.materialFamily}-${entry.thicknessMm}`}>
                • {entry.materialFamily} {entry.thicknessMm} mm → {entry.process} ({fieldStatusLabel(entry.status)})
              </li>
            ))}
          </ul>
        </div>
      </article>

      <FaceEstimatedPriceDraftPanel />

      <div className="overflow-x-auto">
        <table
          data-testid="product-system-face-truth-fields-table"
          className="min-w-full border-collapse text-left"
        >
          <thead>
            <tr className="border-b border-slate-800 text-[10px] font-bold uppercase tracking-wide text-slate-500">
              <th className="px-2 py-2">Field</th>
              <th className="px-2 py-2">Label</th>
              <th className="px-2 py-2">Status</th>
              <th className="px-2 py-2">Value</th>
              <th className="px-2 py-2">Truth path</th>
              <th className="px-2 py-2">Notes</th>
            </tr>
          </thead>
          <tbody>
            {FACE_TRUTH_WORKSHOP_FIELDS.map((field) => (
              <TruthFieldRow key={field.fieldKey} field={field} />
            ))}
          </tbody>
        </table>
      </div>

      <article
        data-testid="product-system-face-truth-retired-finish-paths"
        className="rounded-lg border border-slate-800/80 bg-slate-950/40 px-3 py-3"
      >
        <p className="text-[11px] font-bold uppercase text-slate-200">Generic FINISH paths — retired conceptual</p>
        <ul className="mt-2 space-y-1 text-[10px] text-slate-400">
          {CANONICAL_FINISH_RETIRED_PATHS.map((entry) => (
            <li key={entry.retiredPath}>
              <span className="font-mono text-rose-200/80">{entry.retiredPath}</span>
              {" → "}
              {entry.replacementPaths.join(" · ")}
            </li>
          ))}
        </ul>
      </article>

      <article
        data-testid="product-system-face-truth-forbidden-ownership"
        className="rounded-lg border border-slate-800/80 bg-slate-950/40 px-3 py-3"
      >
        <p className="text-[11px] font-bold uppercase text-slate-200">Forbidden ownership</p>
        <ul className="mt-2 space-y-1 text-[10px] text-slate-400">
          {FACE_FORBIDDEN_OWNERSHIP.map((item) => (
            <li key={item}>• {item}</li>
          ))}
        </ul>
      </article>

      <article
        data-testid="product-system-face-truth-readiness-blockers"
        className="rounded-lg border border-rose-900/30 bg-rose-950/10 px-3 py-3"
      >
        <p className="text-[11px] font-bold uppercase text-rose-200">Readiness blockers</p>
        <p
          data-testid="product-system-face-truth-readiness-blocker-count"
          className="mt-1 text-[10px] text-slate-500"
        >
          {summary.readinessBlockerCount} blockers · FINISH blocked entries: {summary.blockedFinishEntryCount}
        </p>
        <ul className="mt-2 space-y-1 text-[10px] text-slate-300">
          {FACE_READINESS_BLOCKERS.map((blocker) => (
            <li key={blocker}>• {blocker}</li>
          ))}
        </ul>
      </article>
    </section>
  );
}
