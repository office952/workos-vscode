"""
ExecutionObservationConfig — WorkOS Observability v1.

SINGLETON (id=1). Stores configurable thresholds used by the
ExecutionObservabilityService when classifying divergence between
ExecutionPlan and ExecutionReality. The thresholds are READ by the
service and NEVER modified by it — writes are exclusively through
the config CRUD (admin / CRUD router), not through observability.

Canonical invariants:
  - Thresholds are configurable at runtime. They MUST NOT be hardcoded
    in business logic.
  - This config has NO knowledge of cost, pricing, product or quote
    data. It is purely about observability classification.
  - `is_active = False` means observability should fall back to
    `UNCONFIRMED` (a neutral, non-evaluative status) rather than
    guessing with stale thresholds.

Fields:
  - warning_time_delta_pct:        % delta above which status is WARNING
                                   (e.g. 15 == 15 %). Applied on absolute
                                   relative delta vs plan.
  - critical_time_delta_pct:       % delta above which status is CRITICAL
                                   (e.g. 35 == 35 %).
  - warning_time_delta_minutes:    absolute minutes above which status
                                   is WARNING (used in addition to pct
                                   so small jobs still trip on big absolute
                                   overruns).
  - critical_time_delta_minutes:   absolute minutes above which status
                                   is CRITICAL.
  - is_active:                     when False, observability returns
                                   UNCONFIRMED for every order.
"""

from core.database import Base
from datetime import datetime
from sqlalchemy import Boolean, Column, DateTime, Float, Integer


class ExecutionObservationConfig(Base):
    __tablename__ = "execution_observation_config"
    __table_args__ = {"extend_existing": True}

    id = Column(Integer, primary_key=True, index=True, autoincrement=True, nullable=False)

    warning_time_delta_pct = Column(Float, nullable=False, default=15.0)
    critical_time_delta_pct = Column(Float, nullable=False, default=35.0)
    warning_time_delta_minutes = Column(Float, nullable=False, default=30.0)
    critical_time_delta_minutes = Column(Float, nullable=False, default=120.0)

    is_active = Column(Boolean, nullable=False, default=True)

    created_at = Column(DateTime(timezone=True), default=datetime.now)
    updated_at = Column(DateTime(timezone=True), default=datetime.now, onupdate=datetime.now)