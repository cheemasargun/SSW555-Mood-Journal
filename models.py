from extensions import db
from datetime import datetime
from sqlalchemy.orm import relationship
from sqlalchemy import ForeignKey

class MoodEntry(db.Model):
    """
    Legacy model used by tests and backwards compatibility only.
    NOT used by the new Mood Journal system.
    """
    id = db.Column(db.Integer, primary_key=True)
    mood = db.Column(db.String(20), nullable=False)
    note = db.Column(db.Text)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)


# =================================================
# =============== NEW JOURNAL MODELS ===============
# =================================================

# Many-to-Many association table between JournalEntry and Tag
entry_tag = db.Table(
    "entry_tag",
    db.Column("entry_id", db.Integer, db.ForeignKey("journal_entry.id", ondelete="CASCADE")),
    db.Column("tag_id", db.Integer, db.ForeignKey("tag.id", ondelete="CASCADE"))
)


class JournalEntry(db.Model):
    """
    New primary model for the Mood Journal application.
    Replaces MoodEntry for production features.
    """
    __tablename__ = "journal_entry"

    id = db.Column(db.Integer, primary_key=True)

    # Core journal data
    title = db.Column(db.String(200), nullable=False)
    body = db.Column(db.Text)

    # Mood data
    rank = db.Column(db.Integer, nullable=False)         # e.g., emoji level
    mood_rating = db.Column(db.Integer, nullable=False)  # 1–100 scale

    # Metadata / privacy
    is_private = db.Column(db.Boolean, default=False)

    # Date fields
    entry_date = db.Column(db.Date, nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    # Many-to-many → tags
    tags = relationship("Tag", secondary=entry_tag, back_populates="entries")

    # One-to-many → biometrics
    biometrics = relationship("Biometric", back_populates="entry", cascade="all, delete")


class Tag(db.Model):
    """
    Tags that can be assigned to journal entries (e.g. exercise, stressed, family).
    Shared globally across entries, stored once.
    """
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(50), unique=True, nullable=False)

    entries = relationship("JournalEntry", secondary=entry_tag, back_populates="tags")


class Biometric(db.Model):
    """
    Optional biometric data (e.g., heart rate, sleep, calories, steps) per entry.
    Stored as JSON for flexible structure.
    """
    id = db.Column(db.Integer, primary_key=True)
    entry_id = db.Column(db.Integer, ForeignKey("journal_entry.id", ondelete="CASCADE"))

    # 🧠 Flexible JSON (e.g. {"heart_rate": 78, "sleep": 6.2})
    data = db.Column(db.JSON, nullable=False)

    # Link back to entry
    entry = relationship("JournalEntry", back_populates="biometrics")
