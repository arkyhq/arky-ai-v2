"""
Media Engine orchestration for the ARKY Media Acquisition pipeline.

This module coordinates public module APIs only. It performs no provider logic,
validation logic, AI work, direct networking, direct filesystem operations,
asset searching, prompt generation, or routing decisions.
"""

from __future__ import annotations

from datetime import datetime, timezone
from typing import Any, Iterable

try:
    from ai_provider_router import AIProviderRouter
    from asset_scorer import AssetScorer
    from asset_library import AssetLibrary
    from download.download_manager import DownloadManager
    from media_mapper import map_media_request
    from media_validator import validate_media_request
    from provider_router import ProviderRouter
except ModuleNotFoundError:
    from scripts.media_engine.ai_provider_router import AIProviderRouter
    from scripts.media_engine.asset_scorer import AssetScorer
    from scripts.media_engine.asset_library import AssetLibrary
    from scripts.media_engine.download.download_manager import DownloadManager
    from scripts.media_engine.media_mapper import map_media_request
    from scripts.media_engine.media_validator import validate_media_request
    from scripts.media_engine.provider_router import ProviderRouter


STOCK_SCORE_THRESHOLD = 80


class MediaEngine:
    """
    Orchestrate the complete Media Acquisition pipeline.

    Dependencies are supplied externally so provider implementations and asset
    storage remain replaceable without changing engine orchestration.
    """

    def __init__(
        self,
        router: ProviderRouter | None = None,
        asset_library: AssetLibrary | None = None,
        download_manager: DownloadManager | None = None,
        asset_scorer: AssetScorer | None = None,
        ai_provider_router: AIProviderRouter | None = None,
    ) -> None:
        """Initialize Media Engine with injectable pipeline dependencies."""
        self._router = router if router is not None else ProviderRouter()
        self._asset_library = (
            asset_library if asset_library is not None else AssetLibrary()
        )
        self._download_manager = (
            download_manager
            if download_manager is not None
            else DownloadManager()
        )
        self._asset_scorer = (
            asset_scorer if asset_scorer is not None else AssetScorer()
        )
        self._ai_provider_router = (
            ai_provider_router
            if ai_provider_router is not None
            else AIProviderRouter()
        )

    def process_request(self, request: dict[str, Any]) -> dict[str, Any]:
        """
        Process one Asset Planning record through the Media Engine pipeline.

        Arguments:
            request: Asset Planning record to map into a Media Request.

        Returns:
            Structured pipeline result.
        """
        try:
            media_request = map_media_request(request)
            request_validation = validate_media_request(media_request)
            if not request_validation.get("valid"):
                return _pipeline_result(
                    success=False,
                    status="validation_failed",
                    asset={},
                    errors=request_validation.get("errors"),
                    warnings=request_validation.get("warnings"),
                )

            cached = self._asset_library.asset_exists(
                media_request.get("asset_id", "")
            )
            if cached.get("success") is True and cached.get("exists") is True:
                return _pipeline_result(
                    success=True,
                    status="cache_hit",
                    asset=cached.get("asset"),
                    errors=cached.get("errors"),
                    warnings=cached.get("warnings"),
                )

            routed = self._router.route(media_request)
            if routed.get("success") is not True:
                return self._ai_provider_router.route(media_request)

            candidates = _provider_candidates(routed)
            if not candidates:
                return self._ai_provider_router.route(media_request)

            scoring = self._asset_scorer.score_candidates(candidates)
            if scoring.get("success") is not True:
                return self._ai_provider_router.route(media_request)

            best_asset = _safe_mapping(scoring.get("best_asset"))
            if not best_asset:
                return self._ai_provider_router.route(media_request)

            best_score = _best_score(scoring)
            if best_score < STOCK_SCORE_THRESHOLD:
                return self._ai_provider_router.route(media_request)

            downloaded = self._download_manager.download_asset(best_asset)
            if downloaded.get("success") is not True:
                return _pipeline_result(
                    success=False,
                    status="download_failed",
                    asset=best_asset,
                    errors=downloaded.get("errors"),
                    warnings=(
                        *_as_tuple(routed.get("warnings")),
                        *_as_tuple(scoring.get("warnings")),
                        *_as_tuple(downloaded.get("warnings")),
                    ),
                )

            downloaded_asset = _downloaded_asset_record(
                media_request,
                best_asset,
                downloaded,
            )
            registration = self._asset_library.register_downloaded_asset(
                downloaded_asset
            )
            if registration.get("success") is not True:
                return _pipeline_result(
                    success=False,
                    status="registration_failed",
                    asset=registration.get("asset"),
                    errors=registration.get("errors"),
                    warnings=registration.get("warnings"),
                )

            return _pipeline_result(
                success=True,
                status="success",
                asset=registration.get("asset"),
                errors=(),
                warnings=(
                    *_as_tuple(routed.get("warnings")),
                    *_as_tuple(scoring.get("warnings")),
                    *_as_tuple(downloaded.get("warnings")),
                    *_as_tuple(registration.get("warnings")),
                ),
            )
        except Exception as exc:
            return _pipeline_result(
                success=False,
                status="failed",
                asset={},
                errors=(f"unexpected media engine error: {exc}",),
                warnings=(),
            )

    def process_batch(
        self,
        requests: Iterable[dict[str, Any]],
    ) -> tuple[dict[str, Any], ...]:
        """
        Process multiple Asset Planning records through the Media Engine.

        Arguments:
            requests: iterable of Asset Planning records.

        Returns:
            Tuple of structured pipeline results.
        """
        try:
            return tuple(self.process_request(request) for request in requests)
        except Exception as exc:
            return (
                _pipeline_result(
                    success=False,
                    status="failed",
                    asset={},
                    errors=(f"unexpected media engine batch error: {exc}",),
                    warnings=(),
                ),
            )


