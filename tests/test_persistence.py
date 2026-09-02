import json
from pathlib import Path
from types import SimpleNamespace

from app import App
from version import APP_VERSION


def make_test_app(save_file: Path):
    """
    Create an App instance without starting Tkinter.

    save_state() only needs these attributes, so this lets us test
    persistence independently from the GUI.
    """
    app = App.__new__(App)

    app.save_file = save_file
    app.title = "Test Tracker"
    app.dark_mode = True

    app.counter_names = [
        "HP",
        "Sanity",
        "Luck",
    ]

    app.players = [
        SimpleNamespace(
            name="Alice",
            values=[10, 7, 3],
            group="Green",
        ),
        SimpleNamespace(
            name="Bob",
            values=[4, 9, 6],
            group="Purple",
        ),
    ]

    return app


def test_save_state_creates_parent_directory(tmp_path):
    save_file = (
        tmp_path
        / "Stat Tracker"
        / "tracker_data.json"
    )

    assert not save_file.parent.exists()

    app = make_test_app(save_file)

    app.save_state()

    assert save_file.parent.exists()
    assert save_file.exists()


def test_save_state_survives_after_method_returns(tmp_path):
    save_file = (
        tmp_path
        / "Stat Tracker"
        / "tracker_data.json"
    )

    app = make_test_app(save_file)

    app.save_state()

    # save_state() has fully returned at this point.
    assert save_file.exists()

    contents = save_file.read_text(
        encoding="utf-8"
    )

    assert contents


def test_save_state_writes_valid_json(tmp_path):
    save_file = (
        tmp_path
        / "Stat Tracker"
        / "tracker_data.json"
    )

    app = make_test_app(save_file)

    app.save_state()

    data = json.loads(
        save_file.read_text(
            encoding="utf-8"
        )
    )

    assert isinstance(data, dict)


def test_save_state_preserves_tracker_state(tmp_path):
    save_file = (
        tmp_path
        / "Stat Tracker"
        / "tracker_data.json"
    )

    app = make_test_app(save_file)

    app.save_state()

    data = json.loads(
        save_file.read_text(
            encoding="utf-8"
        )
    )

    assert data["version"] == APP_VERSION
    assert data["title"] == "Test Tracker"
    assert data["dark_mode"] is True

    assert data["counter_names"] == [
        "HP",
        "Sanity",
        "Luck",
    ]

    assert data["players"] == [
        {
            "name": "Alice",
            "values": [10, 7, 3],
            "group": "Green",
        },
        {
            "name": "Bob",
            "values": [4, 9, 6],
            "group": "Purple",
        },
    ]


def test_existing_save_is_overwritten(tmp_path):
    save_file = (
        tmp_path
        / "Stat Tracker"
        / "tracker_data.json"
    )

    save_file.parent.mkdir(
        parents=True,
        exist_ok=True,
    )

    save_file.write_text(
        '{"old": true}',
        encoding="utf-8",
    )

    app = make_test_app(save_file)

    app.save_state()

    data = json.loads(
        save_file.read_text(
            encoding="utf-8"
        )
    )

    assert "old" not in data
    assert data["title"] == "Test Tracker"


def test_repeated_saves_remain_valid(tmp_path):
    save_file = (
        tmp_path
        / "Stat Tracker"
        / "tracker_data.json"
    )

    app = make_test_app(save_file)

    app.save_state()

    app.players[0].values[0] = 42

    app.save_state()

    data = json.loads(
        save_file.read_text(
            encoding="utf-8"
        )
    )

    assert save_file.exists()
    assert data["players"][0]["values"][0] == 42

def test_save_state_captures_unsaved_title_entry(tmp_path):
    """
    A title typed into the UI must be captured even if the user
    closes the window before FocusOut or Return fires.
    """

    class FakeTitleEntry:
        def __init__(self, value):
            self.value = value

        def get(self):
            return self.value

    save_file = (
        tmp_path
        / "Stat Tracker"
        / "tracker_data.json"
    )

    app = make_test_app(save_file)

    # self.title still contains the old committed value.
    app.title = "Stat Tracker"

    # But the Entry contains the user's newly typed title.
    app.title_entry = FakeTitleEntry(
        "Sanity Tracker"
    )

    app.save_state()

    data = json.loads(
        save_file.read_text(
            encoding="utf-8"
        )
    )

    assert app.title == "Sanity Tracker"
    assert data["title"] == "Sanity Tracker"
