/**
 * Wave 0 — Desktop WorkOS chrome (sidebar + topbar).
 * Business routes stay in App.tsx; this shell renders <Outlet />.
 */

import { NavLink, Outlet, useLocation } from "react-router-dom";
import {
  AlertTriangle,
  Bell,
  ChevronLeft,
  ChevronRight,
  LogOut,
  Menu,
  Search,
  X,
  Zap,
} from "lucide-react";
import { useEffect, useRef, useState } from "react";
import { useIsMobile } from "@/hooks/use-mobile";
import { useAuth } from "@/contexts/AuthContext";
import { useCurrentPermissions } from "@/hooks/useCurrentPermissions";
import { ThemeToggle } from "@/components/workos/design-system/ThemeToggle";
import EnvironmentBanner from "@/components/workos/EnvironmentBanner";
import VersionBadge from "@/components/system/VersionBadge";
import { productionAlerts } from "@/lib/mockData";
import { isMockEnabled } from "@/lib/mockGuard";
import { resolveShellCriticalCount } from "@/lib/shellAlertTruth";
import { projectNavSectionsForRole } from "@/lib/shellNavigation";
import { useTheme } from "@/contexts/ThemeContext";

function getInitials(name?: string, email?: string): string {
  if (name && name.trim().length > 0) {
    const parts = name.trim().split(/\s+/);
    if (parts.length >= 2) return (parts[0][0] + parts[1][0]).toUpperCase();
    return parts[0].slice(0, 2).toUpperCase();
  }
  if (email) return email.slice(0, 2).toUpperCase();
  return "U";
}

function UserMenu() {
  const { user, logout } = useAuth();
  const [open, setOpen] = useState(false);
  const ref = useRef<HTMLDivElement>(null);

  useEffect(() => {
    const handler = (e: MouseEvent) => {
      if (ref.current && !ref.current.contains(e.target as Node)) setOpen(false);
    };
    document.addEventListener("mousedown", handler);
    return () => document.removeEventListener("mousedown", handler);
  }, []);

  const initials = getInitials(user?.name, user?.email);
  const displayName = user?.name || user?.email?.split("@")[0] || "Utilizator";

  return (
    <div className="relative" ref={ref}>
      <button
        onClick={() => setOpen((v) => !v)}
        className="flex items-center justify-center w-8 h-8 rounded-full bg-blue-600 hover:bg-blue-500 text-[11px] font-bold text-white transition-colors"
        title="Cont utilizator"
      >
        {initials}
      </button>
      {open && (
        <div className="absolute right-0 top-10 w-56 bg-wo-surface-raised border border-wo-border-strong rounded-lg shadow-xl overflow-hidden z-50">
          <div className="px-3 py-2.5 border-b border-wo-border-strong">
            <p className="text-[12px] font-semibold text-wo-text-primary truncate">{displayName}</p>
            <p className="text-[10px] text-wo-text-dim uppercase tracking-wide mt-0.5">Autentificat</p>
          </div>
          <button
            onClick={() => {
              setOpen(false);
              logout();
            }}
            className="w-full flex items-center gap-2 px-3 py-2.5 text-[12px] text-wo-text-secondary hover:bg-wo-error-muted hover:text-wo-error transition-colors text-left"
          >
            <LogOut className="w-3.5 h-3.5" />
            Deconectare
          </button>
        </div>
      )}
    </div>
  );
}

