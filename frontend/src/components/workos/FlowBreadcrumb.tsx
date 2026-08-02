/**
 * FlowBreadcrumb — Operator flow trail component.
 *
 * Shows the operator where they are in the operational flow:
 * Cereri → Detaliu Cerere → Ofertă → Comandă → Producție → Realitate → Rapoarte
 *
 * Rules:
 *  - Links where route exists
 *  - Disabled items where no context
 *  - Does NOT change business logic
 */
import { Link } from "react-router-dom";
import { ChevronRight, Home } from "lucide-react";

export interface BreadcrumbItem {
  label: string;
  to?: string;
  active?: boolean;
}

interface FlowBreadcrumbProps {
  items: BreadcrumbItem[];
  className?: string;
}

export default function FlowBreadcrumb({ items, className = "" }: FlowBreadcrumbProps) {
  return (
    <nav
      aria-label="Navigare flux"
      className={`flex items-center gap-1 text-[11px] text-wo-text-muted ${className}`}
    >
      <Link
        to="/dashboard"
        className="flex items-center gap-1 transition-colors hover:text-wo-text-primary"
      >
        <Home className="w-3 h-3" />
      </Link>
      {items.map((item, idx) => (
        <span key={idx} className="flex items-center gap-1">
          <ChevronRight className="w-3 h-3 text-wo-text-dim" />
          {item.to && !item.active ? (
            <Link
              to={item.to}
              className="transition-colors hover:text-wo-text-primary"
            >
              {item.label}
            </Link>
          ) : (
            <span
              className={
                item.active
                  ? "font-medium text-wo-text-primary"
                  : "text-wo-text-dim"
              }
            >
              {item.label}
            </span>
          )}
        </span>
      ))}
    </nav>
  );
}

/**
 * Pre-built breadcrumb configs for common flows.
 */
export function intakeBreadcrumb(): BreadcrumbItem[] {
  return [{ label: "Cereri", to: "/intake", active: true }];
}

export function intakeDetailBreadcrumb(id?: string): BreadcrumbItem[] {
  return [
    { label: "Cereri", to: "/intake" },
    { label: id ? `Cerere ${id}` : "Detaliu Cerere", active: true },
  ];
}

/** Commercial spine: Cereri → Produse (product definition). */
export function productsBreadcrumb(templateLabel?: string): BreadcrumbItem[] {
  const items: BreadcrumbItem[] = [
    { label: "Cereri", to: "/intake" },
    {
      label: "Produse",
      to: "/product-system/products",
      active: !templateLabel,
    },
  ];
  if (templateLabel) {
    items.push({ label: templateLabel, active: true });
  }
  return items;
}

export function quotesBreadcrumb(): BreadcrumbItem[] {
  return [
    { label: "Cereri", to: "/intake" },
    { label: "Produse", to: "/product-system/products" },
    { label: "Oferte", active: true },
  ];
}

export function quoteDetailBreadcrumb(id?: string): BreadcrumbItem[] {
  return [
    { label: "Cereri", to: "/intake" },
    { label: "Produse", to: "/product-system/products" },
    { label: "Oferte", to: "/quotes" },
    { label: id ? `Ofertă ${id}` : "Detaliu Ofertă", active: true },
  ];
}

export function ordersBreadcrumb(): BreadcrumbItem[] {
  return [
    { label: "Cereri", to: "/intake" },
    { label: "Produse", to: "/product-system/products" },
    { label: "Oferte", to: "/quotes" },
    { label: "Comenzi", active: true },
  ];
}

export function orderDetailBreadcrumb(id?: string): BreadcrumbItem[] {
  return [
    { label: "Cereri", to: "/intake" },
    { label: "Produse", to: "/product-system/products" },
    { label: "Oferte", to: "/quotes" },
    { label: "Comenzi", to: "/orders" },
    { label: id ? `Comandă ${id}` : "Detaliu Comandă", active: true },
  ];
}

export function productionBreadcrumb(): BreadcrumbItem[] {
  return [
    { label: "Comenzi", to: "/orders" },
    { label: "Producție", active: true },
  ];
}

export function executionBreadcrumb(): BreadcrumbItem[] {
  return [
    { label: "Comenzi", to: "/orders" },
    { label: "Producție", to: "/execution" },
    { label: "Realitate Execuție", active: true },
  ];
}

export function operationalRealityReviewBreadcrumb(): BreadcrumbItem[] {
  return [
    { label: "Comenzi", to: "/orders" },
    { label: "Producție", to: "/execution" },
    { label: "Review Realitate Operațională", active: true },
  ];
}

export function operationalReportsBreadcrumb(): BreadcrumbItem[] {
  return [
    { label: "Rapoarte", to: "/reports" },
    { label: "Rapoarte Operaționale", active: true },
  ];
}

export function reportsBreadcrumb(): BreadcrumbItem[] {
  return [
    { label: "Producție", to: "/execution" },
    { label: "Rapoarte", active: true },
  ];
}

export function shopFloorBreadcrumb(): BreadcrumbItem[] {
  return [
    { label: "Producție", to: "/execution" },
    { label: "Shop Floor", active: true },
  ];
}

export function operatorBreadcrumb(): BreadcrumbItem[] {
  return [
    { label: "Producție", to: "/execution" },
    { label: "Operator", active: true },
  ];
}