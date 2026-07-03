/** Step 7D — discrete truth label for Intake V6 offer preview (no layout redesign). */

export function IntakeV6AggregateCostTruthNotice({ compact = false }: { compact?: boolean }) {
  if (compact) {
    return (
      <p
        className="mb-2 text-[10px] leading-relaxed text-slate-500"
        data-testid="intake-v6-aggregate-cost-truth-notice"
      >
        Preț oficial backend V6 pentru draft intern. Costul intern rămâne doar referință operațională.
      </p>
    );
  }

  return (
    <p
      className="mb-3 rounded border border-sky-900/40 bg-sky-950/30 px-2.5 py-2 text-[10px] leading-relaxed text-sky-200/90"
      data-testid="intake-v6-aggregate-cost-truth-notice"
    >
      Estimare operațională Intake V6 / dry-run — nu este quote priced și nu creează comandă sau taskuri.
      Prețul final validat vine din sursa aggregate{" "}
      <span className="font-mono text-sky-300">v2_aggregate</span> (ProductDefinition + ProductAggregate + Cost BOM +
      Pricing Registry). Reprice necesită aprobare owner.
    </p>
  );
}
