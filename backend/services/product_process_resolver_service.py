"""Pure product-process resolver — deterministic DAG from component + interface contracts.

No DB. No snapshot. No CPP. No Intake mutation. No task materialization.
"""

from __future__ import annotations

import hashlib
import json
from collections import defaultdict, deque
from typing import Any

from data.product_process.catalogs import (
    ALLOWED_MAINS_CABLE_LENGTHS_M,
    CATALOG_VERSION,
    PROCESS_NAMES_RO,
    PROCESS_TO_MINI_MODULE,
    PROCESS_TO_PRICED_OPERATION,
)
from data.product_process.volumetric_letters_v1 import (
    COMP_ALUCOBOND,
    COMP_BACK,
    COMP_CANT,
    COMP_FACE,
    COMP_LIGHTING,
    COMP_METAL_SUPPORT,
    COMP_TEMPLATE,
    COMPONENT_CONTRACTS,
    CONTRACT_VERSION,
    IFACE_BACK_LIGHTING,
    IFACE_BACK_SUPPORT,
    IFACE_BODY_BACK,
    IFACE_FACE_CANT,
    IFACE_LIGHTING_SUPPORT,
    INTERFACE_CONTRACTS,
    NO_SUPPORT_EXTRA_PROCESSES,
    PRODUCT_SHARED_PROCESSES,
    PRODUCT_TEMPLATE_CODE,
)
from schemas.product_process_contract import (
    ProductProcessResolveInput,
    ResolvedMaterialRequirement,
    ResolvedProcessRule,
    ResolvedProductProcessGraph,
    ResolverIssue,
)

FORBIDDEN_PROCESS_CODES = frozenset(
    {
        "ADHESIVE_CURING",
        "CURE_ADHESIVE",
        "BACK_DRILLING",
        "DRILL_BACK",
    }
)


def _stable_hash(payload: Any) -> str:
    raw = json.dumps(payload, sort_keys=True, ensure_ascii=False, separators=(",", ":"), default=str)
    return hashlib.sha256(raw.encode("utf-8")).hexdigest()


def _active_when_ok(active_when: dict[str, Any], ctx: dict[str, Any]) -> bool:
    if not active_when:
        return True
    for key, expected in active_when.items():
        if ctx.get(key) != expected:
            return False
    return True


def _normalize_active_components(inp: ProductProcessResolveInput) -> list[str]:
    """Derive active components from explicit list + support/template/lighting flags."""
    requested = {str(c).strip().upper() for c in inp.active_components if str(c).strip()}
    # Alias normalization
    aliases = {
        "RETURN-CANT": COMP_CANT,
        "RETURN_CANT": COMP_CANT,
        "ALUCOBOND": COMP_ALUCOBOND,
        "METAL_BARS": COMP_METAL_SUPPORT,
        "SUPPORT": COMP_METAL_SUPPORT,
    }
    normalized: set[str] = set()
    for code in requested:
        normalized.add(aliases.get(code, code))

    # If caller omitted components, compose from support/lighting defaults for full-product fixtures
    if not normalized:
        normalized.update({COMP_FACE, COMP_CANT, COMP_BACK})
        if inp.illuminated:
            normalized.add(COMP_LIGHTING)
        if inp.support_type == "metal_bars":
            normalized.add(COMP_METAL_SUPPORT)
        elif inp.support_type == "alucobond_cased":
            normalized.add(COMP_ALUCOBOND)
        if inp.template_selected:
            normalized.add(COMP_TEMPLATE)
    else:
        # Enforce support exclusivity
        if inp.support_type == "metal_bars":
            normalized.add(COMP_METAL_SUPPORT)
            normalized.discard(COMP_ALUCOBOND)
        elif inp.support_type == "alucobond_cased":
            normalized.add(COMP_ALUCOBOND)
            normalized.discard(COMP_METAL_SUPPORT)
        else:
            normalized.discard(COMP_METAL_SUPPORT)
            normalized.discard(COMP_ALUCOBOND)
        if inp.template_selected:
            normalized.add(COMP_TEMPLATE)
        else:
            normalized.discard(COMP_TEMPLATE)
        if not inp.illuminated:
            normalized.discard(COMP_LIGHTING)

    order = [
        COMP_FACE,
        COMP_CANT,
        COMP_BACK,
        COMP_LIGHTING,
        COMP_METAL_SUPPORT,
        COMP_ALUCOBOND,
        COMP_TEMPLATE,
    ]
    return [c for c in order if c in normalized]


