# Movement lifecycle

```text
ISSUE/CONSUME (consumption) → adds actual cost (frozen valuation)
RETURN (return, reverses_movement_id required) → subtracts eligible frozen amount + restores stock
SCRAP (scrap + reason) → distinct actual cost
ADJUSTMENT → not job actual
RESERVATION / PLANNED BOM → rejected, never written as actual
```

Idempotency: unique `idempotency_key` → replay returns existing movement id.
Unit conversion: not silent; unit mismatch rejected against material.unit.
