"""Independent offline verification of published numerical assets; no inference."""
import argparse,array,hashlib,json,math,sys,zipfile
from pathlib import Path
p=argparse.ArgumentParser();p.add_argument('--archive',type=Path,required=True);a=p.parse_args();R=Path(__file__).resolve().parents[1];expected=json.loads((R/'data/correctness.json').read_text());teacher=expected['teacher_token_ids'];runs={}
with zipfile.ZipFile(a.archive) as z:
 manifest=json.loads(z.read('manifest.json'))
 for path,m in manifest.items():assert hashlib.sha256(z.read(path)).hexdigest()==m['sha256']
 for name in ('rtx-reference','rtx-repeat','b70','tensor-original','tensor-repeat','layer'):
  events=[json.loads(s) for s in z.read(name+'/original.jsonl').decode().splitlines()];prompt=next(e for e in events if e['event']=='prompt');t=[e for e in events if e['event']=='token'];forced=[e for e in events if e['event']=='teacher'];n=prompt['n_vocab'];raw=z.read(name+'/logits.f32');assert len(raw)==32*n*4
  logits=array.array('f');logits.frombytes(raw)
  if sys.byteorder!='little':logits.byteswap()
  assert all(map(math.isfinite,logits));assert [e['step'] for e in t]==list(range(32));assert [e['id'] for e in t]==teacher
  if forced:assert [e['id'] for e in forced]==teacher and [e['step'] for e in forced]==list(range(32))
  for i in range(32):assert max(range(n),key=lambda j:logits[i*n+j])==t[i]['id']
  assert z.read(name+'/generated.bin')==bytes.fromhex(''.join(e['piece_hex'] for e in t))
  runs[name]=(prompt,logits,hashlib.sha256(raw).hexdigest())
 assert runs['rtx-reference'][2]==runs['rtx-repeat'][2];assert runs['tensor-original'][2]==runs['tensor-repeat'][2]
 for name,key in [('b70','reference__b70'),('tensor-repeat','reference__mixed'),('layer',None)]:
  rp,x,h=runs['rtx-reference'];cp,y,h=runs[name];assert cp['tokens']==rp['tokens'];n=rp['n_vocab'];rows=expected['layer']['rows'] if name=='layer' else expected['rows'][key]
  for i,e in enumerate(rows):
   xx=x[i*n:(i+1)*n];yy=y[i*n:(i+1)*n];mx=math.fsum(xx)/n;md=math.fsum(b-a for a,b in zip(xx,yy))/n
   nmse=math.fsum((b-a)**2 for a,b in zip(xx,yy))/math.fsum(a*a for a in xx)
   cen=math.fsum((b-a-md)**2 for a,b in zip(xx,yy))/math.fsum((a-mx)**2 for a in xx)
   assert math.isclose(nmse,e['nmse'],rel_tol=1e-12,abs_tol=1e-15);assert math.isclose(cen,e['centered_nmse'],rel_tol=1e-12,abs_tol=1e-15)
print('PASS: six32-row finite/argmax/prefix captures, hashes,bytes, both bitidentical pairs and96raw/centered NMSE rows. No GPU work.')
