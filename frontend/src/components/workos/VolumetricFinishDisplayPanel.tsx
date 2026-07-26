import type { IntakeProductSpec } from "@/lib/intakeProductSpec";
import { formatVolumetricFinishSummary } from "@/lib/volumetricFinishDisplay";

function ColorSwatch({ hex, testId }: { hex: string; testId?: string }) {
  return (
    <span
      className="inline-block w-6 h-6 rounded border border-slate-600 shrink-0"
      style={{ backgroundColor: hex }}
      data-testid={testId}
      aria-hidden
    />
  );
}

export interface VolumetricFinishDisplayPanelProps {
  spec: IntakeProductSpec | null | undefined;
  testId?: string;
}

/** Read-only Finisaje și folii — intake → quote review. */
export default function VolumetricFinishDisplayPanel({
  spec,
  testId = "quote-finish-display",
}: VolumetricFinishDisplayPanelProps) {
  const summary = formatVolumetricFinishSummary(spec);

  return (
    <section
      className="rounded-md border border-wo-border-strong bg-wo-surface-inset/40 p-3 space-y-3"
      data-testid={testId}
    >
      <h3 className="text-[12px] font-bold text-slate-200">Finisaje și folii</h3>

      <div className="space-y-1" data-testid={`${testId}-return`}>
        <p className="text-[10px] uppercase tracking-wide text-slate-500">Cant / return</p>
        <div className="flex items-start gap-2">
          {summary.returnPreviewHex && (
            <ColorSwatch
              hex={summary.returnPreviewHex}
              testId={`${testId}-return-swatch`}
            />
          )}
          <div className="min-w-0">
            <p className="text-[12px] font-medium text-slate-100">{summary.returnFinishLabel}</p>
            {summary.returnFinishDetail && (
              <p className="text-[11px] text-slate-300" data-testid={`${testId}-return-detail`}>
                {summary.returnFinishDetail}
              </p>
            )}
            {summary.returnApproximatePreview && (
              <p
                className="text-[10px] text-slate-500 mt-1"
                data-testid={`${testId}-return-approx-note`}
              >
                Preview aproximativ
              </p>
            )}
          </div>
        </div>
      </div>

      <div className="space-y-1" data-testid={`${testId}-face`}>
        <p className="text-[10px] uppercase tracking-wide text-slate-500">Față / folie</p>
        <div className="flex items-start gap-2">
          {summary.faceVinylPreviewHex && (
            <ColorSwatch hex={summary.faceVinylPreviewHex} testId={`${testId}-face-swatch`} />
          )}
          <div className="min-w-0">
            <p className="text-[12px] font-medium text-slate-100" data-testid={`${testId}-face-label`}>
              {summary.faceVinylLabel}
              {summary.faceVinylTranslucent && (
                <span className="ml-1.5 text-[9px] uppercase tracking-wide text-purple-300/90">
                  translucent
                </span>
              )}
            </p>
            {summary.faceVinylDetail && summary.faceVinylLabel !== "Nu" && (
              <p className="text-[11px] text-slate-300" data-testid={`${testId}-face-detail`}>
                {summary.faceVinylDetail}
              </p>
            )}
          </div>
        </div>
      </div>

      {summary.warnings.length > 0 && (
        <ul className="space-y-1 pt-1 border-t border-wo-border-subtle/80" data-testid={`${testId}-warnings`}>
          {summary.warnings.map((w) => (
            <li key={w} className="text-[10px] text-slate-500">
              {w}
            </li>
          ))}
        </ul>
      )}
    </section>
  );
}
