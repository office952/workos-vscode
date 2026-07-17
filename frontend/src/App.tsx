import { Toaster } from "@/components/ui/toaster";
import { Toaster as Sonner } from "@/components/ui/sonner";
import { TooltipProvider } from "@/components/ui/tooltip";
import { QueryClient, QueryClientProvider } from "@tanstack/react-query";
import { BrowserRouter, Routes, Route, NavLink, Navigate, Outlet, useLocation } from "react-router-dom";
import {
  LayoutDashboard,
  Factory,
  User,
  GitBranch,
  Shield,
  Bell,
  Search,
  ChevronLeft,
  ChevronRight,
  AlertTriangle,
  Zap,
  Inbox,
  FileText,
  ClipboardList,
  Warehouse,
  BarChart3,
  Users,
  Cog,
  Handshake,
  Settings,
  LogOut,
  Package,
  Activity,
} from "lucide-react";
import { useState, useRef, useEffect, lazy, Suspense } from "react";
import Dashboard from "./pages/Dashboard";
import ShopFloor from "./pages/ShopFloor";
import OperatorView from "./pages/OperatorView";
import ModuleChain from "./pages/ModuleChain";
import Governance from "./pages/Governance";
import WorkIntake from "./pages/WorkIntake";
import IntakeLegacyRoute from "./pages/IntakeLegacyRoute";
import Quotes from "./pages/Quotes";
import Orders from "./pages/Orders";
import Inventory from "./pages/Inventory";
import Pricing from "./pages/Pricing";
import Reports from "./pages/Reports";
import Employees from "./pages/Employees";
import EmployeesRecords from "./pages/EmployeesRecords";
import EmployeeProfile from "./pages/EmployeeProfile";
import Attendance from "./pages/Attendance";
import EmployeeAttendanceEffects from "./pages/EmployeeAttendanceEffects";
import EmployeePayments from "./pages/EmployeePayments";
import EmployeeAdvances from "./pages/EmployeeAdvances";
import EmployeeMobileApp from "./pages/EmployeeMobileApp";
import EmployeeMobileV2App from "./pages/EmployeeMobileV2App";
import Colaboratori from "./pages/Colaboratori";
import Utilaje from "./pages/Utilaje";
import SettingsPage from "./pages/Settings";
import ProductSystem from "./pages/ProductSystem";
import ProductSystemLayout from "./features/product-system/ProductSystemLayout";
import ProductSystemIndexRedirect from "./features/product-system/ProductSystemIndexRedirect";
import ProductSystemPlannedSectionPage from "./features/product-system/ProductSystemPlannedSectionPage";
import Clients from "./pages/Clients";
import ClientWorkspace from "./pages/ClientWorkspace";
import DocumentCenter from "./pages/DocumentCenter";
import { TabletStationSelector, TabletStationQueue, TabletTaskDetail } from "./pages/TabletMode";
const BlueprintDossierStudio = lazy(() => import("./pages/BlueprintDossierStudio"));
const OutputBlocksPreview = lazy(() => import("./pages/OutputBlocksPreview"));
import ErrorBoundary from "./components/ErrorBoundary";
import ExecutionDashboard from "./pages/ExecutionDashboard";
import ExecutionDetail from "./pages/ExecutionDetail";
import OperationalRealityReview from "./pages/OperationalRealityReview";
import OperationalReports from "./pages/OperationalReports";
import CommercialSpineDemo from "./pages/CommercialSpineDemo";
import VolumetricLetterPreviewDemo from "./pages/VolumetricLetterPreviewDemo";
// Deprecated intake entrypoints removed; Intake V6 is the active dedicated workspace.
import IntakeV6OperatorWorkspaceApp from "./pages/IntakeV6OperatorWorkspaceApp";
import AuthCallback from "./pages/AuthCallback";
import AuthError from "./pages/AuthError";
import LogoutCallbackPage from "./pages/LogoutCallbackPage";
import LoginGate from "./components/LoginGate";
import { AuthProvider, useAuth } from "./contexts/AuthContext";
import { productionAlerts } from "./lib/mockData";
import { isMockEnabled } from "./lib/mockGuard";
import { resolveShellCriticalCount } from "./lib/shellAlertTruth";
import VersionBadge from "./components/system/VersionBadge";
import EnvironmentBanner from "./components/workos/EnvironmentBanner";
import { personalNavItems } from "./lib/personalNavigation";

