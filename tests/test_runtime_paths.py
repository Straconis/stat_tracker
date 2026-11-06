from pathlib import Path
from runtime_paths import data_directory


def test_platform_data_directories():
    assert data_directory("linux", {}, "/home/test") == Path("/home/test/.local/share/stat-tracker")
    assert data_directory("linux", {"XDG_DATA_HOME": "/tmp/data"}, "/home/test") == Path("/tmp/data/stat-tracker")
    assert data_directory("linux", {"XDG_DATA_HOME": "relative"}, "/home/test") == Path("/home/test/.local/share/stat-tracker")
    assert data_directory("win32", {"LOCALAPPDATA": "C:/Data"}, "/home/test") == Path("C:/Data/Stat Tracker")
    assert data_directory("darwin", {}, "/Users/test") == Path("/Users/test/Library/Application Support/Stat Tracker")
