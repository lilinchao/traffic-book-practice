#!/usr/bin/env bash
set -euo pipefail

mkdir -p data/raw

curl -L --fail \
  --output data/raw/stats19_collision_2023.csv \
  'https://data.dft.gov.uk/road-accidents-safety-data/dft-road-casualty-statistics-collision-2023.csv'

curl -L --fail \
  --output data/raw/stats19_casualty_2023.csv \
  'https://data.dft.gov.uk/road-accidents-safety-data/dft-road-casualty-statistics-casualty-2023.csv'

curl -L --fail -G \
  'https://data.cityofnewyork.us/resource/h9gi-nx95.csv' \
  --data-urlencode '$limit=5000' \
  --data-urlencode '$select=crash_date,crash_time,borough,zip_code,latitude,longitude,on_street_name,cross_street_name,number_of_persons_injured,number_of_persons_killed,number_of_pedestrians_injured,number_of_pedestrians_killed,number_of_cyclist_injured,number_of_cyclist_killed,number_of_motorist_injured,number_of_motorist_killed,contributing_factor_vehicle_1,collision_id' \
  --data-urlencode '$where=crash_date between "2023-01-01T00:00:00" and "2023-12-31T23:59:59"' \
  --data-urlencode '$order=crash_date' \
  --output data/raw/nyc_motor_vehicle_collisions_crashes_2023_sample.csv

mkdir -p data/processed

curl -L --fail -G \
  'https://data.cityofnewyork.us/resource/h9gi-nx95.csv' \
  --data-urlencode '$select=borough,date_extract_m(crash_date) as month,count(*) as crashes,sum(number_of_persons_injured) as persons_injured,sum(number_of_persons_killed) as persons_killed,sum(number_of_pedestrians_injured) as pedestrians_injured,sum(number_of_cyclist_injured) as cyclists_injured,sum(number_of_motorist_injured) as motorists_injured' \
  --data-urlencode '$where=crash_date between "2023-01-01T00:00:00" and "2023-12-31T23:59:59" and borough IS NOT NULL' \
  --data-urlencode '$group=borough,date_extract_m(crash_date)' \
  --data-urlencode '$order=borough,month' \
  --output data/processed/nyc_crash_borough_month_panel_2023.csv

curl -L --fail \
  --output data/raw/nyc_traffic_volume_counts_sample.csv \
  'https://data.cityofnewyork.us/resource/btm5-ppia.csv?$limit=5000'

curl -L --fail \
  --output data/raw/chicago_cta_daily_boarding_sample.csv \
  'https://data.cityofchicago.org/resource/6iiy-9s97.csv?$limit=5000'

curl -L --fail \
  --output data/raw/capital_bikeshare_station_information.json \
  'https://gbfs.lyft.com/gbfs/2.3/dca-cabi/en/station_information.json'

curl -L --fail \
  --output data/raw/capital_bikeshare_station_status.json \
  'https://gbfs.lyft.com/gbfs/2.3/dca-cabi/en/station_status.json'

python3 scripts/build_stats19_tabular_case.py
