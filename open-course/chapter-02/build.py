"""Build the offline classroom from the course's pinned, real observations."""
import csv
import hashlib
import io
import json
from pathlib import Path
import tarfile
import urllib.request

HERE = Path(__file__).resolve().parent
COURSE = HERE.parent


def source(path):
    data = (COURSE / path).read_bytes()
    hashes[path] = hashlib.sha256(data).hexdigest()
    return data


hashes = {}
text = source('chapters/data/ch02_raw.csv').decode('utf-8-sig')
reader = csv.reader(io.StringIO(text))
columns = next(reader)
rows = [[int(v) if i == 8 else float(v) if i in (1, 2, 3, 4) else v
         for i, v in enumerate(row)] for row in reader]
groups = {}
for row in rows:
    groups.setdefault(row[7], set()).add(row[8])
assert len(rows) == 48204 and len(groups) == 40575, 'Source snapshot changed; review classroom scope'
assert all(len(values) == 1 for values in groups.values()), 'Conflicting hourly volume; stop build'
crashes = list(csv.DictReader(io.StringIO(source('projects/data/nyc-crashes-2024-01.csv').decode())))
points = [[r['id'], float(r['longitude']), float(r['latitude']), r['borough']]
          for r in crashes if r['valid_coordinates'] == 'True']
tracks = list(csv.DictReader(io.StringIO(source('projects/data/sind-tianjin-120s.csv').decode())))
ids = sorted({r['track_id'] for r in tracks}, key=lambda t: int(t))[:3]
tracks = [[r['track_id'], float(r['timestamp_ms']) / 1000, float(r['x']), float(r['y']), r['agent_type']]
          for r in tracks if r['track_id'] in ids]
protocols = json.loads(source('chapters/data/project-protocols.json'))
data = dict(columns=columns, rows=rows, crashes=points, crashTotal=len(crashes), tracks=tracks,
            protocols=protocols, hashes=hashes, protocol='ch02-audit-v1', version='2026-09-15')
(HERE / 'data').mkdir(exist_ok=True)
(HERE / 'data/observations.js').write_text('window.OBSERVATIONS=' + json.dumps(data, ensure_ascii=False, separators=(',', ':')) + ';\n', encoding='utf-8')
(HERE / 'data/ch02_raw.csv').write_bytes((COURSE / 'chapters/data/ch02_raw.csv').read_bytes())
(HERE / 'data/SIND-LICENSE.txt').write_bytes((COURSE / 'projects/data/SIND-LICENSE.txt').read_bytes())
(HERE / 'data/manifest.json').write_text(json.dumps(dict(inputs=hashes, rows=len(rows), uniqueHours=len({r[7] for r in rows}), crashPoints=len(points), trajectoryIDs=ids), indent=2), encoding='utf-8')

# Vendor a pinned, single-file SQLite engine so SQL also works under file://.
vendor = HERE / 'vendor'
vendor.mkdir(exist_ok=True)
version = '1.14.2'
archive_url = f'https://registry.npmjs.org/sql.js/-/sql.js-{version}.tgz'
if not (vendor / 'sqlite.js').exists():
    archive = urllib.request.urlopen(archive_url, timeout=90).read()
    with tarfile.open(fileobj=io.BytesIO(archive), mode='r:gz') as tar:
        engine = tar.extractfile('package/dist/sql-asm-memory-growth.js').read()
        license_text = tar.extractfile('package/LICENSE').read()
    (vendor / 'sqlite.js').write_text('window.SQL_ENGINE_SOURCE=' + json.dumps(engine.decode()) + ';\n', encoding='utf-8')
    (vendor / 'SQLJS-LICENSE.txt').write_bytes(license_text)
    (vendor / 'manifest.json').write_text(json.dumps(dict(version=version, url=archive_url,
        archiveSHA256=hashlib.sha256(archive).hexdigest(), engineSHA256=hashlib.sha256(engine).hexdigest(),
        license='MIT', source='https://github.com/sql-js/sql.js'), indent=2), encoding='utf-8')
print(f'Built {len(rows)} original records, {len(points)} crash points and {len(tracks)} trajectory points.')
