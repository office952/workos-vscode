import type { IntakeProductSpec } from "@/lib/intakeProductSpec";
import { applyFrontlitConstructionDefaults } from "@/lib/volumetricFrontlitIntake";

export function buildVolumetricLightingSnapshot(
  spec: IntakeProductSpec,
): IntakeProductSpec {
  return applyFrontlitConstructionDefaults(spec);
}

export function formatVolumetricPsuConfiguration(
  configuration: Array<60 | 100 | 160 | 200>,
): string {
  return configuration.map((watts) => `${watts} W`).join(" + ");
}