const queryClient = new QueryClient({
  defaultOptions: {
    queries: {
      retry: (failureCount, error: unknown) => {
        const err = error as { status?: number; response?: { status?: number } };
        const status = err?.status ?? err?.response?.status;
        if (status === 401 || status === 403 || status === 503) return false;
        return failureCount < 1;
      },
      refetchOnWindowFocus: false,
    },
  },
});

interface NavSection {
  title: string;
  items: { to: string; label: string; icon: React.ComponentType<{ className?: string }> }[];
}

const DEV_GUARD_BYPASS_KEY = "WORKOS_DEV_GUARD_BYPASS";

function getDevGuardAllowlist(): string[] {
  const raw = import.meta.env.VITE_DEV_GUARD_ALLOWLIST;
  if (!raw) return [];
  return raw
    .split(",")
    .map((p) => p.trim())
    .filter(Boolean)
    .map((p) => (p.startsWith("/") ? p : `/${p}`));
}

function isDevGuardBypassEnabled(): boolean {
  if (import.meta.env.VITE_DEV_GUARD_BYPASS === "true") return true;
  try {
    return globalThis.sessionStorage?.getItem(DEV_GUARD_BYPASS_KEY) === "1";
  } catch {
    return false;
  }
}

function setDevGuardBypass(enabled: boolean): void {
  try {
    if (enabled) {
      globalThis.sessionStorage?.setItem(DEV_GUARD_BYPASS_KEY, "1");
    } else {
      globalThis.sessionStorage?.removeItem(DEV_GUARD_BYPASS_KEY);
    }
  } catch {
    // noop
  }
}

function isAllowedByDevAllowlist(pathname: string, allowlist: string[]): boolean {
  return allowlist.some((allowedPath) => {
    if (allowedPath === pathname) return true;
    return pathname.startsWith(`${allowedPath}/`);
  });
}

const navSections: NavSection[] = [
  {
    title: "Operațiuni",
    items: [
      { to: "/dashboard", label: "Control Tower", icon: LayoutDashboard },
      { to: "/shop-floor", label: "Shop Floor", icon: Factory },
      { to: "/operator", label: "Operator", icon: User },
      { to: "/tablet", label: "Atelier Tablet", icon: Zap },
    ],
  },
  {
    title: "Comercial",
    items: [
      { to: "/clients", label: "Clienți", icon: Users },
      { to: "/intake", label: "Work Intake", icon: Inbox },
      { to: "/quotes", label: "Oferte", icon: FileText },
      { to: "/orders", label: "Comenzi", icon: ClipboardList },
      { to: "/execution", label: "Execuție", icon: Activity },
      { to: "/documents", label: "Documente", icon: FileText },
    ],
  },
  {
    title: "Resurse",
    items: [
      { to: "/inventory", label: "Inventar & OC", icon: Warehouse },
      { to: "/inventory/pricing", label: "Pricing", icon: BarChart3 },
      { to: "/product-system/products", label: "Product System", icon: Package },
      { to: "/colaboratori", label: "Colaboratori", icon: Handshake },
      { to: "/utilaje", label: "Utilaje", icon: Cog },
      { to: "/reports", label: "Rapoarte", icon: BarChart3 },
    ],
  },
  {
    title: "Personal",
    items: personalNavItems,
  },
  {
    title: "Sistem",
    items: [
      { to: "/modules", label: "Harta sistemelor", icon: GitBranch },
      { to: "/governance", label: "Guvernanța sistemului", icon: Shield },
      { to: "/settings", label: "Setări", icon: Settings },
    ],
  },
];

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
        <div className="absolute right-0 top-10 w-56 bg-[#1A2236] border border-[#2A3548] rounded-lg shadow-xl overflow-hidden z-50">
          <div className="px-3 py-2.5 border-b border-[#2A3548]">
            <p className="text-[12px] font-semibold text-slate-200 truncate">{displayName}</p>
            <p className="text-[10px] text-slate-500 uppercase tracking-wide mt-0.5">Autentificat</p>
          </div>
          <button
            onClick={() => {
              setOpen(false);
              logout();
            }}
            className="w-full flex items-center gap-2 px-3 py-2.5 text-[12px] text-slate-300 hover:bg-red-900/20 hover:text-red-300 transition-colors text-left"
          >
            <LogOut className="w-3.5 h-3.5" />
            Deconectare
          </button>
        </div>
      )}
    </div>
  );
}

