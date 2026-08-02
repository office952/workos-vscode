"""Seed canonical Operational Workforce & Resource Registry data.

Idempotent on employee name + machine_code + operation_code keys.
Does NOT modify CostEngine, Pricing, or Quote flows.

MANUAL RUN ONLY — not invoked on dev boot or seed_sync_all by default.
See docs/qa/BUILD_OPERATIONAL_WORKFORCE_MACHINE_OPERATION_MAPPING_FULL_FOUNDATION.md
"""
from __future__ import annotations

import json
import logging
from typing import Any, Dict, List

from models.employees import Employees
from services.employees import EmployeesService
from services.operational_registry_service import OperationalRegistryService
from sqlalchemy import select

logger = logging.getLogger(__name__)


REAL_EMPLOYEES: List[Dict[str, Any]] = [
    {
        "name": "Calin Cimpean",
        "role": "Grafician / Operator",
        "department": "Atelier",
        "employee_type": "productive",
        "cost_lunar_firma": 8500.0,
        "skill_codes": [
            "SK_GRAPHIC_DESIGN",
            "SK_QUOTING",
            "SK_PRINT_OPERATOR",
            "SK_LAMINATOR_OPERATOR",
            "SK_CUTTER_OPERATOR",
        ],
        "workcenter_codes": ["WC_PRINT", "WC_LAMINATE", "WC_CUT"],
        "resource_codes": ["MCH-EPSON-60800", "MCH-LAMINATOR-XPRO", "MCH-CUTTER-PLOTTER"],
    },
    {
        "name": "Octavian Dumitru",
        "role": "Grafician / Operator",
        "department": "Atelier",
        "employee_type": "productive",
        "cost_lunar_firma": 7000.0,
        "skill_codes": [
            "SK_GRAPHIC_DESIGN",
            "SK_QUOTING",
            "SK_PRINT_OPERATOR",
            "SK_LAMINATOR_OPERATOR",
            "SK_CUTTER_OPERATOR",
        ],
        "workcenter_codes": ["WC_PRINT", "WC_LAMINATE", "WC_CUT"],
        "resource_codes": ["MCH-EPSON-60800", "MCH-LAMINATOR-XPRO", "MCH-CUTTER-PLOTTER"],
    },
    {
        "name": "Florin CNC",
        "role": "Operator CNC",
        "department": "CNC",
        "employee_type": "productive",
        "cost_lunar_firma": 8000.0,
        "skill_codes": [
            "SK_CNC_OPERATOR",
            "SK_CNC_PREP",
            "SK_LETTER_CANT_OPERATOR",
        ],
        "workcenter_codes": ["WC_CNC_ROUTING", "WC_LETTER_FORMING"],
        "resource_codes": ["MCH-CNC-4020", "MCH-CNC-CANT-LITERE"],
    },
    {
        "name": "Putaru Sandu",
        "role": "Lăcătuș / Montator",
        "department": "Producție",
        "employee_type": "productive",
        "cost_lunar_firma": 8000.0,
        "skill_codes": [
            "SK_LOCKSMITH",
            "SK_ASSEMBLY",
            "SK_VINYL_APPLICATOR",
            "SK_ELECTRICIAN",
            "SK_FIELD_INSTALLER",
        ],
        "workcenter_codes": ["WC_METAL_FAB", "WC_ASSEMBLY", "WC_LED_ASSEMBLY", "WC_FIELD_INSTALLATION"],
        "resource_codes": [
            "MCH-WELD-STEEL",
            "MCH-WELD-ALU",
            "WA-WELD-TABLE",
            "WA-ASSEMBLY-01",
            "WA-ASSEMBLY-02",
        ],
    },
    {
        "name": "Vali Colantator",
        "role": "Colantator / Montator",
        "department": "Producție",
        "employee_type": "productive",
        "cost_lunar_firma": 5000.0,
        "skill_codes": [
            "SK_ASSEMBLY",
            "SK_VINYL_APPLICATOR",
            "SK_ELECTRICIAN",
            "SK_FIELD_INSTALLER",
        ],
        "workcenter_codes": ["WC_ASSEMBLY", "WC_LED_ASSEMBLY", "WC_VINYL_APPLICATION", "WC_FIELD_INSTALLATION"],
        "resource_codes": ["WA-ASSEMBLY-01", "WA-ASSEMBLY-02", "MCH-RIGID-FILM-LAMINATOR"],
    },
    {
        "name": "Costi Modelator",
        "role": "Modelator / Colantator",
        "department": "Producție",
        "employee_type": "productive",
        "cost_lunar_firma": 7000.0,
        "skill_codes": [
            "SK_ASSEMBLY",
            "SK_VINYL_APPLICATOR",
            "SK_ELECTRICIAN",
            "SK_FIELD_INSTALLER",
            "SK_LETTER_MODELING",
        ],
        "workcenter_codes": ["WC_ASSEMBLY", "WC_LED_ASSEMBLY", "WC_LETTER_FORMING", "WC_VINYL_APPLICATION"],
        "resource_codes": ["WA-ASSEMBLY-01", "MCH-CNC-CANT-LITERE"],
    },
    {
        "name": "Andrei Goghi",
        "role": "Producție / CNC",
        "department": "Producție",
        "employee_type": "productive",
        "cost_lunar_firma": 8000.0,
        "skill_codes": [
            "SK_ASSEMBLY",
            "SK_VINYL_APPLICATOR",
            "SK_ELECTRICIAN",
            "SK_FIELD_INSTALLER",
            "SK_CNC_OPERATOR",
        ],
        "workcenter_codes": ["WC_ASSEMBLY", "WC_CNC_ROUTING", "WC_LED_ASSEMBLY", "WC_FIELD_INSTALLATION"],
        "resource_codes": ["MCH-CNC-4020", "WA-ASSEMBLY-02"],
    },
    {
        "name": "Chirila Cristian",
        "role": "Direct comercial / tehnic",
        "department": "Comercial",
        "employee_type": "administrative",
        "cost_lunar_firma": 7000.0,
        "skill_codes": ["SK_COMMERCIAL_TECH", "SK_QUOTING"],
        "workcenter_codes": [],
        "resource_codes": [],
    },
]


