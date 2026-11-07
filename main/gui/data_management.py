import logging
from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QPushButton, QFileDialog, QGroupBox, QLabel
)
from main.core.data_manager import DataManager
from main.gui.dialogs import show_error, show_info

logger = logging.getLogger(__name__)

class DataManagementWidget(QWidget):
    """Widget for importing and exporting data."""
    def __init__(self):
        super().__init__()
        self.layout = QVBoxLayout(self)
        self.data_manager = DataManager()

        # Import Section
        self.import_group = QGroupBox("Import Data (CSV)")
        self.import_layout = QVBoxLayout()

        self.btn_import_metrics = QPushButton("Import Metrics")
        self.btn_import_metrics.clicked.connect(lambda: self.import_data('metrics'))
        self.import_layout.addWidget(self.btn_import_metrics)

        self.btn_import_interventions = QPushButton("Import Interventions")
        self.btn_import_interventions.clicked.connect(lambda: self.import_data('interventions'))
        self.import_layout.addWidget(self.btn_import_interventions)

        self.btn_import_events = QPushButton("Import Events")
        self.btn_import_events.clicked.connect(lambda: self.import_data('events'))
        self.import_layout.addWidget(self.btn_import_events)

        self.btn_import_definitions = QPushButton("Import Metric Definitions")
        self.btn_import_definitions.clicked.connect(lambda: self.import_data('metric_definitions'))
        self.import_layout.addWidget(self.btn_import_definitions)

        self.import_group.setLayout(self.import_layout)
        self.layout.addWidget(self.import_group)

        # Export Section
        self.export_group = QGroupBox("Export Data (CSV)")
        self.export_layout = QVBoxLayout()

        self.btn_export_metrics = QPushButton("Export Metrics")
        self.btn_export_metrics.clicked.connect(lambda: self.export_data('metrics'))
        self.export_layout.addWidget(self.btn_export_metrics)

        self.btn_export_interventions = QPushButton("Export Interventions")
        self.btn_export_interventions.clicked.connect(lambda: self.export_data('interventions'))
        self.export_layout.addWidget(self.btn_export_interventions)

        self.btn_export_events = QPushButton("Export Events")
        self.btn_export_events.clicked.connect(lambda: self.export_data('events'))
        self.export_layout.addWidget(self.btn_export_events)

        self.btn_export_definitions = QPushButton("Export Metric Definitions")
        self.btn_export_definitions.clicked.connect(lambda: self.export_data('metric_definitions'))
        self.export_layout.addWidget(self.btn_export_definitions)

        self.export_group.setLayout(self.export_layout)
        self.layout.addWidget(self.export_group)

        self.layout.addStretch()

    def import_data(self, data_type: str):
        filepath, _ = QFileDialog.getOpenFileName(self, f"Import {data_type.capitalize()}", "", "CSV Files (*.csv)")
        if filepath:
            result = self.data_manager.import_from_csv(filepath, data_type)
            if result['success']:
                show_info(self, result['message'])
            else:
                show_error(self, "Import Failed", result['message'])

    def export_data(self, data_type: str):
        filepath, _ = QFileDialog.getSaveFileName(self, f"Export {data_type.capitalize()}", f"{data_type}.csv", "CSV Files (*.csv)")
        if filepath:
            result = self.data_manager.export_to_csv(filepath, data_type)
            if result['success']:
                show_info(self, result['message'])
            else:
                show_error(self, "Export Failed", result['message'])
