import json
import tkinter as tk

from models import Player
from theme import GROUP_COLORS
from version import APP_VERSION


class PersistenceMixin:
    def save_state(self):
        # Capture the current title directly from the UI before saving.
        # This protects against closing the window before the title
        # Entry receives a FocusOut or Return event.
        title_entry = getattr(
            self,
            "title_entry",
            None
        )

        if title_entry is not None:
            try:
                current_title = (
                    title_entry.get().strip()
                )
            except (
                tk.TclError,
                AttributeError
            ):
                current_title = ""

            if current_title:
                self.title = current_title

        data = {
            "version": APP_VERSION,
            "title": self.title,
            "dark_mode": self.dark_mode,
            "counter_names": self.counter_names,
            "players": [
                {
                    "name": player.name,
                    "values": player.values,
                    "group": player.group
                }
                for player in self.players
            ]
        }

        try:
            # Ensure the user-data directory exists every time
            # before writing. This also protects against the
            # directory being removed while the app is running.
            self.save_file.parent.mkdir(
                parents=True,
                exist_ok=True
            )

            self.save_file.write_text(
                json.dumps(
                    data,
                    indent=2
                ),
                encoding="utf-8"
            )

        except OSError as exc:
            print(
                "ERROR saving tracker state:",
                repr(exc)
            )
            print(
                "Attempted save path:",
                self.save_file
            )

    def load_state(self):
        if not self.save_file.exists():
            return

        try:
            data = json.loads(
                self.save_file.read_text(
                    encoding="utf-8"
                )
            )

            title = data.get(
                "title"
            )

            if (
                isinstance(title, str)
                and title.strip()
            ):
                self.title = title.strip()

            self.dark_mode = bool(
                data.get(
                    "dark_mode",
                    False
                )
            )

            counters = data.get(
                "counter_names"
            )

            if (
                isinstance(counters, list)
                and counters
            ):
                valid_counters = [
                    str(name).strip()
                    for name in counters
                    if str(name).strip()
                ]

                if valid_counters:
                    self.counter_names = (
                        valid_counters
                    )

            saved_players = data.get(
                "players"
            )

            if isinstance(
                saved_players,
                list
            ):
                loaded_players = []

                for index, saved in enumerate(
                    saved_players
                ):
                    if not isinstance(
                        saved,
                        dict
                    ):
                        continue

                    player = Player(
                        index + 1,
                        len(self.counter_names)
                    )

                    name = saved.get(
                        "name"
                    )

                    if (
                        isinstance(name, str)
                        and name.strip()
                    ):
                        player.name = name.strip()

                    group = saved.get(
                        "group"
                    )

                    if group in GROUP_COLORS:
                        player.group = group

                    values = saved.get(
                        "values"
                    )

                    if isinstance(
                        values,
                        list
                    ):
                        player.values = [
                            str(
                                self.parse_int(
                                    value
                                )
                            )
                            for value in values
                        ]

                    # Normalize values to current
                    # counter count.
                    if len(player.values) < len(
                        self.counter_names
                    ):
                        player.values.extend(
                            ["0"] *
                            (
                                len(self.counter_names)
                                - len(player.values)
                            )
                        )

                    elif len(player.values) > len(
                        self.counter_names
                    ):
                        player.values = player.values[
                            :len(self.counter_names)
                        ]

                    loaded_players.append(
                        player
                    )

                if loaded_players:
                    self.players = loaded_players

        except (
            OSError,
            json.JSONDecodeError,
            TypeError,
            ValueError
        ):
            pass
