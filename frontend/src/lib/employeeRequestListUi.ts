import type { EmployeeRequestStatus } from "@/api/employeeMobileRequests";

export type EmployeeRequestStatusFilter =
  | "all"
  | "submitted"
  | "approved"
  | "rejected"
  | "cancelled";

export const EMPLOYEE_REQUEST_STATUS_FILTERS: {
  value: EmployeeRequestStatusFilter;
  label: string;
}[] = [
  { value: "all", label: "Toate" },
  { value: "submitted", label: "Trimise" },
  { value: "approved", label: "Aprobate" },
  { value: "rejected", label: "Respinse" },
  { value: "cancelled", label: "Anulate" },
];

export const REVIEW_DEFAULT_STATUS_FILTER: EmployeeRequestStatusFilter = "submitted";

export const LIST_DISPLAY_LIMIT = 25;

export const STATUS_GROUP_ORDER: EmployeeRequestStatus[] = [
  "submitted",
  "approved",
  "rejected",
  "cancelled",
  "draft",
];

export const STATUS_GROUP_LABELS: Record<EmployeeRequestStatus, string> = {
  draft: "Ciorne",
  submitted: "Trimise",
  approved: "Aprobate",
  rejected: "Respinse",
  cancelled: "Anulate",
};

export function filterRequestsByStatus<T extends { status: EmployeeRequestStatus }>(
  items: T[],
  filter: EmployeeRequestStatusFilter,
): T[] {
  if (filter === "all") return items;
  return items.filter((item) => item.status === filter);
}

export function countRequestsByFilter<T extends { status: EmployeeRequestStatus }>(
  items: T[],
): Record<EmployeeRequestStatusFilter, number> {
  return {
    all: items.length,
    submitted: items.filter((item) => item.status === "submitted").length,
    approved: items.filter((item) => item.status === "approved").length,
    rejected: items.filter((item) => item.status === "rejected").length,
    cancelled: items.filter((item) => item.status === "cancelled").length,
  };
}

export function groupRequestsByStatus<T extends { status: EmployeeRequestStatus }>(
  items: T[],
): { status: EmployeeRequestStatus; items: T[] }[] {
  return STATUS_GROUP_ORDER.map((status) => ({
    status,
    items: items.filter((item) => item.status === status),
  })).filter((group) => group.items.length > 0);
}

export function getSelfRequestsEmptyMessage(
  filter: EmployeeRequestStatusFilter,
  totalCount: number,
): string {
  if (totalCount === 0) {
    return "Nu ai nicio cerere încă.";
  }
  if (filter === "all") {
    return "Nu ai cereri în listă.";
  }
  return "Nicio cerere în filtrul selectat.";
}

export function getReviewEmptyMessage(
  filter: EmployeeRequestStatusFilter,
  totalCount: number,
): string {
  if (totalCount === 0) {
    if (filter === "submitted") {
      return "Nu există cereri trimise pentru review.";
    }
    return "Nu există cereri pentru review.";
  }
  if (filter === "submitted") {
    return "Nu există cereri trimise pentru review.";
  }
  if (filter === "all") {
    return "Nu există cereri pentru review.";
  }
  return "Nicio cerere în filtrul selectat.";
}
