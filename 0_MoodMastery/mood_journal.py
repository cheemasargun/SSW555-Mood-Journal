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
from datetime import datetime

class Mood_Journal:
    # Attributes (TO BE UPDATED) (if we need attributes here, really)

    def __init__(self):
        # TODO
        # This is likely where we'll try to get the database file/instance, or create one if it doesn't exist
        # we can work on this together to get it set up and then be able to create tests.

        # In the meantime, maybe just creating a dictionary or JSON file to store all of the entries could be good
        # so we can at least test the general logic of the methods in entry.py and some kind of implementation for
        # delete_entry, even if not specifically for a database just yet
        pass

    def delete_entry(entry_id: int):
        # TODO
        # I imagine this would search for an entry's unique id and remove it from the database.

        # We can probably have this implemented using a dictionary or JSON file if the database might take
        # a sec to understand/get set up properly.

        # We can work together on making this database-based
        pass