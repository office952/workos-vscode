import type { ProductAggregate } from "@/api/productAggregate";
import type { ProductTemplateEntity, ProductTemplateModuleLinkEntity } from "@/lib/api";

export type TemplateCatalogKind = "assembly" | "assembly_module" | "reusable_module" | "standalone";
export type TemplateCatalogRelationshipKind =
  | "parent_assembly"
  | "required_module"
  | "optional_module"
  | "mixed_module"
  | "standalone";
export type TemplateCatalogOfferPolicyKind =
  | "assembly_minimum_component"
  | "required_auto_included"
  | "optional_explicit"
  | "mixed_selection"
  | "standalone_individual";

export interface TemplateCatalogEntry {
  templateCode: string;
  kind: TemplateCatalogKind;
  label: string;
  description: string;
  relationshipKind: TemplateCatalogRelationshipKind;
  relationshipLabel: string;
  relationshipDescription: string;
  incomingParentCodes: string[];
  outgoingModuleCodes: string[];
  incomingRelationTypes: string[];
  outgoingRelationTypes: Record<string, string>;
  offerPolicyKind: TemplateCatalogOfferPolicyKind;
  offerPolicyLabel: string;
  offerPolicyDescription: string;
}

function normalizeTemplateCode(code: string | null | undefined): string {
  return String(code ?? "").trim().toUpperCase();
}

function normalizeRelationType(value: string | null | undefined): string {
  const normalized = String(value ?? "required_module").trim().toLowerCase();
  if (!normalized) return "required_module";
  if (normalized.includes("optional")) return "optional_addon";
  if (normalized.includes("required")) return "required_module";
  return normalized;
}

function formatCount(count: number, singular: string, plural: string): string {
  return `${count} ${count === 1 ? singular : plural}`;
}

function resolveRelationshipMeta(
  outgoingModuleCount: number,
  incomingParentCount: number,
  incomingRelationTypes: string[],
): Pick<TemplateCatalogEntry, "relationshipKind" | "relationshipLabel" | "relationshipDescription"> {
  const relationTypes = new Set(incomingRelationTypes);
  const hasRequired = relationTypes.has("required_module");
  const hasOptional = relationTypes.has("optional_addon");

  let relationshipKind: TemplateCatalogRelationshipKind;
  if (outgoingModuleCount > 0 && incomingParentCount === 0) {
    relationshipKind = "parent_assembly";
  } else if (hasRequired && hasOptional) {
    relationshipKind = "mixed_module";
  } else if (hasOptional) {
    relationshipKind = "optional_module";
  } else if (incomingParentCount > 0) {
    relationshipKind = "required_module";
  } else {
    relationshipKind = "standalone";
  }

  switch (relationshipKind) {
    case "parent_assembly":
      return {
        relationshipKind,
        relationshipLabel: "Ansamblu părinte",
        relationshipDescription: `Publică ${formatCount(outgoingModuleCount, "modul linkuit", "module linkuite")} către Product System.`,
      };
    case "required_module":
      return {
        relationshipKind,
        relationshipLabel: outgoingModuleCount > 0 ? "Ansamblu părinte + modul obligatoriu" : "Modul obligatoriu",
        relationshipDescription: `Este utilizat ca modul obligatoriu în ${formatCount(incomingParentCount, "ansamblu", "ansambluri")}.`,
      };
    case "optional_module":
      return {
        relationshipKind,
        relationshipLabel: outgoingModuleCount > 0 ? "Ansamblu părinte + modul opțional" : "Modul opțional",
        relationshipDescription: `Este utilizat ca modul opțional în ${formatCount(incomingParentCount, "ansamblu", "ansambluri")}.`,
      };
    case "mixed_module":
      return {
        relationshipKind,
        relationshipLabel: outgoingModuleCount > 0 ? "Ansamblu părinte + modul mixt" : "Modul mixt",
        relationshipDescription: `Apare cu roluri obligatorii și opționale în ${formatCount(incomingParentCount, "ansamblu", "ansambluri")}.`,
      };
    default:
      return {
        relationshipKind: "standalone",
        relationshipLabel: "Șablon standalone",
        relationshipDescription: "Nu este linkuit momentan ca parent sau child în alte ansambluri.",
      };
  }
}

