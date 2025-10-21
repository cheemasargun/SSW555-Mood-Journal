# Any imports we may need (TODO: update as necessary as we implement more things here)
import uuid
from datetime import date
from datetime import datetime
import emoji
# ^ FOR RANKING EMOJI: make sure to run 'pip install emoji'
# ref: https://www.geeksforgeeks.org/python/introduction-to-emoji-module-in-python/
# CTRL+F "emojize" on ref page: emoji.emojize could be useful if we want to use emoji shortcodes (i.e. ":earth_americas:" for the globe emoji with the Americas)

class Entry:
    """
    A class representing a user's entry.

    Attributes -------------------------
     - entry_name : str     // The name assigned to a user's entry
     - entry_date : date    // The date of a user's entry
     - entry_body : str     // The body/main text of a user's entry
     - ranking : int        // The ranking assigned to the entry by a user (TODO: describe valid range if we're doing it numerically in the code + then representing certain value ranges with different emojis)
    """

    # Attributes (TODO: update if we have more features to add to entries)
    entry_id_str = ""
    entry_name = ""
    entry_date = None
    entry_body = ""
    ranking = -999 # CMNT: this default value is for if we want to keep a numerical representation for rankings in the code

    def __init__(self, entry_name: str, entry_day: int, entry_month: int, entry_year: int, entry_body: str, ranking: int):
        """
        Initializes the Entry instance with values for each attribute of the class.

        Parameters -------------------------
        - entry_name : str      // The name assigned to a user's entry
        - entry_day : int       // The day of a user's entry
        - entry_month : int     // The month of a user's entry
        - entry_year : int      // The year of a user's entry
        - entry_body : str      // The body/main text of a user's entry
        - ranking : int         // The ranking assigned to the entry by a user (TODO: describe valid range ^ see line 12)
        """
        self.entry_id_str = uuid.uuid4() # Generating a unique id for the entry
        self.entry_name = entry_name
        self.entry_date = date(entry_year,entry_month,entry_day)
        self.entry_body = entry_body
        self.ranking = ranking

    def edit_entry(self, new_name: str, new_day: int, new_month: int, new_year: int, new_body: str, new_ranking: int):
        """
        Modifies the Entry instance's attributes.

        Parameters -------------------------
        - new_name : str        // The updated name for the user's entry
        - new_day : int         // The updated day for the user's entry
        - new_month : int       // The updated month for the user's entry
        - new_year : int        // The updated year for the user's entry
        - new_body : str        // The updated body/main text of a user's story
        - new_ranking : int     // The updated ranking assigned to the entry (TODO: describe valid range ^ see line 12)
        """
        self.entry_name = new_name
        self.entry_date = date(new_year, new_month, new_day)
        self.entry_body = new_body
        self.ranking = new_ranking

    def determine_ranking_emoji(self):
        """
        Checks the Entry instance's ranking attribute and determines its associated emoji

        Returns string with ranking's associated emoji
        """
        # TODO
        pass

    
        