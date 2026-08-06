"""Reusable media asset download manager."""

import hashlib
from pathlib import Path
from typing import Optional
from urllib.parse import urlparse

import requests


class DownloadManager:
    """Download remote media assets into the local asset library."""

    ACCEPTED_MIME_TYPES = {
        "image/jpeg": ".jpg",
        "image/png": ".png",
        "image/webp": ".webp",
    }
    OUTPUT_DIR = Path("assets/library")
    RETRY_ATTEMPTS = 3
    TIMEOUT_SECONDS = 20

    def download_asset(self, asset: dict) -> dict:
        """Download a remote asset and return local file metadata."""
        response_payload = self._base_response(asset)
        download_url = str(asset.get("download_url", "")).strip()

        if not self._is_valid_url(download_url):
            response_payload["errors"].append("Invalid URL.")
            return response_payload

        try:
            response = self._request_with_retries(download_url)
        except requests.Timeout:
            response_payload["errors"].append("Download timed out.")
            return response_payload
        except requests.RequestException as exc:
            response_payload["errors"].append(f"Network failure: {exc}")
            return response_payload
        except Exception as exc:
            response_payload["errors"].append(
                f"Unexpected download error: {exc}"
            )
            return response_payload

        if response is None:
            response_payload["errors"].append("Network failure.")
            return response_payload

        content_type = self._content_type(response)
        extension = self.ACCEPTED_MIME_TYPES.get(content_type)
        if extension is None:
            response_payload["errors"].append(
                f"Invalid MIME type: {content_type or 'unknown'}"
            )
            return response_payload

        filename = self._filename(asset, extension)
        local_path = self.OUTPUT_DIR / filename

        try:
            self.OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
            local_path.write_bytes(response.content)
        except OSError as exc:
            response_payload["errors"].append(f"Write failure: {exc}")
            return response_payload

        response_payload["success"] = True
        response_payload["local_path"] = str(local_path)
        response_payload["sha256"] = hashlib.sha256(response.content).hexdigest()
        return response_payload

    def _request_with_retries(
        self,
        download_url: str,
    ) -> Optional[requests.Response]:
        """Request a URL with a fixed retry count."""
        last_response = None

        for _ in range(self.RETRY_ATTEMPTS):
            response = requests.get(
                download_url,
                timeout=self.TIMEOUT_SECONDS,
            )
            last_response = response
            if response.ok:
                return response

        if last_response is not None:
            last_response.raise_for_status()

        return None

    def _base_response(self, asset: dict) -> dict:
        """Return the standard download response envelope."""
        return {
            "success": False,
            "local_path": "",
            "sha256": "",
            "provider": asset.get("provider", ""),
            "asset_id": asset.get("asset_id", ""),
            "errors": [],
            "warnings": [],
        }

    def _is_valid_url(self, download_url: str) -> bool:
        """Return whether the URL is an HTTP or HTTPS URL with a host."""
        parsed_url = urlparse(download_url)
        return parsed_url.scheme in {"http", "https"} and bool(
            parsed_url.netloc
        )

    def _content_type(self, response: requests.Response) -> str:
        """Return the normalized response content type."""
        return response.headers.get("Content-Type", "").split(";")[0].lower()

    def _filename(self, asset: dict, extension: str) -> str:
        """Return the local asset filename."""
        provider = str(asset.get("provider", "")).strip()
        asset_id = str(asset.get("asset_id", "")).strip()
        return f"{provider}_{asset_id}{extension}"
