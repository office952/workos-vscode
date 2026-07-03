import { Link, useLocation } from "react-router-dom";
import {
  Download,
  Home,
  ListTodo,
  User,
  UserCheck,
} from "lucide-react";
import { useAuth } from "@/contexts/AuthContext";
import { usePwaInstallPrompt } from "@/hooks/usePwaInstallPrompt";
import { canAccessRequestReviewWorkspace } from "@/lib/employeeMobileAccess";
import { formatOperationalPanelSubtitle } from "@/lib/employeeMobileUiHelpers";
import { cn } from "@/lib/utils";

export const EMPLOYEE_MOBILE_NAV_ITEMS = [
  { id: "home", label: "Acasă", path: "/employee-app", icon: Home, end: true },
  { id: "tasks", label: "Taskuri", path: "/employee-app/tasks", icon: ListTodo },
  { id: "personal", label: "Personal", path: "/employee-app/personal", icon: User },
  { id: "review", label: "Review", path: "/employee-app/review", icon: UserCheck },
] as const;

function navIsActive(pathname: string, path: string, end?: boolean): boolean {
  const normalized = pathname.replace(/\/$/, "") || "/";
  if (end) return normalized === path.replace(/\/$/, "");
  return normalized.startsWith(path);
}

export function EmployeeMobileHeader() {
  const { user } = useAuth();
  const displayName = user?.name ?? user?.email ?? "Angajat";

  return (
    <header
      className="flex items-center gap-2.5 px-0.5 py-0.5"
      data-testid="employee-mobile-header"
    >
      <div
        className="flex h-8 w-8 shrink-0 items-center justify-center rounded-full bg-blue-500/15 text-blue-400 ring-1 ring-blue-500/25"
        aria-hidden
      >
        <User className="w-4 h-4" />
      </div>
      <div className="min-w-0 flex-1">
        <h1 className="text-[15px] font-semibold text-slate-100 truncate leading-tight">
          {displayName}
        </h1>
        <p
          className="text-[11px] text-slate-500 truncate"
          data-testid="employee-mobile-subtitle"
        >
          {formatOperationalPanelSubtitle(undefined, user?.role)}
        </p>
      </div>
    </header>
  );
}

export function EmployeeMobileBottomNav() {
  const location = useLocation();
  const { user } = useAuth();
  const showReviewNav = canAccessRequestReviewWorkspace(user?.role);
  const navItems = EMPLOYEE_MOBILE_NAV_ITEMS.filter(
    (item) => item.id !== "review" || showReviewNav,
  );

  return (
    <nav
      className="fixed bottom-0 inset-x-0 z-40 border-t border-[#1E293B] bg-[#0A1020]/95 backdrop-blur-md pb-[env(safe-area-inset-bottom,0px)]"
      data-testid="employee-mobile-bottom-nav"
      aria-label="Navigare Employee Mobile"
    >
      <div className="mx-auto flex max-w-lg px-1 pt-1 pb-2">
        {navItems.map((item) => {
          const Icon = item.icon;
          const active = navIsActive(location.pathname, item.path, item.end);
          return (
            <Link
              key={item.id}
              to={item.path}
              className={cn(
                "flex flex-1 flex-col items-center gap-1 rounded-xl py-2 text-xs font-medium transition-colors min-h-[52px] justify-center",
                active
                  ? "bg-blue-900/35 text-blue-200"
                  : "text-slate-500 hover:text-slate-300 hover:bg-[#111827]/60",
              )}
              data-testid={`employee-mobile-nav-${item.id}`}
              aria-current={active ? "page" : undefined}
            >
              <Icon className={cn("w-5 h-5", active ? "text-blue-400" : "text-slate-500")} aria-hidden />
              {item.label}
            </Link>
          );
        })}
      </div>
    </nav>
  );
}

export function EmployeeMobileInstallCard({ compact = false }: { compact?: boolean }) {
  const { canPromptInstall, isInstalled, promptInstall } = usePwaInstallPrompt();

  return (
    <section
      className={cn(
        "rounded-xl space-y-2.5",
        compact
          ? "border-0 bg-[#0A1020]/50 p-3"
          : "border border-[#1E293B] bg-[#111827] p-4",
      )}
      data-testid="employee-mobile-install-card"
    >
      <div className="flex items-center gap-2">
        <Download className="w-4 h-4 text-blue-400 shrink-0" aria-hidden />
        <h2 className="text-[13px] font-semibold text-slate-100">Instalează pe telefon</h2>
      </div>
      {isInstalled ? (
        <p
          className="text-[11px] text-emerald-300/90 leading-relaxed"
          data-testid="employee-mobile-install-status-installed"
        >
          Aplicația este deschisă ca PWA instalată pe acest dispozitiv.
        </p>
      ) : canPromptInstall ? (
        <p
          className="text-[11px] text-blue-200/90 leading-relaxed"
          data-testid="employee-mobile-install-status-ready"
        >
          Browserul permite instalarea — poți adăuga WorkOS pe ecranul principal.
        </p>
      ) : (
        <p
          className="text-[11px] text-slate-400 leading-relaxed"
          data-testid="employee-mobile-install-status-manual"
        >
          Poți adăuga WorkOS pe ecranul principal din meniul browserului. Nu există cont separat —
          folosești același login WorkOS.
        </p>
      )}
      {canPromptInstall && !isInstalled && (
        <button
          type="button"
          onClick={() => void promptInstall()}
          className="inline-flex w-full items-center justify-center gap-2 rounded-xl border border-blue-800/40 bg-blue-950/30 px-3 py-2.5 text-[12px] font-medium text-blue-200 hover:bg-blue-950/50 transition-colors min-h-[44px]"
          data-testid="employee-mobile-install-button"
        >
          <Download className="w-4 h-4" aria-hidden />
          Instalează aplicația
        </button>
      )}
      <p className="text-[10px] text-slate-500 leading-relaxed">
        iPhone: Share → Add to Home Screen · Android/Chrome: meniul browser → Instalează aplicația
      </p>
      <p className="text-[10px] text-slate-600 leading-relaxed">
        Fără notificări push sau mod offline în acest build — doar acces rapid la Employee Mobile.
      </p>
    </section>
  );
}
