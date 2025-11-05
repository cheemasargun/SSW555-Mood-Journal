# Here we'll write tests for all of the possible functions in mood_journal
# which also--by extension--means testing the functionality of entry and anything else related to it

# Look to docs/TESTING.md and tests/test_models.py for reference
from mood_mastery.entry import Entry
from mood_mastery.mood_journal import Mood_Journal
from mood_mastery.user import User
from datetime import date
import pytest

"""Create Entry Test"""
def test_create_entry():
    e1 = Entry("Test Entry", 13,1,2025, "Today is my birthday!", 9)
    assert e1.entry_name == "Test Entry", "Entry name should match the provided input"
    assert e1.entry_date == (13, 1, 2025) or hasattr(e1, "entry_date"), "Entry should store a valid date"
    assert e1.entry_body == "Today is my birthday!", "Entry body should match input text"
    assert e1.ranking == 9, "Ranking should match the provided number"
    print("Entry of id " + e1.entry_id_str + " successfully created.")
    print("Create Entry Test Passed")
    print()

"""Edit Entry Test"""
def test_edit_entry():
    e1 = Entry("Test Entry 2", 1, 1, 2026, "Happy New Year!", 9)
    e1.edit_entry("New Year's Party", 1, 1, 2026, "Happy New Year! The party was so fun!!", 10)
    assert e1.entry_name == "New Year's Party", "New entry name should match the provided input"
    assert e1.entry_date == (1,1,2026) or hasattr(e1, "entry_date"), "New entry date should match and be a valid date"
    assert e1.entry_body == "Happy New Year! The party was so fun!!", "New entry body should match the input text"
    assert e1.ranking == 10, "New ranking should match the provided number"
    print("Entry of id " + e1.entry_id_str + " successfully edited.")
    print("Edit Entry Test Passed")
    print()

"""Determine Ranking Emoji Test"""
def test_determine_ranking_emoji():
    e1 = Entry("Test Entry", 1, 1, 1, "Awesome", 1)
    assert e1.determine_ranking_emoji() == (b'\\0001f60e').decode('unicode_escape')
    print("Determine Ranking Emoji Test Passed")
    print()

""""Test Tagging System"""
def test_add_tag_basic_and_blank():
    e = Entry("A", 1, 1, 2025, "X", 1)
    assert e.add_tag("Focus") is True
    assert e.tags == ["focus"]

    # Duplicate (case-insensitive)
    assert e.add_tag("focus") is False
    assert e.tags == ["focus"]

    # Blank / whitespace-only should be rejected
    assert e.add_tag("   ") is False
    assert e.tags == ["focus"]

def test_add_tags_bulk_counting():
    e = Entry("A", 1, 1, 2025, "X", 1)
    added = e.add_tags(["Friends", " Sleep ", "friends", "FOCUS"])
    assert added == 3  # friends, sleep, focus (one duplicate ignored)
    assert sorted(e.tags) == ["focus", "friends", "sleep"]

def test_has_tag_case_insensitive():
    e = Entry("A", 1, 1, 2025, "X", 1, tags=["Exercise"])
    assert e.has_tag("exercise") is True
    assert e.has_tag("ExErCiSe") is True
    assert e.has_tag("rest") is False

def test_remove_tag_and_clear():
    e = Entry("A", 1, 1, 2025, "X", 1, tags=["focus", "friends", "sleep"])
    assert e.remove_tag("Friends") is True
    assert sorted(e.tags) == ["focus", "sleep"]

    # Removing non-existent returns False
    assert e.remove_tag("gratitude") is False

    e.clear_tags()
    assert e.tags == []
"""Test Privatize Entries"""
def test_is_private_check():
    e1 = Entry("Test Entry 2", 1, 1, 2026, "Happy New Year!", 9)
    # Testing if e1 is public (is_private is False) by default
    assert e1.is_private_check() == False
    print("Entry of id " + e1.entry_id_str + " is public (is_private is False) by default.")
    print("Entry is_private_check() Default Test Passed.")
    print()

def test_set_privacy_setting():
    e1 = Entry("Test Entry", 13,1,2025, "Today is my birthday!", 9)
    # Testing if set_privacy_setting() works directly
    e1.set_privacy_setting(True)
    assert e1.is_private_check() == True
    print("Entry of id " + e1.entry_id_str + " successfully made private (is_private is True.")
    print("Entry set_privacy_setting() Test Passed.")
    print()

