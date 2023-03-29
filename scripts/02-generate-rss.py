import argparse
import html
import re
import sys
import typing
from datetime import datetime, timedelta, timezone
from pathlib import Path

import pandas as pd
from feedgen.feed import FeedGenerator

BASE_ID = "data-liberation-project:phma-hazmat-incident-reports"
RE_PATTERN = r"^(?:<a href = .*?>)?([A-Z]+-[0-9]+)(?:</A>)?$"
NOW = datetime.now(tz=timezone.utc)


def parse_args(args: list[str]) -> argparse.Namespace:
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--num-months",
        type=int,
        default=12,
        help="The number of months (by incident date) to consider for inclusion. Defaults to 12.",  # noqa: E501
    )
    parser.add_argument(
        "--discovered-days",
        type=int,
        default=7,
        help="In RSS feeds, show only reports *discovered* in past X days. Defaults to 7.",  # noqa: E501
    )
    return parser.parse_args(args)


def convert_entry(row: dict[str, typing.Any]) -> dict[str, typing.Any]:
    report_number = row["report_number"]
    report_link_match = re.search("href = (.+)>", row["Report Number"])

    link = report_link_match.group(1) if report_link_match else None

    return dict(
        id=BASE_ID + ":" + report_number,
        link={"link": {"href": link}},
        title=f"Report {report_number}",
        published=row["timestamp"],
        content=dict(
            content=f"""
            <h3><a link="{link}">Report {report_number}</a></h3>
            <h4>Identified by scraper @ {row["timestamp"]}</h4>
            <ul>
                <li>Incident Date: {row["Date Of Incident"]}</li>
                <li>City: {row["Incident City"]}</li>
                <li>State: {row["Incident State"]}</li>
                <li>Report Type: {row["Report Type"]}</li>
                <li>Mode Of Transportation: {row["Mode Of Transportation"]}</li>
                <li>Carrier/Reporter: {row["Carrier Reporter Name"]}</li>
                <li>Hazmat Fatalities: {row["Total Hazmat Fatalities"]}</li>
                <li>Hazmat Injuries: {row["Total Hazmat Injuries"]}</li>
                <li>Non-Hazmat Fatalities: {row["Non Hazmat Fatalities"]}</li>
                <li>Description: {html.escape(row["Description Of Events"])}</li>
            </ul>
            """,
            type="html",
        ),
    )


def convert_feed(rows: pd.DataFrame) -> FeedGenerator:
    feed_attrs = {
        "title": "Latest PHMSA Hazardous Materials Incident Reports",
        "id": BASE_ID,
        "subtitle": "The latest Form 5800.1 hazardous material reports submitted to the Department of Transportation and posted online by the Pipeline and Hazardous Materials Safety Administration.",  # noqa: E501
        "author": {"name": "Data Liberation Project"},
        "language": "en",
        "link": {
            "href": "https://github.com/data-liberation-project/phma-hazmat-incident-reports",  # noqa: E501
        },
        "updated": NOW.isoformat(),
    }

    fg = FeedGenerator()
    for k, v in feed_attrs.items():
        getattr(fg, k)(v)

    for _, row in rows.iterrows():
        e = convert_entry(row)
        new_entry = fg.add_entry()
        for k, v in e.items():
            method = getattr(new_entry, k)
            if isinstance(v, dict):
                method(**v)
            else:
                method(v)

    return fg


def fetch_entry_data(num_months: int, discovered_days: int) -> pd.DataFrame:
    hist_paths = Path("data/processed/discovered-dates").glob("*.csv")
    hist_paths_limited = sorted(hist_paths)[-num_months:]
    data_paths = Path("data/fetched").glob("*.csv")
    data_paths_limited = sorted(data_paths)[-num_months:]

    history = pd.concat(map(pd.read_csv, hist_paths_limited))
    data = (
        pd.concat(map(pd.read_csv, data_paths_limited))
        .drop_duplicates(subset=["Report Number"])
        .assign(
            report_number=lambda df: df["Report Number"].str.extract(
                RE_PATTERN, expand=False
            )
        )
    )

    rows = history.loc[
        lambda df: pd.to_datetime(df["timestamp"])
        > (NOW - timedelta(days=discovered_days))
    ].merge(data, on=["report_number"], validate="1:1")

    return rows


def main() -> None:
    args = parse_args(sys.argv[1:])
    entry_data = fetch_entry_data(
        num_months=args.num_months, discovered_days=args.discovered_days
    )
    converted = convert_feed(entry_data)
    converted.rss_file(sys.stdout.buffer, pretty=True)


if __name__ == "__main__":
    main()
