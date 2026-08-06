"""
Provider candidate collection for the ARKY Media Engine.

This module collects candidates across externally supplied provider
objects. It depends only on the provider contract:
provider_id(), supports(asset_type), priority(), and search(request).
"""

from __future__ import annotations

from typing import Any, Protocol


class MediaProvider(Protocol):
    """Contract expected from externally supplied media providers."""

    def provider_id(self) -> str:
        """Return the provider identifier."""

    def supports(self, asset_type: str) -> bool:
        """Return whether the provider supports the requested asset type."""

    def priority(self) -> int:
        """Return provider priority for deterministic routing order."""

    def provider_type(self) -> str:
        """Return provider category or integration type."""

    def search(self, request: dict[str, Any]) -> dict[str, Any]:
        """Search for assets matching the provided request."""


class ProviderRouter:
    """
    Collect Media Request candidates from registered stock providers.

    Providers are dependency-injected and are never instantiated here. The
    router uses only the public provider contract and returns candidates from
    all successful stock provider searches.
    """

    def __init__(self, providers: list[MediaProvider] | None = None) -> None:
        """Initialize the router with optional externally supplied providers."""
        self.providers: tuple[MediaProvider, ...] = ()
        self._providers: tuple[MediaProvider, ...] = self.providers
        if providers:
            self.register_providers(providers)

    def register_provider(self, provider: MediaProvider) -> None:
        """Register one externally supplied provider."""
        self.providers = _sorted_providers((*self.providers, provider))
        self._providers = self.providers

    def register_providers(self, providers: list[MediaProvider]) -> None:
        """Register multiple externally supplied providers."""
        self.providers = _sorted_providers((*self.providers, *providers))
        self._providers = self.providers

    def route(self, request: dict[str, Any]) -> dict[str, Any]:
        """
        Collect provider candidates for one request.

        Arguments:
            request: validated normalized Media Request.

        Returns:
            Structured success or failure result.
        """
        errors: list[str] = []
        warnings: list[str] = []
        candidates: list[dict[str, Any]] = []
        providers_checked: list[str] = []
        asset_type = _safe_text(request.get("asset_type"))

        for provider in self.providers:
            provider_id = _provider_id(provider)

            try:
                if not _is_stock_provider(provider):
                    warnings.append(f"{provider_id} skipped non-stock provider")
                    continue

                if not provider.supports(asset_type):
                    warnings.append(f"{provider_id} skipped unsupported asset type")
                    continue

                providers_checked.append(provider_id)
                result = provider.search(dict(request))
                if not isinstance(result, dict):
                    provider_errors = _provider_errors(provider_id, result)
                    errors.extend(provider_errors)
                    warnings.extend(provider_errors)
                    continue

                provider_errors = _provider_errors(provider_id, result)
                provider_warnings = _safe_sequence(result.get("warnings"))

                if _is_successful_result(result):
                    candidates.extend(_safe_results(result.get("results")))
                    warnings.extend(provider_warnings)
                    continue

                errors.extend(provider_errors)
                warnings.extend((*provider_warnings, *provider_errors))
                if _is_empty_success(result):
                    warnings.append(f"{provider_id} returned no results")
            except Exception as exc:
                provider_error = f"{provider_id} failed: {exc}"
                errors.append(provider_error)
                warnings.append(provider_error)

        if candidates:
            return _route_result(
                success=True,
                provider=_safe_text(candidates[0].get("provider")) or None,
                candidates=candidates,
                providers_checked=providers_checked,
                errors=errors,
                warnings=warnings,
            )

        return _route_result(
            success=False,
            provider=None,
            candidates=(),
            providers_checked=providers_checked,
            errors=tuple(errors) or ("no provider returned results",),
            warnings=warnings,
        )

    def available_providers(self) -> tuple[str, ...]:
        """Return registered provider ids in routing order."""
        return tuple(_provider_id(provider) for provider in self.providers)


def _sorted_providers(
    providers: tuple[MediaProvider, ...],
) -> tuple[MediaProvider, ...]:
    """Return providers sorted by provider priority."""
    return tuple(sorted(providers, key=_provider_priority))


def _provider_priority(provider: MediaProvider) -> int:
    """Return provider priority, preserving safe fallback behavior."""
    try:
        return int(provider.priority())
    except Exception:
        return 1_000_000


def _provider_id(provider: MediaProvider) -> str:
    """Return provider id, preserving safe fallback behavior."""
    try:
        provider_id = _safe_text(provider.provider_id())
    except Exception:
        provider_id = ""
    return provider_id or "unknown_provider"


