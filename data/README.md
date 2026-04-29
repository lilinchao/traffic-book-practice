# Case Data

This directory contains small case datasets for the traffic analysis chapters.

The files in `raw/` are downloaded from public data sources and are intended for teaching, examples, and reproducible practice. Before redistributing a published release, review each source's license and citation requirements.

## Files

| File | Chapter | Source | Suggested Use |
| --- | --- | --- | --- |
| `raw/stats19_collision_2023.csv` | Chapter 4 | UK DfT STATS19 | Traffic collision tabular data, severity modeling |
| `raw/stats19_casualty_2023.csv` | Chapter 4 | UK DfT STATS19 | Casualty-level table for derived vulnerable road-user outcomes |
| `processed/stats19_collision_casualty_tabular_2023_sample.csv` | Chapter 4 | Derived from STATS19 | Tabular causal-oriented modeling, logistic/count/zero-inflated examples |
| `results/chapter-04/*.csv` | Chapter 4 | Derived from STATS19 model outputs | Model coefficients, model comparison, scenario predictions |
| `raw/nyc_motor_vehicle_collisions_crashes_2023_sample.csv` | Chapter 4 | NYC Open Data Motor Vehicle Collisions Crashes | Traffic accident records, panel construction, injury and crash factor analysis |
| `processed/nyc_crash_borough_month_panel_2023.csv` | Chapter 4 | NYC Open Data grouped API result | Borough-month panel data, grouped statistics, fixed-effect style exercises |
| `raw/nyc_traffic_volume_counts_sample.csv` | Chapter 4 / 6 | NYC Open Data Traffic Volume Counts | Traffic volume panel data, hourly profile analysis, road segment comparison |
| `raw/chicago_cta_daily_boarding_sample.csv` | Chapter 6 | Chicago Data Portal CTA Ridership | Daily public transit time series, trend and seasonality analysis |
| `raw/capital_bikeshare_station_information.json` | Chapter 5 | Capital Bikeshare GBFS | Station location mapping, capacity analysis, spatial joins |
| `raw/capital_bikeshare_station_status.json` | Chapter 5 | Capital Bikeshare GBFS | Station status analysis, availability snapshots |

## Reproduce Downloads

Run:

```bash
bash scripts/download_case_data.sh
```

## Source Links

- NYC Traffic Volume Counts: https://data.cityofnewyork.us/Transportation/Traffic-Volume-Counts/btm5-ppia
- NYC Motor Vehicle Collisions Crashes: https://data.cityofnewyork.us/Public-Safety/Motor-Vehicle-Collisions-Crashes/h9gi-nx95
- UK DfT STATS19 Road Safety Data: https://data.dft.gov.uk/road-accidents-safety-data/
- National Household Travel Survey: https://nhts.ornl.gov/
- Chicago CTA Daily Boarding Totals: https://data.cityofchicago.org/Transportation/CTA-Ridership-Daily-Boarding-Totals/6iiy-9s97
- Capital Bikeshare GBFS: https://capitalbikeshare.com/system-data
