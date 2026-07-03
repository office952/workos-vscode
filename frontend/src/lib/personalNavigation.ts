import { Activity, BarChart3, FileText, Users, Warehouse } from "lucide-react";
import type { LucideIcon } from "lucide-react";

export interface PersonalNavItem {
  to: string;
  label: string;
  icon: LucideIcon;
}

/** Sidebar entries under Personal — operational registry vs HR demo are separate. */
export const personalNavItems: PersonalNavItem[] = [
  { to: "/employees", label: "Angajați operaționali", icon: Users },
  { to: "/employees-records", label: "Evidență internă HR", icon: FileText },
  { to: "/attendance", label: "Pontaj", icon: Activity },
  { to: "/employee-payments", label: "Plăți angajați", icon: BarChart3 },
  { to: "/employee-advances", label: "Avansuri / Datorii", icon: Warehouse },
];

export function findPersonalNavItem(label: string): PersonalNavItem | undefined {
  return personalNavItems.find((item) => item.label === label);
}
