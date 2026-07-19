import fs from "fs";
import path from "path";
import { fileURLToPath } from "url";

const dir = path.dirname(fileURLToPath(import.meta.url));

function load(f) {
  let t = fs.readFileSync(path.join(dir, f), "utf8");
  if (t.charCodeAt(0) === 0xfeff) t = t.slice(1);
  return JSON.parse(t);
}

function walkLines(o, out = []) {
  if (!o || typeof o !== "object") return out;
  if (Array.isArray(o)) {
    for (const x of o) walkLines(x, out);
    return out;
  }
  const name = o.display_name || o.material_name || o.label || o.line_label || o.name;
  if (name && /montaj|sablon|accesor|connector|cablu|template|acp_|acm_/i.test(String(name))) {
    out.push({
      name,
      quantity: o.quantity,
      unit_price: o.unit_price,
      cost: o.material_cost ?? o.estimated_cost ?? o.line_total,
      src: o.price_source || o.registry_code || o.line_code || o.material_key,
    });
  }
  for (const k of Object.keys(o)) walkLines(o[k], out);
  return out;
}

for (const f of [
  "acm_finish_setup_slice.json",
  "acm_priced_quote_dry_run.json",
  "acm_task_preview.json",
  "acm_runtime_capture_read_model.json",
  "acm_product_definition.json",
  "acm_product_aggregate.json",
]) {
  if (!fs.existsSync(path.join(dir, f))) {
    console.log("missing", f);
    continue;
  }
  const j = load(f);
  console.log("\n===", f, "top", Object.keys(j).slice(0, 40).join(","));
  if (f.includes("finish")) {
    console.log({
      scope: j.mounting_scope,
      template: [j.mounting_template_enabled, j.mounting_template_material_type, j.mounting_template_area_m2],
      sol: [j.mounting_solution?.kind, j.mounting_solution?.template_code],
      seg: j.segmented_background?.status ?? j.segmented_background,
      support: [j.svg_support_selection?.status, j.svg_support_selection?.role],
      bindings: j.binding_roles,
      cable: j.mains_cable_length_m,
      corner: j.power_supply_service_corner,
    });
  }
  if (f.includes("priced")) {
    const s = JSON.stringify(j);
    console.log({
      Accesorii: /Accesorii montaj/i.test(s),
      Tarife: /Tarife lips/i.test(s),
      sablon: /sablon_montaj/i.test(s),
      montaj_line: /"line_code"\s*:\s*"montaj"/.test(s),
      gate: j.gate || j.status || j.ready || j.composition_confirmed,
    });
    console.log("montaj-ish lines", walkLines(j).slice(0, 40));
    const blockers = j.blockers || j.blocker_codes || j.errors || j.gate_blockers || [];
    console.log("blockers", JSON.stringify(blockers).slice(0, 800));
  }
  if (f.includes("task")) {
    console.log(JSON.stringify(j).slice(0, 1500));
  }
  if (f.includes("capture")) {
    const s = JSON.stringify(j);
    console.log(
      "MOUNTING",
      [...new Set([...s.matchAll(/MOUNTING_[A-Z_]+/g)].map((x) => x[0]))],
    );
    console.log(JSON.stringify(j).slice(0, 1800));
  }
  if (f.includes("product_definition")) {
    const s = JSON.stringify(j);
    for (const key of [
      "mounting_scope",
      "mounting_solution",
      "segmented",
      "service_corner",
      "mains_cable",
      "fixing",
      "svg_support",
      "ALUCOBOND",
    ]) {
      console.log(key, s.includes(key));
    }
  }
  if (f.includes("aggregate")) {
    const s = JSON.stringify(j);
    console.log({
      mounting: /mounting/i.test(s),
      segmented: /segmented/i.test(s),
      task_rules: /task_rule/i.test(s),
      forex_template: /sablon|forex|template/i.test(s),
    });
  }
}
