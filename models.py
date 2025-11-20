from extensions import db
from datetime import datetime, date
import json

class MoodEntry(db.Model):
    """
    Legacy model formerly used by the UI and tests.
    We keep it ONLY for backward compatibility and import safety.
    DO NOT use for new journal features.
    """
    id = db.Column(db.Integer, primary_key=True)
    mood = db.Column(db.String(50), nullable=False)
    note = db.Column(db.Text)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)


# ======================================================
# =============== NEW JOURNAL MODELS ===================
# ======================================================

# Many-to-many association table between journal entries and tags
entry_tag = db.Table(
    "entry_tag",
    db.Column("entry_id", db.Integer, db.ForeignKey("journal_entry.id", ondelete="CASCADE")),
    db.Column("tag_id", db.Integer, db.ForeignKey("tag.id", ondelete="CASCADE"))
)


class JournalEntry(db.Model):
    """
    Main model for the new Mood Journal system.
    Replaces MoodEntry for ALL new features.

    We store entry_id_str so the Python Entry class can round-trip cleanly.
    """
    __tablename__ = "journal_entry"

    id = db.Column(db.Integer, primary_key=True)

    # Match the Entry object ID (UUID string)
    entry_id_str = db.Column(db.String(36), unique=True, nullable=False)

    # Core journal content
    title = db.Column(db.String(200), nullable=False)
    body = db.Column(db.Text)

    # Mood data
    rank = db.Column(db.Integer, nullable=False)         # emoji level from original app
    mood_rating = db.Column(db.Integer, nullable=False)  # scale 1–100

    # Privacy
    is_private = db.Column(db.Boolean, default=False)

    # Date and metadata
    entry_date = db.Column(db.Date, nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    # Relationships
    tags = relationship("Tag", secondary=entry_tag, back_populates="entries")
    biometrics = relationship("Biometric", back_populates="entry", cascade="all, delete")


class Tag(db.Model):
    """
    Global tag list (unique). Tags are reused across entries.
    Example: exercise, stressed, family, meditation
    """
    __tablename__ = "tag"

    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(50), unique=True, nullable=False)

    entries = relationship("JournalEntry", secondary=entry_tag, back_populates="tags")


class Biometric(db.Model):
    """
    Flexible biometric JSON storage, attached to one entry.
    Example structure:
        {"heart_rate": 72, "sleep": 6.5, "steps": 10452}

    The JSON format allows any attribute to be added without schema changes.
    """
    __tablename__ = "biometric"

    id = db.Column(db.Integer, primary_key=True)
    entry_id = db.Column(db.Integer, ForeignKey("journal_entry.id", ondelete="CASCADE"))

    # Flexible JSON data
    data = db.Column(db.JSON, nullable=False)

    # Relationship back to entry
    entry = relationship("JournalEntry", back_populates="biometrics")
