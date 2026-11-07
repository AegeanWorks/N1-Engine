"""Failing-first regressions found by the cumulative push-window audit.

Each test pins one defect that older windows shipped and that current HEAD
still carries. Run with the project's canonical command:
    python -m pytest tests
"""

from __future__ import annotations

import csv
import json
from datetime import date
from pathlib import Path

import numpy as np
import pandas as pd
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from main.config import MAX_SAFE_METRICS, MIN_DATA_POINTS
from main.core.analysis import AnalysisEngine
from main.core.data_manager import DataManager
from main.core.database import Base
from main.core.models import (
    EventEntry,
    Intervention,
    MetricDefinition,
    MetricEntry,
)
from main.core.reporting import ReportGenerator
from main.core.settings_manager import SettingsManager


def _session():
    engine = create_engine("sqlite:///:memory:")
    Base.metadata.create_all(engine)
    return sessionmaker(bind=engine)()


def test_suite_never_uses_the_live_main_database():
    from main.core.database import engine

    live = (Path(__file__).resolve().parent.parent / "main.db").resolve()
    used = Path(engine.url.database).resolve()
    assert used != live, "the test suite must never open the owner's live main.db"


def test_bootstrap_ci_is_reproducible():
    engine = AnalysisEngine()
    baseline = pd.Series([10.0, 11.0, 9.0, 10.0, 12.0, 10.5])
    intervention = pd.Series([14.0, 15.0, 13.0, 16.0, 14.5, 15.5])

    first = engine.bootstrap_ci(baseline, intervention, n_bootstraps=200)
    second = engine.bootstrap_ci(baseline, intervention, n_bootstraps=200)

    assert first == second
    assert first["lower"] < first["upper"]


def test_calculate_trend_handles_missing_values_with_a_datetime_index():
    engine = AnalysisEngine()
    dates = pd.date_range("2026-01-01", periods=5)
    series = pd.Series([1.0, np.nan, 3.0, 4.0, 5.0], index=dates)

    result = engine.calculate_trend(series)

    assert result["slope"] is not None
    assert result["slope"] > 0


def test_report_escapes_warning_html(tmp_path):
    results = {
        "analysis": {
            "mean_difference": 1.0,
            "cohens_d": 0.5,
            "bootstrap_ci": {"lower": 0.0, "upper": 2.0},
            "t_test": {"statistic": 1.0, "p_value": 0.4},
            "mann_whitney_u": {"statistic": 1.0, "p_value": 0.4},
        },
        "baseline_window": {
            "start": "2026-01-01", "end": "2026-01-03", "count": 3,
            "mean": 1.0, "std": 0.5, "trend": {"slope": 0.0, "p_value": 1.0},
        },
        "intervention_window": {
            "start": "2026-01-04", "end": "2026-01-06", "count": 3,
            "mean": 2.0, "std": 0.5, "trend": {"slope": 0.0, "p_value": 1.0},
        },
        "warnings": ["<script>alert('x')</script>"],
    }
    report = tmp_path / "report.html"

    assert ReportGenerator.generate_html_report(
        results, str(report), "Intervention <b>", "Metric <i>"
    )
    content = report.read_text(encoding="utf-8")

    assert "<script>" not in content
    assert "&lt;script&gt;" in content


def test_settings_reject_wrong_types(tmp_path):
    path = tmp_path / "settings.json"
    path.write_text(
        json.dumps({"min_data_points": "three", "max_safe_metrics": -2}),
        encoding="utf-8",
    )

    manager = SettingsManager(str(path))

    assert manager.get("min_data_points") == MIN_DATA_POINTS
    assert manager.get("max_safe_metrics") == MAX_SAFE_METRICS


def test_settings_refuse_an_unsupported_schema_version(tmp_path):
    path = tmp_path / "settings.json"
    path.write_text(
        json.dumps({"version": 99, "min_data_points": 10}), encoding="utf-8"
    )

    manager = SettingsManager(str(path))

    assert manager.get("min_data_points") == MIN_DATA_POINTS


