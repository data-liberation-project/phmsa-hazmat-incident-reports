# Filtered Subsets

This directory contains filtered subsets of the full incident dataset.

## `serious-incidents.csv`

This dataset contains all rows for which *any* of the following fields' values is `Yes`:

- `Serious Incident Ind`
- `Hmis Serious Bulk Release`
- `Hmis Serious Evacuations`
- `Hmis Serious Fatality`
- `Hmis Serious Flight Plan`
- `Hmis Serious Injury`
- `Hmis Serious Major Artery`
- `Hmis Serious Marine Pollutant`
- `Hmis Serious Radioactive`

The Data Liberation Project thanks volunteer Madeline Everett for developing this filter, as well the filter described below.

## `serious-incidents-expensive.csv`

This dataset begins with the same filter as above, but adds an additional constraint: The total cost of the incident (`Total Amount Of Damages`) is $10,000 or more.
