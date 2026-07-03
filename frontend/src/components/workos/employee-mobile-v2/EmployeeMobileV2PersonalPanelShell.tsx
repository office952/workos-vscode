import { emV2Surface } from "@/lib/employeeMobileV2DesignTokens";
import { cn } from "@/lib/utils";

/**
 * Light v2 skin for reused v1 Personal panels — spacing and surfaces only, no logic changes.
 */
export default function EmployeeMobileV2PersonalPanelShell({
  children,
  testId,
}: {
  children: React.ReactNode;
  testId: string;
}) {
  return (
    <div
      className={cn(
        emV2Surface.panel,
        "mt-1 space-y-4 p-4",
        "[&_[data-testid='employee-mobile-requests-panel']>div:nth-child(2)]:hidden",
        "[&_[data-testid='employee-mobile-requests-self-badge']]:hidden",
        "[&_[data-testid='employee-mobile-attendance-panel']>div:first-child]:hidden",
        "[&_.border-\\[\\#243044\\]]:border-[#1E293B]",
        "[&_.bg-\\[\\#0A1020\\]]:bg-[#0B1120]/70",
        "[&_.rounded-xl]:rounded-2xl",
        "[&_.space-y-5]:space-y-4",
      )}
      data-testid={testId}
    >
      {children}
    </div>
  );
}
