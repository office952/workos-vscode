/** Shared grid for collapsed layer card headers — columns align across cards. */
export const REVIEW_LAYER_CARD_HEADER_GRID =
  "grid w-full min-w-0 grid-cols-[1.25rem_1.25rem_minmax(4rem,0.75fr)_minmax(0,1fr)_minmax(0,1fr)_minmax(0,1fr)_auto_1.25rem] items-center gap-x-2";

export const REVIEW_LAYER_CARD_FACE_SUMMARY_CLASS =
  "min-w-0 truncate text-[13px] text-slate-400 tabular-nums";

export const REVIEW_LAYER_CARD_CANT_SUMMARY_CLASS =
  "min-w-0 truncate text-[13px] text-slate-300 tabular-nums";

export const REVIEW_LAYER_CARD_SPATE_SUMMARY_CLASS =
  "min-w-0 truncate text-[13px] text-slate-300 tabular-nums";

export const REVIEW_LAYER_CARD_NAME_CLASS =
  "min-w-0 truncate text-[14px] font-semibold text-slate-100";

/** Stacked expanded body — Fata → Cant → Spate; no empty reserved columns. */
export const REVIEW_LAYER_CARD_EXPANDED_STACK_CLASS =
  "flex min-w-0 flex-col gap-3.5 border-t border-[#2A3548] px-2.5 py-3";
