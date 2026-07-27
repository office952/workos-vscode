/**
 * Day Mode honesty chips — visual separation of Product System truth surfaces.
 * Labels only; no compiler / aggregate / pricing logic.
 */

const CHIPS: { label: string; tone: string; testId: string }[] = [
  {
    label: "Template truth",
    tone: "border-wo-info/40 bg-wo-info-muted text-wo-info",
    testId: "ps-chip-template-truth",
  },
  {
    label: "ProductDefinition PREVIEW ONLY",
    tone: "border-wo-border-strong bg-wo-surface-inset text-wo-text-secondary",
    testId: "ps-chip-definition-preview",
  },
  {
    label: "ProductAggregate READ MODEL",
    tone: "border-wo-border-strong bg-wo-surface-inset text-wo-text-secondary",
    testId: "ps-chip-aggregate-read",
  },
  {
    label: "Pricing reference · NOT PRICE",
    tone: "border-wo-warning/40 bg-wo-warning-muted text-wo-warning",
    testId: "ps-chip-pricing-ref",
  },
  {
    label: "Internal cost · NOT CLIENT PRICE",
    tone: "border-wo-warning/40 bg-wo-warning-muted text-wo-warning",
    testId: "ps-chip-internal-cost",
  },
  {
    label: "Commercial rule · OWNER DECISION",
    tone: "border-wo-info/40 bg-wo-info-muted text-wo-info",
    testId: "ps-chip-commercial-rule",
  },
  {
    label: "Capacity warning · FROZEN",
    tone: "border-wo-border-strong bg-wo-surface-inset text-wo-text-muted",
    testId: "ps-chip-capacity-warning",
  },
];

export function ProductSystemSurfaceTruthChips({
  testId = "product-system-surface-truth-chips",
}: {
  testId?: string;
}) {
  return (
    <div
      data-testid={testId}
      className="flex flex-wrap items-center gap-1.5"
      aria-label="Product System surface honesty"
    >
      {CHIPS.map((chip) => (
        <span
          key={chip.testId}
          data-testid={chip.testId}
          className={`rounded-full border px-2 py-0.5 text-[10px] font-semibold ${chip.tone}`}
        >
          {chip.label}
        </span>
      ))}
      <p className="basis-full text-[10px] leading-relaxed text-wo-text-muted">
        Prețuri din template ≠ sursă universală ofertă client. Aggregate BOM ≠ ofertă client.
        Surface-urile de mai sus sunt etichete de claritate admin — nu activează compiler, pricing
        sau Capacity %.
      </p>
    </div>
  );
}