def _active_interfaces(components: set[str]) -> list[str]:
    out: list[str] = []
    if COMP_FACE in components and COMP_CANT in components:
        out.append(IFACE_FACE_CANT)
    if COMP_BACK in components and COMP_LIGHTING in components:
        out.append(IFACE_BACK_LIGHTING)
    if COMP_BACK in components and (COMP_METAL_SUPPORT in components or COMP_ALUCOBOND in components):
        out.append(IFACE_BACK_SUPPORT)
    if COMP_LIGHTING in components and (COMP_METAL_SUPPORT in components or COMP_ALUCOBOND in components):
        out.append(IFACE_LIGHTING_SUPPORT)
    if COMP_FACE in components and COMP_CANT in components and COMP_BACK in components:
        out.append(IFACE_BODY_BACK)
    return out


def _build_context(inp: ProductProcessResolveInput) -> dict[str, Any]:
    mains_selected = inp.mains_cable_length_m is not None
    return {
        "cant_finish": inp.cant_finish,
        "support_type": inp.support_type,
        "screw_finish": inp.screw_finish,
        "template_selected": inp.template_selected,
        "mains_cable_selected": mains_selected,
        "service_corner_required": inp.support_type == "alucobond_cased",
        "illuminated": inp.illuminated,
        "geometry_confirmed": inp.geometry_confirmed,
        "led_layout_confirmed": inp.led_layout_confirmed,
    }


