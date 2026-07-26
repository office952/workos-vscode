/**
 * Minimal Artwork Analysis Contract v1 — consume / review only.
 * WorkOS does not parse SVG/DWG/DXF; desktop app owns file intelligence.
 * Transport: TBD.
 */

export const ARTWORK_ANALYSIS_CONTRACT_VERSION = "artwork_analysis_contract_v1" as const;

export const SUPPORTED_ARTWORK_ANALYSIS_CONTRACT_VERSIONS = [
  ARTWORK_ANALYSIS_CONTRACT_VERSION,
] as const;

export type ArtworkAnalysisContractVersion =
  (typeof SUPPORTED_ARTWORK_ANALYSIS_CONTRACT_VERSIONS)[number];

export type ObservationStatus = "observed" | "proposed" | "confirmed";
export type BindingStatus = "proposed" | "confirmed";
export type SourceFileKind = "svg" | "dwg" | "dxf" | "other" | "unknown";

export interface ArtworkAnalysisProvenanceV1 {
  analysis_id: string;
  analysis_version: string;
  source_file_name?: string | null;
  source_file_hash?: string | null;
  source_file_kind?: SourceFileKind;
  producer_app?: string | null;
  producer_app_version?: string | null;
  produced_at?: string | null;
  source_entity_ids?: string[];
}

export interface ArtworkAnalysisEntityV1 {
  entity_id: string;
  kind?: string | null;
  label?: string | null;
  status?: ObservationStatus;
  attributes?: Record<string, unknown>;
}

export interface ArtworkAnalysisGroupV1 {
  group_id: string;
  member_entity_ids?: string[];
  label?: string | null;
  status?: ObservationStatus;
}

export interface ArtworkAnalysisMeasurementV1 {
  measurement_id: string;
  entity_id?: string | null;
  metric: string;
  value: number;
  unit?: string | null;
  status?: ObservationStatus;
}

export interface ArtworkAnalysisObservationV1 {
  observation_id: string;
  code?: string | null;
  message: string;
  status?: ObservationStatus;
  related_entity_ids?: string[];
  confidence?: number | null;
}

export interface ArtworkAnalysisSuggestedBindingV1 {
  binding_id: string;
  target_role?: string | null;
  entity_ids?: string[];
  /** Inbound bindings must be proposed; confirmed is operator-only. */
  status: "proposed";
  confidence?: number | null;
  rationale?: string | null;
}

export interface ArtworkAnalysisContractV1 {
  artwork_analysis_contract_version: ArtworkAnalysisContractVersion;
  provenance: ArtworkAnalysisProvenanceV1;
  entities?: ArtworkAnalysisEntityV1[];
  groups?: ArtworkAnalysisGroupV1[];
  measurements?: ArtworkAnalysisMeasurementV1[];
  observations?: ArtworkAnalysisObservationV1[];
  suggested_bindings?: ArtworkAnalysisSuggestedBindingV1[];
  confidence_summary?: number | null;
  extensions?: Record<string, unknown>;
}

export interface ArtworkAnalysisReviewSurfaceV1 {
  analysis_id: string;
  contract_version: string;
  source_file_name?: string | null;
  source_file_hash?: string | null;
  entity_count: number;
  group_count: number;
  measurement_count: number;
  observation_count: number;
  suggested_binding_count: number;
  unconfirmed_observation_count: number;
  all_bindings_proposed: boolean;
  product_truth_writable_from_adapter: false;
  transport: "tbd";
  notes: string[];
}

export function isSupportedArtworkAnalysisContractVersion(
  version: string | null | undefined,
): version is ArtworkAnalysisContractVersion {
  return (
    typeof version === "string" &&
    (SUPPORTED_ARTWORK_ANALYSIS_CONTRACT_VERSIONS as readonly string[]).includes(version)
  );
}

export function buildArtworkAnalysisReviewSurface(
  contract: ArtworkAnalysisContractV1,
): ArtworkAnalysisReviewSurfaceV1 {
  const observations = contract.observations ?? [];
  const bindings = contract.suggested_bindings ?? [];
  const unconfirmed = observations.filter((o) => o.status !== "confirmed").length;
  return {
    analysis_id: contract.provenance.analysis_id,
    contract_version: contract.artwork_analysis_contract_version,
    source_file_name: contract.provenance.source_file_name ?? null,
    source_file_hash: contract.provenance.source_file_hash ?? null,
    entity_count: contract.entities?.length ?? 0,
    group_count: contract.groups?.length ?? 0,
    measurement_count: contract.measurements?.length ?? 0,
    observation_count: observations.length,
    suggested_binding_count: bindings.length,
    unconfirmed_observation_count: unconfirmed,
    all_bindings_proposed: bindings.every((b) => b.status === "proposed"),
    product_truth_writable_from_adapter: false,
    transport: "tbd",
    notes: [
      "Analiza vine din aplicația desktop (observed/proposed).",
      "Operatorul confirmă înainte de Product Truth — adapterul nu scrie automat.",
      "Transport desktop → WorkOS: TBD.",
    ],
  };
}
