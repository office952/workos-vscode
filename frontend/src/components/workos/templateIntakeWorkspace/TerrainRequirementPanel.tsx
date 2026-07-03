import type { ReactNode } from "react";
import { MapPin } from "lucide-react";
import { INTAKE_SECTION_IDS } from "@/lib/intakeActionSummary";
import { TERRAIN_NA_COMPACT_LABEL } from "@/lib/intakeDeliverySemantics";
import InfoHint from "./InfoHint";

export interface TerrainRequirementPanelProps {
  requiresInstallAudit: boolean;
  installTerrainSection: ReactNode | null;
  terrainDataPreservedNote?: string | null;
}

export default function TerrainRequirementPanel({
  requiresInstallAudit,
  installTerrainSection,
  terrainDataPreservedNote,
}: TerrainRequirementPanelProps) {
  if (requiresInstallAudit && installTerrainSection) {
    return (
      <div id={INTAKE_SECTION_IDS.terrain} className="scroll-mt-4">
        {installTerrainSection}
      </div>
    );
  }

  return (
    <div className="space-y-2" data-testid="terrain-na-panel">
      <div
        className="bg-[#111827] border border-[#1E293B] rounded-lg px-3 py-2 flex items-center gap-2"
        data-testid="terrain-na"
      >
        <MapPin className="w-4 h-4 text-slate-500 shrink-0" />
        <p className="text-[12px] text-slate-400">{TERRAIN_NA_COMPACT_LABEL}</p>
        <InfoHint label="Teren N/A">
          Cererea nu include montaj la locație — verificările de teren nu sunt necesare.
        </InfoHint>
      </div>
      {terrainDataPreservedNote && (
        <p className="text-[10px] text-slate-500 px-1" data-testid="terrain-data-preserved-note">
          {terrainDataPreservedNote}
        </p>
      )}
    </div>
  );
}
