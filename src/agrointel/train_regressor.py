import time
from sklearn.dummy import DummyRegressor
from sklearn.ensemble import ExtraTreesRegressor, GradientBoostingRegressor
from .config import RFEATURES,CONFIG
from .preprocessing import regression_pipeline
from .evaluation import regression_metrics

def train(frame):
    years=sorted(frame.year.unique())
    nt=CONFIG['regression_test_years']
    nv=CONFIG['regression_validation_years']
    test_years=years[-nt:]
    val_years=years[-nt-nv:-nt]
    train=frame[frame.year<min(val_years)]
    val=frame[frame.year.isin(val_years)]
    test=frame[frame.year.isin(test_years)]
    if min(len(train),len(val),len(test))<100:
        raise ValueError('Insufficient chronological coverage')
    candidates={'dummy':DummyRegressor(strategy='median'),
        'extra_trees':ExtraTreesRegressor(n_estimators=CONFIG['tree_count'],min_samples_leaf=5,max_depth=24,n_jobs=CONFIG['workers'],random_state=CONFIG['seed']),
        'gradient_boosting':GradientBoostingRegressor(n_estimators=120,max_depth=4,learning_rate=.08,loss='huber',random_state=42,n_iter_no_change=10,validation_fraction=.1)}
    comparisons=[]
    for name,estimator in candidates.items():
        start=time.perf_counter()
        model=regression_pipeline(estimator).fit(train[RFEATURES],train['yield'])
        scores=regression_metrics(val['yield'],model.predict(val[RFEATURES]))
        comparisons.append(dict(task='regression',model=name,**scores,seconds=time.perf_counter()-start))
        print(name,scores,flush=True)
    selected=min(comparisons,key=lambda r:r['mae'])['model']
    fit=frame[frame.year<min(test_years)]
    model=regression_pipeline(candidates[selected]).fit(fit[RFEATURES],fit['yield'])
    prediction=model.predict(test[RFEATURES])
    baseline=regression_pipeline(DummyRegressor(strategy='median')).fit(fit[RFEATURES],fit['yield'])
    metrics={'selected':selected,'test':regression_metrics(test['yield'],prediction),
        'baseline_test':regression_metrics(test['yield'],baseline.predict(test[RFEATURES])),
        'train_rows':len(fit),'test_rows':len(test),'test_years':[int(v) for v in test_years],
        'validation_years':[int(v) for v in val_years],'fit_years':[int(fit.year.min()),int(fit.year.max())]}
    return model,metrics,comparisons,fit,val,test,prediction
