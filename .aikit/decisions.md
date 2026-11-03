# Decisions

Why this project is built the way it is, oldest first. One entry per decision that changes a
contract, a dependency, a data format or the architecture; IDs are consecutive and never reused.

### ADR-001: Adopt pytest as the canonical test command
- **Date**: 2026-10-21
- **Status**: Accepted
- **Context**: auto-detection picked `python -m unittest discover`, which discovers zero tests: `tests/` has no `__init__.py` and two of three test modules are pytest-style.
- **Decision**: `.aikit/project.json` `test_command` is set to `python -m pytest tests`; 13/13 tests pass.
- **Consequences**: every future gate run exercises the real suite; pytest stays a development dependency of the project.

### ADR-002: Rename main/gui/utils.py to main/gui/dialogs.py
- **Date**: 2026-10-21
- **Status**: Accepted
- **Context**: the AIKit structure gate flags `utils` as a junk-drawer name; the module holds exactly one role: QMessageBox helpers (show_error, show_warning, show_info).
- **Decision**: renamed the module and updated all 7 import sites; behavior unchanged, 13/13 tests pass.
- **Consequences**: import path `main.gui.utils` no longer exists; `main/utils/` and `main/api/` remain as documented empty reserved packages.

## Licensing migration (apache-final)

- New versions use the Aegean License 1.1 (AL-1.1); versions up to and including `apache-final` remain under the Apache License 2.0.
- Rights holder: AegeanWorks; commercial use under ACL-1.0.
- Counsel review of the 1.1 texts remains pending.

## License notice cleanup (2026-10-26)

- The license-history notes and the old-license boundary tag were removed: the project is offered only under the Aegean License 1.1 (AL-1.1), with commercial use under ACL-1.0.

### ADR-003: Upgrade older SQLite databases in place
- **Date**: 2026-10-29
- **Status**: Accepted
- **Context**: the workspace and settings release added `interventions.projected_end_date` and `metrics/events.intervention_id`; `create_all` does not alter an existing `main.db`, so upgrades would fail or hide legacy rows.
- **Decision**: `main.core.database.ensure_schema()` runs `create_all`, adds missing SQLite columns/indexes idempotently, and backfills rows with a `NULL` `intervention_id` into a visible `Legacy (unassigned)` intervention. CSV import/export also preserves `intervention_id` and `projected_end_date`.
- **Consequences**: existing databases open without manual deletion and legacy rows stay reachable; the placeholder intervention can be renamed or merged later; 16/16 tests pass.

### ADR-004: Blank-database keeper; live owner data never framed
- **Date**: 2026-11-03
- **Status**: Accepted
- **Context**: The app opens the owner's live `main.db`; a first capture framed a real health row and was deleted before wiring. No registered screenshots existed.
- **Decision**: Register `2026-11-03-main.png` (`python run_gui.py` with `N1_DATABASE_URL` pointed at a TEMP blank database, PrintWindow on `N1-Engine`, 1016x839, commit `6f6a75e`) in `.aikit/media.json` and the README `aegean:screenshots` block. The empty workspace is the honest fresh-user state.
- **Consequences**: README proves the current app without exposing personal data. Reproduce with the env override plus PrintWindow helper above.
