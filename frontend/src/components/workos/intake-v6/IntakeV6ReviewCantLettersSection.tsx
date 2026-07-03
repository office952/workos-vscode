import IntakeV6ReturnCantFields from "./IntakeV6ReturnCantFields";
import type { IntakeV6LetterGroupFinish } from "@/lib/intakeV6/intakeV6LetterGroups";
import {
  letterGroupToReturnCant,
  patchLetterGroupFromReturnCant,
} from "@/lib/intakeV6/intakeV6ReturnCantBridge";
import { v6 } from "./atoms/intakeV6Presentation";
import {
  copyFirstCantSettingsToAllGroups,
  patchLetterGroupFinishes,
} from "./letterGroupFinishSectionHelpers";

export default function IntakeV6ReviewCantLettersSection({
  groups,
  onChange,
  allowedReturnDepthMm,
}: {
  groups: IntakeV6LetterGroupFinish[];
  onChange: (groups: IntakeV6LetterGroupFinish[]) => void;
  allowedReturnDepthMm?: readonly number[];
}) {
  if (groups.length === 0) return null;

  function patchGroup(groupKey: string, patch: Partial<IntakeV6LetterGroupFinish>) {
    onChange(patchLetterGroupFinishes(groups, groupKey, patch));
  }

  return (
    <div className={`${v6.card} mb-4`} data-testid="intake-v6-letter-group-cant-finishes">
      <p className="mb-3 text-[11px] text-slate-400" data-testid="intake-v6-cant-letters-helper">
        Laterala literei / adâncimea volumului.
      </p>
      {groups.length > 1 ? (
        <div className="mb-3 flex justify-end">
          <button
            type="button"
            className={`${v6.btnGhost} text-[10px]`}
            onClick={() => onChange(copyFirstCantSettingsToAllGroups(groups))}
            data-testid="intake-v6-copy-cant-to-all"
          >
            Copiază cantul la toate layerele
          </button>
        </div>
      ) : null}
      <div className="space-y-3">
        {groups.map((group) => (
          <div
            key={group.group_key}
            className="rounded border border-[#2A3548] bg-[#0A0F1A]/40 p-3"
            data-testid={`intake-v6-letter-group-${group.group_key}`}
          >
            <div className="mb-2 flex items-center gap-2">
              <span
                className="h-6 w-6 shrink-0 rounded border border-slate-600"
                style={{ backgroundColor: group.source_fill_color ?? "#64748b" }}
                data-testid={`intake-v6-letter-group-cant-swatch-${group.group_key}`}
                aria-hidden
              />
              <p className="text-[12px] font-semibold text-slate-200">{group.layer_name}</p>
            </div>
            <IntakeV6ReturnCantFields
              layout="review"
              idPrefix={`v6-${group.group_key}`}
              returnCant={letterGroupToReturnCant(group)}
              onReturnChange={(cant) =>
                patchGroup(group.group_key, patchLetterGroupFromReturnCant(cant))
              }
              testIdPrefix={`intake-v6-letter-group-return-${group.group_key}`}
              allowedReturnDepthMm={allowedReturnDepthMm}
            />
          </div>
        ))}
      </div>
    </div>
  );
}