def _is_stock_provider(provider: MediaProvider) -> bool:
    """Return whether a provider should be included in stock collection."""
    try:
        provider_type = _safe_text(provider.provider_type()).casefold()
    except Exception:
        return True
    return provider_type not in {"ai", "generation", "generative"}


def _is_successful_result(result: Any) -> bool:
    """Return whether a provider search result contains usable assets."""
    return (
        isinstance(result, dict)
        and result.get("success") is True
        and bool(_safe_results(result.get("results")))
    )


def _is_empty_success(result: Any) -> bool:
    """Return whether a provider succeeded without returning results."""
    return (
        isinstance(result, dict)
        and result.get("success") is True
        and not _safe_results(result.get("results"))
    )


def _provider_errors(provider_id: str, result: Any) -> tuple[str, ...]:
    """Return normalized provider errors from a search result."""
    if not isinstance(result, dict):
        return (f"{provider_id} returned invalid result",)

    if _is_empty_success(result):
        return ()

    errors = _safe_sequence(result.get("errors"))
    if errors:
        return tuple(f"{provider_id}: {error}" for error in errors)
    return (f"{provider_id} did not return results",)


def _route_result(
    success: bool,
    provider: str | None,
    candidates: Any,
    providers_checked: Any,
    errors: Any,
    warnings: Any,
) -> dict[str, Any]:
    """Build a normalized provider candidate collection response."""
    clean_candidates = _safe_results(candidates)
    return {
        "success": success,
        "provider": provider,
        "candidates": list(clean_candidates),
        "providers_checked": list(_safe_sequence(providers_checked)),
        "results": list(clean_candidates),
        "asset": dict(clean_candidates[0]) if clean_candidates else {},
        "errors": list(_safe_sequence(errors)),
        "warnings": list(_safe_sequence(warnings)),
    }


def _safe_results(value: Any) -> tuple[dict[str, Any], ...]:
    """Return normalized provider result dictionaries."""
    if not isinstance(value, (tuple, list)):
        return ()
    return tuple(_safe_mapping(item) for item in value if isinstance(item, dict))


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


def _self_test() -> bool:
    """Verify provider routing behavior with lightweight mock providers."""

    class MockProvider:
        """Small contract-compatible provider for router self-test."""

        def __init__(
            self,
            provider_name: str,
            supported_types: tuple[str, ...],
            provider_priority: int,
            should_succeed: bool,
        ) -> None:
            self._provider_name = provider_name
            self._supported_types = supported_types
            self._provider_priority = provider_priority
            self._should_succeed = should_succeed

        def provider_id(self) -> str:
            """Return mock provider id."""
            return self._provider_name

        def supports(self, asset_type: str) -> bool:
            """Return whether mock provider supports the asset type."""
            return asset_type in self._supported_types

        def priority(self) -> int:
            """Return mock priority."""
            return self._provider_priority

        def provider_type(self) -> str:
            """Return mock provider type."""
            return "stock"

        def search(self, request: dict[str, Any]) -> dict[str, Any]:
            """Return mock provider search result."""
            if self._should_succeed:
                return {
                    "success": True,
                    "provider": self._provider_name,
                    "results": [{"asset_id": request.get("asset_id", "")}],
                    "errors": [],
                    "warnings": [],
                }
            return {
                "success": False,
                "provider": self._provider_name,
                "results": [],
                "errors": ["mock failure"],
                "warnings": [],
            }

    request = {"asset_type": "background", "asset_id": "asset_001"}
    unsupported = MockProvider("unsupported", ("icon",), 1, True)
    failing = MockProvider("failing", ("background",), 2, False)
    successful = MockProvider("successful", ("background",), 3, True)
    router = ProviderRouter()
    router.register_provider(successful)
    router.register_providers([failing, unsupported])

    routed = router.route(request)
    failing_router = ProviderRouter([failing])
    failed = failing_router.route(request)

    checks = (
        router.available_providers() == ("unsupported", "failing", "successful"),
        routed["success"] is True,
        routed["provider"] == "successful",
        len(routed["candidates"]) == 1,
        routed["providers_checked"] == ["failing", "successful"],
        routed["results"][0]["asset_id"] == "asset_001",
        any("unsupported" in warning for warning in routed["warnings"]),
        failed["success"] is False,
        failed["provider"] is None,
        failing_router.available_providers() == ("failing",),
    )
    return all(checks)


if __name__ == "__main__":
    print("PASS" if _self_test() else "FAIL")