function AppShell() {
  const location = useLocation();
  const [collapsed, setCollapsed] = useState(false);
  // UI-TRUTH-01C: never show mock "N critical" as real incidents.
  const criticalAlerts = resolveShellCriticalCount(isMockEnabled(), productionAlerts);

  return (
    <div
      className="flex h-screen bg-[#0A0F1C] text-slate-200 overflow-hidden"
      data-testid="workos-desktop-shell"
      style={{ "--workos-sidebar-width": collapsed ? "60px" : "220px" } as React.CSSProperties}
    >
      {/* Sidebar */}
      <aside
        data-testid="workos-sidebar"
        className={`relative z-30 flex shrink-0 flex-col border-r border-[#1E293B] bg-[#0D1321] transition-all duration-200 ${
          collapsed ? "w-[60px]" : "w-[220px]"
        }`}
      >
        {/* Logo */}
        <div className="flex items-center gap-2 px-4 h-[48px] border-b border-[#1E293B]">
          <Zap className="w-5 h-5 text-blue-400 shrink-0" />
          {!collapsed && <span className="text-[15px] font-bold tracking-tight text-slate-100">WorkOS</span>}
        </div>

        {/* Nav */}
        <nav className="flex-1 py-2 px-2 overflow-y-auto scrollbar-thin">
          {navSections.map((section) => (
            <div key={section.title} className="mb-2">
              {!collapsed && (
                <p className="px-3 pt-2 pb-1 text-[9px] font-bold uppercase tracking-widest text-slate-600">
                  {section.title}
                </p>
              )}
              <div className="space-y-0.5">
                {section.items.map((item) => (
                  <NavLink
                    key={item.to}
                    to={item.to}
                    end={
                      item.to === "/inventory" || item.to === "/product-system/products"
                        ? false
                        : true
                    }
                    className={({ isActive }) =>
                      `flex items-center gap-3 px-3 py-2 rounded-md text-[13px] font-medium transition-colors ${
                        isActive
                          ? "bg-blue-600/15 text-blue-400 border-l-2 border-blue-500"
                          : "text-slate-400 hover:text-slate-200 hover:bg-slate-800/50 border-l-2 border-transparent"
                      }`
                    }
                  >
                    <item.icon className="w-4 h-4 shrink-0" />
                    {!collapsed && <span>{item.label}</span>}
                  </NavLink>
                ))}
              </div>
            </div>
          ))}
        </nav>

        {/* Runtime release version indicator (Sprint #38) */}
        <VersionBadge collapsed={collapsed} />

        {/* Collapse toggle */}
        <button
          onClick={() => setCollapsed(!collapsed)}
          className="flex items-center justify-center h-10 border-t border-[#1E293B] text-slate-500 hover:text-slate-300 transition-colors"
        >
          {collapsed ? <ChevronRight className="w-4 h-4" /> : <ChevronLeft className="w-4 h-4" />}
        </button>
      </aside>

      {/* Main */}
      <div className="flex-1 flex flex-col overflow-hidden">
        {/* Top bar */}
        <header
          data-testid="workos-desktop-topbar"
          className="flex items-center justify-between h-[48px] px-4 border-b border-[#1E293B] bg-[#0D1321]"
        >
          <div className="flex items-center gap-2 bg-[#111827] rounded-md px-3 py-1.5 w-72">
            <Search className="w-3.5 h-3.5 text-slate-500" />
            <input
              id="app-global-search"
              name="app-global-search"
              type="text"
              placeholder="Search jobs, tasks, machines..."
              aria-label="Search jobs, tasks, machines"
              className="bg-transparent text-[12px] text-slate-300 placeholder:text-slate-600 outline-none w-full"
            />
          </div>
          <div className="flex items-center gap-3">
            {criticalAlerts > 0 && (
              <div className="flex items-center gap-1 px-2 py-1 bg-red-900/30 border border-red-800/50 rounded text-red-400 text-[11px] font-semibold">
                <AlertTriangle className="w-3 h-3" />
                {criticalAlerts} critical
              </div>
            )}
            <button className="relative p-1.5 rounded hover:bg-slate-800 transition-colors">
              <Bell className="w-4 h-4 text-slate-400" />
              {criticalAlerts > 0 && (
                <span className="absolute -top-0.5 -right-0.5 w-2 h-2 bg-red-500 rounded-full" />
              )}
            </button>
            <div className="pl-3 border-l border-[#1E293B]">
              <UserMenu />
            </div>
          </div>
        </header>

        {/* Environment Banner */}
        <EnvironmentBanner />

        {/* Content */}
        <main className="relative z-0 flex-1 overflow-auto p-4">
          <Routes location={location} key={location.pathname}>
            <Route path="/" element={<Navigate to="/dashboard" replace />} />
            <Route path="/dashboard" element={<Dashboard />} />
            <Route path="/shop-floor" element={<ShopFloor />} />
            <Route path="/operator" element={<OperatorView />} />
            <Route path="/tablet" element={<TabletStationSelector />} />
            <Route path="/tablet/:stationId" element={<TabletStationQueue />} />
            <Route path="/tablet/:stationId/:taskId" element={<TabletTaskDetail />} />
            <Route path="/clients" element={<Clients />} />
              <Route path="/clients/:clientName" element={<ClientWorkspace />} />
              <Route path="/documents" element={<DocumentCenter />} />
              <Route path="/intake" element={<WorkIntake />} />
              <Route path="/intake/:id" element={<IntakeLegacyRoute />} />
              <Route path="/quotes/:quoteId" element={<ErrorBoundary fallbackTitle="Eroare în Oferte"><Quotes /></ErrorBoundary>} />
              <Route path="/quotes" element={<ErrorBoundary fallbackTitle="Eroare în Oferte"><Quotes /></ErrorBoundary>} />
              <Route path="/orders/:orderId" element={<ErrorBoundary fallbackTitle="Eroare în Comenzi"><Orders /></ErrorBoundary>} />
              <Route path="/orders" element={<ErrorBoundary fallbackTitle="Eroare în Comenzi"><Orders /></ErrorBoundary>} />
              <Route path="/execution" element={<ExecutionDashboard />} />
              <Route path="/execution/reality-review" element={<OperationalRealityReview />} />
              <Route path="/execution/:order_id" element={<ExecutionDetail />} />
              <Route path="/demo/commercial-spine" element={<CommercialSpineDemo />} />
              <Route path="/demo/volumetric-letter-preview" element={<VolumetricLetterPreviewDemo />} />
              {/* V6 is the only active intake operator flow. */}
              <Route path="/intake-v6/operator" element={<IntakeV6OperatorWorkspaceApp />} />
              <Route path="/intake-v6/:workspaceId/operator" element={<IntakeV6OperatorWorkspaceApp />} />
              <Route path="/inventory" element={<Inventory />} />
              <Route path="/inventory/pricing" element={<Pricing />} />
              <Route path="/inventory/material-price-registry" element={<Navigate to="/inventory/pricing" replace />} />
              <Route path="/inventory/commercial-markup-policy" element={<Navigate to="/inventory/pricing" replace />} />
              <Route path="/inventory/productsystem-pricing-preview" element={<Navigate to="/inventory/pricing" replace />} />
              <Route path="/product-system" element={
                  <ErrorBoundary fallbackTitle="Eroare în ProductSystem">
                    <ProductSystemLayout />
                  </ErrorBoundary>
                }
              >
                <Route index element={<ProductSystemIndexRedirect />} />
                <Route path="products" element={<ProductSystem />} />
                <Route path="products/:templateCode" element={<ProductSystem />} />
                <Route path="components" element={<ProductSystemPlannedSectionPage section="components" />} />
                <Route path="resources" element={<ProductSystemPlannedSectionPage section="resources" />} />
                <Route path="operations" element={<ProductSystemPlannedSectionPage section="operations" />} />
                <Route path="dependencies" element={<ProductSystemPlannedSectionPage section="dependencies" />} />
                <Route path="validation" element={<ProductSystemPlannedSectionPage section="validation" />} />
                <Route path="advanced" element={<ProductSystemPlannedSectionPage section="advanced" />} />
              </Route>
              <Route
                path="/product-system/blueprint-dossier"
                element={
                  <ErrorBoundary fallbackTitle="Eroare în Blueprint Dossier Studio">
                    <Suspense fallback={<div className="flex items-center justify-center py-20"><div className="animate-spin rounded-full h-10 w-10 border-b-2 border-purple-500" /></div>}>
                      <BlueprintDossierStudio />
                    </Suspense>
                  </ErrorBoundary>
                }
              />
              {/* Legacy Dossier completion → single canonical Blueprint Dossier */}
              <Route
                path="/product-system/dossier-completion"
                element={<Navigate to="/product-system/blueprint-dossier" replace />}
              />
              <Route path="/pricing" element={<Navigate to="/inventory/pricing" replace />} />
              <Route
                path="/product-system/output-blocks-preview"
                element={
                  <ErrorBoundary fallbackTitle="Eroare în Output Blocks Preview">
                    <Suspense fallback={<div className="flex items-center justify-center py-20"><div className="animate-spin rounded-full h-10 w-10 border-b-2 border-purple-500" /></div>}>
                      <OutputBlocksPreview />
                    </Suspense>
                  </ErrorBoundary>
                }
              />
              <Route path="/products" element={<Navigate to="/product-system/products" replace />} />
              <Route path="/templates" element={<Navigate to="/product-system/products" replace />} />
              <Route path="/personal" element={<Navigate to="/employees" replace />} />
              <Route path="/employees" element={<Employees />} />
              <Route path="/employees-records" element={<EmployeesRecords />} />
              <Route path="/employees-records/:employeeId" element={<EmployeeProfile />} />
              <Route path="/attendance" element={<Attendance />} />
              <Route path="/attendance/effects" element={<EmployeeAttendanceEffects />} />
              <Route path="/employee-payments" element={<EmployeePayments />} />
              <Route path="/employee-advances" element={<EmployeeAdvances />} />
              <Route path="/colaboratori" element={<Colaboratori />} />
              <Route path="/utilaje" element={<Utilaje />} />
              <Route path="/reports" element={<Reports />} />
              <Route path="/reports/operational" element={<OperationalReports />} />
              <Route path="/modules" element={<ModuleChain />} />
              <Route path="/governance" element={<Governance />} />
            <Route path="/settings" element={<SettingsPage />} />
            <Route path="*" element={<Navigate to="/dashboard" replace />} />
          </Routes>
        </main>
      </div>
    </div>
  );
}

