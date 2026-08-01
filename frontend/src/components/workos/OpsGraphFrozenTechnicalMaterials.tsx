/**
 * Ops-graph order/plan-level frozen technical materials (read-only).
 *
 * Semantic: technical requirements from frozen Order snapshot — NOT stock,
 * reservation, allocation, preparation, or consumption. Quantity null →
 * "Nespecificată" (never coerce to 0).
 */

import { useState } from "react";
import type { FrozenTechnicalMaterialsProjection } from "@/api/execution";

export function formatFrozenMaterialQuantity(
  quantity: number | null | undefined,
  quantityStatus?: string | null,
  statusLabelRo?: string | null,
): string {
  if (quantity !== null && quantity !== undefined) {
    return String(quantity);
  }
  const label = statusLabelRo?.trim();
  if (label) {
    return label;
  }
  switch ((quantityStatus || "").trim()) {
    case "reference_only":
      return "Referință (fără cantitate)";
    case "source_missing":
      return "Sursă lipsă";
    case "legacy_unspecified":
    default:
      return "Nespecificată";
  }
}

type Props = {
  projection: FrozenTechnicalMaterialsProjection | null | undefined;
};

export default function OpsGraphFrozenTechnicalMaterials({ projection }: Props) {
  const [open, setOpen] = useState(false);

  if (!projection) {
    return null;
  }

  const entries = projection.entries ?? [];
  const count = projection.entry_count ?? entries.length;
  const title = projection.title?.trim() || "Materiale tehnice conform comenzii";
  const note =
    projection.semantic_note?.trim() ||
    "Lista provine din definiția tehnică înghețată a comenzii. Nu reprezintă stoc, rezervare sau consum.";
  const status = projection.status ?? "unknown";
  const isEmpty =
    status === "materials_empty" ||
    status === "materials_absent" ||
    status === "snapshot_missing" ||
    status === "snapshot_invalid" ||
    count === 0;

  return (
    <section
      className="rounded-lg border border-wo-border-strong bg-wo-surface-raised"
      data-testid="ops-graph-frozen-technical-materials"
      aria-label={title}
    >
      <div className="px-3 py-2.5 space-y-1.5">
        <div className="flex flex-wrap items-center justify-between gap-2">
          <div className="min-w-0">
            <h2
              className="text-[12px] font-semibold text-wo-text-primary"
              data-testid="ops-graph-frozen-materials-title"
            >
              {title}
            </h2>
            <p
              className="text-[10px] text-wo-text-muted mt-0.5 max-w-3xl"
              data-testid="ops-graph-frozen-materials-note"
            >
              {note}
            </p>
          </div>
          <div className="flex items-center gap-2 shrink-0">
            <span
              className="text-[10px] font-mono text-wo-text-secondary border border-wo-border-subtle rounded px-1.5 py-0.5 bg-wo-surface-inset"
              data-testid="ops-graph-frozen-materials-count"
            >
              {count} {count === 1 ? "intrare" : "intrări"}
            </span>
            {!isEmpty && (
              <button
                type="button"
                className="px-2.5 py-1 text-[11px] font-semibold rounded border border-wo-border-strong bg-wo-surface-inset text-wo-text-primary hover:bg-wo-hover"
                data-testid="ops-graph-frozen-materials-toggle"
                aria-expanded={open}
                onClick={() => setOpen((v) => !v)}
              >
                {open ? "Ascunde lista" : "Arată lista"}
              </button>
            )}
          </div>
        </div>

        {isEmpty && (
          <p
            className="text-[11px] text-wo-text-muted"
            data-testid="ops-graph-frozen-materials-empty"
          >
            {status === "snapshot_missing" || status === "snapshot_invalid"
              ? "Snapshot tehnic al comenzii indisponibil — lista materialelor nu poate fi afișată."
              : "Nicio cerință tehnică de material înregistrată în snapshotul înghețat al comenzii."}
          </p>
        )}
      </div>

      {open && !isEmpty && (
        <div
          className="border-t border-wo-border-subtle overflow-x-auto"
          data-testid="ops-graph-frozen-materials-list"
        >
          <table className="w-full text-[11px]">
            <thead className="bg-wo-surface-inset border-b border-wo-border-strong">
              <tr className="text-left text-wo-text-muted uppercase text-[9px] tracking-wide">
                <th className="px-3 py-1.5 font-semibold">Cod</th>
                <th className="px-3 py-1.5 font-semibold">Denumire</th>
                <th className="px-3 py-1.5 font-semibold">Unitate</th>
                <th className="px-3 py-1.5 font-semibold">Cantitate</th>
                <th className="px-3 py-1.5 font-semibold">Proveniență</th>
              </tr>
            </thead>
            <tbody>
              {entries.map((entry) => {
                const qtyLabel = formatFrozenMaterialQuantity(
                  entry.quantity,
                  entry.quantity_status,
                  entry.quantity_status_label_ro,
                );
                const provenanceBits = [
                  entry.provenance,
                  entry.component_ref,
                  entry.variant_discriminator,
                ].filter(Boolean);
                return (
                  <tr
                    key={`ftm-${entry.entry_index}-${entry.requirement_id ?? entry.material_code ?? "x"}`}
                    className="border-b border-wo-border-subtle last:border-b-0 align-top"
                    data-testid={`ops-graph-frozen-material-row-${entry.entry_index}`}
                    data-quantity-status={entry.quantity_status ?? "legacy_unspecified"}
                  >
                    <td className="px-3 py-1.5 font-mono text-wo-text-secondary whitespace-nowrap">
                      {entry.material_code?.trim() || "—"}
                    </td>
                    <td className="px-3 py-1.5 text-wo-text-primary">
                      {entry.label?.trim() || "—"}
                    </td>
                    <td className="px-3 py-1.5 font-mono text-wo-text-muted">
                      {entry.unit?.trim() || "—"}
                    </td>
                    <td
                      className="px-3 py-1.5 text-wo-text-secondary"
                      data-testid={`ops-graph-frozen-material-qty-${entry.entry_index}`}
                      data-quantity-null={
                        entry.quantity === null || entry.quantity === undefined
                          ? "true"
                          : "false"
                      }
                      data-quantity-status={entry.quantity_status ?? "legacy_unspecified"}
                    >
                      {qtyLabel}
                    </td>
                    <td className="px-3 py-1.5 text-[10px] font-mono text-wo-text-dim">
                      {provenanceBits.length > 0 ? provenanceBits.join(" · ") : "—"}
                    </td>
                  </tr>
                );
              })}
            </tbody>
          </table>
        </div>
      )}
    </section>
  );
}
