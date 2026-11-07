from sqlalchemy import Column, Integer, String, Date, Float, DateTime, CheckConstraint, ForeignKey
from sqlalchemy.orm import relationship
from .database import Base

class Intervention(Base):
    __tablename__ = "interventions"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, index=True, nullable=False)
    start_date = Column(Date, nullable=False, index=True)
    projected_end_date = Column(Date, nullable=True)
    end_date = Column(Date, nullable=True)
    dosage = Column(String, nullable=True)
    notes = Column(String, nullable=True)

    metrics = relationship("MetricEntry", back_populates="intervention")
    events = relationship("EventEntry", back_populates="intervention")

    def __repr__(self):
        return f"<Intervention(name='{self.name}', start_date={self.start_date})>"

class MetricDefinition(Base):
    __tablename__ = "metric_definitions"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, unique=True, index=True, nullable=False)
    description = Column(String, nullable=True)
    unit = Column(String, nullable=True)

    def __repr__(self):
        return f"<MetricDefinition(name='{self.name}')>"

class MetricEntry(Base):
    __tablename__ = "metrics"

    id = Column(Integer, primary_key=True, index=True)
    date = Column(Date, index=True, nullable=False)
    metric_name = Column(String, index=True, nullable=False)
    value = Column(Float, nullable=False)

    intervention_id = Column(Integer, ForeignKey("interventions.id"), nullable=True, index=True)
    intervention = relationship("Intervention", back_populates="metrics")

    def __repr__(self):
        return f"<MetricEntry(date={self.date}, metric_name='{self.metric_name}', value={self.value})>"

class EventEntry(Base):
    __tablename__ = "events"
    __table_args__ = (
        CheckConstraint('severity >= 1 AND severity <= 5', name='check_severity_range'),
    )

    id = Column(Integer, primary_key=True, index=True)
    timestamp = Column(DateTime, index=True, nullable=False)
    event_name = Column(String, index=True, nullable=False)
    severity = Column(Integer, nullable=True) # 1-5
    notes = Column(String, nullable=True)

    intervention_id = Column(Integer, ForeignKey("interventions.id"), nullable=True, index=True)
    intervention = relationship("Intervention", back_populates="events")

    def __repr__(self):
        return f"<EventEntry(timestamp={self.timestamp}, event_name='{self.event_name}', severity={self.severity})>"
