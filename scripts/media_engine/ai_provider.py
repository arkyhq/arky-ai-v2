"""
Deterministic AI image provider adapter skeletons for the ARKY Media Engine.

This module defines common-contract adapters for free AI image providers. It
performs no networking, API calls, API key handling, logging, routing,
validation, asset-library work, or stock-provider coordination.
"""

from __future__ import annotations

from types import MappingProxyType
from typing import Any


CAPABILITY_FIELDS = (
    "background",
    "character",
    "object",
    "poster",
    "illustration",
    "meme",
    "ui",
    "overlay",
)

AI_CAPABILITIES = MappingProxyType(
    {
        "background": True,
        "character": True,
        "object": True,
        "poster": True,
        "illustration": True,
        "meme": True,
        "ui": True,
        "overlay": True,
    }
)


class BaseAIProvider:
    """
    Base deterministic adapter for free AI image providers.

    Subclasses supply provider identity and priority. Real provider integration
    can be added later outside this deterministic skeleton.
    """

    _provider_id = "base_ai"
    _priority = 0
    _capabilities: MappingProxyType[str, bool] = AI_CAPABILITIES

    def provider_id(self) -> str:
        """Return provider identifier."""
        return self._provider_id

    def provider_type(self) -> str:
        """Return normalized provider type."""
        return "ai"

    def priority(self) -> int:
        """Return provider priority."""
        return self._priority

    def supports(self, asset_type: str) -> bool:
        """Return whether this provider supports an asset type."""
        return bool(self._capabilities.get(_safe_text(asset_type), False))

    def capabilities(self) -> dict[str, bool]:
        """Return normalized provider capabilities."""
        return {
            field: bool(self._capabilities.get(field, False))
            for field in CAPABILITY_FIELDS
        }

    def acquire(self, request: dict[str, Any]) -> dict[str, Any]:
        """
        Return a normalized deterministic AI acquisition response skeleton.

        Arguments:
            request: normalized Media Acquisition Request.

        Returns:
            Normalized AI provider response.
        """
        asset_type = _safe_text(request.get("asset_type"))
        errors: list[str] = []
        warnings: list[str] = []

        if not self.supports(asset_type):
            errors.append(f"unsupported asset_type: {asset_type}")
            return self._normalized_result(False, request, errors, warnings)

        prompt = _safe_text(request.get("generation_prompt"))
        if not prompt:
            errors.append("generation_prompt must be populated")
            return self._normalized_result(False, request, errors, warnings)

        return self._normalized_result(True, request, errors, warnings)

    def _normalized_result(
        self,
        success: bool,
        request: dict[str, Any],
        errors: list[str],
        warnings: list[str],
    ) -> dict[str, Any]:
        """Build a normalized AI provider result."""
        asset_type = _safe_text(request.get("asset_type"))
        asset_id = _safe_text(request.get("asset_id")) or _mock_asset_id(
            self.provider_id(),
            asset_type,
        )
        width, height = _resolution(request.get("preferred_resolution"))

        return {
            "success": success,
            "provider": self.provider_id(),
            "provider_type": self.provider_type(),
            "asset": {
                "asset_id": asset_id,
                "asset_type": asset_type,
                "prompt": _safe_text(request.get("generation_prompt")),
                "negative_prompt": "",
                "seed": None,
                "image_url": None,
                "width": width,
                "height": height,
            },
            "errors": tuple(errors),
            "warnings": tuple(warnings),
        }


class PollinationsProvider(BaseAIProvider):
    """Deterministic adapter skeleton for Pollinations AI."""

    _provider_id = "pollinations_ai"
    _priority = 7
    _capabilities = AI_CAPABILITIES


class FluxProvider(BaseAIProvider):
    """Deterministic adapter skeleton for FLUX."""

    _provider_id = "flux"
    _priority = 8
    _capabilities = AI_CAPABILITIES


def get_ai_providers() -> tuple[BaseAIProvider, ...]:
    """Return free AI provider adapters in deterministic priority order."""
    providers: tuple[BaseAIProvider, ...] = (
        PollinationsProvider(),
        FluxProvider(),
    )
    return tuple(sorted(providers, key=lambda provider: provider.priority()))


def _safe_text(value: Any) -> str:
    """Return stripped text for scalar values."""
    if value is None:
        return ""
    return str(value).strip()


def _resolution(value: Any) -> tuple[int, int]:
    """Return a normalized width-height pair."""
    if isinstance(value, dict):
        width = value.get("width")
        height = value.get("height")
        return _int_pair(width, height)

    if isinstance(value, (tuple, list)) and len(value) >= 2:
        return _int_pair(value[0], value[1])

    return (0, 0)


def _int_pair(first: Any, second: Any) -> tuple[int, int]:
    """Return a positive integer pair or empty dimensions."""
    try:
        width = int(first)
        height = int(second)
    except (TypeError, ValueError):
        return (0, 0)

    if width <= 0 or height <= 0:
        return (0, 0)
    return (width, height)


def _mock_asset_id(provider_id: str, asset_type: str) -> str:
    """Build deterministic mock asset identifier."""
    provider = provider_id.replace("_", "-")
    clean_type = asset_type.replace("_", "-") or "asset"
    return f"{provider}-{clean_type}-mock"


def _self_test() -> bool:
    """Verify AI provider adapter skeleton behavior."""
    request = {
        "asset_id": "asset_001",
        "asset_type": "illustration",
        "generation_prompt": "bright futuristic media control room",
        "preferred_resolution": (1080, 1920),
    }
    providers = get_ai_providers()
    first = providers[0]
    acquire_result = first.acquire(request)

    checks = (
        tuple(provider.provider_id() for provider in providers)
        == ("pollinations_ai", "flux"),
        all(isinstance(provider.capabilities(), dict) for provider in providers),
        first.supports("illustration") is True,
        first.supports("logo") is False,
        acquire_result["success"] is True,
        acquire_result["provider_type"] == "ai",
        isinstance(acquire_result["asset"], dict),
        len(providers) == 2,
    )
    return all(checks)


if __name__ == "__main__":
    print("PASS" if _self_test() else "FAIL")
