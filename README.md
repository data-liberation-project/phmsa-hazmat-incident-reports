# PHMSA "5800.1" Hazmat Transportation Incident Reports

[Federal law](https://www.ecfr.gov/current/title-49/subtitle-B/chapter-I/subchapter-C/part-171/subpart-B/section-171.16) requires transportation-related spills, explosions, and other safety-endangering [incidents involving hazardous materials](https://www.ecfr.gov/current/title-49/subtitle-B/chapter-I/subchapter-C/part-171/subpart-B/section-171.15#p-171.15\(b\)) to be reported to the [Pipeline and Hazardous Materials Safety Administration](https://www.phmsa.dot.gov/) (PHMSA).

Specifically, "each person in physical possession of a hazardous material at the time that any of [certain types of incidents] occurs during transportation (including loading, unloading, and temporary storage) must submit a Hazardous Materials Incident Report on DOT Form F 5800.1 [...] within 30 days of discovery of the incident".

These ["5800.1" forms](https://www.phmsa.dot.gov/sites/phmsa.dot.gov/files/docs/IncidentForm010105.pdf) include details about the location of the incident, mode of transportation, parties involved, hazardous materials involved, causes of failure, fatalities, injuries, financial cost, and more.

PHSMA publishes the submitted reports [through an online portal](https://www.phmsa.dot.gov/hazmat-program-management-data-and-statistics/data-operations/incident-statistics). That portal, however, is brittle and does not provide a straightforward mechanism to download the full set of submitted reports.

This repository, developed by the [Data Liberation Project](https://www.data-liberation-project.org/), aims to do the following:

- Automate the downloading of all data available through the portal
    - Status: 🟢 All data, going back to January 1971, has been fetched, and recent months' data is being [updated on a regular schedule](METHODOLOGY.md)
- Develop documentation to aid in the interpretation of the reports
    - Status: 🔵 In progress
- Generate one file that contains a subset of fields (to keep size within GitHub's limits) for *all* reports
    - Status: 🟠 Not yet started
- Provide RSS feeds with the latest available incidents, nationally and by state
    - Status: 🟢 Completed, now available [here](data/processed/feeds/)
- Provide RSS feeds listing incident [updates](https://www.ecfr.gov/current/title-49/subtitle-B/chapter-I/subchapter-C/part-171/subpart-B/section-171.16#p-171.16\(c\))
    - Status: 🟠 Not yet started
- Standardize/normalize the data
    - Status: 🟠 Not yet started

## Available Data

In the [`data/fetched`](data/fetched/) directory, you can find CSVs containing the report information, with one month of data per CSV. Note that recent months' data may be incomplete (due to yet-unsubmitted reports), and will be regularly updated.

You can clone or [download](https://sites.northwestern.edu/researchcomputing/resources/downloading-from-github/) the repository to get the full set of files. Alternatively, you can access them individually via URL: `https://raw.githubusercontent.com/data-liberation-project/phmsa-hazmat-incident-reports/main/data/fetched/YYYY-MM.csv`, swapping out `YYYY` for the year and `MM` for the two-digit month.

The files are split into months to stay within GitHub's file size limits. You can combine them with your preferred toolset. For example, using [`xsv`](https://github.com/BurntSushi/xsv#installation), you could run `xsv cat rows data/fetched/*.csv > combined.csv`.


### Resources

- [PHMSA's data dictionary for the report data](https://portal.phmsa.dot.gov/HIP_Help/DataDictionary.pdf)
- [PHMSA's *Serious Incident Definition*](https://portal.phmsa.dot.gov/HIP_Help/serious_incident_new_def.pdf)

### Notes

- Some reports are represented by *more than one row*. This happens when the report includes multiple values for a field that the data exports only represent as a single column, such as the name and quantity of the material released. You can identify these multiple-row reports via the `Multiple Rows Per Incident` column.
- Although the vast majority of entries represent hazardous materials incident, some do not. The `Report Type` column provides that detail, and includes values such as "Undeclared Shipment with no Release" and "A specification cargo tank 1,000 gallons or greater containing any hazardous materials that [...]".
- As of the initial publication of this document (Feb. 28, 2023), PHMSA [says on its incident data page](https://www.phmsa.dot.gov/hazmat-program-management-data-and-statistics/data-operations/incident-statistics), "We are experiencing a delay in processing 5800.1 hazardous materials incident reports due to an extraordinary influx in new data submissions. We are working diligently to process 5800.1 reports in a timely manner as they are received."
    - In a March 21, 2023 email responding to a Data Liberation Project inquiry, PHMSA staff clarified the nature of the influx: "Improved incident reporting practices have resulted in an influx of reports – we received 10,000 more filings in 2022 than in prior years. The improved reporting stems from PHMSA’s encouragement of filers to transition from paper reports to using electronic systems, and a lower reporting threshold." When asked when the issue would be resolved, PHMSA staff wrote, "We are diligently working to process these reports and aim to have them complete by summer."
- Reports submitted with "inaccurate or incomplete data" undergo an "Information Resolution process" before the report is ready to release, according to an email from PHMSA staff.

## Methodology

Please see the [METHODOLOGY.md](METHODOLOGY.md) document for a description of how this repository fetches and processes the data.

## Contributors

Many thanks to the volunteers who have contributed to this repository:

- [@gcappaert](https://github.com/gcappaert)
- [@m-nolan](https://github.com/m-nolan)

## Licensing

This repository's code is available under the [MIT License terms](https://opensource.org/license/mit/). The raw data files (those in `data/fetched`) are public domain. All other data files are available under the Creative Commons [CC BY-SA 4.0 license terms](https://creativecommons.org/licenses/by-sa/4.0/).

## Questions?

File an issue in this repository or email Jeremy Singer-Vine at `jsvine@gmail.com`.
