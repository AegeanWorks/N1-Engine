# Codebase Map & Symbol Catalog 🗺️

> **AUTO-GENERATED & VERIFIED BY `scripts/update_knowledge_base.py`**
> This document provides an automated, up-to-date registry of all modules, classes, and exported functions across this repository.

---

## 📊 Codebase Metrics
- **Total Python Modules**: `29`
- **Total Classes**: `22`
- **Total Top-Level Functions**: `49`
- **Total Class Methods**: `72`
- **Total Source Lines**: `3609`

---

## 📦 Modules & Exported Symbols

### [`main/__init__.py`](main/__init__.py)
**Size**: `0` lines (`0` bytes)

---

### [`main/api/__init__.py`](main/api/__init__.py)
**Size**: `0` lines (`0` bytes)

---

### [`main/config.py`](main/config.py)
**Size**: `11` lines (`277` bytes)

---

### [`main/core/__init__.py`](main/core/__init__.py)
**Size**: `0` lines (`0` bytes)

---

### [`main/core/analysis.py`](main/core/analysis.py)
**Size**: `315` lines (`12951` bytes)

**Classes:**
- `class AnalysisEngine` - *Engine for analyzing experiment data.*
  - Method `.calculate_trend(series)` - *Calculates linear trend (slope and p-value) for a time series.*
  - Method `.bootstrap_ci(group1, group2, n_bootstraps, confidence_level, seed)` - *Calculates confidence interval for the difference in means (group2 - group1) using bootstrap resampling.*
  - Method `.correlation_matrix(metrics_df)` - *Calculates correlation matrix for multiple metrics.*
  - Method `.calculate_baseline_vs_intervention(metrics, start_date, baseline_days, intervention_days)` - *Analyzes metric data comparing a baseline period to an intervention period.*
  - Method `.analyze_multiple_metrics(metrics_map, start_date, baseline_days, intervention_days)` - *Analyzes multiple metrics and provides a warning if too many comparisons are made.*

---

### [`main/core/data_manager.py`](main/core/data_manager.py)
**Size**: `299` lines (`13501` bytes)

**Classes:**
- `class DataManager` - *Manages data import and export.*
  - Method `.__init__(db)`
  - Method `._get_session()` - *Yields the existing session or creates a new one.*
  - Method `.import_from_csv(filepath, data_type)` - *Imports data from a CSV file.*
  - Method `.export_to_csv(filepath, data_type)` - *Exports data to a CSV file.*

**Functions:**
- `def _is_missing(value)` - *Return True only when pandas can prove the cell is missing.*
- `def _coerce_int_or_none(value, min_value, max_value)` - *Coerce CSV cells to int or None without raising.*
- `def _clean_str_or_none(value)` - *Return stripped string or None for NaN/empty cells.*
- `def _coerce_link(value, valid_ids)` - *Return (id, cleared) where an unknown foreign key becomes None.*
- `def _import_notes(skipped_bad, cleared_links)`

---

### [`main/core/database.py`](main/core/database.py)
**Size**: `117` lines (`4392` bytes)

**Functions:**
- `def _earliest_legacy_date(connection)` - *Return the earliest date among rows that need the legacy placeholder.*
- `def _backfill_legacy_rows(connection)` - *Attach rows logged before interventions were linked to a visible placeholder.*
- `def ensure_schema(target_engine)` - *Create missing tables and add columns introduced after the first release.*
- `def get_db()`

---

### [`main/core/models.py`](main/core/models.py)
**Size**: `63` lines (`2521` bytes)

**Classes:**
- `class Intervention`
  - Method `.__repr__()`
- `class MetricDefinition`
  - Method `.__repr__()`
- `class MetricEntry`
  - Method `.__repr__()`
- `class EventEntry`
  - Method `.__repr__()`

---

### [`main/core/reporting.py`](main/core/reporting.py)
**Size**: `144` lines (`5670` bytes)

**Classes:**
- `class ReportGenerator` - *Generates HTML reports from analysis results.*
  - Method `.generate_html_report(results, filepath, intervention_name, metric_name)` - *Generates an HTML report and saves it to the specified filepath.*

---

### [`main/core/settings_manager.py`](main/core/settings_manager.py)
**Size**: `117` lines (`4423` bytes)

**Classes:**
- `class SettingsManager`
  - Method `.__init__(settings_file)`
  - Method `._validated(raw)` - *Keep known keys whose values are positive integers; else default.*
  - Method `.load_settings()`
  - Method `.save_settings()`
  - Method `.get(key, default)`
  - Method `.set(key, value)`

---

### [`main/gui/__init__.py`](main/gui/__init__.py)
**Size**: `0` lines (`0` bytes)

---

