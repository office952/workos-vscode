import type { ReactNode } from "react";

export default function WorkspaceMainColumn({ children }: { children: ReactNode }) {
  return (
    <div
      className="min-w-0 space-y-3"
      data-testid="workspace-main-column"
    >
      {children}
    </div>
  );
}