def test_settings_save_writes_a_schema_version_and_migrates_a_legacy_file(tmp_path):
    path = tmp_path / "settings.json"
    path.write_text(json.dumps({"min_data_points": 5}), encoding="utf-8")
    manager = SettingsManager(str(path))
    assert manager.get("min_data_points") == 5

    assert manager.save_settings() is True

    saved = json.loads(path.read_text(encoding="utf-8"))
    assert saved["version"] == 1


def test_metric_import_clears_unknown_intervention_links(tmp_path):
    session = _session()
    try:
        session.add(Intervention(name="Known", start_date=date(2026, 1, 1)))
        session.commit()
        source = tmp_path / "metrics.csv"
        source.write_text(
            "date,metric_name,value,intervention_id\n"
            "2026-01-02,Sleep,8.0,999\n",
            encoding="utf-8",
        )

        result = DataManager(session).import_from_csv(str(source), "metrics")

        assert result["success"] is True
        assert "unknown intervention link" in result["message"]
        assert session.query(MetricEntry).one().intervention_id is None
    finally:
        session.close()


def test_event_import_clears_unknown_intervention_links(tmp_path):
    session = _session()
    try:
        session.add(Intervention(name="Known", start_date=date(2026, 1, 1)))
        session.commit()
        source = tmp_path / "events.csv"
        source.write_text(
            "timestamp,event_name,severity,intervention_id\n"
            "2026-01-02 10:00:00,Stress,2,999\n",
            encoding="utf-8",
        )

        result = DataManager(session).import_from_csv(str(source), "events")

        assert result["success"] is True
        assert "unknown intervention link" in result["message"]
        assert session.query(EventEntry).one().intervention_id is None
    finally:
        session.close()


def test_metric_definition_csv_roundtrip(tmp_path):
    source = _session()
    target = _session()
    try:
        source.add_all([
            MetricDefinition(name="Energy", description="Daily energy", unit="score"),
            MetricDefinition(name="Sleep", description="Hours slept", unit="hours"),
        ])
        source.commit()
        exported = tmp_path / "definitions.csv"
        assert DataManager(source).export_to_csv(
            str(exported), "metric_definitions"
        )["success"]

        result = DataManager(target).import_from_csv(
            str(exported), "metric_definitions"
        )

        assert result["success"] is True
        rows = target.query(MetricDefinition).order_by(MetricDefinition.name).all()
        assert [row.name for row in rows] == ["Energy", "Sleep"]
        assert rows[1].unit == "hours"
    finally:
        source.close()
        target.close()


def test_metric_definition_import_skips_existing_names(tmp_path):
    session = _session()
    try:
        session.add(MetricDefinition(name="Sleep", unit="hours"))
        session.commit()
        source = tmp_path / "definitions.csv"
        source.write_text(
            "name,description,unit\nSleep,hours slept,hours\nEnergy,daily energy,score\n",
            encoding="utf-8",
        )

        result = DataManager(session).import_from_csv(
            str(source), "metric_definitions"
        )

        assert result["success"] is True
        assert "duplicate" in result["message"]
        assert session.query(MetricDefinition).count() == 2
    finally:
        session.close()


def test_export_orders_metrics_deterministically(tmp_path):
    session = _session()
    try:
        for day, value in ((3, 30.0), (1, 10.0), (2, 20.0)):
            session.add(MetricEntry(
                date=date(2026, 1, day), metric_name="Sleep", value=value
            ))
        session.commit()

        target = tmp_path / "metrics.csv"
        assert DataManager(session).export_to_csv(str(target), "metrics")["success"]

        with target.open(newline="", encoding="utf-8") as handle:
            rows = list(csv.DictReader(handle))
        assert [row["date"] for row in rows] == [
            "2026-01-01", "2026-01-02", "2026-01-03"
        ]
    finally:
        session.close()