REAL_RESOURCES: List[Dict[str, Any]] = [
    {
        "machine_code": "MCH-CNC-4020",
        "name": "CNC 4020",
        "machine_type": "cnc_router",
        "resource_kind": "machine",
        "workcenter_code": "WC_CNC_ROUTING",
        "description": "Masă 4000 x 2000 mm, preluare automată scule, ARTCAM",
        "capacity_metadata": {
            "table_width_mm": 4000,
            "table_length_mm": 2000,
            "software": "ARTCAM",
            "auto_tool_change": True,
        },
    },
    {
        "machine_code": "MCH-EPSON-60800",
        "name": "Imprimanta Epson 60800",
        "machine_type": "printer_large_format",
        "resource_kind": "machine",
        "workcenter_code": "WC_PRINT",
        "description": "Lățime maximă print 1600 mm",
        "capacity_metadata": {"max_print_width_mm": 1600},
    },
    {
        "machine_code": "MCH-LAMINATOR-XPRO",
        "name": "Laminator X-Pro",
        "machine_type": "laminator",
        "resource_kind": "machine",
        "workcenter_code": "WC_LAMINATE",
        "description": "Lățime maximă laminare 1600 mm",
        "capacity_metadata": {"max_laminate_width_mm": 1600},
    },
    {
        "machine_code": "MCH-LASER-CNC",
        "name": "Laser CNC",
        "machine_type": "laser_cutter",
        "resource_kind": "machine",
        "workcenter_code": "WC_LASER_CUTTING",
        "description": "1300 x 900 mm, RDWORKS",
        "capacity_metadata": {"table_width_mm": 1300, "table_length_mm": 900, "software": "RDWORKS"},
    },
    {
        "machine_code": "MCH-CNC-CANT-LITERE",
        "name": "CNC Cant Litere",
        "machine_type": "letter_forming",
        "resource_kind": "machine",
        "workcenter_code": "WC_LETTER_FORMING",
        "description": "Formează cant până la 100 mm lățime",
        "capacity_metadata": {"max_cant_width_mm": 100},
    },
    {
        "machine_code": "MCH-WELD-STEEL",
        "name": "Aparat sudură oțel",
        "machine_type": "welder_steel",
        "resource_kind": "tool",
        "workcenter_code": "WC_METAL_FAB",
        "description": "Sudură oțel",
    },
    {
        "machine_code": "MCH-WELD-ALU",
        "name": "Aparat sudură aluminiu",
        "machine_type": "welder_aluminum",
        "resource_kind": "tool",
        "workcenter_code": "WC_METAL_FAB",
        "description": "Sudură aluminiu",
    },
    {
        "machine_code": "MCH-METAL-CUTTER-AUTO",
        "name": "Debitator metale cu masă automatizată",
        "machine_type": "metal_cutter",
        "resource_kind": "machine",
        "workcenter_code": "WC_METAL_FAB",
        "description": "Dimensiune masă de completat în admin",
        "capacity_metadata": {"table_dimensions_confirmed": False},
    },
    {
        "machine_code": "WA-WELD-TABLE",
        "name": "Masă pentru sudură",
        "machine_type": "work_area",
        "resource_kind": "work_area",
        "workcenter_code": "WC_METAL_FAB",
    },
    {
        "machine_code": "WA-ASSEMBLY-01",
        "name": "Masă lucru ansamblare 1",
        "machine_type": "work_area",
        "resource_kind": "work_area",
        "workcenter_code": "WC_ASSEMBLY",
    },
    {
        "machine_code": "WA-ASSEMBLY-02",
        "name": "Masă lucru ansamblare 2",
        "machine_type": "work_area",
        "resource_kind": "work_area",
        "workcenter_code": "WC_ASSEMBLY",
    },
    {
        "machine_code": "MCH-STYRO-CUTTER",
        "name": "Utilaj debitare polistiren",
        "machine_type": "styro_cutter",
        "resource_kind": "machine",
        "workcenter_code": "WC_CNC_ROUTING",
    },
    {
        "machine_code": "MCH-RIGID-FILM-LAMINATOR",
        "name": "Laminator pentru aplicare folie pe plăci rigide",
        "machine_type": "rigid_film_laminator",
        "resource_kind": "machine",
        "workcenter_code": "WC_VINYL_APPLICATION",
    },
    {
        "machine_code": "MCH-CUTTER-PLOTTER",
        "name": "Cutter Plotter",
        "machine_type": "cutter_plotter",
        "resource_kind": "machine",
        "workcenter_code": "WC_CUT",
        "description": "Decupare contur / vinyl",
    },
]


