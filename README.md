# 🌿 EcoLens – ML-Based Environmental Intelligence and Pollution Forecasting System

Predicts next-day PM2.5, flags unusual readings, and shows everything on a Flask + MySQL dashboard.

## Folder structure
```
ecolens/
├── config.py          # paths + MySQL settings (edit your password here)
├── generate_data.py   # STEP 1: creates sample dataset (skip if you have a real CSV)
├── preprocess.py      # cleaning + feature engineering (shared by training and app)
├── train_model.py     # STEP 2: trains Linear Regression, Random Forest, Isolation Forest
├── setup_db.py        # STEP 3: creates MySQL tables and loads data (uses schema.sql)
├── app.py             # STEP 4: Flask web app
├── db.py              # MySQL helper functions
├── schema.sql         # table definitions
├── templates/         # HTML pages (Bootstrap)
├── static/            # CSS + JavaScript (Chart.js charts)
├── data/  models/     # generated CSVs, trained models, metrics.json
```

## How to run
1. Install Python 3.9+ and MySQL Server. Then:  `pip install -r requirements.txt`
2. Open `config.py` and set your MySQL password (or `set DB_PASSWORD=yourpass` on Windows / `export DB_PASSWORD=yourpass` on Linux).
3. Run, in order:
   ```
   python generate_data.py
   python train_model.py
   python setup_db.py
   python app.py
   ```
4. Open http://127.0.0.1:5000

## Using a real dataset
Save your CSV as `data/air_quality.csv` with columns `date, location, pm25` (e.g. from CPCB, OpenAQ,
or Kaggle "Air Quality Data in India"), skip `generate_data.py`, and run steps 2–4 again.

## How it works
| Stage | What happens |
|---|---|
| Cleaning | invalid values (≤0, >1000, blanks) removed, missing days filled by interpolation |
| Features | yesterday's value, lag 2/3/7, 7-day mean and std, weekday, month |
| Models | Linear Regression vs Random Forest, time-based 80/20 split, MAE/RMSE/R² compared; best saved |
| Anomalies | Isolation Forest on (value, change from yesterday, deviation from 7-day mean) |
| Web app | Flask serves pages + JSON APIs; MySQL stores readings, predictions, anomalies, metrics |

## Pages
Dashboard · History (date filter) · Anomalies · Model Performance · Add Reading
(adding a reading checks it for anomaly, fills the actual value of an earlier forecast, and refreshes tomorrow's forecast)

## Viva tips
- Why no random shuffle? Time series: train on past, test on future.
- MAE = average error; RMSE punishes large errors; R² = variance explained.
- Isolation Forest isolates outliers with fewer random splits; `contamination=0.03` means ~3% flagged.
- On the sample data Linear Regression and Random Forest score similarly; on real data with complex patterns Random Forest often wins. The app automatically picks the better one.