export default function AppShell() {
  const location = useLocation();
  const isNarrow = useIsMobile();
  const { role } = useCurrentPermissions();
  const { resolvedTheme } = useTheme();
  const [collapsed, setCollapsed] = useState(false);
  /** Narrow viewport: nav starts closed so content (e.g. ops-graph) is first-fold. */
  const [navDrawerOpen, setNavDrawerOpen] = useState(false);
  // UI-TRUTH-01C: never show mock "N critical" as real incidents.
  const criticalAlerts = resolveShellCriticalCount(isMockEnabled(), productionAlerts);
  const navSections = projectNavSectionsForRole(role);
  const dayMode = resolvedTheme === "light";

  // Content-first on route change at narrow width (OR-07: ops-graph not occluded by nav).
  useEffect(() => {
    if (isNarrow) setNavDrawerOpen(false);
  }, [location.pathname, isNarrow]);

  const railCollapsed = isNarrow ? false : collapsed;
  const showNavLabels = isNarrow ? true : !collapsed;

  return (
    <div
      className="flex h-screen bg-wo-surface-app text-wo-text-primary overflow-hidden"
      data-testid="workos-desktop-shell"
      data-nav-mode={isNarrow ? "drawer" : "rail"}
      data-nav-drawer={isNarrow ? (navDrawerOpen ? "open" : "closed") : "n/a"}
      data-shell-day={dayMode ? "true" : "false"}
      data-shell-role={role}
      style={
        {
          "--workos-sidebar-width": isNarrow
            ? "0px"
            : collapsed
              ? "60px"
              : "220px",
        } as React.CSSProperties
      }
    >
      {/* Narrow backdrop — closes drawer; does not mutate product truth */}
      {isNarrow && navDrawerOpen && (
        <button
          type="button"
          aria-label="Close navigation drawer"
          data-testid="workos-nav-drawer-backdrop"
          className="fixed inset-0 z-40 bg-black/40 border-0 cursor-pointer"
          onClick={() => setNavDrawerOpen(false)}
        />
      )}

      {/* Sidebar — rail on desktop; overlay drawer on narrow (OR-07) */}
      <aside
        data-testid="workos-sidebar"
        data-nav-drawer-open={isNarrow ? String(navDrawerOpen) : undefined}
        data-day-shell={dayMode ? "true" : "false"}
        className={
          isNarrow
            ? `workos-app-sidebar fixed inset-y-0 left-0 z-50 flex w-[220px] flex-col border-r border-wo-border-subtle bg-wo-surface-shell transition-transform duration-200 ${
                navDrawerOpen ? "translate-x-0" : "-translate-x-full"
              }`
            : `workos-app-sidebar relative z-30 flex shrink-0 flex-col border-r border-wo-border-subtle bg-wo-surface-shell transition-all duration-200 ${
                collapsed ? "w-[60px]" : "w-[220px]"
              }`
        }
      >
        {/* Logo */}
        <div className="flex items-center gap-2 px-4 h-[48px] border-b border-wo-border-subtle">
          <Zap className="w-5 h-5 text-primary shrink-0" />
          {showNavLabels && (
            <span className="text-[15px] font-bold tracking-tight text-wo-text-primary">
              WorkOS
            </span>
          )}
          {isNarrow && (
            <button
              type="button"
              aria-label="Close navigation"
              data-testid="workos-nav-drawer-close"
              className="ml-auto p-1.5 rounded text-wo-text-dim hover:text-wo-text-secondary hover:bg-wo-hover"
              onClick={() => setNavDrawerOpen(false)}
            >
              <X className="w-4 h-4" />
            </button>
          )}
        </div>

        {/* Nav */}
        <nav className="flex-1 py-2 px-2 overflow-y-auto scrollbar-thin" data-testid="workos-shell-nav">
          {navSections.map((section) => (
            <div key={section.id} className="mb-2" data-nav-section={section.id}>
              {showNavLabels && (
                <p className="px-3 pt-2 pb-1 text-[9px] font-bold uppercase tracking-widest text-wo-text-dim">
                  {section.title}
                </p>
              )}
              <div className="space-y-0.5">
                {section.items.map((item) => (
                  <NavLink
                    key={`${section.id}-${item.to}`}
                    to={item.to}
                    end={item.end === false ? false : true}
                    onClick={() => {
                      if (isNarrow) setNavDrawerOpen(false);
                    }}
                    className={({ isActive }) =>
                      `flex items-center gap-3 px-3 py-2 rounded-md text-[13px] font-medium transition-colors ${
                        isActive
                          ? "bg-primary/15 text-primary border-l-2 border-primary"
                          : "text-wo-text-muted hover:text-wo-text-primary hover:bg-wo-hover border-l-2 border-transparent"
                      }`
                    }
                  >
                    <item.icon className="w-4 h-4 shrink-0" />
                    {showNavLabels && <span>{item.label}</span>}
                  </NavLink>
                ))}
              </div>
            </div>
          ))}
        </nav>

        {/* Runtime release version indicator (Sprint #38) */}
        <VersionBadge collapsed={railCollapsed} />

        {/* Collapse toggle — desktop rail only */}
        {!isNarrow && (
          <button
            type="button"
            onClick={() => setCollapsed(!collapsed)}
            className="flex items-center justify-center h-10 border-t border-wo-border-subtle text-wo-text-dim hover:text-wo-text-secondary transition-colors"
          >
            {collapsed ? <ChevronRight className="w-4 h-4" /> : <ChevronLeft className="w-4 h-4" />}
          </button>
        )}
      </aside>

      {/* Main */}
      <div className="flex-1 flex flex-col overflow-hidden min-w-0">
        {/* Top bar */}
        <header
          data-testid="workos-desktop-topbar"
          className="workos-app-topbar flex items-center justify-between h-[48px] px-4 border-b border-wo-border-subtle bg-wo-surface-shell gap-2"
          data-day-shell={dayMode ? "true" : "false"}
        >
          <div className="flex items-center gap-2 min-w-0 flex-1">
            {isNarrow && (
              <button
                type="button"
                aria-label={navDrawerOpen ? "Close navigation drawer" : "Open navigation drawer"}
                aria-expanded={navDrawerOpen}
                data-testid="workos-nav-drawer-toggle"
                className="relative z-10 shrink-0 p-1.5 rounded border border-wo-border-subtle bg-wo-surface-input text-wo-text-muted hover:text-wo-text-primary hover:bg-wo-hover"
                onClick={() => setNavDrawerOpen((open) => !open)}
              >
                <Menu className="w-4 h-4" />
              </button>
            )}
            {!isNarrow && (
              <div className="flex items-center gap-2 bg-wo-surface-input border border-wo-border-subtle rounded-md px-3 py-1.5 w-full max-w-72 min-w-0">
                <Search className="w-3.5 h-3.5 text-wo-text-dim shrink-0" />
                <input
                  id="app-global-search"
                  name="app-global-search"
                  type="text"
                  placeholder="Caută comenzi, task-uri, utilaje..."
                  aria-label="Caută comenzi, task-uri, utilaje"
                  className="bg-transparent text-[12px] text-wo-text-secondary placeholder:text-wo-text-dim outline-none w-full min-w-0"
                />
              </div>
            )}
            {isNarrow && (
              <p
                className="truncate text-[12px] font-semibold text-wo-text-primary min-w-0"
                data-testid="workos-narrow-topbar-title"
              >
                WorkOS
              </p>
            )}
          </div>
          <div className="flex items-center gap-2 shrink-0">
            {/* Full status chip overlaps Menu at ~390px — keep desktop only (OR-07). */}
            {!isNarrow && <EnvironmentBanner />}
            {criticalAlerts > 0 && (
              <div className="flex items-center gap-1 px-2 py-1 bg-wo-error-muted border border-wo-error/40 rounded text-wo-error text-[11px] font-semibold">
                <AlertTriangle className="w-3 h-3" />
                {criticalAlerts} critical
              </div>
            )}
            <ThemeToggle compact className="text-wo-text-muted" />
            <button className="relative p-1.5 rounded hover:bg-wo-hover transition-colors">
              <Bell className="w-4 h-4 text-wo-text-muted" />
              {criticalAlerts > 0 && (
                <span className="absolute -top-0.5 -right-0.5 w-2 h-2 bg-wo-error rounded-full" />
              )}
            </button>
            <div className="pl-2 border-l border-wo-border-subtle">
              <UserMenu />
            </div>
          </div>
        </header>

        {/* Content — routes owned by App.tsx */}
        <main className="relative z-0 flex-1 overflow-auto p-4">
          <Outlet />
        </main>
      </div>
    </div>
  );
}
