import { NavLink, Outlet, useLocation, useParams } from "react-router-dom";
import { ProductSystemShellProvider, useProductSystemShell } from "./ProductSystemShellContext";
import { PRODUCT_SYSTEM_SHELL_NAV } from "./productSystemShellConfig";
import { productSystemShellNavIdForPath } from "./productSystemRouteSync";
import { ProductSystemAuthoringStackBanner } from "./ProductSystemAuthoringStackBanner";
import FlowBreadcrumb, { productsBreadcrumb } from "@/components/workos/FlowBreadcrumb";
import CommercialFlowStrip from "@/components/workos/CommercialFlowStrip";
import NextStepPanel from "@/components/workos/NextStepPanel";
import { productsNextStepHint } from "@/lib/commercialFlowUi";

function ProductSystemLayoutInner() {
  const location = useLocation();
  const { templateCode } = useParams<{ templateCode?: string }>();
  const { canViewAdvanced } = useProductSystemShell();
  const activeNavId = productSystemShellNavIdForPath(location.pathname);
  const nextHint = productsNextStepHint();

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

  const crumbLabel = templateCode
    ? decodeURIComponent(templateCode)
    : undefined;

  return (
    <div className="space-y-3" data-testid="product-system-shell" data-workspace="blank">
      <FlowBreadcrumb items={productsBreadcrumb(crumbLabel)} />
      <CommercialFlowStrip active="produse" />

      <header className="flex flex-wrap items-end justify-between gap-2">
        <div className="min-w-0">
          <h1
            className="text-base font-bold text-wo-text-primary"
            data-testid="product-system-shell-title"
          >
            Produse
          </h1>
          <p
            className="text-[12px] text-wo-text-muted mt-0.5"
            data-testid="product-system-shell-subtitle"
          >
            Structură produs și template-uri — definire înainte de ofertă. Nu este preț client.
          </p>
        </div>
      </header>

      {showSectionNav ? (
        <div className="border-b border-wo-border-subtle pb-0.5">
          <nav
            aria-label="Secțiuni produse"
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
                <span>{item.label === "Products" ? "Produse" : item.label}</span>
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

      {onWorkspace ? (
        <NextStepPanel
          title={nextHint.title}
          description={nextHint.description}
          primaryAction={
            nextHint.primaryLabel && nextHint.primaryTo
              ? { label: nextHint.primaryLabel, to: nextHint.primaryTo }
              : undefined
          }
          secondaryAction={
            nextHint.secondaryLabel && nextHint.secondaryTo
              ? {
                  label: nextHint.secondaryLabel,
                  to: nextHint.secondaryTo,
                  variant: "ghost",
                }
              : undefined
          }
        />
      ) : null}

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
