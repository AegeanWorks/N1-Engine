"""UI regression: analysis warnings must render as text, never as markup."""

from __future__ import annotations

import pytest
from PyQt6.QtWidgets import QApplication


@pytest.fixture(scope="session")
def qapp():
    app = QApplication.instance() or QApplication([])
    return app


def test_display_warnings_are_escaped(qapp):
    from main.gui.analysis import AnalysisWidget

    widget = AnalysisWidget()
    results = {
        "baseline_window": {
            "start": "2026-01-01", "end": "2026-01-03", "count": 3,
            "mean": 1.0, "std": 0.5, "trend": {"slope": 0.0, "p_value": 1.0},
        },
        "intervention_window": {
            "start": "2026-01-04", "end": "2026-01-06", "count": 3,
            "mean": 2.0, "std": 0.5, "trend": {"slope": 0.0, "p_value": 1.0},
        },
        "analysis": {
            "mean_difference": 1.0,
            "cohens_d": 0.5,
            "bootstrap_ci": {"lower": 0.0, "upper": 2.0},
            "t_test": {"p_value": 0.4},
            "mann_whitney_u": {"p_value": 0.4},
        },
        "warnings": ["<b>bold warning</b>"],
    }

    widget.display_results(results, "Test", "Sleep")

    assert "<b>bold warning</b>" in widget.results_text.toPlainText()
