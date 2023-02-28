# Methodology

## Getting data from the PHSMA query tool

### Overview

Broadly speaking, the data-fetching code in this repository aims to automate the following processes:

1. Open the [Hazmat Incident Report Search Tool](https://portal.phmsa.dot.gov/PDMPublicReport/?url=https://portal.phmsa.dot.gov/analytics/saw.dll?Portalpages&PortalPath=%2Fshared%2FPublic%20Website%20Pages%2F_portal%2FHazmat%20Incident%20Report%20Search) that is [linked from this page](https://www.phmsa.dot.gov/hazmat-program-management-data-and-statistics/data-operations/incident-statistics).
2. Use the form in that tool to submit a query, specifying `3. Date of Incident: From: Between ________ - ________` with the dates being the first and last day of a given month.
3. Request the tool to expand the set of columns provided, as if one clicked the `Incident Detailed Report: All fields included in Form 5800.1` link.
4. Initiate a download of those expanded results, as if one clicked the `Click here to download the below report` link.

Instead of interacting directly with the site through a browser, the code sends HTTP calls that parallel that workflow.

### Code representation

The core code can be found in the [`scripts/lib/scraper.py`](scripts/lib/scraper.py) file. Within that module, the main chunk of code is the `Session` class, which represents an interaction with the query tool. The module also contains a `fetch(...)` convenience method, which goes through the steps described above:

```python
def fetch(expand: bool = False, **params: str) -> bytes:
    """
    `params` here is a dictionary in the form of:
        {
            "date_from": "YYYY-MM-DD",
            "date_to": "YYYY-MM-DD"
        }

        ... but which could, theoretically, be expanded
        in the future to handle other parameters permitted
        in the query tool.
    """
    # Step 1
    session = Session()
    session.initialize()

    # Step 2
    view_state, download_params = session.query(**params)

    # Step 3
    if expand:
        view_state, download_params = session.expand_results(view_state)

    # Step 4
    file_bytes = session.download(download_params)
    return file_bytes
```

That convenience method is then used by other scripts, such as [`scripts/utils/cli.py`](scripts/utils/cli.py) and [`scripts/00-fetch.py`](scripts/00-fetch.py), which implement higher-level routines.

## Saving the data to this repository

The [`scripts/00-fetch.py`](scripts/00-fetch.py) Python script provides a command-line interface for fetching and refreshing historical data. Its help-string provides a sense of how it works:


```
usage: 00-fetch.py [-h] [--year YEAR] [--month MONTH]
                   [--num-months NUM_MONTHS] [--expand] [--forward]
                   [--overwrite]

options:
  -h, --help            show this help message and exit
  --year YEAR           The year of the month to start fetching. Defaults to
                        today's year.
  --month MONTH         The month to start fetching. Defaults to today's
                        month.
  --num-months NUM_MONTHS
                        The number of months to fetch. Defaults to 3.
  --expand              Fetch the full set of fields (200 columns), rather
                        than the dashboard's default (43 columns)
  --forward             Go [num-months] forward, rather than backward.
  --overwrite           If set, overwrites existing files. Defaults to False,
                        which means that previously-fetched months are not
                        refetched.
```

## Automation

The [`.github/workflows/scrape.yml`](.github/workflows/scrape.yml) file defines a [GitHub Action](https://docs.github.com/en/actions) that does the following:

- Every three hours, refreshes the *past three months* of data, using the following call `python scripts/00-fetch.py --overwrite --expand --num-months 3`. Once a day, refreshes the *past year* of data, using the following call `python scripts/00-fetch.py --overwrite --expand --num-months 12`. 

- Commits the new and updated files to `git`, and pushes that commit back to this repository.
