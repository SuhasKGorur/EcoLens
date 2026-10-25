"""
STEP 4 - The Flask web application (run: python app.py, open http://127.0.0.1:5000)
"""
import json
from datetime import timedelta

import joblib
import pandas as pd
from flask import Flask, flash, jsonify, redirect, render_template, request, url_for

from config import *
from db import execute, fetch_all
from preprocess import ANOMALY_FEATURES, FEATURES, anomaly_features, make_features

app = Flask(__name__)
app.secret_key = "ecolens-secret"          # needed for flash() messages

# Load the trained models once, when the app starts
best = joblib.load(MODEL_PATH)             # {"name":..., "model":..., "features":...}
iso = joblib.load(ISO_PATH)


# ---------------------------------------------------------------- helpers
def aqi_category(pm25):
    """Indian CPCB PM2.5 categories -> (label, bootstrap colour)."""
    if pm25 <= 30:  return "Good", "success"
    if pm25 <= 60:  return "Satisfactory", "info"
    if pm25 <= 90:  return "Moderate", "warning"
    if pm25 <= 120: return "Poor", "orange"
    if pm25 <= 250: return "Very Poor", "danger"
    return "Severe", "dark"

app.jinja_env.filters["aqi"] = aqi_category   # usable inside templates


def predict_next_day():
    """Use the last 14 readings in MySQL to forecast tomorrow, and save it."""
    rows = fetch_all("SELECT date, pm25 FROM air_quality ORDER BY date DESC LIMIT 14")
    if len(rows) < 8:
        return None
    df = pd.DataFrame(rows[::-1])                       # oldest -> newest
    df["date"] = pd.to_datetime(df["date"])
    df["pm25"] = df["pm25"].astype(float)

    latest_features = make_features(df).iloc[[-1]][FEATURES]   # features of the newest day
    predicted = round(float(best["model"].predict(latest_features)[0]), 1)
    target_date = (df["date"].iloc[-1] + timedelta(days=1)).strftime("%Y-%m-%d")

    execute("""INSERT INTO predictions (date, location, model_name, predicted_pm25, source)
               VALUES (%s,%s,%s,%s,'live')
               ON DUPLICATE KEY UPDATE predicted_pm25=VALUES(predicted_pm25)""",
            (target_date, DEFAULT_LOCATION, best["name"], predicted))
    return {"date": target_date, "predicted_pm25": predicted}


# ---------------------------------------------------------------- pages
@app.route("/")
def dashboard():
    latest = fetch_all("SELECT date, pm25 FROM air_quality ORDER BY date DESC LIMIT 1")[0]
    forecast = predict_next_day()                       # always fresh for the newest reading
    stats = fetch_all("""SELECT ROUND(AVG(pm25),1) AS avg30, MAX(pm25) AS max30
                         FROM (SELECT pm25 FROM air_quality ORDER BY date DESC LIMIT 30) t""")[0]
    n_anom = fetch_all("SELECT COUNT(*) AS c FROM anomalies")[0]["c"]
    latest_is_anom = bool(fetch_all("SELECT 1 FROM anomalies WHERE date=%s", (latest["date"],)))
    metric = fetch_all("SELECT * FROM model_metrics WHERE is_selected=TRUE")[0]
    return render_template("dashboard.html", latest=latest, forecast=forecast, stats=stats,
                           n_anom=n_anom, latest_is_anom=latest_is_anom, metric=metric,
                           model_name=best["name"])


@app.route("/history")
def history():
    start = request.args.get("start") or "1900-01-01"
    end = request.args.get("end") or "2999-12-31"
    rows = fetch_all("""SELECT a.date, a.location, a.pm25, (an.id IS NOT NULL) AS is_anomaly
                        FROM air_quality a LEFT JOIN anomalies an ON a.date = an.date
                        WHERE a.date BETWEEN %s AND %s ORDER BY a.date DESC LIMIT 200""",
                     (start, end))
    return render_template("history.html", rows=rows, start=request.args.get("start", ""),
                           end=request.args.get("end", ""))