def _provider_candidates(routed: dict[str, Any]) -> list[dict[str, Any]]:
    """Return normalized provider candidates from a routing result."""
    candidates = routed.get("candidates")
    if isinstance(candidates, (list, tuple)):
        return [
            _safe_mapping(candidate)
            for candidate in candidates
            if isinstance(candidate, dict)
        ]

    results = routed.get("results")
    if isinstance(results, (list, tuple)):
        return [
            _safe_mapping(result)
            for result in results
            if isinstance(result, dict)
        ]

    asset = _safe_mapping(routed.get("asset"))
    return [asset] if asset else []


def _best_score(scoring: dict[str, Any]) -> int:
    """Return the highest candidate score from a scorer response."""
    scored_candidates = scoring.get("candidates")
    if not isinstance(scored_candidates, (list, tuple)):
        return 0

    scores = [
        _safe_int(candidate.get("score"))
        for candidate in scored_candidates
        if isinstance(candidate, dict)
    ]
    return max(scores, default=0)


def _downloaded_asset_record(
    media_request: dict[str, Any],
    provider_asset: dict[str, Any],
    downloaded: dict[str, Any],
) -> dict[str, Any]:
    """Merge request, provider, and download metadata for cache storage."""
    timestamp = _timestamp()
    provider_asset_id = _safe_text(provider_asset.get("asset_id"))
    metadata = _safe_mapping(media_request.get("metadata"))

    return {
        **provider_asset,
        **downloaded,
        "asset_id": _safe_text(media_request.get("asset_id"))
        or provider_asset_id,
        "provider": _safe_text(provider_asset.get("provider"))
        or _safe_text(downloaded.get("provider")),
        "provider_asset_id": _safe_text(
            provider_asset.get("provider_asset_id")
        )
        or provider_asset_id,
        "asset_type": _safe_text(media_request.get("asset_type"))
        or _safe_text(provider_asset.get("asset_type")),
        "download_url": _safe_text(provider_asset.get("download_url")),
        "local_path": _safe_text(downloaded.get("local_path")),
        "sha256": _safe_text(downloaded.get("sha256")),
        "width": provider_asset.get("width", ""),
        "height": provider_asset.get("height", ""),
        "license": provider_asset.get("license", ""),
        "created_at": timestamp,
        "last_used": timestamp,
        "tags": _safe_tags(metadata.get("tags")),
    }


def _timestamp() -> str:
    """Return an ISO-like UTC timestamp for downloaded asset metadata."""
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat()


def _safe_tags(value: Any) -> list[str]:
    """Return clean tag strings as a list."""
    if not isinstance(value, (tuple, list)):
        return []
    return list(filter(None, (_safe_text(item) for item in value)))


def _acquisition_output(routed: dict[str, Any]) -> dict[str, Any]:
    """Build the output package for legacy callers that import this helper."""
    asset = _safe_mapping(routed.get("asset"))
    provider = _safe_text(routed.get("provider"))
    provider_type = _safe_text(routed.get("provider_type")) or _safe_text(
        asset.get("provider_type")
    )

    return {
        "success": routed.get("success") is True,
        "status": "success" if routed.get("success") is True else "failed",
        "provider": provider or _safe_text(asset.get("provider")),
        "provider_type": provider_type,
        "asset": asset,
        "errors": list(_as_tuple(routed.get("errors"))),
        "warnings": list(_as_tuple(routed.get("warnings"))),
        "metadata": _safe_mapping(routed.get("metadata")),
    }