function RuntimeStatePanel({
  title,
  description,
  actions,
}: {
  title: string;
  description: string;
  actions?: React.ReactNode;
}) {
  return (
    <div className="min-h-[65vh] flex items-center justify-center">
      <div className="max-w-xl w-full rounded-xl border border-[#1E293B] bg-[#111827] p-6">
        <h2 className="text-[18px] font-semibold text-slate-100">{title}</h2>
        <p className="text-[13px] text-slate-400 mt-2">{description}</p>
        {actions ? <div className="mt-4 flex items-center gap-2 flex-wrap">{actions}</div> : null}
      </div>
    </div>
  );
}

function RuntimeProtectedOutlet() {
  const { authState, login } = useAuth();
  const location = useLocation();
  const allowlist = getDevGuardAllowlist();
  const bypassEnabled = isDevGuardBypassEnabled();

  const allowlistHit = isAllowedByDevAllowlist(location.pathname, allowlist);

  if (authState === "authenticated") {
    return <Outlet />;
  }

  if (authState === "dev_auth_enabled" && (bypassEnabled || allowlistHit)) {
    return <Outlet />;
  }

  if (authState === "dev_auth_enabled") {
    return (
      <RuntimeStatePanel
        title="DEV auth activ fără sesiune reală"
        description="Cereri protejate sunt blocate până la o sesiune reală. Poți continua temporar în preview (bypass) sau permite doar anumite rute prin allow-list, fără a schimba auth real."
        actions={
          <>
            <button
              onClick={() => login()}
              className="px-3 py-1.5 rounded border border-blue-700 bg-blue-900/20 text-blue-300 text-[12px]"
            >
              Încearcă login real
            </button>
            <button
              onClick={() => {
                setDevGuardBypass(true);
                globalThis.location.reload();
              }}
              className="px-3 py-1.5 rounded border border-amber-700 bg-amber-900/20 text-amber-300 text-[12px]"
            >
              Bypass temporar preview
            </button>
            <button
              onClick={() => {
                setDevGuardBypass(false);
                globalThis.location.reload();
              }}
              className="px-3 py-1.5 rounded border border-slate-700 bg-slate-800 text-slate-300 text-[12px]"
            >
              Oprește bypass
            </button>
          </>
        }
      />
    );
  }

  if (authState === "auth_config_missing") {
    return (
      <RuntimeStatePanel
        title="Configurație auth backend lipsă"
        description="Autentificarea nu poate fi finalizată în acest mediu. UI oprește requesturile protejate pentru a evita loop-uri și noise runtime."
      />
    );
  }

  return <Navigate to="/" replace />;
}

