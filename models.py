from core import app
from flask_sqlalchemy import SQLAlchemy
from datetime import datetime, timedelta

db = SQLAlchemy(app)

class Measurement(db.Model):
    """
    The table containing the measurements.
    """
    __tablename__ = 'measurements'
    id = db.Column(db.Integer, primary_key=True)
    datetime = db.Column(db.DateTime(timezone=True), unique=True, nullable=False)
    temperature = db.Column(db.Float, unique=False, nullable=False)
    humidity = db.Column(db.Float, unique=False, nullable=False)
    moisture = db.Column(db.Float, unique=False, nullable=False)
    brightness = db.Column(db.Float, unique=False, default=0)
    wateringtime = db.Column(db.Float, unique=False, default=0)

#### Lastly ####
engine = db.create_engine(app.config["SQLALCHEMY_DATABASE_URI"], {})