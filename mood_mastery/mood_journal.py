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
"""
Mood Journal (DB-backed)

This module keeps your existing public API (mj_create_entry, mj_get_entry, etc.)
but persists data to the database defined by the SQLAlchemy models:
    - JournalEntry
    - Tag
    - Biometric

It also mirrors a lightweight in-memory cache (entries_dict) so your current
tests and streak/report helpers continue to work without rewrites.

Assumptions:
- `Entry` is your lightweight Python object used by the UI/tests.
- `Entry.entry_date` is either a date or a (day, month, year) tuple.
- `Entry` has attributes:
    entry_id_str, entry_name/title, entry_date, entry_body,
    ranking (emoji 1–8), mood_rating (1–100), tags (list[str]),
    biometrics (dict | None), created_at (datetime, optional)
- A Flask app context / db session is available where these functions are used.

If your models are in a different module, the try/except imports below should
cover typical layouts. Adjust if needed.
"""

from __future__ import annotations

from datetime import datetime, date, timedelta
from typing import Optional, Dict, List

from extensions import db
from mood_mastery.entry import Entry

# ---- Flexible imports for your models (edit if your paths differ) ----
try:
    from mood_mastery.database import JournalEntry, Tag, Biometric  # type: ignore
except Exception:
    try:
        from mood_mastery.models import JournalEntry, Tag, Biometric  # type: ignore
    except Exception:
        from models import JournalEntry, Tag, Biometric  # type: ignore


