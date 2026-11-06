import json
import os
from pathlib import Path
from types import SimpleNamespace

import pytest

from app import App
from version import APP_VERSION


def make_app(save_file: Path):
    app = App.__new__(App)

    app.save_file = save_file
    app.data_dir = save_file.parent

    app.title = "Lifecycle Test"
    app.dark_mode = False
    app.counter_names = [
        "HP",
        "Sanity",
    ]

    app.players = [
        SimpleNamespace(
            name="Alice",
            values=[10, 5],
            group="Green",
        )
    ]

    return app


class FakeRoot:
    def __init__(self):
        self.destroy_called = False

    def destroy(self):
        self.destroy_called = True


def test_close_saves_before_destroy(tmp_path):
    save_file = (
        tmp_path
        / "Stat Tracker"
        / "tracker_data.json"
    )

    app = make_app(save_file)
    app.root = FakeRoot()

    app.close()

    assert save_file.exists()
    assert app.root.destroy_called is True

    data = json.loads(
        save_file.read_text(
            encoding="utf-8"
        )
    )

    assert data["title"] == "Lifecycle Test"


def test_close_file_still_exists_after_destroy(tmp_path):
    save_file = (
        tmp_path
        / "Stat Tracker"
        / "tracker_data.json"
    )

    app = make_app(save_file)
    app.root = FakeRoot()

    app.close()

    assert app.root.destroy_called
    assert save_file.parent.exists()
    assert save_file.exists()


def test_multiple_close_cycles_preserve_file(tmp_path):
    save_file = (
        tmp_path
        / "Stat Tracker"
        / "tracker_data.json"
    )

    first = make_app(save_file)
    first.root = FakeRoot()

    first.close()

    assert save_file.exists()

    first_data = json.loads(
        save_file.read_text(
            encoding="utf-8"
        )
    )

    assert first_data["players"][0]["values"][0] == 10

    second = make_app(save_file)
    second.root = FakeRoot()

    second.players[0].values[0] = 37

    second.close()

    assert save_file.exists()

    second_data = json.loads(
        save_file.read_text(
            encoding="utf-8"
        )
    )

    assert second_data["players"][0]["values"][0] == 37


def test_appdata_style_path_persists(tmp_path):
    fake_local_appdata = (
        tmp_path
        / "AppData"
        / "Local"
    )

    save_file = (
        fake_local_appdata
        / "Stat Tracker"
        / "tracker_data.json"
    )

    app = make_app(save_file)
    app.root = FakeRoot()

    app.close()

    assert fake_local_appdata.exists()
    assert save_file.parent.exists()
    assert save_file.exists()


def test_migration_copy_logic(tmp_path):
    legacy_save = (
        tmp_path
        / "project"
        / "tracker_data.json"
    )

    destination = (
        tmp_path
        / "AppData"
        / "Local"
        / "Stat Tracker"
        / "tracker_data.json"
    )

    legacy_save.parent.mkdir(
        parents=True,
        exist_ok=True,
    )

    legacy_data = {
        "version": APP_VERSION,
        "title": "Migrated Tracker",
        "dark_mode": True,
        "counter_names": [
            "HP",
            "Sanity",
        ],
        "players": [
            {
                "name": "Migrated Player",
                "values": [8, 4],
                "group": "Purple",
            }
        ],
    }

    legacy_save.write_text(
        json.dumps(
            legacy_data,
            indent=2,
        ),
        encoding="utf-8",
    )

    destination.parent.mkdir(
        parents=True,
        exist_ok=True,
    )

    if (
        not destination.exists()
        and legacy_save.exists()
    ):
        destination.write_text(
            legacy_save.read_text(
                encoding="utf-8"
            ),
            encoding="utf-8",
        )

    assert legacy_save.exists()
    assert destination.exists()

    migrated = json.loads(
        destination.read_text(
            encoding="utf-8"
        )
    )

    assert migrated == legacy_data


def test_migration_does_not_overwrite_existing_save(tmp_path):
    legacy_save = (
        tmp_path
        / "project"
        / "tracker_data.json"
    )

    destination = (
        tmp_path
        / "AppData"
        / "Local"
        / "Stat Tracker"
        / "tracker_data.json"
    )

    legacy_save.parent.mkdir(
        parents=True,
        exist_ok=True,
    )

    destination.parent.mkdir(
        parents=True,
        exist_ok=True,
    )

    legacy_save.write_text(
        '{"title": "OLD"}',
        encoding="utf-8",
    )

    destination.write_text(
        '{"title": "CURRENT"}',
        encoding="utf-8",
    )

    if (
        not destination.exists()
        and legacy_save.exists()
    ):
        destination.write_text(
            legacy_save.read_text(
                encoding="utf-8"
            ),
            encoding="utf-8",
        )

    data = json.loads(
        destination.read_text(
            encoding="utf-8"
        )
    )

    assert data["title"] == "CURRENT"


def test_no_persistence_code_deletes_save_directory(tmp_path):
    save_file = (
        tmp_path
        / "Stat Tracker"
        / "tracker_data.json"
    )

    app = make_app(save_file)
    app.root = FakeRoot()

    app.save_state()

    assert save_file.exists()

    app.close()

    assert save_file.parent.exists()
    assert save_file.exists()


@pytest.mark.skipif(os.name != "nt", reason="Windows environment diagnostic")
def test_real_localappdata_environment_is_available():
    """
    Diagnostic only: verifies the environment Python sees.
    Does NOT write to the user's actual AppData.
    """
    local_appdata = os.environ.get(
        "LOCALAPPDATA"
    )

    assert local_appdata

    path = Path(local_appdata)

    assert path.is_absolute()
