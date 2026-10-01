"""Acquire public CSVs without modifying source records."""
from pathlib import Path
from datetime import datetime, timezone
import hashlib, io, json, zipfile
import pandas as pd
import requests
ROOT = Path(__file__).resolve().parents[1]
def main():
    raw = ROOT / 'data/raw'
    raw.mkdir(parents=True, exist_ok=True)
    provenance = ROOT / 'data/provenance'
    provenance.mkdir(parents=True, exist_ok=True)
    sources = [
        ('crop.csv', 'https://www.kaggle.com/api/v1/datasets/download/atharvaingle/crop-recommendation-dataset', 'Atharva Ingle / Kaggle', 'See Kaggle data card; raw data excluded from deliverable'),
        ('production.csv', 'https://raw.githubusercontent.com/k0rn/India_Agri_Data/master/agridata.csv', 'k0rn; attributed to Government of India', 'Repository CC0; original provenance incomplete'),
    ]
    records = []
    for name, url, publisher, licence in sources:
        response = requests.get(url, timeout=120)
        response.raise_for_status()
        content = response.content
        if content[:2] == b'PK':
            (raw / 'crop_download.zip').write_bytes(content)
            with zipfile.ZipFile(io.BytesIO(content)) as archive:
                entries = [n for n in archive.namelist() if n.lower().endswith('.csv')]
                if len(entries) != 1:
                    raise ValueError(entries)
                content = archive.read(entries[0])
        (raw / name).write_bytes(content)
        frame = pd.read_csv(raw / name)
        records.append(dict(file=name, url=url, publisher=publisher, licence=licence,
            downloaded_at=datetime.now(timezone.utc).isoformat(), sha256=hashlib.sha256(content).hexdigest(),
            shape=list(frame.shape), columns=list(frame.columns)))
        print(name, frame.shape, list(frame.columns), flush=True)
    (provenance / 'sources.json').write_text(json.dumps(records, indent=2), encoding='utf-8')
if __name__ == '__main__':
    main()
