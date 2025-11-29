from extensions import db
from datetime import datetime, date
import json  # Add this import

class MoodEntry(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    mood = db.Column(db.String(50), nullable=False)
    notes = db.Column(db.Text)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    # Fields for mood journal integration
    entry_id_str = db.Column(db.String(36), unique=True, nullable=False)
    entry_name = db.Column(db.String(200), nullable=False)
    entry_date = db.Column(db.Date, nullable=False)
    ranking = db.Column(db.Integer, nullable=False)
    mood_rating = db.Column(db.Integer, nullable=False)
    difficulty_ranking = db.Column(db.Integer, nullable=False)  # Add missing field
    entry_body = db.Column(db.Text, nullable=False)  # Rename from 'note' to match usage
    tags_raw = db.Column(db.Text, nullable=True)
    biometrics_raw = db.Column(db.Text, nullable=True)
    is_private = db.Column(db.Boolean, default=False)  # Add privacy field

    def to_entry(self):
        from mood_mastery.entry import Entry

        tags = self.tags_raw.split(",") if self.tags_raw else []
        biometrics = json.loads(self.biometrics_raw) if self.biometrics_raw else None

        e = Entry(
            self.entry_name,
            self.entry_date.day,
            self.entry_date.month,
            self.entry_date.year,
            self.entry_body,
            self.ranking,
            self.mood_rating,
            self.difficulty_ranking,  # Add this
            tags=tags,
            biometrics=biometrics,
        )
        e.entry_id_str = self.entry_id_str
        e.is_private = self.is_private
        # Set the created_at if needed
        if hasattr(e, 'created_at'):
            e.created_at = self.created_at
        return e

    @classmethod
    def from_entry(cls, entry):
        return cls(
            entry_id_str=entry.entry_id_str,
            entry_name=entry.entry_name,
            entry_date=entry.entry_date,
            ranking=entry.ranking,
            mood_rating=entry.mood_rating,
            difficulty_ranking=getattr(entry, 'difficulty_ranking', 3),  # Default if missing
            mood=str(entry.mood_rating),
            notes=entry.entry_body,  # Map to notes field
            entry_body=entry.entry_body,  # Keep original
            tags_raw=",".join(entry.tags) if getattr(entry, "tags", None) else None,
            biometrics_raw=json.dumps(entry.biometrics) if getattr(entry, "biometrics", None) else None,
            is_private=getattr(entry, 'is_private', False)
        )
