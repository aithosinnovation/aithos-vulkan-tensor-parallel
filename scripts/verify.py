"""Verify public timing tables and derived summaries without private captures or GPU access."""
import csv,hashlib,json,math,statistics
from collections import defaultdict
from pathlib import Path
R=Path(__file__).resolve().parents[1]

def verify():
 data=json.loads((R/'data/summary.json').read_text(encoding='utf-8'))
 records={(r['run_id'],r['test']):r for r in data['records']}
 rows=list(csv.DictReader((R/'data/samples.csv').open(encoding='utf-8',newline='')))
 assert len(rows)==data['meta']['timings']==280
 grouped=defaultdict(list)
 for row in rows:
  key=(row['run_id'],row['test']); assert key in records
  rec=records[key]; rep=int(row['rep'])-1; elapsed=int(row['elapsed_ns'])
  assert elapsed==rec['samples_ns'][rep]
  assert math.isclose(float(row['tokens_per_second']),rec['samples_ts'][rep],rel_tol=1e-10)
  for field in ('effective_context','effective_batch','effective_ubatch'): assert int(row[field])==rec[field]
  grouped[key].append(rec['samples_ts'][rep])
 for key,rec in records.items():
  rates=grouped[key]; assert len(rates)==5 and rates==rec['samples_ts']
  assert statistics.median(rates)==rec['median'] and min(rates)==rec['min'] and max(rates)==rec['max']
 for comp in data['comparisons']:
  for pair in comp['pairs']:
   a=records[(pair['block']+'-'+comp['mode'],comp['test'])]; b=records[(pair['block']+'-rtx',comp['test'])]
   assert pair['candidate_median']==a['median'] and pair['rtx_median']==b['median'] and pair['ratio']==a['median']/b['median']
 assert json.loads((R/'docs/data.json').read_text(encoding='utf-8'))==data
 js=(R/'docs/data.js').read_text(encoding='utf-8')
 assert json.loads(js[len('window.BENCH_DATA = '):].strip().removesuffix(';'))==data
 for path,h in json.loads((R/'manifest.json').read_text(encoding='utf-8'))['files_sha256'].items(): assert hashlib.sha256((R/path).read_bytes()).hexdigest()==h,path
 print(f'PASS: {len(records)} timing records, {len(rows)} samples, medians/ranges/ratios, contexts, explorer data and file hashes. No GPU or private captures used.')
if __name__=='__main__': verify()