# Authorized employee groups (resolved to IDs at seed time).
_E_PRINT = ["Calin Cimpean", "Octavian Dumitru"]
_E_GRAPHIC = ["Calin Cimpean", "Octavian Dumitru", "Chirila Cristian"]
_E_CNC = ["Florin CNC", "Andrei Goghi"]
_E_ASSEMBLY = ["Putaru Sandu", "Vali Colantator", "Costi Modelator", "Andrei Goghi"]
_E_WELD = ["Putaru Sandu"]
_E_FIELD = _E_ASSEMBLY
_E_CANT = ["Florin CNC", "Costi Modelator"]

OPERATION_MAPPINGS: List[Dict[str, Any]] = [
    {
        "operation_code": "prepress",
        "authorization_mode": "hybrid",
        "required_skill_codes": ["SK_GRAPHIC_DESIGN", "SK_QUOTING"],
        "allowed_workcenter_codes": ["WC_PREPRESS"],
        "allowed_resource_codes": [],
        "product_system_aliases": [
            "vector_prep",
            "prepress",
            "file_preparation",
            "graphic_prepress",
            "volumetric_vector_prep",
            "volumetric_file_prep",
        ],
        "authorized_employee_names": _E_GRAPHIC,
    },
    {
        "operation_code": "print",
        "authorization_mode": "hybrid",
        "required_skill_codes": ["SK_PRINT_OPERATOR"],
        "allowed_workcenter_codes": ["WC_PRINT"],
        "allowed_resource_codes": ["MCH-EPSON-60800"],
        "default_resource_code": "MCH-EPSON-60800",
        "product_system_aliases": [
            "print",
            "face_print",
            "volumetric_face_print",
            "print_large_format",
        ],
        "authorized_employee_names": _E_PRINT,
    },
    {
        "operation_code": "print_roll",
        "authorization_mode": "hybrid",
        "required_skill_codes": ["SK_PRINT_OPERATOR"],
        "allowed_workcenter_codes": ["WC_PRINT"],
        "allowed_resource_codes": ["MCH-EPSON-60800"],
        "default_resource_code": "MCH-EPSON-60800",
        "product_system_aliases": ["print_roll"],
        "authorized_employee_names": _E_PRINT,
    },
    {
        "operation_code": "laminare",
        "authorization_mode": "hybrid",
        "required_skill_codes": ["SK_LAMINATOR_OPERATOR"],
        "allowed_workcenter_codes": ["WC_LAMINATE"],
        "allowed_resource_codes": ["MCH-LAMINATOR-XPRO"],
        "default_resource_code": "MCH-LAMINATOR-XPRO",
        "product_system_aliases": [
            "laminare",
            "lamination",
            "laminating",
            "print_lamination",
            "face_lamination",
        ],
        "authorized_employee_names": _E_PRINT,
    },
    {
        "operation_code": "cutter_plotter",
        "authorization_mode": "hybrid",
        "required_skill_codes": ["SK_CUTTER_OPERATOR"],
        "allowed_workcenter_codes": ["WC_CUT"],
        "allowed_resource_codes": ["MCH-CUTTER-PLOTTER"],
        "default_resource_code": "MCH-CUTTER-PLOTTER",
        "product_system_aliases": [
            "cutter_plotter",
            "oracal_cutting",
            "face_vinyl_cut",
        ],
        "authorized_employee_names": _E_PRINT,
    },
    {
        "operation_code": "cnc_cutting",
        "authorization_mode": "hybrid",
        "required_skill_codes": ["SK_CNC_OPERATOR"],
        "allowed_workcenter_codes": ["WC_CNC_ROUTING"],
        "allowed_resource_codes": ["MCH-CNC-4020"],
        "default_resource_code": "MCH-CNC-4020",
        "product_system_aliases": [
            "face_cnc_cut",
            "back_cut",
            "mounting_template_cnc_cut",
            "cnc_routing",
            "plexiglas_face_cut",
            "volumetric_face_cut",
            "forex_back_cut",
            "volumetric_back_cut",
            "plexi_cutting",
        ],
        "authorized_employee_names": _E_CNC,
    },
    {
        "operation_code": "cant_modelare",
        "authorization_mode": "hybrid",
        "required_skill_codes": ["SK_LETTER_CANT_OPERATOR", "SK_LETTER_MODELING"],
        "allowed_workcenter_codes": ["WC_LETTER_FORMING"],
        "allowed_resource_codes": ["MCH-CNC-CANT-LITERE"],
        "default_resource_code": "MCH-CNC-CANT-LITERE",
        "product_system_aliases": [
            "side_forming",
            "edge_bending",
            "letter_return_forming",
            "volumetric_side_forming",
            "cant_litere",
        ],
        "authorized_employee_names": _E_CANT,
    },
    {
        "operation_code": "colantare",
        "authorization_mode": "hybrid",
        "required_skill_codes": ["SK_VINYL_APPLICATOR"],
        "allowed_workcenter_codes": ["WC_VINYL_APPLICATION"],
        "allowed_resource_codes": ["MCH-RIGID-FILM-LAMINATOR", "WA-ASSEMBLY-01", "WA-ASSEMBLY-02"],
        "product_system_aliases": [
            "vinyl_application",
            "face_vinyl_application",
            "oracal_application",
            "letter_face_vinyl",
            "rigid_film_application",
            "vinyl_cutting",
        ],
        "authorized_employee_names": _E_ASSEMBLY,
        "notes": "Montaj autocolant atelier — NU montaj teren la beneficiar",
    },
    {
        "operation_code": "assembly",
        "authorization_mode": "hybrid",
        "required_skill_codes": ["SK_ASSEMBLY"],
        "allowed_workcenter_codes": ["WC_ASSEMBLY"],
        "allowed_resource_codes": ["WA-ASSEMBLY-01", "WA-ASSEMBLY-02"],
        "product_system_aliases": [
            "assembly_letters",
            "painting",
            "volumetric_letter_assembly",
            "final_assembly",
            "letter_assembly",
            "return_bonding",
            "side_bonding",
            "letter_bonding",
        ],
        "authorized_employee_names": _E_ASSEMBLY,
    },
    {
        "operation_code": "welding",
        "authorization_mode": "hybrid",
        "required_skill_codes": ["SK_LOCKSMITH"],
        "allowed_workcenter_codes": ["WC_METAL_FAB"],
        "allowed_resource_codes": ["MCH-WELD-STEEL", "MCH-WELD-ALU", "WA-WELD-TABLE"],
        "product_system_aliases": [
            "return_face_bonding",
            "return_profile_face_bonding",
            "welding",
            "steel_welding",
            "aluminum_welding",
            "support_structure_welding",
            "metal_frame_welding",
        ],
        "authorized_employee_names": _E_WELD,
    },
    {
        # DEC-014: single canonical WC — PROD-INT-02 matrix:
        # Montare LED / cablare → SK_ELECTRICIAN → WC_LED_ASSEMBLY → montaj_led.
        # WC_ASSEMBLY remains the assembly operation WC (SK_ASSEMBLY), not LED.
        # WA-ASSEMBLY-* stay as allowed physical work-area resources only.
        "operation_code": "montaj_led",
        "authorization_mode": "hybrid",
        "required_skill_codes": ["SK_ELECTRICIAN"],
        "allowed_workcenter_codes": ["WC_LED_ASSEMBLY"],
        "allowed_resource_codes": ["WA-ASSEMBLY-01", "WA-ASSEMBLY-02"],
        "product_system_aliases": [
            "led_install_letters",
            "electrical_letters",
            "led_assembly",
            "led_wiring",
            "electrical_wiring",
            "psu_wiring",
            "volumetric_led_install",
            "power_testing",
        ],
        "authorized_employee_names": _E_ASSEMBLY,
    },
    {
        "operation_code": "quality_control",
        "authorization_mode": "hybrid",
        "required_skill_codes": ["SK_ASSEMBLY"],
        "allowed_workcenter_codes": ["WC_ASSEMBLY"],
        "allowed_resource_codes": ["WA-ASSEMBLY-01", "WA-ASSEMBLY-02"],
        "product_system_aliases": ["qc_letters", "quality_control", "measurement"],
        "authorized_employee_names": _E_ASSEMBLY,
    },
    {
        "operation_code": "packaging",
        "authorization_mode": "hybrid",
        "required_skill_codes": ["SK_ASSEMBLY"],
        "allowed_workcenter_codes": ["WC_ASSEMBLY"],
        "allowed_resource_codes": ["WA-ASSEMBLY-01", "WA-ASSEMBLY-02"],
        "product_system_aliases": ["packaging_letters", "packaging"],
        "authorized_employee_names": _E_ASSEMBLY,
    },
    {
        "operation_code": "field_installation",
        "authorization_mode": "hybrid",
        "required_skill_codes": ["SK_FIELD_INSTALLER"],
        "allowed_workcenter_codes": ["WC_FIELD_INSTALLATION"],
        "allowed_resource_codes": [],
        "product_system_aliases": [
            "mounting",
            "field_mounting",
            "onsite_installation",
            "installation_team",
            "installation_onsite",
            "installation_prep",
            "field_installation",
        ],
        "authorized_employee_names": _E_FIELD,
        "notes": "Montaj teren la beneficiar — echipă multi-angajat via field_installation_teams",
    },
]


