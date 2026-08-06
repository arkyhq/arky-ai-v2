"""
In-memory asset metadata library for ARKY-managed media assets.

The Asset Library is a deterministic metadata registry. It does not route,
download, generate, validate providers, read files, write files, log, or call
external services.
"""

from __future__ import annotations

from datetime import datetime, timezone
from typing import Any


ASSET_FIELDS = (
    "asset_id",
    "asset_type",
    "provider",
    "provider_type",
    "source",
    "license",
    "confidence",
    "status",
    "local_path",
    "metadata",
    "hash",
    "created_at",
    "updated_at",
)

LOOKUP_FIELDS = frozenset({"asset_id", "hash", "asset_type", "provider"})

DOWNLOADED_ASSET_FIELDS = (
    "asset_id",
    "provider",
    "provider_asset_id",
    "local_path",
    "download_url",
    "sha256",
    "width",
    "height",
    "license",
    "asset_type",
    "created_at",
    "last_used",
    "tags",
)

REQUIRED_DOWNLOADED_ASSET_FIELDS = (
    "asset_id",
    "provider",
    "local_path",
    "download_url",
    "sha256",
    "width",
    "height",
    "license",
    "asset_type",
)


class AssetLibrary:
    """
    Manage ARKY asset metadata in memory.

    The library stores shallow copies of supplied metadata records and supports
    generic asset types for images, audio, video, subtitles, thumbnails,
    animations, and future media categories.
    """

    def __init__(self) -> None:
        """Initialize an empty in-memory asset library."""
        self._assets: dict[str, dict[str, Any]] = {}

    def register_asset(self, asset: dict[str, Any]) -> dict[str, Any]:
        """
        Register one asset metadata record.

        Arguments:
            asset: asset metadata dictionary.

        Returns:
            Structured registration result.
        """
        errors: list[str] = []
        warnings: list[str] = []

        try:
            record = _normalize_asset(asset)
            asset_id = _safe_text(record.get("asset_id"))
            asset_hash = _safe_text(record.get("hash"))

            if not asset_id:
                errors.append("asset_id must be populated")
                return _result(False, {}, errors, warnings)

            if asset_id in self._assets:
                errors.append(f"asset_id already exists: {asset_id}")
                return _result(False, self._assets[asset_id], errors, warnings)

            duplicate = self._find_by_hash(asset_hash)
            if asset_hash and duplicate:
                errors.append(f"duplicate asset hash: {asset_hash}")
                return _result(False, duplicate, errors, warnings)

            timestamp = _timestamp()
            record["created_at"] = _safe_text(record.get("created_at")) or timestamp
            record["updated_at"] = _safe_text(record.get("updated_at")) or timestamp
            self._assets[asset_id] = record
            return _result(True, record, errors, warnings)
        except Exception as exc:
            errors.append(f"unexpected register error: {exc}")
            return _result(False, {}, errors, warnings)

    def update_asset(
        self,
        asset_id: str,
        updates: dict[str, Any],
    ) -> dict[str, Any]:
        """
        Apply partial metadata updates to an existing asset.

        Arguments:
            asset_id: existing asset identifier.
            updates: partial metadata updates.

        Returns:
            Structured update result.
        """
        errors: list[str] = []
        warnings: list[str] = []

        try:
            clean_asset_id = _safe_text(asset_id)
            if clean_asset_id not in self._assets:
                errors.append(f"asset not found: {clean_asset_id}")
                return _result(False, {}, errors, warnings)

            clean_updates = _safe_mapping(updates)
            if not clean_updates:
                warnings.append("updates are empty")
                return _result(True, self._assets[clean_asset_id], errors, warnings)

            current = dict(self._assets[clean_asset_id])
            next_hash = _safe_text(clean_updates.get("hash"))
            duplicate = self._find_by_hash(next_hash, exclude_asset_id=clean_asset_id)
            if next_hash and duplicate:
                errors.append(f"duplicate asset hash: {next_hash}")
                return _result(False, duplicate, errors, warnings)

            for field, value in clean_updates.items():
                if field == "created_at":
                    warnings.append("created_at is immutable")
                    continue
                if field == "asset_id" and _safe_text(value) != clean_asset_id:
                    warnings.append("asset_id cannot be changed")
                    continue
                current[field] = value

            current["updated_at"] = _timestamp()
            self._assets[clean_asset_id] = _normalize_asset(current)
            return _result(True, self._assets[clean_asset_id], errors, warnings)
        except Exception as exc:
            errors.append(f"unexpected update error: {exc}")
            return _result(False, {}, errors, warnings)

    def register_downloaded_asset(self, asset: dict[str, Any]) -> dict[str, Any]:
        """
        Register downloaded asset metadata in the asset library cache.

        Arguments:
            asset: downloaded asset metadata dictionary.

        Returns:
            Structured registration result.
        """
        errors: list[str] = []
        warnings: list[str] = []

        try:
            source = _safe_mapping(asset)
            missing_fields = _missing_downloaded_asset_fields(source)
            if missing_fields:
                errors.append(
                    "missing downloaded asset fields: "
                    + ", ".join(missing_fields)
                )
                return _result(False, {}, errors, warnings)

            existing = self.asset_exists(source)
            if existing.get("exists") is True:
                errors.append("downloaded asset already exists")
                return _result(False, existing.get("asset", {}), errors, warnings)

            timestamp = _timestamp()
            record = {
                field: source.get(field, "")
                for field in DOWNLOADED_ASSET_FIELDS
            }
            record["provider_asset_id"] = _safe_text(
                source.get("provider_asset_id")
            )
            record["created_at"] = (
                _safe_text(source.get("created_at")) or timestamp
            )
            record["last_used"] = _safe_text(source.get("last_used")) or timestamp
            record["tags"] = _safe_tags(source.get("tags"))
            record["hash"] = _safe_text(source.get("sha256"))
            record["status"] = source.get("status", "downloaded")
            record["metadata"] = _safe_mapping(source.get("metadata"))

            registered = self.register_asset(record)
            if not registered.get("success"):
                return registered

            return _result(True, registered.get("asset", {}), errors, warnings)
        except Exception as exc:
            errors.append(f"unexpected register downloaded asset error: {exc}")
            return _result(False, {}, errors, warnings)

    def get_asset(self, asset_id: str) -> dict[str, Any]:
        """
        Return one asset by asset_id.

        Arguments:
            asset_id: asset identifier.

        Returns:
            Structured lookup result.
        """
        errors: list[str] = []
        warnings: list[str] = []

        try:
            clean_asset_id = _safe_text(asset_id)
            asset = self._assets.get(clean_asset_id)
            if not asset:
                errors.append(f"asset not found: {clean_asset_id}")
                return _result(False, {}, errors, warnings)
            return _result(True, asset, errors, warnings)
        except Exception as exc:
            errors.append(f"unexpected get error: {exc}")
            return _result(False, {}, errors, warnings)

    def find_asset(self, field: str, value: Any) -> dict[str, Any]:
        """
        Find assets by asset_id, hash, asset_type, or provider.

        Arguments:
            field: lookup field.
            value: lookup value.

        Returns:
            Structured result. Singular lookups return the first asset in
            asset. Multi-match lookups return all matches in assets.
        """
        errors: list[str] = []
        warnings: list[str] = []

        try:
            clean_field = _safe_text(field)
            if clean_field not in LOOKUP_FIELDS:
                errors.append(f"unsupported lookup field: {clean_field}")
                return _result(False, {}, errors, warnings, ())

            clean_value = _safe_text(value)
            matches = tuple(
                dict(asset)
                for asset in self._assets.values()
                if _safe_text(asset.get(clean_field)) == clean_value
            )

            if not matches:
                errors.append(f"asset not found by {clean_field}: {clean_value}")
                return _result(False, {}, errors, warnings, ())

            return _result(True, matches[0], errors, warnings, matches)
        except Exception as exc:
            errors.append(f"unexpected find error: {exc}")
            return _result(False, {}, errors, warnings, ())

    def find_by_sha256(self, sha256: str) -> dict[str, Any]:
        """
        Find one asset by SHA256 hash.

        Arguments:
            sha256: downloaded asset SHA256 hash.

        Returns:
            Structured lookup result.
        """
        return self._find_by_download_field("sha256", sha256)

    def find_by_download_url(self, url: str) -> dict[str, Any]:
        """
        Find one asset by original download URL.

        Arguments:
            url: remote media download URL.

        Returns:
            Structured lookup result.
        """
        return self._find_by_download_field("download_url", url)

    def find_by_local_path(self, path: str) -> dict[str, Any]:
        """
        Find one asset by local filesystem path.

        Arguments:
            path: local downloaded asset path.

        Returns:
            Structured lookup result.
        """
        return self._find_by_download_field("local_path", path)

    def asset_exists(self, asset: Any) -> dict[str, Any]:
        """
        Return whether an asset exists by id or downloaded asset identity.

        Arguments:
            asset: asset identifier or downloaded asset metadata dictionary.

        Returns:
            Structured existence result.
        """
        errors: list[str] = []
        warnings: list[str] = []

        if isinstance(asset, dict):
            match = self._find_existing_downloaded_asset(asset)
            exists = bool(match)
            return {
                "success": True,
                "exists": exists,
                "asset": match,
                "errors": tuple(errors),
                "warnings": tuple(warnings),
            }

        clean_asset_id = _safe_text(asset)
        exists = clean_asset_id in self._assets
        return {
            "success": True,
            "exists": exists,
            "asset": dict(self._assets[clean_asset_id]) if exists else {},
            "errors": tuple(errors),
            "warnings": tuple(warnings),
        }

    def list_assets(self) -> dict[str, Any]:
        """
        List all registered asset metadata records.

        Returns:
            Structured list result.
        """
        assets = tuple(dict(asset) for asset in self._assets.values())
        return {
            "success": True,
            "asset": {},
            "assets": assets,
            "errors": (),
            "warnings": (),
        }

    def _find_by_hash(
        self,
        asset_hash: str,
        exclude_asset_id: str = "",
    ) -> dict[str, Any]:
        """Return first asset with the supplied hash, excluding one asset id."""
        if not asset_hash:
            return {}

        for asset in self._assets.values():
            if _safe_text(asset.get("asset_id")) == exclude_asset_id:
                continue
            if _safe_text(asset.get("hash")) == asset_hash:
                return dict(asset)
        return {}

    def _find_by_download_field(
        self,
        field: str,
        value: Any,
    ) -> dict[str, Any]:
        """Return first asset matching a downloaded asset field."""
        errors: list[str] = []
        warnings: list[str] = []
        clean_value = _safe_text(value)

        try:
            for asset in self._assets.values():
                if _safe_text(asset.get(field)) == clean_value:
                    return _result(True, asset, errors, warnings)
                if field == "sha256" and (
                    _safe_text(asset.get("hash")) == clean_value
                ):
                    return _result(True, asset, errors, warnings)

            errors.append(f"asset not found by {field}: {clean_value}")
            return _result(False, {}, errors, warnings)
        except Exception as exc:
            errors.append(f"unexpected find by {field} error: {exc}")
            return _result(False, {}, errors, warnings)

    def _find_existing_downloaded_asset(
        self,
        asset: dict[str, Any],
    ) -> dict[str, Any]:
        """Return an existing downloaded asset matching cache identity."""
        sha256 = _safe_text(asset.get("sha256"))
        download_url = _safe_text(asset.get("download_url"))
        local_path = _safe_text(asset.get("local_path"))

        for existing_asset in self._assets.values():
            existing_sha256 = _safe_text(existing_asset.get("sha256"))
            existing_hash = _safe_text(existing_asset.get("hash"))
            if sha256 and sha256 in {existing_sha256, existing_hash}:
                return dict(existing_asset)
            if download_url and (
                _safe_text(existing_asset.get("download_url")) == download_url
            ):
                return dict(existing_asset)
            if local_path and (
                _safe_text(existing_asset.get("local_path")) == local_path
            ):
                return dict(existing_asset)

        return {}


