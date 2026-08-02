/**
 * Wave 0 + U7 — Romanian-first shell navigation projection.
 *
 * Route URLs stay stable. Visibility is decided by rbac.canViewNav.
 * U7: single canonical production home (/shop-floor = Atelier) and role home redirects.
 * DEV tooling section appears only when VITE_ENABLE_DEV_AUTH is active (non-prod).
 */

import {
  Activity,
  BarChart3,
  ClipboardList,
  Cog,
  Factory,
  FileText,
  GitBranch,
  Handshake,
  Inbox,
  LayoutDashboard,
  Package,
  Settings,
  Shield,
  Users,
  Warehouse,
  Zap,
  User,
  type LucideIcon,
} from "lucide-react";
import type { NavItem, Role } from "./rbac";
import { canViewNav } from "./rbac";

/** Single operational entry for production — Shop Floor surface, operator-facing label Atelier. */
export const CANONICAL_PRODUCTION_HOME = "/shop-floor";

export type NavItemStatus = "active" | "preview" | "audit" | "legacy" | "compat";

export interface ShellNavItemDef {
  to: string;
  label: string;
  icon: LucideIcon;
  navKey: NavItem;
  /** Exact NavLink match (default true). Product System keeps prefix match. */
  end?: boolean;
  /** Optional honesty label in nav (audit/preview/compat). */
  status?: NavItemStatus;
  /** Highlight as the role's primary production entry when path matches canonical home. */
  productionPrimary?: boolean;
}

export interface ShellNavSectionDef {
  id: string;
  title: string;
  items: ShellNavItemDef[];
  /** Shown only when rbac reports demos/dev tooling is visible */
  devOnly?: boolean;
}

/**
 * Canonical IA — maps existing routes only (no invented paths).
 * U7: Producție no longer lists peer "homes"; Control sits under Management.
 */
export const SHELL_NAV_SECTIONS: ShellNavSectionDef[] = [
  {
    id: "lucrari",
    title: "Lucrări",
    items: [
      { to: "/intake", label: "Cereri", icon: Inbox, navKey: "intake" },
      {
        to: "/product-system/products",
        label: "Produse",
        icon: Package,
        navKey: "products",
        end: false,
      },
      { to: "/quotes", label: "Oferte", icon: FileText, navKey: "quotes" },
      { to: "/orders", label: "Comenzi", icon: ClipboardList, navKey: "orders" },
    ],
  },
  {
    id: "productie",
    title: "Producție",
    items: [
      {
        to: CANONICAL_PRODUCTION_HOME,
        label: "Atelier",
        icon: Factory,
        navKey: "shopfloor",
        productionPrimary: true,
      },
      { to: "/execution", label: "Planificare", icon: Activity, navKey: "execution" },
      {
        to: "/execution/ops-graph",
        label: "Ops-Graph",
        icon: GitBranch,
        navKey: "ops_graph",
        status: "audit",
      },
      {
        to: "/operator",
        label: "Acțiune task",
        icon: User,
        navKey: "operator",
        status: "compat",
      },
      {
        to: "/tablet",
        label: "Stații",
        icon: Zap,
        navKey: "tablet",
        status: "compat",
      },
    ],
  },
  {
    id: "oameni",
    title: "Oameni",
    items: [
      { to: "/employees", label: "Angajați", icon: Users, navKey: "employees" },
      { to: "/attendance", label: "Pontaj", icon: Activity, navKey: "attendance" },
      {
        to: "/employees-records",
        label: "Evidență HR",
        icon: FileText,
        navKey: "employees_records",
      },
    ],
  },
  {
    id: "resurse",
    title: "Resurse",
    items: [
      { to: "/utilaje", label: "Utilaje", icon: Cog, navKey: "utilaje" },
      { to: "/inventory", label: "Inventar", icon: Warehouse, navKey: "inventory" },
      {
        to: "/inventory/pricing",
        label: "Prețuri",
        icon: BarChart3,
        navKey: "pricing",
      },
    ],
  },
  {
    id: "relatii",
    title: "Relații",
    items: [
      { to: "/clients", label: "Clienți", icon: Users, navKey: "clients" },
      {
        to: "/colaboratori",
        label: "Colaboratori",
        icon: Handshake,
        navKey: "colaboratori",
      },
      { to: "/documents", label: "Documente", icon: FileText, navKey: "documents" },
    ],
  },
  {
    id: "management",
    title: "Management",
    items: [
      {
        to: "/dashboard",
        label: "Control producție",
        icon: LayoutDashboard,
        navKey: "dashboard",
        status: "preview",
      },
      { to: "/reports", label: "Rapoarte", icon: BarChart3, navKey: "reports" },
      {
        to: "/employee-payments",
        label: "Plăți",
        icon: BarChart3,
        navKey: "payments",
      },
      {
        to: "/employee-advances",
        label: "Avansuri",
        icon: Warehouse,
        navKey: "advances",
      },
    ],
  },
  {
    id: "administrare",
    title: "Administrare",
    items: [
      { to: "/modules", label: "Harta", icon: GitBranch, navKey: "modules" },
      {
        to: "/governance",
        label: "Guvernanță",
        icon: Shield,
        navKey: "governance",
      },
      { to: "/settings", label: "Setări", icon: Settings, navKey: "settings" },
    ],
  },
  {
    id: "dev-tooling",
    title: "DEV tooling",
    devOnly: true,
    items: [
      {
        to: "/demo/commercial-spine",
        label: "Demo Commercial Spine",
        icon: Activity,
        navKey: "demos",
        status: "audit",
      },
      {
        to: "/demo/volumetric-letter-preview",
        label: "Demo Volumetric Preview",
        icon: Package,
        navKey: "demos",
        status: "audit",
      },
      {
        to: "/product-system/blueprint-dossier",
        label: "Blueprint Dossier",
        icon: FileText,
        navKey: "demos",
        status: "audit",
      },
      {
        to: "/reports/operational",
        label: "Rapoarte operaționale",
        icon: BarChart3,
        navKey: "demos",
        status: "audit",
      },
    ],
  },
];

