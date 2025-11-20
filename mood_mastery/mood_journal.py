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
from mood_mastery.entry import Entry
from typing import Optional, Dict, List, Tuple
import json

class Mood_Journal:
    # Attributes (TO BE UPDATED) (if we need attributes here, really)
    entries_dict = {}
    streak_current = 0
    streak_longest = 0
    last_entry_date : Optional[date] = None

    def __init__(self):
        # TODO
        # This is likely where we'll try to get the database file/instance, or create one if it doesn't exist
        # we can work on this together to get it set up and then be able to create tests.

        # In the meantime, maybe just creating a dictionary to store all of the entries could be good
        # so we can at least test the general logic of the methods in entry.py and some kind of implementation for
        # delete_entry, even if not specifically for a database just yet
        
        self.entries_dict = {}
        self.streak_current = 0
        self.streak_longest = 0
        self.last_entry_date = None

        try:
            from flask import current_app
            from models import MoodEntry
            
            with current_app.app_context():
                rows = MoodEntry.query.order_by(MoodEntry.entry_date.asc(), MoodEntry.created_at.asc()).all()
                for row in rows:
                    entry = row.to_entry()
                    self.entries_dict[entry.entry_id_str] = entry
    
                self.recompute_streak()
        except RuntimeError:
        # No app context available (e.g., during testing)
        # Just initialize with empty data
            pass

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
        # Fallback: today (shouldn't happen if Entry is consistent)
        return date.today()

    def _entry_date(self, e: Entry) -> date:
        return self._to_date(e.entry_date)
        
    def mj_log_entry(self, entry_name: str, entry_day: int, entry_month: int, entry_year: int,
                 entry_body: str, ranking: int, mood_rating: int, tags=None, biometrics=None) -> str:
        """
        Create an entry and update the streaks. Returns the new entry's id.
        """
        entry_id = self.mj_create_entry(entry_name, entry_day, entry_month, entry_year, entry_body, ranking, mood_rating, tags,biometrics)
        new_entry = self.mj_get_entry(entry_id)
        self.update_streak(new_entry.entry_date)
        return entry_id

    def mj_create_entry(self, entry_name: str, entry_day: int, entry_month: int, entry_year: int, entry_body: str, ranking: int, mood_rating: int, tags=None,biometrics=None):
        new_entry = Entry(entry_name, entry_day, entry_month, entry_year, entry_body, ranking, mood_rating, tags, biometrics)
        new_entry_id = new_entry.entry_id_str
        self.entries_dict[new_entry_id] = new_entry

        # added functionality for database
        row = MoodEntry.from_entry(new_entry)
        db.session.add(row)
        db.session.commit()

        self.recompute_streak()
        return new_entry_id

    # rewrote this to integrate with database
    def mj_edit_entry(self, entry_id_str: str, new_name: str, new_day: int, new_month: int, new_year: int, new_body: str, new_ranking: int, new_mood_rating: int):
        # 1) Update in-memory Entry (existing behavior)
        entry = self.entries_dict.get(entry_id_str)
        if not entry:
            return False  # no such entry in memory

        entry.edit_entry(
            new_name,
            new_day,
            new_month,
            new_year,
            new_body,
            new_ranking,
            new_mood_rating,
        )

        # 2) Update streaks if date changed
        self.recompute_streak()

        # 3) Update the DB row
        row = MoodEntry.query.get(entry_id_str)
        if not row:
            # Optional: if DB somehow missing, recreate it from the updated Entry
            row = MoodEntry.from_entry(entry)
            db.session.add(row)
        else:
            # Keep DB fields in sync with Entry
            row.entry_name = entry.entry_name
            row.entry_date = entry.entry_date
            row.entry_body = entry.entry_body
            row.ranking = entry.ranking
            row.mood_rating = entry.mood_rating
            row.is_private = entry.is_private
            row.tags_raw = ",".join(entry.tags) if entry.tags else None
            row.biometrics_raw = json.dumps(entry.biometrics) if entry.biometrics else None

        db.session.commit()
        return True
        

    def mj_delete_entry(self, entry_id_str: str):
        # I imagine this would search for an entry's unique id and remove it from the database.

        # We can probably have this implemented using a dictionary if the database might take
        # a sec to understand/get set up properly.

        # We can work together on making this database-based later

        # In the meantime: use the del statement to delete the entry of the given entry_id from
        # self.entries_dict // example of formatting: del my_dict[id]

        removed = False
        
        if entry_id_str in self.entries_dict:
            del self.entries_dict[entry_id_str]
            removed = True
            
        # 2) Remove from the database
        row = MoodEntry.query.get(entry_id_str)
       
        if row:
            db.session.delete(row)
            db.session.commit()
            removed = True

        # 3) Recompute streak after deletion
        if removed:
            self.recompute_streak()

        return removed

    def mj_get_entry(self, entry_id_str: str):
        """
        Returns the Entry object of id entry_id_str if such an entry exists.
        Otherwise, returns False.

        Parameters -------------------------
        - entry_id_str : str        // The id of the Entry object the user wishes to search for
        """
        if entry_id_str in self.entries_dict:
            return self.entries_dict[entry_id_str]
        else:
            return False # No such entry exists
        
    def mj_get_entry_privacy_status(self, entry_id_str: str):
        """
        Returns the privacy status of an Entry of entry_id_str if such an entry exists.
        Otherwise, returns None.

        Parameters -------------------------
        - entry_id_str : str        // The id of the Entry object the user wishes to search for
        """
        if(self.mj_get_entry(entry_id_str) ==  False):
            return None # No such entry exists
        else:
            # Returns true if entry is private; False if not
            return self.mj_get_entry(entry_id_str).is_private_check()
        
    "Returns all the mood entries"
    def mj_get_all_entries(self):
        return list(self.entries_dict.values())
    
    """Streak System"""
    def recompute_streak(self):
        """
        Recompute current/longest streak from all entries.
        """
        entries = self.mj_get_all_entries()
        if not entries:
            self.streak_current = 0
            self.streak_longest = 0
            self.last_entry_date = None 
            return 
        #get unqiue entry dates
        dates = sorted({e.entry_date for e in entries})
        self.last_entry_date = dates[-1]

        #Longest streak
        longest = 1
        run = 1
        for i in range(1,len(dates)):
            if (dates[i] -dates[i-1]) == timedelta(days=1):
                run +=1
            else:
                longest = max(longest,run)
                run = 1
        longest = max(longest,run)
        #Current streak
        current = 1
        for j in range(len(dates)-1,0,-1):
            if(dates[j] - dates[j-1]) == timedelta(days=1):
                current +=1 
            else:
                break
        self.streak_current = current
        self.streak_longest = longest
        
    def get_streak_summary(self):
        return {
            "current_streak": self.streak_current,
            "longest_streak": self.streak_longest,
            "last_entry_date": self.last_entry_date
        }
    
    def update_streak(self, entry_date: date):
        "Used by log entry to update streak when entry is added for that day"
        if self.last_entry_date is None:
            self.last_entry_date = entry_date
            self.streak_current = 1
            self.streak_longest = max(self.streak_longest,self.streak_current)
            return
        if entry_date == self.last_entry_date:
            return #entry already logged that day
        if entry_date == self.last_entry_date + timedelta(days=1):
            self.streak_current += 1
            self.last_entry_date = entry_date
            self.streak_longest = max(self.streak_longest,self.streak_current)
            return
        if entry_date > self.last_entry_date +timedelta(days=1):
            #A gap breaks the current streak
            self.streak_current = 1
            self.last_entry_date = entry_date
            self.streak_longest = max(self.streak_longest,self.streak_current)
            return
        #Else, recompute just incase
        self.recompute_streak()

    def mj_weekly_report(self, curr_day, curr_month, curr_year):
        curr_date = date(curr_year, curr_month, curr_day)
        weekly_dates = []

        for i in range(7):
            weekly_dates.append(curr_date - timedelta(days = i))
        
        entries_to_report = []

        for i in self.entries_dict.keys():
            for d in weekly_dates:
                if self.entries_dict[i].entry_date == d:
                    entries_to_report.append(i)
        
        emoji_count =  [0, 0, 0, 0, 0, 0, 0, 0]

        if len(entries_to_report) == 0:
            return None
        else:
            for i in entries_to_report:
                emoji_count[self.entries_dict[i].ranking - 1] += 1
            return emoji_count
    
    def mj_monthly_report(self, curr_day, curr_month, curr_year):
        curr_date = date(curr_year, curr_month, curr_day)
        monthly_dates = []

        for i in range(30):
            monthly_dates.append(curr_date - timedelta(days = i))
        
        entries_to_report = []

        for i in self.entries_dict.keys():
            for d in monthly_dates:
                if self.entries_dict[i].entry_date == d:
                    entries_to_report.append(i)
        
        emoji_count =  [0, 0, 0, 0, 0, 0, 0, 0]

        if len(entries_to_report) == 0:
            return None
        else:
            for i in entries_to_report:
                emoji_count[self.entries_dict[i].ranking - 1] += 1
            return emoji_count

    def mj_entries_on(self, year: int, month: int, day: int) -> List[Entry]:
        """
        UI selects a date → return entries for that date
        """
        target = date(year, month, day)
        items = [e for e in self.entries_dict.values() if self._entry_date(e) == target]
    
        items.sort(key=lambda e: (
            getattr(e, "created_at", datetime.combine(self._entry_date(e), datetime.min.time())),
            getattr(e, "entry_name", ""),
            getattr(e, "entry_id_str", "")
        ))
        return items

    def mj_entries_between(self, start: date, end: date) -> List[Entry]:
        """
        Return all entries where start <= entry_date <= end, sorted by date then created_at.
        """
        items = []
        for e in self.entries_dict.values():
            d = self._entry_date(e)
            if start <= d <= end:
                items.append(e)
        items.sort(key=lambda e: (
            self._entry_date(e),
            getattr(e, "created_at", datetime.combine(self._entry_date(e), datetime.min.time())),
            getattr(e, "entry_id_str", "")
        ))
        return items

    def mj_entries_grouped_by_day(self, start: date, end: date) -> Dict[date, List[Entry]]:
        """
        Calendar-friendly structure: {date: [entries...]}, including empty days in range.
        """
        # all days start with empty lists so the UI can render blanks for no-entry dates
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
            lst.sort(key=lambda e: (
                getattr(e, "created_at", datetime.combine(self._entry_date(e), datetime.min.time())),
                getattr(e, "entry_name", ""),
                getattr(e, "entry_id_str", "")
            ))
        return days

    def mj_month_calendar(self, year: int, month: int) -> Dict[date, List[Entry]]:
        """
        give the whole visible month grid (from the calendar’s first weekday to last).
        """
        # First of month
        first = date(year, month, 1)
        # Start on Monday (ISO) for backend; align with UI if it uses Sunday
        start = first - timedelta(days=(first.weekday()))  # weekday(): Mon=0..Sun=6
        # Compute last day of month
        if month == 12:
            next_first = date(year + 1, 1, 1)
        else:
            next_first = date(year, month + 1, 1)
        last = next_first - timedelta(days=1)
        # End on Sunday to close the grid
        end = last + timedelta(days=(6 - last.weekday()))
        return self.mj_entries_grouped_by_day(start, end)

    def mj_mood_rating_graph(self, type_of_graph: str, start_date: date, end_date: date):
        """
        Returns a dictionary representing the mood_rating information from start_date to end_date for either a:
            - Line graph showing all mood_ratings across the period of time
                Graph details: (x axis = dates from start_date to end_date, y axis = ratings from 1 to 100)
                Dictionary format: { start_date (date) : start_date_mood_ratings_avg (int), ..., end_date (date) : end_date_mood_ratings_avg (int) }
            or
            - Bar graph showing frequency of different mood_ratings during the period of time
                Graph details: (x axis = ratings from 1 to 100, y axis = amount of times the rating occurred during the period of time)
                Dictionary format: { 1 : amount_of_1s (int), ..., 100 : amount_of_100s (int) } 

        Parameters -------------------------
        - type_of_graph : str       // The type of graph the user wishes to see
        - start_date : date         // The beginning of the time period the user wants to see their mood_ratings for
        - end_date : date           // The ending of the time period the user wants to see their mood_ratings for
        """
        entries_grouped_by_day = self.mj_entries_grouped_by_day(start_date, end_date)
        
        rating_graph_info = {}
        
        if type_of_graph == "line":
            for curr_day, list_of_entries in entries_grouped_by_day.items():
                # Setting mood_ratings_avg to 0 (an invalid mood_rating value) by default; indicates no entries for the day
                mood_ratings_avg = 0

                if len(list_of_entries) >= 1:
                    # Getting average of mood_ratings if there's at least 1 entry for the day
                    for curr_entry in list_of_entries:
                        mood_ratings_avg += curr_entry.mood_rating
                    mood_ratings_avg = mood_ratings_avg / len(list_of_entries)
                
                rating_graph_info[curr_day] = mood_ratings_avg

        elif type_of_graph == "bar":
            # Initializing rating_graph_info to have a count for each rating (1 to 100)
            for i in range(1,101):
                rating_graph_info[i] = 0
            
            # Iterating through every day's entries, and incrementing the count for each encountered mood_rating accordingly
            for curr_day, list_of_entries in entries_grouped_by_day.items():
                for curr_entry in list_of_entries:
                    curr_rating = curr_entry.mood_rating
                    rating_graph_info[curr_rating] = rating_graph_info[curr_rating] + 1
        
        return rating_graph_info
    #Organize tags 
    def mj_all_tags(self):
        """Returns sorted list of all unique tags"""
        tag_set: set[str] = set()
        for e in self.entries_dict.values():
            # Entry.tags is already cleaned (lowercased, stripped) by Entry.add_tag
            for t in getattr(e, "tags", []):
                tag_set.add(t)
        return sorted(tag_set)
    def mj_entries_with_tag(self, tag):
        """Returns all entries with given tag sorted by date and name"""
        items: list[Entry] = []
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
        """Returns a list of  pairs summarizing how often a tag is used"""
        counts: dict[str, int] = {}
        for e in self.entries_dict.values():
            for t in getattr(e, "tags", []):
                counts[t] = counts.get(t, 0) + 1

        # Convert to sorted list of (tag, count)
        return sorted(counts.items(), key=lambda kv: (-kv[1], kv[0]))
    
    #takes into account ranking(emoji), mood rating(scale from 1-100)
    def mj_emoji_groups(self, emoji):
        #creates a list with the keys of every entry that has a given emoji
        keys = []
        ratingCount = [0] * 100

        for i in self.entries_dict.keys():
            if self.entries_dict[i].ranking == emoji:
                ratingCount[self.entries_dict[i].mood_rating - 1] += 1
                keys.append(i)

        return ratingCount, keys
    
    def mj_clear_all_data(self):
        self.entries_dict.clear()
        # Clear DB as well
        MoodEntry.query.delete()
        db.session.commit()
        self.recompute_streak()
        
        


