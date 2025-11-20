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

from extensions import db
from datetime import datetime, date, timedelta
from typing import Optional, Dict, List

from mood_mastery.entry import Entry        # keep using Entry internally
from models import JournalEntry             # new: DB model


class Mood_Journal:
    # Class attributes (will be shadowed by instance attributes)
    entries_dict: Dict[str, Entry] = {}
    streak_current: int = 0
    streak_longest: int = 0
    last_entry_date: Optional[date] = None

    def __init__(self):
        """
        On creation, load all existing rows from the DB into entries_dict,
        so the app can 'remember' previous entries between runs
        (US-33: Create Database & persist data).
        """
        self.entries_dict = {}
        self.streak_current = 0
        self.streak_longest = 0
        self.last_entry_date = None

        # Load from the database if tables exist and app context is active.
        try:
            rows = (
                JournalEntry.query
                .order_by(JournalEntry.entry_date.asc(), JournalEntry.created_at.asc())
                .all()
            )
        except Exception:
            # In tests or environments without DB setup, just skip loading
            rows = []

        for row in rows:
            # Rebuild Entry from JournalEntry fields
            d = row.entry_date
            e = Entry(
                row.entry_name,
                d.day,
                d.month,
                d.year,
                row.body or "",
                row.ranking,
                row.mood_rating,
                tags=row.tags.split(",") if row.tags else None,
                biometrics=row.biometrics or None,
            )
            # Keep the DB id_str so lookups are consistent
            e.entry_id_str = row.entry_id_str
            # Attach created_at for ordering
            setattr(e, "created_at", row.created_at or datetime.combine(d, datetime.min.time()))
            self.entries_dict[e.entry_id_str] = e

        # Ensure streaks reflect persisted entries
        self.recompute_streak()

    # ---------- Helpers ----------

    def _to_date(self, d) -> date:
        """
        Normalize various date shapes to datetime.date.
        Supports:
          - datetime.date
          - (day, month, year) tuple
          - Entry.entry_date as either of the above
        """
        if isinstance(d, date):
            return d
        if isinstance(d, tuple) and len(d) == 3:
            day, month, year = d
            return date(year, month, day)
        return date.today()

    def _entry_date(self, e: Entry) -> date:
        return self._to_date(e.entry_date)

    # ---------- Create / Log / Edit / Delete (US-33 & US-34) ----------

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
        """
        High-level helper used by UI:
        - creates an entry (and persists it)
        - updates streaks
        - returns the entry_id_str
        """
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
            self.update_streak(new_entry.entry_date)
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
        Creates a new Entry object, stores it in memory and in the database.

        This satisfies US-33:
        - Data is stored persistently in the DB
        - When the user returns, entries can be reloaded from the DB
        """
        # 1) Build Entry object (your original behavior)
        new_entry = Entry(
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

        # Ensure a created_at timestamp exists for sorting / history
        if not hasattr(new_entry, "created_at"):
            setattr(new_entry, "created_at", datetime.utcnow())

        new_entry_id = new_entry.entry_id_str
        self.entries_dict[new_entry_id] = new_entry

        # 2) Persist to database (best-effort; if DB fails, in-memory still works)
        try:
            entry_date = self._entry_date(new_entry)
            db_row = JournalEntry(
                entry_id_str=new_entry.entry_id_str,
                entry_name=new_entry.entry_name,
                entry_date=entry_date,
                body=new_entry.entry_body,
                ranking=new_entry.ranking,
                mood_rating=new_entry.mood_rating,
                tags=",".join(new_entry.tags) if getattr(new_entry, "tags", None) else None,
                biometrics=new_entry.biometrics or None,
                created_at=new_entry.created_at,
            )
            db.session.add(db_row)
            db.session.commit()
        except Exception:
            # In CI or environments without DB, we don't want tests to explode
            db.session.rollback()

        # Recompute streaks based on all entries
        self.recompute_streak()
        return new_entry_id

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
    ) -> bool:
        """
        Updates an existing entry both in memory and in the database.

        This satisfies US-34:
        - When the user edits data, the stored version changes
        - Future use shows the updated data
        """
        entry = self.entries_dict.get(entry_id_str)
        if not entry:
            return False

        # Update in-memory Entry
        entry.edit_entry(
            new_name,
            new_day,
            new_month,
            new_year,
            new_body,
            new_ranking,
            new_mood_rating,
        )

        # Recompute streaks (date may have changed)
        self.recompute_streak()

        # Update database row (best-effort)
        try:
            row = JournalEntry.query.filter_by(entry_id_str=entry_id_str).first()
            if row:
                row.entry_name = entry.entry_name
                row.entry_date = self._entry_date(entry)
                row.body = entry.entry_body
                row.ranking = entry.ranking
                row.mood_rating = entry.mood_rating
                row.tags = ",".join(entry.tags) if getattr(entry, "tags", None) else None
                row.biometrics = entry.biometrics or None
                db.session.commit()
            else:
                # If not found (shouldn't happen), recreate row to avoid data loss
                entry_date = self._entry_date(entry)
                new_row = JournalEntry(
                    entry_id_str=entry.entry_id_str,
                    entry_name=entry.entry_name,
                    entry_date=entry_date,
                    body=entry.entry_body,
                    ranking=entry.ranking,
                    mood_rating=entry.mood_rating,
                    tags=",".join(entry.tags) if getattr(entry, "tags", None) else None,
                    biometrics=entry.biometrics or None,
                    created_at=getattr(entry, "created_at", datetime.utcnow()),
                )
                db.session.add(new_row)
                db.session.commit()
        except Exception:
            db.session.rollback()

        return True

    def mj_delete_entry(self, entry_id_str: str) -> bool:
        """
        Deletes an entry from memory and from the DB if present.
        """
        removed = False

        # In-memory
        if entry_id_str in self.entries_dict:
            del self.entries_dict[entry_id_str]
            removed = True

        # Database
        try:
            row = JournalEntry.query.filter_by(entry_id_str=entry_id_str).first()
            if row:
                db.session.delete(row)
                db.session.commit()
                removed = True
        except Exception:
            db.session.rollback()

        if removed:
            self.recompute_streak()

        return removed

    # ---------- Query / Utility methods (unchanged behavior) ----------

    def mj_get_entry(self, entry_id_str: str):
        if entry_id_str in self.entries_dict:
            return self.entries_dict[entry_id_str]
        return False

    def mj_get_entry_privacy_status(self, entry_id_str: str):
        entry = self.mj_get_entry(entry_id_str)
        if not entry:
            return None
        return entry.is_private_check()

    def mj_get_all_entries(self) -> List[Entry]:
        return list(self.entries_dict.values())

    # ---------- Streak System (unchanged) ----------

    def recompute_streak(self):
        entries = self.mj_get_all_entries()
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

        # Current streak
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

    # ---------- Weekly / Monthly Reports, Calendar, Graphs, Tags, Emoji ----------

    def mj_weekly_report(self, curr_day, curr_month, curr_year):
        curr_date = date(curr_year, curr_month, curr_day)
        weekly_dates = [curr_date - timedelta(days=i) for i in range(7)]
        entries_to_report = []

        for key in self.entries_dict.keys():
            for d in weekly_dates:
                if self._entry_date(self.entries_dict[key]) == d:
                    entries_to_report.append(key)

        emoji_count = [0] * 8

        if not entries_to_report:
            return None
        for key in entries_to_report:
            self_idx = self.entries_dict[key].ranking - 1
            if 0 <= self_idx < 8:
                emoji_count[self_idx] += 1
        return emoji_count

    def mj_monthly_report(self, curr_day, curr_month, curr_year):
        curr_date = date(curr_year, curr_month, curr_day)
        monthly_dates = [curr_date - timedelta(days=i) for i in range(30)]
        entries_to_report = []

        for key in self.entries_dict.keys():
            for d in monthly_dates:
                if self._entry_date(self.entries_dict[key]) == d:
                    entries_to_report.append(key)

        emoji_count = [0] * 8

        if not entries_to_report:
            return None
        for key in entries_to_report:
            self_idx = self.entries_dict[key].ranking - 1
            if 0 <= self_idx < 8:
                emoji_count[self_idx] += 1
        return emoji_count

    def mj_entries_on(self, year: int, month: int, day: int) -> List[Entry]:
        target = date(year, month, day)
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

        for e in self.entries_dict.values():
            d = self._entry_date(e)
            if start <= d <= end:
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
        start = first - timedelta(days=first.weekday())
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
                mood_ratings_avg = 0
                if list_of_entries:
                    for curr_entry in list_of_entries:
                        mood_ratings_avg += curr_entry.mood_rating
                    mood_ratings_avg = mood_ratings_avg / len(list_of_entries)
                rating_graph_info[curr_day] = mood_ratings_avg

        elif type_of_graph == "bar":
            for i in range(1, 101):
                rating_graph_info[i] = 0
            for _, list_of_entries in entries_grouped_by_day.items():
                for curr_entry in list_of_entries:
                    curr_rating = curr_entry.mood_rating
                    if 1 <= curr_rating <= 100:
                        rating_graph_info[curr_rating] += 1

        return rating_graph_info

    def mj_all_tags(self):
        tag_set: set[str] = set()
        for e in self.entries_dict.values():
            for t in getattr(e, "tags", []):
                tag_set.add(t)
        return sorted(tag_set)

    def mj_entries_with_tag(self, tag):
        items: List[Entry] = []
        for e in self.entries_dict.values():
            if e.has_tag(tag):
                items.append(e)
        items.sort(
            key=lambda e: (
                self._entry_date(e),
                getattr(e, "entry_name", ""),
                getattr(e, "entry_id_str", ""),
            )
        )
        return items

    def mj_tag_summary(self):
        counts: Dict[str, int] = {}
        for e in self.entries_dict.values():
            for t in getattr(e, "tags", []):
                counts[t] = counts.get(t, 0) + 1
        return sorted(counts.items(), key=lambda kv: (-kv[1], kv[0]))

    def mj_emoji_groups(self, emoji_value: int):
        keys = []
        rating_count = [0] * 100

        for k, e in self.entries_dict.items():
            if e.ranking == emoji_value:
                if 1 <= e.mood_rating <= 100:
                    rating_count[e.mood_rating - 1] += 1
                keys.append(k)

        return rating_count, keys

    def mj_clear_all_data(self):
        self.entries_dict.clear()
        try:
            JournalEntry.query.delete()
            db.session.commit()
        except Exception:
            db.session.rollback()
        self.recompute_streak()