def _collect_raw_processes(
    *,
    components: list[str],
    interfaces: list[str],
    ctx: dict[str, Any],
    inp: ProductProcessResolveInput,
) -> list[dict[str, Any]]:
    collected: list[dict[str, Any]] = []

    def consider(proc: dict[str, Any], *, source_component: str | None, source_interface: str | None, reason: str) -> None:
        code = str(proc["process_code"])
        if code in FORBIDDEN_PROCESS_CODES:
            return
        if not _active_when_ok(proc.get("active_when") or {}, ctx):
            return
        row = dict(proc)
        row["source_component"] = source_component
        row["source_interface"] = source_interface
        row["active_reason"] = reason
        collected.append(row)

    lighting_active = COMP_LIGHTING in components
    for shared in PRODUCT_SHARED_PROCESSES:
        code = str(shared["process_code"])
        # QC → clean → pack require lighting uniformity for illuminated letters pilot.
        if code in ("QUALITY_CONTROL", "CLEAN_PRODUCT", "PACK_PRODUCT") and not lighting_active:
            continue
        consider(shared, source_component=None, source_interface=None, reason="product_shared")

    for comp in components:
        contract = COMPONENT_CONTRACTS.get(comp) or {}
        for proc in contract.get("processes") or []:
            consider(proc, source_component=comp, source_interface=None, reason=f"component:{comp}")

    for iface in interfaces:
        contract = INTERFACE_CONTRACTS.get(iface) or {}
        for proc in contract.get("processes") or []:
            consider(proc, source_component=None, source_interface=iface, reason=f"interface:{iface}")

    if inp.support_type == "none" and COMP_LIGHTING in components:
        for proc in NO_SUPPORT_EXTRA_PROCESSES:
            consider(proc, source_component=None, source_interface=None, reason="no_support_branch")

    # Vinyl: FORM must depend on APPLY
    if ctx.get("cant_finish") == "vinyl":
        for row in collected:
            if row["process_code"] == "FORM_CANT_CNC":
                deps = list(row.get("depends_on") or [])
                if "APPLY_CANT_VINYL" not in deps:
                    deps.append("APPLY_CANT_VINYL")
                row["depends_on"] = deps
                req = list(row.get("requires_states") or [])
                if "CANT_VINYLED" not in req:
                    req.append("CANT_VINYLED")
                row["requires_states"] = req

    # Metal / Alucobond: TEST_LED_ON waits for mains/PSU path when support present
    if COMP_METAL_SUPPORT in components:
        for row in collected:
            if row["process_code"] == "TEST_LED_ON":
                deps = list(row.get("depends_on") or [])
                for d in ("INSTALL_MAINS_CABLE", "INSTALL_POWER_SUPPLY", "CONNECT_LETTERS"):
                    if d not in deps:
                        # only add if those processes will be active
                        pass
                # Prefer wiring complete before test when support installs PSU
                if ctx.get("mains_cable_selected") and "INSTALL_MAINS_CABLE" not in deps:
                    deps.append("INSTALL_MAINS_CABLE")
                elif "INSTALL_POWER_SUPPLY" not in deps:
                    deps.append("INSTALL_POWER_SUPPLY")
                row["depends_on"] = deps
    if COMP_ALUCOBOND in components:
        for row in collected:
            if row["process_code"] == "TEST_LED_ON":
                deps = list(row.get("depends_on") or [])
                if ctx.get("mains_cable_selected") and "INSTALL_MAINS_CABLE" not in deps:
                    deps.append("INSTALL_MAINS_CABLE")
                elif "INSTALL_POWER_SUPPLY_NEAR_SERVICE_CORNER" not in deps:
                    deps.append("INSTALL_POWER_SUPPLY_NEAR_SERVICE_CORNER")
                row["depends_on"] = deps

    # BODY_BACK: RAL requires VOLUME_FINISH_READY before attach when RAL active
    if ctx.get("cant_finish") == "ral":
        for row in collected:
            if row["process_code"] == "ATTACH_BODY_TO_BACK":
                req = list(row.get("requires_states") or [])
                if "VOLUME_FINISH_READY" not in req:
                    req.append("VOLUME_FINISH_READY")
                row["requires_states"] = req
                deps = list(row.get("depends_on") or [])
                if "INSPECT_VOLUME_FINISH" not in deps:
                    deps.append("INSPECT_VOLUME_FINISH")
                row["depends_on"] = deps

    for code in inp.force_include_processes:
        collected.append(
            {
                "process_code": code,
                "requires_states": [],
                "produces_states": [],
                "depends_on": [],
                "material_roles": [],
                "required_capabilities": [],
                "active_when": {},
                "parallel_group": None,
                "source_component": None,
                "source_interface": None,
                "active_reason": "force_include",
            }
        )

    # Deduplicate by process_code (first wins; interfaces may refine later)
    by_code: dict[str, dict[str, Any]] = {}
    for row in collected:
        code = str(row["process_code"])
        if code not in by_code:
            by_code[code] = row
        else:
            # Merge depends_on / states / materials
            prev = by_code[code]
            for key in ("depends_on", "requires_states", "produces_states", "material_roles", "required_capabilities"):
                prev[key] = sorted(set((prev.get(key) or []) + (row.get(key) or [])))
            if row.get("source_interface") and not prev.get("source_interface"):
                prev["source_interface"] = row["source_interface"]
            if row.get("source_component") and not prev.get("source_component"):
                prev["source_component"] = row["source_component"]
    return list(by_code.values())


