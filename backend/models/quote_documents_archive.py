"""
BUILD 15 — Quote Documents Archive Model.

Stores metadata for generated PDF documents with full traceability
back to the source quote (id, code, version).

Storage: filesystem (MVP) with file_path reference.
Future: migrate to cloud storage by changing file_path resolution only.
"""

from datetime import datetime

from sqlalchemy import Column, DateTime, Integer, String
from core.database import Base


class QuoteDocumentsArchive(Base):
    """Archive record for a generated quote PDF document."""

    __tablename__ = "quote_documents_archive"

    id = Column(Integer, primary_key=True, autoincrement=True)
    quote_id = Column(Integer, nullable=False, index=True)
    quote_code = Column(String, nullable=False)
    quote_version = Column(Integer, nullable=False)
    document_type = Column(String, nullable=False, default="quote_pdf")
    filename = Column(String, nullable=False)
    file_path = Column(String, nullable=False)
    file_size_bytes = Column(Integer, nullable=True)
    content_hash = Column(String, nullable=True)
    generated_by = Column(String, nullable=True)
    source_snapshot_id = Column(Integer, nullable=True)
    notes = Column(String, nullable=True)
    created_at = Column(DateTime(timezone=True), default=datetime.utcnow)