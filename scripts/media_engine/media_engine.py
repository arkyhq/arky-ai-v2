"""
Media Engine orchestration for the ARKY Media Acquisition pipeline.

This module coordinates public module APIs only. It performs no provider logic,
validation logic, AI work, downloading, networking, filesystem operations,
asset searching, prompt generation, or routing decisions.
"""

from __future__ import annotations

from typing import Any, Iterable

try:
    from asset_library import AssetLibrary
    from media_mapper import map_media_request
    from media_output_validator import validate_media_output
    from media_validator import validate_media_request
    from provider_router import ProviderRouter
except ModuleNotFoundError:
    from scripts.media_engine.asset_library import AssetLibrary
    from scripts.media_engine.media_mapper import map_media_request
    from scripts.media_engine.media_output_validator import validate_media_output
    from scripts.media_engine.media_validator import validate_media_request
    from scripts.media_engine.provider_router import ProviderRouter


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
    ) -> None:
        """Initialize Media Engine with injectable router and asset library."""
        self._router = router if router is not None else ProviderRouter()
        self._asset_library = (
            asset_library if asset_library is not None else AssetLibrary()
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

            routed = self._router.route(media_request)
            if routed.get("success") is not True:
                return _pipeline_result(
                    success=False,
                    status="routing_failed",
                    asset={},
                    errors=routed.get("errors"),
                    warnings=routed.get("warnings"),
                )

            acquisition_output = _acquisition_output(routed)
            output_validation = validate_media_output(acquisition_output)
            if not output_validation.get("valid"):
                return _pipeline_result(
                    success=False,
                    status="output_validation_failed",
                    asset=acquisition_output.get("asset"),
                    errors=output_validation.get("errors"),
                    warnings=output_validation.get("warnings"),
                )

            registration = self._asset_library.register_asset(
                acquisition_output["asset"]
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
                    *_as_tuple(output_validation.get("warnings")),
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


def _acquisition_output(routed: dict[str, Any]) -> dict[str, Any]:
    """Build the output package for public output validation."""
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

        def acquire(self, request: dict[str, Any]) -> dict[str, Any]:
            """Return deterministic mock provider acquisition result."""
            if not self._should_succeed:
                return {
                    "success": False,
                    "asset": {},
                    "errors": ["mock route failure"],
                    "warnings": [],
                }

            return {
                "success": True,
                "asset": {
                    "asset_id": request["asset_id"],
                    "asset_type": request["asset_type"],
                    "provider": "Pexels",
                    "provider_type": "stock",
                    "confidence": 92,
                    "local_path": "",
                    "status": "available",
                    "metadata": {},
                },
                "errors": [],
                "warnings": [],
            }

    request = {
        "scene_id": "scene_001",
        "asset_id": "asset_001",
        "asset_type": "background",
        "description": "futuristic studio",
    }
    successful_engine = MediaEngine(ProviderRouter([MockProvider()]))
    failing_engine = MediaEngine(ProviderRouter([MockProvider(False)]))

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
