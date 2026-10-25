"""
STEP 2 - Train and evaluate the ML models.

  * Linear Regression  (simple baseline)
  * Random Forest      (more powerful, captures non-linear patterns)
  * Isolation Forest   (anomaly detection - finds unusual readings)

Outputs are saved in models/ and data/ ; setup_db.py then loads them into MySQL.
"""
import json
import joblib
import numpy as np
import pandas as pd
from sklearn.ensemble import IsolationForest, RandomForestRegressor
from sklearn.linear_model import LinearRegression
from sklearn.metrics import mean_absolute_error, mean_squared_error, r2_score

from config import *
from preprocess import FEATURES, ANOMALY_FEATURES, load_and_clean, make_features, anomaly_features

# ---------- 1. Clean data and build features ----------
clean = load_and_clean(RAW_CSV)
clean.to_csv(CLEAN_CSV, index=False)

data = make_features(clean)
data = data.dropna(subset=FEATURES + ["next_pm25"])   # first rows (no lags) and last row (no target)

# ---------- 2. Time-based split ----------
# We must NOT shuffle: the model should learn from the past and be tested on the future.
split = int(len(data) * 0.8)
train, test = data.iloc[:split], data.iloc[split:]
X_train, y_train = train[FEATURES], train["next_pm25"]
X_test,  y_test  = test[FEATURES],  test["next_pm25"]
print(f"[split] train rows: {len(train)} | test rows: {len(test)}")

# ---------- 3. Train and compare two models ----------
models = {
    "Linear Regression": LinearRegression(),
    "Random Forest": RandomForestRegressor(n_estimators=200, max_depth=10,
                                           random_state=42, n_jobs=-1),
}

results, preds = {}, {}
for name, model in models.items():
    model.fit(X_train, y_train)
    p = model.predict(X_test)
    preds[name] = p
    results[name] = {
        "mae":  round(float(mean_absolute_error(y_test, p)), 3),            # average error
        "rmse": round(float(np.sqrt(mean_squared_error(y_test, p))), 3),    # penalises big errors
        "r2":   round(float(r2_score(y_test, p)), 3),                       # 1.0 = perfect
    }
    print(f"[{name}] {results[name]}")

# Pick the model with the lowest RMSE
best_name = min(results, key=lambda k: results[k]["rmse"])
print(f"[best] {best_name}")
joblib.dump({"name": best_name, "model": models[best_name], "features": FEATURES}, MODEL_PATH)

# Save backtest predictions (date = the day being predicted = row date + 1)
backtest = []
for name, p in preds.items():
    backtest.append(pd.DataFrame({
        "date": (test["date"] + pd.Timedelta(days=1)).dt.strftime("%Y-%m-%d").values,
        "model_name": name, "predicted_pm25": p.round(1), "actual_pm25": y_test.values}))
pd.concat(backtest).to_csv(BACKTEST_CSV, index=False)

# ---------- 4. Anomaly detection with Isolation Forest ----------
adf = anomaly_features(clean).dropna(subset=ANOMALY_FEATURES)
iso = IsolationForest(n_estimators=200, contamination=0.03, random_state=42)  # ~3% flagged
iso.fit(adf[ANOMALY_FEATURES])
adf["flag"] = iso.predict(adf[ANOMALY_FEATURES])                  # -1 = anomaly, 1 = normal
adf["score"] = -iso.decision_function(adf[ANOMALY_FEATURES])      # higher = more unusual
flagged = adf[adf["flag"] == -1][["date", "location", "pm25", "score"]].copy()
flagged["date"] = flagged["date"].dt.strftime("%Y-%m-%d")
flagged["score"] = flagged["score"].round(3)
flagged.to_csv(ANOMALY_CSV, index=False)
joblib.dump(iso, ISO_PATH)
print(f"[anomaly] flagged {len(flagged)} unusual readings")

# ---------- 5. Save metrics for the dashboard ----------
rf = models["Random Forest"]
importance = dict(zip(FEATURES, [round(float(x), 4) for x in rf.feature_importances_]))
with open(METRICS_JSON, "w") as f:
    json.dump({"results": results, "best": best_name, "feature_importance": importance,
               "train_rows": len(train), "test_rows": len(test)}, f, indent=2)
print("Training finished. Next: python setup_db.py")
