export type ProductSystemPrimaryTab =
  | "products"
  | "components"
  | "candidate-sets"
  | "dossiers"
  | "guards-audit"
  | "archived";

export const PRODUCT_SYSTEM_PRIMARY_TABS: Array<{
  id: ProductSystemPrimaryTab;
  label: string;
  testId: string;
}> = [
  { id: "products", label: "Products", testId: "product-system-primary-tab-products" },
  { id: "components", label: "Components", testId: "product-system-primary-tab-components" },
  { id: "candidate-sets", label: "Candidate Sets", testId: "product-system-primary-tab-candidate-sets" },
  { id: "dossiers", label: "Dossiers", testId: "product-system-primary-tab-dossiers" },
  { id: "guards-audit", label: "Guards / Audit", testId: "product-system-primary-tab-guards-audit" },
  { id: "archived", label: "Archived", testId: "product-system-primary-tab-archived" },
];

export function getDefaultProductSystemPrimaryTab(): ProductSystemPrimaryTab {
  return "products";
}

export function primaryTabTestId(tab: ProductSystemPrimaryTab): string {
  return `product-system-primary-tab-${tab}`;
}
