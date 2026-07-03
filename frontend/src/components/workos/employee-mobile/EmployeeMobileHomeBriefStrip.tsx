import type { HomeBriefLine } from "@/lib/employeeMobileShopFloorPresentation";
import { cn } from "@/lib/utils";

const KIND_STYLES: Record<HomeBriefLine["kind"], string> = {
  continue: "text-emerald-300",
  waiting: "text-amber-300",
  upcoming: "text-violet-300",
};

export default function EmployeeMobileHomeBriefStrip({
  lines,
  testId = "employee-mobile-home-brief",
}: {
  lines: HomeBriefLine[];
  testId?: string;
}) {
  if (lines.length === 0) return null;

  return (
    <section
      className="rounded-xl border border-[#243044]/80 bg-[#161b28]/80 px-3 py-2.5 space-y-1.5"
      data-testid={testId}
    >
      <p className="text-xs font-semibold uppercase tracking-wide text-blue-300/90">Pe scurt</p>
      <ul className="space-y-1">
        {lines.map((line) => (
          <li
            key={`${line.kind}-${line.taskId ?? line.text}`}
            className="flex items-start gap-2 text-sm text-slate-300 leading-snug"
            data-testid={`${testId}-${line.kind}`}
          >
            <span
              className={cn(
                "shrink-0 text-xs font-semibold uppercase tracking-wide min-w-[4.5rem]",
                KIND_STYLES[line.kind],
              )}
            >
              {line.label}:
            </span>
            <span className="min-w-0">{line.text}</span>
          </li>
        ))}
      </ul>
    </section>
  );
}
