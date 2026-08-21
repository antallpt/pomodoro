"""A clean, minimal, animated pomodoro timer for your terminal."""

import argparse
import math
import os
import random
import select
import shutil
import subprocess
import sys
import termios
import time
import tty

SECONDS_PER_MIN = 60

RESET = "\x1b[0m"
BOLD = "\x1b[1m"
DIM = "\x1b[2m"
RED = "\x1b[38;5;203m"
GREEN = "\x1b[38;5;114m"
BLUE = "\x1b[38;5;68m"
ORANGE = "\x1b[38;5;173m"

ALT_SCREEN_ON = "\x1b[?1049h"
ALT_SCREEN_OFF = "\x1b[?1049l"
CURSOR_HIDE = "\x1b[?25l"
CURSOR_SHOW = "\x1b[?25h"
CURSOR_HOME = "\x1b[H"
CLEAR_LINE_END = "\x1b[K"
CLEAR_BELOW = "\x1b[J"

WORK = "WORK"
PAUSE = "PAUSE"
PHASE_COLOR = {WORK: RED, PAUSE: GREEN}

# medium fallback font for windows too small for the Big Money digits
BLOCK_ROWS = 5
BLOCK_FONT = {
    "0": ("███", "█ █", "█ █", "█ █", "███"),
    "1": (" █ ", " █ ", " █ ", " █ ", " █ "),
    "2": ("███", "  █", "███", "█  ", "███"),
    "3": ("███", "  █", "███", "  █", "███"),
    "4": ("█ █", "█ █", "███", "  █", "  █"),
    "5": ("███", "█  ", "███", "  █", "███"),
    "6": ("███", "█  ", "███", "█ █", "███"),
    "7": ("███", "  █", "  █", "  █", "  █"),
    "8": ("███", "█ █", "███", "█ █", "███"),
    "9": ("███", "█ █", "███", "  █", "███"),
    ":": ("   ", " █ ", "   ", " █ ", "   "),
}

# digits from the figlet font "Big Money-nw", embedded so there is no dependency
MONEY_ROWS = 8
MONEY_FONT = {
    '0': (
        ' $$$$$$\\  ',
        '$$$ __$$\\ ',
        '$$$$\\ $$ |',
        '$$\\$$\\$$ |',
        '$$ \\$$$$ |',
        '$$ |\\$$$ |',
        '\\$$$$$$  /',
        ' \\______/ ',
    ),
    '1': (
        '  $$\\   ',
        '$$$$ |  ',
        '\\_$$ |  ',
        '  $$ |  ',
        '  $$ |  ',
        '  $$ |  ',
        '$$$$$$\\ ',
        '\\______|',
    ),
    '2': (
        ' $$$$$$\\  ',
        '$$  __$$\\ ',
        '\\__/  $$ |',
        ' $$$$$$  |',
        '$$  ____/ ',
        '$$ |      ',
        '$$$$$$$$\\ ',
        '\\________|',
    ),
    '3': (
        ' $$$$$$\\  ',
        '$$ ___$$\\ ',
        '\\_/   $$ |',
        '  $$$$$ / ',
        '  \\___$$\\ ',
        '$$\\   $$ |',
        '\\$$$$$$  |',
        ' \\______/ ',
    ),
    '4': (
        '$$\\   $$\\ ',
        '$$ |  $$ |',
        '$$ |  $$ |',
        '$$$$$$$$ |',
        '\\_____$$ |',
        '      $$ |',
        '      $$ |',
        '      \\__|',
    ),
    '5': (
        '$$$$$$$\\  ',
        '$$  ____| ',
        '$$ |      ',
        '$$$$$$$\\  ',
        '\\_____$$\\ ',
        '$$\\   $$ |',
        '\\$$$$$$  |',
        ' \\______/ ',
    ),
    '6': (
        ' $$$$$$\\  ',
        '$$  __$$\\ ',
        '$$ /  \\__|',
        '$$$$$$$\\  ',
        '$$  __$$\\ ',
        '$$ /  $$ |',
        ' $$$$$$  |',
        ' \\______/ ',
    ),
    '7': (
        '$$$$$$$$\\ ',
        '\\____$$  |',
        '    $$  / ',
        '   $$  /  ',
        '  $$  /   ',
        ' $$  /    ',
        '$$  /     ',
        '\\__/      ',
    ),
    '8': (
        ' $$$$$$\\  ',
        '$$  __$$\\ ',
        '$$ /  $$ |',
        ' $$$$$$  |',
        '$$  __$$< ',
        '$$ /  $$ |',
        '\\$$$$$$  |',
        ' \\______/ ',
    ),
    '9': (
        ' $$$$$$\\  ',
        '$$  __$$\\ ',
        '$$ /  $$ |',
        '\\$$$$$$$ |',
        ' \\____$$ |',
        '$$\\   $$ |',
        '\\$$$$$$  |',
        ' \\______/ ',
    ),
    ':': (
        '    ',
        '    ',
        '$$\\ ',
        '\\__|',
        '    ',
        '$$\\ ',
        '\\__|',
        '    ',
    ),
}

