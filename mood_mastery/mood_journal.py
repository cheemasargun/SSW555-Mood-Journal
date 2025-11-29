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
from models import MoodEntry
import json
from typing import Optional, Dict, List, Tuple

class Mood_Journal:
    def __init__(self, use_database=True):
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
        self.use_database = use_database
        self._db_loaded = False

    def _get_app(self):
        """Safely get the Flask app from db"""
        return getattr(db, 'app', None)
        
    def _ensure_db_loaded(self, app=None):
        """Lazy load from database when needed"""
        if not self._db_loaded and self.use_database:
        app = self._get_app()
        if app:
            try:
                with app.app_context():
                    db_entries = MoodEntry.query.all()
                    for db_entry in db_entries:
                        entry = db_entry.to_entry()
                        self.entries_dict[entry.entry_id_str] = entry
                    self.recompute_streak()
                    self._db_loaded = True
            except Exception as e:
                print(f"Warning: Could not load from database: {e}")
                
    def _load_entries_from_db(self):
        """Load all entries from database into memory"""
        with db.app.app_context():  # Ensure app context
            db_entries = MoodEntry.query.all()
            for db_entry in db_entries:
                entry = db_entry.to_entry()
                self.entries_dict[entry.entry_id_str] = entry

    def _save_entry_to_db(self, entry: Entry):
        """Save to database only if enabled"""
        if not self.use_database:
            return
            
        app = self._get_app()
        if app:
            try:
                with app.app_context():
                    existing = MoodEntry.query.filter_by(entry_id_str=entry.entry_id_str).first()
                    
                    if existing:
                        # Update existing
                        existing.entry_name = entry.entry_name
                        existing.entry_date = entry.entry_date
                        existing.ranking = entry.ranking
                        existing.mood_rating = entry.mood_rating
                        existing.difficulty_ranking = getattr(entry, 'difficulty_ranking', 3)
                        existing.entry_body = entry.entry_body
                        existing.tags_raw = ",".join(entry.tags) if getattr(entry, "tags", None) else None
                        existing.biometrics_raw = json.dumps(entry.biometrics) if getattr(entry, "biometrics", None) else None
                        existing.is_private = getattr(entry, 'is_private', False)
                    else:
                        # Create new
                        db_entry = MoodEntry.from_entry(entry)
                        db.session.add(db_entry)
                    
                    db.session.commit()
            except Exception as e:
                print(f"Warning: Could not save to database: {e}")

    def _delete_entry_from_db(self, entry_id_str: str):
        """Delete from database only if enabled"""
        if not self.use_database:
            return
            
        app = self._get_app()
        if app:
            try:
                with app.app_context():
                    entry = MoodEntry.query.filter_by(entry_id_str=entry_id_str).first()
                    if entry:
                        db.session.delete(entry)
                        db.session.commit()
            except Exception as e:
                print(f"Warning: Could not delete from database: {e}")


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
                 entry_body: str, ranking: int, mood_rating: int, difficulty_ranking: int, tags=None, biometrics=None) -> str:
        """
        Create an entry and update the streaks. Returns the new entry's id.
        """
        entry_id = self.mj_create_entry(entry_name, entry_day, entry_month, entry_year, entry_body, ranking, mood_rating, difficulty_ranking, tags, biometrics)
        new_entry = self.mj_get_entry(entry_id)
        self.update_streak(new_entry.entry_date)
        return entry_id

    def mj_create_entry(self, entry_name: str, entry_day: int, entry_month: int, entry_year: int, entry_body: str, ranking: int, mood_rating: int, difficulty_ranking: int, tags=None,biometrics=None):
        new_entry = Entry(entry_name, entry_day, entry_month, entry_year, entry_body, ranking, mood_rating, difficulty_ranking, tags, biometrics)
        new_entry_id = new_entry.entry_id_str
        self.entries_dict[new_entry_id] = new_entry
        self._save_entry_to_db(new_entry)
        
        self.recompute_streak()
        return new_entry_id

    def mj_edit_entry(self, entry_id_str: str, new_name: str, new_day: int, new_month: int, new_year: int, new_body: str, new_ranking: int, new_mood_rating: int, new_difficulty_ranking: int):
        entry = self.entries_dict[entry_id_str]
        entry.edit_entry(new_name, new_day, new_month, new_year, new_body, new_ranking, new_mood_rating, new_difficulty_ranking)
        # Update database if enabled
        self._save_entry_to_db(entry)

    def mj_delete_entry(self, entry_id_str: str):
        # I imagine this would search for an entry's unique id and remove it from the database.

        # We can probably have this implemented using a dictionary if the database might take
        # a sec to understand/get set up properly.

        # We can work together on making this database-based later

        # In the meantime: use the del statement to delete the entry of the given entry_id from
        # self.entries_dict // example of formatting: del my_dict[id]

        if entry_id_str in self.entries_dict:
            # Delete from database if enabled
            self._delete_entry_from_db(entry_id_str)
            # Delete from memory
            del self.entries_dict[entry_id_str]
            self.recompute_streak()
            return True
        return False

    def mj_get_entry(self, entry_id_str: str):
        """
        Returns the Entry object of id entry_id_str if such an entry exists.
        Otherwise, returns False.

        Parameters -------------------------
        - entry_id_str : str        // The id of the Entry object the user wishes to search for
        """
        if entry_id_str in self.entries_dict:
            return self.entries_dict[entry_id_str]
        
        # If not found, try loading from database
        self._ensure_db_loaded()
        return self.entries_dict.get(entry_id_str, False)
        
    def mj_get_entry_privacy_status(self, entry_id_str: str):
        """
        Returns the privacy status of an Entry of entry_id_str if such an entry exists.
        Otherwise, returns None.

        Parameters -------------------------
        - entry_id_str : str        // The id of the Entry object the user wishes to search for
        """
        self._ensure_db_loaded()
        if(self.mj_get_entry(entry_id_str) ==  False):
            return None # No such entry exists
        else:
            # Returns true if entry is private; False if not
            return self.mj_get_entry(entry_id_str).is_private_check()
        
    "Returns all the mood entries"
    def mj_get_all_entries(self):
        self._ensure_db_loaded()
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
        self._ensure_db_loaded()
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
        self._ensure_db_loaded()
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
        self._ensure_db_loaded()
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
        self._ensure_db_loaded()
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
        self._ensure_db_loaded()
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
        self._ensure_db_loaded()
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
        self._ensure_db_loaded()
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
        self._ensure_db_loaded()
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
        self._ensure_db_loaded()
        tag_set: set[str] = set()
        for e in self.entries_dict.values():
            # Entry.tags is already cleaned (lowercased, stripped) by Entry.add_tag
            for t in getattr(e, "tags", []):
                tag_set.add(t)
        return sorted(tag_set)
    def mj_entries_with_tag(self, tag):
        """Returns all entries with given tag sorted by date and name"""
        self._ensure_db_loaded()
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
        self._ensure_db_loaded()
        counts: dict[str, int] = {}
        for e in self.entries_dict.values():
            for t in getattr(e, "tags", []):
                counts[t] = counts.get(t, 0) + 1

        # Convert to sorted list of (tag, count)
        return sorted(counts.items(), key=lambda kv: (-kv[1], kv[0]))
    
    #takes into account ranking(emoji), mood rating(scale from 1-100)
    def mj_emoji_groups(self, emoji):
        #creates a list with the keys of every entry that has a given emoji
        self._ensure_db_loaded()
        keys = []
        ratingCount = [0] * 100

        for i in self.entries_dict.keys():
            if self.entries_dict[i].ranking == emoji:
                ratingCount[self.entries_dict[i].mood_rating - 1] += 1
                keys.append(i)

        return ratingCount, keys
    
    def mj_clear_all_data(self):
        self.entries_dict.clear()
        if self.use_database:
            app = self._get_app()
            if app:
                try:
                    with app.app_context():
                        MoodEntry.query.delete()
                        db.session.commit()
                except Exception as e:
                    print(f"Warning: Could not clear database: {e}")
        self.streak_current = 0
        self.streak_longest = 0
        self.last_entry_date = None

    def mj_mood_graph_trends(self):
        """
        Returns a dictionary listing mood_rating trends:
            - Weekly: (ON AVERAGE) on which day of the week the user's mood tends to be HIGHEST (HAPPIEST) and on which it tends to be LOWEST (SADDEST)
            - Monthly: (ON AVERAGE) during which third of the month the user's mood tends to be HIGHEST (HAPPIEST) and during which third it tends to be LOWEST (SADDEST)
            - Yearly: (ON AVERAGE) during which month the user's mood tends to be HIGHEST (HAPPIEST) and during which the user's mood tends to be LOWEST (SADDEST)
        
        Dictionary format: { happiest_day_of_week (str)     : [ happiest_day_of_week (str), happiest_day_of_week_avg (float) ],
                             saddest_day_of_week (str)      : [ saddest_day_of_week (str), saddest_day_of_week_avg (float) ],
                             happiest_time_of_month (str)   : [ happiest_time_of_month (str), happiest_time_of_month_avg (float) ],
                             saddest_time_of_month (str)    : [ saddest_time_of_month (str), saddest_time_of_month_avg (float) ],
                             happiest_month_of_year (str)   : [ happiest_month_of_year (str), happiest_month_of_year_avg (float) ],
                             saddest_month_of_year (str)    : [ saddest_month_of_year (str), saddest_month_of_year_avg (float) ],
                            }
            
        Parameters -------------------------
        (None)
        """
        self._ensure_db_loaded()
        mood_ratings_by_day_of_week = { "Monday": [], "Tuesday" : [], "Wednesday" : [],
                                        "Thursday" : [], "Friday" : [], "Saturday" : [], "Sunday" : [] }
        mood_ratings_by_time_of_month = { "First third" : [], "Second third" : [], "Last third": [] }
        mood_ratings_by_month_of_year = { "January" : [], "February" : [], "March" : [],
                                          "April" : [], "May" : [], "June" : [],
                                          "July" : [], "August" : [], "September" : [],
                                          "October" : [], "November" : [], "December" : [] }

        # Sorting all entries by day of the week // day of the month range (1-10, 11-20, 20-onward) // month of the year
        for entry in self.entries_dict.values():
            entry_day_of_week_num = entry.entry_date.weekday() # 0 = Monday, ..., 6 = Sunday
            entry_day_of_month = entry.entry_date.day
            entry_month = entry.entry_date.month # 1 = January, ..., 12 = December

            match entry_day_of_week_num:
                case 0: mood_ratings_by_day_of_week["Monday"].append(entry.mood_rating)
                case 1: mood_ratings_by_day_of_week["Tuesday"].append(entry.mood_rating)
                case 2: mood_ratings_by_day_of_week["Wednesday"].append(entry.mood_rating)
                case 3: mood_ratings_by_day_of_week["Thursday"].append(entry.mood_rating)
                case 4: mood_ratings_by_day_of_week["Friday"].append(entry.mood_rating)
                case 5: mood_ratings_by_day_of_week["Saturday"].append(entry.mood_rating)
                case 6: mood_ratings_by_day_of_week["Sunday"].append(entry.mood_rating)

            if entry_day_of_month < 11:
                mood_ratings_by_time_of_month["First third"].append(entry.mood_rating)
            elif entry_day_of_month < 21:
                mood_ratings_by_time_of_month["Second third"].append(entry.mood_rating)
            else:
                mood_ratings_by_time_of_month["Last third"].append(entry.mood_rating)

            match entry_month:
                case 1: mood_ratings_by_month_of_year["January"].append(entry.mood_rating)
                case 2: mood_ratings_by_month_of_year["February"].append(entry.mood_rating)
                case 3: mood_ratings_by_month_of_year["March"].append(entry.mood_rating)
                case 4: mood_ratings_by_month_of_year["April"].append(entry.mood_rating)
                case 5: mood_ratings_by_month_of_year["May"].append(entry.mood_rating)
                case 6: mood_ratings_by_month_of_year["June"].append(entry.mood_rating)
                case 7: mood_ratings_by_month_of_year["July"].append(entry.mood_rating)
                case 8: mood_ratings_by_month_of_year["August"].append(entry.mood_rating)
                case 9: mood_ratings_by_month_of_year["September"].append(entry.mood_rating)
                case 10: mood_ratings_by_month_of_year["October"].append(entry.mood_rating)
                case 11: mood_ratings_by_month_of_year["November"].append(entry.mood_rating)
                case 12: mood_ratings_by_month_of_year["December"].append(entry.mood_rating)
                
        mood_rating_day_of_week_avgs = { "Monday": 0, "Tuesday" : 0, "Wednesday" : 0,
                                        "Thursday" : 0, "Friday" : 0, "Saturday" : 0, "Sunday" : 0 }
        mood_ratings_time_of_month_avgs = { "First third" : 0, "Second third" : 0, "Last third": 0 }
        mood_rating_month_of_year_avgs = { "January" : 0, "February" : 0, "March" : 0,
                                          "April" : 0, "May" : 0, "June" : 0,
                                          "July" : 0, "August" : 0, "September" : 0,
                                          "October" : 0, "November" : 0, "December" : 0 }
        
        # Calculating average mood rating for each day of the week
        for day in mood_ratings_by_day_of_week.keys():
            if len(mood_ratings_by_day_of_week[day]) != 0:
                mood_rating_day_of_week_avgs[day] = sum(mood_ratings_by_day_of_week[day]) / len(mood_ratings_by_day_of_week[day])

        # Calculating average mood rating for each day of the month range (1-10, 11-20, 20-onward)
        for time_of_month in mood_ratings_by_time_of_month.keys():
            if len(mood_ratings_by_time_of_month[time_of_month]) != 0:
                mood_ratings_time_of_month_avgs[time_of_month] = sum(mood_ratings_by_time_of_month[time_of_month]) / len(mood_ratings_by_time_of_month[time_of_month])

        # Calculating average mood rating for each month of the year
        for month in mood_ratings_by_month_of_year.keys():
            if len(mood_ratings_by_month_of_year[month]) != 0:
                mood_rating_month_of_year_avgs[month] = sum(mood_ratings_by_month_of_year[month]) / len(mood_ratings_by_month_of_year[month])
        
        # Finding highest (happiest) and lowest (saddest) mood rating for each category
        happiest_day_of_week_avg = 0
        saddest_day_of_week_avg = 999
        happiest_day_of_week = ""
        saddest_day_of_week = ""
        for day, avg in mood_rating_day_of_week_avgs.items():
            if len(mood_ratings_by_day_of_week[day]) > 0:
                if avg > happiest_day_of_week_avg:
                    happiest_day_of_week_avg = avg
                    happiest_day_of_week = day
                elif avg == happiest_day_of_week_avg:
                    happiest_day_of_week += ", " + day

                if avg < saddest_day_of_week_avg:
                    saddest_day_of_week_avg = avg
                    saddest_day_of_week = day
                elif avg == saddest_day_of_week_avg:
                    saddest_day_of_week += ", " + day

        happiest_time_of_month_avg = 0
        saddest_time_of_month_avg = 999
        happiest_time_of_month = ""
        saddest_time_of_month = ""
        for time_of_month, avg in mood_ratings_time_of_month_avgs.items():
            if len(mood_ratings_by_time_of_month[time_of_month]) > 0:
                if avg > happiest_time_of_month_avg:
                    happiest_time_of_month_avg = avg
                    happiest_time_of_month = time_of_month
                elif avg == happiest_time_of_month_avg:
                    happiest_time_of_month = happiest_time_of_month + ", " + time_of_month
                
                if avg < saddest_time_of_month_avg:
                    saddest_time_of_month_avg = avg
                    saddest_time_of_month = time_of_month
                elif avg == saddest_time_of_month_avg:
                    saddest_time_of_month = saddest_time_of_month + ", " + time_of_month
                
        happiest_month_of_year_avg = 0
        saddest_month_of_year_avg = 999
        happiest_month_of_year = ""
        saddest_month_of_year = ""
        for month_of_year, avg in mood_rating_month_of_year_avgs.items():
            if len(mood_ratings_by_month_of_year[month_of_year]) > 0:
                if avg > happiest_month_of_year_avg:
                    happiest_month_of_year_avg = avg
                    happiest_month_of_year = month_of_year
                elif avg == happiest_month_of_year_avg:
                    happiest_month_of_year = happiest_month_of_year + ", " + month_of_year
                
                if avg < saddest_month_of_year_avg:
                    saddest_month_of_year_avg = avg
                    saddest_month_of_year = month_of_year
                elif avg == saddest_month_of_year_avg:
                    saddest_month_of_year = saddest_month_of_year + ", " + month_of_year

        mood_graph_trends = { "happiest_day_of_week" : [ happiest_day_of_week, happiest_day_of_week_avg ],
                             "saddest_day_of_week" : [ saddest_day_of_week, saddest_day_of_week_avg ],
                             "happiest_time_of_month" : [ happiest_time_of_month, happiest_time_of_month_avg ],
                             "saddest_time_of_month" : [ saddest_time_of_month, saddest_time_of_month_avg ],
                             "happiest_month_of_year" : [ happiest_month_of_year, happiest_month_of_year_avg ],
                             "saddest_month_of_year" : [ saddest_month_of_year, saddest_month_of_year_avg ] }
        
        return mood_graph_trends
