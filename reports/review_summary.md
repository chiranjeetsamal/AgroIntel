# Review summary

Students: Student A ([registration omitted]), Student B ([registration omitted]). BCSE206L, SCOPE & SENSE.

Completed: acquisition, audit, preprocessing, model comparison, trained artifacts, held-out evaluation, global validation importance, local CLI, MCP stdio tools, REST dashboard, local median-replacement sensitivity, optional weather context, JSON/CSV exports, tests and deployment recipe.

Application version 1.0.0. Model files and their held-out evaluation are unchanged. Local academic prototype: public hosting and production security are not claimed. Docker recipe is included but Docker is not installed on the development host.

Classification: {"selected": "extra_trees", "test": {"top1": 0.9954545454545455, "top3": 1.0, "macro_f1": 0.9954517027687758, "log_loss": 0.057301752782304115, "ece": 0.04701116431338005}, "train": {"top1": 1.0, "top3": 1.0, "macro_f1": 1.0, "log_loss": 0.044710200570751236, "ece": 0.043367939201579095}, "baseline_test": {"top1": 0.045454545454545456, "top3": 0.13636363636363635, "macro_f1": 0.003952569169960474, "log_loss": 3.091042453358315, "ece": 0.0}, "train_rows": 1760, "test_rows": 440, "calibration": {"used": true, "raw_validation": {"top1": 0.9886363636363636, "top3": 1.0, "macro_f1": 0.9886363636363636, "log_loss": 0.11897411460206012, "ece": 0.08809659090909092}, "sigmoid_validation": {"top1": 0.9971590909090909, "top3": 1.0, "macro_f1": 0.9971563138718564, "log_loss": 0.0722110774087174, "ece": 0.06205308428711154}}}

Regression: {"selected": "extra_trees", "test": {"mae": 0.6261238847659997, "rmse": 2.08805267799537, "r2": 0.930385053676633}, "baseline_test": {"mae": 2.277229773765313, "rmse": 8.126378250302276, "r2": -0.05442005338327616}, "train_rows": 49404, "test_rows": 2275, "test_years": [2011, 2012], "validation_years": [2009, 2010], "fit_years": [1998, 2010]}

Yield overlap: {"rice": "rice", "maize": "maize", "chickpea": "gram", "pigeonpeas": "arhar (tur)", "mungbean": "moong", "blackgram": "urad", "lentil": "masoor", "mothbeans": "moth", "banana": "banana"}

Historical data is old; later years require extrapolation warnings. Suitability probabilities describe benchmark classification, not farm success. Yield extremes remain and can increase RMSE. Source chain and nutrient units remain limited.

Elapsed seconds: 82.8
