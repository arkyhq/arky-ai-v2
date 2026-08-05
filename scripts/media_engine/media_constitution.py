"""
Immutable constitution for the ARKY Media Engine.

This module contains configuration only. It defines provider priorities,
asset categories, supported formats and resolutions, quality targets, retry
policy, confidence ranges, output schema, naming conventions, and forbidden
behaviors for media acquisition.
"""

from __future__ import annotations

from types import MappingProxyType
from typing import Any


MEDIA_METADATA = MappingProxyType(
    {
        "engine_name": "Media Engine",
        "engine_version": "v0.9",
        "repository_infrastructure": "infra-v1",
        "status": "constitution",
        "purpose": "Acquire approved media assets without changing asset intent.",
    }
)

PROVIDER_PRIORITY = (
    "Local Asset Library",
    "Pexels",
    "Pixabay",
    "Unsplash",
    "Wikimedia Commons",
    "Openverse",
    "Pollinations AI",
    "FLUX",
)

PROVIDER_CONFIGURATION = MappingProxyType(
    {
        "Local Asset Library": MappingProxyType(
            {
                "provider_type": "local",
                "requires_api_key": False,
                "allows_generation": False,
                "allows_download": False,
            }
        ),
        "Pexels": MappingProxyType(
            {
                "provider_type": "official_stock",
                "requires_api_key": True,
                "allows_generation": False,
                "allows_download": True,
            }
        ),
        "Pixabay": MappingProxyType(
            {
                "provider_type": "official_stock",
                "requires_api_key": True,
                "allows_generation": False,
                "allows_download": True,
            }
        ),
        "Unsplash": MappingProxyType(
            {
                "provider_type": "official_stock",
                "requires_api_key": True,
                "allows_generation": False,
                "allows_download": True,
            }
        ),
        "Wikimedia Commons": MappingProxyType(
            {
                "provider_type": "open_repository",
                "requires_api_key": False,
                "allows_generation": False,
                "allows_download": True,
            }
        ),
        "Openverse": MappingProxyType(
            {
                "provider_type": "open_repository",
                "requires_api_key": False,
                "allows_generation": False,
                "allows_download": True,
            }
        ),
        "Pollinations AI": MappingProxyType(
            {
                "provider_type": "free_ai",
                "requires_api_key": False,
                "allows_generation": True,
                "allows_download": True,
            }
        ),
        "FLUX": MappingProxyType(
            {
                "provider_type": "free_ai",
                "requires_api_key": False,
                "allows_generation": True,
                "allows_download": True,
            }
        ),
    }
)

ASSET_CATEGORIES = (
    "background",
    "character",
    "object",
    "prop",
    "icon",
    "logo",
    "poster",
    "illustration",
    "meme",
    "ui",
    "overlay",
)

SUPPORTED_FORMATS = ("PNG", "JPG", "JPEG", "WEBP")

SUPPORTED_RESOLUTIONS = MappingProxyType(
    {
        "vertical_shorts": ((720, 1280), (1080, 1920)),
        "landscape": ((1920, 1080),),
        "square": ((1080, 1080),),
    }
)

ASPECT_RATIOS = MappingProxyType(
    {
        "vertical_shorts": "9:16",
        "landscape": "16:9",
        "square": "1:1",
    }
)

QUALITY_TARGETS = MappingProxyType(
    {
        "minimum_width": 720,
        "minimum_height": 720,
        "preferred_resolution": (1080, 1920),
        "preferred_aspect_ratio": "9:16",
        "maximum_retries": 3,
        "minimum_confidence_score": 70,
    }
)

RETRY_POLICY = MappingProxyType(
    {
        "maximum_retries": 3,
        "retryable_statuses": ("provider_unavailable", "timeout", "rate_limited"),
        "non_retryable_statuses": (
            "unsupported_asset_type",
            "unsupported_file_format",
            "license_rejected",
        ),
    }
)

CONFIDENCE_RANGES = MappingProxyType(
    {
        "local_library": (95, 100),
        "official_stock": (90, 95),
        "free_ai": (75, 90),
        "unknown": (0, 69),
    }
)

