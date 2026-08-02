# Source ownership map

| Fact | Owner |
|------|-------|
| Labor time | ExecutionActuals / sessions |
| Labor money | HR RoleSkillLaborCostPolicy → ActualLaborCostLine |
| Material consumption/scrap/return | Inventory StockMovement |
| Material valuation | Frozen on movement |
| Machine applicability | ExecutionPlan task declaration |
| Machine actual cost | Not captured (unavailable) |
| Other direct | Not declared (not_applicable) |
| Closure | ActualCostPolicyRuntimeService |
| Profitability | Read-only consumer |
