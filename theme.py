GROUP_COLORS = {
    "None": None,
    "Green": "#7fc97f",
    "Orange": "#fdb462",
    "Blue": "#80b1d3",
    "Purple": "#bebada",
    "Yellow": "#ffed6f",
    "Red": "#fb8072",
    "Pink": "#fdb5d5",
}


DARK_GROUP_COLORS = {
    "None": None,
    "Green": "#315b35",
    "Orange": "#714820",
    "Blue": "#294e67",
    "Purple": "#514b70",
    "Yellow": "#6b5e18",
    "Red": "#71332e",
    "Pink": "#704858",
}


class ThemeMixin:
    def canvas_bg(self):
        return (
            "#202124"
            if self.dark_mode
            else "#ffffff"
        )

    def text_color(self):
        return (
            "#f1f3f4"
            if self.dark_mode
            else "#000000"
        )

    def entry_bg(self):
        return (
            "#303134"
            if self.dark_mode
            else "#ffffff"
        )

    def entry_readonly_bg(self):
        return (
            "#28292b"
            if self.dark_mode
            else "#f0f0f0"
        )

    def group_color(self, group):
        palette = (
            DARK_GROUP_COLORS
            if self.dark_mode
            else GROUP_COLORS
        )

        return palette.get(group)

    # =========================================================
    # UI
    # =========================================================

    def toggle_dark_mode(self):
        self.dark_mode = not self.dark_mode

        self.save_state()

        self.apply_theme()
        self.rebuild_grid()

    def apply_theme(self):
        bg = self.canvas_bg()
        fg = self.text_color()

        self.root.configure(
            bg=bg
        )

        self.outer.configure(
            bg=bg
        )

        self.canvas.configure(
            bg=bg
        )

        self.grid_frame.configure(
            bg=bg
        )

        self.controls.configure(
            bg=bg
        )

        self.player_controls.configure(
            bg=bg
        )

        self.counter_controls.configure(
            bg=bg
        )

        self.right_controls.configure(
            bg=bg
        )

        self.title_entry.configure(
            bg=self.entry_bg(),
            fg=fg,
            insertbackground=fg,
            readonlybackground=self.entry_readonly_bg()
        )

        button_bg = (
            "#3c4043"
            if self.dark_mode
            else "#f0f0f0"
        )

        button_fg = (
            "#f1f3f4"
            if self.dark_mode
            else "#000000"
        )

        buttons = [
            self.add_player_button,
            self.remove_player_button,
            self.add_counter_button,
            self.remove_counter_button,
            self.reset_button,
            self.reset_groups_button,
            self.dark_button,
            self.lock_button,
            self.quit_button
        ]

        for button in buttons:
            button.configure(
                bg=button_bg,
                fg=button_fg,
                activebackground=(
                    "#505357"
                    if self.dark_mode
                    else "#d9d9d9"
                ),
                activeforeground=button_fg
            )

        if self.dark_mode:
            self.dark_button.configure(
                text="☀ Light Mode"
            )

            self.v_scroll.redraw()
            self.h_scroll.redraw()

        else:
            self.dark_button.configure(
                text="Dark Mode"
            )

            self.v_scroll.redraw()
            self.h_scroll.redraw()

    # =========================================================
    # PERSISTENCE
    # =========================================================
