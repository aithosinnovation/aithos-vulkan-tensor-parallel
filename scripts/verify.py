"""Check published timing calculations and file integrity without GPU or private captures."""
import csv
import hashlib
import json
import math
import statistics
from collections import defaultdict
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def require(condition, message):
    if not condition:
        raise ValueError(message)


def close(a, b):
    return math.isclose(a, b, rel_tol=1e-10)


def verify():
    data = json.loads((ROOT / 'data/summary.json').read_text(encoding='utf-8'))
    records = {(r['run_id'], r['test']): r for r in data['records']}
    require(len(records) == len(data['records']) == 56, 'record count or duplicate key')
    require(len({r['run_id'] for r in records.values()}) == data['meta']['benchmark_processes'] == 20,
            'benchmark-process count')
    with (ROOT / 'data/samples.csv').open(encoding='utf-8', newline='') as stream:
        rows = list(csv.DictReader(stream))
    require(len(rows) == data['meta']['timings'] == 280, 'sample count')
    grouped = defaultdict(dict)
    for row in rows:
        key = (row['run_id'], row['test'])
        require(key in records, f'unknown CSV record: {key}')
        rec = records[key]
        rep = int(row['rep']) - 1
        require(0 <= rep < 5 and rep not in grouped[key], f'invalid/duplicate repetition: {key}')
        elapsed = int(row['elapsed_ns'])
        require(elapsed > 0 and elapsed == rec['samples_ns'][rep], f'elapsed time: {key}')
        rate = (rec['n_prompt'] + rec['n_gen']) * 1e9 / elapsed
        require(close(rate, rec['samples_ts'][rep]), f'recomputed rate: {key}, rep {rep + 1}')
        require(close(float(row['tokens_per_second']), rate), f'CSV rate: {key}, rep {rep + 1}')
        for field in ('effective_context', 'effective_batch', 'effective_ubatch'):
            require(int(row[field]) == rec[field], f'CSV/summary {field}: {key}')
        require(int(row['requested_batch']) == rec['batch'], f'CSV requested batch: {key}')
        require(int(row['requested_ubatch']) == rec['ubatch'], f'CSV requested ubatch: {key}')
        grouped[key][rep] = rec['samples_ts'][rep]
    for key, rec in records.items():
        require(set(grouped[key]) == set(range(5)), f'missing repetition: {key}')
        rates = [grouped[key][rep] for rep in range(5)]
        require(len(rec['samples_ns']) == len(rec['samples_ts']) == 5, f'sample array size: {key}')
        require(statistics.median(rates) == rec['median'], f'median: {key}')
        require(min(rates) == rec['min'] and max(rates) == rec['max'], f'range: {key}')
    pair_count = 0
    for comparison in data['comparisons']:
        ratios = []
        for pair in comparison['pairs']:
            a = records[(pair['block'] + '-' + comparison['mode'], comparison['test'])]
            b = records[(pair['block'] + '-rtx', comparison['test'])]
            ratio = a['median'] / b['median']
            require(pair['candidate_median'] == a['median'] and pair['rtx_median'] == b['median'],
                    'comparison medians')
            require(close(pair['ratio'], ratio), 'comparison ratio')
            require(close(pair['percent_change'], (ratio - 1) * 100), 'comparison percent change')
            overlap = max(a['min'], b['min']) <= min(a['max'], b['max'])
            require(pair['ranges_overlap'] == overlap, 'comparison range overlap')
            ratios.append(ratio)
            pair_count += 1
        require(comparison['ratio_range'] == [min(ratios), max(ratios)], 'comparison ratio range')
        same_direction = all(r < 1 for r in ratios) or all(r > 1 for r in ratios)
        require(comparison['same_direction'] == same_direction, 'comparison direction')
    require(json.loads((ROOT / 'docs/data.json').read_text(encoding='utf-8')) == data,
            'explorer JSON differs')
    js = (ROOT / 'docs/data.js').read_text(encoding='utf-8')
    require(js.startswith('window.BENCH_DATA = '), 'explorer JavaScript wrapper')
    require(json.loads(js[len('window.BENCH_DATA = '):].strip().removesuffix(';')) == data,
            'explorer JavaScript data differs')
    manifest = json.loads((ROOT / 'manifest.json').read_text(encoding='utf-8'))['files_sha256']
    for path, expected in manifest.items():
        require(hashlib.sha256((ROOT / path).read_bytes()).hexdigest() == expected,
                f'file hash: {path}')
    print(f'PASS: {len(records)} timing records, {len(rows)} recomputed sample rates, '
          f'process medians/ranges, {pair_count} matched comparison pairs, CSV settings, '
          'explorer payloads and file hashes. No GPU or private captures used.')


if __name__ == '__main__':
    verify()
