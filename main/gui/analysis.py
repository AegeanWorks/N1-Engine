import logging
import json
import html
import pandas as pd
from typing import Dict, Any, Optional
from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QPushButton, QFormLayout, QComboBox,
    QSpinBox, QTextEdit, QFileDialog, QGroupBox
)
from sqlalchemy.orm import Session

from main.core.database import SessionLocal
from main.core.models import Intervention, MetricEntry
from main.core.analysis import AnalysisEngine
from main.core.reporting import ReportGenerator
from main.gui.dialogs import show_error, show_info

logger = logging.getLogger(__name__)

class AnalysisWidget(QWidget):
    """Widget for running analysis and displaying results."""
    def __init__(self):
        self.current_intervention_id: Optional[int] = None
        super().__init__()
        self.layout = QVBoxLayout(self)
        self.report_generator = ReportGenerator()

        # Controls
        self.control_group = QGroupBox("Analysis Settings")
        self.form_layout = QFormLayout()
        self.metric_combo = QComboBox()

        self.baseline_days = QSpinBox()
        self.baseline_days.setRange(1, 365)
        self.baseline_days.setValue(14)

        self.intervention_days = QSpinBox()
        self.intervention_days.setRange(1, 365)
        self.intervention_days.setValue(14)

        self.run_button = QPushButton("Run Analysis")
        self.run_button.clicked.connect(self.run_analysis)

        self.form_layout.addRow("Metric:", self.metric_combo)
        self.form_layout.addRow("Baseline Days:", self.baseline_days)
        self.form_layout.addRow("Intervention Days:", self.intervention_days)
        self.form_layout.addRow(self.run_button)

        self.control_group.setLayout(self.form_layout)
        self.layout.addWidget(self.control_group)

        # Results
        self.results_group = QGroupBox("Results")
        self.results_layout = QVBoxLayout()

        self.results_text = QTextEdit()
        self.results_text.setReadOnly(True)
        self.results_layout.addWidget(self.results_text)

        self.save_button = QPushButton("Save Report (JSON)")
        self.save_button.clicked.connect(self.save_report)
        self.save_button.setEnabled(False)
        self.results_layout.addWidget(self.save_button)

        self.export_html_button = QPushButton("Export HTML Report")
        self.export_html_button.clicked.connect(self.export_html_report)
        self.export_html_button.setEnabled(False)
        self.results_layout.addWidget(self.export_html_button)

        self.results_group.setLayout(self.results_layout)
        self.layout.addWidget(self.results_group)

        self.current_results: Optional[Dict[str, Any]] = None

    def set_current_intervention(self, intervention_id: Optional[int]):
        """Sets the active intervention and refreshes metric choices."""
        self.current_intervention_id = intervention_id
        is_enabled = intervention_id is not None

        self.control_group.setEnabled(is_enabled)
        self.results_text.clear()
        self.save_button.setEnabled(False)
        self.export_html_button.setEnabled(False)

        if is_enabled:
            self.refresh_metrics()
        else:
            self.metric_combo.clear()

    def refresh_metrics(self) -> None:
        """Reloads metrics from the database for the current intervention."""
        self.metric_combo.clear()
        if not self.current_intervention_id:
            return

        db = SessionLocal()
        try:
            metrics = db.query(MetricEntry.metric_name).filter(
                MetricEntry.intervention_id == self.current_intervention_id
            ).distinct().all()
            for m in metrics:
                self.metric_combo.addItem(m[0])
        except Exception as e:
            show_error(self, "Failed to load analysis options", str(e))
        finally:
            db.close()

    def run_analysis(self) -> None:
        """Runs the analysis based on selected inputs."""
        intervention_id = self.current_intervention_id
        metric_name = self.metric_combo.currentText()

        if not intervention_id or not metric_name:
             show_error(self, "Input Error", "An intervention and a metric must be selected.")
             return

        b_days = self.baseline_days.value()
        i_days = self.intervention_days.value()

        db = SessionLocal()
        try:
            intervention = db.query(Intervention).get(intervention_id)
            if not intervention:
                show_error(self, "Error", "Intervention not found.")
                return

            # Eager load needed attributes
            start_date_val = intervention.start_date
            intervention_name = intervention.name

            # Fetch metric data for this intervention only
            entries = db.query(MetricEntry).filter(
                MetricEntry.metric_name == metric_name,
                MetricEntry.intervention_id == intervention_id
            ).order_by(MetricEntry.date).all()

            if not entries:
                show_error(self, "Error", "No data found for this metric.")
                return

            df = pd.DataFrame([{
                "date": e.date,
                "value": e.value,
                "metric_name": e.metric_name
            } for e in entries])

            # Ensure date is datetime64[ns]
            df['date'] = pd.to_datetime(df['date'])

            engine = AnalysisEngine()
            start_date = pd.to_datetime(start_date_val)

            results = engine.calculate_baseline_vs_intervention(
                metrics=df,
                start_date=start_date,
                baseline_days=b_days,
                intervention_days=i_days
            )

            self.display_results(results, intervention_name, metric_name)
            self.current_results = results
            self.current_results["intervention"] = intervention_name
            self.current_results["metric"] = metric_name
            self.save_button.setEnabled(True)
            self.export_html_button.setEnabled(True)

        except Exception as e:
            show_error(self, "Analysis Failed", str(e))
        finally:
            db.close()

    def display_results(self, results: Dict[str, Any], intervention_name: str, metric_name: str) -> None:
        """Displays the analysis results in the text area."""
        intervention_name = html.escape(intervention_name)
        metric_name = html.escape(metric_name)

        text = f"<h1>Analysis Report</h1>"
        text += f"<h3>Intervention: {intervention_name}</h3>"
        text += f"<h3>Metric: {metric_name}</h3>"

        if "error" in results:
            text += f"<p style='color:red'><b>Error:</b> {html.escape(str(results['error']))}</p>"
            if "baseline_count" in results:
                 text += f"<p>Baseline Count: {results['baseline_count']}</p>"
                 text += f"<p>Intervention Count: {results['intervention_count']}</p>"
            self.results_text.setHtml(text)
            return

        # Windows
        bw = results.get("baseline_window", {})
        iw = results.get("intervention_window", {})

        text += "<h4>Windows</h4>"
        # Trends
        b_trend = bw.get('trend', {})
        i_trend = iw.get('trend', {})
        b_trend_str = f"Trend: {b_trend.get('slope', 0):.4f} (p={b_trend.get('p_value', 1):.4f})" if b_trend and b_trend.get('slope') is not None else "Trend: N/A"
        i_trend_str = f"Trend: {i_trend.get('slope', 0):.4f} (p={i_trend.get('p_value', 1):.4f})" if i_trend and i_trend.get('slope') is not None else "Trend: N/A"

        text += f"<b>Baseline:</b> {bw.get('start')} to {bw.get('end')} (N={bw.get('count')}, Mean={bw.get('mean'):.2f}, Std={bw.get('std'):.2f})<br>"
        text += f"&nbsp;&nbsp;&nbsp;{b_trend_str}<br>"
        text += f"<b>Intervention:</b> {iw.get('start')} to {iw.get('end')} (N={iw.get('count')}, Mean={iw.get('mean'):.2f}, Std={iw.get('std'):.2f})<br>"
        text += f"&nbsp;&nbsp;&nbsp;{i_trend_str}<br>"

        # Stats
        an = results.get("analysis", {})
        text += "<h4>Statistics</h4>"
        text += f"<b>Mean Difference:</b> {an.get('mean_difference'):.2f}<br>"
        text += f"<b>Cohen's d:</b> {an.get('cohens_d'):.2f}<br>"

        # Bootstrap CI
        ci = an.get("bootstrap_ci", {})
        if ci and ci.get('lower') is not None:
            text += f"<b>Bootstrap 95% CI:</b> [{ci.get('lower', 0):.2f}, {ci.get('upper', 0):.2f}]<br>"
        else:
            text += f"<b>Bootstrap 95% CI:</b> N/A<br>"

        tt = an.get("t_test", {})
        u = an.get("mann_whitney_u", {})

        p_t = tt.get("p_value")
        p_u = u.get("p_value")

        text += f"<b>T-Test p-value:</b> {p_t:.4f} " if p_t is not None else "<b>T-Test:</b> N/A "
        text += f"<b>Mann-Whitney U p-value:</b> {p_u:.4f}<br>" if p_u is not None else "<b>Mann-Whitney U:</b> N/A<br>"

        # Warnings
        warnings = results.get("warnings", [])
        if warnings:
            text += "<h4>Warnings (Scientific Rigor)</h4>"
            text += "<ul>"
            for w in warnings:
                text += f"<li style='color:orange'>{html.escape(str(w))}</li>"
            text += "</ul>"

        self.results_text.setHtml(text)

    def save_report(self) -> None:
        """Saves the current report to a JSON file."""
        if not self.current_results:
            return

        filename, _ = QFileDialog.getSaveFileName(self, "Save Report", "report.json", "JSON Files (*.json)")
        if filename:
            try:
                with open(filename, 'w', encoding='utf-8') as f:
                    json.dump(self.current_results, f, indent=4, default=str)
                show_info(self, f"Report saved to {filename}")
            except Exception as e:
                show_error(self, "Failed to save report", str(e))

    def export_html_report(self) -> None:
        """Exports the current report to an HTML file."""
        if not self.current_results:
            return

        filename, _ = QFileDialog.getSaveFileName(self, "Export HTML Report", "report.html", "HTML Files (*.html)")
        if filename:
            success = self.report_generator.generate_html_report(
                self.current_results,
                filename,
                self.current_results.get("intervention", "Unknown"),
                self.current_results.get("metric", "Unknown")
            )
            if success:
                show_info(self, f"Report exported to {filename}")
            else:
                show_error(self, "Failed to export report", "Check logs for details.")
