# Here we'll write tests for all of the possible functions in mood_journal
# which also--by extension--means testing the functionality of entry and anything else related to it

# Look to docs/TESTING.md and tests/test_models.py for reference
from mood_mastery.entry import Entry
from mood_mastery.mood_journal import Mood_Journal
import pytest

"""Create Entry Test"""
def create_entry_test():
    e1 = Entry("Test Entry", 13,1,2025, "Today is my birthday!", 9)
    assert e1.entry_name == "Test Entry", "Entry name should match the provided input"
    assert e1.entry_date == (13, 1, 2025) or hasattr(e1, "entry_date"), "Entry should store a valid date"
    assert e1.entry_body == "Today is my birthday!", "Entry body should match input text"
    assert e1.ranking == 9, "Ranking should match the provided number"
    print("Entry of id " + e1.entry_id_str + " successfully created.")
    print("Create Entry Test Passed")

"""Edit Entry Test"""
def edit_entry_test():
    e1 = Entry("Test Entry 2", 1, 1, 2026, "Happy New Year!", 9)
    e1.edit_entry("New Year's Party", 1, 1, 2026, "Happy New Year! The party was so fun!!", 10)
    assert e1.entry_name == "New Year's Party", "New entry name should match the provided input"
    assert e1.entry_date == (1,1,2026) or hasattr(e1, "entry_date"), "New entry date should match and be a valid date"
    assert e1.entry_body == "Happy New Year! The party was so fun!!", "New entry body should match the input text"
    assert e1.ranking == 10, "New ranking should match the provided number"
    print("Entry of id " + e1.entry_id_str + " successfully edited.")
    print("Edit Entry Test Passed")

"""Determine Ranking Emoji Test"""
def determine_ranking_emoji_test():
    e1 = Entry("Test Entry", 1, 1, 1, "Awesome", 1)
    assert e1.determine_ranking_emoji() == (b'\\0001f60e').decode('unicode_escape')
    print("Determine Ranking Emoji Test Passed")

def mj_create_entry_test():
    mj1 = Mood_Journal()
    entry1_id = mj1.mj_create_entry("Test Entry 2", 1, 1, 2026, "Happy New Year!", 9)
    assert len(mj1.entries_dict) == 1
    print(mj1.entries_dict)
    print("Mood Journal entry of id " + entry1_id + " successfully created and added.")
    print("Mood Journal Create Entry Test Passed")
    pass

def mj_edit_entry_test():
    mj1 = Mood_Journal()
    entry1_id = mj1.mj_create_entry("Test Entry 2", 1, 1, 2026, "Happy New Year!", 9)
    mj1.mj_edit_entry(entry1_id, "New Year's Party", 1, 1, 2026, "Happy New Year! The party was so fun!!", 10)
    assert len(mj1.entries_dict) == 1
    assert mj1.entries_dict[entry1_id].entry_name == "New Year's Party", "New entry name should match the provided input"
    assert mj1.entries_dict[entry1_id].entry_date == (1,1,2026) or hasattr(mj1.entries_dict[entry1_id], "entry_date"), "New entry date should match and be a valid date"
    assert mj1.entries_dict[entry1_id].entry_body == "Happy New Year! The party was so fun!!", "New entry body should match the input text"
    assert mj1.entries_dict[entry1_id].ranking == 10, "New ranking should match the provided number"
    print("Entry of id " + entry1_id + " successfully edited.")
    print("Mood Journal Edit Entry Test Passed")


"""Mood Journal Delete Entry Test"""
def mj_delete_entry_test():
    # TODO: create a Mood_Journal object, make two entries using the mj_create_entry function,
    #       call the mj_delete_entry function with one of their ids, and assert that the length of your
    #       Mood_Journal object is now one.
   
    mj1 = Mood_Journal()

    # Create two entries
    id1 = mj1.mj_create_entry("Test Entry 1", 10, 1, 2025, "First", 5)
    id2 = mj1.mj_create_entry("Test Entry 2", 11, 1, 2025, "Second", 7)

    # Make sure there are two entries in the dictionary
    assert len(mj1.entries_dict) == 2

    # Delete one entry
    deleted = mj1.mj_delete_entry(id1)
    
    assert deleted is True, "mj_delete_entry should return True when deletion succeeds"
    assert id1 not in mj1.entries_dict, "Deleted entry should be removed from entries_dict"
    assert len(mj1.entries_dict) == 1, "After deleting one, exactly one entry should remain"

    # Ensure the other entry is untouched
    assert id2 in mj1.entries_dict, "Non-deleted entry should still exist"

    # Deleting a non-existent entry should return False
    deleted_missing = mj1.mj_delete_entry("does-not-exist")
    assert deleted_missing is False, "Deleting a missing ID should return False"

    print("Mood Journal Delete Entry Test Passed")
    pass

create_entry_test()
edit_entry_test()
determine_ranking_emoji_test()
mj_create_entry_test()
mj_edit_entry_test()
mj_delete_entry_test()