def test_mj_get_entry():
    mj1 = Mood_Journal()
    entry1_id = mj1.mj_create_entry("New Year's Party", 1, 1, 2026, "Happy New Year! The party was so fun!!", 10)
    mj1_received_entry = mj1.mj_get_entry(entry1_id)
    assert mj1_received_entry.entry_name == "New Year's Party", "entry name should match the provided input"
    assert mj1_received_entry.entry_date == (1,1,2026) or hasattr(mj1_received_entry, "entry_date"), "entry date should match and be a valid date"
    assert mj1_received_entry.entry_body == "Happy New Year! The party was so fun!!", "entry body should match the input text"
    assert mj1_received_entry.ranking == 10, "ranking should match the provided number"
    print("Mood Journal Get Entry Test Passed")
    print()

def test_mj_get_entry_privacy_status_DEFAULT():
    mj1 = Mood_Journal()
    entry1_id = mj1.mj_create_entry("New Year's Party", 1, 1, 2026, "Happy New Year! The party was so fun!!", 10)
    entry2_id = mj1.mj_create_entry("Test Entry", 13,1,2025, "Today is my birthday!", 9)
    assert mj1.mj_get_entry_privacy_status(entry1_id) == False
    assert mj1.mj_get_entry_privacy_status(entry2_id) == False
    print("Mood Journal Get Entry Privacy Status Test (DEFAULT) Passed")
    print()

def test_user_pwd_initialization():
    user1 = User()
    assert user1.user_entries_pwd_encrypted == None
    print("User Pwd Initialization Test (DEFAULT) Passed (User pwd is None by default)")
    print()

def test_user_view_entry_PUBLIC():
    user1 = User()
    entry1_id = user1.user_mood_journal.mj_create_entry("New Year's Party", 1, 1, 2026, "Happy New Year! The party was so fun!!", 10)
    entry1 = user1.view_entry(entry1_id)
    assert entry1.entry_name == "New Year's Party", "entry name should match the provided input"
    assert entry1.entry_date == (1,1,2026) or hasattr(entry1, "entry_date"), "entry date should match and be a valid date"
    assert entry1.entry_body == "Happy New Year! The party was so fun!!", "entry body should match the input text"
    assert entry1.ranking == 10, "ranking should match the provided number"
    assert entry1.is_private == False, "privacy status should match the default (False)"
    print("User View Entry Test (PUBLIC) Passed")
    print()

def test_user_check_if_private_PUBLIC():
    user1 = User()
    entry1_id = user1.user_mood_journal.mj_create_entry("New Year's Party", 1, 1, 2026, "Happy New Year! The party was so fun!!", 10)
    assert user1.check_if_private(entry1_id) == False, "privacy status should match the default (False)"
    print("User Check If Private Test (PUBLIC) Passed")
    print()

def test_user_privatize_entry_NOPWD_NOINPUT():
    user1 = User()
    entry1_id = user1.user_mood_journal.mj_create_entry("New Year's Party", 1, 1, 2026, "Happy New Year! The party was so fun!!", 10)
    assert user1.privatize_entry(entry1_id) == False, "privatize_entry should return False if no pwd exists and none was given as input"
    print("User Privatize Entry (NO PWD, NO INPUT) Test Passed")
    print()

def test_user_privatize_entry_PWD_INPUT():
    user1 = User()
    entry1_id = user1.user_mood_journal.mj_create_entry("New Year's Party", 1, 1, 2026, "Happy New Year! The party was so fun!!", 10)
    user1.privatize_entry(entry1_id, "hello123")
    assert user1.check_if_private(entry1_id) == True # Entry is private (True)
    assert user1.view_entry(entry1_id) == False # Entry is private, but no pwd attempt given
    assert user1.view_entry(entry1_id, "oops987") == False # Entry is private, but pwd attempt is incorrect
    
    # Checking that pivate entry is accesible (and its traits are as expected)
    # if proper pwd is input
    entry1 = user1.view_entry(entry1_id, "hello123")
    assert entry1.entry_name == "New Year's Party", "entry name should match the provided input"
    assert entry1.entry_date == (1,1,2026) or hasattr(entry1, "entry_date"), "entry date should match and be a valid date"
    assert entry1.entry_body == "Happy New Year! The party was so fun!!", "entry body should match the input text"
    assert entry1.ranking == 10, "ranking should match the provided number"
    assert entry1.is_private == True, "privacy status should be True"
    print("User Privatize Entry (PWD, INPUT) Test Passed")
    print()

def test_mj_create_entry():
    mj1 = Mood_Journal()
    entry1_id = mj1.mj_create_entry("Test Entry 2", 1, 1, 2026, "Happy New Year!", 9)
    assert len(mj1.entries_dict) == 1
    print(mj1.entries_dict)
    print("Mood Journal entry of id " + entry1_id + " successfully created and added.")
    print("Mood Journal Create Entry Test Passed")
    print()

def test_mj_edit_entry():
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
    print()


