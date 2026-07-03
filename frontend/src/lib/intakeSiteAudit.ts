/**
 * intake_requests.site_audit_json — site/terrain capture (not CostEngine input).
 */

export type LocationPhotosStatus =
  | "missing"
  | "received"
  | "verified"
  | "needs_clarification";

export type PowerAvailable = "unknown" | "yes" | "no";
export type MountingAccess = "unknown" | "ok" | "limited" | "blocked";
export type CableRoute = "unknown" | "ok" | "needs_review";

export interface IntakeSiteAuditChecks {
  address_confirmed: boolean;
  photos_verified: boolean;
  power_confirmed: boolean;
  access_confirmed: boolean;
}

export interface IntakeSiteAuditJson {
  mounting_address: string;
  location_photos_status: LocationPhotosStatus;
  power_available: PowerAvailable;
  mounting_access: MountingAccess;
  cable_route: CableRoute;
  notes: string;
  checks: IntakeSiteAuditChecks;
}

export const EMPTY_SITE_AUDIT: IntakeSiteAuditJson = {
  mounting_address: "",
  location_photos_status: "missing",
  power_available: "unknown",
  mounting_access: "unknown",
  cable_route: "unknown",
  notes: "",
  checks: {
    address_confirmed: false,
    photos_verified: false,
    power_confirmed: false,
    access_confirmed: false,
  },
};

/** UI audit state shape used by IntakeDetail AuditTerenSection. */
export interface IntakeAuditUiState {
  address: string;
  addressSelected: boolean;
  mapsOpened: boolean;
  addressConfirmed: boolean;
  photosStatus: "none" | "link_sent" | "received";
  photoLink: string;
  techPowerSource: string;
  surfaceType: string;
  foundationResponsibility: string;
  foundationClientConfirmed: boolean;
  existingFoundationDims: string;
  heavyEquipmentAccess: string;
}

export function parseSiteAuditJson(
  raw: IntakeSiteAuditJson | string | null | undefined
): IntakeSiteAuditJson {
  if (!raw) return { ...EMPTY_SITE_AUDIT, checks: { ...EMPTY_SITE_AUDIT.checks } };
  let obj: Record<string, unknown>;
  if (typeof raw === "string") {
    try {
      obj = JSON.parse(raw) as Record<string, unknown>;
    } catch {
      return { ...EMPTY_SITE_AUDIT, checks: { ...EMPTY_SITE_AUDIT.checks } };
    }
  } else {
    obj = raw as unknown as Record<string, unknown>;
  }
  const checksRaw = (obj.checks ?? {}) as Record<string, unknown>;
  return {
    mounting_address: String(obj.mounting_address ?? ""),
    location_photos_status: (obj.location_photos_status as LocationPhotosStatus) ?? "missing",
    power_available: (obj.power_available as PowerAvailable) ?? "unknown",
    mounting_access: (obj.mounting_access as MountingAccess) ?? "unknown",
    cable_route: (obj.cable_route as CableRoute) ?? "unknown",
    notes: String(obj.notes ?? ""),
    checks: {
      address_confirmed: Boolean(checksRaw.address_confirmed),
      photos_verified: Boolean(checksRaw.photos_verified),
      power_confirmed: Boolean(checksRaw.power_confirmed),
      access_confirmed: Boolean(checksRaw.access_confirmed),
    },
  };
}

function mapPhotosStatusToUi(
  status: LocationPhotosStatus
): IntakeAuditUiState["photosStatus"] {
  if (status === "received" || status === "verified") return "received";
  if (status === "needs_clarification") return "link_sent";
  return "none";
}

function mapPhotosStatusFromUi(
  status: IntakeAuditUiState["photosStatus"]
): LocationPhotosStatus {
  if (status === "received") return "received";
  if (status === "link_sent") return "needs_clarification";
  return "missing";
}

function mapPowerFromUi(source: string): PowerAvailable {
  if (!source) return "unknown";
  if (source === "none") return "no";
  return "yes";
}

function mapPowerToUi(power: PowerAvailable): string {
  if (power === "no") return "none";
  if (power === "yes") return "220V";
  return "";
}

export function siteAuditToAuditUi(
  json: IntakeSiteAuditJson | null | undefined
): Pick<
  IntakeAuditUiState,
  | "address"
  | "addressSelected"
  | "addressConfirmed"
  | "photosStatus"
  | "techPowerSource"
  | "heavyEquipmentAccess"
> {
  const audit = parseSiteAuditJson(json);
  return {
    address: audit.mounting_address,
    addressConfirmed: audit.checks.address_confirmed,
    addressSelected: audit.mounting_address.length > 0,
    photosStatus: mapPhotosStatusToUi(audit.location_photos_status),
    techPowerSource: mapPowerToUi(audit.power_available),
    heavyEquipmentAccess:
      audit.mounting_access === "ok"
        ? "yes"
        : audit.mounting_access === "blocked" || audit.mounting_access === "limited"
          ? "no"
          : "",
  };
}

export function auditUiToSiteAudit(
  ui: IntakeAuditUiState,
  prev?: IntakeSiteAuditJson | null
): IntakeSiteAuditJson {
  const base = parseSiteAuditJson(prev);
  const mountingAccess: MountingAccess =
    ui.heavyEquipmentAccess === "yes"
      ? "ok"
      : ui.heavyEquipmentAccess === "no"
        ? "limited"
        : base.mounting_access;

  return {
    mounting_address: ui.address.trim(),
    location_photos_status: mapPhotosStatusFromUi(ui.photosStatus),
    power_available: mapPowerFromUi(ui.techPowerSource),
    mounting_access: mountingAccess,
    cable_route: base.cable_route,
    notes: base.notes,
    checks: {
      address_confirmed: ui.addressConfirmed && ui.address.trim().length > 0,
      photos_verified: ui.photosStatus === "received",
      power_confirmed: ui.techPowerSource !== "",
      access_confirmed:
        ui.heavyEquipmentAccess === "yes" || base.checks.access_confirmed,
    },
  };
}

export function countSiteAuditChecks(json: IntakeSiteAuditJson | null | undefined): {
  completed: number;
  total: number;
} {
  const audit = parseSiteAuditJson(json);
  const total = 3;
  let completed = 0;
  if (audit.checks.address_confirmed) completed += 1;
  if (audit.checks.photos_verified) completed += 1;
  if (audit.checks.power_confirmed) completed += 1;
  return { completed, total };
}

export function terrainSummaryLabel(json: IntakeSiteAuditJson | null | undefined): string {
  const { completed, total } = countSiteAuditChecks(json);
  return `Teren: ${completed} / ${total} verificări`;
}

/** Map persisted site audit to quote workspace terrain display (read-only). */
export function siteAuditToTerrainChecks(
  json: IntakeSiteAuditJson | null | undefined
): {
  locationVerified: boolean;
  photosVerified: boolean;
  powerVerified: boolean;
  accessVerified: boolean;
} {
  const audit = parseSiteAuditJson(json);
  return {
    locationVerified: audit.checks.address_confirmed,
    photosVerified: audit.checks.photos_verified,
    powerVerified: audit.checks.power_confirmed,
    accessVerified: audit.checks.access_confirmed,
  };
}
