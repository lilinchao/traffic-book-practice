# NYC Motor Vehicle Collisions Data Dictionary

Source: https://data.cityofnewyork.us/Public-Safety/Motor-Vehicle-Collisions-Crashes/h9gi-nx95

Local files:

- `data/raw/nyc_motor_vehicle_collisions_crashes_2023_sample.csv`
- `data/processed/nyc_crash_borough_month_panel_2023.csv`

## Raw Sample Fields

| Field | Meaning |
| --- | --- |
| `crash_date` | Collision date |
| `crash_time` | Collision time |
| `borough` | NYC borough |
| `zip_code` | ZIP code |
| `latitude`, `longitude` | Collision location |
| `on_street_name`, `cross_street_name` | Road context |
| `number_of_persons_injured` | Injured persons count |
| `number_of_persons_killed` | Killed persons count |
| `number_of_pedestrians_injured` | Injured pedestrians count |
| `number_of_pedestrians_killed` | Killed pedestrians count |
| `number_of_cyclist_injured` | Injured cyclists count |
| `number_of_cyclist_killed` | Killed cyclists count |
| `number_of_motorist_injured` | Injured motorists count |
| `number_of_motorist_killed` | Killed motorists count |
| `contributing_factor_vehicle_1` | Primary contributing factor |
| `collision_id` | Unique collision identifier |

## Processed Panel Fields

| Field | Meaning |
| --- | --- |
| `borough` | Panel entity |
| `month` | Monthly period |
| `crashes` | Number of crashes in the borough-month |
| `persons_injured` | Total injured persons |
| `persons_killed` | Total killed persons |
| `pedestrians_injured` | Injured pedestrians |
| `cyclists_injured` | Injured cyclists |
| `motorists_injured` | Injured motorists |
