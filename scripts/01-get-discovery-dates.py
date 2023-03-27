import argparse
import csv
import io
import os
import re
import sys
from datetime import datetime, timezone

import git

RE_PATTERN = r"^(?:<a href = .*?>)?([A-Z]+-[0-9]+)(?:</A>)?$"


def parse_args(args: list[str]) -> argparse.Namespace:
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--year",
        type=int,
        default=datetime.now().year,
        help="The year of the month to start processing. Defaults to today's year.",
    )
    parser.add_argument(
        "--month",
        type=int,
        default=datetime.now().month,
        help="The month to start processing. Defaults to today's month.",
    )
    parser.add_argument(
        "--num-months",
        type=int,
        default=3,
        help="The number of months to process. Defaults to 3.",
    )
    parser.add_argument(
        "--forward",
        action="store_true",
        help="Go [num-months] forward, rather than backward.",
    )
    return parser.parse_args(args)


def prev_month(year: int, month: int) -> tuple[int, int]:
    if month == 1:
        return year - 1, 12
    else:
        return year, month - 1


def next_month(year: int, month: int) -> tuple[int, int]:
    if month == 12:
        return year + 1, 1
    else:
        return year, month + 1


def parse_report_number(report_number_str: str) -> str:
    match = re.match(RE_PATTERN, report_number_str)
    if match:
        return match.group(1)
    else:
        raise ValueError(f"could not parse from {report_number_str}")


def discover_dates(repo: git.Repo, path: str) -> dict[str, dict[str, str]]:
    discovered_dates = {}

    commits = repo.iter_commits("main", paths=[path], reverse=True)

    for commit in commits:
        dt = commit.committed_datetime.astimezone(timezone.utc).isoformat()
        try:
            blob = commit.tree[path]
        except KeyError:
            # This happens only when a file has been deleted in a commit,
            # something that was done manually once early in the history.
            continue

        data = csv.DictReader(
            io.StringIO(blob.data_stream.read().decode("utf-8-sig")),
            delimiter=",",
            quotechar='"',
            quoting=csv.QUOTE_ALL,
            skipinitialspace=True,
        )
        for row in data:
            report_number = parse_report_number(row["Report Number"])
            if report_number not in discovered_dates:
                discovered_dates[report_number] = {
                    "report_number": report_number,
                    "file": path.split("/")[-1],
                    "commit": commit.hexsha,
                    "timestamp": dt,
                }
    return discovered_dates


def generate_discovery_file(repo: git.Repo, year: int, month: int) -> None:
    src_path = f"data/fetched/{year}-{month:02d}.csv"
    dest_path = f"data/processed/discovered-dates/{year}-{month:02d}.csv"
    discovered_dates = discover_dates(repo, src_path)
    with open(dest_path, "w") as f:
        writer = csv.DictWriter(
            f, fieldnames=["report_number", "file", "commit", "timestamp"]
        )
        writer.writeheader()
        writer.writerows(discovered_dates.values())


def run_for_months(
    repo: git.Repo,
    start_year: int,
    start_month: int,
    num: int = 3,
    forward: bool = False,
) -> None:
    month_i = 0
    year, month = start_year, start_month
    while month_i < num:
        generate_discovery_file(repo, year, month)
        month_i += 1
        shift_month = next_month if forward else prev_month
        year, month = shift_month(year, month)


def main() -> None:
    args = parse_args(sys.argv[1:])
    repo = git.Repo(os.getcwd())
    run_for_months(repo, args.year, args.month, args.num_months, args.forward)


if __name__ == "__main__":
    main()
