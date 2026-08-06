"""Abstract provider contract for media asset providers."""

from abc import ABC, abstractmethod


class BaseProvider(ABC):
    """Base interface that all media providers must implement."""

    @abstractmethod
    def provider_id(self) -> str:
        """Return the unique provider identifier."""

    @abstractmethod
    def provider_type(self) -> str:
        """Return the provider category or integration type."""

    @abstractmethod
    def priority(self) -> int:
        """Return the provider priority used for provider ordering."""

    @abstractmethod
    def supports(self, asset_type: str) -> bool:
        """Return whether the provider supports the requested asset type."""

    @abstractmethod
    def search(self, request: dict) -> dict:
        """Search for media assets using the provided request payload."""

    @abstractmethod
    def download(self, search_result: dict) -> dict:
        """Download or resolve media from a provider search result."""
