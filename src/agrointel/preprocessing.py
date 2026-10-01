from sklearn.compose import ColumnTransformer
from sklearn.preprocessing import OneHotEncoder
from sklearn.impute import SimpleImputer
from sklearn.pipeline import Pipeline
from .config import RFEATURES

def classification_pipeline(model):
    return Pipeline([('imputer',SimpleImputer(strategy='median')),('model',model)])

def regression_pipeline(model):
    encoder = ColumnTransformer([
        ('category',OneHotEncoder(handle_unknown='ignore',sparse_output=True),RFEATURES[:4]),
        ('numeric',SimpleImputer(strategy='median'),RFEATURES[4:])])
    return Pipeline([('preprocess',encoder),('model',model)])
