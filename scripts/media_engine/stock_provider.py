"""
Deterministic stock provider adapter skeletons for the ARKY Media Engine.

This module defines common-contract adapters for free stock media providers.
It performs no HTTP requests, downloads, API key handling, logging, routing,
validation, asset-library work, or AI generation.
"""

from __future__ import annotations

from types import MappingProxyType
from typing import Any


CAPABILITY_FIELDS = (
    "background",
    "character",
    "object",
    "icon",
    "logo",
    "poster",
    "illustration",
    "meme",
    "ui",
    "overlay",
)

STOCK_CAPABILITIES = MappingProxyType(
    {
        "background": True,
        "character": True,
        "object": True,
        "icon": False,
        "logo": False,
        "poster": False,
        "illustration": True,
        "meme": False,
        "ui": False,
        "overlay": True,
    }
)

OPEN_REPOSITORY_CAPABILITIES = MappingProxyType(
    {
        "background": True,
        "character": True,
        "object": True,
        "icon": True,
        "logo": True,
        "poster": True,
        "illustration": True,
        "meme": True,
        "ui": True,
        "overlay": True,
    }
)


class BaseStockProvider:
    """
    Base deterministic adapter for stock provider integrations.

    Subclasses supply only provider identity, priority, license label, and
    capabilities. Real API integration can be added later outside this
    skeleton contract.
    """

    _provider_id = "base_stock"
    _priority = 0
    _license = "unknown"
    _capabilities: MappingProxyType[str, bool] = STOCK_CAPABILITIES

    def provider_id(self) -> str:
        """Return provider identifier."""
        return self._provider_id

    def provider_type(self) -> str:
        """Return normalized provider type."""
        return "stock"

    def priority(self) -> int:
        """Return provider priority."""
        return self._priority

    def supports(self, asset_type: str) -> bool:
        """Return whether this provider supports an asset type."""
        return bool(self._capabilities.get(_safe_text(asset_type), False))

    def search(self, request: dict[str, Any]) -> dict[str, Any]:
        """
        Return a normalized deterministic search response skeleton.

        Arguments:
            request: normalized Media Acquisition Request.

        Returns:
            Normalized search result dictionary.
        """
        asset_type = _safe_text(request.get("asset_type"))
        errors: list[str] = []
        warnings: list[str] = []

        if not self.supports(asset_type):
            errors.append(f"unsupported asset_type: {asset_type}")
            return self._normalized_result(False, request, errors, warnings)

        return self._normalized_result(True, request, errors, warnings)

    def acquire(self, search_result: dict[str, Any]) -> dict[str, Any]:
        """
        Return a normalized deterministic acquisition response skeleton.

        Arguments:
            search_result: normalized provider search result.

        Returns:
            Normalized acquisition result dictionary.
        """
        result = _safe_mapping(search_result)
        if result.get("success") is not True:
            return self._normalized_result(
                False,
                _safe_mapping(result.get("asset")),
                ["search result was not successful"],
                [],
            )

        return {
            "success": True,
            "provider": self.provider_id(),
            "provider_type": self.provider_type(),
            "asset": _safe_mapping(result.get("asset")),
            "errors": (),
            "warnings": tuple(_safe_sequence(result.get("warnings"))),
        }

    def capabilities(self) -> dict[str, bool]:
        """Return normalized provider capabilities."""
        return {field: bool(self._capabilities.get(field, False)) for field in CAPABILITY_FIELDS}

    def _normalized_result(
        self,
        success: bool,
        request: dict[str, Any],
        errors: list[str],
        warnings: list[str],
    ) -> dict[str, Any]:
        """Build a normalized stock provider result."""
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
                "license": self._license,
                "download_url": "",
                "preview_url": "",
                "width": width,
                "height": height,
            },
            "errors": tuple(errors),
            "warnings": tuple(warnings),
        }


class PexelsProvider(BaseStockProvider):
    """Deterministic adapter skeleton for Pexels."""

    _provider_id = "pexels"
    _priority = 2
    _license = "Pexels License"
    _capabilities = STOCK_CAPABILITIES


class PixabayProvider(BaseStockProvider):
    """Deterministic adapter skeleton for Pixabay."""

    _provider_id = "pixabay"
    _priority = 3
    _license = "Pixabay Content License"
    _capabilities = STOCK_CAPABILITIES


class UnsplashProvider(BaseStockProvider):
    """Deterministic adapter skeleton for Unsplash."""

    _provider_id = "unsplash"
    _priority = 4
    _license = "Unsplash License"
    _capabilities = STOCK_CAPABILITIES


class WikimediaProvider(BaseStockProvider):
    """Deterministic adapter skeleton for Wikimedia Commons."""

    _provider_id = "wikimedia_commons"
    _priority = 5
    _license = "Wikimedia Commons License"
    _capabilities = OPEN_REPOSITORY_CAPABILITIES


class OpenverseProvider(BaseStockProvider):
    """Deterministic adapter skeleton for Openverse."""

    _provider_id = "openverse"
    _priority = 6
    _license = "Openverse Source License"
    _capabilities = OPEN_REPOSITORY_CAPABILITIES


def get_stock_providers() -> tuple[BaseStockProvider, ...]:
    """Return free stock provider adapters in deterministic priority order."""
    providers: tuple[BaseStockProvider, ...] = (
        PexelsProvider(),
        PixabayProvider(),
        UnsplashProvider(),
        WikimediaProvider(),
        OpenverseProvider(),
    )
    return tuple(sorted(providers, key=lambda provider: provider.priority()))


def _safe_mapping(value: Any) -> dict[str, Any]:
    """Return a shallow dictionary copy when possible."""
    if isinstance(value, dict):
        return dict(value)
    return {}


def _safe_sequence(value: Any) -> tuple[str, ...]:
    """Return a tuple of non-empty text values."""
    if not isinstance(value, (tuple, list)):
        return ()
    return tuple(filter(None, (_safe_text(item) for item in value)))


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
    """Verify stock provider adapter skeleton behavior."""
    request = {
        "asset_id": "asset_001",
        "asset_type": "background",
        "preferred_resolution": (1080, 1920),
    }
    providers = get_stock_providers()
    first = providers[0]
    search_result = first.search(request)

    checks = (
        tuple(provider.provider_id() for provider in providers)
        == (
            "pexels",
            "pixabay",
            "unsplash",
            "wikimedia_commons",
            "openverse",
        ),
        all(isinstance(provider.capabilities(), dict) for provider in providers),
        first.supports("background") is True,
        first.supports("ui") is False,
        search_result["success"] is True,
        search_result["provider_type"] == "stock",
        isinstance(search_result["asset"], dict),
        len(providers) == 5,
    )
    return all(checks)


if __name__ == "__main__":
    print("PASS" if _self_test() else "FAIL")
