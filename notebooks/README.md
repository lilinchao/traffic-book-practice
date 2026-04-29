# Notebooks

This directory contains executable chapter notebooks.

## Setup

From the repository root:

```bash
pip install -r requirements.txt
```

## Chapter 4

Traffic accident panel analysis:

```bash
jupyter notebook notebooks/chapter-04/traffic_accident_panel_analysis.ipynb
```

Execute the whole notebook and write outputs back:

```bash
bash scripts/execute_chapter04_notebook.sh
```

The notebook uses:

- `data/raw/nyc_motor_vehicle_collisions_crashes_2023_sample.csv`
- `data/processed/nyc_crash_borough_month_panel_2023.csv`

## Data Refresh

To refresh the downloaded case data:

```bash
bash scripts/download_case_data.sh
```
