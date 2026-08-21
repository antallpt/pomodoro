# pomodoro 🍅

A clean, minimal, animated pomodoro timer for your terminal.

- Big countdown digits in the figlet font *Big Money-nw*, with an animated dithered ASCII art panel beside them
- Fully responsive — shrink the window and the timer falls back to smaller block digits, then to a single compact line
- Manual phase transitions: your break starts when *you* press enter, not when a timer decides
- Desktop notification (macOS, with sound) or terminal bell when a phase ends
- Zero dependencies — pure Python standard library

## Install

The recommended way is [pipx](https://pipx.pypa.io/), which installs the `pomodoro` command globally in its own isolated environment:

```sh
# install pipx first if you don't have it
brew install pipx          # macOS
pipx ensurepath            # makes sure ~/.local/bin is on your PATH

pipx install git+https://github.com/antallpt/pomodoro.git
```

Open a new shell afterwards and `pomodoro` is available everywhere.

Alternative from a local clone: `pipx install .` (or `pip install .` into an environment of your choice).

## Usage

```sh
pomodoro -s                    # 25 min work · 5 min pause · endless loops
pomodoro -s -d 15 -p 5 -l 4    # 15 min work · 5 min pause · 4 loops
```

| Flag | Meaning | Default |
| --- | --- | --- |
| `-s`, `--start` | start the timer | – |
| `-d`, `--duration` | work duration in minutes | 25 |
| `-p`, `--pause` | pause duration in minutes | 5 |
| `-l`, `--loops` | number of loops, `0` = infinite | 0 |

## Keys

| Key | Action |
| --- | --- |
| `enter` | start the next phase |
| `a` | toggle the art animation on/off |
| `q` / `ctrl+c` | quit |

The art panel appears automatically when the window is wide enough (roughly 100+ columns).

## Requirements

macOS or Linux · Python ≥ 3.9

## License

[MIT](LICENSE)
