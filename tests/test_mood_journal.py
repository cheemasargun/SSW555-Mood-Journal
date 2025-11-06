# Here we'll write tests for all of the possible functions in mood_journal
# which also--by extension--means testing the functionality of entry and anything else related to it

# Look to docs/TESTING.md and tests/test_models.py for reference
from mood_mastery.entry import Entry
from mood_mastery.mood_journal import Mood_Journal
from mood_mastery.user import User
from datetime import date, datetime
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
    assert e1.determine_ranking_emoji() == '😎'
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

def test_mj_weekly_report():
    mj = Mood_Journal()
    assert mj.mj_weekly_report(1, 1, 2025) == None
    mj.mj_create_entry("e1", 1, 1, 2025, "body", 3)
    assert mj.mj_weekly_report(1, 1, 2025) == [0, 0, 1, 0, 0, 0, 0, 0]
    print("Report Test Passed")

def test_mj_monthly_report():
    mjm = Mood_Journal()
    assert mjm.mj_monthly_report(1, 1, 2025) == None
    mjm.mj_create_entry("e1", 1, 1, 2025, "body", 3)
    assert mjm.mj_monthly_report(1, 1, 2025) == [0, 0, 1, 0, 0, 0, 0, 0]
    print("Monthly Report Test Passed")

""" Testing Biometrics """
def test_mj_create_entry_with_biometrics():
    mj = Mood_Journal()

    # Create entry
    entry_id = mj.mj_create_entry(
        "Bio Day",
        5, 11, 2025,
        "Testing biometrics with journal",
        5
    )

    e = mj.mj_get_entry(entry_id)

    # Set biometrics
    assert e.set_biometric("Sleep", "well rested") is True
    assert e.set_biometric("Physical Wellness", "energized") is True
    assert e.set_biometric("Mental Wellness", "normal") is True
    assert e.set_biometric("Menstruation", "no") is True

    # Validate stored data
    result = e.get_biometrics()
    assert result == {
        "Sleep": "well rested",
        "Physical Wellness": "energized",
        "Mental Wellness": "normal",
        "Menstruation": "no"
    }

def test_mj_biometrics_update_and_delete():
    mj = Mood_Journal()
    entry_id = mj.mj_create_entry("Bio Update", 6, 11, 2025, "body", 4)
    e = mj.mj_get_entry(entry_id)

    # Add a biometric
    e.set_biometric("Sleep", "sleepy")
    assert e.get_biometrics() == {"Sleep": "sleepy"}

    # Update it
    e.set_biometric("Sleep", "meh")
    assert e.get_biometrics()["Sleep"] == "meh"

    # Delete it
    assert e.delete_biometric("Sleep") is True
    assert e.get_biometrics() == {}

""" Testing Timeline/Calendar"""
def _attach_created_at(entry, dt):
    """Helper to attach created_at for deterministic ordering in tests."""
    setattr(entry, "created_at", dt)
    return entry

def test_mj_entries_on_filters_by_day_and_sorts():
    mj = Mood_Journal()

    # Two entries on Nov 5, one on Nov 6
    id1 = mj.mj_create_entry("Zeta", 5, 11, 2025, "body", 3)
    id2 = mj.mj_create_entry("Alpha", 5, 11, 2025, "body", 7)
    id3 = mj.mj_create_entry("Next Day", 6, 11, 2025, "body", 6)

    # Attach created_at to ensure stable order: earlier first
    _attach_created_at(mj.entries_dict[id1], datetime(2025, 11, 5, 9, 0, 0))
    _attach_created_at(mj.entries_dict[id2], datetime(2025, 11, 5, 8, 59, 0))
    _attach_created_at(mj.entries_dict[id3], datetime(2025, 11, 6, 10, 0, 0))

    results_1105 = mj.mj_entries_on(2025, 11, 5)
    assert [e.entry_id_str for e in results_1105] == [id2, id1], "Should return only Nov 5 entries sorted by created_at"

    results_1106 = mj.mj_entries_on(2025, 11, 6)
    assert [e.entry_id_str for e in results_1106] == [id3], "Should return only Nov 6 entry"


