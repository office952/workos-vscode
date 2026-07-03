"""
OrderSnapshotService — builds an immutable OrderSnapshot from a priced quote.

Canonical rules:
  - Accepts ONLY a priced QuoteCalculationSnapshot.
  - Does NOT recalculate ProductDefinition or CostResult.
  - Returns OrderSnapshot with is_locked=True and a frozen created_at.
  - Any subsequent change must be a separate revision (handled elsewhere),
    never a mutation of the produced OrderSnapshot.
"""

from __future__ import annotations

import copy
import uuid
from typing import Any, Dict, List, Optional

from data_models.product_contracts import (
    OrderFinalPrice,
    OrderSnapshot,
    QuoteCalculationSnapshot,
    iso_now,
)
from services.order_execution_snapshot_mapper import (
    normalize_product_definition_for_execution,
)


class OrderSnapshotLockedError(RuntimeError):
    """Raised when caller attempts to mutate an already-created OrderSnapshot."""


class OrderSnapshotService:
    def create_from_quote(
        self,
        quote_snapshot: QuoteCalculationSnapshot,
        order_id: Optional[str] = None,
        *,
        component_breakdown: Optional[List[Dict[str, Any]]] = None,
    ) -> OrderSnapshot:
        if quote_snapshot is None:
            raise ValueError("quote_snapshot is required")
        if quote_snapshot.status != "priced":
            raise ValueError(
                f"Order can be created only from a priced quote. Got status={quote_snapshot.status!r}"
            )

        # Deep-copy to ensure immutability from upstream mutation.
        pd = normalize_product_definition_for_execution(
            quote_snapshot.product_definition,
            component_breakdown=component_breakdown,
        )
        cr = copy.deepcopy(quote_snapshot.cost_result)
        qs = copy.deepcopy(quote_snapshot)

        final_price = OrderFinalPrice(
            net=float(quote_snapshot.price.net),
            gross=float(quote_snapshot.price.gross),
        )

        return OrderSnapshot(
            order_id=order_id or f"ORD-{uuid.uuid4().hex[:8].upper()}",
            product_definition=pd,
            cost_result=cr,
            quote_snapshot=qs,
            final_price=final_price,
            created_at=iso_now(),
            is_locked=True,
        )