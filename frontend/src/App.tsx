import { Toaster } from "@/components/ui/toaster";
import { Toaster as Sonner } from "@/components/ui/sonner";
import { TooltipProvider } from "@/components/ui/tooltip";
import { QueryClient, QueryClientProvider } from "@tanstack/react-query";
import { BrowserRouter, Routes, Route, Navigate, Outlet, useLocation } from "react-router-dom";
import { lazy, Suspense } from "react";
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
import LettersFaceStructureDetailPage from "./features/product-system/LettersFaceStructureDetailPage";
import LettersVolumeAluminumStructureDetailPage from "./features/product-system/LettersVolumeAluminumStructureDetailPage";
import LettersBackForexStructureDetailPage from "./features/product-system/LettersBackForexStructureDetailPage";
import LettersLedStructureDetailPage from "./features/product-system/LettersLedStructureDetailPage";
import AcmBoxedStructureDetailPage from "./features/product-system/AcmBoxedStructureDetailPage";
import LettersAcmCompositionConnectionPricesPage from "./features/product-system/LettersAcmCompositionConnectionPricesPage";
import LettersAcmComposerIaMockPage from "./features/product-system/LettersAcmComposerIaMockPage";
import Clients from "./pages/Clients";
import ClientWorkspace from "./pages/ClientWorkspace";
import DocumentCenter from "./pages/DocumentCenter";
import { TabletStationSelector, TabletStationQueue, TabletTaskDetail } from "./pages/TabletMode";
const BlueprintDossierStudio = lazy(() => import("./pages/BlueprintDossierStudio"));
const OutputBlocksPreview = lazy(() => import("./pages/OutputBlocksPreview"));
import ErrorBoundary from "./components/ErrorBoundary";
import ExecutionDashboard from "./pages/ExecutionDashboard";
import ExecutionDetail from "./pages/ExecutionDetail";
import MaterializedOpsGraph from "./pages/MaterializedOpsGraph";
import OperationalRealityReview from "./pages/OperationalRealityReview";
import OperationalReports from "./pages/OperationalReports";
import CommercialSpineDemo from "./pages/CommercialSpineDemo";
import VolumetricLetterPreviewDemo from "./pages/VolumetricLetterPreviewDemo";
// Deprecated intake entrypoints removed; Intake V6 is the active dedicated workspace.
// WorkIntakeProductDefinitionDemo was referenced but never shipped on disk — removed to restore boot.
import IntakeV6OperatorWorkspaceApp from "./pages/IntakeV6OperatorWorkspaceApp";
import AuthCallback from "./pages/AuthCallback";
import AuthError from "./pages/AuthError";
import LogoutCallbackPage from "./pages/LogoutCallbackPage";
import LoginGate from "./components/LoginGate";
import { AuthProvider, useAuth } from "./contexts/AuthContext";
import { ThemeProvider } from "./contexts/ThemeContext";
import LocalApiCompatibilityBanner from "./components/workos/LocalApiCompatibilityBanner";
import AppShell from "./components/workos/AppShell";

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
      <div className="max-w-xl w-full rounded-xl border border-wo-border-subtle bg-wo-surface-raised p-6">
        <h2 className="text-[18px] font-semibold text-wo-text-primary">{title}</h2>
        <p className="text-[13px] text-wo-text-muted mt-2">{description}</p>
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
        <Route element={<AppShell />}>
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
          <Route path="/execution/ops-graph" element={<MaterializedOpsGraph />} />
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
            <Route
              path="products/:templateCode/structure/vizual-fata"
              element={<LettersFaceStructureDetailPage />}
            />
            <Route
              path="products/:templateCode/structure/volum-aluminiu"
              element={<LettersVolumeAluminumStructureDetailPage />}
            />
            <Route
              path="products/:templateCode/structure/capac-spate"
              element={<LettersBackForexStructureDetailPage />}
            />
            <Route
              path="products/:templateCode/structure/sistem-led"
              element={<LettersLedStructureDetailPage />}
            />
            <Route
              path="products/:templateCode/structure/conexiune-litere-acm-preturi"
              element={<LettersAcmCompositionConnectionPricesPage />}
            />
            <Route
              path="products/:templateCode/structure/composer-litere-acm"
              element={<LettersAcmComposerIaMockPage />}
            />
            <Route
              path="products/:templateCode/structure/:stepId"
              element={<AcmBoxedStructureDetailPage />}
            />
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
        </Route>
      </Route>
    </Routes>
  );
}

function AuthGate() {
  const { loading, authState } = useAuth();

  if (loading) {
    return (
      <div className="min-h-screen flex items-center justify-center bg-wo-surface-app">
        <div className="text-center">
          <div className="animate-spin rounded-full h-10 w-10 border-b-2 border-primary mx-auto mb-3"></div>
          <p className="text-[12px] text-wo-text-dim">Se verifică sesiunea...</p>
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
  <ThemeProvider defaultTheme="light">
    <QueryClientProvider client={queryClient}>
      <TooltipProvider>
        <Toaster />
        <Sonner />
        {/* DEV-only stale/wrong backend banner — outside shell so Intake V6 sees it too */}
        <LocalApiCompatibilityBanner />
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
  </ThemeProvider>
);

export default App;
