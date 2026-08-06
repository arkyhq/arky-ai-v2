"""Pexels media provider adapter."""

import os
from json import JSONDecodeError
from typing import Any

import requests
from dotenv import load_dotenv

from scripts.media_engine.providers.base_provider import BaseProvider


class PexelsProvider(BaseProvider):
    """Provider adapter for searching media through the Pexels REST API."""

    SEARCH_URL = "https://api.pexels.com/v1/search"
    PROVIDER_ID = "pexels"
    LICENSE = "Pexels License"
    TIMEOUT_SECONDS = 15
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

    def __init__(self) -> None:
        """Load provider configuration from environment variables."""
        load_dotenv()
        self.api_key = os.getenv("PEXELS_API_KEY")

    def provider_id(self) -> str:
        """Return the unique provider identifier."""
        return self.PROVIDER_ID

    def provider_type(self) -> str:
        """Return the provider category."""
        return "image"

    def priority(self) -> int:
        """Return the provider priority used for provider ordering."""
        return 100

    def supports(self, asset_type: str) -> bool:
        """Return whether Pexels can source the requested ARKY asset type."""
        return asset_type.lower() in self.SUPPORTED_ASSET_TYPES

    def search(self, request: dict) -> dict:
        """Search Pexels and return normalized image results."""
        response_payload = self._base_response()
        asset_type = str(request.get("asset_type", "")).strip()
        try:
            search_query = str(request["search_query"]).strip()
        except KeyError:
            search_query = ""
        per_page = request.get("per_page", 15)

        if not self.api_key:
            response_payload["errors"].append("Missing PEXELS_API_KEY.")
            return response_payload

        if not search_query:
            response_payload["errors"].append("Missing search_query.")
            return response_payload

        if not self.supports(asset_type):
            response_payload["errors"].append(
                f"Unsupported asset_type for Pexels: {asset_type}"
            )
            return response_payload

        headers = {"Authorization": self.api_key}
        params = {"query": search_query, "per_page": per_page}

        try:
            response = requests.get(
                self.SEARCH_URL,
                headers=headers,
                params=params,
                timeout=self.TIMEOUT_SECONDS,
            )
            response.raise_for_status()
            data = response.json()
            if not isinstance(data, dict):
                response_payload["errors"].append(
                    "Pexels returned invalid JSON."
                )
                return response_payload
        except requests.Timeout:
            response_payload["errors"].append("Pexels request timed out.")
            return response_payload
        except requests.HTTPError as exc:
            status_code = exc.response.status_code if exc.response else None
            response_payload["errors"].append(
                f"Pexels HTTP error: {status_code}"
            )
            return response_payload
        except JSONDecodeError:
            response_payload["errors"].append("Pexels returned invalid JSON.")
            return response_payload
        except requests.RequestException as exc:
            response_payload["errors"].append(f"Pexels request error: {exc}")
            return response_payload
        except ValueError:
            response_payload["errors"].append("Pexels returned invalid JSON.")
            return response_payload
        except Exception as exc:
            response_payload["errors"].append(
                f"Unexpected Pexels provider error: {exc}"
            )
            return response_payload

        photos = data.get("photos", [])
        response_payload["results"] = [
            self._normalize_photo(photo, asset_type)
            for photo in photos
            if isinstance(photo, dict)
        ]
        response_payload["success"] = True
        return response_payload

    def download(self, search_result: dict) -> dict:
        """Return a structured placeholder response for future downloads."""
        return {
            "success": False,
            "provider": self.PROVIDER_ID,
            "asset_id": search_result.get("asset_id"),
            "errors": ["Download is not implemented for PexelsProvider."],
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

    def _normalize_photo(self, photo: dict[str, Any], asset_type: str) -> dict:
        """Normalize a Pexels photo object into the shared asset shape."""
        sources = photo.get("src") or {}

        return {
            "asset_id": str(photo.get("id", "")),
            "provider": self.PROVIDER_ID,
            "asset_type": asset_type,
            "photographer": photo.get("photographer", ""),
            "width": photo.get("width"),
            "height": photo.get("height"),
            "preview_url": sources.get("medium", ""),
            "download_url": sources.get("original", ""),
            "license": self.LICENSE,
        }
