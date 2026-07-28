# QA Checklist

## Compilation

- Compile every Python file.
- Confirm no syntax errors.

## Imports

- Import every production module required by the current release.
- Confirm no circular import failures.

## Public API

- Compare expected public APIs against module `__all__` or approved callable names.
- Confirm no public API removals.

## Integration

- Run available end-to-end deterministic paths.
- Confirm every stage passes data to the next stage.

## Pipeline

- Verify row-level failure isolation.
- Verify output schemas.
- Verify generated JSON where file outputs exist.

## Fallback

- Simulate unavailable AI services.
- Simulate malformed AI responses.
- Confirm deterministic fallback succeeds where designed.

## Architecture

- Confirm only approved modules call AI services.
- Confirm validators do not perform generation.
- Confirm mappers do not perform validation or file I/O.

## Performance

- Record processed count.
- Record success rate.
- Record execution time for integration tests.

## QA

- Inspect representative outputs.
- Confirm no prompt leakage, markdown leakage, unsupported facts, or schema drift.

## Freeze

- Confirm Compilation, Imports, Public API, Integration, Fallback, and Architecture all pass.

## Git Tag

- Tag only after QA passes and the release decision is `READY`.
