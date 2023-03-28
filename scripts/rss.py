import argparse
import hashlib
import os
import re
import sys

import numpy as np
import pandas as pd

from feedgen.feed import FeedGenerator
from glob import glob


BASE_ID = "data-liberation-project:phma-hazmat-incident-reports"
HASH_SALT = None
RE_PATTERN = r"^(?:<a href = .*?>)?([A-Z]+-[0-9]+)(?:</A>)?$"


def parse_args():
    parser = argparse.ArgumentParser()
    parser.add_argument("data_path")
    return parser.parse_args()


def convert_entry(entry_row):
    hash_payload = f"{entry_row['report_number']}:{HASH_SALT}".encode("utf-8")
    new_id = hashlib.sha1(hash_payload).hexdigest()
    re_link = re.match("^<a href = (.+)>([A-Z]-[0-9]+)</A>$",entry_row["Report Number"])
    if re_link:
        if len(re_link.groups()) < 2:
            breakpoint()
        link = re_link.group(1)
    else:
        link = None
    title = entry_row['report_number']
    return dict(
        id=BASE_ID + ":" + new_id,
        link={"link":{"href":link}},
        title=title,
        published=entry_row['timestamp'],
        content=dict(
            content=f'<a link="{link}">{title}</a>',
            type="html",
        ),
    )

def convert_feed(entry_data):
    #TODO: Fill these values with something that makes sense. Not sure what "updated" is without an actual parent feed.
    feed_attrs = {
        "title": None,
        "id": BASE_ID,
        "subtitle": (None, None),
        "author": {"name": None},
        "language": "en",
        "link": {
            "href": (
                "https://github.com/data-liberation-project/",
                "phma-hazmat-incident-reports",
            )
        },
        "updated": None, #?
    }

    fg = FeedGenerator()
    for k, v in feed_attrs.items():
        getattr(fg, k)(v)

    for _, row in entry_data.iterrows():
        if isinstance(row['Report Number'],str):
            e = convert_entry(row)
            new_entry = fg.add_entry()
            for k, v in e.items():
                method = getattr(new_entry, k)
                if isinstance(v, dict):
                    method(**v)
                else:
                    method(v)

    return fg


def fetch_entry_data(data_path):
    #TODO: structure this differently to filter by date
    discovered_date_files = glob(os.path.join(data_path,r'processed/discovered-dates/*.csv'))
    fetched_data_files = [os.path.join(data_path,'fetched',os.path.basename(ddf)) for ddf in discovered_date_files]
    discovered_dates = pd.DataFrame()
    for ddf in discovered_date_files:
        discovered_dates = pd.concat(
            [
                discovered_dates,
                pd.read_csv(ddf)
            ],
            ignore_index=True
        )
    discovered_dates = discovered_dates.sort_values('timestamp')
    entry_data = pd.DataFrame()
    for fdf in fetched_data_files:
        entry_data = pd.concat(
            [
                entry_data,
                pd.read_csv(fdf)
            ]
        )
    entry_data['report_number'] = [re.match(RE_PATTERN,rn).group(1) for rn in entry_data['Report Number']]
    entry_data = pd.merge(entry_data, discovered_dates, how='outer', on='report_number')
    return entry_data


def main():
    args = parse_args()
    entry_data = fetch_entry_data(args.data_path)
    converted = convert_feed(entry_data)
    converted.rss_file(sys.stdout.buffer, pretty=True)


if __name__ == "__main__":
    main()
