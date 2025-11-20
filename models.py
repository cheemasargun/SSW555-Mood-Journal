from extensions import db
from datetime import datetime
import json

class MoodEntry(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    mood = db.Column(db.String(50), nullable=False)
    notes = db.Column(db.Text)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    # 🔹 NEW FIELDS for mood journal integration
    entry_id_str = db.Column(db.String(36), unique=True, nullable=False)  # UUID from Entry
    entry_name = db.Column(db.String(200), nullable=False)
    entry_date = db.Column(db.Date, nullable=False)
    ranking = db.Column(db.Integer, nullable=False)
    mood_rating = db.Column(db.Integer, nullable=False)
    tags_raw = db.Column(db.Text, nullable=True)         # comma-separated tags
    biometrics_raw = db.Column(db.Text, nullable=True)   # JSON string

    # 🔹 Helper: DB → Entry
    def to_entry(self):
        from mood_mastery.entry import Entry  # avoid circular import at top

        d: date = self.entry_date
        tags = self.tags_raw.split(",") if self.tags_raw else []
        biometrics = json.loads(self.biometrics_raw) if self.biometrics_raw else None

        # Recreate the Entry object using journal data
        e = Entry(
            self.entry_name,
            d.day,
            d.month,
            d.year,
            self.note or "",      # use note as entry_body
            self.ranking,
            self.mood_rating,
            tags=tags,
            biometrics=biometrics,
        )
        e.entry_id_str = self.entry_id_str
        e.is_private = False  # or map from another field if you add one later
        setattr(e, "created_at", self.created_at)
        return e

    # 🔹 Helper: Entry → DB row
    @classmethod
    def from_entry(cls, entry):
        return cls(
            entry_id_str=entry.entry_id_str,
            entry_name=entry.entry_name,
            entry_date=entry.entry_date,
            ranking=entry.ranking,
            mood_rating=entry.mood_rating,
            mood=str(entry.mood_rating),          # simple mapping so 'mood' isn't empty
            note=entry.entry_body,
            tags_raw=",".join(entry.tags) if getattr(entry, "tags", None) else None,
            biometrics_raw=json.dumps(entry.biometrics) if getattr(entry, "biometrics", None) else None,
        )