def _pipeline_result(
    success: bool,
    status: str,
    asset: Any,
    errors: Any,
    warnings: Any,
) -> dict[str, Any]:
    """Build a structured Media Engine result."""
    return {
        "success": success,
        "status": status,
        "asset": _safe_mapping(asset),
        "errors": list(_as_tuple(errors)),
        "warnings": list(_as_tuple(warnings)),
    }


def _safe_mapping(value: Any) -> dict[str, Any]:
    """Return a shallow dictionary copy when possible."""
    if isinstance(value, dict):
        return dict(value)
    return {}


def _safe_text(value: Any) -> str:
    """Return stripped text for scalar values."""
    if value is None:
        return ""
    return str(value).strip()


def _safe_int(value: Any) -> int:
    """Return integer value when possible."""
    try:
        return int(value)
    except (TypeError, ValueError):
        return 0


def _as_tuple(value: Any) -> tuple[Any, ...]:
    """Return value as a tuple for result normalization."""
    if value is None:
        return ()
    if isinstance(value, tuple):
        return value
    if isinstance(value, list):
        return tuple(value)
    return (value,)


def _self_test() -> bool:
    """Verify Media Engine orchestration with mock providers and requests."""

    class MockProvider:
        """Small provider contract implementation for self-test."""

        def __init__(self, should_succeed: bool = True) -> None:
            self._should_succeed = should_succeed

        def provider_id(self) -> str:
            """Return mock provider id."""
            return "Pexels"

        def supports(self, asset_type: str) -> bool:
            """Return whether mock provider supports asset type."""
            return asset_type == "background"

        def priority(self) -> int:
            """Return mock provider priority."""
            return 1

        def provider_type(self) -> str:
            """Return mock provider type."""
            return "stock"

        def search(self, request: dict[str, Any]) -> dict[str, Any]:
            """Return deterministic mock provider search result."""
            if not self._should_succeed:
                return {
                    "success": False,
                    "provider": "Pexels",
                    "results": [],
                    "errors": ["mock route failure"],
                    "warnings": [],
                }

            return {
                "success": True,
                "provider": "Pexels",
                "results": [
                    {
                        "asset_id": "provider_asset_001",
                        "asset_type": request["asset_type"],
                        "download_url": "https://example.com/asset.jpg",
                        "height": 1080,
                        "license": "mock",
                        "photographer": "mock",
                        "provider": "Pexels",
                        "provider_type": "stock",
                        "width": 1920,
                        "confidence": 92,
                        "local_path": "",
                        "status": "available",
                        "metadata": {},
                    }
                ],
                "errors": [],
                "warnings": [],
            }

    class MockDownloadManager:
        """Small download manager implementation for self-test."""

        def download_asset(self, asset: dict[str, Any]) -> dict[str, Any]:
            """Return deterministic mock download metadata."""
            return {
                "success": True,
                "local_path": "assets/library/pexels_provider_asset_001.jpg",
                "sha256": "sha256_001",
                "provider": asset.get("provider", ""),
                "asset_id": asset.get("asset_id", ""),
                "errors": [],
                "warnings": [],
            }

    request = {
        "scene_id": "scene_001",
        "asset_id": "asset_001",
        "asset_type": "background",
        "description": "futuristic studio",
    }
    successful_engine = MediaEngine(
        ProviderRouter([MockProvider()]),
        download_manager=MockDownloadManager(),
    )
    failing_engine = MediaEngine(
        ProviderRouter([MockProvider(False)]),
        download_manager=MockDownloadManager(),
    )

    successful = successful_engine.process_request(request)
    failed_validation = successful_engine.process_request({"asset_type": "unknown"})
    failed_routing = failing_engine.process_request(request)
    batch = successful_engine.process_batch((request, request))

    checks = (
        successful["success"] is True,
        failed_validation["success"] is False,
        failed_routing["success"] is False,
        successful_engine._asset_library.asset_exists("asset_001").get("exists")
        is True,
        len(batch) == 2,
    )
    return all(checks)


if __name__ == "__main__":
    print("PASS" if _self_test() else "FAIL")
