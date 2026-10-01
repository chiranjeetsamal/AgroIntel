import json
import numpy as np
import pytest
from agrointel.config import ROOT,CFEATURES,RFEATURES
from agrointel.validation import validate
from agrointel.inference import predict_crop_and_yield,artifacts

@pytest.fixture
def sample_request():
    return json.loads((ROOT/'examples/request.json').read_text())

@pytest.mark.parametrize('field,value',[('nitrogen',-1),('humidity',101),('ph',15),('area',0),('year',2020.5),('temperature',float('inf')),('rainfall','20'),('district',''),('nitrogen',True)])
def test_invalid(sample_request,field,value):
    sample_request[field]=value
    with pytest.raises(ValueError):
        validate(sample_request)

def test_required(sample_request):
    del sample_request['season']
    with pytest.raises(ValueError):
        validate(sample_request)

def test_saved_models_and_order(sample_request):
    classifier,regressor,meta=artifacts()
    assert list(classifier.feature_names_in_)==CFEATURES
    assert list(regressor.feature_names_in_)==RFEATURES
    assert 'production' not in regressor.feature_names_in_
    result=predict_crop_and_yield(sample_request)
    probabilities=[r['suitability_probability'] for r in result['recommendations']]
    assert len(probabilities)==3
    assert probabilities==sorted(probabilities,reverse=True)
    assert all(0<=p<=1 for p in probabilities)
    assert result['recommendations'][0]['estimated_yield'] is not None
    json.dumps(result,allow_nan=False)

def test_unknown_geography(sample_request):
    sample_request['district']='unknown district'
    result=predict_crop_and_yield(sample_request)
    assert all(r['estimated_yield'] is None for r in result['recommendations'])
    assert result['warnings']

def test_crop_without_yield(sample_request):
    import pandas as pd
    # Real benchmark class absent from regional crop support.
    row=pd.read_csv(ROOT/'data/raw/crop.csv').query("label == 'apple'").iloc[0]
    for key,feature in zip(['nitrogen','phosphorus','potassium','temperature','humidity','ph','rainfall'],CFEATURES):
        sample_request[key]=float(row[feature])
    result=predict_crop_and_yield(sample_request)
    apples=[r for r in result['recommendations'] if r['crop']=='apple']
    assert apples and apples[0]['yield_status']=='crop_unavailable'
    assert apples[0]['estimated_yield'] is None

def test_extrapolation_warning(sample_request):
    sample_request['year']=2026
    assert any('Year outside' in w for w in predict_crop_and_yield(sample_request)['warnings'])
