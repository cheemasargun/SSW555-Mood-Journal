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
from typing import Optional

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

    def mj_log_entry(self, entry_name: str, entry_day: int, entry_month: int, entry_year: int,
                 entry_body: str, ranking: int, tags=None) -> str:
        """
        Create an entry and update the streaks. Returns the new entry's id.
        """
        entry_id = self.mj_create_entry(entry_name, entry_day, entry_month, entry_year, entry_body, ranking, tags)
        new_entry = self.mj_get_entry(entry_id)
        self.update_streak(new_entry.entry_date)
        return entry_id

    def mj_create_entry(self, entry_name: str, entry_day: int, entry_month: int, entry_year: int, entry_body: str, ranking: int, tags=None):
        new_entry = Entry(entry_name, entry_day, entry_month, entry_year, entry_body, ranking, tags)
        new_entry_id = new_entry.entry_id_str
        self.entries_dict[new_entry_id] = new_entry
        self.recompute_streak()
        return new_entry_id

    def mj_edit_entry(self, entry_id_str: str, new_name: str, new_day: int, new_month: int, new_year: int, new_body: str, new_ranking: int):
        (self.entries_dict[entry_id_str]).edit_entry(new_name, new_day, new_month, new_year, new_body, new_ranking)

    def mj_delete_entry(self, entry_id_str: str):
        # I imagine this would search for an entry's unique id and remove it from the database.

        # We can probably have this implemented using a dictionary if the database might take
        # a sec to understand/get set up properly.

        # We can work together on making this database-based later

        # In the meantime: use the del statement to delete the entry of the given entry_id from
        # self.entries_dict // example of formatting: del my_dict[id]

        if entry_id_str in self.entries_dict:
            del self.entries_dict[entry_id_str]
            self.recompute_streak()
            return True
        else:
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
