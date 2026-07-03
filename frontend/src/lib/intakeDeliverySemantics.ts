/**
 * Canonical delivery / install / terrain semantics for Work Intake (display + gating).
 * Readiness policy in intakeReadiness.ts is unchanged — callers pass requiresInstallAudit
 * derived from requiresTerrainAudit() here.
 */

import { isUnresolvedIntakeProductFamily } from "@/lib/intakeProductFamilyDisplay";
import type { IntakeSiteAuditJson } from "@/lib/intakeSiteAudit";
import { parseSiteAuditJson } from "@/lib/intakeSiteAudit";
import {
  deliveryTypeLabels,
  type DeliveryType,
} from "@/lib/mockData";

const CANONICAL_DELIVERY_TYPES: DeliveryType[] = [
  "pickup",
  "delivery_standard",
  "delivery_express",
  "delivery_install",
  "courier",
];

export const DELIVERY_UNSET_LABEL = "Livrare nealeasă";

export const STAGE0_INSTALL_NEUTRAL_NOTE =
  "Montajul va fi verificat după alegerea tipului lucrării.";

export const TERRAIN_DATA_PRESERVED_NOTE =
  "Datele de teren existente sunt păstrate, dar nu sunt necesare pentru acest tip de livrare.";

export const TERRAIN_NA_COMPACT_LABEL =
  "Teren: N/A pentru livrare fără montaj";

export const TERRAIN_AUDIT_MISSING_LABEL = "Audit teren — incomplet";

/** Quick Start + detail + side panel — same value keys as DeliveryType. */
export const INTAKE_DELIVERY_OPTIONS: { value: DeliveryType; label: string }[] =
  CANONICAL_DELIVERY_TYPES.map((value) => ({
    value,
    label: deliveryTypeLabels[value],
  }));

export function normalizeDeliveryType(
  value: string | null | undefined
): DeliveryType | null {
  const trimmed = (value ?? "").trim();
  if (!trimmed) return null;
  return CANONICAL_DELIVERY_TYPES.includes(trimmed as DeliveryType)
    ? (trimmed as DeliveryType)
    : null;
}

export function getDeliveryLabel(value: string | null | undefined): string {
  const normalized = normalizeDeliveryType(value);
  if (!normalized) return DELIVERY_UNSET_LABEL;
  return deliveryTypeLabels[normalized];
}

export function isDeliveryUnset(value: string | null | undefined): boolean {
  return normalizeDeliveryType(value) === null;
}

export function isDeliveryPickup(value: string | null | undefined): boolean {
  return normalizeDeliveryType(value) === "pickup";
}

export function isDeliveryCourier(value: string | null | undefined): boolean {
  return normalizeDeliveryType(value) === "courier";
}

export function isDeliveryStandardDelivery(
  value: string | null | undefined
): boolean {
  const n = normalizeDeliveryType(value);
  return n === "delivery_standard" || n === "delivery_express";
}

export function isDeliveryWithInstall(value: string | null | undefined): boolean {
  return normalizeDeliveryType(value) === "delivery_install";
}

export function isDeliveryNoInstall(value: string | null | undefined): boolean {
  return !isDeliveryWithInstall(value);
}

export interface IntakeDeliveryTerrainInput {
  deliveryType: string | null | undefined;
  productFamily?: string | null | undefined;
}

/**
 * Terrain/site audit is required only when work type is known and delivery includes install.
 */
export function requiresTerrainAudit(input: IntakeDeliveryTerrainInput): boolean {
  if (isUnresolvedIntakeProductFamily(input.productFamily)) {
    return false;
  }
  return isDeliveryWithInstall(input.deliveryType);
}

export function hasPersistedSiteAuditData(
  siteAudit: IntakeSiteAuditJson | null | undefined
): boolean {
  const audit = parseSiteAuditJson(siteAudit);
  return (
    audit.checks.address_confirmed ||
    audit.checks.photos_verified ||
    audit.checks.power_confirmed ||
    (audit.mounting_address ?? "").trim().length > 0
  );
}

export interface IntakeDeliveryStageContext extends IntakeDeliveryTerrainInput {
  siteAudit?: IntakeSiteAuditJson | null;
}

/** Contextual notes for delivery selector / side panel (no blockers). */
export function getDeliveryStageNote(
  ctx: IntakeDeliveryStageContext
): string | null {
  if (isUnresolvedIntakeProductFamily(ctx.productFamily)) {
    if (isDeliveryWithInstall(ctx.deliveryType)) {
      return STAGE0_INSTALL_NEUTRAL_NOTE;
    }
    return null;
  }
  if (
    isDeliveryNoInstall(ctx.deliveryType) &&
    hasPersistedSiteAuditData(ctx.siteAudit)
  ) {
    return TERRAIN_DATA_PRESERVED_NOTE;
  }
  if (
    isDeliveryWithInstall(ctx.deliveryType) &&
    !isUnresolvedIntakeProductFamily(ctx.productFamily)
  ) {
    return null;
  }
  return null;
}

/** Display-only filter — readiness evaluation unchanged. */
export function filterReadinessMissingForDisplay(
  missing: string[],
  requiresTerrain: boolean
): string[] {
  if (requiresTerrain) return missing;
  return missing.filter(
    (item) => !item.toLowerCase().includes("audit teren")
  );
}

export function terrainProgressLabel(
  siteAudit: IntakeSiteAuditJson | null | undefined,
  requiresTerrain: boolean
): { label: string; ok: boolean | null } {
  if (!requiresTerrain) {
    return { label: "N/A (fără montaj)", ok: null };
  }
  const audit = parseSiteAuditJson(siteAudit);
  const checks = [
    audit.checks.address_confirmed,
    audit.checks.photos_verified,
    audit.checks.power_confirmed,
  ];
  const completed = checks.filter(Boolean).length;
  return {
    label: `${completed}/3`,
    ok: completed === 3,
  };
}
