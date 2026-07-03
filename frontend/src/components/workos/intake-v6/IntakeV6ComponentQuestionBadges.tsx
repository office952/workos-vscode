import {
  getIntakeV6ComponentQuestionChips,
  type IntakeV6ComponentQuestionDisplayChip,
  type IntakeV6ComponentQuestionKey,
} from "@/lib/intakeV6/intakeV6ComponentQuestionDisplay";
import { AtomsBadge, type AtomsBadgeTone } from "./atoms/intakeV6Presentation";

function chipTone(tone: IntakeV6ComponentQuestionDisplayChip["tone"]): AtomsBadgeTone {
  if (tone === "owner") return "ok";
  if (tone === "blocker") return "pending";
  if (tone === "warning") return "action";
  return "muted";
}

export default function IntakeV6ComponentQuestionBadges({
  question,
  testId,
  className = "",
}: {
  question: IntakeV6ComponentQuestionKey;
  testId: string;
  className?: string;
}) {
  return (
    <div className={`flex flex-wrap items-center gap-1 ${className}`} data-testid={testId}>
      {getIntakeV6ComponentQuestionChips(question).map((chip) => (
        <AtomsBadge key={chip.text} tone={chipTone(chip.tone)}>
          {chip.text}
        </AtomsBadge>
      ))}
    </div>
  );
}