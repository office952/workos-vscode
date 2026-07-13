import { Link } from "react-router-dom";
import {
  PRODUCT_SYSTEM_PLANNED_SECTION_MESSAGE,
  PRODUCT_SYSTEM_PRODUCTS_PATH,
  type ProductSystemShellNavId,
} from "./productSystemShellConfig";

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
      className="rounded-xl border border-slate-800/60 bg-slate-950/20 p-8 text-center"
    >
      <h2 className="text-base font-semibold text-slate-100">{SECTION_TITLES[section]}</h2>
      <p className="mx-auto mt-3 max-w-lg text-sm leading-relaxed text-slate-400">
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
