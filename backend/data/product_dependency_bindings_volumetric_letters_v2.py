"""Product Template capability bindings for TPL-VOLUMETRIC-LETTERS_v2."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Literal

from data.component_dependency_contract_v1 import LED_MOUNT_SURFACE

ProviderKind = Literal["sold_module", "sold_bundle"]


@dataclass(frozen=True)
class CapabilityProvider:
    kind: ProviderKind
    modules: tuple[str, ...]

    def satisfied_by(self, sold: set[str]) -> bool:
        if self.kind == "sold_module":
            return bool(self.modules) and self.modules[0] in sold
        if self.kind == "sold_bundle":
            return set(self.modules).issubset(sold)
        return False


@dataclass(frozen=True)
class ProductDependencyBinding:
    template_code: str
    capability_providers: dict[str, tuple[CapabilityProvider, ...]]


TPL_VOLUMETRIC_LETTERS_V2_BINDING = ProductDependencyBinding(
    template_code="TPL-VOLUMETRIC-LETTERS_v2",
    capability_providers={
        LED_MOUNT_SURFACE: (
            CapabilityProvider(kind="sold_module", modules=("BACK",)),
            CapabilityProvider(kind="sold_bundle", modules=("FACE", "RETURN-CANT")),
        ),
    },
)

PRODUCT_DEPENDENCY_BINDINGS: dict[str, ProductDependencyBinding] = {
    TPL_VOLUMETRIC_LETTERS_V2_BINDING.template_code: TPL_VOLUMETRIC_LETTERS_V2_BINDING,
}
