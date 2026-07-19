import ColorRegistrySelect from "@/components/workos/colorRegistry/ColorRegistrySelect";
import type { ColorRegistryItem } from "@/lib/colorRegistry/colorRegistryTypes";
import {
  ALLOWED_RETURN_DEPTH_MM,
  isCustomReturnDepth,
  isKnownRegistryColor,
} from "@/lib/intakeV6/intakeV6ReturnFinishModel";
import type { LetterGroupReturnCantFinish } from "@/lib/intakeV6/intakeV6ReturnFinishModel";
import {
  buildIntakeV6ReturnCantForUiOption,
  INTAKE_V6_CANT_VOLUM_LABEL_LOWER,
  INTAKE_V6_RETURN_FINISH_UI_OPTIONS,
  resolveIntakeV6ReturnFinishUiOption,
  type IntakeV6ReturnFinishUiOption,
} from "@/lib/intakeV6/intakeV6ReturnFinishOptions";
import { v6 } from "./atoms/intakeV6Presentation";
import {
  PILOT_REVIEW_FIELD_LABEL_CLASS,
  PILOT_REVIEW_SELECT_CLASS,
  REVIEW_FIELD_BLOCK_CLASS,
  REVIEW_SELECT_CLASS,
} from "./reviewFieldLayout";

export interface IntakeV6ReturnCantFieldsProps {
  idPrefix: string;
  returnCant: LetterGroupReturnCantFinish;
  readOnly?: boolean;
  onReturnChange: (returnCant: LetterGroupReturnCantFinish) => void;
  testIdPrefix: string;
  allowedReturnDepthMm?: readonly number[];
  layout?: "default" | "review";
  cantSettingsRowTestId?: string;
  compact?: boolean;
  /** Render a single review grid row (finish / depth / color) for Față|Cant alignment. */
  reviewGridRow?: "finish" | "depth" | "color";
  finishLabel?: string;
  depthLabel?: string;
}

