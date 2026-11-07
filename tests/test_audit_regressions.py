"""Failing-first regressions found by the cumulative push-window audit.

Each test pins one defect that older windows shipped and that current HEAD
still carries. Run with the project's canonical command:
    python -m pytest tests
"""

from __future__ import annotations

import csv
from datetime import date
from pathlib import Path

import numpy as np
import pandas as pd
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from main.core.analysis import AnalysisEngine
from main.core.data_manager import DataManager
from main.core.database import Base
from main.core.models import MetricEntry
from main.core.reporting import ReportGenerator


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



