/**
 * Display-only helpers for inventory material registry status in ProductSystem.
 * Uses fields present on API rows; InventoryMaterialEntity may omit optional keys at compile time.
 */

import type { InventoryMaterialEntity } from "@/lib/api";

/** Optional registry fields returned by inventory_materials list API. */
export type MaterialRegistryRow = InventoryMaterialEntity & {
  status?: string | null;
  unit_cost?: number | null;
  currency?: string | null;
  vat_percent?: number | null;
  valid_from?: string | null;
  source_name?: string | null;
  source_notes?: string | null;
  source_review_status?: string | null;
  subcategory?: string | null;
};

export type MaterialRegistryBadge = {
  key: string;
  label: string;
  className: string;
  title?: string;
};

const BADGE =
  "px-1.5 py-0.5 text-[8px] font-semibold rounded border whitespace-nowrap";

function asRegistryRow(material: InventoryMaterialEntity): MaterialRegistryRow {
  return material as MaterialRegistryRow;
}

function normStatus(status: string | null | undefined): string {
  return (status ?? "").trim().toLowerCase();
}

function normReview(status: string | null | undefined): string {
  return (status ?? "").trim().toLowerCase();
}

export function isUnitCostUnset(unitCost: number | null | undefined): boolean {
  return unitCost === null || unitCost === undefined;
}

/** Mirrors pricing registry “complete” checks; display-only, not used for save/quote. */
export function isCommercialPricingComplete(material: MaterialRegistryRow): boolean {
  if (isUnitCostUnset(material.unit_cost)) return false;
  if ((material.unit_cost as number) <= 0) return false;
  if (!(material.currency ?? "").trim()) return false;
  if (material.vat_percent === null || material.vat_percent === undefined) return false;
  if (!material.valid_from) return false;
  return true;
}

export function hasMaterialSourceNotes(material: InventoryMaterialEntity): boolean {
  const notes = asRegistryRow(material).source_notes;
  return typeof notes === "string" && notes.trim().length > 0;
}

export function formatMaterialSourceNotes(material: InventoryMaterialEntity): string | null {
  const notes = asRegistryRow(material).source_notes;
  if (typeof notes !== "string") return null;
  const trimmed = notes.trim();
  return trimmed.length > 0 ? trimmed : null;
}

export function getMaterialRegistryUnknownLabel(): string {
  return "Necunoscut în registru";
}

export function getMaterialRegistryStatusBadges(
  material: InventoryMaterialEntity
): MaterialRegistryBadge[] {
  const row = asRegistryRow(material);
  const badges: MaterialRegistryBadge[] = [];
  const status = normStatus(row.status);
  const review = normReview(row.source_review_status);
  const unitUnset = isUnitCostUnset(row.unit_cost);

  badges.push({
    key: "in-registry",
    label: "În registru",
    className: `${BADGE} bg-emerald-900/25 text-emerald-300 border-emerald-700/40`,
    title: "Cod găsit în registrul de materiale încărcat",
  });

  if (unitUnset || status === "missing_price") {
    badges.push({
      key: "no-price",
      label: "Fără preț",
      className: `${BADGE} bg-amber-900/25 text-amber-300 border-amber-700/40`,
      title: "unit_cost lipsă sau status missing_price",
    });
  }

  if (status === "needs_owner_input") {
    badges.push({
      key: "needs-owner",
      label: "Necesită owner",
      className: `${BADGE} bg-orange-900/25 text-orange-300 border-orange-700/40`,
      title: "Status registru: needs_owner_input",
    });
  }

  if (status === "active") {
    if (isCommercialPricingComplete(row)) {
      badges.push({
        key: "commercial-active",
        label: "Preț activ",
        className: `${BADGE} bg-cyan-900/25 text-cyan-300 border-cyan-700/40`,
        title: "status=active și câmpuri de preț comercial complete",
      });
    } else {
      badges.push({
        key: "price-inactive",
        label: "Preț neactivat",
        className: `${BADGE} bg-slate-800/50 text-slate-400 border-slate-600/50`,
        title: "status=active dar prețul comercial nu este complet",
      });
    }
  } else if (status && status !== "missing_price" && status !== "needs_owner_input") {
    if (status === "archived") {
      badges.push({
        key: "archived",
        label: "Arhivat",
        className: `${BADGE} bg-slate-800/50 text-slate-500 border-slate-600/50`,
      });
    } else if (!unitUnset) {
      badges.push({
        key: "price-inactive",
        label: "Preț neactivat",
        className: `${BADGE} bg-slate-800/50 text-slate-400 border-slate-600/50`,
        title: `Status registru: ${status}`,
      });
    }
  } else if (!unitUnset && status !== "active") {
    badges.push({
      key: "price-inactive",
      label: "Preț neactivat",
      className: `${BADGE} bg-slate-800/50 text-slate-400 border-slate-600/50`,
      title: "Material în registru, dar status nu este active",
    });
  }

  if (review === "reviewed" || review === "accepted_override") {
    badges.push({
      key: "owner-confirmed",
      label: "Owner-confirmed",
      className: `${BADGE} bg-violet-900/25 text-violet-300 border-violet-700/40`,
      title: `source_review_status: ${row.source_review_status}`,
    });
  } else if (review === "needs_review") {
    badges.push({
      key: "review-needed",
      label: "Revizuire sursă",
      className: `${BADGE} bg-amber-900/25 text-amber-300 border-amber-700/40`,
    });
  } else if (review === "missing") {
    badges.push({
      key: "source-missing",
      label: "Sursă lipsă",
      className: `${BADGE} bg-red-900/20 text-red-300 border-red-800/40`,
    });
  } else if (review === "stale") {
    badges.push({
      key: "source-stale",
      label: "Sursă învechită",
      className: `${BADGE} bg-orange-900/25 text-orange-300 border-orange-700/40`,
    });
  }

  const sourceName = (row.source_name ?? "").trim();
  if (sourceName) {
    badges.push({
      key: "source-name",
      label: `Sursă: ${sourceName}`,
      className: `${BADGE} bg-slate-800/40 text-slate-300 border-slate-600/50 max-w-[140px] truncate`,
      title: sourceName,
    });
  }

  if (hasMaterialSourceNotes(material)) {
    badges.push({
      key: "source-notes",
      label: "Note sursă disponibile",
      className: `${BADGE} bg-slate-800/40 text-slate-400 border-slate-600/50`,
      title: "Referință / guvernanță — nu este alias runtime",
    });
  }

  return badges;
}