/** Employee Mobile PWA — outside desktop WorkOS shell (no sidebar/topbar). */
export function EmployeeMobileStandaloneRoot() {
  return (
    <div
      className="min-h-screen w-full bg-[#0A0F1C] text-slate-200 overflow-x-hidden"
      data-testid="employee-mobile-standalone-root"
    >
      <EmployeeMobileApp />
    </div>
  );
}

/** Employee Mobile v2 prototype — parallel route, does not replace v1. */
export function EmployeeMobileV2StandaloneRoot() {
  return (
    <div
      className="min-h-screen w-full bg-[#0B1120] text-slate-100 overflow-x-hidden"
      data-testid="employee-mobile-v2-standalone-root"
    >
      <ErrorBoundary fallbackTitle="A apărut o problemă la încărcarea aplicației mobile.">
        <EmployeeMobileV2App />
      </ErrorBoundary>
    </div>
  );
}

/** Intake V6 operator — V4 UI shell with V6 API surface. */
export function IntakeV6StandaloneRoot() {
  return (
    <div
      className="min-h-screen w-full bg-[#0A0F1A] text-slate-200 overflow-x-hidden"
      data-testid="intake-v6-standalone-root"
    >
      <Routes>
        <Route path="operator" element={<IntakeV6OperatorWorkspaceApp />} />
        <Route path=":workspaceId/operator" element={<IntakeV6OperatorWorkspaceApp />} />
      </Routes>
    </div>
  );
}

