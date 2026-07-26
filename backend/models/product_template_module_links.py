from datetime import datetime

from core.database import Base
from sqlalchemy import Boolean, Column, DateTime, Integer, String


class ProductTemplateModuleLink(Base):
    __tablename__ = "product_template_module_links"
    __table_args__ = {"extend_existing": True}

    id = Column(Integer, primary_key=True, index=True, autoincrement=True, nullable=False)
    parent_template_id = Column(Integer, nullable=False, index=True)
    parent_template_code = Column(String, nullable=False, index=True)
    module_template_id = Column(Integer, nullable=False, index=True)
    module_template_code = Column(String, nullable=False, index=True)
    relation_type = Column(String, nullable=False, default="optional_addon")
    trigger_field = Column(String, nullable=False)
    trigger_value_json = Column(String, nullable=False)
    input_mapping_json = Column(String, nullable=False)
    default_values_json = Column(String, nullable=True)
    pricing_mode = Column(String, nullable=False, default="separate_quote_line")
    execution_mode = Column(String, nullable=False, default="linked_child_work")
    # Component contract representation on the composition edge (no CT table).
    usage_mode = Column(String, nullable=True)
    instance_schema_id = Column(String, nullable=True)
    active = Column(Boolean, nullable=False, default=True)
    notes = Column(String, nullable=True)
    created_at = Column(DateTime(timezone=True), default=datetime.now)
    updated_at = Column(DateTime(timezone=True), default=datetime.now, onupdate=datetime.now)