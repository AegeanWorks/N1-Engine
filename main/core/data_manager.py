import pandas as pd
from sqlalchemy.orm import Session
from typing import Literal, Optional, Generator
import logging
import contextlib
from main.core.models import MetricEntry, Intervention, EventEntry
from main.core.database import SessionLocal

logger = logging.getLogger(__name__)

class DataManager:
    """
    Manages data import and export.
    """
    def __init__(self, db: Session = None):
        self.db = db

    @contextlib.contextmanager
    def _get_session(self) -> Generator[Session, None, None]:
        """
        Yields the existing session or creates a new one.
        """
        if self.db:
            yield self.db
        else:
            session = SessionLocal()
            try:
                yield session
                session.commit()
            except Exception:
                session.rollback()
                raise
            finally:
                session.close()

    def import_from_csv(self, filepath: str, data_type: Literal['metrics', 'interventions', 'events']) -> dict:
        """
        Imports data from a CSV file.
        Returns a dictionary with success/failure status and message.
        """
        try:
            df = pd.read_csv(filepath)

            with self._get_session() as session:
                if data_type == 'metrics':
                    required_cols = ['date', 'metric_name', 'value']
                    if not all(col in df.columns for col in required_cols):
                        return {"success": False, "message": f"CSV must contain columns: {required_cols}"}

                    # Use pandas to handle date parsing
                    df['date'] = pd.to_datetime(df['date']).dt.date

                    # Coerce bad numeric cells to NaN so one bad cell does not
                    # fail the whole import (extends intervention_id tolerance).
                    df['value'] = pd.to_numeric(df['value'], errors='coerce')
                    skipped_bad = int(df['value'].isna().sum())
                    df = df.dropna(subset=['value'])
                    if df.empty:
                        return {"success": False, "message": f"No valid metric entries (skipped {skipped_bad} bad value row(s))."}

                    entries = []
                    # Convert to list of dicts for faster iteration
                    records = df.to_dict('records')
                    for row in records:
                        intervention_id = row.get('intervention_id')
                        if pd.isna(intervention_id):
                            intervention_id = None
                        elif intervention_id is not None:
                            try:
                                intervention_id = int(intervention_id)
                            except (TypeError, ValueError):
                                intervention_id = None
                        entries.append(MetricEntry(
                            date=row['date'],
                            metric_name=row['metric_name'],
                            value=row['value'],
                            intervention_id=intervention_id
                        ))
                    session.bulk_save_objects(entries)
                    if self.db: session.commit() # Commit if using external session too, though context manager handles new ones.
                    # Wait, if self.db is passed, context manager yields it but doesn't commit/close.
                    # So explicit commit here is good for immediate persistence if user expects it.
                    # But usually transaction management is up to caller if they pass session.
                    # However, "import" implies a complete action. I will commit.
                    session.commit()
                    if skipped_bad:
                        return {"success": True, "message": f"Successfully imported {len(entries)} metric entries (skipped {skipped_bad} bad value row(s))."}
                    return {"success": True, "message": f"Successfully imported {len(entries)} metric entries."}

                elif data_type == 'interventions':
                    required_cols = ['name', 'start_date']
                    if not all(col in df.columns for col in required_cols):
                        return {"success": False, "message": f"CSV must contain columns: {required_cols}"}

                    df['start_date'] = pd.to_datetime(df['start_date']).dt.date

                    # Ensure optional columns exist and convert NaT to None for SQL.
                    for col in ['projected_end_date', 'end_date']:
                        if col in df.columns:
                            df[col] = pd.to_datetime(df[col]).dt.date
                            df[col] = df[col].apply(lambda x: None if pd.isna(x) else x)
                        else:
                            df[col] = None
                    for col in ['dosage', 'notes']:
                        if col not in df.columns:
                            df[col] = None

                    records = df.to_dict('records')
                    entries = []
                    for row in records:
                        entries.append(Intervention(
                            name=row['name'],
                            start_date=row['start_date'],
                            projected_end_date=row.get('projected_end_date'),
                            end_date=row.get('end_date'),
                            dosage=row.get('dosage'),
                            notes=row.get('notes')
                        ))
                    session.bulk_save_objects(entries)
                    session.commit()
                    return {"success": True, "message": f"Successfully imported {len(entries)} interventions."}

                elif data_type == 'events':
                    required_cols = ['timestamp', 'event_name']
                    if not all(col in df.columns for col in required_cols):
                        return {"success": False, "message": f"CSV must contain columns: {required_cols}"}

                    df['timestamp'] = pd.to_datetime(df['timestamp'])

                    # Ensure optional columns
                    for col in ['severity', 'notes']:
                        if col not in df.columns:
                            df[col] = None

                    records = df.to_dict('records')
                    entries = []
                    for row in records:
                        # Handle severity being float (NaN) if missing in CSV
                        severity = row.get('severity')
                        if pd.isna(severity):
                            severity = None
                        elif severity is not None:
                            try:
                                severity = int(severity)
                            except (TypeError, ValueError):
                                severity = None

                        intervention_id = row.get('intervention_id')
                        if pd.isna(intervention_id):
                            intervention_id = None
                        elif intervention_id is not None:
                            try:
                                intervention_id = int(intervention_id)
                            except (TypeError, ValueError):
                                intervention_id = None

                        entries.append(EventEntry(
                            timestamp=row['timestamp'],
                            event_name=row['event_name'],
                            severity=severity,
                            notes=row.get('notes'),
                            intervention_id=intervention_id
                        ))
                    session.bulk_save_objects(entries)
                    session.commit()
                    return {"success": True, "message": f"Successfully imported {len(entries)} events."}

                else:
                    return {"success": False, "message": "Invalid data type."}

        except Exception as e:
            # If we created the session, rollback is in finally.
            # If passed, we should probably rollback too?
            # Context manager handles local session rollback.
            # For passed session, we might not want to rollback entire session if it had other changes?
            # But import failed, so we should at least rollback this transaction.
            # safe to rollback.
            if self.db: self.db.rollback()
            logger.error(f"Import failed: {e}")
            return {"success": False, "message": f"Import failed: {str(e)}"}

    def export_to_csv(self, filepath: str, data_type: Literal['metrics', 'interventions', 'events']) -> dict:
        """
        Exports data to a CSV file.
        Returns a dictionary with success/failure status and message.
        """
        try:
            with self._get_session() as session:
                if data_type == 'metrics':
                    query = session.query(MetricEntry)
                    df = pd.read_sql(query.statement, session.bind)
                    if 'id' in df.columns:
                        df = df.drop(columns=['id'])
                    df.to_csv(filepath, index=False)
                    return {"success": True, "message": f"Successfully exported metrics to {filepath}."}

                elif data_type == 'interventions':
                    query = session.query(Intervention)
                    df = pd.read_sql(query.statement, session.bind)
                    if 'id' in df.columns:
                        df = df.drop(columns=['id'])
                    df.to_csv(filepath, index=False)
                    return {"success": True, "message": f"Successfully exported interventions to {filepath}."}

                elif data_type == 'events':
                    query = session.query(EventEntry)
                    df = pd.read_sql(query.statement, session.bind)
                    if 'id' in df.columns:
                        df = df.drop(columns=['id'])
                    df.to_csv(filepath, index=False)
                    return {"success": True, "message": f"Successfully exported events to {filepath}."}

                else:
                    return {"success": False, "message": "Invalid data type."}

        except Exception as e:
            logger.error(f"Export failed: {e}")
            return {"success": False, "message": f"Export failed: {str(e)}"}
