import type { ReactNode } from "react";

/** Sticky operator control column — context, status, actions. */
export default function WorkspaceSidePanel({ children }: { children: ReactNode }) {
  return (
    <aside
      className="xl:sticky xl:top-4 space-y-3 min-w-0"
      data-testid="workspace-side-panel"
    >
      {children}
    </aside>
  );
}