def _normalize_asset(asset: dict[str, Any]) -> dict[str, Any]:
    """Return a normalized shallow asset metadata record."""
    source = _safe_mapping(asset)
    record = {field: source.get(field, "") for field in ASSET_FIELDS}
    record["metadata"] = _safe_mapping(source.get("metadata"))

    for field, value in source.items():
        if field not in record:
            record[field] = value

    return record


def _result(
    success: bool,
    asset: dict[str, Any],
    errors: list[str],
    warnings: list[str],
    assets: tuple[dict[str, Any], ...] = (),
) -> dict[str, Any]:
    """Build a structured method result."""
    result = {
        "success": success,
        "asset": dict(asset),
        "errors": tuple(errors),
        "warnings": tuple(warnings),
    }
    if assets:
        result["assets"] = assets
    return result


def _safe_mapping(value: Any) -> dict[str, Any]:
    """Return a shallow dictionary copy when possible."""
    if isinstance(value, dict):
        return dict(value)
    return {}


def _missing_downloaded_asset_fields(asset: dict[str, Any]) -> tuple[str, ...]:
    """Return required downloaded asset fields that are not populated."""
    return tuple(
        field
        for field in REQUIRED_DOWNLOADED_ASSET_FIELDS
        if _safe_text(asset.get(field)) == ""
    )


