import type { ReactNode } from "react";

/** Groups primary CTAs in the side panel without extra chrome. */
export default function StickyWorkspaceActions({
  children,
}: {
  children: ReactNode;
}) {
  return (
    <div
      className="space-y-2"
      data-testid="sticky-workspace-actions"
    >
      {children}
    </div>
  );
}
