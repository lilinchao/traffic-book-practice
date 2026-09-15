"""Build public self-check targets directly from the fixed source snapshots."""
import csv
import hashlib
import json
import math
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
DEST = ROOT/'chapters/data/primary'
PROTOCOLS = json.loads((ROOT/'chapters/data/project-protocols.json').read_text(encoding='utf-8'))


def read(path):
    return json.loads((ROOT/path).read_text(encoding='utf-8'))


def write(chapter, paths, **data):
    key = f'ch{chapter:02}'
    result = dict(protocol=PROTOCOLS[key]['id'], inputs={p: hashlib.sha256((ROOT/p).read_bytes()).hexdigest() for p in paths}, **data)
    DEST.mkdir(exist_ok=True)
    (DEST/f'{key}.json').write_text(json.dumps(result, ensure_ascii=False, allow_nan=False, separators=(',', ':')), encoding='utf-8')


with (ROOT/'chapters/data/ch04_solution.csv').open(encoding='utf-8-sig') as f:
    truth = [[r['id'], float(r['cnt'])] for r in csv.DictReader(f)]
write(4, [f'chapters/data/ch04_{p}.csv' for p in ['train', 'validation', 'test', 'solution']], truth=truth, models=['OLS','Poisson','NB2'])
points = [r for r in read('projects/data/crashes.json')['rows'] if r[7]]
cells = sorted({(math.floor((r[4]+74.3)*111320*math.cos(math.radians(40.73))/500), math.floor((r[3]-40.45)*111320/500)) for r in points})
write(5, ['projects/data/crashes.json'], grid_ids=[f'{x}:{y}' for x,y in cells], point_ids=[r[0] for r in points])
horizons = read('projects/data/forecast.json')['horizons']
common = sorted(set.intersection(*[set(r[0] for r in horizons[str(h)]['rows']) for h in [1,3,6]]))
actual = {r[0]: r[1] for r in horizons['1']['rows']}
write(6, ['projects/data/audit.json','projects/data/forecast.json'], truth=[[t,actual[t]] for t in common], models=[f'{name}|h={h}' for h in [1,3,6] for name in ['ARIMA','SARIMA','Week','Calendar']])
nodes = ['Manhattan','Brooklyn','Queens','Bronx']
taxi = {(d,b,h): n for d,b,h,n in read('projects/data/taxi.json')['rows']}
truth = [[f'2024-01-{d:02}T{h:02}:00|{b}',taxi.get((f'2024-01-{d:02}',b,h),0)] for d in range(25,32) for h in range(24) for b in nodes]
write(7, ['projects/data/taxi.json'], truth=truth, models=['AR','VAR','Calendar'], optional_models=['Last'])
write(8, ['projects/data/sind.json'], points=[[str(r[0]),r[1]/1000,r[2],r[3]] for r in read('projects/data/sind.json')['rows']])
print('Built primary references: 4376 regression / 2169 forecast / 672 region-hours; spatial and tracking inventories')
