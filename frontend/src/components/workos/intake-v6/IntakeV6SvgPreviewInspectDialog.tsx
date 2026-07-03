import { useMemo, useState } from "react";
import type { LayerAutoRole, LayerRoleConfirmation, SvgAnalysisCoreReport } from "@/lib/svgAnalyzer";
import { resolveSvgPreviewLayerHighlightTarget } from "@/lib/intakeV6/intakeV6SvgPreviewLayerHighlight";
import {
  Dialog,
  DialogContent,
  DialogDescription,
  DialogHeader,
  DialogTitle,
} from "@/components/ui/dialog";
import IntakeV6LayersRoleTable from "./IntakeV6LayersRoleTable";
import IntakeV6SvgPreviewCanvas from "./IntakeV6SvgPreviewCanvas";
import { v6 } from "./atoms/intakeV6Presentation";

export default function IntakeV6SvgPreviewInspectDialog({
  open,
  onOpenChange,
  fileName,
  previewSource,
  missingExternalRaster,
  report,
  confirmation,
  onUpdateLayerRole,
}: {
  open: boolean;
  onOpenChange: (open: boolean) => void;
  fileName?: string | null;
  previewSource: string;
  missingExternalRaster?: boolean;
  report: SvgAnalysisCoreReport;
  confirmation: LayerRoleConfirmation;
  onUpdateLayerRole: (layerKey: string, role: LayerAutoRole) => void;
}) {
  const [hoveredLayerKey, setHoveredLayerKey] = useState<string | null>(null);

  const highlightedLayer = useMemo(
    () => resolveSvgPreviewLayerHighlightTarget(report, confirmation, hoveredLayerKey),
    [hoveredLayerKey, report, confirmation],
  );

  return (
    <Dialog open={open} onOpenChange={onOpenChange}>
      <DialogContent
        className="max-h-[92vh] max-w-[min(96vw,1180px)] overflow-hidden border-[#2A3548] bg-[#111827] p-4 sm:p-5"
        data-testid="intake-v6-preview-inspect-dialog"
      >
        <DialogHeader className="text-left">
          <DialogTitle className="text-[14px] font-semibold text-slate-100">
            Preview SVG & straturi
          </DialogTitle>
          <DialogDescription className="text-[11px] text-slate-500">
            {fileName ? `${fileName} · ` : ""}
            Inspectează grafica și setează rolurile din legendă.
          </DialogDescription>
        </DialogHeader>

        <div
          className="grid max-h-[calc(92vh-7rem)] min-h-0 gap-4 lg:grid-cols-[minmax(0,1.35fr)_minmax(240px,320px)]"
          data-testid="intake-v6-preview-inspect-layout"
        >
          <div className="min-h-0 overflow-auto rounded-md border border-[#2A3548]/80 bg-[#0A0F1A]/30 p-2">
            <IntakeV6SvgPreviewCanvas
              source={previewSource}
              missingExternalRaster={missingExternalRaster}
              testId="intake-v6-preview-inspect-canvas"
              variant="large"
              highlightedLayer={highlightedLayer}
            />
          </div>

          <div className="flex min-h-0 flex-col overflow-hidden rounded-md border border-[#2A3548]/80 bg-[#0A0F1A]/40">
            <div className="border-b border-[#2A3548]/70 px-3 py-2">
              <h3 className={v6.zoneTitle}>Legendă straturi</h3>
              <p className="text-[10px] text-slate-500">Rol confirmat per strat detectat.</p>
            </div>
            <div className="min-h-0 flex-1 overflow-y-auto px-3 py-2">
              <IntakeV6LayersRoleTable
                report={report}
                confirmation={confirmation}
                onUpdateLayerRole={onUpdateLayerRole}
                layout="legend"
                hoveredLayerKey={hoveredLayerKey}
                onHoverLayerKey={setHoveredLayerKey}
              />
            </div>
          </div>
        </div>
      </DialogContent>
    </Dialog>
  );
}
