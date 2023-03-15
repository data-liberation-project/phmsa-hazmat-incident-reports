import argparse
import logging
import sys
import time
from datetime import datetime, timedelta
from pathlib import Path

# from lib.scraper import fetch
# from retry.api import retry_call

logging.basicConfig()
logger = logging.getLogger(__name__)
logger.setLevel(logging.DEBUG)


def parse_args(args: list[str]) -> argparse.Namespace:
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--year",
        type=int,
        default=datetime.now().year,
        help="The year of the month to start fetching. Defaults to today's year.",
    )
    parser.add_argument(
        "--month",
        type=int,
        default=datetime.now().month,
        help="The month to start fetching. Defaults to today's month.",
    )
    parser.add_argument(
        "--num-months",
        type=int,
        default=3,
        help="The number of months to fetch. Defaults to 3.",
    )
    parser.add_argument(
        "--expand",
        action="store_true",
        help="Fetch the full set of fields (200 columns), rather than the dashboard's default (43 columns)",  # noqa: E501
    )
    parser.add_argument(
        "--forward",
        action="store_true",
        help="Go [num-months] forward, rather than backward.",
    )
    parser.add_argument(
        "--overwrite",
        action="store_true",
        help="If set, overwrites existing files. Defaults to False, which means that previously-fetched months are not refetched.",  # noqa: E501
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


def get_dates_for_month(year: int, month: int) -> tuple[str, str]:
    start_str = f"{year}-{month:02d}-01"
    year_next, month_next = next_month(year, month)
    end_date = datetime(year_next, month_next, 1) - timedelta(days=1)
    end_str = end_date.strftime("%Y-%m-%d")
    return start_str, end_str

def validate_month(year: int, month: int) -> None:
    if year < 1971:
        raise ValueError(f"Reports are only availble from January 1971 to present. You requested data from {year}")
    
    today = datetime.today()
    if year > today.year or (month > today.month and year==today.year):
        raise ValueError(f"Fetching failed at {month}-{year} because your request includes a period in the future. Only data up {today.month}-{today.year} can be fetched.")
    
def download_months(
    start_year: int,
    start_month: int,
    num: int = 3,
    overwrite: bool = False,
    expand: bool = False,
    forward: bool = False,
) -> None:
    month_i = 0
    year, month = start_year, start_month
    while month_i < num:
        month_i += 1
        validate_month(year, month)
        date_from, date_to = get_dates_for_month(year, month)
        dest = Path(f"data/fetched/{date_from[:7]}.csv")

        if overwrite or not dest.exists():
            logger.debug(f"Fetching {date_from} to {date_to} ...")
            file_bytes = retry_call(
                fetch,
                fkwargs=dict(expand=expand, date_from=date_from, date_to=date_to),
                tries=5,
                delay=60,
                backoff=2,
                logger=logger,
            )

            if file_bytes == b"\xef\xbb\xbfThe query resulted in no rows":
                logger.debug("The query resulted in no rows")
            else:
                with open(dest, "wb") as f:
                    f.write(file_bytes)

            if month_i < num:
                time.sleep(10)

        shift_month = next_month if forward else prev_month
        year, month = shift_month(year, month)


def main() -> None:
    args = parse_args(sys.argv[1:])
    download_months(
        args.year,
        args.month,
        expand=args.expand,
        num=args.num_months,
        overwrite=args.overwrite,
        forward=args.forward,
    )


if __name__ == "__main__":
    main()
