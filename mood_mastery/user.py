# Imports
from mood_mastery.mood_journal import Mood_Journal
import bcrypt

class User:
    """
    A class representing a user.

    Attributes -------------------------
     - user_mood_journal : Mood_Journal()       // The Mood_Journal() object where the user's entries are stored
     - user_entries_pwd_encrypted : str         // The encrypted value of the user's password for them to access private entries
    """
    # Attributes (TO BE UPDATED, depending on what we need)
    user_mood_journal = None
    user_entries_pwd_encrypted = None

    def __init__(self):
        self.user_mood_journal = Mood_Journal()
        self.user_entries_pwd_encrypted = None
        self.streak_current = 0
        self.streak_longest = 0
        self.last_entry_date = None

    def view_entry(self, entry_id_str: str, entry_pwd_attempt=None):
        if self.check_if_private(entry_id_str):
                # If the entry is private
                # Check if pwd attempt was given; if not, return False
                if entry_pwd_attempt == None:
                    return False
                # If pwd attempt was given, get hashed version of the input and compare
                if bcrypt.checkpw(entry_pwd_attempt.encode('utf-8'), self.user_entries_pwd_encrypted):
                    # If the hashed version of the input == the pwd, show private entry
                    return self.user_mood_journal.mj_get_entry(entry_id_str)
                else:
                    # Otherwise, since hashed version of the input != the pwd, don't show the private entry
                    return False
        else:
            # If the entry isn't private, show the entry (no pwd checking needed)
            return self.user_mood_journal.mj_get_entry(entry_id_str)

   
    def check_if_private(self, entry_id_str: str):
        return self.user_mood_journal.mj_get_entry_privacy_status(entry_id_str)


    def privatize_entry(self, entry_id_str: str, user_entries_pwd=None):
        # If the entry doesn't exist, return False
        if(self.user_mood_journal.mj_get_entry(entry_id_str) == False):
            return False
        #Otherwise:
        if self.user_entries_pwd_encrypted == None:
            # If user never made an entry private (and therefore didn't set an entry pwd)
            # Check if pwd input was given; if not, return False
            if user_entries_pwd == None:
                return False
            # If pwd was given, set the value to the encrypted pwd input (user_entries_pwd)
            encrypted_pwd = bcrypt.hashpw(user_entries_pwd.encode('utf-8'), bcrypt.gensalt())
            self.user_entries_pwd_encrypted = encrypted_pwd
            # and then make the entry private
            self.user_mood_journal.mj_get_entry(entry_id_str).set_privacy_setting(True)
        else:
            # If user has made an entry private before (meaning an entry pwd exists),
            # just make the entry private
            self.user_mood_journal.mj_get_entry(entry_id_str).set_privacy_setting(True)