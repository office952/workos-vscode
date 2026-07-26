import { useState } from "react";
import { Info } from "lucide-react";
import VolumetricLetterExpandedPreview from "@/components/workos/preview/VolumetricLetterExpandedPreview";
import type { VolumetricLetterPreviewMode } from "@/lib/volumetricLetterPreview/volumetricLetterPreviewTypes";
import { VOLUMETRIC_LETTER_PREVIEW_DEMO_SCENARIOS } from "@/lib/volumetricLetterPreview/volumetricLetterPreviewMocks";

function ScenarioCard({
  scenarioId,
  title,
  description,
  mode,
  showLabels,
}: {
  scenarioId: string;
  title: string;
  description: string;
  mode: VolumetricLetterPreviewMode;
  showLabels: boolean;
}) {
  const scenario = VOLUMETRIC_LETTER_PREVIEW_DEMO_SCENARIOS.find((s) => s.id === scenarioId);
  if (!scenario) return null;

  const { config } = scenario;
  const { blockers, warnings } = config.readiness;

  return (
    <article
      className="bg-wo-surface-raised border border-wo-border-subtle rounded-lg p-4 space-y-3"
      data-testid={`volumetric-preview-demo-scenario-${scenarioId}`}
    >
      <div>
        <h2 className="text-[14px] font-bold text-wo-text-primary">{title}</h2>
        <p className="text-[11px] text-slate-400 mt-1">{description}</p>
      </div>

      <VolumetricLetterExpandedPreview
        config={config}
        mode={mode}
        showLabels={showLabels}
        hideControls
        testId={`volumetric-preview-demo-${scenarioId}`}
      />

      <div
        className="flex flex-wrap gap-2 text-[10px] font-mono text-slate-500"
        data-testid={`volumetric-preview-demo-readiness-${scenarioId}`}
      >
        <span data-testid={`volumetric-preview-demo-blocker-count-${scenarioId}`}>
          blockers: {blockers.length}
        </span>
        <span data-testid={`volumetric-preview-demo-warning-count-${scenarioId}`}>
          warnings: {warnings.length}
        </span>
      </div>
    </article>
  );
}

/**
 * Isolated visual QA for VolumetricLetterExpandedPreview (ERP-13).
 * Read-only mock configs — no Work Intake, quote, or backend coupling.
 */
export default function VolumetricLetterPreviewDemo() {
  const [mode, setMode] = useState<VolumetricLetterPreviewMode>("expanded");
  const [showLabels, setShowLabels] = useState(true);

  return (
    <div className="max-w-6xl mx-auto space-y-4" data-testid="volumetric-letter-preview-demo-page">
      <header className="space-y-2">
        <div className="flex flex-wrap items-center gap-2">
          <h1 className="text-lg font-bold text-wo-text-primary">Volumetric Letter Preview — Demo QA</h1>
          <span
            className="inline-flex items-center gap-1 rounded border border-slate-600 bg-slate-800/60 px-2 py-0.5 text-[10px] font-semibold uppercase tracking-wide text-slate-300"
            data-testid="volumetric-letter-preview-demo-internal-label"
          >
            <Info className="h-3 w-3" />
            Internal / dev only
          </span>
        </div>
        <p className="text-[12px] text-slate-400 max-w-3xl">
          Preview vectorial generat din configurație — nu ilustrație manuală. Configurile sunt
          read-only; readiness blockers/warnings provin exclusiv din{" "}
          <code className="text-slate-300">config.readiness</code>.
        </p>
      </header>

      <div
        className="flex flex-wrap items-center gap-3 rounded-lg border border-wo-border-subtle bg-wo-surface-raised p-3"
        data-testid="volumetric-letter-preview-demo-global-controls"
      >
        <span className="text-[10px] uppercase tracking-wide text-slate-500">Controale globale</span>
        <div className="inline-flex rounded border border-wo-border-subtle overflow-hidden">
          <button
            type="button"
            className={`px-3 py-1.5 text-[10px] uppercase tracking-wide ${
              mode === "compact"
                ? "bg-slate-700 text-wo-text-primary"
                : "bg-transparent text-slate-400 hover:text-slate-200"
            }`}
            onClick={() => setMode("compact")}
            data-testid="volumetric-letter-preview-demo-global-mode-compact"
          >
            Secțiune
          </button>
          <button
            type="button"
            className={`px-3 py-1.5 text-[10px] uppercase tracking-wide ${
              mode === "expanded"
                ? "bg-slate-700 text-wo-text-primary"
                : "bg-transparent text-slate-400 hover:text-slate-200"
            }`}
            onClick={() => setMode("expanded")}
            data-testid="volumetric-letter-preview-demo-global-mode-expanded"
          >
            Explodat (recomandat)
          </button>
        </div>
        <button
          type="button"
          className={`px-3 py-1.5 text-[10px] uppercase tracking-wide rounded border border-wo-border-subtle ${
            showLabels ? "bg-slate-700 text-wo-text-primary" : "text-slate-400 hover:text-slate-200"
          }`}
          onClick={() => setShowLabels((v) => !v)}
          data-testid="volumetric-letter-preview-demo-global-toggle-labels"
        >
          Etichete {showLabels ? "ON" : "OFF"}
        </button>
        <span
          className="text-[10px] text-slate-500"
          data-testid="volumetric-letter-preview-demo-scenario-count"
        >
          {VOLUMETRIC_LETTER_PREVIEW_DEMO_SCENARIOS.length} scenarii
        </span>
        <span className="text-[10px] text-slate-500" data-testid="volumetric-letter-preview-demo-mode-hint">
          Modul secțiune este pentru citire tehnică interior/exterior.
        </span>
      </div>

      <div
        className="grid gap-4 md:grid-cols-2"
        data-testid="volumetric-letter-preview-demo-grid"
      >
        {VOLUMETRIC_LETTER_PREVIEW_DEMO_SCENARIOS.map((scenario) => (
          <ScenarioCard
            key={scenario.id}
            scenarioId={scenario.id}
            title={scenario.title}
            description={scenario.description}
            mode={mode}
            showLabels={showLabels}
          />
        ))}
      </div>
    </div>
  );
}
