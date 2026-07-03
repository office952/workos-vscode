import type { IntakeV6LetterGroupFinish } from "@/lib/intakeV6/intakeV6LetterGroups";
import IntakeV6ReviewLetterGroupsSection from "./IntakeV6ReviewLetterGroupsSection";

/** Combined face + cant editor — one card per layer in Review. */
export default function IntakeV6LetterGroupFinishesSection({
  groups,
  onChange,
  faceFinishOptions,
  allowedReturnDepthMm,
}: {
  groups: IntakeV6LetterGroupFinish[];
  onChange: (groups: IntakeV6LetterGroupFinish[]) => void;
  faceFinishOptions?: readonly { value: string; label: string }[];
  allowedReturnDepthMm?: readonly number[];
}) {
  return (
    <div data-testid="intake-v6-letter-group-finishes">
      <IntakeV6ReviewLetterGroupsSection
        groups={groups}
        onChange={onChange}
        faceFinishOptions={faceFinishOptions}
        allowedReturnDepthMm={allowedReturnDepthMm}
      />
    </div>
  );
}
