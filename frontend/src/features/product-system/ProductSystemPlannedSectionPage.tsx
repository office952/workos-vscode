import { Link } from "react-router-dom";
import {
  PRODUCT_SYSTEM_PLANNED_BADGE_RO,
  PRODUCT_SYSTEM_PLANNED_SECTION_MESSAGE,
  PRODUCT_SYSTEM_PRODUCTS_PATH,
  type ProductSystemShellNavId,
} from "./productSystemShellConfig";
import { PS_SURFACE_QUIET } from "./productSystemSurfaces";

const SECTION_TITLES: Record<ProductSystemShellNavId, string> = {
  products: "Products",
  components: "Components",
  resources: "Resources",
  operations: "Operations",
  dependencies: "Dependencies",
  validation: "Validation",
  advanced: "Advanced",
};

export default function ProductSystemPlannedSectionPage({
  section,
}: {
  section: ProductSystemShellNavId;
}) {
  return (
    <div
      data-testid="product-system-planned-section"
      data-section={section}
      data-operational="false"
      className={`${PS_SURFACE_QUIET} border-dashed p-8 text-center`}
    >
      <div className="mb-3 flex flex-wrap items-center justify-center gap-2">
        <span
          data-testid="product-system-planned-section-badge"
          className="text-[10px] font-medium uppercase tracking-wide text-slate-500"
        >
          {PRODUCT_SYSTEM_PLANNED_BADGE_RO}
        </span>
        <span className="text-[11px] text-slate-600">Secțiune neoperațională</span>
      </div>
      <h2 className="text-base font-semibold text-slate-300">{SECTION_TITLES[section]}</h2>
      <p
        data-testid="product-system-planned-section-message"
        className="mx-auto mt-3 max-w-lg text-sm leading-relaxed text-slate-500"
      >
        {PRODUCT_SYSTEM_PLANNED_SECTION_MESSAGE}
      </p>
      <Link
        to={PRODUCT_SYSTEM_PRODUCTS_PATH}
        className="mt-6 inline-block text-sm text-blue-400 hover:text-blue-300"
      >
        Înapoi la Products
      </Link>
    </div>
  );
}
