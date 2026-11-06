"""Platform-appropriate state paths; resources also work in PyInstaller bundles."""
import os
import sys
from pathlib import Path


def data_directory(platform=None, environ=None, home=None):
    platform = sys.platform if platform is None else platform
    environ = os.environ if environ is None else environ
    home = Path.home() if home is None else Path(home)
    if platform == "win32":
        return Path(environ.get("LOCALAPPDATA", home / "AppData" / "Local")) / "Stat Tracker"
    if platform == "darwin":
        return home / "Library" / "Application Support" / "Stat Tracker"
    xdg = Path(environ.get("XDG_DATA_HOME", ""))
    base = xdg if xdg.is_absolute() else home / ".local" / "share"
    return base / "stat-tracker"


def asset_path(relative):
    return Path(__file__).resolve().parent / relative
