# Any imports we may need (TODO: update as necessary as we implement more things here)
import uuid
from datetime import date
from datetime import datetime
from typing import Dict, Optional
import emoji

# ^ FOR RANKING EMOJI: make sure to run 'pip install emoji'
# ref: https://www.geeksforgeeks.org/python/introduction-to-emoji-module-in-python/
# CTRL+F "emojize" on ref page: emoji.emojize could be useful if we want to use emoji shortcodes (i.e. ":earth_americas:" for the globe emoji with the Americas)

BIOMETRICS: Dict[str, list[str]] = {
    "Sleep": ["well rested", "meh", "sleepy", "exhausted"],
    "Physical Wellness": ["sick", "been better", "normal", "energized"],
    "Mental Wellness": ["terrible", "been better", "normal", "energized"],
    "Menstruation": ["yes", "no"],
}

class Entry:
    """
    A class representing a user's entry.

    Attributes -------------------------
     - entry_name : str     // The name assigned to a user's entry
     - entry_date : date    // The date of a user's entry
     - entry_body : str     // The body/main text of a user's entry
     - ranking : int        // The ranking assigned to the entry by a user (TODO: describe valid range if we're doing it numerically in the code + then representing certain value ranges with different emojis)
     - is_private : bool    // The privacy status of the entry (True = private; False = public)
    """

    # Attributes (TODO: update if we have more features to add to entries)
    entry_id_str = ""
    entry_name = ""
    entry_date = None
    entry_body = ""
    ranking = -999 # CMNT: this default value is for if we want to keep a numerical representation for rankings in the code
    is_private = None

    def __init__(self, entry_name: str, entry_day: int, entry_month: int, entry_year: int, entry_body: str, ranking: int, tags=None, biometrics: Optional[Dict[str, str]] = None):
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
        self.entry_id_str = str(uuid.uuid4()) # Generating a unique id for the entry
        self.entry_name = entry_name
        self.entry_date = date(entry_year,entry_month,entry_day)
        self.entry_body = entry_body
        self.ranking = ranking
        self.tags: list[str] =[]
        if tags:
            for t in tags:
                self.add_tag(t)
        self.is_private = False # By default, entry is not private
        self.biometrics: Dict[str, str] = {}
        if biometrics:
            self.initialize_biometrics(biometrics)

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

    def initialize_biometrics(self, data: Dict[str, str]) -> None:
        """
        bulk set biometrics
        """
        for key, value in data.items():
            if key in BIOMETRICS and value in BIOMETRICS[key]:
                self.biometrics[key] = value

    def set_biometric(self, key: str, value: str) -> bool:
        """
        sets one biometric, returns True if accepted
        """
        if key in BIOMETRICS and value in BIOMETRICS[key]:
            self.biometrics[key] = value
            return True
        return False

    def get_biometrics(self) -> Dict[str, str]:
        """
        Returns the raw storage values (e.g., {'sleep': 'well rested'})
        """
        return dict(self.biometrics)

    def delete_biometric(self, key: str) -> bool:
        """
        removes one biometric field, returns True if removed
        """
        return bool(self.biometrics.pop(key, None))
        
    def determine_ranking_emoji(self):
        """
        Checks the Entry instance's ranking attribute and determines its associated emoji

        Returns string with ranking's associated emoji
        """
        toReturn = ""
        match self.ranking:
            case 1:
                toReturn = b'\\0001f60e'
            case 2:
                toReturn = b'\\0001f621'
            case 3:
                toReturn = b'\\0001f628'
            case 4:
                toReturn = b'\\0001f62d'
            case 5:
                toReturn = b'\\0001f63c'
            case 6:
                toReturn = b'\\0001f922'
            case 7:
                toReturn = b'\\0001fae0'
            case 8:
                toReturn = b'\\0001fae9'
        return toReturn.decode('unicode_escape')

    #Tagging System
    def _clean(self, tag):
        #Trim spaces and lowercase
        return tag.strip().lower()
    
    def has_tag(self,tag):
        t = self._clean(tag)
        return t in self.tags
    
    def add_tag(self,tag):
        #Add one tag, return true if added, false if blank or already added
        t = self._clean(tag)
        if t == "":
            return False
        if t in self.tags:
            return False
        self.tags.append(t)
        return True 
    
    def add_tags(self, tags):
        #Add multiple tags
        added = 0
        for tag in tags:
            if self.add_tag(tag):
                added += 1
        return added
    
    def remove_tag(self,tag):
        #Remove tags, Returns true if removed
        t = self._clean(tag)
        if t in self.tags:
            self.tags.remove(t)
            return True 
        return False
    
    def clear_tags(self):
        #remove all tags
        self.tags =[]

    def is_private_check(self):
        return self.is_private
    
    def set_privacy_setting(self, priv_setting: bool):
        self.is_private = priv_setting