# dithered art panel, stored as a density map (0 = empty, 1-4 = darker)
ART = (
    '00000002244433200100000000000000000113421000',
    '00000024244410121000010021000101000000134410',
    '00000222423013122112211123111111111111113420',
    '00001223330033231223232222322212222211214320',
    '00012232221232332322223312113222233232132220',
    '00032232222332332210112321001223213323223130',
    '00322232224244243221011232110111222423333001',
    '11223323333434433224321001212243233332233000',
    '12322322232334333111010010010011222432332000',
    '23433310120143331110001111100000133322320000',
    '34444433100033242232221111100112234110110000',
    '00113444300011142022233111131111400000000000',
    '01111234423312201013013122221222100000000000',
    '11122334444424221022211132223241411111100000',
    '22343434434434421031142133122222222443431000',
    '00122212434324322222112223122321010344441000',
    '00000000000001131211002211123111011244230000',
    '00000000000000321100102210022123234244341000',
)
ART_POOLS = {"1": ".'`", "2": ":;i", "3": "+*x", "4": "%#@"}


class Quit(Exception):
    pass


def format_mmss(seconds):
    minutes, secs = divmod(seconds, 60)
    return f"{minutes:02d}:{secs:02d}"


def money_time_lines(text):
    return ["  ".join(MONEY_FONT[c][row] for c in text if c in MONEY_FONT) for row in range(MONEY_ROWS)]


def block_time_lines(text, scale):
    gap = " " * scale
    rows = []
    for row in range(BLOCK_ROWS):
        cells = ["".join(ch * scale for ch in BLOCK_FONT[c][row]) for c in text if c in BLOCK_FONT]
        rows.append(gap.join(cells))
    return rows


def merge_panels(left, right, gap=6):
    def normalize(panel):
        width = max(len(plain) for plain, _styled in panel)
        return [
            (plain + " " * (width - len(plain)), styled + " " * (width - len(plain)))
            for plain, styled in panel
        ], width

    def vpad(panel, width, height):
        blank = (" " * width, " " * width)
        top = (height - len(panel)) // 2
        return [blank] * top + panel + [blank] * (height - len(panel) - top)

    left, left_w = normalize(left)
    right, right_w = normalize(right)
    height = max(len(left), len(right))
    left = vpad(left, left_w, height)
    right = vpad(right, right_w, height)
    spacer = " " * gap
    return [
        (lp + spacer + rp, ls + spacer + rs)
        for (lp, ls), (rp, rs) in zip(left, right)
    ]


