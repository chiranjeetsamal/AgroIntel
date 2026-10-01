import numpy as np
from sklearn.metrics import accuracy_score, f1_score, mean_absolute_error, root_mean_squared_error, r2_score, log_loss

def classification_metrics(model,x,y):
    p = model.predict_proba(x)
    labels = model.classes_
    top = labels[np.argsort(-p,axis=1)[:,:3]]
    confidence = p.max(axis=1)
    correct = labels[p.argmax(axis=1)] == np.asarray(y)
    ece = 0.0
    for lo in np.arange(0,1,0.1):
        mask = (confidence>=lo) & (confidence<lo+0.1 if lo<0.9 else confidence<=1)
        if mask.any():
            ece += mask.mean()*abs(confidence[mask].mean()-correct[mask].mean())
    return {'top1':accuracy_score(y,model.predict(x)), 'top3':float((top==np.asarray(y)[:,None]).any(axis=1).mean()),
        'macro_f1':f1_score(y,model.predict(x),average='macro'), 'log_loss':log_loss(y,p,labels=labels),'ece':float(ece)}

def regression_metrics(y,p):
    return {'mae':mean_absolute_error(y,p),'rmse':root_mean_squared_error(y,p),'r2':r2_score(y,p)}
