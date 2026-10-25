"""
Data cleaning + feature engineering. Used by both train_model.py and app.py,
so training and live prediction always build features in exactly the same way.
"""
import numpy as np
import pandas as pd

# Columns the forecasting model learns from
FEATURES = ["lag_1", "lag_2", "lag_3", "lag_7",
            "roll_mean_7", "roll_std_7", "day_of_week", "month"]

# Columns Isolation Forest uses to judge "is this reading unusual?"
ANOMALY_FEATURES = ["pm25", "change_1d", "dev_7d"]


def load_and_clean(path):
    """Read the raw CSV and fix missing / invalid values."""
    df = pd.read_csv(path)
    rows_raw = len(df)

    df["date"] = pd.to_datetime(df["date"], errors="coerce")      # bad dates -> NaT
    df["pm25"] = pd.to_numeric(df["pm25"], errors="coerce")       # text -> NaN
    df = df.dropna(subset=["date"]).drop_duplicates("date").sort_values("date")

    # PM2.5 can't be zero/negative, and > 1000 is physically unrealistic
    invalid = (df["pm25"] <= 0) | (df["pm25"] > 1000)
    df.loc[invalid, "pm25"] = np.nan

    location = df["location"].mode()[0] if "location" in df.columns else "Bengaluru"

    # Make sure every calendar day exists (missing days become NaN rows)
    df = df.set_index("date").asfreq("D")
    n_missing = int(df["pm25"].isna().sum())

    # Fill gaps by drawing a straight line between neighbouring valid readings
    df["pm25"] = df["pm25"].interpolate(limit_direction="both").round(1)
    df["location"] = location
    df = df.reset_index()[["date", "location", "pm25"]]

    print(f"[clean] rows in file: {rows_raw} | invalid/missing fixed: {n_missing} | final rows: {len(df)}")
    return df


def make_features(df):
    """
    Build features from past values. Row t's features describe day t,
    and the target 'next_pm25' is the PM2.5 of day t+1 (what we forecast).
    """
    d = df.copy().sort_values("date").reset_index(drop=True)
    p = d["pm25"]
    d["lag_1"] = p.shift(1)            # yesterday
    d["lag_2"] = p.shift(2)
    d["lag_3"] = p.shift(3)
    d["lag_7"] = p.shift(7)            # same weekday last week
    d["roll_mean_7"] = p.rolling(7).mean()   # 7-day average (trend)
    d["roll_std_7"] = p.rolling(7).std()     # 7-day variability
    d["day_of_week"] = d["date"].dt.dayofweek
    d["month"] = d["date"].dt.month
    d["next_pm25"] = p.shift(-1)       # TARGET: tomorrow's value
    return d


def anomaly_features(df):
    """Features for Isolation Forest: the value, its jump from yesterday,
    and how far it is from the previous 7-day average."""
    d = df.copy().reset_index(drop=True)
    p = d["pm25"]
    d["change_1d"] = p - p.shift(1)
    d["dev_7d"] = p - p.shift(1).rolling(7).mean()
    return d
