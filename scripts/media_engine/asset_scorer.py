"""Reusable scoring for normalized media asset candidates."""

from __future__ import annotations

from typing import Any


class AssetScorer:
    """Rank normalized media candidates and select the best asset."""

    WEIGHTS = {
        "resolution": 35,
        "aspect_ratio": 20,
        "metadata": 15,
        "provider": 10,
        "license": 10,
        "asset_type": 10,
    }
    PROVIDER_PRIORITY = {
        "pexels": 10,
        "pixabay": 8,
        "unsplash": 6,
        "openverse": 4,
        "pollinations": 2,
        "flux": 1,
    }
    REQUIRED_METADATA_FIELDS = (
        "asset_id",
        "provider",
        "photographer",
        "width",
        "height",
        "preview_url",
        "download_url",
        "license",
    )
    MIN_USEFUL_PIXELS = 1_000_000
    FULL_SCORE_PIXELS = 2_073_600

    def score_candidates(self, candidates: list[dict]) -> dict:
        """
        Score normalized media candidates and return the highest ranked asset.

        Arguments:
            candidates: normalized asset dictionaries to score.

        Returns:
            Structured scoring result with best asset and score breakdowns.
        """
        errors: list[str] = []
        warnings: list[str] = []

        try:
            if not isinstance(candidates, list):
                errors.append("candidates must be a list")
                return _result(False, {}, [], errors, warnings)

            if not candidates:
                errors.append("candidates must not be empty")
                return _result(False, {}, [], errors, warnings)

            scored_candidates = [
                self._score_candidate(candidate)
                for candidate in candidates
                if isinstance(candidate, dict)
            ]

            if not scored_candidates:
                errors.append("candidates must contain dictionaries")
                return _result(False, {}, [], errors, warnings)

            best_index = max(
                range(len(scored_candidates)),
                key=lambda index: scored_candidates[index]["score"],
            )
            best_asset = dict(candidates[best_index])

            return _result(
                True,
                best_asset,
                scored_candidates,
                errors,
                warnings,
            )
        except Exception as exc:
            errors.append(f"unexpected asset scoring error: {exc}")
            return _result(False, {}, [], errors, warnings)

    def _score_candidate(self, candidate: dict[str, Any]) -> dict[str, Any]:
        """Return score details for one normalized asset candidate."""
        breakdown = {
            "resolution": self._score_resolution(candidate),
            "aspect_ratio": self._score_aspect_ratio(candidate),
            "metadata": self._score_metadata(candidate),
            "provider": self._score_provider(candidate),
            "license": self._score_license(candidate),
            "asset_type": self._score_asset_type(candidate),
        }
        score = min(100, sum(breakdown.values()))

        return {
            "provider": _safe_text(candidate.get("provider")),
            "score": score,
            "breakdown": breakdown,
        }

    def _score_resolution(self, candidate: dict[str, Any]) -> int:
        """Score candidate resolution quality."""
        width = _safe_int(candidate.get("width"))
        height = _safe_int(candidate.get("height"))
        pixels = width * height

        if pixels >= self.FULL_SCORE_PIXELS:
            return self.WEIGHTS["resolution"]
        if pixels >= self.MIN_USEFUL_PIXELS:
            return 25
        if pixels > 0:
            return 10
        return 0

    def _score_aspect_ratio(self, candidate: dict[str, Any]) -> int:
        """Score whether dimensions provide a usable aspect ratio."""
        width = _safe_int(candidate.get("width"))
        height = _safe_int(candidate.get("height"))

        if width <= 0 or height <= 0:
            return 0
        if width == height:
            return 16
        return self.WEIGHTS["aspect_ratio"]

    def _score_metadata(self, candidate: dict[str, Any]) -> int:
        """Score normalized metadata completeness."""
        populated = sum(
            1
            for field in self.REQUIRED_METADATA_FIELDS
            if _has_value(candidate.get(field))
        )
        completeness = populated / len(self.REQUIRED_METADATA_FIELDS)
        return round(self.WEIGHTS["metadata"] * completeness)

    def _score_provider(self, candidate: dict[str, Any]) -> int:
        """Score provider priority."""
        provider = _safe_text(candidate.get("provider")).casefold()
        return self.PROVIDER_PRIORITY.get(provider, 0)

    def _score_license(self, candidate: dict[str, Any]) -> int:
        """Score license metadata availability."""
        if _has_value(candidate.get("license")):
            return self.WEIGHTS["license"]
        return 0

    def _score_asset_type(self, candidate: dict[str, Any]) -> int:
        """Score asset type availability."""
        if _has_value(candidate.get("asset_type")):
            return self.WEIGHTS["asset_type"]
        return 0


def _result(
    success: bool,
    best_asset: dict[str, Any],
    candidates: list[dict[str, Any]],
    errors: list[str],
    warnings: list[str],
) -> dict[str, Any]:
    """Build a structured asset scoring result."""
    return {
        "success": success,
        "best_asset": dict(best_asset),
        "candidates": candidates,
        "errors": list(errors),
        "warnings": list(warnings),
    }


def _has_value(value: Any) -> bool:
    """Return whether a normalized field is populated."""
    if value is None:
        return False
    if isinstance(value, str):
        return bool(value.strip())
    return True


def _safe_int(value: Any) -> int:
    """Return a non-negative integer when possible."""
    try:
        number = int(value)
    except (TypeError, ValueError):
        return 0
    return max(0, number)


def _safe_text(value: Any) -> str:
    """Return stripped text for scalar values."""
    if value is None:
        return ""
    return str(value).strip()
