import { v6 } from "./atoms/intakeV6Presentation";

const PROJECT_FILE_SLOTS = [
  { id: "vector", label: "Grafică / proiect vectorial", types: "SVG · PDF · AI · CDR · EPS · DXF" },
  { id: "cnc", label: "Materiale CNC", types: "DXF · PDF" },
  { id: "print", label: "Print / artwork", types: "PNG · JPG · PDF" },
] as const;

export default function IntakeV6ProjectFilesPlaceholder() {
  return (
    <div className={`${v6.card} mb-4`} data-testid="intake-v6-project-files-placeholder">
      <h3 className="mb-3 text-[12px] font-bold uppercase tracking-wide text-slate-200">Fișiere proiect</h3>
      <ul className="space-y-2">
        {PROJECT_FILE_SLOTS.map((slot) => (
          <li
            key={slot.id}
            className="flex flex-wrap items-center justify-between gap-2 rounded border border-wo-border-strong bg-wo-surface-inset/50 px-3 py-2 text-[11px]"
            data-testid={`intake-v6-project-file-slot-${slot.id}`}
          >
            <div>
              <span className="font-medium text-slate-200">{slot.label}</span>
              <span className="mt-0.5 block text-[10px] text-slate-500">{slot.types}</span>
            </div>
            <span className="rounded bg-slate-800/80 px-2 py-0.5 text-[10px] text-slate-400">Lipsă</span>
          </li>
        ))}
      </ul>
    </div>
  );
}



