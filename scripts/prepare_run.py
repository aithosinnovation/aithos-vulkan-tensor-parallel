"""Bind recorded protocol to local paths. Does not launch benchmarks or install tools."""
import argparse,json,hashlib
from pathlib import Path
R=Path(__file__).resolve().parents[1]
p=argparse.ArgumentParser();p.add_argument('--model',type=Path,required=True);p.add_argument('--llama-root',type=Path,required=True);p.add_argument('--work-root',type=Path,required=True);a=p.parse_args()
if a.work_root.exists():raise SystemExit('Work root exists; choose a new directory')
with a.model.open('rb') as f:
 h=hashlib.sha256()
 for chunk in iter(lambda:f.read(8*1024*1024),b''):h.update(chunk)
if h.hexdigest()!='78272d8d32084548bd450394a560eb2d70de8232ab96a725769b1f9171235c1c':raise SystemExit('Model bytes differ from recorded protocol; do not silently relabel')
plans=json.loads((R/'data/run-plans.json').read_text())
for case in plans:
 case['model']=str(a.model);case['argv']=[str(a.model) if s=='${MODEL}' else s for s in case['argv']]
binaries={}
for f in sorted((a.llama_root/'build/bin').iterdir()):
 if f.suffix.lower() in ('.dll','.exe'):binaries[f.name]=hashlib.sha256(f.read_bytes()).hexdigest()
if 'llama-bench.exe' not in binaries:raise SystemExit('Expected native build/bin/llama-bench.exe')
a.work_root.mkdir(parents=True);(a.work_root/'plans.json').write_text(json.dumps(plans,indent=2)+'\n');(a.work_root/'frozen-binaries.json').write_text(json.dumps(binaries,indent=2)+'\n')
print('Prepared',len(plans),'cases. Nothing executed. Verify source/drivers/device descriptions and compile+run the layer correctness gate before benchmarking.')
