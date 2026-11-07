"""UI regression: summary user names must render as text, never as markup."""

from __future__ import annotations

from datetime import date, datetime
from types import SimpleNamespace

import pytest
from PyQt6.QtWidgets import QApplication


@pytest.fixture(scope="session")
def qapp():
    app = QApplication.instance() or QApplication([])
    return app


def test_summary_escapes_user_entered_names(qapp):
    from main.core.database import ensure_schema
    from main.gui.summarizer import SummarizerWidget

    ensure_schema()
    widget = SummarizerWidget()
    intervention = SimpleNamespace(
        name="<b>Experiment</b>",
        start_date=date(2026, 1, 1),
        projected_end_date=None,
        end_date=None,
    )
    metric = SimpleNamespace(
        date=date(2026, 1, 2), metric_name="<i>Sleep</i>", value=8.0
    )
    event = SimpleNamespace(
        timestamp=datetime(2026, 1, 2, 10, 0),
        event_name="<script>Stress</script>",
        severity=2,
    )

    widget.display_summary(
        [intervention], [metric], [event],
        date(2026, 1, 1), date(2026, 1, 3), "<u>Scope</u>",
    )

    text = widget.results_text.toPlainText()
    assert "<b>Experiment</b>" in text
    assert "<i>Sleep</i>" in text
    assert "<script>Stress</script>" in text
    assert "<u>Scope</u>" in text
