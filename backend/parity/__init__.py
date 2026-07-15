"""Runtime parity instrumentation foundation (APP-AUTH-04).

Isolated contracts, pure comparators, and feature flags for future OBSERVE_ONLY
instrumentation. Operational services must not import this package until APP-AUTH-05+.
"""

from parity.contracts import (
    PARITY_EVENT_CONTRACT_VERSION,
    PARITY_RESULT_CONTRACT_VERSION,
    ParityEventV1,
    ParityResultContract,
    ReconciliationSheetContract,
)
from parity.enums import (
    AuthorizationConfirmationStatus,
    CapabilityClassification,
    ComparisonResult,
    DiscrepancyStatus,
    ExplicitMappingClassification,
    ParityDomain,
    ParityEventType,
    ParityMetricName,
    ParitySeverity,
)

__all__ = [
    "PARITY_EVENT_CONTRACT_VERSION",
    "PARITY_RESULT_CONTRACT_VERSION",
    "AuthorizationConfirmationStatus",
    "CapabilityClassification",
    "ComparisonResult",
    "DiscrepancyStatus",
    "ExplicitMappingClassification",
    "ParityDomain",
    "ParityEventType",
    "ParityEventV1",
    "ParityMetricName",
    "ParityResultContract",
    "ParitySeverity",
    "ReconciliationSheetContract",
]
