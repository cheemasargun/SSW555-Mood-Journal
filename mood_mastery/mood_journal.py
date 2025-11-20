"""
General thoughts: this is where we'd have the mood journal

mood_journal.py would likely refer to some kind of database (see docs/DATABASE.md) and get any pre-existing entries

These entries would be loaded into the appropriate object/variable, and here we would have the functions to add/create/delete
(esp since we can't exactly delete an object/instance of a class *from* that object/instance)
(so the delete method would definitely have to go here/wherever it is we're gathering and modifying entries)

REFERENCES TO LOOK AT: docs/DATABASE.md, 
"""

"""
Example from DATABASE.md:

class MoodEntry(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    mood = db.Column(db.String(20), nullable=False)
    note = db.Column(db.Text)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
"""

"""
^ This example seems to be doing what we're doing in entry.py
We can make further edits to mood_journal.py and entry.py in accordance to the examples given if we
wish to follow them to a T, or we can see how we'd do the equivalents with what we currently have
in entry.py and mood_journal.py
"""

from datetime import datetime, date, timedelta
from typing import Optional, Dict, List
from extensions import db
from models import JournalEntry, Tag, Biometric
from mood_mastery.entry import Entry  # still used as in-memory object

class Mood_Journal:
    """
    Mood Journal service layer.
    - Uses Entry objects in-memory (for compatibility with tests).
    - Persists data in NEW database tables (JournalEntry, Tag, Biometric).
    - Supports streaks, reports, calendars, tags, and biometrics.
    """

    def __init__(self):
        self.entries_dict: Dict[str, Entry] = {}
        self.streak_current = 0
        self.streak_longest = 0
        self.last_entry_date: Optional[date] = None
        self._load_from_db()

    # ======================================================
    # ================ DATABASE HELPERS =====================
    # ======================================================

    def _load_from_db(self):
        """Load all JournalEntry rows + relationships into Entry objects."""
        rows: List[JournalEntry] = JournalEntry.query.order_by(
            JournalEntry.entry_date.asc(),
            JournalEntry.created_at.asc()
        ).all()

        for row in rows:
            self.entries_dict[str(row.id)] = self._db_to_entry(row)

        # ensure streak reflects DB history
        self.recompute_streak()

    def _db_to_entry(self, row: JournalEntry) -> Entry:
        """Convert DB row → Entry object"""
        d = row.entry_date
        e = Entry(
            row.title,
            d.day, d.month, d.year,
            row.body or "",
            row.rank,
            row.mood_rating,
            tags=[t.name for t in row.tags],
            biometrics={b.data for b in row.biometrics} if row.biometrics else None,
        )
        e.entry_id_str = str(row.id)
        e.is_private = row.is_private
        setattr(e, "created_at", row.created_at)
        return e

    def _save_entry_to_db(self, entry: Entry) -> int:
        """Persist Entry → JournalEntry row + tags + biometrics."""
        row = JournalEntry(
            title=entry.entry_name,
            body=entry.entry_body,
            rank=entry.ranking,
            mood_rating=entry.mood_rating,
            entry_date=entry.entry_date,
            is_private=entry.is_private,
            created_at=getattr(entry, "created_at", datetime.utcnow()),
        )
        db.session.add(row)
        db.session.commit()  # row.id now exists

        # Save tags
        if getattr(entry, "tags", None):
            for t in entry.tags:
                self._add_tag_to_entry(row.id, t)

        # Save biometrics
        if getattr(entry, "biometrics", None):
            b = Biometric(entry_id=row.id, data=entry.biometrics)
            db.session.add(b)

        db.session.commit()
        return row.id

    def _add_tag_to_entry(self, entry_id: int, tag_name: str):
        """Ensure tag exists globally and attach it to entry."""
        tag = Tag.query.filter_by(name=tag_name).first()
        if not tag:
            tag = Tag(name=tag_name)
            db.session.add(tag)
            db.session.commit()
        entry = JournalEntry.query.get(entry_id)
        entry.tags.append(tag)
        db.session.commit()

    # ======================================================
    # ================ UTILITY HELPERS ======================
    # ======================================================

    def _to_date(self, d) -> date:
        if isinstance(d, date):
            return d
        if isinstance(d, tuple) and len(d) == 3:
            day, month, year = d
            return date(year, month, day)
        return date.today()

    def _entry_date(self, e: Entry):
        return self._to_date(e.entry_date)

    # ======================================================
    # ================= CRUD FUNCTIONS =====================
    # ======================================================

    def mj_log_entry(self, entry_name, entry_day, entry_month, entry_year,
                     entry_body, ranking, mood_rating, tags=None, biometrics=None) -> str:
        eid = self.mj_create_entry(entry_name, entry_day, entry_month, entry_year,
                                   entry_body, ranking, mood_rating, tags, biometrics)
        new_entry = self.mj_get_entry(eid)
        self.update_streak(new_entry.entry_date)
        return eid

    def mj_create_entry(self, entry_name, entry_day, entry_month, entry_year,
                        entry_body, ranking, mood_rating, tags=None, biometrics=None):
        new_entry = Entry(entry_name, entry_day, entry_month, entry_year,
                          entry_body, ranking, mood_rating, tags, biometrics)

        # Ensure created_at for streak sorting
        if not hasattr(new_entry, "created_at"):
            setattr(new_entry, "created_at", datetime.utcnow())

        # Persist to DB first
        new_id = self._save_entry_to_db(new_entry)
        new_entry.entry_id_str = str(new_id)

        # Mirror in-memory
        self.entries_dict[new_entry.entry_id_str] = new_entry
        self.recompute_streak()
        return new_entry.entry_id_str

    def mj_edit_entry(self, entry_id_str, new_name, new_day, new_month, new_year,
                      new_body, new_ranking, new_mood_rating):
        entry = self.entries_dict.get(entry_id_str)
        if not entry:
            return False

        entry.edit_entry(new_name, new_day, new_month, new_year,
                         new_body, new_ranking, new_mood_rating)

        # Update DB
        row: JournalEntry = JournalEntry.query.get(int(entry_id_str))
        row.title = entry.entry_name
        row.body = entry.entry_body
        row.rank = entry.ranking
        row.mood_rating = entry.mood_rating
        row.entry_date = entry.entry_date
        db.session.commit()

        self.recompute_streak()
        return True

    def mj_delete_entry(self, entry_id_str):
        removed = False
        if entry_id_str in self.entries_dict:
            del self.entries_dict[entry_id_str]
            removed = True

        row = JournalEntry.query.get(int(entry_id_str))
        if row:
            db.session.delete(row)
            db.session.commit()
            removed = True

        if removed:
            self.recompute_streak()

        return removed

    def mj_get_entry(self, entry_id_str):
        return self.entries_dict.get(entry_id_str, False)

    def mj_get_entry_privacy_status(self, entry_id_str):
        entry = self.mj_get_entry(entry_id_str)
        return None if not entry else entry.is_private_check()

    def mj_get_all_entries(self):
        return list(self.entries_dict.values())

    # ======================================================
    # ================= STREAK SYSTEM ======================
    # ======================================================

    def recompute_streak(self):
        entries = self.mj_get_all_entries()
        if not entries:
            self.streak_current = 0
            self.streak_longest = 0
            self.last_entry_date = None
            return

        dates = sorted({e.entry_date for e in entries})
        self.last_entry_date = dates[-1]

        longest = run = 1
        for i in range(1, len(dates)):
            if (dates[i] - dates[i-1]) == timedelta(days=1):
                run += 1
            else:
                longest = max(longest, run)
                run = 1
        longest = max(longest, run)

        current = 1
        for j in range(len(dates) - 1, 0, -1):
            if (dates[j] - dates[j-1]) == timedelta(days=1):
                current += 1
            else:
                break

        self.streak_current = current
        self.streak_longest = longest

    def update_streak(self, entry_date: date):
        if self.last_entry_date is None:
            self.last_entry_date = entry_date
            self.streak_current = 1
            self.streak_longest = max(self.streak_longest, self.streak_current)
            return
        if entry_date == self.last_entry_date:
            return
        if entry_date == self.last_entry_date + timedelta(days=1):
            self.streak_current += 1
            self.last_entry_date = entry_date
            self.streak_longest = max(self.streak_longest, self.streak_current)
            return
        if entry_date > self.last_entry_date + timedelta(days=1):
            self.streak_current = 1
            self.last_entry_date = entry_date
            self.streak_longest = max(self.streak_longest, self.streak_current)
            return
        self.recompute_streak()

    def get_streak_summary(self):
        return {
            "current_streak": self.streak_current,
            "longest_streak": self.streak_longest,
            "last_entry_date": self.last_entry_date
        }

    # ======================================================
    # ===================== REPORTS ========================
    # ======================================================

    def mj_weekly_report(self, curr_day, curr_month, curr_year):
        curr_date = date(curr_year, curr_month, curr_day)
        weekly_dates = [curr_date - timedelta(days=i) for i in range(7)]
        entries = [k for k in self.entries_dict if self.entries_dict[k].entry_date in weekly_dates]

        if not entries:
            return None

        emoji_count = [0] * 8
        for k in entries:
            emoji_count[self.entries_dict[k].ranking - 1] += 1
        return emoji_count

    def mj_monthly_report(self, curr_day, curr_month, curr_year):
        curr_date = date(curr_year, curr_month, curr_day)
        monthly_dates = [curr_date - timedelta(days=i) for i in range(30)]
        entries = [k for k in self.entries_dict if self.entries_dict[k].entry_date in monthly_dates]

        if not entries:
            return None

        emoji_count = [0] * 8
        for k in entries:
            emoji_count[self.entries_dict[k].ranking - 1] += 1
        return emoji_count

    def mj_emoji_groups(self, emoji):
        keys = []
        ratingCount = [0] * 100

        for k, e in self.entries_dict.items():
            if e.ranking == emoji:
                ratingCount[e.mood_rating - 1] += 1
                keys.append(k)

        return ratingCount, keys

    # ======================================================
    # ===================== CALENDAR =======================
    # ======================================================

    def mj_entries_on(self, year, month, day):
        target = date(year, month, day)
        items = [e for e in self.entries_dict.values() if self._entry_date(e) == target]

        items.sort(key=lambda e: (
            getattr(e, "created_at", datetime.combine(self._entry_date(e), datetime.min.time())),
            getattr(e, "entry_name", ""),
            getattr(e, "entry_id_str", "")
        ))
        return items

    def mj_entries_between(self, start, end):
        items = [e for e in self.entries_dict.values() if start <= self._entry_date(e) <= end]

        items.sort(key=lambda e: (
            self._entry_date(e),
            getattr(e, "created_at", datetime.combine(self._entry_date(e), datetime.min.time())),
            getattr(e, "entry_id_str", "")
        ))
        return items

    def mj_entries_grouped_by_day(self, start, end):
        days = {}
        cur = start
        while cur <= end:
            days[cur] = []
            cur += timedelta(days=1)

        for e in self.entries_dict.values():
            d = self._entry_date(e)
            if start <= d <= end:
                days[d].append(e)

        for lst in days.values():
            lst.sort(key=lambda e: (
                getattr(e, "created_at", datetime.combine(self._entry_date(e), datetime.min.time())),
                getattr(e, "entry_name", ""),
                getattr(e, "entry_id_str", "")
            ))
        return days

    def mj_month_calendar(self, year, month):
        first = date(year, month, 1)
        start = first - timedelta(days=first.weekday())
        next_first = date(year + 1, 1, 1) if month == 12 else date(year, month + 1, 1)
        last = next_first - timedelta(days=1)
        end = last + timedelta(days=(6 - last.weekday()))
        return self.mj_entries_grouped_by_day(start, end)

    # ======================================================
    # ====================== TAGS ==========================
    # ======================================================

    def mj_all_tags(self):
        tag_set = set()
        for e in self.entries_dict.values():
            for t in getattr(e, "tags", []):
                tag_set.add(t)
        return sorted(tag_set)

    def mj_entries_with_tag(self, tag):
        items = [e for e in self.entries_dict.values() if e.has_tag(tag)]
        items.sort(key=lambda e: (
            self._entry_date(e),
            getattr(e, "entry_name", ""),
            getattr(e, "entry_id_str", ""),
        ))
        return items

    def mj_tag_summary(self):
        counts = {}
        for e in self.entries_dict.values():
            for t in getattr(e, "tags", []):
                counts[t] = counts.get(t, 0) + 1
        return sorted(counts.items(), key=lambda kv: (-kv[1], kv[0]))

    # ======================================================
    # ===================== ADMIN =========================
    # ======================================================

    def mj_clear_all_data(self):
        """Wipe ALL journal data (DB + memory)"""
        self.entries_dict.clear()
        JournalEntry.query.delete()
        Tag.query.delete()
        Biometric.query.delete()
        db.session.commit()
        self.recompute_streak()
