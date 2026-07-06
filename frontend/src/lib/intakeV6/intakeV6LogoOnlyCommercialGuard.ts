export const LOGO_ONLY_NOT_OFFERABLE_STATUS = "logo_only_candidate_not_offerable";

export const LOGO_ONLY_COMMERCIAL_GUARD_TITLE = "Logo-only candidate";

export const LOGO_ONLY_COMMERCIAL_GUARD_MESSAGE =
  "TPL-VOLUMETRIC-LOGO_v1 candidate/read-only · root comercial neofertabil fara owner GO · nu creeaza quote/order/execution.";

export const LOGO_ONLY_COMMERCIAL_CTA_DISABLED_REASON =
  "Draft blocat pentru logo-only candidate. Owner GO necesar pentru root commercial Logo. Nu creeaza quote/order/execution.";

export function isLogoOnlyCandidateNotOfferableStatus(status: string | null | undefined): boolean {
  return status === LOGO_ONLY_NOT_OFFERABLE_STATUS;
}