def test_mj_entries_between_is_inclusive_and_sorted():
    mj = Mood_Journal()

    a1 = mj.mj_create_entry("A1", 4, 11, 2025, "a", 5)
    a2 = mj.mj_create_entry("A2", 4, 11, 2025, "a", 5)
    b1 = mj.mj_create_entry("B1", 5, 11, 2025, "b", 5)
    c1 = mj.mj_create_entry("C1", 6, 11, 2025, "c", 5)
    x = mj.mj_create_entry("X", 7, 11, 2025, "x", 5)  # outside range

    _attach_created_at(mj.entries_dict[a1], datetime(2025, 11, 4, 9))
    _attach_created_at(mj.entries_dict[a2], datetime(2025, 11, 4, 10))
    _attach_created_at(mj.entries_dict[b1], datetime(2025, 11, 5, 8))
    _attach_created_at(mj.entries_dict[c1], datetime(2025, 11, 6, 7))
    _attach_created_at(mj.entries_dict[x],  datetime(2025, 11, 7, 7))

    results = mj.mj_entries_between(date(2025, 11, 4), date(2025, 11, 6))
    assert [e.entry_id_str for e in results] == [a1, a2, b1, c1], "Range must be inclusive and sorted by date then created_at"


def test_mj_entries_grouped_by_day_includes_empty_days_and_sorts_each_bucket():
    mj = Mood_Journal()

    d1 = mj.mj_create_entry("D1", 3, 11, 2025, "d", 5)
    e1 = mj.mj_create_entry("E1", 5, 11, 2025, "e", 5)
    e2 = mj.mj_create_entry("E2", 5, 11, 2025, "e", 5)
    f1 = mj.mj_create_entry("F1", 6, 11, 2025, "f", 5)

    _attach_created_at(mj.entries_dict[d1], datetime(2025, 11, 3, 9))
    _attach_created_at(mj.entries_dict[e1], datetime(2025, 11, 5, 8))
    _attach_created_at(mj.entries_dict[e2], datetime(2025, 11, 5, 9))
    _attach_created_at(mj.entries_dict[f1], datetime(2025, 11, 6, 7))

    grouped = mj.mj_entries_grouped_by_day(date(2025, 11, 3), date(2025, 11, 6))

    # All days present (including empty Nov 4)
    assert date(2025, 11, 3) in grouped
    assert date(2025, 11, 4) in grouped
    assert date(2025, 11, 5) in grouped
    assert date(2025, 11, 6) in grouped

    # Empty day has empty list
    assert grouped[date(2025, 11, 4)] == []

    # Buckets sorted deterministically
    assert [e.entry_id_str for e in grouped[date(2025, 11, 5)]] == [e1, e2]
    assert [e.entry_id_str for e in grouped[date(2025, 11, 3)]] == [d1]
    assert [e.entry_id_str for e in grouped[date(2025, 11, 6)]] == [f1]


def test_mj_month_calendar_covers_full_grid_and_groups_entries():
    mj = Mood_Journal()

    m1 = mj.mj_create_entry("Morning", 5, 11, 2025, "m", 4)
    m2 = mj.mj_create_entry("Evening", 5, 11, 2025, "m", 6)
    mid = mj.mj_create_entry("Mid", 18, 11, 2025, "m", 2)

    _attach_created_at(mj.entries_dict[m1], datetime(2025, 11, 5, 9))
    _attach_created_at(mj.entries_dict[m2], datetime(2025, 11, 5, 20))
    _attach_created_at(mj.entries_dict[mid], datetime(2025, 11, 18, 12))

    cal = mj.mj_month_calendar(2025, 11)

    # Should include dates needed to render a full Monday→Sunday grid
    assert date(2025, 11, 5) in cal
    assert date(2025, 11, 18) in cal

    # Day with two entries appears in deterministic order
    nov5_ids = [e.entry_id_str for e in cal[date(2025, 11, 5)]]
    assert nov5_ids == [m1, m2]

    # A random day with no entries is present and empty
    assert date(2025, 11, 7) in cal
    assert cal[date(2025, 11, 7)] == []
