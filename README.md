# pomodoro 🍅

A clean, minimal, animated pomodoro timer for your terminal.

- Big animated countdown that adapts to your window size — shrink the terminal and it collapses into a single compact line
- Manual phase transitions: your break starts when *you* press enter, not when a timer decides
- Desktop notification (macOS, with sound) or terminal bell when a phase ends
- Zero dependencies — pure Python standard library

## Install

```sh
pipx install git+https://github.com/antallpt/pomodoro.git
```

Or from a local clone: `pip install .`

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
| `q` / `ctrl+c` | quit |

## Requirements

macOS or Linux · Python ≥ 3.9

## License

[MIT](LICENSE)
