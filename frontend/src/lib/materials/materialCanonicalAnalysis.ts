/**
 * Material name analysis helpers — suggestions/warnings only; no auto-rename.
 */

import {
  MATERIAL_CANONICAL_FAMILIES,
  type MaterialFamilyDefinition,
  type MaterialFamilyId,
} from "./materialCanonicalTaxonomy";

export interface MaterialFamilyMatch {
  family: MaterialFamilyDefinition;
  matchedAliases: string[];
  matchedBrands: string[];
  matchedSeries: string[];
  score: number;
}

export interface BrandTermMatch {
  term: string;
  familyId: MaterialFamilyId;
  canonicalLabel: string;
}

export interface UsageTermWarning {
  term: string;
  familyId: MaterialFamilyId;
  message: string;
}

export interface CanonicalMaterialSuggestion {
  normalizedInput: string;
  families: MaterialFamilyMatch[];
  brandMatches: BrandTermMatch[];
  usageWarnings: UsageTermWarning[];
  aliasHints: string[];
  canonicalLabelSuggestion: string | null;
  messages: string[];
}

const USAGE_WARNING_MESSAGE =
  'Atenție: "{term}" descrie utilizarea materialului, nu materialul brut. Recomandat: folosește denumirea materialului fizic și păstrează utilizarea în template/componentă.';

const BRAND_WARNING_MESSAGE =
  'Brand detectat: {brand}. Păstrează brandul ca brand/serie, nu ca familie generică.';

export function normalizeMaterialSearchTerm(input: string): string {
  return input
    .normalize("NFD")
    .replace(/[\u0300-\u036f]/g, "")
    .toLowerCase()
    .replace(/[_\-×x]/g, " ")
    .replace(/\s+/g, " ")
    .trim();
}

/** Token match with word boundaries for short terms. */
export function termMatches(haystack: string, term: string): boolean {
  const hay = normalizeMaterialSearchTerm(haystack);
  const t = normalizeMaterialSearchTerm(term);
  if (!t) return false;
  if (t.includes(" ")) return hay.includes(t);
  const padded = ` ${hay} `;
  return padded.includes(` ${t} `);
}

function scoreFamilyMatch(
  family: MaterialFamilyDefinition,
  input: string
): MaterialFamilyMatch | null {
  const matchedAliases: string[] = [];
  const matchedBrands: string[] = [];
  const matchedSeries: string[] = [];

  for (const alias of family.aliases) {
    if (termMatches(input, alias)) matchedAliases.push(alias);
  }
  for (const brand of family.brand_terms) {
    if (termMatches(input, brand)) matchedBrands.push(brand);
  }
  for (const series of family.series_terms) {
    if (termMatches(input, series)) matchedSeries.push(series);
  }

  const score = matchedAliases.length * 2 + matchedBrands.length * 3 + matchedSeries.length;
  if (score === 0) return null;

  return { family, matchedAliases, matchedBrands, matchedSeries, score };
}

export function findMaterialFamilyMatches(input: string): MaterialFamilyMatch[] {
  const matches = MATERIAL_CANONICAL_FAMILIES.map((family) => scoreFamilyMatch(family, input))
    .filter((m): m is MaterialFamilyMatch => m !== null)
    .sort((a, b) => b.score - a.score);

  // Disambiguate steel vs aluminium when only generic "profil" matches both contexts.
  const hasSteelSignal = matches.some(
    (m) =>
      m.family.material_family === "steel_profile" &&
      (m.matchedAliases.some((a) => ["otel", "oțel", "teava", "țeavă", "cornier"].includes(a)) ||
        termMatches(input, "otel") ||
        termMatches(input, "oțel"))
  );
  const hasAluSignal = matches.some(
    (m) =>
      m.family.material_family === "aluminium_profile" &&
      (m.matchedAliases.includes("aluminiu") || m.matchedAliases.includes("profil aluminiu"))
  );

  if (hasSteelSignal && !hasAluSignal) {
    return matches.filter((m) => m.family.material_family !== "aluminium_profile");
  }
  if (hasAluSignal && !hasSteelSignal) {
    return matches.filter((m) => m.family.material_family !== "steel_profile");
  }

  return matches;
}

export function findBrandTermMatches(input: string): BrandTermMatch[] {
  const results: BrandTermMatch[] = [];
  for (const family of MATERIAL_CANONICAL_FAMILIES) {
    for (const brand of family.brand_terms) {
      if (termMatches(input, brand)) {
        results.push({
          term: brand,
          familyId: family.material_family,
          canonicalLabel: family.canonical_label,
        });
      }
    }
  }
  return results;
}