function resolveOfferPolicyMeta(
  outgoingRelationTypes: Record<string, string>,
  incomingRelationTypes: string[],
): Pick<TemplateCatalogEntry, "offerPolicyKind" | "offerPolicyLabel" | "offerPolicyDescription"> {
  const outgoingTypes = Object.values(outgoingRelationTypes);
  const requiredOutgoingCount = outgoingTypes.filter((value) => value === "required_module").length;
  const optionalOutgoingCount = outgoingTypes.filter((value) => value === "optional_addon").length;
  const hasIncomingRequired = incomingRelationTypes.includes("required_module");
  const hasIncomingOptional = incomingRelationTypes.includes("optional_addon");

  if (outgoingTypes.length > 0) {
    return {
      offerPolicyKind: "assembly_minimum_component",
      offerPolicyLabel: "Ofertă: minim 1 componentă",
      offerPolicyDescription:
        requiredOutgoingCount > 0 || optionalOutgoingCount > 0
          ? `Oferta pornește cu minimum 1 componentă. ${requiredOutgoingCount > 0 ? `${formatCount(requiredOutgoingCount, "modul obligatoriu", "module obligatorii")} poate intra automat` : "Nu are module obligatorii auto-incluse"}${optionalOutgoingCount > 0 ? `, iar ${formatCount(optionalOutgoingCount, "addon opțional", "addon-uri opționale")} se alege explicit.` : "."}`
          : "Oferta pornește cu minimum 1 componentă selectată din ansamblu.",
    };
  }

  if (hasIncomingRequired && hasIncomingOptional) {
    return {
      offerPolicyKind: "mixed_selection",
      offerPolicyLabel: "Ofertare mixtă",
      offerPolicyDescription: "Poate intra automat în unele ansambluri și explicit în altele.",
    };
  }

  if (hasIncomingOptional) {
    return {
      offerPolicyKind: "optional_explicit",
      offerPolicyLabel: "Addon explicit",
      offerPolicyDescription: "Nu intră automat în ofertă. Se adaugă doar când este selectat explicit.",
    };
  }

  if (hasIncomingRequired) {
    return {
      offerPolicyKind: "required_auto_included",
      offerPolicyLabel: "Componentă auto-inclusă",
      offerPolicyDescription: "Intră automat când este ofertat ansamblul părinte, dar poate fi calculată și separat.",
    };
  }

  return {
    offerPolicyKind: "standalone_individual",
    offerPolicyLabel: "Ofertare individuală",
    offerPolicyDescription: "Poate constitui singură componenta minimă necesară într-o ofertă.",
  };
}

