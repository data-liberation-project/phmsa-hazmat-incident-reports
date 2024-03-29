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
RE_PATTERN = re.compile(r"^(?:<a href = .*?>)?([A-Z]+-[0-9]+)(?:</A>)?$", re.I)
NOW = datetime.now(tz=timezone.utc)
STATE_ABBRS = [
    "AL",
    "AK",
    "AS",
    "AZ",
    "AR",
    "CA",
    "CO",
    "CT",
    "DE",
    "DC",
    "FL",
    "GA",
    "GU",
    "HI",
    "ID",
    "IL",
    "IN",
    "IA",
    "KS",
    "KY",
    "LA",
    "ME",
    "MD",
    "MA",
    "MI",
    "MN",
    "MS",
    "MO",
    "MT",
    "NE",
    "NV",
    "NH",
    "NJ",
    "NM",
    "NY",
    "NC",
    "ND",
    "OH",
    "OK",
    "OR",
    "PA",
    "PR",
    "RI",
    "SC",
    "SD",
    "TN",
    "TX",
    "UT",
    "VT",
    "VA",
    "VI",
    "WA",
    "WV",
    "WI",
    "WY",
]


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
                <li>Total Amount Of Damages: {row["Total Amount Of Damages"]}</li>
                <li>Serious Incident Ind: {row["Serious Incident Ind"]}</li>
                <li>Description: {html.escape(row["Description Of Events"])}</li>
            </ul>
            """,
            type="html",
        ),
    )


def convert_to_feed(rows: pd.DataFrame, state: typing.Optional[str]) -> FeedGenerator:
    title_suffix = "" if state is None else f", for {state}"
    subtitle_suffix = "." if state is None else f", for {state}"
    feed_attrs = {
        "title": f"Latest PHMSA Hazardous Materials Incident Reports{title_suffix}",
        "id": BASE_ID + "" if state is None else f":{state.lower()}",
        "subtitle": f"The latest Form 5800.1 hazardous material reports submitted to the Department of Transportation and posted online by the Pipeline and Hazardous Materials Safety Administration{subtitle_suffix}",  # noqa: E501
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

    for _, row in rows.fillna("").iterrows():
        entry = fg.add_entry()
        e = convert_entry(row)
        for k, v in e.items():
            method = getattr(entry, k)
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

    history = (
        pd.concat(map(pd.read_csv, hist_paths_limited))
        # Necessary for edge-case when report shifts
        # from one month's file to another
        .drop_duplicates(subset=["report_number"])
    )

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

    main_feed = convert_to_feed(entry_data, state=None)
    with open("data/processed/feeds/recent-reports.rss", "wb") as f:
        main_feed.rss_file(f, pretty=True)

    for state in STATE_ABBRS:
        state_entry_data = entry_data.loc[lambda df: df["Incident State"] == state]

        state_feed = convert_to_feed(state_entry_data, state=state)
        with open(
            f"data/processed/feeds/by-state/recent-reports-{state.lower()}.rss", "wb"
        ) as f:
            state_feed.rss_file(f, pretty=True)


if __name__ == "__main__":
    main()
