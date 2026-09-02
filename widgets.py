import tkinter as tk


class CustomScrollbar(tk.Canvas):
    def __init__(
        self,
        master,
        orient="vertical",
        command=None,
        **kwargs
    ):
        self.orient = orient
        self.command = command

        self.track_color = "#18191a"
        self.thumb_color = "#3c4043"
        self.thumb_hover_color = "#606368"

        self.first = 0.0
        self.last = 1.0

        self.dragging = False
        self.drag_offset = 0

        super().__init__(
            master,
            width=14 if orient == "vertical" else 0,
            height=14 if orient == "horizontal" else 0,
            bg=self.track_color,
            highlightthickness=0,
            borderwidth=0,
            relief="flat",
            **{
                key: value
                for key, value in kwargs.items()
                if key not in (
                    "troughcolor",
                    "activebackground",
                    "highlightbackground",
                    "highlightcolor",
                    "bd",
                    "relief"
                )
            }
        )

        self.bind(
            "<Configure>",
            lambda event: self.redraw()
        )

        self.bind(
            "<Button-1>",
            self.on_press
        )

        self.bind(
            "<B1-Motion>",
            self.on_drag
        )

        self.bind(
            "<ButtonRelease-1>",
            self.on_release
        )

        self.bind(
            "<Enter>",
            self.on_enter
        )

        self.bind(
            "<Leave>",
            self.on_leave
        )

        self.thumb = self.create_rectangle(
            0,
            0,
            0,
            0,
            fill=self.thumb_color,
            outline=""
        )

    def configure(self, cnf=None, **kwargs):
        # Accept old Tk scrollbar-style configuration calls
        # without allowing native styling to interfere.
        if cnf:
            kwargs.update(cnf)

        if "bg" in kwargs:
            self.track_color = kwargs["bg"]

        if "troughcolor" in kwargs:
            self.track_color = kwargs["troughcolor"]

        if "activebackground" in kwargs:
            self.thumb_hover_color = kwargs["activebackground"]

        if "highlightbackground" in kwargs:
            kwargs.pop("highlightbackground")

        if "highlightcolor" in kwargs:
            kwargs.pop("highlightcolor")

        for key in (
            "troughcolor",
            "activebackground",
            "bd",
            "relief",
            "highlightbackground",
            "highlightcolor"
        ):
            kwargs.pop(key, None)

        if "bg" in kwargs:
            self.track_color = kwargs["bg"]

        if "background" in kwargs:
            self.track_color = kwargs.pop("background")

        kwargs.pop("arrowcolor", None)
        kwargs.pop("darkcolor", None)
        kwargs.pop("lightcolor", None)

        result = super().configure(
            kwargs
        )

        self.configure_canvas_colors()
        self.redraw()

        return result

    config = configure

    def configure_canvas_colors(self):
        super().configure(
            bg=self.track_color
        )

        self.itemconfigure(
            self.thumb,
            fill=self.thumb_color
        )

    def set(self, first, last):
        self.first = float(first)
        self.last = float(last)

        self.redraw()

    def redraw(self):
        width = self.winfo_width()
        height = self.winfo_height()

        if width <= 1 or height <= 1:
            return

        if self.orient == "vertical":
            length = height

            if self.last - self.first >= 0.999:
                self.itemconfigure(
                    self.thumb,
                    state="hidden"
                )
                return

            self.itemconfigure(
                self.thumb,
                state="normal"
            )

            thumb_start = int(
                self.first * length
            )

            thumb_end = int(
                self.last * length
            )

            minimum = 28

            if thumb_end - thumb_start < minimum:
                thumb_end = min(
                    length,
                    thumb_start + minimum
                )

            self.coords(
                self.thumb,
                1,
                thumb_start + 1,
                width - 1,
                thumb_end - 1
            )

        else:
            length = width

            if self.last - self.first >= 0.999:
                self.itemconfigure(
                    self.thumb,
                    state="hidden"
                )
                return

            self.itemconfigure(
                self.thumb,
                state="normal"
            )

            thumb_start = int(
                self.first * length
            )

            thumb_end = int(
                self.last * length
            )

            minimum = 28

            if thumb_end - thumb_start < minimum:
                thumb_end = min(
                    length,
                    thumb_start + minimum
                )

            self.coords(
                self.thumb,
                thumb_start + 1,
                1,
                thumb_end - 1,
                height - 1
            )

    def thumb_bounds(self):
        coords = self.coords(
            self.thumb
        )

        if not coords:
            return None

        return coords

    def on_enter(self, event):
        self.itemconfigure(
            self.thumb,
            fill=self.thumb_hover_color
        )

    def on_leave(self, event):
        if not self.dragging:
            self.itemconfigure(
                self.thumb,
                fill=self.thumb_color
            )

    def on_press(self, event):
        coords = self.thumb_bounds()

        if not coords:
            return

        if self.orient == "vertical":
            start = coords[1]
            end = coords[3]
            position = event.y
        else:
            start = coords[0]
            end = coords[2]
            position = event.x

        if start <= position <= end:
            self.dragging = True
            self.drag_offset = position - start

            self.itemconfigure(
                self.thumb,
                fill=self.thumb_hover_color
            )
            return

        # Clicking the track pages in the appropriate direction.
        if position < start:
            self.page(-1)
        elif position > end:
            self.page(1)

    def on_drag(self, event):
        if not self.dragging:
            return

        if self.orient == "vertical":
            length = self.winfo_height()
            position = event.y - self.drag_offset
        else:
            length = self.winfo_width()
            position = event.x - self.drag_offset

        coords = self.thumb_bounds()

        if not coords:
            return

        if self.orient == "vertical":
            thumb_length = coords[3] - coords[1]
        else:
            thumb_length = coords[2] - coords[0]

        usable = max(
            1,
            length - thumb_length
        )

        fraction = position / usable
        fraction = max(
            0.0,
            min(1.0, fraction)
        )

        if self.command:
            self.command(
                "moveto",
                fraction
            )

    def on_release(self, event):
        self.dragging = False

        self.itemconfigure(
            self.thumb,
            fill=self.thumb_hover_color
        )

    def page(self, amount):
        if self.command:
            self.command(
                "scroll",
                amount,
                "pages"
            )