class Mood_Journal:
    """
    DB-backed journal with an in-memory cache for convenience & tests.
    """

    def __init__(self):
        # in-memory cache: {entry_id_str -> Entry}
        self.entries_dict: Dict[str, Entry] = {}

        # streak bookkeeping
        self.streak_current: int = 0
        self.streak_longest: int = 0
        self.last_entry_date: Optional[date] = None

        # preload from DB (safe if DB empty)
        self._hydrate_from_db()
        self.recompute_streak()

    # ---------------------------- Utilities ----------------------------

    def _hydrate_from_db(self) -> None:
        """Load all JournalEntry rows and mirror into self.entries_dict."""
        self.entries_dict.clear()
        # Order by created_at so created_at fallback ordering is stable
        rows = (
            db.session.query(JournalEntry)
            .order_by(JournalEntry.created_at.asc(), JournalEntry.id.asc())
            .all()
        )
        for row in rows:
            entry = self._model_to_entry(row)
            self.entries_dict[entry.entry_id_str] = entry

    def _to_date(self, d) -> date:
        """Normalize date-like shapes to datetime.date."""
        if isinstance(d, date):
            return d
        if isinstance(d, tuple) and len(d) == 3:
            day, month, year = d
            return date(year, month, day)
        return date.today()

    def _entry_date(self, e: Entry) -> date:
        return self._to_date(getattr(e, "entry_date", date.today()))

    # ------------------------ Model <-> Entry bridge -------------------

    def _model_to_entry(self, m: JournalEntry) -> Entry:
        """Convert a JournalEntry row to your in-memory Entry object."""
        d = m.entry_date
        e = Entry(
            m.title,
            d.day,
            d.month,
            d.year,
            m.body or "",
            m.rank,
            m.mood_rating,
            tags=[t.name for t in (m.tags or [])],
            biometrics=(m.biometrics[0].data if m.biometrics else None),
        )
        # Overwrite ID to match DB
        setattr(e, "entry_id_str", m.entry_id_str)
        # Preserve created_at for stable ordering
        setattr(e, "created_at", m.created_at or datetime.combine(d, datetime.min.time()))
        # Preserve privacy if Entry supports it (best effort)
        try:
            e.is_private = bool(m.is_private)
        except Exception:
            pass
        return e

    def _ensure_tag(self, name: str) -> Tag:
        name = (name or "").strip().lower()
        if not name:
            # Create nothing for blank names; callers should filter
            raise ValueError("Empty tag name is not allowed")
        obj = db.session.query(Tag).filter_by(name=name).one_or_none()
        if obj is None:
            obj = Tag(name=name)
            db.session.add(obj)
        return obj

    # ----------------------------- Public API --------------------------

    def mj_log_entry(
        self,
        entry_name: str,
        entry_day: int,
        entry_month: int,
        entry_year: int,
        entry_body: str,
        ranking: int,
        mood_rating: int,
        tags=None,
        biometrics=None,
    ) -> str:
        """Create an entry, persist it, and update streaks. Return entry_id_str."""
        entry_id = self.mj_create_entry(
            entry_name,
            entry_day,
            entry_month,
            entry_year,
            entry_body,
            ranking,
            mood_rating,
            tags,
            biometrics,
        )
        new_entry = self.mj_get_entry(entry_id)
        if new_entry:
            self.update_streak(self._entry_date(new_entry))
        return entry_id

    def mj_create_entry(
        self,
        entry_name: str,
        entry_day: int,
        entry_month: int,
        entry_year: int,
        entry_body: str,
        ranking: int,
        mood_rating: int,
        tags=None,
        biometrics=None,
    ) -> str:
        """
        Create Entry (in-memory) first to get its UUID, then persist to DB with
        the same entry_id_str to keep parity across layers.
        """
        # 1) Build Entry object (as your current tests expect)
        e = Entry(
            entry_name,
            entry_day,
            entry_month,
            entry_year,
            entry_body,
            ranking,
            mood_rating,
            tags=tags or [],
            biometrics=biometrics,
        )
        entry_id = e.entry_id_str
        d = self._entry_date(e)

        # 2) Persist to DB
        row = JournalEntry(
            entry_id_str=entry_id,
            title=entry_name,
            body=entry_body,
            rank=ranking,
            mood_rating=mood_rating,
            is_private=getattr(e, "is_private", False),
            entry_date=d,
            created_at=getattr(e, "created_at", datetime.utcnow()),
        )

        # Tags
        tag_objs: List[Tag] = []
        for t in (tags or []):
            t = (t or "").strip().lower()
            if not t:
                continue
            tag_objs.append(self._ensure_tag(t))
        row.tags = tag_objs

        # Biometrics (optional)
        if biometrics is not None:
            row.biometrics = [Biometric(data=biometrics)]

        try:
            db.session.add(row)
            db.session.commit()
        except Exception:
            db.session.rollback()
            raise

        # 3) Mirror into cache for fast reads & existing helpers
        setattr(e, "created_at", row.created_at)
        self.entries_dict[entry_id] = e
        self.recompute_streak()

        return entry_id

    def mj_edit_entry(
        self,
        entry_id_str: str,
        new_name: str,
        new_day: int,
        new_month: int,
        new_year: int,
        new_body: str,
        new_ranking: int,
        new_mood_rating: int,
        new_tags=None,
        new_biometrics=None,
        is_private: Optional[bool] = None,
    ) -> bool:
        """
        Update both DB row and in-memory cache. Returns True if updated.
        """
        row = db.session.query(JournalEntry).filter_by(entry_id_str=entry_id_str).one_or_none()
        if row is None:
            return False

        # Update DB row
        row.title = new_name
        row.body = new_body
        row.rank = new_ranking
        row.mood_rating = new_mood_rating
        if is_private is not None:
            row.is_private = bool(is_private)
        row.entry_date = date(new_year, new_month, new_day)

        # Tags
        if new_tags is not None:
            tag_objs: List[Tag] = []
            for t in new_tags:
                t = (t or "").strip().lower()
                if not t:
                    continue
                tag_objs.append(self._ensure_tag(t))
            row.tags = tag_objs

        # Biometrics: simple policy — keep latest as single record
        if new_biometrics is not None:
            # Clear existing biometrics
            for b in list(row.biometrics or []):
                db.session.delete(b)
            if new_biometrics:
                row.biometrics = [Biometric(data=new_biometrics)]

        try:
            db.session.commit()
        except Exception:
            db.session.rollback()
            raise

        # Update cache Entry (create if not present)
        e = self.entries_dict.get(entry_id_str)
        if e is None:
            e = self._model_to_entry(row)
            self.entries_dict[entry_id_str] = e
        else:
            # Reuse your Entry API if available
            try:
                e.edit_entry(new_name, new_day, new_month, new_year, new_body, new_ranking, new_mood_rating)
            except Exception:
                # Fallback: set attributes directly
                e.entry_name = new_name
                e.entry_body = new_body
                e.ranking = new_ranking
                e.mood_rating = new_mood_rating
                e.entry_date = (new_day, new_month, new_year)
            # Tags & biometrics
            if new_tags is not None:
                e.tags = [(t or "").strip().lower() for t in new_tags if (t or "").strip()]
            if is_private is not None:
                try:
                    e.is_private = bool(is_private)
                except Exception:
                    pass
            if new_biometrics is not None:
                e.biometrics = new_biometrics

        # Recompute streaks in case the date changed
        self.recompute_streak()
        return True

    def mj_delete_entry(self, entry_id_str: str) -> bool:
        """
        Delete from DB (cascades to biometrics and entry_tag) and from cache.
        """
        row = db.session.query(JournalEntry).filter_by(entry_id_str=entry_id_str).one_or_none()
        if row is None:
            return False

        try:
            db.session.delete(row)
            db.session.commit()
        except Exception:
            db.session.rollback()
            raise

        self.entries_dict.pop(entry_id_str, None)
        self.recompute_streak()
        return True

    def mj_get_entry(self, entry_id_str: str) -> Optional[Entry]:
        """
        Return the Entry object if present; load from DB if missing.
        """
        cached = self.entries_dict.get(entry_id_str)
        if cached:
            return cached

        row = db.session.query(JournalEntry).filter_by(entry_id_str=entry_id_str).one_or_none()
        if row is None:
            return None
        entry = self._model_to_entry(row)
        self.entries_dict[entry_id_str] = entry
        return entry

    def mj_get_entry_privacy_status(self, entry_id_str: str):
        e = self.mj_get_entry(entry_id_str)
        if not e:
            return None
        # Prefer Entry API if available
        try:
            return bool(e.is_private_check())
        except Exception:
            return bool(getattr(e, "is_private", False))

    # --------------------------- Bulk getters --------------------------

    def mj_get_all_entries(self) -> List[Entry]:
        """Return all entries as Entry objects (cache-backed)."""
        # Keep cache fresh (cheap unless table is large)
        self._hydrate_from_db()
        return list(self.entries_dict.values())

    # --------------------------- Streak System -------------------------

    def recompute_streak(self) -> None:
        entries = list(self.entries_dict.values())
        if not entries:
            self.streak_current = 0
            self.streak_longest = 0
            self.last_entry_date = None
            return

        dates = sorted({self._entry_date(e) for e in entries})
        self.last_entry_date = dates[-1]

        # Longest streak
        longest = 1
        run = 1
        for i in range(1, len(dates)):
            if (dates[i] - dates[i - 1]) == timedelta(days=1):
                run += 1
            else:
                longest = max(longest, run)
                run = 1
        longest = max(longest, run)

        # Current streak (ending at last date)
        current = 1
        for j in range(len(dates) - 1, 0, -1):
            if (dates[j] - dates[j - 1]) == timedelta(days=1):
                current += 1
            else:
                break

        self.streak_current = current
        self.streak_longest = longest

    def get_streak_summary(self):
        return {
            "current_streak": self.streak_current,
            "longest_streak": self.streak_longest,
            "last_entry_date": self.last_entry_date,
        }

    def update_streak(self, entry_date: date) -> None:
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

    # --------------------------- Reports/Queries -----------------------

    def mj_weekly_report(self, curr_day, curr_month, curr_year):
        curr_date = date(curr_year, curr_month, curr_day)
        weekly_dates = {curr_date - timedelta(days=i) for i in range(7)}
        # Keep cache in sync with DB
        self._hydrate_from_db()

        entries_to_report = [
            e for e in self.entries_dict.values() if self._entry_date(e) in weekly_dates
        ]

        if not entries_to_report:
            return None

        emoji_count = [0] * 8
        for e in entries_to_report:
            if 1 <= e.ranking <= 8:
                emoji_count[e.ranking - 1] += 1
        return emoji_count

    def mj_monthly_report(self, curr_day, curr_month, curr_year):
        curr_date = date(curr_year, curr_month, curr_day)
        monthly_dates = {curr_date - timedelta(days=i) for i in range(30)}
        self._hydrate_from_db()

        entries_to_report = [
            e for e in self.entries_dict.values() if self._entry_date(e) in monthly_dates
        ]

        if not entries_to_report:
            return None

        emoji_count = [0] * 8
        for e in entries_to_report:
            if 1 <= e.ranking <= 8:
                emoji_count[e.ranking - 1] += 1
        return emoji_count

    def mj_entries_on(self, year: int, month: int, day: int) -> List[Entry]:
        target = date(year, month, day)
        self._hydrate_from_db()
        items = [e for e in self.entries_dict.values() if self._entry_date(e) == target]
        items.sort(
            key=lambda e: (
                getattr(e, "created_at", datetime.combine(self._entry_date(e), datetime.min.time())),
                getattr(e, "entry_name", ""),
                getattr(e, "entry_id_str", ""),
            )
        )
        return items

    def mj_entries_between(self, start: date, end: date) -> List[Entry]:
        self._hydrate_from_db()
        items: List[Entry] = []
        for e in self.entries_dict.values():
            d = self._entry_date(e)
            if start <= d <= end:
                items.append(e)
        items.sort(
            key=lambda e: (
                self._entry_date(e),
                getattr(e, "created_at", datetime.combine(self._entry_date(e), datetime.min.time())),
                getattr(e, "entry_id_str", ""),
            )
        )
        return items

    def mj_entries_grouped_by_day(self, start: date, end: date) -> Dict[date, List[Entry]]:
        days: Dict[date, List[Entry]] = {}
        cur = start
        while cur <= end:
            days[cur] = []
            cur += timedelta(days=1)

        for e in self.mj_entries_between(start, end):
            d = self._entry_date(e)
            days[d].append(e)

        for d, lst in days.items():
            lst.sort(
                key=lambda e: (
                    getattr(e, "created_at", datetime.combine(self._entry_date(e), datetime.min.time())),
                    getattr(e, "entry_name", ""),
                    getattr(e, "entry_id_str", ""),
                )
            )
        return days

    def mj_month_calendar(self, year: int, month: int) -> Dict[date, List[Entry]]:
        first = date(year, month, 1)
        start = first - timedelta(days=first.weekday())  # Monday-start grid
        if month == 12:
            next_first = date(year + 1, 1, 1)
        else:
            next_first = date(year, month + 1, 1)
        last = next_first - timedelta(days=1)
        end = last + timedelta(days=(6 - last.weekday()))
        return self.mj_entries_grouped_by_day(start, end)

    def mj_mood_rating_graph(self, type_of_graph: str, start_date: date, end_date: date):
        entries_grouped_by_day = self.mj_entries_grouped_by_day(start_date, end_date)
        rating_graph_info = {}

        if type_of_graph == "line":
            for curr_day, list_of_entries in entries_grouped_by_day.items():
                mood_ratings_sum = 0
                n = len(list_of_entries)
                if n:
                    for curr_entry in list_of_entries:
                        mood_ratings_sum += curr_entry.mood_rating
                    rating_graph_info[curr_day] = mood_ratings_sum / n
                else:
                    rating_graph_info[curr_day] = 0  # sentinel for "no entries"
        elif type_of_graph == "bar":
            for i in range(1, 101):
                rating_graph_info[i] = 0
            for _, list_of_entries in entries_grouped_by_day.items():
                for curr_entry in list_of_entries:
                    rating = curr_entry.mood_rating
                    if 1 <= rating <= 100:
                        rating_graph_info[rating] += 1
        return rating_graph_info

    # ------------------------------ Tags --------------------------------

    def mj_all_tags(self):
        """Return sorted list of all unique tags, from DB."""
        tags = db.session.query(Tag).order_by(Tag.name.asc()).all()
        return [t.name for t in tags]

    def mj_entries_with_tag(self, tag: str) -> List[Entry]:
        """Return entries having the given tag (sorted by date/name)."""
        tag = (tag or "").strip().lower()
        if not tag:
            return []
        rows = (
            db.session.query(JournalEntry)
            .join(JournalEntry.tags)
            .filter(Tag.name == tag)
            .order_by(JournalEntry.entry_date.asc(), JournalEntry.title.asc(), JournalEntry.created_at.asc())
            .all()
        )
        entries = [self._model_to_entry(r) for r in rows]
        # Sync cache (optional but keeps things consistent)
        for e in entries:
            self.entries_dict[e.entry_id_str] = e
        return entries

    def mj_tag_summary(self):
        """
        Return list of (tag, count) from DB.
        """
        # Simple approach: fetch and count in Python.
        rows = (
            db.session.query(JournalEntry)
            .options()
            .all()
        )
        counts: Dict[str, int] = {}
        for r in rows:
            for t in (r.tags or []):
                counts[t.name] = counts.get(t.name, 0) + 1
        return sorted(counts.items(), key=lambda kv: (-kv[1], kv[0]))

    # ----------------------- Emoji/rating helpers -----------------------

    def mj_emoji_groups(self, emoji: int):
        """Return (ratingCount[100], [entry_ids]) for entries with given emoji rank."""
        self._hydrate_from_db()
        keys: List[str] = []
        ratingCount = [0] * 100
        for eid, e in self.entries_dict.items():
            if e.ranking == emoji:
                keys.append(eid)
                if 1 <= e.mood_rating <= 100:
                    ratingCount[e.mood_rating - 1] += 1
        return ratingCount, keys

    # -------------------------- Danger zone -----------------------------

    def mj_clear_all_data(self):
        """
        Danger: wipes all journal data.
        Uses bulk deletes for speed; cascades will remove biometrics/links.
        """
        try:
            # Clear association table & biometrics via cascade by deleting entries
            db.session.query(JournalEntry).delete(synchronize_session=False)
            # Keep Tag catalog, or wipe if you prefer:
            # db.session.query(Tag).delete(synchronize_session=False)
            db.session.commit()
        except Exception:
            db.session.rollback()
            raise
        finally:
            self.entries_dict.clear()
            self.recompute_streak()