def _wire_state_dependencies(processes: list[dict[str, Any]]) -> list[ResolverIssue]:
    """Add depends_on edges from requires_states → producer process among active set."""
    blockers: list[ResolverIssue] = []
    producers: dict[str, list[str]] = defaultdict(list)
    codes = {str(p["process_code"]) for p in processes}
    for p in processes:
        for state in p.get("produces_states") or []:
            producers[str(state)].append(str(p["process_code"]))

    for p in processes:
        deps = set(p.get("depends_on") or [])
        for state in p.get("requires_states") or []:
            makers = producers.get(str(state)) or []
            # Prefer other processes (not self)
            makers = [m for m in makers if m != p["process_code"]]
            if not makers:
                # Some states are config-confirmed, not process-produced
                if state in ("LED_LAYOUT_CONFIRMED",) and True:
                    continue
                if state == "GEOMETRY_CONFIRMED" and "CONFIRM_GEOMETRY" in codes:
                    deps.add("CONFIRM_GEOMETRY")
                    continue
                blockers.append(
                    ResolverIssue(
                        code="missing_state_producer",
                        message=f"No active producer for required state {state} (process {p['process_code']})",
                        details={"state": state, "process_code": p["process_code"]},
                    )
                )
                continue
            # Deterministic: pick lexicographically first producer if multiple
            deps.add(sorted(makers)[0])
        # Drop deps on inactive processes
        deps = {d for d in deps if d in codes}
        p["depends_on"] = sorted(deps)
    return blockers


def _topo_sort(processes: list[dict[str, Any]]) -> tuple[list[str], bool, list[str]]:
    codes = [str(p["process_code"]) for p in processes]
    code_set = set(codes)
    indeg: dict[str, int] = {c: 0 for c in codes}
    adj: dict[str, list[str]] = defaultdict(list)
    for p in processes:
        src = str(p["process_code"])
        for dep in p.get("depends_on") or []:
            if dep not in code_set:
                continue
            # edge dep -> src (dep before src)
            adj[dep].append(src)
            indeg[src] += 1

    # Stable: alphabet among zero-indegree, but prefer sequence of known prep first
    priority = {
        "ANALYZE_SVG": 0,
        "CONFIRM_GEOMETRY": 1,
        "CUT_FACE": 10,
        "CUT_FOREX_BACK": 10,
        "PREPARE_CANT_STRIP": 11,
        "APPLY_CANT_VINYL": 12,
        "FORM_CANT_CNC": 13,
        "BOND_FACE_TO_CANT": 20,
        "PACK_PRODUCT": 900,
    }
    q = sorted([c for c, d in indeg.items() if d == 0], key=lambda c: (priority.get(c, 100), c))
    queue = deque(q)
    order: list[str] = []
    while queue:
        node = queue.popleft()
        order.append(node)
        for nxt in sorted(adj[node], key=lambda c: (priority.get(c, 100), c)):
            indeg[nxt] -= 1
            if indeg[nxt] == 0:
                # insert keeping sort
                queue.append(nxt)
                queue = deque(sorted(queue, key=lambda c: (priority.get(c, 100), c)))
    cycle = len(order) != len(codes)
    unresolved = sorted(code_set - set(order)) if cycle else []
    return order, cycle, unresolved


