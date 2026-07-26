/**
 * Geometry-derived relations only.
 * mounts_on / attached_to_structure require operator confirmation — never auto-derived.
 */

import type { ClosedContourCandidate } from "@/lib/svgAnalyzer/closed-contour/closedContourTypes";
import type { LayerRoleConfirmation } from "@/lib/svgAnalyzer";
import type { SegmentedPanel } from "../segmentedBackground";
import type { ComponentRelation } from "./types";

/** Build belongs_to_assembly for nested panels under an ACM instance. */
export function buildPanelBelongsToAssemblyRelations(args: {
  componentInstanceId: string;
  panels: Array<Pick<SegmentedPanel, "panel_id">>;
}): ComponentRelation[] {
  return args.panels.map((p, i) => ({
    relation_id: `rel_belongs_${p.panel_id}_${i}`,
    from_component_ref: p.panel_id,
    to_component_ref: args.componentInstanceId,
    relation_type: "belongs_to_assembly",
    status: "proposed",
    provenance: "segmented_panels_proposal",
  }));
}

/**
 * Propose positioned_on / contained_by when geometry allows a safe panel assignment.
 * Multi-panel without per-element mapping → unknown (never mounts_on).
 */
export function proposeGeometryPlacementRelations(args: {
  componentInstanceId: string;
  confirmation: LayerRoleConfirmation;
  candidates: ClosedContourCandidate[];
  panels: SegmentedPanel[];
}): ComponentRelation[] {
  const relations: ComponentRelation[] = [];
  const primaryPanelId = args.panels[0]?.panel_id ?? null;
  const singlePanel = args.panels.length === 1;

  for (const layer of args.confirmation.layers) {
    const role = layer.confirmedRole;
    if (role !== "face" && role !== "printed_artwork" && role !== "logo") continue;
    const layerRef = layer.layerKey;

    if (!singlePanel || !primaryPanelId) {
      relations.push({
        relation_id: `rel_place_${layerRef}`,
        from_component_ref: layerRef,
        to_component_ref: args.componentInstanceId,
        relation_type: "positioned_on",
        status: "unknown",
        provenance: "geometry_insufficient_for_panel_assignment",
      });
      continue;
    }

    relations.push({
      relation_id: `rel_pos_${layerRef}_${primaryPanelId}`,
      from_component_ref: layerRef,
      to_component_ref: primaryPanelId,
      relation_type: "positioned_on",
      status: "proposed",
      provenance: "ccc_geometry_proposal",
    });
    relations.push({
      relation_id: `rel_cb_${layerRef}_${primaryPanelId}`,
      from_component_ref: layerRef,
      to_component_ref: primaryPanelId,
      relation_type: "contained_by",
      status: "proposed",
      provenance: "ccc_geometry_proposal",
    });
  }

  return relations;
}

export function assertNoAutoMountRelations(relations: ComponentRelation[]): boolean {
  return !relations.some(
    (r) =>
      (r.relation_type === "mounts_on" || r.relation_type === "attached_to_structure") &&
      r.provenance !== "operator",
  );
}
