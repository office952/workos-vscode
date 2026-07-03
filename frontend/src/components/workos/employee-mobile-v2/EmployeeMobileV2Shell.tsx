import { Link, Outlet, useLocation } from "react-router-dom";
import { Home, ListTodo, User } from "lucide-react";
import { useAuth } from "@/contexts/AuthContext";
import { formatOperationalPanelSubtitle } from "@/lib/employeeMobileUiHelpers";
import { v2Effects, v2Motion } from "@/lib/employeeMobileV2Effects";
import { cn } from "@/lib/utils";

const NAV_ITEMS = [
  { id: "home", label: "Acasă", path: "/employee-app-v2", icon: Home, end: true },
  { id: "tasks", label: "Taskuri", path: "/employee-app-v2/tasks", icon: ListTodo },
  { id: "personal", label: "Personal", path: "/employee-app-v2/personal", icon: User },
] as const;

function navIsActive(pathname: string, path: string, end?: boolean): boolean {
  const normalized = pathname.replace(/\/$/, "") || "/";
  const target = path.replace(/\/$/, "");
  if (end) return normalized === target;
  return normalized === target || normalized.startsWith(`${target}/`);
}

export function EmployeeMobileV2Header() {
  const { user } = useAuth();
  const displayName = user?.name ?? user?.email ?? "Angajat";

  return (
    <header
      className="flex items-center gap-3 mb-5"
      data-testid="employee-mobile-v2-header"
    >
      <div
        className="flex h-10 w-10 shrink-0 items-center justify-center rounded-full bg-blue-500/12 text-blue-400 font-semibold text-sm"
        aria-hidden
      >
        {displayName.charAt(0).toUpperCase()}
      </div>
      <div className="min-w-0 flex-1">
        <h1 className="text-[17px] font-semibold text-slate-100 truncate leading-tight">
          Bună, {displayName.split(" ")[0]}
        </h1>
        <p
          className="text-[13px] text-slate-400 truncate"
          data-testid="employee-mobile-v2-subtitle"
        >
          {formatOperationalPanelSubtitle(undefined, user?.role)}
        </p>
      </div>
    </header>
  );
}

export function EmployeeMobileV2BottomNav() {
  const location = useLocation();

  return (
    <nav
      className={cn(
        "fixed bottom-0 inset-x-0 z-40 pb-[env(safe-area-inset-bottom,0px)]",
        v2Effects.stickySurface,
      )}
      data-testid="employee-mobile-v2-bottom-nav"
      aria-label="Navigare Employee Mobile v2"
    >
      <div className="mx-auto flex max-w-[430px] justify-around px-6 pt-2.5 pb-2 min-h-[72px]">
        {NAV_ITEMS.map((item) => {
          const Icon = item.icon;
          const active = navIsActive(location.pathname, item.path, item.end);
          return (
            <Link
              key={item.id}
              to={item.path}
              className={cn(
                v2Effects.bottomNavItem,
                v2Motion.tapTarget,
                active ? v2Effects.bottomNavActive : v2Effects.bottomNavInactive,
              )}
              data-testid={`employee-mobile-v2-nav-${item.id}`}
              aria-current={active ? "page" : undefined}
            >
              {active ? (
                <span
                  className={v2Effects.bottomNavIndicator}
                  aria-hidden
                  data-testid={`employee-mobile-v2-nav-${item.id}-indicator`}
                />
              ) : null}
              <Icon
                className={cn("w-[22px] h-[22px]", active ? "text-blue-400" : "text-slate-500")}
                aria-hidden
              />
              <span
                className={cn(
                  "text-[12px] font-medium",
                  active ? "text-blue-400 font-semibold" : "text-slate-500",
                )}
              >
                {item.label}
              </span>
            </Link>
          );
        })}
      </div>
    </nav>
  );
}

export function EmployeeMobileV2Layout() {
  const location = useLocation();

  return (
    <div
      className="mx-auto flex min-h-[100dvh] w-full max-w-[430px] flex-col bg-[#0B1120] text-slate-100 [-webkit-tap-highlight-color:transparent]"
      data-testid="employee-mobile-v2-shell"
    >
      <div className="flex-1 px-4 pt-[calc(0.75rem+env(safe-area-inset-top,0px))] pb-[calc(5rem+env(safe-area-inset-bottom,0px))]">
        <div key={location.pathname} className={v2Motion.pageEnter}>
          <Outlet />
        </div>
      </div>
      <EmployeeMobileV2BottomNav />
    </div>
  );
}
