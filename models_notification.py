from extensions import db
from datetime import time

class NotificationSettings(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    enabled = db.Column(db.Boolean, default=False)
    scheduled_hour = db.Column(db.Integer, default=20)  # 8 PM reminder
    scheduled_minute = db.Column(db.Integer, default=0)
