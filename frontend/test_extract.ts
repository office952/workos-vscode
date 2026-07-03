import { readFileSync } from 'fs';

// Let's just copy the function here to test it
function isCanonicalSnapshot(obj: any): boolean {
  if (!obj || typeof obj !== "object" || Array.isArray(obj)) return false;
  return (
    "product_definition" in obj && ("cost_result" in obj || "pricing" in obj || "price" in obj)
  );
}

function deriveLineItemsFromCanonical(snapshot: any): any[] {
  const costResult = snapshot.cost_result;
  if (!costResult) return [];

  const breakdown: any[] = Array.isArray(costResult.breakdown) ? costResult.breakdown : [];

  if (breakdown.length > 0) {
    return breakdown.map((bl: any, i: number) => ({
      productCode: bl.type ?? `COST-${i + 1}`,
      description: bl.name ?? bl.type ?? "Cost line",
      quantity: Number(bl.quantity ?? 1),
      unit_price: Number(bl.unit_cost ?? 0),
      unitPrice: Number(bl.unit_cost ?? 0),
      total: Number(bl.total ?? 0),
    }));
  }

  if (costResult.total_cost > 0) {
    return [
      {
        productCode: "TOTAL-COST",
        description: `Total cost (${costResult.currency ?? "RON"})`,
        quantity: 1,
        unit_price: Number(costResult.total_cost),
        unitPrice: Number(costResult.total_cost),
        total: Number(costResult.total_cost),
      },
    ];
  }
  return [];
}

function deriveBreakdownFromCanonical(snapshot: any): any[] | undefined {
  const costResult = snapshot.cost_result;
  if (!costResult) return undefined;

  const productDef = snapshot.product_definition;
  if (productDef && Array.isArray(productDef.layers) && productDef.layers.length > 0) {
    const components: any[] = productDef.layers.map((layer: any) => ({
      component_id: layer.layer_id ?? layer.id ?? "unknown",
      type: layer.layer_type ?? "layer",
      name: layer.layer_type ?? "Layer",
      material_cost: Number(costResult.materials_cost ?? 0) / productDef.layers.length,
      operation_cost: Number(costResult.labour_cost ?? 0) / productDef.layers.length,
      total_component_cost:
        (Number(costResult.materials_cost ?? 0) + Number(costResult.labour_cost ?? 0)) /
        productDef.layers.length,
      materials_detail: [],
      operations_detail: [],
      errors: [],
      warnings: [],
    }));
    return components.length > 0 ? components : undefined;
  }
  return undefined;
}

function extractQuotePayload(raw?: string): any {
  if (!raw) return { lineItemsRaw: [] };
  let parsed: any;
  try {
    parsed = JSON.parse(raw);
  } catch {
    return { lineItemsRaw: [] };
  }

  if (isCanonicalSnapshot(parsed)) {
    const lineItemsRaw = deriveLineItemsFromCanonical(parsed);
    const componentBreakdown = deriveBreakdownFromCanonical(parsed);
    return { lineItemsRaw, componentBreakdown };
  }

  if (parsed && !Array.isArray(parsed) && typeof parsed === "object") {
    if (parsed.line_items && !Array.isArray(parsed.line_items) && isCanonicalSnapshot(parsed.line_items)) {
      const lineItemsRaw = deriveLineItemsFromCanonical(parsed.line_items);
      const componentBreakdown =
        deriveBreakdownFromCanonical(parsed.line_items) ??
        (Array.isArray(parsed.component_breakdown) && parsed.component_breakdown.length > 0
          ? parsed.component_breakdown
          : undefined);
      return { lineItemsRaw, componentBreakdown };
    }

    const lineItemsRaw = Array.isArray(parsed.line_items) ? parsed.line_items : [];
    const cb = parsed.component_breakdown;
    const componentBreakdown =
      Array.isArray(cb) && cb.length > 0 ? cb : undefined;

    if (lineItemsRaw.length === 0 && isCanonicalSnapshot(parsed)) {
      return {
        lineItemsRaw: deriveLineItemsFromCanonical(parsed),
        componentBreakdown: deriveBreakdownFromCanonical(parsed) ?? componentBreakdown,
      };
    }

    return { lineItemsRaw, componentBreakdown };
  }

  if (Array.isArray(parsed)) {
    return { lineItemsRaw: parsed };
  }

  return { lineItemsRaw: [] };
}

const shapeB = JSON.stringify({
  line_items: [{ productCode: "A", description: "A", quantity: 1, unit_price: 10, total: 10 }],
  component_breakdown: [{ component_id: "1", type: "layer", name: "Layer 1", material_cost: 5, operation_cost: 5, total_component_cost: 10 }]
});

console.log(extractQuotePayload(shapeB));

