# Contributing

## Coding Style

- Follow PEP 8.
- Use type hints for public functions and new helpers.
- Keep functions small and deterministic unless a module is explicitly AI-powered.
- Add concise docstrings that state purpose, arguments, and returns.
- Avoid broad refactors in frozen engines.

## Folder Structure

- `config/`: runtime configuration.
- `docs/`: architecture and release documentation.
- `scripts/`: engine implementations.
- `tests/`: automated tests.
- `demo/`: integration demonstrations.
- `outputs/`: generated engine outputs.

## Naming Conventions

- Constitution files define immutable constants and accessor functions.
- Mapper files convert one structured object into one blueprint.
- Validator files validate one object or a sequence of objects.
- Planner, narrator, transformer, or refiner files are the only allowed AI-powered layers when explicitly approved.
- Engine files orchestrate public APIs and should not duplicate business logic.

## Release Process

1. Implement the smallest approved scope.
2. Run compilation on every Python file.
3. Run deterministic self-tests.
4. Run pytest.
5. Run integration checks.
6. Review architecture boundaries.
7. Freeze the engine only after QA passes.
8. Tag the release.

## QA Requirements

- Imports must succeed.
- Public APIs must remain stable.
- Fallback paths must be tested.
- Validators must reject invalid outputs.
- No engine may crash the full pipeline when one row fails.
- External services must fail gracefully.

## Git Workflow

- Keep commits scoped to one milestone.
- Do not commit secrets or generated cache files.
- Do not rewrite frozen engine behavior without a documented bug.
- Use clear commit messages describing the engine or infrastructure area.

## Architecture Rules

- Deterministic modules must not call Groq or other AI services.
- AI modules must preserve protected facts and schema contracts.
- Orchestrators must call public APIs only.
- Configuration should flow through `config/settings.py`.
- Documentation changes should not imply unimplemented features are available.
