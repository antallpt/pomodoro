import argparse

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
    
    if args.pause < 1:
        parser.error("pause must be at least 1 min")

    if args.duration < 1:
        parser.error("duration must be at least 1 min")
    
    if args.loops < 0:
        parser.error("loops must be at least 0 (infinite)")

    print(f"work={args.duration}min pause={args.pause}min loops={args.loops if args.loops else '∞'}")
    