"""Schema checks and explicit, audited cleaning decisions."""
import numpy as np
import pandas as pd
from .config import ROOT, CFEATURES, CROP_MAP

def normalise(value):
    return ' '.join(str(value).strip().lower().split())

def profile(frame):
    return {'rows':len(frame), 'columns':list(frame.columns),
        'missing':frame.isna().sum().astype(int).to_dict(),
        'duplicates':int(frame.duplicated().sum()),
        'dtypes':frame.dtypes.astype(str).to_dict()}

def load_clean():
    a = pd.read_csv(ROOT / 'data/raw/crop.csv')
    b = pd.read_csv(ROOT / 'data/raw/production.csv')
    audit = {'crop_raw':profile(a), 'production_raw':profile(b)}
    a.columns = a.columns.str.strip()
    if not set(CFEATURES + ['label']).issubset(a):
        raise ValueError('Unexpected crop schema')
    a = a.drop_duplicates().dropna(subset=['label']).copy()
    a['label'] = a.label.map(normalise)
    for c in CFEATURES:
        a[c] = pd.to_numeric(a[c], errors='coerce')
    valid = (a[['N','P','K','rainfall']].ge(0) | a[['N','P','K','rainfall']].isna()).all(axis=1)
    valid &= a.humidity.between(0,100) | a.humidity.isna()
    valid &= a.ph.between(0,14) | a.ph.isna()
    valid &= a.temperature.between(-50,65) | a.temperature.isna()
    a = a[valid & ~a[CFEATURES].isin([np.inf,-np.inf]).any(axis=1)].copy()
    b.columns = b.columns.str.strip().str.lower()
    if not set(['state','district','crop','season','year','area','production']).issubset(b):
        raise ValueError(f'Unexpected regional schema: {list(b.columns)}')
    b = b.drop_duplicates().copy()
    for c in ['state','district','crop','season']:
        b[c] = b[c].astype('string').str.strip().str.lower().str.replace(r'\s+',' ',regex=True)
    b['year'] = pd.to_numeric(b.year.astype(str).str.extract(r'(\d{4})',expand=False),errors='coerce')
    for c in ['area','production']:
        b[c] = pd.to_numeric(b[c],errors='coerce')
    b = b.dropna(subset=['state','district','crop','season','year','area','production'])
    b = b[(b.area>0) & (b.production>=0) & np.isfinite(b.area) & np.isfinite(b.production)]
    # Restrict to individually named, interoperable crops; exclude bales/nuts and aggregates.
    b = b[b.crop.isin(set(CROP_MAP.values()))].copy()
    keys = ['state','district','crop','season','year']
    conflicts = b.duplicated(keys,keep=False)
    audit['ambiguous_key_rows_excluded'] = int(conflicts.sum())
    b = b[~conflicts].copy()
    b['year'] = b.year.astype(int)
    b['yield'] = b.production / b.area
    audit.update(crop_clean=profile(a), production_clean=profile(b),
        excluded_units=['cotton (bales)','jute (bales)','coconut (nuts)'],
        crop_counts=a.label.value_counts().to_dict(), regional_crop_counts=b.crop.value_counts().to_dict(),
        years=[int(b.year.min()),int(b.year.max())],
        cleaning='Exact duplicates removed; conflicting keys excluded, never summed; plausible yield extremes retained.')
    processed = ROOT / 'data/processed'
    processed.mkdir(parents=True,exist_ok=True)
    a.to_csv(processed/'crop.csv',index=False)
    b.to_csv(processed/'yield.csv',index=False)
    return a,b,audit