async def seed_operational_workforce_registry() -> Dict[str, Any]:
    from core.database import db_manager

    stats: Dict[str, Any] = {
        "employees_created": 0,
        "employees_updated": 0,
        "resources_upserted": 0,
        "operation_mappings_upserted": 0,
        "authorizations_synced": 0,
    }

    async with db_manager.async_session_maker() as db:
        emp_svc = EmployeesService(db)
        reg_svc = OperationalRegistryService(db)
        name_to_id: Dict[str, int] = {}

        for spec in REAL_EMPLOYEES:
            existing = (
                await db.execute(select(Employees).where(Employees.name == spec["name"]))
            ).scalar_one_or_none()

            payload = {
                "name": spec["name"],
                "role": spec["role"],
                "department": spec["department"],
                "status": "active",
                "employee_type": spec["employee_type"],
                "cost_lunar_firma": spec["cost_lunar_firma"],
                "salary_currency": "RON",
                "salary_period": "monthly",
                "skills": json.dumps(spec["skill_codes"], ensure_ascii=False),
                "machines": json.dumps(spec["resource_codes"], ensure_ascii=False),
            }

            if existing is None:
                row = await emp_svc.create(payload)
                stats["employees_created"] += 1
            else:
                row = await emp_svc.update(existing.id, payload)
                stats["employees_updated"] += 1

            await reg_svc.set_employee_authorizations(
                row.id,
                skill_codes=spec["skill_codes"],
                workcenter_codes=spec["workcenter_codes"],
                resource_codes=spec["resource_codes"],
            )
            stats["authorizations_synced"] += 1
            name_to_id[spec["name"]] = row.id

        for res in REAL_RESOURCES:
            await reg_svc.upsert_resource(res)
            stats["resources_upserted"] += 1

        def _auth_ids(names: List[str]) -> List[int]:
            return [name_to_id[n] for n in names if n in name_to_id]

        for mapping in OPERATION_MAPPINGS:
            payload = dict(mapping)
            auth_names = payload.pop("authorized_employee_names", None)
            if auth_names is not None:
                payload["authorized_employee_ids"] = _auth_ids(auth_names)
            await reg_svc.upsert_operation_mapping(payload)
            stats["operation_mappings_upserted"] += 1

    logger.info("seed_operational_workforce_registry: %s", stats)
    return stats
