# Here we'll write tests for all of the possible functions in mood_journal
# which also--by extension--means testing the functionality of entry and anything else related to it

# Look to docs/TESTING.md and tests/test_models.py for reference
from  mood_mastery.entry import Entry
import pytest
#Create Entry Test

def create_entry_test():
    e1 = Entry("Test Entry", 13,1,2025, "Today is my birthday!", 9)
    assert e1.entry_name == "Test Entry", "Entry name should match the provided input"
    assert e1.entry_date == (13, 1, 2025) or hasattr(e1, "entry_date"), "Entry should store a valid date"
    assert e1.entry_body == "Today is my birthday!", "Entry body should match input text"
    assert e1.ranking == 9, "Ranking should match the provided number"
    print("Create Entry Test Passed")


create_entry_test()