@app.route("/anomalies")
def anomalies():
    rows = fetch_all("SELECT * FROM anomalies ORDER BY date DESC")
    return render_template("anomalies.html", rows=rows)


@app.route("/models")
def models_page():
    rows = fetch_all("SELECT * FROM model_metrics")
    with open(METRICS_JSON) as f:
        info = json.load(f)
    return render_template("models.html", rows=rows, info=info)


@app.route("/add", methods=["GET", "POST"])
def add_reading():
    """Add a new daily reading, check it for anomaly, update predictions."""
    if request.method == "POST":
        try:
            date = request.form["date"]
            pm25 = float(request.form["pm25"])
            assert 0 < pm25 <= 1000
        except (ValueError, AssertionError, KeyError):
            flash("Please enter a valid date and a PM2.5 value between 1 and 1000.", "danger")
            return redirect(url_for("add_reading"))

        # Anomaly check: needs the previous 8 readings for context
        prev = fetch_all("SELECT pm25 FROM air_quality WHERE date < %s ORDER BY date DESC LIMIT 8", (date,))
        is_anomaly = False
        if len(prev) == 8:
            series = pd.DataFrame({"pm25": [float(r["pm25"]) for r in prev[::-1]] + [pm25]})
            row = anomaly_features(series).iloc[[-1]][ANOMALY_FEATURES]
            is_anomaly = iso.predict(row)[0] == -1
            score = round(float(-iso.decision_function(row)[0]), 3)

        execute("""INSERT INTO air_quality (date, location, pm25) VALUES (%s,%s,%s)
                   ON DUPLICATE KEY UPDATE pm25=VALUES(pm25)""", (date, DEFAULT_LOCATION, pm25))
        execute("UPDATE predictions SET actual_pm25=%s WHERE date=%s", (pm25, date))  # fill actual value
        if is_anomaly:
            execute("""INSERT INTO anomalies (date, location, pm25, score, status) VALUES (%s,%s,%s,%s,'Review')
                       ON DUPLICATE KEY UPDATE pm25=VALUES(pm25), score=VALUES(score)""",
                    (date, DEFAULT_LOCATION, pm25, score))
            flash(f"Saved. ⚠ {pm25} µg/m³ looks UNUSUAL and was flagged for review.", "warning")
        else:
            execute("DELETE FROM anomalies WHERE date=%s", (date,))
            flash("Saved. The reading looks normal. Dashboard forecast updated.", "success")
        return redirect(url_for("add_reading"))
    return render_template("add.html")


# ---------------------------------------------------------------- JSON APIs (used by Chart.js)
@app.route("/api/trend")
def api_trend():
    days = request.args.get("days", 90, type=int)
    rows = fetch_all("""SELECT a.date, a.pm25, (an.id IS NOT NULL) AS is_anomaly
                        FROM air_quality a LEFT JOIN anomalies an ON a.date = an.date
                        ORDER BY a.date DESC LIMIT %s""", (days + 6,))
    df = pd.DataFrame(rows[::-1])
    df["pm25"] = df["pm25"].astype(float)
    df["ma7"] = df["pm25"].rolling(7).mean().round(1)       # 7-day moving average
    df = df.tail(days)
    return jsonify({"dates": [str(d) for d in df["date"]], "pm25": df["pm25"].tolist(),
                    "ma7": [None if pd.isna(x) else x for x in df["ma7"]],
                    "anomaly": [bool(x) for x in df["is_anomaly"]]})


@app.route("/api/predictions")
def api_predictions():
    rows = fetch_all("""SELECT date, predicted_pm25, actual_pm25 FROM predictions
                        WHERE model_name=%s ORDER BY date DESC LIMIT 60""", (best["name"],))[::-1]
    return jsonify({"dates": [str(r["date"]) for r in rows],
                    "predicted": [r["predicted_pm25"] for r in rows],
                    "actual": [r["actual_pm25"] for r in rows]})


@app.route("/api/metrics")
def api_metrics():
    with open(METRICS_JSON) as f:
        return jsonify(json.load(f))


if __name__ == "__main__":
    app.run(debug=True)
