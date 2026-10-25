"""Central settings. Change the MySQL password here or set it as an environment variable."""
import os

BASE_DIR = os.path.dirname(os.path.abspath(__file__))

# ---- File locations ----
RAW_CSV      = os.path.join(BASE_DIR, "data", "air_quality.csv")        # raw dataset
CLEAN_CSV    = os.path.join(BASE_DIR, "data", "air_quality_clean.csv")  # after cleaning
BACKTEST_CSV = os.path.join(BASE_DIR, "data", "backtest.csv")           # predictions on test data
ANOMALY_CSV  = os.path.join(BASE_DIR, "data", "anomalies.csv")          # flagged readings
MODEL_PATH   = os.path.join(BASE_DIR, "models", "best_model.pkl")
ISO_PATH     = os.path.join(BASE_DIR, "models", "isolation_forest.pkl")
METRICS_JSON = os.path.join(BASE_DIR, "models", "metrics.json")

# ---- MySQL connection ----
DB_CONFIG = {
    "host":     os.getenv("DB_HOST", "localhost"),
    "user":     os.getenv("DB_USER", "root"),
    "password": os.getenv("DB_PASSWORD", "your_password"),   # <-- change this
    "database": os.getenv("DB_NAME", "ecolens"),
}

DEFAULT_LOCATION = "Bengaluru"
