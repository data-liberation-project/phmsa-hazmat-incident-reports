import argparse
import sys

from ..lib.scraper import QUERY_FIELDS, fetch


def parse_args(args: list[str]) -> argparse.Namespace:
    parser = argparse.ArgumentParser()
    parser.add_argument("--debug", action="store_true")
    parser.add_argument("--quiet", action="store_true")
    parser.add_argument("--expand", action="store_true")
    parser.add_argument("--outfile", type=argparse.FileType("wb"))
    for field in QUERY_FIELDS:
        parser.add_argument(
            f"--{field.replace('_', '-')}", help="(For query.)", required=True
        )
    return parser.parse_args(args)


def main() -> None:
    args = parse_args(sys.argv[1:])
    file_bytes = fetch(**vars(args))
    out = args.outfile if args.outfile else sys.stdout.buffer
    out.write(file_bytes)


if __name__ == "__main__":
    main()