export function AuthenticatedAppRoutes() {
  return (
    <Routes>
      <Route element={<RuntimeProtectedOutlet />}>
        <Route path="/employee-app/*" element={<EmployeeMobileStandaloneRoot />} />
        <Route path="/employee-app-v2/*" element={<EmployeeMobileV2StandaloneRoot />} />
        <Route path="/intake-v6-app/*" element={<IntakeV6StandaloneRoot />} />
        <Route path="*" element={<AppShell />} />
      </Route>
    </Routes>
  );
}

function AuthGate() {
  const { loading, authState } = useAuth();

  if (loading) {
    return (
      <div className="min-h-screen flex items-center justify-center bg-[#0A0F1C]">
        <div className="text-center">
          <div className="animate-spin rounded-full h-10 w-10 border-b-2 border-blue-500 mx-auto mb-3"></div>
          <p className="text-[12px] text-slate-500">Se verifică sesiunea...</p>
        </div>
      </div>
    );
  }

  if (authState === "unauthenticated") return <LoginGate />;

  if (authState === "auth_config_missing") {
    return (
      <RuntimeStatePanel
        title="Auth indisponibil în runtime"
        description="Backend-ul a răspuns cu 503 pentru auth config missing. Nu se rulează route-uri protejate până la configurarea OIDC/JWT."
      />
    );
  }

  return <AuthenticatedAppRoutes />;
}

const App = () => (
  <QueryClientProvider client={queryClient}>
    <TooltipProvider>
      <Toaster />
      <Sonner />
      <BrowserRouter future={{ v7_relativeSplatPath: true }}>
        <AuthProvider>
          <Routes>
            <Route path="/auth/callback" element={<AuthCallback />} />
            <Route path="/auth/error" element={<AuthError />} />
            <Route path="/auth/logout" element={<LogoutCallbackPage />} />
            <Route path="/logout-callback" element={<LogoutCallbackPage />} />
            <Route path="*" element={<AuthGate />} />
          </Routes>
        </AuthProvider>
      </BrowserRouter>
    </TooltipProvider>
  </QueryClientProvider>
);

export default App;