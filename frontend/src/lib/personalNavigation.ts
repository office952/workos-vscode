import { Activity, BarChart3, FileText, Users, Warehouse } from "lucide-react";
import type { LucideIcon } from "lucide-react";

export interface PersonalNavItem {
  to: string;
  label: string;
  icon: LucideIcon;
}

/**
 * People / money entries used by shell (Oameni + Management).
 * Labels are Romanian-first; no "(registry)" chrome.
 * HR demo must not use the generic "Angajați" label — that points at /employees.
 */
export const personalNavItems: PersonalNavItem[] = [
  { to: "/employees", label: "Angajați", icon: Users },
  { to: "/employees-records", label: "Evidență HR", icon: FileText },
  { to: "/attendance", label: "Pontaj", icon: Activity },
  { to: "/employee-payments", label: "Plăți", icon: BarChart3 },
  { to: "/employee-advances", label: "Avansuri", icon: Warehouse },
];

export function findPersonalNavItem(label: string): PersonalNavItem | undefined {
  return personalNavItems.find((item) => item.label === label);
}
