"""
STEP 3 - Create the MySQL tables and load data into them.
Safe to run again: it clears old rows first.
"""
import json
import pandas as pd
import mysql.connector
from config import *

# 1) Create database + tables from schema.sql (connect WITHOUT a database first)
cfg = {k: v for k, v in DB_CONFIG.items() if k != "database"}
conn = mysql.connector.connect(**cfg)
cur = conn.cursor()
with open("schema.sql") as f:
    for statement in f.read().split(";"):
        if statement.strip():
            cur.execute(statement)
conn.database = DB_CONFIG["database"]

# 2) Clear old data so re-running does not create duplicates
for table in ["air_quality", "predictions", "anomalies", "model_metrics"]:
    cur.execute(f"DELETE FROM {table}")

# 3) Load cleaned readings
clean = pd.read_csv(CLEAN_CSV)
cur.executemany("INSERT INTO air_quality (date, location, pm25) VALUES (%s,%s,%s)",
                list(clean[["date", "location", "pm25"]].itertuples(index=False, name=None)))

# 4) Load backtest predictions (both models)
bt = pd.read_csv(BACKTEST_CSV)
bt["location"] = DEFAULT_LOCATION
cur.executemany("""INSERT INTO predictions
                   (date, location, model_name, predicted_pm25, actual_pm25, source)
                   VALUES (%s,%s,%s,%s,%s,'backtest')""",
                list(bt[["date", "location", "model_name", "predicted_pm25", "actual_pm25"]]
                     .itertuples(index=False, name=None)))

# 5) Load anomalies
an = pd.read_csv(ANOMALY_CSV)
cur.executemany("INSERT INTO anomalies (date, location, pm25, score, status) VALUES (%s,%s,%s,%s,'Review')",
                list(an[["date", "location", "pm25", "score"]].itertuples(index=False, name=None)))

# 6) Load model metrics
with open(METRICS_JSON) as f:
    m = json.load(f)
for name, r in m["results"].items():
    cur.execute("INSERT INTO model_metrics (model_name, mae, rmse, r2, is_selected) VALUES (%s,%s,%s,%s,%s)",
                (name, r["mae"], r["rmse"], r["r2"], name == m["best"]))

conn.commit()
print(f"Loaded {len(clean)} readings, {len(bt)} predictions, {len(an)} anomalies.")
print("Database ready. Next: python app.py")
cur.close(); conn.close()
