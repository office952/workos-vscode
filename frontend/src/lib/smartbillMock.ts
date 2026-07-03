// ============================================================
// SmartBill Mock API — Simulated CUI Lookup
// ============================================================

const SMARTBILL_DEMO_ENABLED = import.meta.env.DEV || import.meta.env.VITE_ENABLE_MOCK_DATA === "true";

export interface SmartBillCompany {
  cui: string;
  name: string;
  address: string;
  county: string;
  city: string;
  registrationNumber: string;
  isRO: boolean;
  isVATPayer: boolean;
  vatCode: string;
  phone: string;
  email: string;
}

const mockCompanies: SmartBillCompany[] = SMARTBILL_DEMO_ENABLED ? [
  {
    cui: "14399840",
    name: "MOL ROMANIA PETROLEUM PRODUCTS S.R.L.",
    address: "Str. Tipografilor Nr. 11-15, Sector 1",
    county: "București",
    city: "București",
    registrationNumber: "J40/14745/2001",
    isRO: true,
    isVATPayer: true,
    vatCode: "RO14399840",
    phone: "021-222-3344",
    email: "office@mol.ro",
  },
  {
    cui: "15513923",
    name: "VODAFONE ROMANIA S.A.",
    address: "Bd. Barbu Văcărescu Nr. 201-209",
    county: "București",
    city: "București",
    registrationNumber: "J40/8870/2003",
    isRO: true,
    isVATPayer: true,
    vatCode: "RO15513923",
    phone: "021-305-0000",
    email: "business@vodafone.ro",
  },
  {
    cui: "50227",
    name: "BANCA TRANSILVANIA S.A.",
    address: "Str. George Barițiu Nr. 8",
    county: "Cluj",
    city: "Cluj-Napoca",
    registrationNumber: "J12/4155/1993",
    isRO: true,
    isVATPayer: true,
    vatCode: "RO50227",
    phone: "0264-407-150",
    email: "contact@bancatransilvania.ro",
  },
  {
    cui: "18aborting",
    name: "DECATHLON ROMANIA S.R.L.",
    address: "Bd. Iuliu Maniu Nr. 546-560",
    county: "București",
    city: "București",
    registrationNumber: "J40/12829/2004",
    isRO: true,
    isVATPayer: true,
    vatCode: "RO16782884",
    phone: "021-301-5500",
    email: "contact@decathlon.ro",
  },
  {
    cui: "16782884",
    name: "DECATHLON ROMANIA S.R.L.",
    address: "Bd. Iuliu Maniu Nr. 546-560",
    county: "București",
    city: "București",
    registrationNumber: "J40/12829/2004",
    isRO: true,
    isVATPayer: true,
    vatCode: "RO16782884",
    phone: "021-301-5500",
    email: "contact@decathlon.ro",
  },
  {
    cui: "6348050",
    name: "OMV PETROM S.A.",
    address: "Str. Coralilor Nr. 22, Sector 1",
    county: "București",
    city: "București",
    registrationNumber: "J40/8302/1997",
    isRO: true,
    isVATPayer: true,
    vatCode: "RO6348050",
    phone: "021-406-0000",
    email: "office@petrom.com",
  },
  {
    cui: "9268740",
    name: "ORANGE ROMANIA S.A.",
    address: "Bd. Lascăr Catargiu Nr. 47-53, Sector 1",
    county: "București",
    city: "București",
    registrationNumber: "J40/10178/1996",
    isRO: true,
    isVATPayer: true,
    vatCode: "RO9268740",
    phone: "021-201-2000",
    email: "business@orange.ro",
  },
  {
    cui: "18189442",
    name: "MEGA IMAGE S.R.L.",
    address: "Bd. Timișoara Nr. 26, Sector 6",
    county: "București",
    city: "București",
    registrationNumber: "J40/664/2006",
    isRO: true,
    isVATPayer: true,
    vatCode: "RO18189442",
    phone: "021-305-7700",
    email: "contact@mega-image.ro",
  },
] : [];

// Map client names to CUI for easy lookup from intake requests
export const clientCUIMap: Record<string, string> = SMARTBILL_DEMO_ENABLED ? {
  "MOL": "14399840",
  "Vodafone": "15513923",
  "Banca Transilvania": "50227",
  "Decathlon": "16782884",
  "Petrom": "6348050",
  "Orange": "9268740",
  "Mega Image": "18189442",
} : {};

/**
 * Simulates SmartBill API CUI lookup.
 * Returns company data after a mock delay.
 */
export async function lookupCUI(cui: string): Promise<{ success: boolean; data?: SmartBillCompany; error?: string }> {
  if (!SMARTBILL_DEMO_ENABLED) {
    return { success: false, error: "SmartBill mock lookup is disabled in this build." };
  }

  // Simulate network delay
  await new Promise((resolve) => setTimeout(resolve, 1200));

  // Clean CUI input
  const cleanCUI = cui.replace(/\s/g, "").replace(/^RO/i, "");

  const company = mockCompanies.find((c) => c.cui === cleanCUI);

  if (company) {
    return { success: true, data: company };
  }

  return { success: false, error: `CUI "${cui}" nu a fost găsit în baza de date SmartBill.` };
}

// --- Mock Google Maps Autocomplete Suggestions ---
export interface MapSuggestion {
  placeId: string;
  description: string;
  mainText: string;
  secondaryText: string;
}

const mockAddresses: MapSuggestion[] = SMARTBILL_DEMO_ENABLED ? [
  { placeId: "p1", description: "Bd. Unirii Nr. 45, București", mainText: "Bd. Unirii Nr. 45", secondaryText: "București, România" },
  { placeId: "p2", description: "Str. Victoriei Nr. 12, Cluj-Napoca", mainText: "Str. Victoriei Nr. 12", secondaryText: "Cluj-Napoca, România" },
  { placeId: "p3", description: "Calea Dorobanților Nr. 89, București", mainText: "Calea Dorobanților Nr. 89", secondaryText: "București, România" },
  { placeId: "p4", description: "Bd. Decebal Nr. 23, Timișoara", mainText: "Bd. Decebal Nr. 23", secondaryText: "Timișoara, România" },
  { placeId: "p5", description: "Str. Republicii Nr. 5, Brașov", mainText: "Str. Republicii Nr. 5", secondaryText: "Brașov, România" },
  { placeId: "p6", description: "Bd. Mamaia Nr. 120, Constanța", mainText: "Bd. Mamaia Nr. 120", secondaryText: "Constanța, România" },
  { placeId: "p7", description: "Str. Mihai Eminescu Nr. 78, Iași", mainText: "Str. Mihai Eminescu Nr. 78", secondaryText: "Iași, România" },
  { placeId: "p8", description: "Calea Victoriei Nr. 155, București", mainText: "Calea Victoriei Nr. 155", secondaryText: "București, România" },
  { placeId: "p9", description: "Bd. Revoluției Nr. 33, Arad", mainText: "Bd. Revoluției Nr. 33", secondaryText: "Arad, România" },
  { placeId: "p10", description: "Str. Avram Iancu Nr. 10, Sibiu", mainText: "Str. Avram Iancu Nr. 10", secondaryText: "Sibiu, România" },
] : [];

/**
 * Simulates Google Maps Places Autocomplete.
 */
export function searchAddresses(query: string): MapSuggestion[] {
  if (!query || query.length < 2) return [];
  const q = query.toLowerCase();
  return mockAddresses.filter(
    (a) => a.description.toLowerCase().includes(q) || a.mainText.toLowerCase().includes(q)
  ).slice(0, 5);
}