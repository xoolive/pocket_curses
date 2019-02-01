import configparser
import curses
import sys
import webbrowser
from pathlib import Path
from textwrap import wrap

import pyperclip
from appdirs import user_config_dir

from pocket import Pocket

help_msg = """
'?'                        display this help
'q', Ctrl-C                quit

'h', LEFT, PAGE_UP         previous page
'j', DOWN                  next item
'k', UP                    previous item
'l', RIGHT, PAGE_DOWN      next page

'a', 'e'                   archive item then refresh
'd', 'x'                   delete item (with confirmation) then refresh
'r', F5                    refresh list

'c'                        copy link to clipboard
'm'                        open link in new mail
'o', ENTER                 open link in browser
"""

basic_config = """
[global]
consumer_key = 
access_token = 
"""


class PocketAPI:
    def __init__(self, consumer_key, access_token):
        self.pocket = Pocket(consumer_key=consumer_key, access_token=access_token)
        self.retrieve()

    def retrieve(self):
        self.json = self.pocket.retrieve()

    def __len__(self):
        return len(self.json["list"])

    def __getitem__(self, select):
        for i, elt in enumerate(self.json["list"].values()):
            if i == select:
                return elt

    def __iter__(self):
        yield from self.json["list"].values()


class PocketScreen:
    def __init__(self, consumer_key, access_token):

        super().__init__()

        self.api = PocketAPI(consumer_key, access_token)
        self.screen = curses.initscr()
        self.init_curses()

        self.cursor_x, self.cursor_y = 3, 2
        self.page_select, self.elt_select = 0, 0
        self.help_flag = False

    @property
    def elt_id(self):
        return self.page_select * self.max_elt + self.elt_select

    @property
    def nb_pages(self):
        if self.max_elt == 0:
            return 0
        return (len(self.api) - 1) // self.max_elt + 1

    def init_curses(self):
        curses.noecho()
        curses.mousemask(1)
        curses.start_color()
        curses.init_pair(1, curses.COLOR_CYAN, curses.COLOR_BLACK)
        self.screen.keypad(True)

    def reset_cursor_pos(self):
        self.screen.move(self.cursor_y, self.cursor_x)

    def assess_screen(self):
        self.scr_h, self.scr_w = self.screen.getmaxyx()
        self.max_elt = (self.scr_h - 12) // 3

    def draw_frame(self):
        header = " Pocket [{}] ({}/{}) "
        header += "('q' or Ctrl+C to exit, '?' to get help) "
        infos = len(self.api), self.page_select + 1, self.nb_pages
        self.screen.border(0)
        self.screen.addstr(0, 2, header.format(*infos))

        if self.nb_pages <= 0:
            self.screen.addstr(2, 2, "Enlarge the terminal window.")
            return

        if self.help_flag is True:

            if self.scr_h <= len(help_msg.split("\n")):
                self.screen.addstr(2, 2, "Enlarge the terminal window.")
                return

            for i, line in enumerate(help_msg.split("\n")):
                self.screen.addstr(1 + i, 2, line)

            self.screen.move(0, 0)

            return

        self.box = self.screen.subwin(8, self.scr_w - 6, self.scr_h - 10, 3)
        self.box.box()

        for i, elt in enumerate(self.api):
            i -= self.page_select * self.max_elt
            if i < 0:
                continue
            if i > self.max_elt - 1:
                break
            self.screen.addstr(2 + 3 * i, 2, f"[ ]")

            title = elt.get("resolved_title", elt["given_title"])
            url = elt.get("resolved_url", elt["given_url"])

            if len(title) > self.scr_w - 10:
                title = title[: self.scr_w - 14]
                self.screen.addstr(2 + 3 * i, self.scr_w - 7, "[...]", curses.A_DIM)
            self.screen.addstr(2 + 3 * i, 7, title)

            if len(url) > self.scr_w - 10:
                url = url[: self.scr_w - 14]
                self.screen.addstr(
                    3 + 3 * i,
                    self.scr_w - 7,
                    "[...]",
                    curses.A_DIM | curses.color_pair(1),
                )
            self.screen.addstr(3 + 3 * i, 7, url, curses.color_pair(1))

        self.preview()
        self.reset_cursor_pos()

    def preview(self):
        self.box.erase()
        self.box.box()

        elt = self.api[self.elt_id]
        for j, line in enumerate(wrap(elt.get("excerpt", ""), self.scr_w - 10)):
            if j < 4:
                self.box.addstr(2 + j, 2, line)
        self.box.refresh()
        return

    def run(self):
        self.assess_screen()

        while True:
            self.screen.clear()
            self.draw_frame()
            self.screen.refresh()

            c = self.screen.getch()

            if self.help_flag is True:
                self.help_flag = False
                continue

            resized = curses.is_term_resized(self.scr_h, self.scr_w)
            if resized is True:
                self.screen.clear()
                self.assess_screen()
                if self.cursor_x > self.scr_w or self.cursor_y > self.scr_h:
                    self.cursor_x, self.cursor_y = 3, 2
                    self.page_select, self.elt_select = 0, 0
                curses.resizeterm(self.scr_h, self.scr_w)
            self.draw_frame()
            self.screen.refresh()

            if c in [curses.KEY_DOWN, b"j"[0]]:
                sel = self.elt_select + 1

                if sel < (
                    self.max_elt
                    if self.page_select < self.nb_pages - 1
                    else len(self.api) - self.page_select * self.max_elt
                ):
                    self.cursor_y += 3
                    self.elt_select += 1
                self.reset_cursor_pos()
            elif c in [curses.KEY_UP, b"k"[0]]:
                sel = self.elt_select - 1
                if sel >= 0:
                    self.cursor_y -= 3
                    self.elt_select -= 1
                self.reset_cursor_pos()
            elif c in [curses.KEY_PPAGE, curses.KEY_LEFT, b"h"[0]]:
                sel = self.page_select - 1
                if sel >= 0:
                    self.cursor_y = 2
                    self.elt_select = 0
                    self.page_select -= 1
                self.reset_cursor_pos()
            elif c in [curses.KEY_NPAGE, curses.KEY_RIGHT, b"l"[0]]:
                sel = self.page_select + 1
                if sel < self.nb_pages:
                    self.cursor_y = 2
                    self.elt_select = 0
                    self.page_select += 1
                self.reset_cursor_pos()
            elif c in [curses.KEY_F5, b"r"[0]]:
                self.api.retrieve()
            elif c in [b"a"[0], b"e"[0]]:
                elt = self.api[self.elt_id]
                self.api.pocket.archive(elt["item_id"]).commit()
                self.api.pocket.retrieve()
            elif c in [b"d"[0], b"x"[0]]:
                self.screen.clear()
                msg = "Deleted items cannot be recovered. Press 'y' to confirm."
                self.screen.addstr(2, 2, msg)
                self.screen.refresh()
                c = self.screen.getch()
                if c == b"y"[0]:
                    elt = self.api[self.elt_id]
                    self.api.pocket.delete(elt["item_id"]).commit()
                    self.api.retrieve()
            elif c == b"c"[0]:
                elt = self.api[self.elt_id]
                pyperclip.copy(elt["resolved_url"])
            elif c in [10, b"o"[0]]:  # ENTER, o
                elt = self.api[self.elt_id]
                webbrowser.open(elt["resolved_url"])
            elif c == b"?"[0]:
                self.help_flag = True
            elif c == b"m"[0]:
                elt = self.api[self.elt_id]
                mailto = "mailto:?subject={subject}&body={body}"
                webbrowser.open(
                    mailto.format(
                        subject=elt["resolved_title"], body=elt["resolved_url"]
                    )
                )
            elif c in [27, int(b"q"[0])]:  # ESC, q
                raise KeyboardInterrupt


def main():
    config_dir = Path(user_config_dir("pocket"))
    config_file = config_dir / "pocket.conf"
    if not config_dir.exists():
        config_dir.mkdir(parents=True)

    if not config_file.exists():
        with config_file.open("w") as fh:
            fh.write(basic_config)

    config = configparser.ConfigParser()
    config.read(config_file.as_posix())

    consumer_key = config.get("global", "consumer_key", fallback="")
    access_token = config.get("global", "access_token", fallback="")

    if consumer_key == "" or access_token == "":
        raise RuntimeError(f"Fill login details in {config_file}")

    try:
        screen = PocketScreen(consumer_key, access_token)
        screen.run()
    except KeyboardInterrupt:
        sys.exit(0)
    finally:
        curses.endwin()


if __name__ == "__main__":
    main()
