import { NavLink, Outlet, Link, useLocation } from "react-router-dom";
import { ExternalLink } from "lucide-react";
import { ProductSystemShellProvider, useProductSystemShell } from "./ProductSystemShellContext";
import {
  PRICING_REGISTRY_PATH,
  PRODUCT_SYSTEM_PLANNED_BADGE_RO,
  PRODUCT_SYSTEM_SHELL_NAV,
} from "./productSystemShellConfig";
import { productSystemShellNavIdForPath } from "./productSystemRouteSync";
import { ProductSystemAuthoringStackBanner } from "./ProductSystemAuthoringStackBanner";
import { PS_SURFACE_QUIET } from "./productSystemSurfaces";

function ProductSystemLayoutInner() {
  const location = useLocation();
  const { canViewAdvanced } = useProductSystemShell();
  const activeNavId = productSystemShellNavIdForPath(location.pathname);

  const visibleNav = PRODUCT_SYSTEM_SHELL_NAV.filter(
    (item) => !item.requiresAdvancedAccess || canViewAdvanced,
  );
  const operationalNav = visibleNav.filter((item) => !item.plannedSection);
  const plannedNav = visibleNav.filter((item) => item.plannedSection);

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
          <div>
            <h1 className="text-base font-bold text-slate-100">Product System</h1>
            <p className="mt-0.5 text-[11px] text-slate-500" data-testid="product-system-shell-subtitle">
              Catalog admin · identitate → lifecycle → compoziție → readiness → publicare
            </p>
          </div>
          <Link
            to={PRICING_REGISTRY_PATH}
            data-testid="product-system-pricing-registry-link"
            className={`inline-flex items-center gap-1.5 ${PS_SURFACE_QUIET} px-2.5 py-1.5 text-[11px] font-medium text-slate-300 transition-colors hover:border-slate-600 hover:text-slate-100`}
          >
            Pricing Registry
            <ExternalLink className="h-3 w-3 shrink-0 opacity-70" aria-hidden />
          </Link>
        </div>
      </div>

      <div className="flex flex-wrap items-end justify-between gap-x-4 gap-y-2 border-b border-slate-800/70 pb-0.5">
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
                    ? `border border-b-0 border-[#1E293B] bg-[#111827] text-slate-100`
                    : "text-slate-500 hover:text-slate-300"
                }`
              }
            >
              <span>{item.label}</span>
            </NavLink>
          ))}
        </nav>

        {plannedNav.length > 0 ? (
          <nav
            aria-label="Secțiuni în dezvoltare"
            className="flex flex-wrap items-center gap-1 pb-1"
            data-testid="product-system-shell-nav-planned"
          >
            <span
              className="mr-1 text-[10px] font-medium uppercase tracking-wide text-slate-600"
              data-testid="product-system-shell-planned-cluster-label"
            >
              {PRODUCT_SYSTEM_PLANNED_BADGE_RO}
            </span>
            {plannedNav.map((item) => (
              <NavLink
                key={item.id}
                to={item.path}
                end
                data-testid={`product-system-shell-nav-${item.id}`}
                data-planned="true"
                className={({ isActive }) =>
                  `inline-flex items-center rounded px-2 py-1 text-[11px] font-medium transition-colors ${
                    item.id === "advanced" ? "ml-1 border-l border-slate-800/80 pl-3" : ""
                  } ${
                    isActive
                      ? "bg-slate-900/50 text-slate-400"
                      : "text-slate-600 hover:text-slate-500"
                  }`
                }
              >
                <span>{item.label}</span>
              </NavLink>
            ))}
          </nav>
        ) : null}
      </div>

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
