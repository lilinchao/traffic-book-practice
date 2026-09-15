"""Reproduce the Chapter 2 audit. Run from any working directory."""
from pathlib import Path
import hashlib
import json
import platform
import numpy as np
import pandas as pd

ROOT = Path(__file__).resolve().parent
SOURCE = ROOT / 'data/ch02_raw.csv'
OUT = ROOT / 'outputs'
OUT.mkdir(exist_ok=True)
raw = pd.read_csv(SOURCE, keep_default_na=False)
raw['time'] = pd.to_datetime(raw['date_time'])
conflicts = raw.groupby('time')['traffic_volume'].nunique()
assert not (conflicts > 1).any(), 'Conflicting volume in the same local-hour label'
hourly = raw.drop_duplicates('time').sort_values('time').copy()
assert len(raw) == 48204 and len(hourly) == 40575
audit = []
for year, part in hourly.groupby(hourly['time'].dt.year):
    skeleton = pd.date_range(part['time'].min(), part['time'].max(), freq='h')
    original = raw[raw['time'].dt.year.eq(year)]
    audit.append(dict(year=int(year), raw=len(original), unique=len(part),
                      extra=len(original)-len(part), conflicts=0,
                      missing=len(skeleton.difference(part['time'])),
                      zeros=int(part['traffic_volume'].eq(0).sum()), expected=len(skeleton)))
pd.DataFrame(audit).to_csv(OUT / 'quality-audit.csv', index=False)
weather = raw.groupby('time')['weather_main'].agg(lambda v: json.dumps(sorted(set(v))))
clean = hourly[['time', 'traffic_volume']].set_index('time').join(weather.rename('weather_labels'))
clean.to_csv(OUT / 'hourly.csv')
part = hourly[hourly['time'].dt.year.eq(2017) & hourly['time'].dt.hour.isin([7, 8, 9])]
peak = part.groupby(part['time'].dt.date)['traffic_volume'].agg(['count', 'mean', 'sum'])
peak = peak[peak['count'].eq(3)]
assert len(peak) == 358
peak.to_csv(OUT / 'ch03-peak-days.csv')
temp_c = raw['temp'].to_numpy(dtype=float) - 273.15
metadata = dict(protocol='ch02-audit-v1', sourceSHA256=hashlib.sha256(SOURCE.read_bytes()).hexdigest(),
                python=platform.python_version(), numpy=np.__version__, pandas=pd.__version__,
                rawRows=len(raw), uniqueHours=len(hourly), peakDays=len(peak),
                temperatureFlaggedRows=int(((temp_c < -60) | (temp_c > 60)).sum()),
                scope='Original local labels, no DST reconstruction; missing values NOT replaced with zero.')
(OUT / 'run-metadata.json').write_text(json.dumps(metadata, indent=2), encoding='utf-8')
print(pd.DataFrame(audit).to_string(index=False))
print(json.dumps(metadata, indent=2))
print('Outputs:', OUT)
