import { emV2SectionLabelClass } from "@/lib/employeeMobileV2DesignTokens";

const FUTURE_MODULES = [
  "Montaje",
  "Materiale",
  "Clarificări",
  "Scanner QR",
  "Notificări",
] as const;

export default function EmployeeMobileV2FutureModules({
  testId = "employee-mobile-v2-future-modules",
}: {
  testId?: string;
}) {
  return (
    <section className="mt-2 space-y-3" data-testid={testId}>
      <p className={emV2SectionLabelClass()}>În curând</p>
      <div className="flex flex-wrap gap-2">
        {FUTURE_MODULES.map((label) => (
          <span
            key={label}
            className="rounded-md border border-[#1E293B] bg-[#111827] px-3 py-1.5 text-[12px] font-medium text-slate-500"
            data-testid={`${testId}-${label.toLowerCase().replace(/\s+/g, "-")}`}
          >
            {label}
          </span>
        ))}
      </div>
    </section>
  );
}
