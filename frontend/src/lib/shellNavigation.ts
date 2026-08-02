/**
 * Wave 0 — Romanian-first shell navigation projection.
 *
 * Route URLs stay stable. Visibility is decided by rbac.canViewNav.
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

export interface ShellNavItemDef {
  to: string;
  label: string;
  icon: LucideIcon;
  navKey: NavItem;
  /** Exact NavLink match (default true). Product System keeps prefix match. */
  end?: boolean;
}

export interface ShellNavSectionDef {
  id: string;
  title: string;
  items: ShellNavItemDef[];
  /** Shown only when rbac reports demos/dev tooling is visible */
  devOnly?: boolean;
}

/** Canonical IA — maps existing routes only (no invented paths). */
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
      { to: "/execution", label: "Planificare", icon: Activity, navKey: "execution" },
      {
        to: "/execution/ops-graph",
        label: "Ops-Graph",
        icon: GitBranch,
        navKey: "ops_graph",
      },
      { to: "/tablet", label: "Atelier", icon: Zap, navKey: "tablet" },
      {
        to: "/dashboard",
        label: "Control producție",
        icon: LayoutDashboard,
        navKey: "dashboard",
      },
      { to: "/shop-floor", label: "Shop Floor", icon: Factory, navKey: "shopfloor" },
      { to: "/operator", label: "Operator", icon: User, navKey: "operator" },
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
      },
      {
        to: "/demo/volumetric-letter-preview",
        label: "Demo Volumetric Preview",
        icon: Package,
        navKey: "demos",
      },
      {
        to: "/intake-v6/operator",
        label: "Intake V6 (diag)",
        icon: Inbox,
        navKey: "demos",
      },
      {
        to: "/product-system/blueprint-dossier",
        label: "Blueprint Dossier",
        icon: FileText,
        navKey: "demos",
      },
      {
        to: "/reports/operational",
        label: "Rapoarte operaționale",
        icon: BarChart3,
        navKey: "demos",
      },
    ],
  },
];

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
