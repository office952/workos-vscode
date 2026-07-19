import { v6, v6Pilot } from "./atoms/intakeV6Presentation";

/** Compact review labels — no forced min-heights for grid alignment. */
export const REVIEW_FIELD_LABEL_CLASS = `${v6.label} mb-0.5 leading-snug`;

export const REVIEW_SELECT_CLASS =
  "h-7 w-full rounded border border-[#2A3548] bg-[#0A0F1A] px-2 py-0.5 text-[11px]";

/** Letter / lighting pilot field chrome — do not use on Montaj. */
export const PILOT_REVIEW_FIELD_LABEL_CLASS = `${v6Pilot.label} mb-0.5 leading-snug`;

export const PILOT_REVIEW_SELECT_CLASS = v6Pilot.select;

export const REVIEW_FIELD_BLOCK_CLASS = "block min-w-0";

export const REVIEW_COLOR_ROW_SHELL_CLASS = "min-w-0 border-t border-[#2A3548]/50 pt-1.5";

export const REVIEW_FACE_COLUMN_CLASS =
  "min-w-0 sm:border-r sm:border-[#243044]/70 sm:pr-2";

export const REVIEW_CANT_COLUMN_CLASS = "min-w-0";

/** Face + cant side-by-side from sm breakpoint. */
export const REVIEW_LAYER_CARD_GRID_CLASS =
  "grid grid-cols-1 gap-y-1.5 p-2 sm:grid-cols-2 sm:gap-x-2 sm:gap-y-1.5";
