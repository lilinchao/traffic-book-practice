"""Daily-block bootstrap for an observed traffic monitoring sample."""
from pathlib import Path
import argparse, csv, json, math

DATA = Path(__file__).resolve().parents[1] / 'data' / 'ch03_daily.csv'

def analyze(rows, n=60, repetitions=500, seed=42, group='all'):
    pool = [r for r in rows if group == 'all' or r['day_type'] == group]
    if not pool or not 2 <= n <= len(pool) or not 50 <= repetitions <= 2000:
        raise ValueError('Invalid sample size or repetition count')
    if not 0 <= seed <= 4294967295:
        raise ValueError('Seed outside uint32 range')
    state = seed
    def random():
        nonlocal state
        state = (1664525 * state + 1013904223) & 0xffffffff
        return state / 4294967296
    sample = pool[:]
    for i in range(len(sample) - 1, 0, -1):
        j = int(random() * (i + 1))
        sample[i], sample[j] = sample[j], sample[i]
    values = [float(r['peak_mean']) for r in sample[:n]]
    means = sorted(sum(values[int(random() * n)] for _ in range(n)) / n for _ in range(repetitions))
    def quantile(q):
        x = (len(means) - 1) * q
        a = int(x)
        return means[a] + (means[min(a + 1, len(means) - 1)] - means[a]) * (x - a)
    return {'n_days': n, 'available_days': len(pool), 'estimate': sum(values) / n,
            'lower': quantile(.025), 'upper': quantile(.975),
            'observed_reference': sum(float(r['peak_mean']) for r in pool) / len(pool),
            'repetitions': repetitions, 'seed': seed, 'group': group,
            'bootstrap_means': means}

def main():
    p = argparse.ArgumentParser()
    p.add_argument('--data', type=Path, default=DATA)
    p.add_argument('--n', type=int, default=60)
    p.add_argument('--repetitions', type=int, default=500)
    p.add_argument('--seed', type=int, default=42)
    p.add_argument('--group', choices=['all', 'weekday', 'weekend'], default='all')
    p.add_argument('--output', type=Path, default=Path('ch03_result.json'))
    a = p.parse_args()
    with a.data.open(encoding='utf-8') as f:
        result = analyze(list(csv.DictReader(f)), a.n, a.repetitions, a.seed, a.group)
    a.output.write_text(json.dumps(result, indent=2), encoding='utf-8')
    with a.output.with_suffix('.csv').open('w', encoding='utf-8', newline='') as f:
        w = csv.DictWriter(f, fieldnames=['estimate', 'lower', 'upper', 'n_days'])
        w.writeheader(); w.writerow({k: result[k] for k in w.fieldnames})
    print(json.dumps({k:v for k,v in result.items() if k != 'bootstrap_means'}, indent=2))

if __name__ == '__main__': main()
