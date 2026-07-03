from datetime import datetime

from core.database import Base
from sqlalchemy import Column, DateTime, Float, Integer, String, Text


class Vector_assets(Base):
    __tablename__ = "vector_assets"
    __table_args__ = {"extend_existing": True}

    id = Column(Integer, primary_key=True, index=True, autoincrement=True, nullable=False)
    asset_code = Column(String, nullable=False, unique=True, index=True)
    owner_type = Column(String, nullable=False, default="standalone")
    owner_id = Column(Integer, nullable=True)
    original_filename = Column(String, nullable=False)
    bucket_name = Column(String, nullable=False)
    object_key = Column(String, nullable=False, unique=True, index=True)
    source_format = Column(String, nullable=False, default="svg")
    content_type_reported = Column(String, nullable=True)
    file_size_bytes = Column(Integer, nullable=True)
    content_sha256 = Column(String, nullable=True)
    parse_status = Column(String, nullable=False, default="pending")
    parse_warnings_json = Column(Text, nullable=False, default="[]")
    parse_error_code = Column(String, nullable=True)
    parse_error_detail = Column(Text, nullable=True)
    bbox_w_mm = Column(Float, nullable=True)
    bbox_h_mm = Column(Float, nullable=True)
    area_mm2_approx = Column(Float, nullable=True)
    perimeter_mm_approx = Column(Float, nullable=True)
    metrics_version = Column(String, nullable=False, default="v1")
    created_by = Column(String, nullable=True)
    created_at = Column(DateTime(timezone=True), default=datetime.now)
    updated_at = Column(DateTime(timezone=True), default=datetime.now, onupdate=datetime.now)
