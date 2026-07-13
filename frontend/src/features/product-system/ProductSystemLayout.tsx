import { NavLink, Outlet, Link, useLocation } from "react-router-dom";
import { ExternalLink } from "lucide-react";
import { ProductSystemShellProvider, useProductSystemShell } from "./ProductSystemShellContext";
import {
  PRICING_REGISTRY_PATH,
  PRODUCT_SYSTEM_SHELL_NAV,
} from "./productSystemShellConfig";
import { productSystemShellNavIdForPath } from "./productSystemRouteSync";

function ProductSystemLayoutInner() {
  const location = useLocation();
  const { canViewAdvanced } = useProductSystemShell();
  const activeNavId = productSystemShellNavIdForPath(location.pathname);

  const visibleNav = PRODUCT_SYSTEM_SHELL_NAV.filter(
    (item) => !item.requiresAdvancedAccess || canViewAdvanced,
  );

  return (
    <div className="space-y-4" data-testid="product-system-shell">
      <div className="space-y-1">
        <nav
          aria-label="Product System breadcrumb"
          className="text-[11px] text-slate-500"
          data-testid="product-system-breadcrumb"
        >
          <span className="text-slate-400">Product System</span>
          {activeNavId && activeNavId !== "products" ? (
            <>
              <span className="mx-1.5 text-slate-600">/</span>
              <span className="text-slate-300">
                {PRODUCT_SYSTEM_SHELL_NAV.find((item) => item.id === activeNavId)?.label}
              </span>
            </>
          ) : null}
        </nav>
        <div className="flex flex-wrap items-center justify-between gap-3">
          <h1 className="text-base font-bold text-slate-100">Product System</h1>
          <Link
            to={PRICING_REGISTRY_PATH}
            data-testid="product-system-pricing-registry-link"
            className="inline-flex items-center gap-1.5 rounded-md border border-slate-700/80 bg-slate-900/60 px-2.5 py-1.5 text-[11px] font-medium text-slate-300 transition-colors hover:border-slate-600 hover:text-slate-100"
          >
            Pricing Registry
            <ExternalLink className="h-3 w-3 shrink-0 opacity-70" />
          </Link>
        </div>
      </div>

      <nav
        aria-label="Product System sections"
        className="flex flex-wrap gap-1 border-b border-slate-800/80 pb-0.5"
        data-testid="product-system-shell-nav"
      >
        {visibleNav.map((item) => (
          <NavLink
            key={item.id}
            to={item.path}
            end={item.id !== "products"}
            data-testid={`product-system-shell-nav-${item.id}`}
            className={({ isActive }) =>
              `rounded-t-md px-3 py-2 text-[12px] font-medium transition-colors ${
                isActive
                  ? "border border-b-0 border-slate-700 bg-slate-900/80 text-slate-100"
                  : "text-slate-500 hover:text-slate-300"
              } ${item.id === "advanced" ? "ml-auto border-l border-slate-800/80 pl-4" : ""}`
            }
          >
            {item.label}
          </NavLink>
        ))}
      </nav>

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
