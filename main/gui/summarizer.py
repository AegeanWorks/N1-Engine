import html as html_lib
import logging
from datetime import date, datetime, timedelta
from typing import Dict, Optional
from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QPushButton, QFormLayout,
    QDateEdit, QTextEdit, QGroupBox, QHBoxLayout, QComboBox
)
from PyQt6.QtCore import QDate
from main.core.database import SessionLocal
from main.core.models import Intervention, MetricEntry, EventEntry
from main.gui.dialogs import show_error

logger = logging.getLogger(__name__)

class SummarizerWidget(QWidget):
    """Widget for generating a daily/weekly summary."""
    def __init__(self):
        super().__init__()
        self.layout = QVBoxLayout(self)
        self.db_interventions: Dict[int, Intervention] = {} # To cache intervention objects

        # Controls
        self.control_group = QGroupBox("Summary Settings")
        self.form_layout = QFormLayout()

        self.intervention_combo = QComboBox()
        self.intervention_combo.currentIndexChanged.connect(self.on_intervention_changed)

        self.start_date_input = QDateEdit(QDate.currentDate().addDays(-7))
        self.start_date_input.setCalendarPopup(True)
        self.end_date_input = QDateEdit(QDate.currentDate())
        self.end_date_input.setCalendarPopup(True)

        self.run_button = QPushButton("Generate Summary")
        self.run_button.clicked.connect(self.generate_summary)

        self.form_layout.addRow("Scope:", self.intervention_combo)
        self.form_layout.addRow("Start Date:", self.start_date_input)
        self.form_layout.addRow("End Date:", self.end_date_input)
        self.form_layout.addRow(self.run_button)

        self.control_group.setLayout(self.form_layout)
        self.layout.addWidget(self.control_group)

        # Results
        self.results_group = QGroupBox("Summary")
        self.results_layout = QVBoxLayout()
        self.results_text = QTextEdit()
        self.results_text.setReadOnly(True)
        self.results_layout.addWidget(self.results_text)
        self.results_group.setLayout(self.results_layout)
        self.layout.addWidget(self.results_group)

        self.refresh_interventions()

    def refresh_interventions(self):
        """Reloads interventions from the database into the combo box."""
        db = SessionLocal()
        try:
            interventions = db.query(Intervention).order_by(Intervention.start_date.desc()).all()
            
            current_selection = self.intervention_combo.currentData()
            
            self.intervention_combo.clear()
            self.db_interventions.clear()
            
            self.intervention_combo.addItem("-- Manual Date Range --", None)
            
            for i in interventions:
                self.intervention_combo.addItem(f"{i.name} ({i.start_date})", i.id)
                self.db_interventions[i.id] = i

            if current_selection in self.db_interventions:
                self.intervention_combo.setCurrentText(f"{self.db_interventions[current_selection].name} ({self.db_interventions[current_selection].start_date})")

        except Exception as e:
            show_error(self, "Failed to load interventions", str(e))
        finally:
            db.close()

    def on_intervention_changed(self, index: int):
        """Handles selection change in the intervention combo box."""
        intervention_id = self.intervention_combo.currentData()
        
        if intervention_id and intervention_id in self.db_interventions:
            intervention = self.db_interventions[intervention_id]
            self.start_date_input.setDate(QDate(intervention.start_date))
            self.end_date_input.setDate(QDate(intervention.end_date) if intervention.end_date else QDate.currentDate())
            self.start_date_input.setEnabled(False)
            self.end_date_input.setEnabled(False)
        else: # Manual date range
            self.start_date_input.setEnabled(True)
            self.end_date_input.setEnabled(True)

    def generate_summary(self):
        """Queries the database and generates a summary for the selected date range."""
        start_date = self.start_date_input.date().toPyDate()
        end_date = self.end_date_input.date().toPyDate()

        if start_date > end_date:
            show_error(self, "Date Error", "Start date cannot be after end date.")
            return

        intervention_id = self.intervention_combo.currentData()
        intervention_name = self.intervention_combo.currentText() if intervention_id else None

        db = SessionLocal()
        try:
            if intervention_id:
                # Scope summary to a single selected intervention
                interventions = db.query(Intervention).filter(Intervention.id == intervention_id).all()
                metrics = db.query(MetricEntry).filter(MetricEntry.intervention_id == intervention_id).order_by(MetricEntry.date, MetricEntry.metric_name).all()
                events = db.query(EventEntry).filter(EventEntry.intervention_id == intervention_id).order_by(EventEntry.timestamp).all()
            else:
                # Manual date range: show global logs and any interventions active in the period
                interventions = db.query(Intervention).filter(
                    Intervention.start_date <= end_date,
                    (Intervention.end_date == None) | (Intervention.end_date >= start_date)
                ).all()

                # Get metric entries in range
                metrics = db.query(MetricEntry).filter(
                    MetricEntry.date.between(start_date, end_date)
                ).order_by(MetricEntry.date, MetricEntry.metric_name).all()

                # Get events in range
                start_datetime = datetime.combine(start_date, datetime.min.time())
                end_datetime = datetime.combine(end_date, datetime.max.time())
                events = db.query(EventEntry).filter(
                    EventEntry.timestamp.between(start_datetime, end_datetime)
                ).order_by(EventEntry.timestamp).all()

            self.display_summary(interventions, metrics, events, start_date, end_date, intervention_name)

        except Exception as e:
            show_error(self, "Summary Failed", str(e))
        finally:
            db.close()

    def display_summary(self, interventions, metrics, events, start_date, end_date, intervention_name: Optional[str] = None):
        """Formats and displays the summary."""
        today = date.today()
        if intervention_name and intervention_name != "-- Manual Date Range --":
            text = f"<h1>Summary for Intervention: {html_lib.escape(str(intervention_name))}</h1>"
        else:
            text = f"<h1>Summary for {start_date} to {end_date}</h1>"

        # Interventions
        text += "<h3>Intervention Details</h3>" if intervention_name and intervention_name != "-- Manual Date Range --" else "<h3>Interventions in Period</h3>"
        if interventions:
            text += "<ul>"
            for i in interventions:
                if i.end_date and i.end_date <= today:
                    status = f"Ended {i.end_date}"
                elif i.projected_end_date:
                    status = f"Ongoing (Projected end: {i.projected_end_date})"
                else:
                    status = "Ongoing"
                text += (
                    f"<li><b>{html_lib.escape(str(i.name))}</b> "
                    f"(Started: {i.start_date}, Status: {html_lib.escape(str(status))})</li>"
                )
            text += "</ul>"
        else:
            text += "<p>No active interventions in this period.</p>"

        # Metrics
        text += "<h3>Logged Metrics</h3>"
        if metrics:
            text += "<ul>"
            for m in metrics:
                text += (
                    f"<li>{m.date}: <b>{html_lib.escape(str(m.metric_name))}</b> "
                    f"= {m.value}</li>"
                )
            text += "</ul>"
        else:
            text += "<p>No metrics logged in this period.</p>"

        # Events
        text += "<h3>Logged Events</h3>"
        if events:
            text += "<ul>"
            for e in events:
                text += (
                    f"<li>{e.timestamp.strftime('%Y-%m-%d %H:%M')}: "
                    f"<b>{html_lib.escape(str(e.event_name))}</b> "
                    f"(Severity: {e.severity})</li>"
                )
            text += "</ul>"
        else:
            text += "<p>No events logged in this period.</p>"

        self.results_text.setHtml(text)