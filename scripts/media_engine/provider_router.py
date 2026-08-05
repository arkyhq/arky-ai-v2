"""
Provider routing orchestration for the ARKY Media Engine.

This module routes validated Media Requests across externally supplied provider
objects. It depends only on the provider contract:
provider_id(), supports(asset_type), priority(), and acquire(request).
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

    def acquire(self, request: dict[str, Any]) -> dict[str, Any]:
        """Attempt to acquire an asset for the provided request."""


class ProviderRouter:
    """
    Route validated Media Requests to registered providers.

    Providers are dependency-injected and are never instantiated here. The
    router uses only the public provider contract and stops at the first
    successful acquisition result.
    """

    def __init__(self, providers: list[MediaProvider] | None = None) -> None:
        """Initialize the router with optional externally supplied providers."""
        self._providers: tuple[MediaProvider, ...] = ()
        if providers:
            self.register_providers(providers)

    def register_provider(self, provider: MediaProvider) -> None:
        """Register one externally supplied provider."""
        self._providers = _sorted_providers((*self._providers, provider))

    def register_providers(self, providers: list[MediaProvider]) -> None:
        """Register multiple externally supplied providers."""
        self._providers = _sorted_providers((*self._providers, *providers))

    def route(self, request: dict[str, Any]) -> dict[str, Any]:
        """
        Route one validated request to the first successful provider.

        Arguments:
            request: validated normalized Media Request.

        Returns:
            Structured success or failure result.
        """
        errors: list[str] = []
        warnings: list[str] = []
        asset_type = _safe_text(request.get("asset_type"))

        for provider in self._providers:
            provider_id = _provider_id(provider)

            try:
                if not provider.supports(asset_type):
                    warnings.append(f"{provider_id} skipped unsupported asset type")
                    continue

                result = provider.acquire(dict(request))
                if _is_successful_result(result):
                    return {
                        "success": True,
                        "provider": provider_id,
                        "asset": _safe_mapping(result.get("asset")),
                        "errors": tuple(errors),
                        "warnings": tuple(
                            [*warnings, *_safe_sequence(result.get("warnings"))]
                        ),
                    }

                errors.extend(_provider_errors(provider_id, result))
                warnings.extend(_safe_sequence(result.get("warnings")))
            except Exception as exc:
                errors.append(f"{provider_id} failed: {exc}")

        return {
            "success": False,
            "provider": "",
            "asset": {},
            "errors": tuple(errors) or ("no provider acquired asset",),
            "warnings": tuple(warnings),
        }

    def available_providers(self) -> tuple[str, ...]:
        """Return registered provider ids in routing order."""
        return tuple(_provider_id(provider) for provider in self._providers)


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


def _is_successful_result(result: Any) -> bool:
    """Return whether a provider acquisition result is successful."""
    return isinstance(result, dict) and result.get("success") is True


def _provider_errors(provider_id: str, result: Any) -> tuple[str, ...]:
    """Return normalized provider errors from an acquisition result."""
    if not isinstance(result, dict):
        return (f"{provider_id} returned invalid result",)

    errors = _safe_sequence(result.get("errors"))
    if errors:
        return tuple(f"{provider_id}: {error}" for error in errors)
    return (f"{provider_id} did not acquire asset",)


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

        def acquire(self, request: dict[str, Any]) -> dict[str, Any]:
            """Return mock acquisition result."""
            if self._should_succeed:
                return {
                    "success": True,
                    "asset": {"asset_id": request.get("asset_id", "")},
                    "errors": [],
                    "warnings": [],
                }
            return {
                "success": False,
                "asset": {},
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
        any("unsupported" in warning for warning in routed["warnings"]),
        failed["success"] is False,
        failing_router.available_providers() == ("failing",),
    )
    return all(checks)


if __name__ == "__main__":
    print("PASS" if _self_test() else "FAIL")
