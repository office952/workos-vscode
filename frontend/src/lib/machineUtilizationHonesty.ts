import type { Machine, MachineUtilizationKind } from "@/lib/mockData";

export type MachineUtilPresentation = {
  kind: MachineUtilizationKind;
  kindLabel: "ACTUAL" | "PROXY" | "GAP";
  /** Display string for util — never a fake percent when gap. */
  displayPct: string;
  showBar: boolean;
  barValue: number;
  note: string;
};

/**
 * Same honesty standard as Dashboard: do not present invented util as shop-floor truth.
 */
export function presentMachineUtilization(machine: Machine): MachineUtilPresentation {
  const kind: MachineUtilizationKind =
    machine.utilizationKind ??
    (machine.currentJobId ? "proxy" : "placeholder");

  if (kind === "placeholder" || (!machine.currentJobId && kind !== "actual")) {
    return {
      kind: "placeholder",
      kindLabel: "GAP",
      displayPct: "—",
      showBar: false,
      barValue: 0,
      note: "Utilizare atelier indisponibilă — registry, nu load pe ture (util% WC pe Dashboard)",
    };
  }

  if (kind === "proxy") {
    return {
      kind: "proxy",
      kindLabel: "PROXY",
      displayPct: `${machine.utilizationPct}%`,
      showBar: true,
      barValue: machine.utilizationPct,
      note: "Semnal proxy / demo — nu utilizare confirmată pe ture",
    };
  }

  return {
    kind: "actual",
    kindLabel: "ACTUAL",
    displayPct: `${machine.utilizationPct}%`,
    showBar: true,
    barValue: machine.utilizationPct,
    note: "Utilizare din semnal operațional confirmat",
  };
}
