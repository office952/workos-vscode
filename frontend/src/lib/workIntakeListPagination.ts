/** Default page size for Work Intake list (client-side pagination). */
export const WORK_INTAKE_LIST_PAGE_SIZE = 10;

export interface WorkIntakeListPaginationResult<T> {
  page: number;
  pageSize: number;
  totalItems: number;
  totalPages: number;
  startIndex: number;
  endIndex: number;
  items: T[];
  rangeLabel: string;
  pageLabel: string;
}

export function paginateWorkIntakeList<T>(
  items: T[],
  page: number,
  pageSize: number = WORK_INTAKE_LIST_PAGE_SIZE
): WorkIntakeListPaginationResult<T> {
  const totalItems = items.length;
  const totalPages = Math.max(1, Math.ceil(totalItems / pageSize));
  const safePage = Math.min(Math.max(1, page), totalPages);
  const startIndex = (safePage - 1) * pageSize;
  const endIndex = Math.min(startIndex + pageSize, totalItems);
  const pageItems = items.slice(startIndex, endIndex);

  const rangeLabel =
    totalItems === 0
      ? "0 din 0"
      : `${startIndex + 1}–${endIndex} din ${totalItems}`;

  return {
    page: safePage,
    pageSize,
    totalItems,
    totalPages,
    startIndex,
    endIndex,
    items: pageItems,
    rangeLabel,
    pageLabel: `Pagina ${safePage} din ${totalPages}`,
  };
}