OUTPUT_SCHEMA = MappingProxyType(
    {
        "asset_id": str,
        "scene_id": str,
        "asset_type": str,
        "provider": str,
        "source": str,
        "license": str,
        "confidence": int,
        "width": int,
        "height": int,
        "file_format": str,
        "local_path": str,
        "metadata_path": str,
        "status": str,
    }
)

NAMING_CONVENTIONS = MappingProxyType(
    {
        "asset_id": "asset_{scene_id}_{asset_type}_{index}",
        "local_path": "outputs/assets/{asset_id}.{extension}",
        "metadata_path": "outputs/assets/{asset_id}.json",
    }
)

ACQUISITION_RULES = (
    "Prefer providers in constitution priority order.",
    "Prefer reusable local assets before external acquisition.",
    "Store originals separately from derived assets.",
    "Record source, license, and confidence for every asset.",
)

FORBIDDEN_RULES = (
    "Never overwrite assets.",
    "Never modify downloaded originals.",
    "Never generate unsupported asset types.",
    "Never accept unsupported file formats.",
    "Never exceed retry limits.",
    "Never use providers outside the constitution.",
)


def get_media_metadata() -> MappingProxyType[str, str]:
    """Return immutable Media Engine metadata."""
    return MEDIA_METADATA


def get_provider_priority() -> tuple[str, ...]:
    """Return immutable provider priority order."""
    return PROVIDER_PRIORITY


def get_asset_categories() -> tuple[str, ...]:
    """Return immutable supported asset categories."""
    return ASSET_CATEGORIES


def get_supported_formats() -> tuple[str, ...]:
    """Return immutable supported file formats."""
    return SUPPORTED_FORMATS


def get_supported_resolutions() -> MappingProxyType[str, tuple[tuple[int, int], ...]]:
    """Return immutable supported image resolutions by format class."""
    return SUPPORTED_RESOLUTIONS


def get_aspect_ratios() -> MappingProxyType[str, str]:
    """Return immutable supported aspect ratios."""
    return ASPECT_RATIOS


def get_quality_targets() -> MappingProxyType[str, Any]:
    """Return immutable media quality targets."""
    return QUALITY_TARGETS


def get_retry_policy() -> MappingProxyType[str, Any]:
    """Return immutable retry policy."""
    return RETRY_POLICY


def get_confidence_ranges() -> MappingProxyType[str, tuple[int, int]]:
    """Return immutable confidence score ranges."""
    return CONFIDENCE_RANGES


def get_output_schema() -> MappingProxyType[str, type]:
    """Return immutable media asset output schema."""
    return OUTPUT_SCHEMA


def get_forbidden_rules() -> tuple[str, ...]:
    """Return immutable forbidden behaviors."""
    return FORBIDDEN_RULES


def _self_test() -> bool:
    """Verify constitution accessors return populated immutable structures."""
    checks = (
        isinstance(get_media_metadata(), MappingProxyType)
        and bool(get_media_metadata()),
        isinstance(get_provider_priority(), tuple)
        and bool(get_provider_priority()),
        isinstance(get_asset_categories(), tuple)
        and bool(get_asset_categories()),
        isinstance(get_supported_formats(), tuple)
        and bool(get_supported_formats()),
        isinstance(get_supported_resolutions(), MappingProxyType)
        and bool(get_supported_resolutions()),
        isinstance(get_aspect_ratios(), MappingProxyType)
        and bool(get_aspect_ratios()),
        isinstance(get_quality_targets(), MappingProxyType)
        and bool(get_quality_targets()),
        isinstance(get_retry_policy(), MappingProxyType)
        and bool(get_retry_policy()),
        isinstance(get_confidence_ranges(), MappingProxyType)
        and bool(get_confidence_ranges()),
        isinstance(get_output_schema(), MappingProxyType)
        and bool(get_output_schema()),
        isinstance(get_forbidden_rules(), tuple)
        and bool(get_forbidden_rules()),
    )
    return all(checks)


if __name__ == "__main__":
    print("PASS" if _self_test() else "FAIL")
