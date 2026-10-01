"""Record reproducible environment and audit the completed delivery."""
from pathlib import Path
import importlib.metadata,json,hashlib,ctypes,os
from datetime import datetime,timezone
ROOT=Path(__file__).resolve().parents[1]

def main():
    packages=sorted(f'{d.metadata["Name"]}=={d.version}' for d in importlib.metadata.distributions() if d.metadata['Name'].lower() not in {'agrointel','pip'})
    (ROOT/'requirements-lock.txt').write_text('\n'.join(packages)+'\n',encoding='utf-8')
    path=ROOT/'artifacts/metadata.json'
    meta=json.loads(path.read_text())
    meta['artifact_sha256']={p.name:hashlib.sha256(p.read_bytes()).hexdigest() for p in (ROOT/'artifacts').glob('*.joblib')}
    meta['recorded_at']=datetime.now(timezone.utc).isoformat()
    class Memory(ctypes.Structure):
        _fields_=[('length',ctypes.c_ulong),('load',ctypes.c_ulong)]+[(n,ctypes.c_ulonglong) for n in ['total','available','page_total','page_available','virtual_total','virtual_available','extended']]
    info=Memory(); info.length=ctypes.sizeof(info)
    if os.name=='nt' and ctypes.windll.kernel32.GlobalMemoryStatusEx(ctypes.byref(info)):
        meta['runtime']['total_ram_gib']=round(info.total/2**30,2)
    path.write_text(json.dumps(meta,indent=2),encoding='utf-8')
    units=meta['units']
    dictionary='\n'.join(f'- **{k}**: {v}' for k,v in units.items())
    (ROOT/'data/provenance/data_dictionary.md').write_text('# Data dictionary\n\n'+dictionary+'\n\nRegional year strings use the starting calendar year. Source yield column is recomputed. Current published files are community snapshots, not independent field measurements.\n',encoding='utf-8')
    print({'artifact_sizes':{p.name:p.stat().st_size for p in (ROOT/'artifacts').glob('*.joblib')},'cpu':meta['runtime']},flush=True)

if __name__=='__main__':
    main()
