import pandas as pd
from sqlalchemy.orm import Session
from typing import Literal, Optional, Generator
import logging
import contextlib
from main.core.models import MetricEntry, Intervention, EventEntry
from main.core.database import SessionLocal

logger = logging.getLogger(__name__)


def _coerce_int_or_none(value, min_value=None, max_value=None):
    """Coerce CSV cells to int or None without raising.

    Floats like 1.0/"2.0" become int; non-integer floats ("2.5"),
    bad strings and out-of-range values become None so one bad cell
    does not fail the whole import (severity 1-5 enforced via range).
    """
    if value is None or (isinstance(value, float) and pd.isna(value)):
        return None
    try:
        if pd.isna(value):
            return None
    except (TypeError, ValueError):
        pass
    try:
        as_float = float(value)
    except (TypeError, ValueError):
        return None
    if not as_float.is_integer():
        return None
    as_int = int(as_float)
    if min_value is not None and as_int < min_value:
        return None
    if max_value is not None and as_int > max_value:
        return None
    return as_int


def _clean_str_or_none(value):
    """Return stripped string or None for NaN/empty cells."""
    if value is None:
        return None
    try:
        if pd.isna(value):
            return None
    except (TypeError, ValueError):
        pass
    text = str(value).strip()
    return text if text else None


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

                    # Coerce bad cells so one bad row does not fail the whole file.
                    df['date'] = pd.to_datetime(df['date'], errors='coerce', format='mixed')
                    df['value'] = pd.to_numeric(df['value'], errors='coerce')
                    valid_mask = (
                        df['date'].notna()
                        & df['value'].notna()
                        & df['metric_name'].notna()
                        & (df['metric_name'].astype(str).str.strip() != '')
                    )
                    skipped_bad = int((~valid_mask).sum())
                    df = df[valid_mask].copy()
                    if df.empty:
                        return {"success": False, "message": f"No valid metric entries (skipped {skipped_bad} bad row(s))."}
                    df['date'] = df['date'].dt.date

                    entries = []
                    # Convert to list of dicts for faster iteration
                    records = df.to_dict('records')
                    for row in records:
                        intervention_id = _coerce_int_or_none(row.get('intervention_id'))
                        entries.append(MetricEntry(
                            date=row['date'],
                            metric_name=str(row['metric_name']).strip(),
                            value=float(row['value']),
                            intervention_id=intervention_id
                        ))
                    session.bulk_save_objects(entries)
                    # Single commit: persists for both owned and caller-passed sessions.
                    session.commit()
                    if skipped_bad:
                        return {"success": True, "message": f"Successfully imported {len(entries)} metric entries (skipped {skipped_bad} bad row(s))."}
                    return {"success": True, "message": f"Successfully imported {len(entries)} metric entries."}

                elif data_type == 'interventions':
                    required_cols = ['name', 'start_date']
                    if not all(col in df.columns for col in required_cols):
                        return {"success": False, "message": f"CSV must contain columns: {required_cols}"}

                    df['start_date'] = pd.to_datetime(df['start_date'], errors='coerce', format='mixed')

                    # Ensure optional columns exist and convert NaT to None for SQL.
                    for col in ['projected_end_date', 'end_date']:
                        if col in df.columns:
                            df[col] = pd.to_datetime(df[col], errors='coerce', format='mixed')
                        else:
                            df[col] = pd.NaT
                    for col in ['dosage', 'notes']:
                        if col not in df.columns:
                            df[col] = None

                    valid_mask = (
                        df['start_date'].notna()
                        & df['name'].notna()
                        & (df['name'].astype(str).str.strip() != '')
                    )
                    skipped_bad = int((~valid_mask).sum())
                    df = df[valid_mask].copy()
                    if df.empty:
                        return {"success": False, "message": f"No valid interventions (skipped {skipped_bad} bad row(s))."}
                    df['start_date'] = df['start_date'].dt.date
                    for col in ['projected_end_date', 'end_date']:
                        df[col] = pd.to_datetime(df[col], errors='coerce', format='mixed').dt.date
                        df[col] = df[col].apply(lambda x: None if pd.isna(x) else x)

                    records = df.to_dict('records')
                    entries = []
                    for row in records:
                        entries.append(Intervention(
                            name=str(row['name']).strip(),
                            start_date=row['start_date'],
                            projected_end_date=row.get('projected_end_date'),
                            end_date=row.get('end_date'),
                            dosage=_clean_str_or_none(row.get('dosage')),
                            notes=_clean_str_or_none(row.get('notes'))
                        ))
                    session.bulk_save_objects(entries)
                    session.commit()
                    if skipped_bad:
                        return {"success": True, "message": f"Successfully imported {len(entries)} interventions (skipped {skipped_bad} bad row(s))."}
                    return {"success": True, "message": f"Successfully imported {len(entries)} interventions."}

                elif data_type == 'events':
                    required_cols = ['timestamp', 'event_name']
                    if not all(col in df.columns for col in required_cols):
                        return {"success": False, "message": f"CSV must contain columns: {required_cols}"}

                    df['timestamp'] = pd.to_datetime(df['timestamp'], errors='coerce', format='mixed')

                    # Ensure optional columns
                    for col in ['severity', 'notes', 'intervention_id']:
                        if col not in df.columns:
                            df[col] = None

                    valid_mask = (
                        df['timestamp'].notna()
                        & df['event_name'].notna()
                        & (df['event_name'].astype(str).str.strip() != '')
                    )
                    skipped_bad = int((~valid_mask).sum())
                    df = df[valid_mask].copy()
                    if df.empty:
                        return {"success": False, "message": f"No valid events (skipped {skipped_bad} bad row(s))."}

                    records = df.to_dict('records')
                    entries = []
                    for row in records:
                        # Out-of-range severity (CHECK 1-5) becomes None instead of failing the file.
                        severity = _coerce_int_or_none(row.get('severity'), min_value=1, max_value=5)
                        intervention_id = _coerce_int_or_none(row.get('intervention_id'))

                        entries.append(EventEntry(
                            timestamp=row['timestamp'].to_pydatetime()
                            if hasattr(row['timestamp'], 'to_pydatetime') else row['timestamp'],
                            event_name=str(row['event_name']).strip(),
                            severity=severity,
                            notes=_clean_str_or_none(row.get('notes')),
                            intervention_id=intervention_id
                        ))
                    session.bulk_save_objects(entries)
                    session.commit()
                    if skipped_bad:
                        return {"success": True, "message": f"Successfully imported {len(entries)} events (skipped {skipped_bad} bad row(s))."}
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
