import {
  ADMIN_TRUTH_FLOW_STEPS,
  type AdminTruthFlowStepId,
} from "@/lib/adminProductTruthUi";

export function AdminTruthFlowStrip({
  active,
}: {
  active: AdminTruthFlowStepId;
}) {
  return (
    <section
      aria-label="Continuitate administrare produs"
      className="rounded-lg border border-wo-border-subtle bg-wo-surface-raised px-3 py-2"
      data-testid="admin-truth-flow-strip"
    >
      <p className="text-[10px] font-semibold uppercase tracking-wide text-wo-text-muted">
        Continuitate administrare produs
      </p>
      <ol className="mt-1.5 flex flex-wrap items-center gap-x-2 gap-y-1 text-[11px]">
        {ADMIN_TRUTH_FLOW_STEPS.map((step, index) => (
          <li key={step.id} className="flex items-center gap-2">
            {index > 0 ? <span aria-hidden="true" className="text-wo-text-dim">→</span> : null}
            <span
              className={
                step.id === active
                  ? "font-semibold text-wo-info"
                  : "text-wo-text-secondary"
              }
              title={step.description}
            >
              {step.label}
            </span>
          </li>
        ))}
      </ol>
    </section>
  );
}
