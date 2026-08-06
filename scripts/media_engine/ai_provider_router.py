"""AI provider routing skeleton for future media generation providers."""

from __future__ import annotations

from typing import Any, Protocol

try:
    from providers.pollinations_provider import PollinationsProvider
except ModuleNotFoundError:
    from scripts.media_engine.providers.pollinations_provider import (
        PollinationsProvider,
    )


class AIProvider(Protocol):
    """Contract expected from future AI media providers."""

    def provider_id(self) -> str:
        """Return the provider identifier."""

    def search(self, request: dict[str, Any]) -> dict[str, Any]:
        """Search or generate AI asset metadata for the request."""


class AIProviderRouter:
    """Register and route requests to future AI providers."""

    def __init__(self, providers: list[AIProvider] | None = None) -> None:
        """Initialize the router with optional injected AI providers."""
        self.providers: tuple[AIProvider, ...] = ()
        if providers:
            for provider in providers:
                self.register_provider(provider)
        else:
            self.register_provider(PollinationsProvider())

    def register_provider(self, provider: AIProvider) -> None:
        """Register one AI provider."""
        self.providers = (*self.providers, provider)

    def available_providers(self) -> tuple[str, ...]:
        """Return registered AI provider ids."""
        return tuple(_provider_id(provider) for provider in self.providers)

    def route(self, request: dict[str, Any]) -> dict[str, Any]:
        """
        Route a request to a future AI provider.

        Arguments:
            request: normalized media request.

        Returns:
            Structured route response.
        """
        errors: list[str] = []
        warnings: list[str] = []

        for provider in self.providers:
            provider_id = _provider_id(provider)

            try:
                result = provider.search(dict(request))
                if not isinstance(result, dict):
                    errors.append(f"{provider_id} returned invalid result")
                    continue

                provider_errors = _safe_sequence(result.get("errors"))
                provider_warnings = _safe_sequence(result.get("warnings"))

                if (
                    result.get("success") is True
                    and _safe_results(result.get("results"))
                ):
                    return _route_result(
                        success=True,
                        provider=provider_id,
                        results=result.get("results"),
                        errors=(),
                        warnings=(*warnings, *provider_warnings),
                    )

                errors.extend(
                    f"{provider_id}: {error}"
                    for error in provider_errors
                )
                warnings.extend(provider_warnings)
                if result.get("success") is True:
                    warnings.append(f"{provider_id} returned no results")
            except Exception as exc:
                errors.append(f"{provider_id} failed: {exc}")

        return _route_result(
            success=False,
            provider=None,
            results=(),
            errors=errors or ["No AI provider returned results."],
            warnings=warnings,
        )


def _provider_id(provider: AIProvider) -> str:
    """Return provider id with a safe fallback."""
    try:
        provider_id = provider.provider_id()
    except Exception:
        provider_id = ""
    return str(provider_id).strip() or "unknown_ai_provider"


def _route_result(
    success: bool,
    provider: str | None,
    results: Any,
    errors: Any,
    warnings: Any,
) -> dict[str, Any]:
    """Build a structured AI routing response."""
    clean_results = _safe_results(results)
    return {
        "success": success,
        "provider": provider,
        "asset": dict(clean_results[0]) if clean_results else None,
        "results": list(clean_results),
        "errors": list(_safe_sequence(errors)),
        "warnings": list(_safe_sequence(warnings)),
    }


def _safe_results(value: Any) -> tuple[dict[str, Any], ...]:
    """Return normalized AI provider result dictionaries."""
    if not isinstance(value, (tuple, list)):
        return ()
    return tuple(dict(item) for item in value if isinstance(item, dict))


def _safe_sequence(value: Any) -> tuple[str, ...]:
    """Return a tuple of non-empty text values."""
    if not isinstance(value, (tuple, list)):
        return ()
    return tuple(
        text
        for text in (str(item).strip() for item in value)
        if text
    )