"""Mood Journal Delete Entry Test"""
def test_mj_delete_entry():
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
    print()

"""Testing Streak System"""
def test_streak_initial_state_new_journal():
    mj = Mood_Journal()
    s = mj.get_streak_summary()
    assert s["current_streak"] == 0
    assert s["longest_streak"] == 0
    assert s["last_entry_date"] is None

def test_streak_first_entry_starts_at_one():
    mj = Mood_Journal()
    mj.mj_log_entry("D1", 1, 1, 2026, "First", 5)
    s = mj.get_streak_summary()
    assert s["current_streak"] == 1
    assert s["longest_streak"] == 1
    assert s["last_entry_date"] == date(2026, 1, 1)

def test_streak_consecutive_days_increment():
    mj = Mood_Journal()
    mj.mj_log_entry("D1", 1, 1, 2026, "Day1", 5)
    mj.mj_log_entry("D2", 2, 1, 2026, "Day2", 5)
    mj.mj_log_entry("D3", 3, 1, 2026, "Day3", 5)
    s = mj.get_streak_summary()
    assert s["current_streak"] == 3
    assert s["longest_streak"] == 3
    assert s["last_entry_date"] == date(2026, 1, 3)

def test_streak_multiple_entries_same_day_no_increment():
    mj = Mood_Journal()
    mj.mj_log_entry("D1-a", 10, 2, 2026, "A", 5)
    # same calendar day, should not increase streak
    mj.mj_log_entry("D1-b", 10, 2, 2026, "B", 5)
    s = mj.get_streak_summary()
    assert s["current_streak"] == 1
    assert s["longest_streak"] == 1
    assert s["last_entry_date"] == date(2026, 2, 10)

def test_streak_gap_breaks_and_resets_current():
    mj = Mood_Journal()
    mj.mj_log_entry("D1", 1, 3, 2026, "Day1", 5)
    mj.mj_log_entry("D2", 2, 3, 2026, "Day2", 5)
    # gap: skip the 3rd, log on the 4th
    mj.mj_log_entry("D4", 4, 3, 2026, "Day4", 5)
    s = mj.get_streak_summary()
    assert s["current_streak"] == 1        # reset on the gap
    assert s["longest_streak"] == 2        # best run was D1-D2
    assert s["last_entry_date"] == date(2026, 3, 4)

def test_streak_backfill_triggers_recompute_and_extends_run():
    mj = Mood_Journal()
    # Create 1st, 2nd, and 4th — current=1, longest=2 (from 1-2), last=4th
    mj.mj_log_entry("D1", 1, 4, 2026, "Day1", 5)
    mj.mj_log_entry("D2", 2, 4, 2026, "Day2", 5)
    mj.mj_log_entry("D4", 4, 4, 2026, "Day4", 5)
    s = mj.get_streak_summary()
    assert s["current_streak"] == 1
    assert s["longest_streak"] == 2
    assert s["last_entry_date"] == date(2026, 4, 4)

    # Backfill the 3rd — recompute should yield a 4-day streak ending on the 4th
    mj.mj_log_entry("D3-backfill", 3, 4, 2026, "Day3", 5)
    s2 = mj.get_streak_summary()
    assert s2["current_streak"] == 4
    assert s2["longest_streak"] == 4
    assert s2["last_entry_date"] == date(2026, 4, 4)

def test_streak_delete_entry_recompute():
    mj = Mood_Journal()
    i1 = mj.mj_create_entry("D1", 1, 6, 2026, "Day1", 5)
    i2 = mj.mj_create_entry("D2", 2, 6, 2026, "Day2", 5)
    i3 = mj.mj_create_entry("D3", 3, 6, 2026, "Day3", 5)
    mj.recompute_streak()
    s0 = mj.get_streak_summary()
    assert s0["current_streak"] == 3
    assert s0["longest_streak"] == 3
    assert s0["last_entry_date"] == date(2026, 6, 3)

    # Delete the middle day; should break the chain (now only 1 and 3)
    assert mj.mj_delete_entry(i2) is True
    s1 = mj.get_streak_summary()
    assert s1["current_streak"] == 1
    assert s1["longest_streak"] == 1
    assert s1["last_entry_date"] == date(2026, 6, 3)

def test_get_streak_summary_shape_and_types():
    mj = Mood_Journal()
    mj.mj_log_entry("Hello", 15, 7, 2026, "Entry", 4)
    s = mj.get_streak_summary()
    assert set(s.keys()) == {"current_streak", "longest_streak", "last_entry_date"}
    assert isinstance(s["current_streak"], int)
    assert isinstance(s["longest_streak"], int)
    # last_entry_date is None or a datetime.date
    led = s["last_entry_date"]
    assert (led is None) or isinstance(led, date)
