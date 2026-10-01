"""Saved-artifact prediction; suitable for later MCP wrapping."""
import json
from functools import lru_cache
import joblib
import numpy as np
import pandas as pd
from .config import ROOT,CFEATURES,RFEATURES
from .validation import validate

@lru_cache(maxsize=1)
def artifacts():
    return (joblib.load(ROOT/'artifacts/crop_classifier.joblib'),joblib.load(ROOT/'artifacts/yield_regressor.joblib'),json.loads((ROOT/'artifacts/metadata.json').read_text()))

def predict_crop_and_yield(request:dict)->dict:
    r=validate(request)
    classifier,regressor,meta=artifacts()
    values=[r[k] for k in ['nitrogen','phosphorus','potassium','temperature','humidity','ph','rainfall']]
    warnings=[]
    for key,value in zip(CFEATURES,values):
        lo,hi=meta['classifier_ranges'][key]
        if not lo<=value<=hi:
            warnings.append(f'{key} outside training range [{lo}, {hi}]')
    if not meta['yield_years'][0]<=r['year']<=meta['yield_years'][1]:
        warnings.append('Year outside historical training coverage; tree extrapolation is limited')
    if not meta['area_range'][0]<=r['area']<=meta['area_range'][1]:
        warnings.append('Area outside training range')
    probabilities=classifier.predict_proba(pd.DataFrame([values],columns=CFEATURES))[0]
    recommendations=[]
    coverage=set(tuple(v) for v in meta['supported_combinations'])
    for i in np.argsort(-probabilities)[:3]:
        crop=str(classifier.classes_[i])
        mapped=meta['crop_mapping'].get(crop)
        combo=(r['state'],r['district'],mapped,r['season'])
        status='supported' if combo in coverage else ('crop_unavailable' if mapped is None else 'region_season_unavailable')
        prediction=None
        if status=='supported':
            record=dict(state=r['state'],district=r['district'],crop=mapped,season=r['season'],year=r['year'],area=r['area'])
            prediction=max(0.,float(regressor.predict(pd.DataFrame([record],columns=RFEATURES))[0]))
        else:
            warnings.append(f'{crop}: {status}')
        recommendations.append(dict(crop=crop,suitability_probability=float(probabilities[i]),estimated_yield=prediction,
            yield_unit='tonnes/hectare',yield_status=status,explanation={'status':'local_explanation_deferred'}))
    return dict(recommendations=recommendations,warnings=warnings,classifier_version=meta['version'],regressor_version=meta['version'],
        training_data_coverage={'yield_years':meta['yield_years'],'crop_classes':len(classifier.classes_)})