/** Short, readable name for material pickers (drops operational suffix noise). */
export function formatMaterialRegistryShortName(name: string): string {
  let s = (name ?? "").trim();
  if (!s) return "—";
  const paren = s.indexOf(" (");
  if (paren > 0) s = s.slice(0, paren);
  const cod = s.indexOf(" — cod ");
  if (cod > 0) s = s.slice(0, cod);
  if (s.length > 72) s = `${s.slice(0, 69)}…`;
  return s;
}

export const VOLUMETRIC_COMPONENT_MATERIAL_HINTS: Record<string, string[]> = {
  comp_face_litere: ["MAT-ACP-FATA", "MAT-PLEXI", "MAT-VINYL"],
  comp_lateral_litere: ["MAT-PROFIL-LATERAL", "MAT-PROFIL"],
  comp_spate_litere: ["MAT-SPATE", "MAT-FOREX"],
  comp_led_litere: ["MAT-LED"],
  comp_finisaj_litere: ["MAT-VOPSEA", "MAT-SABLON"],
};

function materialMatchesHint(code: string, hints: string[]): boolean {
  const upper = code.toUpperCase();
  return hints.some((h) => upper.startsWith(h.toUpperCase()));
}

/** Puts component-relevant materials first in volumetric letter templates. */
export function sortMaterialsForPicker(
  materials: InventoryMaterialEntity[],
  componentId: string | undefined,
  templateCode: string | null | undefined
): InventoryMaterialEntity[] {
  const { suggested, other } = splitMaterialsForPickerGroups(
    materials,
    componentId,
    templateCode
  );
  return [...suggested, ...other];
}

export function splitMaterialsForPickerGroups(
  materials: InventoryMaterialEntity[],
  componentId: string | undefined,
  templateCode: string | null | undefined
): { suggested: InventoryMaterialEntity[]; other: InventoryMaterialEntity[] } {
  const sorted = [...materials].sort((a, b) => a.code.localeCompare(b.code));
  const code = (templateCode ?? "").trim().toUpperCase();
  if (code !== "TPL-VOLUMETRIC-LETTERS" || !componentId) {
    return { suggested: [], other: sorted };
  }
  const hints = VOLUMETRIC_COMPONENT_MATERIAL_HINTS[componentId] ?? [];
  if (hints.length === 0) {
    return { suggested: [], other: sorted };
  }
  const suggested: InventoryMaterialEntity[] = [];
  const other: InventoryMaterialEntity[] = [];
  for (const m of sorted) {
    if (materialMatchesHint(m.code, hints)) suggested.push(m);
    else other.push(m);
  }
  return { suggested, other };
}
