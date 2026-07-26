"""Single canonical mapping source for offer_scope sold modules → runtime mini-modules."""

from __future__ import annotations

# Slice 1: safe standalone subset codes (tests + resolver allow-list).
SLICE1_ACTIVE_CANONICAL: frozenset[str] = frozenset(
    {"FACE", "RETURN-CANT", "BACK", "LIGHTING", "ELECTRICAL"}
)

# Mapped but not safe for component_subset in V1 (whole-module buckets).
SLICE1_DEFERRED_CANONICAL: frozenset[str] = frozenset({"FINISH", "MOUNTING"})

# One mapping source — runtime mini_module_code sets per canonical sold code.
CANONICAL_TO_RUNTIME: dict[str, frozenset[str]] = {
    "FACE": frozenset({"debitare_fata"}),
    "RETURN-CANT": frozenset({"modelare_cant"}),
    "BACK": frozenset({"debitare_spate"}),
    # SLICE1_TEMPORARY_WHOLE_MODULE — op split deferred to later slice.
    "LIGHTING": frozenset({"sistem_led"}),
    "ELECTRICAL": frozenset({"sistem_led"}),
    # Surface finish only — installation template / packaging are separate runtime codes.
    "FINISH": frozenset({"finisaje"}),
    # Narrowed: no surface finish / packaging leakage from MOUNTING-only scope.
    "MOUNTING": frozenset({"structura_suport", "sablon_montaj"}),
}

ALL_CANONICAL_SOLD_MODULES: frozenset[str] = frozenset(CANONICAL_TO_RUNTIME.keys())


def derive_calc_modules(canonical_sold: list[str]) -> list[str]:
    """Calc dependencies — never sold, never priced."""
    calc: set[str] = set()
    if canonical_sold:
        calc.add("GEOMETRY")
    sold = set(canonical_sold)
    if "RETURN-CANT" in sold:
        calc.add("PERIMETER")
    if sold & {"BACK", "FINISH", "FACE", "LIGHTING", "MOUNTING"}:
        calc.add("FACE_AREA")
    if "ELECTRICAL" in sold:
        calc.add("LED_COUNT")
    order = ("GEOMETRY", "PERIMETER", "FACE_AREA", "LED_COUNT")
    return [code for code in order if code in calc]


def runtime_modules_for_canonical(canonical_sold: list[str]) -> set[str]:
    runtime: set[str] = set()
    for code in canonical_sold:
        runtime.update(CANONICAL_TO_RUNTIME.get(code, frozenset()))
    return runtime


def runtime_to_canonical(runtime_module: str) -> str | None:
    """Reverse lookup — first matching canonical in stable priority order."""
    if not runtime_module:
        return None
    matches = [
        canonical
        for canonical, runtimes in CANONICAL_TO_RUNTIME.items()
        if runtime_module in runtimes
    ]
    if not matches:
        return None
    priority = ("FACE", "RETURN-CANT", "BACK", "LIGHTING", "ELECTRICAL", "FINISH", "MOUNTING")
    for code in priority:
        if code in matches:
            return code
    return matches[0]
