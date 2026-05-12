from flask_sqlalchemy import SQLAlchemy
from datetime import datetime

db = SQLAlchemy()

class Driver(db.Model):
    __tablename__ = "drivers"

    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    age = db.Column(db.Integer, nullable=False)
    vehicle_number = db.Column(db.String(50), nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    sessions = db.relationship("Session", backref="driver", lazy=True, cascade="all, delete-orphan")

class Session(db.Model):
    __tablename__ = "sessions"

    id = db.Column(db.Integer, primary_key=True)
    driver_id = db.Column(db.Integer, db.ForeignKey("drivers.id"), nullable=False)
    start_time = db.Column(db.DateTime, default=datetime.utcnow)
    end_time = db.Column(db.DateTime, nullable=True)
    total_drowsy_events = db.Column(db.Integer, default=0)
    total_phone_events = db.Column(db.Integer, default=0)

    events = db.relationship("Event", backref="session", lazy=True, cascade="all, delete-orphan")

class Event(db.Model):
    __tablename__ = "events"

    id = db.Column(db.Integer, primary_key=True)
    session_id = db.Column(db.Integer, db.ForeignKey("sessions.id"), nullable=False)
    event_type = db.Column(db.String(50), nullable=False)   # drowsy, sleepy, phone_usage
    status = db.Column(db.String(50), nullable=False)       # awake, sleepy, drowsy, distracted
    event_time = db.Column(db.DateTime, default=datetime.utcnow)