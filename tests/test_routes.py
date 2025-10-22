import pytest
from models import MoodEntry


# === Mood Journal Tests ===


def test_mood_journal_get_returns_ok(client):
    """Test that GET /mood-journal returns a 200 status code."""
    # Act
    response = client.get('/mood-journal')

    # Assert
    assert response.status_code == 200


def test_mood_journal_post_creates_entry(client):
    """Test that POST /mood-journal creates a new mood entry in the database."""
    # Arrange
    entry_data = {'mood': 'Joyful', 'notes': 'Sunshine and coffee'}

    # Act
    response = client.post('/mood-journal', data=entry_data, follow_redirects=False)

    # Assert
    assert response.status_code == 302
    stored = MoodEntry.query.filter_by(mood='Joyful').first()
    assert stored is not None
    assert stored.notes == 'Sunshine and coffee'


def test_mood_journal_rejects_blank_mood(client):
    """Test that POST /mood-journal rejects entries with blank mood values."""
    # Arrange
    invalid_data = {'mood': '  ', 'notes': 'Forgot to fill mood'}

    # Act
    response = client.post('/mood-journal', data=invalid_data, follow_redirects=False)

    # Assert
    assert response.status_code == 302
    assert MoodEntry.query.count() == 0



# === Parametrized Tests ===


@pytest.mark.parametrize(
    "endpoint",
    ["/mood-journal"]
)
def test_all_modules_get_returns_ok(client, endpoint):
    """Test that all module endpoints return 200 status code on GET requests."""
    # Act
    response = client.get(endpoint)

    # Assert
    assert response.status_code == 200
