"""
STEP 1 - Create a realistic sample dataset (data/air_quality.csv).

Why? It lets the project run without internet. If you have a real dataset
(CPCB / OpenAQ / Kaggle 'Air Quality Data in India'), just save it as
data/air_quality.csv with columns: date, location, pm25 and skip this step.

The data deliberately contains dirty values (blanks, negatives) so that the
cleaning step in preprocess.py has something to fix.
"""
import numpy as np
import pandas as pd
from config import RAW_CSV, DEFAULT_LOCATION

rng = np.random.default_rng(42)                       # fixed seed = same data every run
dates = pd.date_range("2023-01-01", "2026-01-13", freq="D")
n = len(dates)

# 1) Seasonal pattern: pollution is higher in winter (Dec-Feb), lower in monsoon (Jul-Aug)
day_of_year = dates.dayofyear.values
seasonal = 45 + 25 * np.cos(2 * np.pi * (day_of_year - 15) / 365)

# 2) Weekly pattern: slightly more traffic on weekdays
weekly = np.where(dates.dayofweek < 5, 3, -3)

# 3) Day-to-day memory (AR(1) noise): today's pollution depends on yesterday's
noise = np.zeros(n)
for i in range(1, n):
    noise[i] = 0.7 * noise[i - 1] + rng.normal(0, 6)

pm25 = seasonal + weekly + noise

# 4) A few sudden spikes (e.g. festival fireworks / burning) -> these are the anomalies
spike_days = rng.choice(np.arange(10, n - 10), size=14, replace=False)
pm25[spike_days] += rng.uniform(70, 140, size=len(spike_days))

pm25 = np.clip(pm25, 5, None).round(1)
df = pd.DataFrame({"date": dates.strftime("%Y-%m-%d"), "location": DEFAULT_LOCATION, "pm25": pm25})

# 5) Make the data "dirty" on purpose
df.loc[rng.choice(n, 25, replace=False), "pm25"] = np.nan   # missing readings
df.loc[rng.choice(n, 4, replace=False), "pm25"] = -999      # sensor error codes

df.to_csv(RAW_CSV, index=False)
print(f"Saved {len(df)} rows to {RAW_CSV}")
