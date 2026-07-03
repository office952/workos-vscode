import ColorRegistrySelect from "@/components/workos/colorRegistry/ColorRegistrySelect";
import { INTAKE_ROLL_WIDTH_OPTIONS } from "@/lib/intakeVolumetricSpec";
import type { IntakeV6LetterGroupFinish } from "@/lib/intakeV6/intakeV6LetterGroups";
import { resolveLetterGroupFaceFinishOptions } from "@/lib/intakeV6/intakeV6LetterGroupFaceFinishOptions";
import {
  faceFinishNeedsColorPicker,
  faceFinishNeedsRollWidth,
  normalizeFaceVinylRollWidthMm,
  oracalColorPaletteSeriesForFace,
} from "@/lib/intakeV6/intakeV6FaceFinishOptions";
import { v6 } from "./atoms/intakeV6Presentation";
import { patchLetterGroupFinishes } from "./letterGroupFinishSectionHelpers";

const selectClass =
  "w-full rounded border border-[#2A3548] bg-[#0A0F1A] px-2 py-1.5 text-[11px]";

export default function IntakeV6ReviewFaceLettersSection({
  groups,
  onChange,
  faceFinishOptions,
}: {
  groups: IntakeV6LetterGroupFinish[];
  onChange: (groups: IntakeV6LetterGroupFinish[]) => void;
  faceFinishOptions?: readonly { value: string; label: string }[];
}) {
  const effectiveFaceOptions = resolveLetterGroupFaceFinishOptions(faceFinishOptions);
  if (groups.length === 0) return null;

  function patchGroup(groupKey: string, patch: Partial<IntakeV6LetterGroupFinish>) {
    onChange(patchLetterGroupFinishes(groups, groupKey, patch));
  }

  return (
    <div className={`${v6.card} mb-4`} data-testid="intake-v6-letter-group-face-finishes">
      <p className="mb-3 text-[11px] text-slate-400" data-testid="intake-v6-face-letters-helper">
        Față = finisajul vizibil aplicat pe plexiglasul literei.
      </p>
      <div className="space-y-3">
        {groups.map((group) => {
          const showColor = faceFinishNeedsColorPicker(group.face_finish_type);
          const showRollWidth = faceFinishNeedsRollWidth(group.face_finish_type);

          return (
            <div
              key={group.group_key}
              className="rounded border border-[#2A3548] bg-[#0A0F1A]/40 p-3"
              data-testid={`intake-v6-letter-group-face-${group.group_key}`}
            >
              <div className="mb-3 flex items-center gap-2">
                <span
                  className="h-6 w-6 shrink-0 rounded border border-slate-600"
                  style={{ backgroundColor: group.source_fill_color ?? "#64748b" }}
                  data-testid={`intake-v6-letter-group-swatch-${group.group_key}`}
                  aria-hidden
                />
                <p className="text-[12px] font-semibold text-slate-200">{group.layer_name}</p>
              </div>

              <div
                className="rounded border border-[#243044]/80 bg-[#0A0F1A]/30 p-3"
                data-testid={`intake-v6-face-letter-zone-${group.group_key}`}
              >
                <p className="mb-2 text-[10px] font-bold uppercase tracking-wide text-slate-500">
                  Față literei
                </p>

                <div
                  className={`grid gap-3 ${showRollWidth ? "sm:grid-cols-2" : "grid-cols-1"}`}
                  data-testid={`intake-v6-face-settings-row-${group.group_key}`}
                >
                  <label className="block min-w-0">
                    <span className={v6.label}>Finisaj față</span>
                    <select
                      className={selectClass}
                      value={group.face_finish_type}
                      onChange={(event) =>
                        patchGroup(group.group_key, {
                          face_finish_type: event.target.value,
                          face_oracal_code:
                            event.target.value === "none" ? null : group.face_oracal_code,
                          face_oracal_name:
                            event.target.value === "none" ? null : group.face_oracal_name,
                          face_vinyl_roll_width_mm: normalizeFaceVinylRollWidthMm(
                            event.target.value,
                            group.face_vinyl_roll_width_mm,
                          ),
                        })
                      }
                      data-testid={`intake-v6-face-type-${group.group_key}`}
                    >
                      {effectiveFaceOptions.map((opt) => (
                        <option key={opt.value} value={opt.value}>
                          {opt.label}
                        </option>
                      ))}
                    </select>
                  </label>

                  {showRollWidth ? (
                    <label className="block min-w-0">
                      <span className={v6.label}>Lățime rolă (mm)</span>
                      <select
                        className={selectClass}
                        value={
                          normalizeFaceVinylRollWidthMm(
                            group.face_finish_type,
                            group.face_vinyl_roll_width_mm,
                          ) ?? ""
                        }
                        onChange={(event) => {
                          const raw = event.target.value;
                          patchGroup(group.group_key, {
                            face_vinyl_roll_width_mm: raw ? Number(raw) : null,
                          });
                        }}
                        data-testid={`intake-v6-face-roll-width-${group.group_key}`}
                      >
                        <option value="">—</option>
                        {INTAKE_ROLL_WIDTH_OPTIONS.map((option) => (
                          <option key={option.value} value={option.value}>
                            {option.label}
                          </option>
                        ))}
                      </select>
                    </label>
                  ) : null}
                </div>

                {showColor ? (
                  <div
                    className="mt-3 border-t border-[#2A3548]/60 pt-3"
                    data-testid={`intake-v6-face-color-row-${group.group_key}`}
                  >
                    <ColorRegistrySelect
                      label="Culoare față"
                      valueCode={group.face_oracal_code ?? null}
                      filter={{
                        system: "ORACAL",
                        series: oracalColorPaletteSeriesForFace(group.face_finish_type),
                        usageScope: "face_vinyl",
                      }}
                      onChange={(item) =>
                        patchGroup(group.group_key, {
                          face_oracal_code: item?.code,
                          face_oracal_name: item?.name,
                        })
                      }
                      testId={`intake-v6-face-color-${group.group_key}`}
                    />
                  </div>
                ) : null}
              </div>
            </div>
          );
        })}
      </div>
    </div>
  );
}