def resolve_product_process_graph(inp: ProductProcessResolveInput) -> ResolvedProductProcessGraph:
    """Resolve active processes + real depends_on DAG. Pure and deterministic."""
    warnings: list[ResolverIssue] = []
    blockers: list[ResolverIssue] = []

    if inp.product_template_code not in (PRODUCT_TEMPLATE_CODE, "TPL-VOLUMETRIC-LETTERS"):
        blockers.append(
            ResolverIssue(
                code="unsupported_product_template",
                message=f"Resolver pilot supports {PRODUCT_TEMPLATE_CODE} only",
                details={"product_template_code": inp.product_template_code},
            )
        )

    if inp.mains_cable_length_m is not None:
        length = float(inp.mains_cable_length_m)
        if length not in ALLOWED_MAINS_CABLE_LENGTHS_M:
            blockers.append(
                ResolverIssue(
                    code="invalid_mains_cable_length",
                    message="mains_cable_length_m must be in 2.5..25 step 2.5 (not hardcoded 5)",
                    details={"value": length},
                )
            )
        # Explicitly reject silent defaulting to 5.0 when None — transport only

    if inp.support_type == "alucobond_cased" and not inp.power_supply_service_corner:
        blockers.append(
            ResolverIssue(
                code="service_corner_required",
                message="Alucobond cased panel requires power_supply_service_corner",
                details={},
            )
        )

    components = _normalize_active_components(inp)
    comp_set = set(components)
    interfaces = _active_interfaces(comp_set)
    ctx = _build_context(inp)

    # Inactive isolation: template off → COMP_TEMPLATE absent (already). Support exclusivity already.

    raw = _collect_raw_processes(components=components, interfaces=interfaces, ctx=ctx, inp=inp)

    # Config-confirmed states: inject synthetic producers only as virtual for GEOMETRY / LED layout
    # CONFIRM_GEOMETRY already produces GEOMETRY_CONFIRMED.
    # LED_LAYOUT_CONFIRMED is operator config — if lighting active and confirmed, no process needed.
    if COMP_LIGHTING in comp_set and not inp.led_layout_confirmed:
        blockers.append(
            ResolverIssue(
                code="led_layout_not_confirmed",
                message="LED_LAYOUT_CONFIRMED required when LIGHTING active",
                details={},
            )
        )

    if not inp.geometry_confirmed:
        blockers.append(
            ResolverIssue(
                code="geometry_not_confirmed",
                message="GEOMETRY_CONFIRMED required",
                details={},
            )
        )

    if inp.inject_missing_producer_state:
        for p in raw:
            if p["process_code"] == "CUT_FACE":
                req = list(p.get("requires_states") or [])
                req.append(inp.inject_missing_producer_state)
                p["requires_states"] = req

    state_blockers = _wire_state_dependencies(raw)
    blockers.extend(state_blockers)

    if inp.inject_cycle_edge:
        a, b = inp.inject_cycle_edge
        for p in raw:
            if p["process_code"] == a:
                deps = list(p.get("depends_on") or [])
                if b not in deps:
                    deps.append(b)
                p["depends_on"] = deps
            if p["process_code"] == b:
                deps = list(p.get("depends_on") or [])
                if a not in deps:
                    deps.append(a)
                p["depends_on"] = deps

    order, cycle, unresolved = _topo_sort(raw)
    if cycle:
        blockers.append(
            ResolverIssue(
                code="dependency_cycle",
                message="Process dependency graph contains a cycle",
                details={"unresolved": unresolved},
            )
        )

    # Forbidden inactive leakage checks (as warnings if somehow present)
    codes = {str(p["process_code"]) for p in raw}
    if inp.support_type != "metal_bars":
        for bad in ("INSTALL_CABLE_CHANNEL", "FABRICATE_METAL_SUPPORT"):
            if bad in codes and inp.support_type != "metal_bars":
                if bad == "FABRICATE_METAL_SUPPORT" and inp.support_type != "metal_bars":
                    blockers.append(
                        ResolverIssue(
                            code="inactive_support_leakage",
                            message=f"{bad} active while support_type={inp.support_type}",
                            details={},
                        )
                    )
                if bad == "INSTALL_CABLE_CHANNEL" and inp.support_type != "metal_bars":
                    blockers.append(
                        ResolverIssue(
                            code="inactive_support_leakage",
                            message="INSTALL_CABLE_CHANNEL active without metal_bars",
                            details={},
                        )
                    )
    if inp.support_type != "alucobond_cased":
        for bad in ("FABRICATE_ALUCOBOND_CASED_PANEL", "ROUTE_WIRING_BEHIND_PANEL", "INSTALL_POWER_SUPPLY_NEAR_SERVICE_CORNER"):
            if bad in codes:
                blockers.append(
                    ResolverIssue(
                        code="inactive_support_leakage",
                        message=f"{bad} active while support_type={inp.support_type}",
                        details={},
                    )
                )
    if inp.support_type != "none":
        for bad in ("PACK_POWER_SUPPLY_SEPARATELY", "LABEL_POWER_SUPPLY", "RIGIDIZE_FOR_TRANSPORT"):
            if bad in codes:
                blockers.append(
                    ResolverIssue(
                        code="inactive_support_leakage",
                        message=f"{bad} active while support_type={inp.support_type}",
                        details={},
                    )
                )
    if not inp.template_selected and "GENERATE_INSTALLATION_TEMPLATE" in codes:
        blockers.append(
            ResolverIssue(
                code="inactive_template_leakage",
                message="GENERATE_INSTALLATION_TEMPLATE active while template_selected=false",
                details={},
            )
        )
    if inp.cant_finish != "vinyl" and "APPLY_CANT_VINYL" in codes:
        blockers.append(
            ResolverIssue(
                code="inactive_cant_branch_leakage",
                message="APPLY_CANT_VINYL active for non-vinyl cant",
                details={},
            )
        )
    if inp.cant_finish != "ral":
        for bad in ("PAINT_VOLUME_RAL", "MASK_FACE", "DRY_VOLUME_PAINT", "UNMASK_FACE", "INSPECT_VOLUME_FINISH"):
            if bad in codes:
                blockers.append(
                    ResolverIssue(
                        code="inactive_cant_branch_leakage",
                        message=f"{bad} active for cant_finish={inp.cant_finish}",
                        details={},
                    )
                )

    # No adhesive curing / drilling
    for bad in FORBIDDEN_PROCESS_CODES:
        if bad in codes:
            blockers.append(
                ResolverIssue(code="forbidden_process", message=bad, details={})
            )

    seq_map = {code: i + 1 for i, code in enumerate(order)}
    rules: list[ResolvedProcessRule] = []
    materials: list[ResolvedMaterialRequirement] = []
    caps: set[str] = set()
    produced: set[str] = set()
    parallel_groups: dict[str, list[str]] = defaultdict(list)

    by_code = {str(p["process_code"]): p for p in raw}
    for code in order if not cycle else sorted(by_code.keys()):
        p = by_code[code]
        rule = ResolvedProcessRule(
            process_code=code,
            name=PROCESS_NAMES_RO.get(code, code),
            source_component=p.get("source_component"),
            source_interface=p.get("source_interface"),
            requires_states=list(p.get("requires_states") or []),
            produces_states=list(p.get("produces_states") or []),
            depends_on=list(p.get("depends_on") or []),
            material_roles=list(p.get("material_roles") or []),
            required_capabilities=list(p.get("required_capabilities") or []),
            sequence_hint=seq_map.get(code),
            parallel_group=p.get("parallel_group"),
            active_reason=p.get("active_reason"),
            contract_version=CONTRACT_VERSION,
            priced_operation=PROCESS_TO_PRICED_OPERATION.get(code),
            mini_module_code=PROCESS_TO_MINI_MODULE.get(code),
        )
        rules.append(rule)
        for role in rule.material_roles:
            materials.append(
                ResolvedMaterialRequirement(
                    material_role=role,
                    source_process=code,
                    source_component=rule.source_component,
                    source_interface=rule.source_interface,
                )
            )
        caps.update(rule.required_capabilities)
        produced.update(rule.produces_states)
        if rule.parallel_group:
            parallel_groups[rule.parallel_group].append(code)

    # Sort materials deterministically
    materials_sorted = sorted(
        materials,
        key=lambda m: (m.material_role, m.source_process or "", m.source_component or ""),
    )

    component_hash = _stable_hash({c: COMPONENT_CONTRACTS[c] for c in components if c in COMPONENT_CONTRACTS})
    interface_hash = _stable_hash({i: INTERFACE_CONTRACTS[i] for i in interfaces if i in INTERFACE_CONTRACTS})
    graph_payload = {
        "contract_version": CONTRACT_VERSION,
        "components": components,
        "interfaces": interfaces,
        "rules": [
            {
                "process_code": r.process_code,
                "depends_on": r.depends_on,
                "requires_states": r.requires_states,
                "produces_states": r.produces_states,
                "material_roles": r.material_roles,
            }
            for r in rules
        ],
        "config": {
            "cant_finish": inp.cant_finish,
            "support_type": inp.support_type,
            "screw_finish": inp.screw_finish,
            "service_corner": inp.power_supply_service_corner,
            "mains_cable_length_m": inp.mains_cable_length_m,
            "template_selected": inp.template_selected,
        },
    }
    process_graph_hash = _stable_hash(graph_payload)
    graph_hash = _stable_hash(
        {
            "component_contract_hash": component_hash,
            "interface_contract_hash": interface_hash,
            "process_graph_hash": process_graph_hash,
            "catalog_version": CATALOG_VERSION,
        }
    )

    readiness: Any = "ready"
    if blockers:
        readiness = "blocked"
        # On cycle / hard blockers: do not accept partial as ready
        if cycle or any(b.code == "missing_state_producer" for b in blockers):
            # Keep rules for diagnostics but mark blocked
            pass

    config_echo = {
        "cant_finish": inp.cant_finish,
        "support_type": inp.support_type,
        "screw_finish": inp.screw_finish,
        "power_supply_service_corner": inp.power_supply_service_corner,
        "mains_cable_length_m": inp.mains_cable_length_m,
        "template_selected": inp.template_selected,
        "illuminated": inp.illuminated,
        "geometry": inp.geometry,
    }

    hard_block = cycle or any(
        b.code in {"missing_state_producer", "dependency_cycle", "unsupported_product_template"}
        for b in blockers
    )
    accept_rules = not hard_block

    return ResolvedProductProcessGraph(
        contract_version=CONTRACT_VERSION,
        catalog_version=CATALOG_VERSION,
        product_template_code=inp.product_template_code,
        active_component_codes=components,
        active_interface_codes=interfaces,
        process_rules=rules if accept_rules else [],
        process_order=order if accept_rules else [],
        material_roles=materials_sorted if accept_rules else [],
        required_capabilities=sorted(caps) if accept_rules else [],
        produced_states=sorted(produced) if accept_rules else [],
        parallel_groups={k: sorted(v) for k, v in sorted(parallel_groups.items())} if accept_rules else {},
        config_echo=config_echo,
        warnings=warnings,
        blockers=blockers,
        component_contract_hash=component_hash,
        interface_contract_hash=interface_hash,
        process_graph_hash=process_graph_hash,
        graph_hash=graph_hash,
        readiness="blocked" if blockers else readiness,
    )


def resolved_graph_to_aggregate_task_rules(graph: ResolvedProductProcessGraph) -> list[dict[str, Any]]:
    """ProductAggregate-compatible task_rules (optional depends_on_process_ids)."""
    if graph.readiness == "blocked" and any(b.code == "dependency_cycle" for b in graph.blockers):
        return []
    rules: list[dict[str, Any]] = []
    for r in graph.process_rules:
        rules.append(
            {
                "task_name": r.process_code,
                "task_type": "process",
                "priced_operation": r.priced_operation,
                "sequence": r.sequence_hint,
                "trigger_condition": r.active_reason,
                "provenance": "derived",
                "mini_module_code": r.mini_module_code,
                "depends_on_process_ids": list(r.depends_on),
                "process_code": r.process_code,
                "requires_states": list(r.requires_states),
                "produces_states": list(r.produces_states),
                "material_roles": list(r.material_roles),
                "required_capabilities": list(r.required_capabilities),
                "source_component": r.source_component,
                "source_interface": r.source_interface,
            }
        )
    return rules