const STATUS_LABEL: Record<NavItemStatus, string> = {
  active: "",
  preview: "preview",
  audit: "audit",
  legacy: "legacy",
  compat: "compat",
};

export function navStatusLabel(status?: NavItemStatus): string | null {
  if (!status || status === "active") return null;
  return STATUS_LABEL[status];
}

/**
 * Default landing path after login / root / unknown route.
 * UI visibility only — backend authorization remains authoritative for mutations.
 */
export function getRoleHomePath(role: Role): string {
  switch (role) {
    case "operator":
      return CANONICAL_PRODUCTION_HOME;
    case "manager":
      return CANONICAL_PRODUCTION_HOME;
    case "admin":
      return "/dashboard";
    case "sales":
      return "/quotes";
    case "viewer":
      return "/dashboard";
    default: {
      const _exhaustive: never = role;
      return _exhaustive;
    }
  }
}

/** Paths always reachable inside the desktop shell (redirects / shared deep links). */
function isShellUtilityPath(pathname: string): boolean {
  if (pathname === "/") return true;
  // Legacy redirects that immediately bounce — allow so Navigate can run.
  if (
    pathname === "/pricing" ||
    pathname === "/products" ||
    pathname === "/templates" ||
    pathname === "/personal" ||
    pathname.startsWith("/inventory/material-price-registry") ||
    pathname.startsWith("/inventory/commercial-markup-policy") ||
    pathname.startsWith("/inventory/productsystem-pricing-preview") ||
    pathname.startsWith("/product-system/dossier-completion")
  ) {
    return true;
  }
  return false;
}

/**
 * UI route accessibility for desktop shell (not a substitute for backend auth).
 * Deep links stay when the role can view the owning nav surface.
 */
export function pathAllowedForRole(role: Role, pathname: string): boolean {
  if (isShellUtilityPath(pathname)) return true;

  if (pathname.startsWith("/execution/ops-graph")) {
    return canViewNav(role, "ops_graph");
  }
  if (pathname.startsWith("/execution/reality-review")) {
    return canViewNav(role, "execution");
  }
  if (pathname === "/execution" || /^\/execution\/[^/]+$/.test(pathname)) {
    return canViewNav(role, "execution");
  }
  if (pathname.startsWith("/tablet")) {
    return canViewNav(role, "tablet");
  }
  if (pathname.startsWith("/product-system")) {
    return canViewNav(role, "products") || canViewNav(role, "demos");
  }
  // Canonical Intake V6 operator shell — same roles as Cereri list (view:intake).
  // Not demos-gated; production entry is Dashboard CTA → /intake-v6/operator bootstrap.
  if (pathname.startsWith("/intake-v6")) {
    return canViewNav(role, "intake");
  }
  if (pathname.startsWith("/demo/")) {
    return canViewNav(role, "demos");
  }
  if (pathname.startsWith("/reports/operational")) {
    return canViewNav(role, "demos");
  }
  if (pathname.startsWith("/clients/")) {
    return canViewNav(role, "clients");
  }
  if (pathname.startsWith("/quotes/")) {
    return canViewNav(role, "quotes");
  }
  if (pathname.startsWith("/orders/")) {
    return canViewNav(role, "orders");
  }
  if (pathname.startsWith("/intake/")) {
    return canViewNav(role, "intake");
  }
  if (pathname.startsWith("/employees-records/")) {
    return canViewNav(role, "employees_records");
  }
  if (pathname.startsWith("/attendance/")) {
    return canViewNav(role, "attendance");
  }
  if (pathname.startsWith("/inventory/pricing")) {
    return canViewNav(role, "pricing");
  }

  for (const section of projectNavSectionsForRole(role)) {
    for (const item of section.items) {
      if (item.end === false) {
        if (pathname === item.to || pathname.startsWith(`${item.to}/`)) return true;
      } else if (pathname === item.to) {
        return true;
      }
    }
  }
  return false;
}

export function projectNavSectionsForRole(role: Role): ShellNavSectionDef[] {
  return SHELL_NAV_SECTIONS.map((section) => ({
    ...section,
    items: section.items.filter((item) => canViewNav(role, item.navKey)),
  })).filter((section) => section.items.length > 0);
}

/** Labels present in projected nav (for tests / matrix docs). */
export function projectedNavLabels(role: Role): string[] {
  return projectNavSectionsForRole(role).flatMap((s) => s.items.map((i) => i.label));
}
