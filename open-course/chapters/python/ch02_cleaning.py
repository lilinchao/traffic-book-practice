"""Organize original weather/traffic records into unique local-hour observations."""
import argparse, collections, csv, datetime as dt, json
from pathlib import Path

DATA=Path(__file__).resolve().parents[1]/'data/ch02_raw.csv'

def clean(path):
    groups=collections.defaultdict(list)
    with Path(path).open(encoding='utf-8-sig',newline='') as f:
        rows=list(csv.DictReader(f))
    for row in rows:
        time=dt.datetime.strptime(row['date_time'],'%Y-%m-%d %H:%M:%S').isoformat(timespec='minutes')
        groups[time].append(int(row['traffic_volume']))
    conflicts=[key for key,values in groups.items() if len(set(values))!=1]
    if conflicts:raise ValueError(f'{len(conflicts)} hours have conflicting volumes; review before merging')
    cleaned=[(key,values[0]) for key,values in sorted(groups.items())]
    return cleaned,{'raw_rows':len(rows),'unique_hours':len(cleaned),'duplicate_rows':len(rows)-len(cleaned),'conflicting_hours':len(conflicts)}

def main():
    p=argparse.ArgumentParser();p.add_argument('--data',type=Path,default=DATA);p.add_argument('--output',type=Path,default=Path('ch02_cleaned.csv'));a=p.parse_args()
    rows,report=clean(a.data)
    with a.output.open('w',encoding='utf-8',newline='') as f:
        w=csv.writer(f);w.writerow(['local_time','volume']);w.writerows(rows)
    a.output.with_suffix('.json').write_text(json.dumps(report,indent=2),encoding='utf-8')
    print(report)

if __name__=='__main__':main()