export default function IntakeV6ReturnCantFields({
  idPrefix,
  returnCant,
  readOnly = false,
  onReturnChange,
  testIdPrefix,
  allowedReturnDepthMm: allowedDepthOverride,
  layout = "default",
  cantSettingsRowTestId,
  compact = false,
  reviewGridRow,
  finishLabel: finishLabelOverride,
  depthLabel: depthLabelOverride,
}: IntakeV6ReturnCantFieldsProps) {
  const effectiveDepths = allowedDepthOverride ?? ALLOWED_RETURN_DEPTH_MM;
  const uiOption = resolveIntakeV6ReturnFinishUiOption(returnCant.finishType);
  const return651Known = isKnownRegistryColor("ORACAL", returnCant.colorCode, "651");
  const returnRalKnown = isKnownRegistryColor("RAL", returnCant.colorCode);
  const isReviewLayout = layout === "review";
  const finishLabel = finishLabelOverride ?? (isReviewLayout
    ? "Finisaj cant / volum"
    : `Tip finisaj ${INTAKE_V6_CANT_VOLUM_LABEL_LOWER}`);
  const depthLabel = depthLabelOverride ?? (isReviewLayout
    ? "Adâncime cant / volum (mm)"
    : `Adâncime ${INTAKE_V6_CANT_VOLUM_LABEL_LOWER} (mm)`);
  const oracalColorLabel = isReviewLayout
    ? "Culoare Oracal cant"
    : `Culoare Oracal 651 ${INTAKE_V6_CANT_VOLUM_LABEL_LOWER}`;
  const ralColorLabel = isReviewLayout
    ? "Culoare RAL cant"
    : `Culoare RAL ${INTAKE_V6_CANT_VOLUM_LABEL_LOWER}`;

  const labelClass = isReviewLayout ? PILOT_REVIEW_FIELD_LABEL_CLASS : v6.label;
  const selectClass = isReviewLayout ? PILOT_REVIEW_SELECT_CLASS : REVIEW_SELECT_CLASS;

  const finishSelect = (
    <label className={isReviewLayout ? REVIEW_FIELD_BLOCK_CLASS : "block min-w-0"}>
      <span className={labelClass} htmlFor={`${idPrefix}-return-type`}>
        {finishLabel}
      </span>
      <select
        id={`${idPrefix}-return-type`}
        className={selectClass}
        value={uiOption}
        disabled={readOnly}
        data-testid={`${testIdPrefix}-type`}
        onChange={(event) =>
          onReturnChange(
            buildIntakeV6ReturnCantForUiOption(
              event.target.value as IntakeV6ReturnFinishUiOption,
              returnCant,
            ),
          )
        }
      >
        {INTAKE_V6_RETURN_FINISH_UI_OPTIONS.map((option) => (
          <option key={option.value} value={option.value}>
            {option.label}
          </option>
        ))}
      </select>
    </label>
  );

  const depthSelect = (
    <label className={isReviewLayout ? REVIEW_FIELD_BLOCK_CLASS : "block min-w-0"}>
      <span className={labelClass} htmlFor={`${idPrefix}-return-depth`}>
        {depthLabel}
      </span>
      <select
        id={`${idPrefix}-return-depth`}
        className={selectClass}
        value={
          returnCant.depthMm != null && Number.isFinite(returnCant.depthMm)
            ? String(returnCant.depthMm)
            : ""
        }
        disabled={readOnly}
        data-testid={`${testIdPrefix}-depth`}
        onChange={(event) =>
          onReturnChange({
            ...returnCant,
            depthMm: event.target.value ? Number(event.target.value) : undefined,
          })
        }
      >
        <option value="">—</option>
        {effectiveDepths.map((depth) => (
          <option key={depth} value={depth}>
            {depth}
          </option>
        ))}
        {isCustomReturnDepth(returnCant.depthMm) ? (
          <option value={String(returnCant.depthMm)}>{returnCant.depthMm} (salvat)</option>
        ) : null}
      </select>
    </label>
  );

  const settingsRow = isReviewLayout ? (
    <div
      className="grid grid-cols-1 gap-2 sm:grid-cols-2"
      data-testid={cantSettingsRowTestId ?? `${testIdPrefix}-settings-row`}
    >
      {finishSelect}
      {depthSelect}
    </div>
  ) : (
    <>
      <label className={v6.label} htmlFor={`${idPrefix}-return-type`}>
        {finishLabel}
      </label>
      <select
        id={`${idPrefix}-return-type`}
        className={selectClass}
        value={uiOption}
        disabled={readOnly}
        data-testid={`${testIdPrefix}-type`}
        onChange={(event) =>
          onReturnChange(
            buildIntakeV6ReturnCantForUiOption(
              event.target.value as IntakeV6ReturnFinishUiOption,
              returnCant,
            ),
          )
        }
      >
        {INTAKE_V6_RETURN_FINISH_UI_OPTIONS.map((option) => (
          <option key={option.value} value={option.value}>
            {option.label}
          </option>
        ))}
      </select>

      <label className={v6.label} htmlFor={`${idPrefix}-return-depth`}>
        {depthLabel}
      </label>
      <select
        id={`${idPrefix}-return-depth`}
        className={selectClass}
        value={
          returnCant.depthMm != null && Number.isFinite(returnCant.depthMm)
            ? String(returnCant.depthMm)
            : ""
        }
        disabled={readOnly}
        data-testid={`${testIdPrefix}-depth`}
        onChange={(event) =>
          onReturnChange({
            ...returnCant,
            depthMm: event.target.value ? Number(event.target.value) : undefined,
          })
        }
      >
        <option value="">—</option>
        {effectiveDepths.map((depth) => (
          <option key={depth} value={depth}>
            {depth}
          </option>
        ))}
        {isCustomReturnDepth(returnCant.depthMm) ? (
          <option value={String(returnCant.depthMm)}>{returnCant.depthMm} (salvat)</option>
        ) : null}
      </select>
    </>
  );

  const colorFields = (
    <>
      {uiOption === "oracal_wrapped" ? (
        <div data-testid={`${testIdPrefix}-oracal-651`}>
          <ColorRegistrySelect
            label={oracalColorLabel}
            valueCode={return651Known ? returnCant.colorCode ?? null : null}
            filter={{ system: "ORACAL", series: "651", usageScope: "return" }}
            reviewAlign={isReviewLayout}
            onChange={(item: ColorRegistryItem | null) => {
              if (!item) {
                onReturnChange({
                  ...returnCant,
                  finishType: "oracal_wrapped",
                  materialCode: "651",
                  colorCode: undefined,
                  colorName: undefined,
                });
                return;
              }
              onReturnChange({
                ...returnCant,
                finishType: "oracal_wrapped",
                materialCode: "651",
                colorCode: item.code,
                colorName: item.name,
              });
            }}
            disabled={readOnly}
            testId={`${testIdPrefix}-oracal651`}
          />
          {!returnCant.colorCode?.trim() ? (
            <p
              className="mt-2 text-[10px] text-amber-200/90"
              data-testid={`${testIdPrefix}-oracal651-missing`}
            >
              Culoare Oracal 651 nedecisă.
            </p>
          ) : null}
          {!return651Known && returnCant.colorCode?.trim() ? (
            <p
              className="mt-2 text-[10px] text-amber-200/90 bg-amber-950/20 border border-amber-800/40 rounded px-2 py-1.5"
              data-testid={`${testIdPrefix}-oracal651-legacy`}
            >
              Cod salvat: <span className="font-mono">{returnCant.colorCode}</span>
              {returnCant.colorName ? ` — ${returnCant.colorName}` : ""}. Nu este în registry.
            </p>
          ) : null}
        </div>
      ) : null}

      {uiOption === "ral_paint" ? (
        <div data-testid={`${testIdPrefix}-ral`}>
          <ColorRegistrySelect
            label={ralColorLabel}
            valueCode={returnRalKnown ? returnCant.colorCode ?? null : null}
            filter={{ system: "RAL", usageScope: "return" }}
            reviewAlign={isReviewLayout}
            onChange={(item: ColorRegistryItem | null) => {
              if (!item) {
                onReturnChange({
                  ...returnCant,
                  finishType: "ral_paint",
                  materialCode: "RAL",
                  colorCode: undefined,
                  colorName: undefined,
                });
                return;
              }
              onReturnChange({
                ...returnCant,
                finishType: "ral_paint",
                materialCode: "RAL",
                colorCode: item.code,
                colorName: item.name,
              });
            }}
            disabled={readOnly}
            testId={`${testIdPrefix}-ral-select`}
          />
          {!returnCant.colorCode?.trim() ? (
            <p
              className="mt-2 text-[10px] text-amber-200/90"
              data-testid={`${testIdPrefix}-ral-missing`}
            >
              RAL nedecis — selectează codul RAL pentru {INTAKE_V6_CANT_VOLUM_LABEL_LOWER}.
            </p>
          ) : null}
          {!returnRalKnown && returnCant.colorCode?.trim() ? (
            <p
              className="mt-2 text-[10px] text-amber-200/90 bg-amber-950/20 border border-amber-800/40 rounded px-2 py-1.5"
              data-testid={`${testIdPrefix}-ral-legacy`}
            >
              Cod salvat: <span className="font-mono">{returnCant.colorCode}</span>
              {returnCant.colorName ? ` — ${returnCant.colorName}` : ""}. Nu este în registry.
            </p>
          ) : null}
        </div>
      ) : null}
    </>
  );

  if (isReviewLayout && reviewGridRow) {
    if (reviewGridRow === "finish") {
      return <>{finishSelect}</>;
    }
    if (reviewGridRow === "depth") {
      return <>{depthSelect}</>;
    }
    if (reviewGridRow === "color") {
      if (uiOption !== "oracal_wrapped" && uiOption !== "ral_paint") {
        return null;
      }
      return <div data-testid={`${testIdPrefix}-color-row`}>{colorFields}</div>;
    }
  }

  return (
    <div
      className={isReviewLayout ? (compact ? "space-y-2" : "space-y-3") : "space-y-2"}
      data-testid={`${testIdPrefix}-fields`}
    >
      {settingsRow}
      {isReviewLayout && (uiOption === "oracal_wrapped" || uiOption === "ral_paint") ? (
        <div
          className="border-t border-[#2A3548]/60 pt-2"
          data-testid={`${testIdPrefix}-color-row`}
        >
          {colorFields}
        </div>
      ) : (
        colorFields
      )}
    </div>
  );
}


