import type { IntakeProductSpec } from "@/lib/intakeProductSpec";
import type { VolumetricQuoteNavState } from "@/lib/volumetricQuoteFlowState";
import { TPL_VOLUMETRIC_LETTERS } from "@/lib/volumetricQuoteInput";

function num(value: unknown): number | undefined {
  if (typeof value === "number" && Number.isFinite(value) && value > 0) return value;
  if (typeof value === "string" && value.trim()) {
    const parsed = Number(value);
    if (Number.isFinite(parsed) && parsed > 0) return parsed;
  }
  return undefined;
}

/** Map V4 pricing_input preview → IntakeProductSpec for QuoteWizard prefill. */
export function buildIntakeProductSpecFromV4QuoteInput(
  quoteInput: Record<string, unknown>,
  options?: {
    clientName?: string | null;
    jobTitle?: string | null;
  },
): IntakeProductSpec {
  const spec: IntakeProductSpec = {};

  const letterCount = num(quoteInput.letter_count ?? quoteInput.real_letters_count);
  if (letterCount != null) spec.letter_count = Math.round(letterCount);

  const perimeter = num(quoteInput.letter_perimeter_m ?? quoteInput.total_letter_perimeter_ml);
  if (perimeter != null) spec.letter_perimeter_m = perimeter;

  const faceArea = num(quoteInput.face_area_m2 ?? quoteInput.letter_face_area_m2);
  if (faceArea != null) spec.letter_face_area_m2 = faceArea;

  const depth = num(quoteInput.return_depth_mm ?? quoteInput.depth_mm);
  if (depth != null) {
    spec.return_depth_mm = depth;
    spec.depth_mm = depth;
  }

  const width = num(quoteInput.width_mm);
  if (width != null) spec.width_mm = width;
  const height = num(quoteInput.height_mm);
  if (height != null) spec.height_mm = height;

  if (quoteInput.illuminated === false) {
    spec.illumination_type = "non_illuminated";
  } else {
    spec.illumination_type = "frontlit";
    const lighting = quoteInput.lighting_system_type;
    if (lighting === "led_strip" || lighting === "led_modules") {
      spec.lighting_system_type = lighting;
    }
    if (lighting === "led_strip") {
      const stripPower = num(quoteInput.led_strip_power_w_per_ml);
      if (stripPower === 5 || stripPower === 10) {
        spec.led_strip_power_w_per_ml = stripPower;
        spec.led_strip_density = stripPower === 10 ? "120_led_per_m" : "60_led_per_m";
      }
    }
    const psu = num(quoteInput.required_psu_watts);
    if (psu != null) spec.required_psu_watts = psu;
    const led = num(quoteInput.estimated_led_watts);
    if (led != null) spec.total_led_watts = led;
    if (Array.isArray(quoteInput.psu_configuration) && quoteInput.psu_configuration.length > 0) {
      const maxPsu = Math.max(
        ...quoteInput.psu_configuration.filter((v): v is number => typeof v === "number"),
      );
      if (Number.isFinite(maxPsu)) {
        spec.selected_psu_watts = maxPsu as IntakeProductSpec["selected_psu_watts"];
        spec.psu_configuration = quoteInput.psu_configuration.filter(
          (v): v is number => typeof v === "number",
        );
        spec.psu_allocation_status = "ok";
      }
    }
  }

  const faceFinish = quoteInput.face_finish_type;
  if (typeof faceFinish === "string") {
    if (faceFinish === "none") spec.face_finish_type = "none";
    else if (faceFinish === "oracal_8500") spec.face_finish_type = "oracal_8500";
    else if (faceFinish === "vinyl" || faceFinish === "oracal_651") spec.face_finish_type = "oracal_651";
  }

  if (options?.jobTitle) spec.text = options.jobTitle;
  if (options?.clientName) {
    // productSpec has no client_name — carried via nav state clientName
  }

  return spec;
}

export function buildV4QuoteWizardNavState(args: {
  quoteInput: Record<string, unknown>;
  clientName?: string | null;
  jobTitle?: string | null;
  createdQuoteCode?: string;
}): VolumetricQuoteNavState {
  return {
    openWizard: true,
    templateCode: TPL_VOLUMETRIC_LETTERS,
    confirmedTemplateCode: TPL_VOLUMETRIC_LETTERS,
    productSpec: buildIntakeProductSpecFromV4QuoteInput(args.quoteInput, {
      clientName: args.clientName,
      jobTitle: args.jobTitle,
    }),
    clientName: args.clientName ?? undefined,
    fromIntake: true,
    intakeStatus: "ready_for_quote_preview",
  };
}