### [`main/gui/analysis.py`](main/gui/analysis.py)
**Size**: `268` lines (`10605` bytes)

**Classes:**
- `class AnalysisWidget` - *Widget for running analysis and displaying results.*
  - Method `.__init__()`
  - Method `.set_current_intervention(intervention_id)` - *Sets the active intervention and refreshes metric choices.*
  - Method `.refresh_metrics()` - *Reloads metrics from the database for the current intervention.*
  - Method `.run_analysis()` - *Runs the analysis based on selected inputs.*
  - Method `.display_results(results, intervention_name, metric_name)` - *Displays the analysis results in the text area.*
  - Method `.save_report()` - *Saves the current report to a JSON file.*
  - Method `.export_html_report()` - *Exports the current report to an HTML file.*

---

### [`main/gui/data_management.py`](main/gui/data_management.py)
**Size**: `73` lines (`3173` bytes)

**Classes:**
- `class DataManagementWidget` - *Widget for importing and exporting data.*
  - Method `.__init__()`
  - Method `.import_data(data_type)`
  - Method `.export_data(data_type)`

---

### [`main/gui/dialogs.py`](main/gui/dialogs.py)
**Size**: `56` lines (`1544` bytes)

**Functions:**
- `def show_error(parent, message, details)` - *Shows an error message box.*
- `def show_warning(parent, message, details)` - *Shows a warning message box.*
- `def show_info(parent, message)` - *Shows an info message box.*

---

### [`main/gui/events.py`](main/gui/events.py)
**Size**: `108` lines (`3706` bytes)

**Classes:**
- `class EventsWidget` - *Widget for logging events.*
  - Method `.__init__()`
  - Method `.set_current_intervention(intervention_id)` - *Sets the currently active intervention for logging.*
  - Method `.log_event()` - *Logs a new event to the database.*

---

### [`main/gui/interventions.py`](main/gui/interventions.py)
**Size**: `350` lines (`15291` bytes)

**Classes:**
- `class DateTableWidgetItem` - *Custom QTableWidgetItem for sorting dates, including None values.*
  - Method `.__lt__(other)`
- `class InterventionDialog` - *Dialog for adding or editing an intervention.*
  - Method `.__init__(parent, intervention_data)`
  - Method `.get_data()` - *Returns the data entered in the dialog.*
- `class InterventionsWidget`
  - Method `.__init__()`
  - Method `.on_selection_changed()` - *Emits the ID of the currently selected intervention.*
  - Method `.get_selected_intervention_id()` - *Helper to get the ID of the selected row.*
  - Method `.refresh_table()` - *Refreshes the interventions table from the database.*
  - Method `.add_intervention()` - *Opens the dialog to add a new intervention.*
  - Method `.edit_selected_intervention()` - *Opens dialog to edit the selected intervention.*
  - Method `.close_selected_intervention()` - *Sets the end date of the selected intervention to today.*
  - Method `.show_context_menu(pos)` - *Shows context menu for table items.*

---

### [`main/gui/main_window.py`](main/gui/main_window.py)
**Size**: `111` lines (`4454` bytes)

**Classes:**
- `class WorkspaceWidget` - *A widget that encapsulates the main experiment workflow.*
  - Method `.__init__()`
  - Method `.on_intervention_selected(intervention_id)` - *Propagates the selected intervention to child tabs.*
  - Method `.refresh_workspace()` - *Refreshes the data in the workspace view.*
- `class MainWindow` - *The main application window.*
  - Method `.__init__()`
  - Method `.on_tab_change(index)` - *Handles tab change events to refresh data in the selected tab.*

---

### [`main/gui/metrics.py`](main/gui/metrics.py)
**Size**: `362` lines (`14067` bytes)

**Classes:**
- `class LoggingWidget` - *Widget for logging metrics.*
  - Method `.__init__()`
  - Method `.set_current_intervention(intervention_id)` - *Sets the currently active intervention for logging and viewing.*
  - Method `.refresh_combos()` - *Loads dropdown contents from the database.*
  - Method `.log_metric()` - *Logs a new metric entry to the database.*
  - Method `.update_plot()` - *Updates the time-series plot for the selected metric.*
- `class MetricDefinitionDialog` - *Dialog for adding or editing a metric definition.*
  - Method `.__init__(parent, metric_data)`
  - Method `.get_data()`
- `class MetricDefinitionWidget` - *Widget for defining and managing metrics.*
  - Method `.__init__()`
  - Method `.refresh_table()`
  - Method `.add_metric()`
  - Method `.edit_metric()`
  - Method `.delete_metric()`

---

### [`main/gui/settings.py`](main/gui/settings.py)
**Size**: `65` lines (`2888` bytes)

