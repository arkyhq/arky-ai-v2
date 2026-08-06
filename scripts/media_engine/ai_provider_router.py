"""AI provider routing skeleton for future media generation providers."""

from __future__ import annotations

from typing import Any, Protocol


class AIProvider(Protocol):
    """Contract expected from future AI media providers."""

    def provider_id(self) -> str:
        """Return the provider identifier."""


class AIProviderRouter:
    """Register and route requests to future AI providers."""

    def __init__(self, providers: list[AIProvider] | None = None) -> None:
        """Initialize the router with optional injected AI providers."""
        self.providers: tuple[AIProvider, ...] = ()
        if providers:
            for provider in providers:
                self.register_provider(provider)

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
        if not self.providers:
            return {
                "success": False,
                "provider": None,
                "asset": None,
                "errors": ["No AI providers registered."],
                "warnings": [],
            }

        return {
            "success": False,
            "provider": None,
            "asset": None,
            "errors": ["AI provider routing is not implemented."],
            "warnings": [],
        }


def _provider_id(provider: AIProvider) -> str:
    """Return provider id with a safe fallback."""
    try:
        provider_id = provider.provider_id()
    except Exception:
        provider_id = ""
    return str(provider_id).strip() or "unknown_ai_provider"
