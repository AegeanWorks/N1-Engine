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

### ADR-005: Coerce bad numeric CSV value cells instead of failing the import
- **Date**: 2026-11-03
- **Status**: Accepted
- **Context**: `DataManager.import_from_csv(metrics)` passed `row['value']` straight to SQLAlchemy. One `bad-number` cell raised `ValueError: could not convert string to float` and aborted the whole file (0 rows). Wave audit (oldest-first 0,10,20,30; `38705f7` import path) reproduced: 2-row CSV with 1 bad cell returned `success False`. Prior `43605f9` had coerced only `intervention_id`/`severity`.
- **Decision**: `pd.to_numeric(errors='coerce')` on `value`, drop NaN rows, import the valid rows; success message appends `(skipped N bad value row(s))`; all-bad returns `success False` with `No valid metric entries (skipped N ...)`.
- **Consequences**: single-cell faults no longer wipe valid rows; contract adds the parenthesised skip note only when `N>0`; 17/17 pytest passes including `test_csv_import_coerces_bad_numeric_value_cells`.

### ADR-006: Harden CSV import tolerance (dates, severity range, blank names)
- **Date**: 2026-11-05
- **Status**: Accepted
- **Context**: post-push audit of `565f28c`/`43605f9` reproduced two whole-file failures: one `not-a-date` aborted metrics import (`Unknown datetime string format`), and one `severity=99` aborted events import (`CHECK constraint failed: check_severity_range`, 0 rows). README clone URL pointed at `Aegean-E`, `.gitignore` had triple duplicate transient-state comments, and `import_from_csv` double-committed on caller-passed sessions.
- **Decision**: `errors='coerce'` + `format='mixed'` on all date/timestamp parses with per-row skip counting; `_coerce_int_or_none` with integer-check and `severity 1-5` range (out-of-range becomes `None`); drop blank `metric_name`/`event_name`/`name`; `_clean_str_or_none` for optional strings; single `session.commit()`; unify skip note to `(skipped N bad row(s))`; fix clone URL to `AegeanWorks`; dedup `.gitignore`.
- **Consequences**: single bad date/severity/name no longer wipes valid rows; severity faults degrade to `NULL` instead of `IntegrityError`; contract message wording changes from `bad value row(s)` to `bad row(s)`; 20/20 pytest passes including bad-date, out-of-range severity, and all-bad tests.

### ADR-007: Push-Window Audit 1-3 Through 1-12; Tests Stop Touching the Live Database
- **Date**: 2026-11-07
- **Status**: Accepted
- **Context**: The cumulative push review checked windows 1->3, 1->6, 1->9 and 1->12 by running each window's own suite in a throwaway worktree. Eighteen of nineteen windows were green; window 1->12 (`eb957a2`, "Moved files to main folder") was pushed red because the package moved from `pee/` to `main/` while all three test modules still imported `pee`, so collection failed with `ModuleNotFoundError`; `0d1cc20` repaired it in the next push. Reviewing the current HEAD against that foundation found five still-live defects. (1) `tests/test_phase1.py` opened the production `sqlite:///./main.db` and inserted the `Magnesium Supplement` fixture into the owner's real database (the tracked-ignored `main.db` still holds that row). (2) `AnalysisEngine.bootstrap_ci` seeded `default_rng()` from entropy, so the same data produced different confidence intervals on every run, contradicting the README's reproducibility promise. (3) `calculate_trend` dropped missing values from `y` but kept the full datetime index in `x`, so any NaN made the regression raise and silently return `None`. (4) `ReportGenerator` and the GUI inserted warnings and error text into HTML unescaped. (5) CSV export used no ordering, so equal exports could reorder rows.
- **Decision**: Add `tests/conftest.py`, which points `N1_DATABASE_URL` at a session-scoped temp directory before any `main` import and removes it at session end; `bootstrap_ci(..., seed=42)` now seeds `default_rng` and accepts another seed deliberately; `calculate_trend` drops missing values before building both regression vectors; warnings are HTML-escaped in the generated report (the GUI equivalent is ADR-008); exports order metrics by date/id, interventions by start date/id and events by timestamp/id. Five failing-first tests live in `tests/test_audit_regressions.py`.
- **Consequences**: `python -m pytest tests` no longer opens or mutates `main.db`; 25/25 tests pass at this commit; the same dataset now yields one bootstrap interval; trend works with gaps; user-entered names cannot inject markup into a report; exports are stable. Historical red push 1->12 is recorded, not rewritten. The existing `Magnesium Supplement` row is left in place because it may be the owner's data.

### ADR-008: Analysis Warnings Render as Text in the GUI
- **Date**: 2026-11-07
- **Status**: Accepted
- **Context**: ADR-007 escaped warnings in the exported HTML report, but `AnalysisWidget.display_results` still inserted `results["warnings"]` and `results["error"]` into `QTextEdit.setHtml` verbatim. A warning or error containing `<b>` rendered as formatting, and a crafted metric name could inject links or hidden text into the analysis pane.
- **Decision**: Escape both values with `html.escape` before interpolation. The change is confined to `main/gui/analysis.py` and was made under a bounded UI task on surface `app` opened from `037b73f`, verified and closed with reviewer `opencode:n1-audit`; `.aikit/ui_history.json` records it. The regression test lives in `tests/test_gui_escaping.py` and lands in the following commit because the UI contract protects `tests/**`.
- **Consequences**: Warnings and error text display literally in the analysis pane; 26/26 tests pass once the protected test commit lands.
