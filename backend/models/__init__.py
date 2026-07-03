# Models package.
# Import all model modules here so SQLAlchemy's Base.metadata sees them
# BEFORE `Base.metadata.create_all(...)` runs at startup. Missing imports =
# missing tables in the database.
from models import auth  # noqa: F401
from models import clients  # noqa: F401
from models import cost_engine_config  # noqa: F401
from models import company_commercial_settings  # noqa: F401
from models import employees  # noqa: F401
from models import employee_attendance_event  # noqa: F401
from models import attendance_request_effect  # noqa: F401
from models import employee_balance_transaction  # noqa: F401
from models import employee_payment_record  # noqa: F401
from models import employee_request  # noqa: F401
from models import task_clarification_request  # noqa: F401
from models import operational_registry  # noqa: F401
from models import execution_observation_config  # noqa: F401
from models import execution_plan  # noqa: F401
from models import execution_reality  # noqa: F401
from models import intake_requests  # noqa: F401
from models import inventory_materials  # noqa: F401
from models import inventory_material_price_history  # noqa: F401
from models import inventory_material_source_review_audit  # noqa: F401
from models import commercial_markup_policies  # noqa: F401
from models import integration_settings  # noqa: F401
from models import inventory_sheet_remediation_audit_events  # noqa: F401
from models import orders  # noqa: F401
from models import output_blocks  # noqa: F401
from models import product_families  # noqa: F401
from models import product_templates  # noqa: F401
from models import product_template_module_links  # noqa: F401
from models import quotes  # noqa: F401
from models import recurring_payments  # noqa: F401
from models import suppliers  # noqa: F401
from models import product_blueprint_dossier  # noqa: F401
from models import workcenter_rates  # noqa: F401
from models import quote_documents_archive  # noqa: F401
from models import vector_assets  # noqa: F401
from models import intake_v3_workspace  # noqa: F401
from models import intake_v4_workspace  # noqa: F401
from models import intake_v5_project  # noqa: F401
from models import quote_snapshot_v2  # noqa: F401