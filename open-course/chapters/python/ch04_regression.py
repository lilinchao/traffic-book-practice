"""Reproduce chronological bike-demand baselines without target leakage."""
from pathlib import Path
import argparse, json
import numpy as np
import pandas as pd
from sklearn.compose import ColumnTransformer
from sklearn.pipeline import make_pipeline
from sklearn.preprocessing import OneHotEncoder, StandardScaler
from sklearn.linear_model import Ridge, PoissonRegressor

DATA = Path(__file__).resolve().parents[1] / 'data'
NUMERIC = ['temp', 'atemp', 'hum', 'windspeed']
CATEGORICAL = ['season', 'mnth', 'hr', 'holiday', 'weekday', 'workingday', 'weathersit']
FEATURES = NUMERIC + CATEGORICAL

def metrics(actual, predicted):
    e = np.asarray(predicted) - np.asarray(actual)
    return {'RMSE': float(np.sqrt(np.mean(e*e))), 'MAE': float(np.mean(np.abs(e))), 'bias': float(np.mean(e))}

def train(data=DATA):
    training = pd.read_csv(data / 'ch04_train.csv')
    validation = pd.read_csv(data / 'ch04_validation.csv')
    test = pd.read_csv(data / 'ch04_test.csv')
    predictions = {'mean': np.full(len(test), training.cnt.mean())}
    models = [{'id':'mean','name':'训练期均值','validation':metrics(validation.cnt,np.full(len(validation),training.cnt.mean()))}]
    for name, klass, alphas in [('ridge',Ridge,[1,10,100]),('poisson',PoissonRegressor,[.001,.1,1])]:
        best = None
        for alpha in alphas:
            transform = ColumnTransformer([
                ('numbers', StandardScaler(), NUMERIC),
                ('categories', OneHotEncoder(handle_unknown='ignore', sparse_output=False), CATEGORICAL)])
            estimator = klass(alpha=alpha, **({'max_iter':1000} if name=='poisson' else {}))
            model = make_pipeline(transform, estimator)
            model.fit(training[FEATURES], training.cnt)
            val = np.maximum(0, model.predict(validation[FEATURES]))
            score = metrics(validation.cnt, val)
            if best is None or score['RMSE'] < best[0]: best=(score['RMSE'],model,alpha,score)
        predictions[name] = np.maximum(0, best[1].predict(test[FEATURES]))
        models.append({'id':name, 'name':'岭回归' if name=='ridge' else '泊松回归', 'alpha':best[2], 'validation':best[3]})
    return test, predictions, models

def main():
    p=argparse.ArgumentParser(); p.add_argument('--data',type=Path,default=DATA);p.add_argument('--output',type=Path,default=Path('ch04_outputs'))
    a=p.parse_args();a.output.mkdir(parents=True,exist_ok=True)
    test,predictions,models=train(a.data)
    for name, values in predictions.items():
        pd.DataFrame({'id':test.id,'cnt':np.round(values,6)}).to_csv(a.output / f'{name}_submission.csv',index=False)
    (a.output/'validation.json').write_text(json.dumps(models,indent=2,ensure_ascii=False),encoding='utf-8')
    print('Predictions generated using training/validation only. Test labels were not opened.')

if __name__=='__main__': main()
