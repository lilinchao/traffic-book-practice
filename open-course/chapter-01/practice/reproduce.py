"""Reproduce the two real-data summaries. Python 3.10+, pandas and pyarrow.

Install: python -m pip install pandas pyarrow
Run:     python reproduce.py --output ./results
Data downloads require network. Classroom interactions do not.
"""
import argparse
import csv
import gzip
import hashlib
import io
import json
import zipfile
from collections import defaultdict
from datetime import datetime
from pathlib import Path
from urllib.request import Request, urlopen


def download(url, destination):
    if not destination.exists():
        with urlopen(Request(url, headers={'User-Agent': 'TrafficBookTeaching/1.0'}), timeout=90) as r:
            destination.write_bytes(r.read())
    return destination


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--output', type=Path, default=Path('results'))
    out = parser.parse_args().output
    out.mkdir(parents=True, exist_ok=True)
    metro_url = 'https://archive.ics.uci.edu/static/public/492/metro+interstate+traffic+volume.zip'
    p = download(metro_url, out / 'metro.zip')
    with zipfile.ZipFile(p) as z:
        name = next(n for n in z.namelist() if n.endswith('.csv.gz'))
        raw = list(csv.DictReader(io.StringIO(gzip.decompress(z.read(name)).decode())))
    grouped = defaultdict(list)
    for row in raw:
        grouped[row['date_time']].append(row)
    records = []
    for time, rows in sorted(grouped.items()):
        values = {int(r['traffic_volume']) for r in rows}
        if len(values) != 1:
            raise ValueError('Conflicting traffic volume at ' + time)
        dt = datetime.fromisoformat(time)
        records.append({'time': time, 'year': dt.year, 'weekday': dt.weekday(),
                        'hour': dt.hour, 'volume': values.pop(),
                        'weather': ';'.join(sorted({r['weather_main'] for r in rows}))})
    train = [r for r in records if r['year'] == 2017]
    test = [r for r in records if r['year'] == 2018]
    global_mean = sum(r['volume'] for r in train) / len(train)
    groups = defaultdict(list)
    for r in train:
        groups[(r['weekday'], r['hour'])].append(r['volume'])
    means = {k: sum(v) / len(v) for k, v in groups.items()}
    errors = [(abs(r['volume'] - global_mean),
               abs(r['volume'] - means.get((r['weekday'], r['hour']), global_mean))) for r in test]
    with (out / 'metro-2018-reproduced.csv').open('w', encoding='utf-8-sig', newline='') as f:
        writer = csv.DictWriter(f, fieldnames=list(test[0]))
        writer.writeheader()
        writer.writerows(test)
    summary = {'metro': {'url': metro_url, 'sha256': hashlib.sha256(p.read_bytes()).hexdigest(),
                        'raw_rows': len(raw), 'unique_local_hours': len(records),
                        'train_hours': len(train), 'test_hours': len(test),
                        'global_MAE': sum(e[0] for e in errors) / len(errors),
                        'weekday_hour_MAE': sum(e[1] for e in errors) / len(errors)}}

    import pandas as pd
    taxi_url = 'https://d37ci6vzurychx.cloudfront.net/trip-data/green_tripdata_2024-01.parquet'
    tp = download(taxi_url, out / 'green_tripdata_2024-01.parquet')
    df = pd.read_parquet(tp)
    before = len(df)
    dt = pd.to_datetime(df.lpep_pickup_datetime)
    df = df[(dt >= '2024-01-01') & (dt < '2024-02-01')].copy()
    df['hour'] = df.lpep_pickup_datetime.dt.hour
    df['daytype'] = df.lpep_pickup_datetime.dt.dayofweek.map(lambda x: '平日' if x < 5 else '周末')
    zp = download('https://d37ci6vzurychx.cloudfront.net/misc/taxi_zone_lookup.csv', out / 'taxi_zone_lookup.csv')
    zones = pd.read_csv(zp)
    df = df.merge(zones[['LocationID', 'Borough']], how='left', left_on='PULocationID', right_on='LocationID')
    df['Borough'] = df.Borough.fillna('Unknown')
    df.groupby(['Borough', 'daytype', 'hour']).size().reset_index(name='count').to_csv(
        out / 'taxi-2024-01-aggregated.csv', index=False, encoding='utf-8-sig')
    summary['taxi'] = {'url': taxi_url, 'sha256': hashlib.sha256(tp.read_bytes()).hexdigest(),
                       'raw_rows': before, 'retained_rows': len(df), 'excluded_time_rows': before - len(df)}
    (out / 'summary.json').write_text(json.dumps(summary, indent=2), encoding='utf-8')
    print(json.dumps(summary, indent=2))
    # Record hashes make changes in upstream files visible instead of silently changing classroom results.
    assert summary['metro']['raw_rows'] == 48204
    assert summary['metro']['unique_local_hours'] == 40575
    assert summary['metro']['test_hours'] == 6533
    assert round(summary['metro']['global_MAE'], 1) == 1723.8
    assert round(summary['metro']['weekday_hour_MAE'], 1) == 259.2
    assert summary['taxi']['retained_rows'] == 56549


if __name__ == '__main__':
    main()
