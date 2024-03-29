import pathlib

import pandas as pd


def filter_rows(df: pd.DataFrame, cost_min: int = 0) -> pd.DataFrame:
    return df.loc[
        (df["Total Amount Of Damages"] >= cost_min)
        & (
            (df["Serious Incident Ind"] == "Yes")
            | (df["Hmis Serious Bulk Release"] == "Yes")
            | (df["Hmis Serious Evacuations"] == "Yes")
            | (df["Hmis Serious Fatality"] == "Yes")
            | (df["Hmis Serious Flight Plan"] == "Yes")
            | (df["Hmis Serious Injury"] == "Yes")
            | (df["Hmis Serious Major Artery"] == "Yes")
            | (df["Hmis Serious Marine Pollutant"] == "Yes")
            | (df["Hmis Serious Radioactive"] == "Yes")
        )
    ]


def read_csv(path: pathlib.Path) -> pd.DataFrame:
    return pd.read_csv(path, dtype=str).astype({"Total Amount Of Damages": int})


def main() -> None:
    # Collect all of the CSVs in the fetched folder
    paths = sorted(pathlib.Path("data/fetched").glob("*.csv"))

    # Concatenate all of the CSV files
    all_rows = pd.concat(map(read_csv, paths), ignore_index=True)

    # Filter to "serious" incidents
    filtered_rows = filter_rows(all_rows)
    filtered_rows.to_csv("data/processed/filtered/serious-incidents.csv", index=False)

    # Filter the serious incidents to just those with $10k+ in total costs
    filtered_rows_expensive = filter_rows(filtered_rows, cost_min=10000)
    filtered_rows_expensive.to_csv(
        "data/processed/filtered/serious-incidents-expensive.csv", index=False
    )


if __name__ == "__main__":
    main()
