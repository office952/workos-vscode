export type ColorRegistrySystem = "RAL" | "ORACAL";

export type OracalSeries = "651" | "8500";

export type ColorUsageScope =
  | "return"
  | "face_vinyl"
  | "structure"
  | "cable_channel"
  | "illuminated_face";

export type ColorRegistryItem = {
  system: ColorRegistrySystem;
  brand?: "Oracal";
  series?: OracalSeries;
  code: string;
  name: string;
  romanianName?: string;
  previewHex: string;
  finish?: string;
  usageScope: ColorUsageScope[];
  translucent?: boolean;
  active: boolean;
  source?: string;
  notes?: string;
};

export type ReturnFinishSystem = "standard" | "RAL" | "ORACAL";

export type FaceVinylSeries = "651" | "8500";
