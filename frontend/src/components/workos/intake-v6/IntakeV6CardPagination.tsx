import { ChevronLeft, ChevronRight } from "lucide-react";
import { v6 } from "./atoms/intakeV6Presentation";

export const INTAKE_V6_CARD_PAGE_SIZE = 4;

export default function IntakeV6CardPagination({
  pageIndex,
  pageCount,
  totalItems,
  onPageChange,
  testId = "intake-v6-card-pagination",
}: {
  pageIndex: number;
  pageCount: number;
  totalItems: number;
  onPageChange: (nextPage: number) => void;
  testId?: string;
}) {
  if (totalItems <= INTAKE_V6_CARD_PAGE_SIZE) return null;

  const start = pageIndex * INTAKE_V6_CARD_PAGE_SIZE + 1;
  const end = Math.min(totalItems, (pageIndex + 1) * INTAKE_V6_CARD_PAGE_SIZE);

  return (
    <div
      className="mb-2 flex flex-wrap items-center justify-between gap-2"
      data-testid={testId}
    >
      <span className={`${v6.mono} text-[10px] text-slate-500`}>
        {start}–{end} din {totalItems}
      </span>
      <div className="flex items-center gap-1">
        <button
          type="button"
          className="inline-flex items-center gap-0.5 rounded border border-[#2A3548] bg-[#1E293B]/80 px-2 py-0.5 text-[10px] font-semibold text-slate-300 hover:border-sky-500/30 disabled:cursor-not-allowed disabled:opacity-40"
          onClick={() => onPageChange(pageIndex - 1)}
          disabled={pageIndex <= 0}
          data-testid={`${testId}-prev`}
          aria-label="Anterior"
        >
          <ChevronLeft className="h-3 w-3" aria-hidden />
          Înapoi
        </button>
        <span
          className={`${v6.mono} px-1 text-[10px] text-slate-500`}
          data-testid={`${testId}-page`}
        >
          {pageIndex + 1}/{pageCount}
        </span>
        <button
          type="button"
          className="inline-flex items-center gap-0.5 rounded border border-[#2A3548] bg-[#1E293B]/80 px-2 py-0.5 text-[10px] font-semibold text-slate-300 hover:border-sky-500/30 disabled:cursor-not-allowed disabled:opacity-40"
          onClick={() => onPageChange(pageIndex + 1)}
          disabled={pageIndex >= pageCount - 1}
          data-testid={`${testId}-next`}
          aria-label="Următor"
        >
          Înainte
          <ChevronRight className="h-3 w-3" aria-hidden />
        </button>
      </div>
    </div>
  );
}
