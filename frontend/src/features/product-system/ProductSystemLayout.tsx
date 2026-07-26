import { NavLink, Outlet, useLocation } from "react-router-dom";
import { ProductSystemShellProvider, useProductSystemShell } from "./ProductSystemShellContext";
import { PRODUCT_SYSTEM_SHELL_NAV } from "./productSystemShellConfig";
import { productSystemShellNavIdForPath } from "./productSystemRouteSync";
import { ProductSystemAuthoringStackBanner } from "./ProductSystemAuthoringStackBanner";

function ProductSystemLayoutInner() {
  const location = useLocation();
  const { canViewAdvanced } = useProductSystemShell();
  const activeNavId = productSystemShellNavIdForPath(location.pathname);

  // Planned sections stay routable but off primary chrome.
  const operationalNav = PRODUCT_SYSTEM_SHELL_NAV.filter(
    (item) =>
      !item.plannedSection && (!item.requiresAdvancedAccess || canViewAdvanced),
  );
  // One real section today (Workspace) — do not render a lonely tab that repeats the title.
  const showSectionNav = operationalNav.length > 1;
  const onWorkspace =
    activeNavId === "products" ||
    location.pathname === "/product-system" ||
    location.pathname.startsWith("/product-system/products");

  return (
    <div className="space-y-3" data-testid="product-system-shell" data-workspace="blank">
      <header className="flex flex-wrap items-center justify-between gap-2">
        <h1
          className="text-base font-bold text-wo-text-primary"
          data-testid="product-system-shell-title"
        >
          Product System
        </h1>
        {/* Subtitle / breadcrumb / single Workspace tab removed — they duplicated the page header. */}
        <p className="sr-only" data-testid="product-system-shell-subtitle">
          Product Template, Module produs, Product Compiler, Pregătire
        </p>
      </header>

      {showSectionNav ? (
        <div className="border-b border-wo-border-subtle pb-0.5">
          <nav
            aria-label="Product System sections"
            className="flex flex-wrap gap-1"
            data-testid="product-system-shell-nav"
          >
            {operationalNav.map((item) => (
              <NavLink
                key={item.id}
                to={item.path}
                end={item.id !== "products"}
                data-testid={`product-system-shell-nav-${item.id}`}
                data-planned="false"
                className={({ isActive }) =>
                  `inline-flex items-center gap-1.5 rounded-t-md px-3 py-2 text-[12px] font-medium transition-colors ${
                    isActive
                      ? "border border-b-0 border-wo-border-subtle bg-wo-surface-raised text-wo-text-primary"
                      : "text-wo-text-muted hover:text-wo-text-secondary"
                  }`
                }
              >
                <span>{item.label === "Products" ? "Workspace" : item.label}</span>
              </NavLink>
            ))}
          </nav>
        </div>
      ) : (
        <div
          className="hidden"
          data-testid="product-system-shell-nav"
          data-single-section={onWorkspace ? "workspace" : "other"}
        />
      )}

      <ProductSystemAuthoringStackBanner />

      <Outlet />
    </div>
  );
}

export default function ProductSystemLayout() {
  return (
    <ProductSystemShellProvider shellMode>
      <ProductSystemLayoutInner />
    </ProductSystemShellProvider>
  );
}