**Classes:**
- `class SettingsWidget` - *Widget for managing application settings.*
  - Method `.__init__()`
  - Method `.load_settings()` - *Loads settings from the manager and updates the UI.*
  - Method `.save_settings()` - *Saves settings from the UI to the manager and file.*

---

### [`main/gui/summarizer.py`](main/gui/summarizer.py)
**Size**: `195` lines (`8536` bytes)

**Classes:**
- `class SummarizerWidget` - *Widget for generating a daily/weekly summary.*
  - Method `.__init__()`
  - Method `.refresh_interventions()` - *Reloads interventions from the database into the combo box.*
  - Method `.on_intervention_changed(index)` - *Handles selection change in the intervention combo box.*
  - Method `.generate_summary()` - *Queries the database and generates a summary for the selected date range.*
  - Method `.display_summary(interventions, metrics, events, start_date, end_date, intervention_name)` - *Formats and displays the summary.*

---

### [`main/utils/__init__.py`](main/utils/__init__.py)
**Size**: `0` lines (`0` bytes)

---

### [`run_gui.py`](run_gui.py)
**Size**: `20` lines (`396` bytes)

**Functions:**
- `def main()`

---

### [`tests/conftest.py`](tests/conftest.py)
> *Test isolation: never open the owner's live database.*

**Size**: `24` lines (`742` bytes)

**Functions:**
- `def pytest_sessionfinish(session, exitstatus)`

---

### [`tests/test_audit_regressions.py`](tests/test_audit_regressions.py)
> *Failing-first regressions found by the cumulative push-window audit.*

**Size**: `195` lines (`6336` bytes)

**Functions:**
- `def _session()`
- `def test_suite_never_uses_the_live_main_database()`
- `def test_bootstrap_ci_is_reproducible()`
- `def test_calculate_trend_handles_missing_values_with_a_datetime_index()`
- `def test_report_escapes_warning_html(tmp_path)`
- `def test_settings_reject_wrong_types(tmp_path)`
- `def test_settings_refuse_an_unsupported_schema_version(tmp_path)`
- `def test_settings_save_writes_a_schema_version_and_migrates_a_legacy_file(tmp_path)`
- `def test_metric_import_clears_unknown_intervention_links(tmp_path)`
- `def test_event_import_clears_unknown_intervention_links(tmp_path)`
- `def test_export_orders_metrics_deterministically(tmp_path)`

---

### [`tests/test_gui_escaping.py`](tests/test_gui_escaping.py)
> *UI regression: analysis warnings must render as text, never as markup.*

**Size**: `40` lines (`1224` bytes)

**Functions:**
- `def qapp()`
- `def test_display_warnings_are_escaped(qapp)`

---

### [`tests/test_gui_logic.py`](tests/test_gui_logic.py)
**Size**: `69` lines (`2276` bytes)

**Classes:**
- `class TestAnalysisWidgetLogic`
  - Method `.setUp()`
  - Method `.test_display_results_formatting()`
  - Method `.test_display_error()`

---

### [`tests/test_new_features.py`](tests/test_new_features.py)
**Size**: `110` lines (`3489` bytes)

**Functions:**
- `def db_session()`
- `def test_calculate_trend()`
- `def test_bootstrap_ci()`
- `def test_data_manager_import_export(db_session, tmp_path)`
- `def test_report_generator(tmp_path)`

---

### [`tests/test_phase1.py`](tests/test_phase1.py)
**Size**: `270` lines (`8950` bytes)

**Functions:**
- `def test_database_setup()`
- `def test_analysis_engine()`
- `def test_insufficient_duration_warning()`
- `def test_mixed_metrics_error()`
- `def test_zero_variance()`
- `def test_multiple_comparison_warning()`
- `def test_window_duration_exactness()`

---

### [`tests/test_schema_migration.py`](tests/test_schema_migration.py)
**Size**: `227` lines (`8228` bytes)

**Functions:**
- `def _old_database(path)`
- `def test_ensure_schema_upgrades_an_old_sqlite_database(tmp_path)`
- `def test_ensure_schema_creates_lookup_indexes_on_an_old_database(tmp_path)`
- `def test_legacy_placeholder_starts_at_the_earliest_legacy_row(tmp_path)`
- `def test_csv_import_preserves_intervention_links(tmp_path)`
- `def test_save_settings_reports_failure(tmp_path)`
- `def test_csv_import_coerces_bad_numeric_value_cells(tmp_path)`
- `def test_csv_import_skips_bad_date_rows(tmp_path)`
- `def test_csv_import_coerces_out_of_range_severity(tmp_path)`
- `def test_csv_import_rejects_all_bad_file(tmp_path)`

---
