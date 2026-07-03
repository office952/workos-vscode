export * from "./intakeV4LedLighting";

export {
  computeIntakeV4LedLoadWatts as computeIntakeV6LedLoadWatts,
  computeIntakeV4LedModuleCount as computeIntakeV6LedModuleCount,
  INTAKE_V4_LED_PITCH_MM as INTAKE_V6_LED_PITCH_MM,
  INTAKE_V4_LED_MODULE_WATTAGE_OPTIONS as INTAKE_V6_LED_MODULE_WATTAGE_OPTIONS,
  INTAKE_V4_PSU_RESERVE_RATIO as INTAKE_V6_PSU_RESERVE_RATIO,
  normalizeIntakeV4LedModuleWattage as normalizeIntakeV6LedModuleWattage,
  proposeIntakeV4PsuConfiguration as proposeIntakeV6PsuConfiguration,
} from "./intakeV4LedLighting";
