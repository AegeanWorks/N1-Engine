import sqlite3
from datetime import date

from sqlalchemy import create_engine, inspect
from sqlalchemy.orm import sessionmaker

from main.core.data_manager import DataManager
from main.core.database import Base, ensure_schema
from main.core.models import EventEntry, Intervention, MetricEntry
from main.core.settings_manager import SettingsManager


def _old_database(path):
    connection = sqlite3.connect(path)
    connection.executescript(
        """
        CREATE TABLE interventions (
            id INTEGER PRIMARY KEY,
            name VARCHAR NOT NULL,
            start_date DATE NOT NULL,
            end_date DATE,
            dosage VARCHAR,
            notes VARCHAR
        );
        CREATE TABLE metrics (
            id INTEGER PRIMARY KEY,
            date DATE NOT NULL,
            metric_name VARCHAR NOT NULL,
            value FLOAT NOT NULL
        );
        CREATE TABLE events (
            id INTEGER PRIMARY KEY,
            timestamp DATETIME NOT NULL,
            event_name VARCHAR NOT NULL,
            severity INTEGER,
            notes VARCHAR
        );
        INSERT INTO interventions (id, name, start_date) VALUES (1, 'Legacy', '2026-01-01');
        INSERT INTO metrics (id, date, metric_name, value) VALUES (1, '2026-01-02', 'Sleep', 8.0);
        INSERT INTO events (id, timestamp, event_name, severity) VALUES (1, '2026-01-02 10:00:00', 'Stress', 2);
        """
    )
    connection.commit()
    connection.close()


def test_ensure_schema_upgrades_an_old_sqlite_database(tmp_path):
    path = tmp_path / "legacy.db"
    _old_database(path)
    engine = create_engine(f"sqlite:///{path.as_posix()}")

    ensure_schema(engine)

    inspector = inspect(engine)
    assert "projected_end_date" in {column["name"] for column in inspector.get_columns("interventions")}
    assert "intervention_id" in {column["name"] for column in inspector.get_columns("metrics")}
    assert "intervention_id" in {column["name"] for column in inspector.get_columns("events")}
    with engine.connect() as connection:
        assert connection.exec_driver_sql("SELECT COUNT(*) FROM interventions").scalar() == 2
        assert connection.exec_driver_sql("SELECT COUNT(*) FROM metrics").scalar() == 1
        assert connection.exec_driver_sql(
            "SELECT intervention_id FROM metrics WHERE id = 1"
        ).scalar() is not None
        assert connection.exec_driver_sql(
            "SELECT intervention_id FROM events WHERE id = 1"
        ).scalar() is not None
        assert connection.exec_driver_sql(
            "SELECT name FROM interventions WHERE id = 2"
        ).scalar() == "Legacy (unassigned)"


def test_csv_import_preserves_intervention_links(tmp_path):
    engine = create_engine("sqlite:///:memory:")
    Base.metadata.create_all(engine)
    session = sessionmaker(bind=engine)()
    session.add(Intervention(name="Original", start_date=date(2026, 1, 1)))
    session.commit()

    metrics_csv = tmp_path / "metrics.csv"
    metrics_csv.write_text(
        "date,metric_name,value,intervention_id\n2026-01-02,Sleep,8.0,1\n",
        encoding="utf-8",
    )
    events_csv = tmp_path / "events.csv"
    events_csv.write_text(
        "timestamp,event_name,severity,notes,intervention_id\n"
        "2026-01-02 10:00:00,Stress,2,,1\n",
        encoding="utf-8",
    )
    interventions_csv = tmp_path / "interventions.csv"
    interventions_csv.write_text(
        "name,start_date,projected_end_date,end_date,dosage,notes\n"
        "Imported,2026-01-03,2026-02-01,2026-01-20,100mg,test\n",
        encoding="utf-8",
    )

    manager = DataManager(session)
    assert manager.import_from_csv(str(metrics_csv), "metrics")["success"]
    assert manager.import_from_csv(str(events_csv), "events")["success"]
    assert manager.import_from_csv(str(interventions_csv), "interventions")["success"]

    metric = session.query(MetricEntry).one()
    event = session.query(EventEntry).one()
    imported = session.query(Intervention).filter_by(name="Imported").one()
    assert metric.intervention_id == 1
    assert event.intervention_id == 1
    assert imported.projected_end_date == date(2026, 2, 1)
    assert imported.end_date == date(2026, 1, 20)
    session.close()


def test_save_settings_reports_failure(tmp_path):
    manager = SettingsManager(settings_file=str(tmp_path / "settings.json"))
    assert manager.save_settings() is True

    unwritable = SettingsManager(settings_file=str(tmp_path))
    assert unwritable.save_settings() is False


def test_csv_import_coerces_bad_numeric_value_cells(tmp_path):
    engine = create_engine("sqlite:///:memory:")
    Base.metadata.create_all(engine)
    session = sessionmaker(bind=engine)()

    bad_csv = tmp_path / "bad_metrics.csv"
    bad_csv.write_text(
        "date,metric_name,value\n2026-01-02,Sleep,bad-number\n2026-01-03,Sleep,8.0\n",
        encoding="utf-8",
    )

    manager = DataManager(session)
    result = manager.import_from_csv(str(bad_csv), "metrics")
    assert result["success"] is True
    assert session.query(MetricEntry).count() == 1
    assert session.query(MetricEntry).one().value == 8.0
    session.close()


def test_csv_import_skips_bad_date_rows(tmp_path):
    engine = create_engine("sqlite:///:memory:")
    Base.metadata.create_all(engine)
    session = sessionmaker(bind=engine)()

    bad_csv = tmp_path / "bad_dates.csv"
    bad_csv.write_text(
        "date,metric_name,value\nnot-a-date,Sleep,8.0\n2026-01-03,Sleep,7.5\n",
        encoding="utf-8",
    )

    manager = DataManager(session)
    result = manager.import_from_csv(str(bad_csv), "metrics")
    assert result["success"] is True
    assert "skipped 1" in result["message"]
    assert session.query(MetricEntry).count() == 1
    assert session.query(MetricEntry).one().value == 7.5
    session.close()


def test_csv_import_coerces_out_of_range_severity(tmp_path):
    engine = create_engine("sqlite:///:memory:")
    Base.metadata.create_all(engine)
    session = sessionmaker(bind=engine)()

    events_csv = tmp_path / "events.csv"
    events_csv.write_text(
        "timestamp,event_name,severity\n2026-01-02 10:00:00,Stress,99\n2026-01-03 10:00:00,Calm,2\n",
        encoding="utf-8",
    )

    manager = DataManager(session)
    result = manager.import_from_csv(str(events_csv), "events")
    assert result["success"] is True
    assert session.query(EventEntry).count() == 2
    rows = {r.event_name: r.severity for r in session.query(EventEntry).all()}
    assert rows["Stress"] is None
    assert rows["Calm"] == 2
    session.close()


def test_csv_import_rejects_all_bad_file(tmp_path):
    engine = create_engine("sqlite:///:memory:")
    Base.metadata.create_all(engine)
    session = sessionmaker(bind=engine)()

    bad_csv = tmp_path / "all_bad.csv"
    bad_csv.write_text(
        "date,metric_name,value\nnot-a-date,Sleep,bad\n",
        encoding="utf-8",
    )

    manager = DataManager(session)
    result = manager.import_from_csv(str(bad_csv), "metrics")
    assert result["success"] is False
    assert session.query(MetricEntry).count() == 0
    session.close()