export function buildTemplateCatalog(
  templates: ProductTemplateEntity[],
  links: ProductTemplateModuleLinkEntity[],
): Map<string, TemplateCatalogEntry> {
  const outgoingByParent = new Map<string, Set<string>>();
  const incomingByModule = new Map<string, Set<string>>();
  const incomingRelationTypesByModule = new Map<string, Set<string>>();
  const outgoingRelationTypesByParent = new Map<string, Map<string, string>>();

  for (const link of links) {
    if (link.active === false) continue;
    const parentCode = normalizeTemplateCode(link.parent_template_code);
    const moduleCode = normalizeTemplateCode(link.module_template_code);
    const relationType = normalizeRelationType(link.relation_type);
    if (!parentCode || !moduleCode) continue;

    const outgoing = outgoingByParent.get(parentCode) ?? new Set<string>();
    outgoing.add(moduleCode);
    outgoingByParent.set(parentCode, outgoing);

    const incoming = incomingByModule.get(moduleCode) ?? new Set<string>();
    incoming.add(parentCode);
    incomingByModule.set(moduleCode, incoming);

    const incomingRelationTypes = incomingRelationTypesByModule.get(moduleCode) ?? new Set<string>();
    incomingRelationTypes.add(relationType);
    incomingRelationTypesByModule.set(moduleCode, incomingRelationTypes);

    const outgoingRelationTypes = outgoingRelationTypesByParent.get(parentCode) ?? new Map<string, string>();
    outgoingRelationTypes.set(moduleCode, relationType);
    outgoingRelationTypesByParent.set(parentCode, outgoingRelationTypes);
  }

  const catalog = new Map<string, TemplateCatalogEntry>();
  for (const template of templates) {
    const templateCode = normalizeTemplateCode(template.template_code);
    if (!templateCode) continue;
    const outgoingModuleCodes = Array.from(outgoingByParent.get(templateCode) ?? []).sort();
    const incomingParentCodes = Array.from(incomingByModule.get(templateCode) ?? []).sort();
    const incomingRelationTypes = Array.from(incomingRelationTypesByModule.get(templateCode) ?? []).sort();
    const outgoingRelationTypes = Object.fromEntries(
      Array.from(outgoingRelationTypesByParent.get(templateCode)?.entries() ?? []).sort((left, right) =>
        left[0].localeCompare(right[0], "ro-RO"),
      ),
    );

    let kind: TemplateCatalogKind;
    let label: string;
    let description: string;
    if (outgoingModuleCodes.length > 0 && incomingParentCodes.length > 0) {
      kind = "assembly_module";
      label = "Ansamblu modular";
      description = `Conține ${formatCount(outgoingModuleCodes.length, "modul", "module")} și este reutilizat în ${formatCount(incomingParentCodes.length, "ansamblu", "ansambluri")}.`;
    } else if (outgoingModuleCodes.length > 0) {
      kind = "assembly";
      label = "Ansamblu";
      description = `Conține ${formatCount(outgoingModuleCodes.length, "modul linkuit", "module linkuite")}.`;
    } else if (incomingParentCodes.length > 0) {
      kind = "reusable_module";
      label = "Modul reutilizabil";
      description = `Poate fi folosit în ${formatCount(incomingParentCodes.length, "ansamblu", "ansambluri")}.`;
    } else {
      kind = "standalone";
      label = "Șablon independent";
      description = "Se calculează individual și nu are link-uri active în alte ansambluri.";
    }

    const relationshipMeta = resolveRelationshipMeta(
      outgoingModuleCodes.length,
      incomingParentCodes.length,
      incomingRelationTypes,
    );
    const offerPolicyMeta = resolveOfferPolicyMeta(outgoingRelationTypes, incomingRelationTypes);

    catalog.set(templateCode, {
      templateCode,
      kind,
      label,
      description,
      relationshipKind: relationshipMeta.relationshipKind,
      relationshipLabel: relationshipMeta.relationshipLabel,
      relationshipDescription: relationshipMeta.relationshipDescription,
      incomingParentCodes,
      outgoingModuleCodes,
      incomingRelationTypes,
      outgoingRelationTypes,
      offerPolicyKind: offerPolicyMeta.offerPolicyKind,
      offerPolicyLabel: offerPolicyMeta.offerPolicyLabel,
      offerPolicyDescription: offerPolicyMeta.offerPolicyDescription,
    });
  }

  return catalog;
}

export function buildTemplateCatalogFromAggregates(
  templates: ProductTemplateEntity[],
  aggregatesByTemplateCode: Map<string, ProductAggregate>,
): Map<string, TemplateCatalogEntry> {
  const derivedLinks: ProductTemplateModuleLinkEntity[] = [];

  for (const [templateCode, aggregate] of aggregatesByTemplateCode.entries()) {
    const parentTemplateCode = normalizeTemplateCode(templateCode);
    const modules = [
      ...(aggregate.modules?.required ?? []),
      ...(aggregate.modules?.optional ?? []),
    ];
    for (const module of modules) {
      const moduleTemplateCode = normalizeTemplateCode(module.child_template_code);
      if (!parentTemplateCode || !moduleTemplateCode) continue;
      derivedLinks.push({
        id: derivedLinks.length + 1,
        parent_template_id: aggregate.template_id,
        parent_template_code: parentTemplateCode,
        module_template_id: module.child_template_id ?? 0,
        module_template_code: moduleTemplateCode,
        relation_type: module.relation_type,
        trigger_field: String(module.trigger_field ?? ""),
        trigger_value_json: JSON.stringify(module.trigger_value ?? null),
        input_mapping_json: "{}",
        default_values_json: null,
        pricing_mode: String(module.pricing_mode ?? "derived"),
        execution_mode: String(module.execution_mode ?? "derived"),
        active: module.active !== false,
        notes: module.notes ?? null,
      });
    }
  }

  return buildTemplateCatalog(templates, derivedLinks);
}

export function getTemplateCatalogPriority(entry: TemplateCatalogEntry | null | undefined): number {
  switch (entry?.kind) {
    case "assembly":
      return 0;
    case "assembly_module":
      return 1;
    case "reusable_module":
      return 2;
    default:
      return 3;
  }
}