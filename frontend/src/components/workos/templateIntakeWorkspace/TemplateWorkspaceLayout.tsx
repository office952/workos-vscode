import type { ReactNode } from "react";

export interface TemplateWorkspaceLayoutProps {
  main: ReactNode;
  side: ReactNode;
}

/**
 * Responsive two-column workspace shell.
 * Desktop: flexible main + fixed-width sticky side panel.
 * Mobile: stacked (main first, then side).
 */
export default function TemplateWorkspaceLayout({
  main,
  side,
}: TemplateWorkspaceLayoutProps) {
  return (
    <div
      className="grid grid-cols-1 xl:grid-cols-[minmax(0,1fr)_minmax(280px,320px)] gap-4 items-start w-full"
      data-testid="template-workspace-layout"
    >
      {main}
      {side}
    </div>
  );
}