export function findUsageTermWarnings(input: string): UsageTermWarning[] {
  const warnings: UsageTermWarning[] = [];
  const seen = new Set<string>();

  for (const family of MATERIAL_CANONICAL_FAMILIES) {
    for (const usage of family.usage_warning_terms) {
      const key = `${family.material_family}:${usage}`;
      if (seen.has(key)) continue;
      if (!termMatches(input, usage)) continue;
      seen.add(key);
      warnings.push({
        term: usage,
        familyId: family.material_family,
        message: USAGE_WARNING_MESSAGE.replace("{term}", usage),
      });
    }
  }
  return warnings;
}

function buildAliasHintMessages(
  families: MaterialFamilyMatch[],
  input: string
): { aliasHints: string[]; messages: string[] } {
  const aliasHints: string[] = [];
  const messages: string[] = [];
  const primary = families[0];
  if (!primary) return { aliasHints, messages };

  const popularTerms = [
    ...primary.matchedAliases.filter((a) => !["acm", "acp", "pvc", "pmma"].includes(a)),
    ...primary.matchedBrands,
  ];

  for (const term of popularTerms) {
    if (!termMatches(input, term)) continue;
    aliasHints.push(term);
    messages.push(
      `Termen detectat: "${term}". Denumirea canonică recomandată: ${primary.family.canonical_label}.`
    );
  }

  // Technical ACM specs preserved in name — informational only.
  if (
    primary.family.material_family === "acm_acp_panel" &&
    /\b\d+\s*mm\b/.test(normalizeMaterialSearchTerm(input)) &&
    (termMatches(input, "alu") || termMatches(input, "aluminiu"))
  ) {
    messages.push(
      "Specificațiile tehnice (grosime totală, folie aluminiu) pot rămâne în denumire — păstrați identitatea completă conform politicii ACM."
    );
  }

  return { aliasHints, messages };
}

export function buildMaterialNamingHintMessages(suggestion: CanonicalMaterialSuggestion): string[] {
  return suggestion.messages;
}

/** True when the display name already reflects the suggested canonical family. */
export function isSubstantiallyCanonicalMaterialName(
  input: string,
  canonicalLabel: string | null
): boolean {
  if (!input.trim() || !canonicalLabel) return false;
  const norm = normalizeMaterialSearchTerm(input);
  const labelNorm = normalizeMaterialSearchTerm(canonicalLabel);
  if (norm.includes(labelNorm) || labelNorm.includes(norm)) return true;
  const tokens = labelNorm.split(" ").filter((t) => t.length > 3).slice(0, 3);
  return tokens.length >= 2 && tokens.every((t) => norm.includes(t));
}

export function getCanonicalMaterialSuggestion(input: string): CanonicalMaterialSuggestion {
  const normalizedInput = normalizeMaterialSearchTerm(input);
  const families = findMaterialFamilyMatches(input);
  const brandMatches = findBrandTermMatches(input);
  const usageWarnings = findUsageTermWarnings(input);
  const canonicalLabelSuggestion = families[0]?.family.canonical_label ?? null;
  const substantiallyCanonical = isSubstantiallyCanonicalMaterialName(
    input,
    canonicalLabelSuggestion
  );

  const { aliasHints, messages: aliasMessages } = buildAliasHintMessages(families, input);
  const messages: string[] = substantiallyCanonical ? [] : [...aliasMessages];

  if (!substantiallyCanonical) {
    for (const brand of brandMatches) {
      const label = brand.term.charAt(0).toUpperCase() + brand.term.slice(1);
      const msg = BRAND_WARNING_MESSAGE.replace("{brand}", label);
      if (!messages.includes(msg)) messages.push(msg);
    }
  }

  for (const warning of usageWarnings) {
    if (!messages.includes(warning.message)) messages.push(warning.message);
  }

  if (
    substantiallyCanonical &&
    families[0]?.family.material_family === "acm_acp_panel" &&
    /\b\d+\s*mm\b/.test(normalizedInput) &&
    (termMatches(input, "alu") || termMatches(input, "aluminiu"))
  ) {
    messages.push(
      "Specificațiile tehnice (grosime totală, folie aluminiu) pot rămâne în denumire — păstrați identitatea completă conform politicii ACM."
    );
  }

  return {
    normalizedInput,
    families,
    brandMatches,
    usageWarnings,
    aliasHints,
    canonicalLabelSuggestion,
    messages,
  };
}
