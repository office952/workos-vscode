import type { LayerAutoRole } from "@/lib/svgAnalyzer";
import { INTAKE_V4_LAYER_ROLE_OPTIONS } from "./intakeV4LayerRoleOptions";
import { LEGACY_INTAKE_SVG_ROLE_ADAPTER } from "./svgComponentBindings";

export const INTAKE_V6_LAYER_ROLE_OPTIONS = INTAKE_V4_LAYER_ROLE_OPTIONS;
export const INTAKE_V6_OWNER_ROLE_LABEL_LETTERS = "Vector Litere";
export const INTAKE_V6_OWNER_ROLE_LABEL_LOGO = "Vector Logo";
export const INTAKE_V6_OWNER_ROLE_LABEL_SUPPORT = "Contur suport";

/**
 * LEGACY_INTAKE_SVG_ROLE_ADAPTER — layer-role bridge for analysis-bundle only.
 * Not Product System authority. Do not add Vector ACP / TPL-BOND-CASETAT here.
 * Contur suport maps to live TPL-ACM-BOXED-MOUNTING-SUPPORT_v1 via svg_bindable_components.
 */
export const INTAKE_V6_LEGACY_SVG_ROLE_ADAPTER_ID = LEGACY_INTAKE_SVG_ROLE_ADAPTER;

export const INTAKE_V6_OWNER_LAYER_ROLE_OPTIONS: ReadonlyArray<{
	value: LayerAutoRole;
	label: string;
}> = [
	{ value: "face", label: INTAKE_V6_OWNER_ROLE_LABEL_LETTERS },
	{ value: "printed_artwork", label: INTAKE_V6_OWNER_ROLE_LABEL_LOGO },
	{ value: "support_panel", label: INTAKE_V6_OWNER_ROLE_LABEL_SUPPORT },
];

export interface IntakeV6LayerRoleOptionContext {
	layer: { name?: string | null; layerKind?: string | null; autoRole?: string | null };
	layerDisplay?: string | null;
	confirmedRole?: string | null;
	detectedKind?: string | null;
	targetTemplateCode?: string | null;
	activeTemplateCode?: string | null;
	assemblyType?: string | null;
}

export interface IntakeV6LayerRoleOptionGroups {
	recommendedOptions: ReadonlyArray<{ value: LayerAutoRole; label: string }>;
	secondaryOptions: ReadonlyArray<{ value: LayerAutoRole; label: string }>;
	fallbackOptions: ReadonlyArray<{ value: LayerAutoRole; label: string }>;
	displayMode: "flat" | "grouped";
}

const LETTERS = "TPL-VOLUMETRIC-LETTERS_v2";
const LOGO = "TPL-VOLUMETRIC-LOGO_v1";

function pickOption(value: LayerAutoRole) {
	return INTAKE_V4_LAYER_ROLE_OPTIONS.find((option) => option.value === value)!;
}

function isCurrentVolumetricContext(args: IntakeV6LayerRoleOptionContext): boolean {
	return args.activeTemplateCode === LETTERS && (args.targetTemplateCode === LETTERS || args.targetTemplateCode === LOGO);
}

export function getIntakeV6OwnerRoleLabel(role: string | null | undefined): string {
	if (role === "face") return INTAKE_V6_OWNER_ROLE_LABEL_LETTERS;
	if (role === "logo" || role === "printed_artwork") return INTAKE_V6_OWNER_ROLE_LABEL_LOGO;
	if (role === "support_panel") return INTAKE_V6_OWNER_ROLE_LABEL_SUPPORT;
	if (!role) return "—";
	return INTAKE_V4_LAYER_ROLE_OPTIONS.find((option) => option.value === role)?.label ?? role;
}

export function normalizeIntakeV6OwnerSelectableRole(
	args: Pick<IntakeV6LayerRoleOptionContext, "layer" | "confirmedRole" | "targetTemplateCode">,
): LayerAutoRole {
	if (args.confirmedRole === "support_panel") return "support_panel";
	if (args.confirmedRole === "face") return "face";
	if (args.confirmedRole === "logo" || args.confirmedRole === "printed_artwork") return "printed_artwork";
	if (args.layer.autoRole === "support_panel") return "support_panel";
	if (args.targetTemplateCode === LOGO) return "printed_artwork";
	if (args.layer.autoRole === "logo" || args.layer.autoRole === "printed_artwork") return "printed_artwork";
	return "face";
}

export function getIntakeV6RoleOptionsForLayer(
	args: IntakeV6LayerRoleOptionContext,
): IntakeV6LayerRoleOptionGroups {
	if (isCurrentVolumetricContext(args)) {
		const recommended = [pickOption("face"), pickOption("printed_artwork")];
		return {
			recommendedOptions: recommended,
			secondaryOptions: [],
			fallbackOptions: [],
			displayMode: "flat",
		};
	}

	const defaultRecommendedValues: LayerAutoRole[] = args.targetTemplateCode === LOGO
		? ["logo", "printed_artwork", "vinyl", "face", "ignore", "unknown"]
		: ["face", "return", "backing", "vinyl", "ignore", "unknown"];
	const recommendedOptions = defaultRecommendedValues
		.map((value) => INTAKE_V4_LAYER_ROLE_OPTIONS.find((option) => option.value === value))
		.filter((option): option is (typeof INTAKE_V4_LAYER_ROLE_OPTIONS)[number] => Boolean(option));
	const recommendedValues = new Set(recommendedOptions.map((option) => option.value));
	const secondaryOptions = INTAKE_V4_LAYER_ROLE_OPTIONS.filter((option) => !recommendedValues.has(option.value));

	return {
		recommendedOptions,
		secondaryOptions,
		fallbackOptions: [],
		displayMode: "grouped",
	};
}
