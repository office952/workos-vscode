# 2026-08-03 — F7F: Owner commercial law activation + Step 3 complete offer total

Branch `feat/capacity-batch-20d-scoped-b-92401`, start HEAD `d4989b21`. Push not authorized,
not performed.

## Why

F7E closed as `PASS_WITH_OWNER_RULE_BLOCKERS`: several finishes had no commercial rule and Step 3
presented a Litere-only figure as though it were the whole offer (residual A-F4). The Owner issued
the missing rates and required Step 3 to show each commercial product separately plus one complete
total sourced from CPP.

## What changed

Every Owner rate now lives in the commercial rule registry as a classified rule, and CPP resolves
it: Oracal 651 at 5 EUR/m² with no colour tier, Oracal 8500 at 17 or 13.5 EUR/m² by confirmed roll
width, print + laminate at 10 EUR/m², vinyl application at a single 3 EUR/m² per proven applied
surface, ACM sheet at 15 EUR/m² with mirror as a 40 EUR/m² replacement rate.

Rules and lines now carry a `commercial_product_key`, so CPP can publish a
`commercial_product_breakdown` with a `Litere` subtotal, a `Panou ACM` subtotal, and one complete
offer total. Step 3 renders that breakdown directly instead of summing anything in React.

## The decision worth remembering

The engine refuses to publish a single total when the offer mixes currencies. Registry operations
price in RON and Owner material law is EUR, and without a provenance-bearing exchange rate there is
no honest way to add them. Step 3 shows `Total ofertă indisponibil` with the reason rather than a
plausible-looking number. The same fail-closed reflex covers a missing Oracal 8500 roll width, an
unknown ACM shell, and mirror ACM on an exterior installation without a proven supplier SKU — in
each case the price stays `null` instead of borrowing a neighbouring rate.

A softer state was added alongside it: when a total exists but omits lines that are still waiting on
an Owner decision, it is labelled `Total ofertă (parțial)` with the pending line codes, so a partial
figure is never read as complete.

## The trap in "the field already exists"

Oracal 8500 prices off the confirmed roll width, and intake already had a
`face_vinyl_roll_width_mm`, so reading it looked finished. It was not: that job-level field is a
*derived dominant-value projection* of per-letter-group captures. On a mixed-face job it can go null
while an 8500 group genuinely exists, or carry a width belonging to an entirely different face — the
first would block a priceable offer, the second would price 8500 at the wrong tier and look
completely plausible. CPP now reads the width from the letter groups that actually carry the 8500
face, requires those groups to be operator-confirmed, and fails closed when they disagree.

The residual is that the width select is pre-filled with 1000 mm, so a defaulted width and a chosen
one are indistinguishable at field level. The group `confirmed` flag is the closest existing
operator signal, so that is what gates the rate; a real per-field confirmation is an intake contract
change and an Owner decision.

## Open for the Owner

Operation rates in EUR (or an exchange rate with provenance) before a single complete total can be
published; a rate for Oracal 641, which was not in the Owner list; a rate for `printed_vinyl`.

## Evidence

`docs/qa/workos-f7f-owner-commercial-law-step3-complete-total-v1/` — architecture readback,
scenario matrix, live runtime captures, Step 3 screenshot, protected-baseline read, and the
baseline-vs-F7F backend sweep comparison.