def notify(message):
    if sys.platform == "darwin":
        text = message.replace('"', "'")
        script = f'display notification "{text}" with title "Pomodoro" sound name "Glass"'
        subprocess.run(
            ["osascript", "-e", script],
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL,
            check=False,
        )
    else:
        sys.stdout.write("\a")
        sys.stdout.flush()


def poll_keys(timeout):
    ready, _, _ = select.select([sys.stdin], [], [], timeout)
    if not ready:
        return ""
    return os.read(sys.stdin.fileno(), 8).decode(errors="replace")


class Pomodoro:
    def __init__(self, work_min, pause_min, loops):
        self.work_min = work_min
        self.pause_min = pause_min
        self.loops = loops  # 0 = infinite
        self.completed = 0
        self.animate = True

    def run(self):
        current = 1
        while True:
            self.countdown(WORK, self.work_min, current)
            self.completed += 1
            if self.loops and current == self.loops:
                notify("All pomodoros done — great work!")
                return
            notify("Work done — time for a break")
            self.wait_for_enter(PAUSE, current)
            self.countdown(PAUSE, self.pause_min, current)
            notify("Break over — back to work")
            current += 1
            self.wait_for_enter(WORK, current)

    def countdown(self, phase, minutes, current):
        total = minutes * SECONDS_PER_MIN
        end = time.monotonic() + total
        while True:
            remaining = max(0, math.ceil(end - time.monotonic()))
            frac = (total - remaining) / total
            self.draw(phase, current, format_mmss(remaining), frac, None)
            if remaining == 0:
                return
            self.handle_keys(poll_keys(0.1))

    def wait_for_enter(self, next_phase, current):
        minutes = self.pause_min if next_phase == PAUSE else self.work_min
        what = "your break" if next_phase == PAUSE else "the next pomodoro"
        message = "press enter to start " + what
        while True:
            self.draw(next_phase, current, format_mmss(minutes * SECONDS_PER_MIN), 0.0, message)
            keys = poll_keys(0.1)
            if "\r" in keys or "\n" in keys:
                return
            self.handle_keys(keys)

    def handle_keys(self, keys):
        lowered = keys.lower()
        if "q" in lowered:
            raise Quit
        if "a" in lowered:
            self.animate = not self.animate

    def loop_label(self, current):
        total = str(self.loops) if self.loops else "∞"
        return f"{current}/{total}"

    def timer_panel(self, header, time_rows, frac, message, color, time_color):
        width = max(len(row) for row in time_rows)
        filled = round(width * frac)

        def line(plain, styled=None):
            styled = plain if styled is None else styled
            pad_left = max(0, (width - len(plain)) // 2)
            pad_right = max(0, width - len(plain) - pad_left)
            return (" " * pad_left + plain + " " * pad_right,
                    " " * pad_left + styled + " " * pad_right)

        blank = line("")
        hint = "a · animation   q · quit"
        lines = [line(header, DIM + BOLD + header + RESET), blank]
        for row in time_rows:
            lines.append((row, time_color + row + RESET))
        lines.append(blank)
        bar_plain = "█" * filled + "░" * (width - filled)
        bar_styled = color + "█" * filled + RESET + DIM + "░" * (width - filled) + RESET
        lines.append((bar_plain, bar_styled))
        lines.append(blank)
        if message:
            lines.append(line(message))
            lines.append(blank)
        lines.append(line(hint, DIM + hint + RESET))
        return lines

    def art_panel(self):
        lines = []
        for row in ART:
            plain = []
            styled = []
            for cell in row:
                pool = ART_POOLS.get(cell)
                if pool is None:
                    plain.append(" ")
                    styled.append(" ")
                    continue
                char = pool[0]
                style = DIM
                if self.animate:
                    if random.random() < 0.10:
                        char = random.choice(pool)
                    roll = random.random()
                    if roll < 0.05:
                        style = BLUE
                    elif roll < 0.09:
                        style = ORANGE
                plain.append(char)
                styled.append(style + char + RESET)
            lines.append(("".join(plain), "".join(styled)))
        return lines

    def draw(self, phase, current, time_text, frac, message):
        cols, rows = shutil.get_terminal_size()
        color = PHASE_COLOR[phase]
        time_color = color if message is None else color + DIM
        header = f"{phase} · {self.loop_label(current)}"

        panel = None
        money = money_time_lines(time_text)
        if cols >= len(money[0]) + 4 and rows >= MONEY_ROWS + 10:
            panel = self.timer_panel(header, money, frac, message, color, time_color)
        else:
            for scale in (2, 1):
                block = block_time_lines(time_text, scale)
                if cols >= len(block[0]) + 4 and rows >= BLOCK_ROWS + 9:
                    panel = self.timer_panel(header, block, frac, message, color, time_color)
                    break

        if panel is not None:
            panel_width = max(len(plain) for plain, _styled in panel)
            if cols >= panel_width + len(ART[0]) + 10 and rows >= len(ART) + 4:
                panel = merge_panels(panel, self.art_panel())
            lines = panel
        else:
            tail = ("enter ↵", DIM) if message else (self.loop_label(current), DIM)
            candidates = [
                [(phase, DIM), (time_text, time_color), tail],
                [(phase, DIM), (time_text, time_color)],
                [(time_text, time_color)],
            ]
            for parts in candidates:
                plain = "  ".join(text for text, _style in parts)
                if len(plain) <= cols - 2:
                    break
            styled = "  ".join(style + text + RESET for text, style in parts)
            lines = [(plain, styled)]

        top = max(0, (rows - len(lines)) // 2)
        rendered = []
        for plain, styled in [("", "")] * top + lines:
            pad = " " * max(0, (cols - len(plain)) // 2)
            rendered.append(pad + styled + CLEAR_LINE_END)
        sys.stdout.write(CURSOR_HOME + "\n".join(rendered) + CLEAR_BELOW)
        sys.stdout.flush()


def main():
    parser = argparse.ArgumentParser(
        prog="pomodoro",
        description="A clean, minimal pomodoro timer for your terminal",
    )

    parser.add_argument(
        "-d", "--duration",
        type=int,
        default=25,
        metavar="MIN",
        help="work duration in minutes (default: 25)",
    )
    parser.add_argument(
        "-p", "--pause",
        type=int,
        default=5,
        metavar="MIN",
        help="pause duration in minutes (default: 5)",
    )
    parser.add_argument(
        "-l", "--loops",
        type=int,
        default=0,
        metavar="N",
        help="amount of loops (default: infinite)",
    )
    parser.add_argument(
        "-s", "--start",
        action="store_true",
        help="start the timer",
    )

    args = parser.parse_args()
    if not args.start:
        parser.print_help()
        return

    if args.duration < 1:
        parser.error("duration must be at least 1 min")

    if args.pause < 1:
        parser.error("pause must be at least 1 min")

    if args.loops < 0:
        parser.error("loops must be at least 0 (infinite)")

    if not (sys.stdin.isatty() and sys.stdout.isatty()):
        sys.exit("pomodoro: an interactive terminal (TTY) is required")

    timer = Pomodoro(args.duration, args.pause, args.loops)
    fd = sys.stdin.fileno()
    saved = termios.tcgetattr(fd)
    sys.stdout.write(ALT_SCREEN_ON + CURSOR_HIDE)
    sys.stdout.flush()
    tty.setcbreak(fd)
    try:
        timer.run()
    except (KeyboardInterrupt, Quit):
        pass
    finally:
        termios.tcsetattr(fd, termios.TCSADRAIN, saved)
        sys.stdout.write(CURSOR_SHOW + ALT_SCREEN_OFF)
        sys.stdout.flush()

    noun = "pomodoro" if timer.completed == 1 else "pomodoros"
    print(f"{timer.completed} {noun} completed 🍅")


if __name__ == "__main__":
    main()