def _safe_tags(value: Any) -> list[Any]:
    """Return tags as a new list."""
    if isinstance(value, list):
        return list(value)
    if isinstance(value, tuple):
        return list(value)
    return []


def _safe_text(value: Any) -> str:
    """Return stripped text for scalar values."""
    if value is None:
        return ""
    return str(value).strip()


def _timestamp() -> str:
    """Return a deterministic-format UTC timestamp."""
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat()


def _mock_asset(asset_id: str = "asset_001", asset_hash: str = "hash_001") -> dict[str, Any]:
    """Build a mock asset record for self-test."""
    return {
        "asset_id": asset_id,
        "asset_type": "background",
        "provider": "Local Asset Library",
        "provider_type": "local",
        "source": "mock",
        "license": "internal",
        "confidence": 100,
        "status": "available",
        "local_path": "mock/path",
        "metadata": {"scene_id": "scene_001"},
        "hash": asset_hash,
    }


def _self_test() -> bool:
    """Verify in-memory asset library behavior with mock records."""
    library = AssetLibrary()
    registered = library.register_asset(_mock_asset())
    duplicate = library.register_asset(_mock_asset("asset_002", "hash_001"))
    by_id = library.get_asset("asset_001")
    by_hash = library.find_asset("hash", "hash_001")
    updated = library.update_asset("asset_001", {"status": "approved"})
    listed = library.list_assets()
    exists = library.asset_exists("asset_001")

    checks = (
        registered["success"] is True,
        duplicate["success"] is False,
        by_id["success"] is True,
        by_hash["success"] is True,
        updated["asset"].get("status") == "approved",
        len(listed.get("assets", ())) == 1,
        exists.get("exists") is True,
    )
    return all(checks)


if __name__ == "__main__":
    print("PASS" if _self_test() else "FAIL")
