"""Pollinations AI media provider adapter."""

from __future__ import annotations

from typing import Any
from urllib.parse import quote

from scripts.media_engine.providers.base_provider import BaseProvider


class PollinationsProvider(BaseProvider):
    """Provider adapter for Pollinations AI image generation metadata."""

    BASE_URL = "https://image.pollinations.ai/prompt"
    PROVIDER_ID = "pollinations"
    PROVIDER_TYPE = "ai"
    LICENSE = "Generated"
    DEFAULT_WIDTH = 1024
    DEFAULT_HEIGHT = 1024
    SUPPORTED_ASSET_TYPES = {
        "background",
        "character",
        "illustration",
        "meme",
        "object",
        "overlay",
        "poster",
        "ui",
    }

    def provider_id(self) -> str:
        """Return the unique provider identifier."""
        return self.PROVIDER_ID

    def provider_type(self) -> str:
        """Return the provider category."""
        return self.PROVIDER_TYPE

    def priority(self) -> int:
        """Return the provider priority used for provider ordering."""
        return 1

    def supports(self, asset_type: str) -> bool:
        """Return whether Pollinations can generate the asset type."""
        return str(asset_type).strip().lower() in self.SUPPORTED_ASSET_TYPES

    def search(self, request: dict) -> dict:
        """Return normalized Pollinations generation metadata."""
        response_payload = self._base_response()

        try:
            search_query = str(request["search_query"]).strip()
        except KeyError:
            search_query = ""

        asset_type = str(request.get("asset_type", "")).strip()

        if not search_query:
            response_payload["errors"].append("Missing search_query.")
            return response_payload

        if not self.supports(asset_type):
            response_payload["errors"].append(
                f"Unsupported asset_type for Pollinations: {asset_type}"
            )
            return response_payload

        try:
            width, height = self._dimensions(request)
            generation_url = self._generation_url(search_query, width, height)
            response_payload["results"] = [
                {
                    "asset_id": self._asset_id(search_query, width, height),
                    "provider": self.PROVIDER_ID,
                    "provider_type": self.PROVIDER_TYPE,
                    "asset_type": asset_type,
                    "prompt": search_query,
                    "width": width,
                    "height": height,
                    "preview_url": generation_url,
                    "download_url": generation_url,
                    "license": self.LICENSE,
                    "generation_cost": 0,
                }
            ]
            response_payload["success"] = True
            return response_payload
        except Exception as exc:
            response_payload["errors"].append(
                f"Unexpected Pollinations provider error: {exc}"
            )
            return response_payload

    def download(self, search_result: dict) -> dict:
        """Return a structured placeholder response for future downloads."""
        return {
            "success": False,
            "provider": self.PROVIDER_ID,
            "asset_id": search_result.get("asset_id"),
            "errors": [
                "Download is not implemented for PollinationsProvider."
            ],
            "warnings": [],
        }

    def _base_response(self) -> dict:
        """Return the standard provider response envelope."""
        return {
            "success": False,
            "provider": self.PROVIDER_ID,
            "results": [],
            "errors": [],
            "warnings": [],
        }

    def _dimensions(self, request: dict[str, Any]) -> tuple[int, int]:
        """Return requested dimensions or provider defaults."""
        resolution = request.get("resolution")
        if isinstance(resolution, dict):
            width = _safe_positive_int(resolution.get("width"))
            height = _safe_positive_int(resolution.get("height"))
            if width and height:
                return width, height

        if isinstance(resolution, (list, tuple)) and len(resolution) >= 2:
            width = _safe_positive_int(resolution[0])
            height = _safe_positive_int(resolution[1])
            if width and height:
                return width, height

        aspect_ratio = str(request.get("aspect_ratio", "")).strip()
        if aspect_ratio == "16:9":
            return 1024, 576
        if aspect_ratio == "9:16":
            return 576, 1024
        if aspect_ratio == "1:1":
            return self.DEFAULT_WIDTH, self.DEFAULT_HEIGHT

        return self.DEFAULT_WIDTH, self.DEFAULT_HEIGHT

    def _generation_url(self, prompt: str, width: int, height: int) -> str:
        """Return the Pollinations image generation URL."""
        encoded_prompt = quote(prompt)
        return f"{self.BASE_URL}/{encoded_prompt}?width={width}&height={height}"

    def _asset_id(self, prompt: str, width: int, height: int) -> str:
        """Return a deterministic provider asset identifier."""
        slug = "_".join(
            "".join(
                char.lower() if char.isalnum() else "_"
                for char in prompt
            ).split("_")
        )
        slug = slug[:80] or "prompt"
        return f"{self.PROVIDER_ID}_{slug}_{width}x{height}"


def _safe_positive_int(value: Any) -> int:
    """Return a positive integer value or zero."""
    try:
        number = int(value)
    except (TypeError, ValueError):
        return 0
    return number if number > 0 else 0
