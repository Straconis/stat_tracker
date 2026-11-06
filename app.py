import json
import sys
import webbrowser
import tkinter as tk
from pathlib import Path
from tkinter import messagebox, ttk

from version import APP_NAME, APP_VERSION
from runtime_paths import asset_path, data_directory
from models import Player
from persistence import PersistenceMixin
from theme import GROUP_COLORS, ThemeMixin
from widgets import CustomScrollbar


STARTING_PLAYERS = 10
STARTING_COUNTERS = 4


class App(ThemeMixin, PersistenceMixin):
    def __init__(self, root):
        self.root = root

        try:
            self.window_icon = tk.PhotoImage(file=str(asset_path("stat_tracker.png")))
            self.root.iconphoto(True, self.window_icon)
        except (OSError, tk.TclError):
            pass

        self.title = APP_NAME
        self.dark_mode = False
        self.locked = True

        self.data_dir = data_directory()

        self.data_dir.mkdir(
            parents=True,
            exist_ok=True
        )

        self.save_file = (
            self.data_dir
            / "tracker_data.json"
        )

        # Preserve source-checkout saves and the Windows-style path used by older Linux runs.
        legacy_paths = [asset_path("tracker_data.json")]
        if sys.platform != "win32":
            legacy_paths.append(Path.home() / "AppData" / "Local" / APP_NAME / "tracker_data.json")
        for legacy_save in legacy_paths:
            if not self.save_file.exists() and legacy_save.is_file():
                try:
                    self.save_file.write_text(legacy_save.read_text(encoding="utf-8"), encoding="utf-8")
                except OSError:
                    pass

        self.counter_names = [
            f"Counter {i + 1}"
            for i in range(STARTING_COUNTERS)
        ]

        self.players = [
            Player(
                i + 1,
                STARTING_COUNTERS
            )
            for i in range(STARTING_PLAYERS)
        ]

        self.load_state()

        self.style = ttk.Style(root)

        self.root.title(
            f"{self.title} v{APP_VERSION}"
        )

        self.root.minsize(
            850,
            460
        )

        self.build_ui()
        self.build_branding()
        self.apply_theme()
        self.rebuild_grid()

        self.root.protocol(
            "WM_DELETE_WINDOW",
            self.close
        )

    # =========================================================
    # COLORS
    # =========================================================

    def build_ui(self):
        self.outer = tk.Frame(
            self.root,
            bg=self.canvas_bg()
        )

        self.outer.pack(
            fill="both",
            expand=True,
            padx=10,
            pady=10
        )

        # -----------------------------------------------------
        # Tracker title
        # -----------------------------------------------------

        self.title_entry = tk.Entry(
            self.outer,
            justify="center",
            font=("TkDefaultFont", 16, "bold"),
            relief="solid",
            borderwidth=1
        )

        self.title_entry.insert(
            0,
            self.title
        )

        self.title_entry.pack(
            pady=(0, 8)
        )

        self.title_entry.bind(
            "<Return>",
            lambda event: self.save_title()
        )

        self.title_entry.bind(
            "<FocusOut>",
            lambda event: self.save_title()
        )

        # -----------------------------------------------------
        # Tracker area
        # -----------------------------------------------------

        tracker_container = tk.Frame(
            self.outer,
            bg=self.canvas_bg()
        )

        tracker_container.pack(
            fill="both",
            expand=True
        )

        self.canvas = tk.Canvas(
            tracker_container,
            bg=self.canvas_bg(),
            highlightthickness=0,
            borderwidth=0
        )

        self.canvas.grid(
            row=0,
            column=0,
            sticky="nsew"
        )

        self.v_scroll = CustomScrollbar(
            tracker_container,
            orient="vertical",
            command=self.canvas.yview
        )

        self.v_scroll.grid(
            row=0,
            column=1,
            sticky="ns"
        )

        self.h_scroll = CustomScrollbar(
            tracker_container,
            orient="horizontal",
            command=self.canvas.xview
        )

        self.h_scroll.grid(
            row=1,
            column=0,
            sticky="ew"
        )

        tracker_container.rowconfigure(
            0,
            weight=1
        )

        tracker_container.columnconfigure(
            0,
            weight=1
        )

        self.grid_frame = tk.Frame(
            self.canvas,
            bg=self.canvas_bg()
        )

        self.canvas.create_window(
            (0, 0),
            window=self.grid_frame,
            anchor="nw"
        )

        self.canvas.configure(
            xscrollcommand=self.h_scroll.set,
            yscrollcommand=self.v_scroll.set
        )

        # Bind the mouse wheel at the application level so
        # Entries, Buttons, and other child widgets cannot
        # swallow the scrolling event.
        self.root.bind_all("<Button-4>", lambda _event: self.canvas.yview_scroll(-1, "units"))
        self.root.bind_all("<Button-5>", lambda _event: self.canvas.yview_scroll(1, "units"))
        self.root.bind_all(
            "<MouseWheel>",
            self.on_mousewheel
        )

        self.grid_frame.bind(
            "<Configure>",
            lambda event: self.update_scroll_region()
        )

        # -----------------------------------------------------
        # Bottom controls
        # -----------------------------------------------------

        self.controls = tk.Frame(
            self.outer,
            bg=self.canvas_bg()
        )

        self.controls.pack(
            fill="x",
            pady=(8, 0)
        )

        # Player controls.
        self.player_controls = tk.Frame(
            self.controls,
            bg=self.canvas_bg()
        )

        self.player_controls.pack(
            side="left"
        )

        self.add_player_button = tk.Button(
            self.player_controls,
            text="+ Add Player",
            command=self.add_player
        )

        self.add_player_button.pack(
            side="left",
            padx=(0, 5)
        )

        self.remove_player_button = tk.Button(
            self.player_controls,
            text="− Remove Player",
            command=self.remove_player
        )

        self.remove_player_button.pack(
            side="left"
        )

        # Counter controls.
        self.counter_controls = tk.Frame(
            self.controls,
            bg=self.canvas_bg()
        )

        self.counter_controls.pack(
            side="left",
            padx=(10, 0)
        )

        self.add_counter_button = tk.Button(
            self.counter_controls,
            text="+ Add Counter",
            command=self.add_counter
        )

        self.add_counter_button.pack(
            side="left",
            padx=(0, 5)
        )

        self.remove_counter_button = tk.Button(
            self.counter_controls,
            text="− Remove Counter",
            command=self.remove_counter
        )

        self.remove_counter_button.pack(
            side="left"
        )

        # Right-side controls.
        self.right_controls = tk.Frame(
            self.controls,
            bg=self.canvas_bg()
        )

        self.right_controls.pack(
            side="right"
        )

        self.reset_button = tk.Button(
            self.right_controls,
            text="Reset Counters",
            command=self.reset
        )

        self.reset_button.pack(
            side="left",
            padx=3
        )

        self.reset_groups_button = tk.Button(
            self.right_controls,
            text="Reset Groups",
            command=self.reset_groups
        )

        self.reset_groups_button.pack(
            side="left",
            padx=3
        )

        self.dark_button = tk.Button(
            self.right_controls,
            text="Dark Mode",
            command=self.toggle_dark_mode
        )

        self.dark_button.pack(
            side="left",
            padx=3
        )

        self.lock_button = tk.Button(
            self.right_controls,
            text="🔒 Unlock Editing",
            command=self.toggle_lock
        )

        self.lock_button.pack(
            side="left",
            padx=3
        )

        self.quit_button = tk.Button(
            self.right_controls,
            text="Quit",
            command=self.close
        )

        self.quit_button.pack(
            side="left",
            padx=(3, 0)
        )

    # =========================================================
    # GRID
    # =========================================================

    def build_branding(self):
        self.brand_footer = tk.Frame(self.outer, bg=self.canvas_bg())
        self.brand_footer.pack(side="bottom", fill="x", pady=(8, 0))
        self.brand_image = tk.PhotoImage(file=str(asset_path("assets/branding/straconis-software-wordmark.png"))).subsample(8, 8)
        self.brand_link = tk.Label(self.brand_footer, image=self.brand_image,
                                   bg=self.canvas_bg(), cursor="hand2", takefocus=True,
                                   name="straconis_software")
        self.brand_link.pack(side="left")
        self.brand_link.bind("<Button-1>", lambda _event: webbrowser.open("https://straconis.dev"))
        self.brand_link.bind("<Return>", lambda _event: webbrowser.open("https://straconis.dev"))
        self.brand_link.bind("<space>", lambda _event: webbrowser.open("https://straconis.dev"))

    def rebuild_grid(self):
        for widget in self.grid_frame.winfo_children():
            widget.destroy()

        # -----------------------------------------------------
        # Header
        # -----------------------------------------------------

        header_bg = self.canvas_bg()
        header_fg = self.text_color()

        tk.Label(
            self.grid_frame,
            text="Player",
            font=("TkDefaultFont", 10, "bold"),
            bg=header_bg,
            fg=header_fg
        ).grid(
            row=0,
            column=0,
            padx=6,
            pady=5
        )

        tk.Label(
            self.grid_frame,
            text="Group",
            font=("TkDefaultFont", 10, "bold"),
            bg=header_bg,
            fg=header_fg
        ).grid(
            row=0,
            column=1,
            padx=4,
            pady=5
        )

        counter_start = 2

        for index, name in enumerate(
            self.counter_names
        ):
            header = tk.Entry(
                self.grid_frame,
                width=14,
                justify="center",
                relief="solid",
                borderwidth=1,
                bg=self.entry_bg(),
                fg=self.text_color(),
                insertbackground=self.text_color()
            )

            header.insert(
                0,
                name
            )

            header.grid(
                row=0,
                column=counter_start + index,
                padx=4,
                pady=3
            )

            header.bind(
                "<Return>",
                lambda event, i=index, e=header:
                self.save_counter_name(i, e)
            )

            header.bind(
                "<FocusOut>",
                lambda event, i=index, e=header:
                self.save_counter_name(i, e)
            )

            if self.locked:
                header.configure(
                    state="readonly",
                    readonlybackground=self.entry_readonly_bg()
                )

        # -----------------------------------------------------
        # Player rows
        # -----------------------------------------------------

        for row_index, player in enumerate(
            self.players,
            start=1
        ):
            self.build_player_row(
                player,
                row_index,
                counter_start
            )

        self.update_controls()

        self.grid_frame.update_idletasks()
        self.update_scroll_region()

    def build_player_row(
        self,
        player,
        row_index,
        counter_start
    ):
        group_color = self.group_color(
            player.group
        )

        row_bg = (
            group_color
            if group_color
            else self.canvas_bg()
        )

        # -----------------------------------------------------
        # THIS IS THE IMPORTANT PART:
        #
        # One actual frame spans the ENTIRE player row.
        # The highlight therefore exists behind every counter.
        # -----------------------------------------------------

        row_frame = tk.Frame(
            self.grid_frame,
            bg=row_bg,
            borderwidth=0
        )

        row_frame.grid(
            row=row_index,
            column=0,
            columnspan=counter_start + len(
                self.counter_names
            ),
            sticky="ew",
            padx=2,
            pady=1
        )

        # Make the row wide enough for all columns.
        row_frame.grid_columnconfigure(
            0,
            minsize=130
        )

        # -----------------------------------------------------
        # Player name
        # -----------------------------------------------------

        name_entry = tk.Entry(
            row_frame,
            width=18,
            relief="solid",
            borderwidth=1,
            bg=(
                group_color
                if group_color
                else self.entry_bg()
            ),
            fg=(
                "#111111"
                if group_color
                else self.text_color()
            ),
            insertbackground=(
                "#111111"
                if group_color
                else self.text_color()
            )
        )

        name_entry.insert(
            0,
            player.name
        )

        name_entry.grid(
            row=0,
            column=0,
            padx=(4, 3),
            pady=2
        )

        name_entry.bind(
            "<Return>",
            lambda event, p=player, e=name_entry:
            self.save_player_name(p, e)
        )

        name_entry.bind(
            "<FocusOut>",
            lambda event, p=player, e=name_entry:
            self.save_player_name(p, e)
        )

        if self.locked:
            name_entry.configure(
                state="readonly",
                readonlybackground=(
                    group_color
                    if group_color
                    else self.entry_readonly_bg()
                )
            )

        # -----------------------------------------------------
        # Group selector
        # -----------------------------------------------------

        group_button = tk.Button(
            row_frame,
            text=self.group_button_text(
                player.group
            ),
            width=9,
            command=lambda p=player:
            self.choose_group(p)
        )

        group_button.grid(
            row=0,
            column=1,
            padx=4,
            pady=2
        )

        if self.locked:
            group_button.configure(
                state="disabled"
            )

        # -----------------------------------------------------
        # Counters
        # -----------------------------------------------------

        for counter_index in range(
            len(self.counter_names)
        ):
            self.make_counter_cell(
                row_frame,
                player,
                counter_index,
                counter_start
            )

    def make_counter_cell(
        self,
        row_frame,
        player,
        counter_index,
        counter_start
    ):
        cell_bg = self.group_color(
            player.group
        )

        if cell_bg is None:
            cell_bg = self.canvas_bg()

        cell = tk.Frame(
            row_frame,
            bg=cell_bg,
            borderwidth=0
        )

        cell.grid(
            row=0,
            column=counter_start + counter_index,
            padx=2,
            pady=2
        )

        tk.Button(
            cell,
            text="−",
            width=3,
            command=lambda p=player, i=counter_index:
            self.change_value(p, i, -1)
        ).grid(
            row=0,
            column=0
        )

        entry = tk.Entry(
            cell,
            width=7,
            justify="center",
            relief="solid",
            borderwidth=1,
            bg=self.entry_bg(),
            fg=self.text_color(),
            insertbackground=self.text_color()
        )

        entry.insert(
            0,
            player.values[counter_index]
        )

        entry.grid(
            row=0,
            column=1,
            padx=2
        )

        entry.bind(
            "<Return>",
            lambda event, p=player, i=counter_index, e=entry:
            self.save_value(p, i, e)
        )

        entry.bind(
            "<FocusOut>",
            lambda event, p=player, i=counter_index, e=entry:
            self.save_value(p, i, e)
        )

        # Keep direct access to the live counter Entry widgets.
        # This lets +/- update only the affected value instead
        # of rebuilding the entire grid.
        if not hasattr(
            player,
            "value_entries"
        ):
            player.value_entries = []

        while len(
            player.value_entries
        ) <= counter_index:
            player.value_entries.append(
                None
            )

        player.value_entries[
            counter_index
        ] = entry

        # Counter values stay editable even when structural
        # editing is locked.

        tk.Button(
            cell,
            text="+",
            width=3,
            command=lambda p=player, i=counter_index:
            self.change_value(p, i, 1)
        ).grid(
            row=0,
            column=2
        )

    # =========================================================
    # TITLE / NAMES / VALUES
    # =========================================================

    def save_title(self):
        title = self.title_entry.get().strip()

        if title:
            self.title = title

            self.root.title(
                f"{self.title} v{APP_VERSION}"
            )

            self.save_state()

        else:
            self.title_entry.delete(
                0,
                tk.END
            )

            self.title_entry.insert(
                0,
                self.title
            )

    def save_player_name(
        self,
        player,
        entry
    ):
        name = entry.get().strip()

        if name:
            player.name = name
            self.save_state()

    def save_counter_name(
        self,
        index,
        entry
    ):
        name = entry.get().strip()

        if name:
            self.counter_names[index] = name
            self.save_state()

        else:
            entry.delete(
                0,
                tk.END
            )

            entry.insert(
                0,
                self.counter_names[index]
            )

    def save_value(
        self,
        player,
        index,
        entry
    ):
        value = self.parse_int(
            entry.get()
        )

        player.values[index] = str(
            value
        )

        self.save_state()

        entry.delete(
            0,
            tk.END
        )

        entry.insert(
            0,
            str(value)
        )

    @staticmethod
    def parse_int(value):
        try:
            return int(value)
        except (
            TypeError,
            ValueError
        ):
            return 0

    # =========================================================
    # COUNTERS
    # =========================================================

    def change_value(
        self,
        player,
        index,
        amount
    ):
        value = self.parse_int(
            player.values[index]
        )

        new_value = str(
            value + amount
        )

        player.values[index] = new_value

        # Update only the affected counter entry instead of
        # rebuilding the entire grid. Rebuilding here causes
        # a visible UI flash on every +/- click.
        entries = getattr(
            player,
            "value_entries",
            []
        )

        if (
            index < len(entries)
            and entries[index] is not None
        ):
            widget = entries[index]

            try:
                widget.delete(
                    0,
                    tk.END
                )

                widget.insert(
                    0,
                    new_value
                )

            except (
                tk.TclError,
                AttributeError
            ):
                pass

        self.save_state()

    def add_counter(self):
        if self.locked:
            return

        number = len(
            self.counter_names
        ) + 1

        self.counter_names.append(
            f"Counter {number}"
        )

        for player in self.players:
            player.values.append(
                "0"
            )

        self.save_state()
        self.rebuild_grid()

    def remove_counter(self):
        if self.locked:
            return

        if len(self.counter_names) <= 1:
            messagebox.showinfo(
                "Cannot Remove Counter",
                "The tracker must have at least one counter."
            )
            return

        name = self.counter_names[-1]

        if not messagebox.askyesno(
            "Remove Counter",
            f'Remove "{name}" and all of its player values?'
        ):
            return

        self.counter_names.pop()

        for player in self.players:
            player.values.pop()

        self.save_state()
        self.rebuild_grid()

    # =========================================================
    # PLAYERS
    # =========================================================

    def add_player(self):
        if self.locked:
            return

        number = len(
            self.players
        ) + 1

        self.players.append(
            Player(
                number,
                len(self.counter_names)
            )
        )

        self.save_state()
        self.rebuild_grid()

    def remove_player(self):
        if self.locked:
            return

        if len(self.players) <= 1:
            messagebox.showinfo(
                "Cannot Remove Player",
                "The tracker must have at least one player."
            )
            return

        player = self.players[-1]

        if not messagebox.askyesno(
            "Remove Player",
            f'Remove "{player.name}" and all of their values?'
        ):
            return

        self.players.pop()

        self.save_state()
        self.rebuild_grid()

    # =========================================================
    # GROUPS
    # =========================================================

    def group_button_text(
        self,
        group
    ):
        if group == "None":
            return "No Group"

        return group

    def choose_group(self, player):
        if self.locked:
            return

        popup = tk.Toplevel(self.root)
        popup.title("Choose Player Group")
        popup.resizable(False, False)
        popup.transient(self.root)
        popup.grab_set()

        bg = self.canvas_bg()
        fg = self.text_color()

        popup.configure(bg=bg)

        tk.Label(
            popup,
            text=f"Group for {player.name}",
            font=("TkDefaultFont", 10, "bold"),
            bg=bg,
            fg=fg
        ).pack(
            padx=12,
            pady=(10, 8)
        )

        palette = (
            DARK_GROUP_COLORS
            if self.dark_mode
            else GROUP_COLORS
        )

        colors_frame = tk.Frame(
            popup,
            bg=bg
        )

        colors_frame.pack(
            padx=10,
            pady=(0, 10)
        )

        def select_group(group):
            player.group = group
            self.save_state()
            popup.destroy()
            self.rebuild_grid()

        groups = list(GROUP_COLORS.keys())

        for index, group in enumerate(groups):
            color = palette[group]

            if color is None:
                button_bg = (
                    "#303134"
                    if self.dark_mode
                    else "#ffffff"
                )
                button_fg = fg
            else:
                button_bg = color
                button_fg = "#111111"

            button = tk.Button(
                colors_frame,
                text="No Group" if group == "None" else group,
                width=11,
                height=2,
                bg=button_bg,
                fg=button_fg,
                activebackground=button_bg,
                activeforeground=button_fg,
                relief="raised",
                command=lambda g=group:
                    select_group(g)
            )

            button.grid(
                row=index // 2,
                column=index % 2,
                padx=4,
                pady=4
            )

        popup.update_idletasks()

        x = self.root.winfo_rootx() + (
            self.root.winfo_width() // 2
        ) - (
            popup.winfo_width() // 2
        )

        y = self.root.winfo_rooty() + (
            self.root.winfo_height() // 2
        ) - (
            popup.winfo_height() // 2
        )

        popup.geometry(
            f"+{max(x, 0)}+{max(y, 0)}"
        )

    def cycle_group(
        self,
        player
    ):
        if self.locked:
            return

        groups = list(
            GROUP_COLORS.keys()
        )

        current = groups.index(
            player.group
        )

        player.group = groups[
            (current + 1) % len(groups)
        ]

        self.save_state()
        self.rebuild_grid()

    # =========================================================
    # LOCK
    # =========================================================

    def toggle_lock(self):
        self.locked = not self.locked

        self.rebuild_grid()

    def update_controls(self):
        if self.locked:
            self.lock_button.configure(
                text="Editing Locked - Unlock"
            )

            self.title_entry.configure(
                state="readonly",
                readonlybackground=self.entry_readonly_bg(),
                fg=self.text_color()
            )

            self.add_player_button.configure(
                state="disabled"
            )

            self.remove_player_button.configure(
                state="disabled"
            )

            self.add_counter_button.configure(
                state="disabled"
            )

            self.remove_counter_button.configure(
                state="disabled"
            )

        else:
            self.lock_button.configure(
                text="Editing Unlocked - Lock"
            )

            self.title_entry.configure(
                state="normal"
            )

            self.add_player_button.configure(
                state="normal"
            )

            self.remove_player_button.configure(
                state="normal"
            )

            self.add_counter_button.configure(
                state="normal"
            )

            self.remove_counter_button.configure(
                state="normal"
            )

    # =========================================================
    # RESET
    # =========================================================

    def reset_groups(self):
        if not messagebox.askyesno(
            "Reset Groups",
            "Remove all player group assignments?"
        ):
            return

        for player in self.players:
            player.group = "None"

        self.save_state()
        self.rebuild_grid()

    def reset(self):
        if not messagebox.askyesno(
            "Reset Counters",
            "Reset every counter for every player to 0?"
        ):
            return

        for player in self.players:
            player.values = [
                "0"
                for _ in self.counter_names
            ]

        self.save_state()
        self.rebuild_grid()

    # =========================================================
    # DARK MODE
    # =========================================================

    # =========================================================
    # MISC
    # =========================================================

    def on_mousewheel(self, event):
        # Windows normally reports MouseWheel in multiples of
        # 120, but some mice/drivers use smaller increments.
        # Accumulate the delta so small wheel movements still
        # produce reliable scrolling.
        if not hasattr(self, "_wheel_remainder"):
            self._wheel_remainder = 0

        self._wheel_remainder += event.delta

        units = int(
            self._wheel_remainder / 120
        )

        if units != 0:
            self._wheel_remainder -= units * 120

            self.canvas.yview_scroll(
                -units,
                "units"
            )

    def update_scroll_region(self):
        self.canvas.configure(
            scrollregion=self.canvas.bbox(
                "all"
            )
        )

    def close(self):
        self.save_state()
        self.root.destroy()


if __name__ == "__main__":
    smoke_test = "--smoke-test" in sys.argv
    root = tk.Tk()
    if smoke_test:
        root.withdraw()
    app = App(root)
    if smoke_test:
        root.after(200, root.destroy)
    root.mainloop()
