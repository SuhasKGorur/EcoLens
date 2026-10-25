-- EcoLens database schema (run automatically by setup_db.py)
CREATE DATABASE IF NOT EXISTS ecolens;
USE ecolens;

-- Daily PM2.5 readings
CREATE TABLE IF NOT EXISTS air_quality (
    id       INT AUTO_INCREMENT PRIMARY KEY,
    date     DATE NOT NULL UNIQUE,
    location VARCHAR(50) NOT NULL DEFAULT 'Bengaluru',
    pm25     FLOAT NOT NULL
);

-- Model predictions (backtest = on old test data, live = real next-day forecast)
CREATE TABLE IF NOT EXISTS predictions (
    id             INT AUTO_INCREMENT PRIMARY KEY,
    date           DATE NOT NULL,                 -- the day being predicted
    location       VARCHAR(50) NOT NULL DEFAULT 'Bengaluru',
    model_name     VARCHAR(30) NOT NULL,
    predicted_pm25 FLOAT NOT NULL,
    actual_pm25    FLOAT NULL,                    -- filled when the real value is known
    source         ENUM('backtest','live') NOT NULL DEFAULT 'live',
    created_at     TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    UNIQUE KEY uq_pred (date, model_name)
);

-- Unusual readings flagged by Isolation Forest
CREATE TABLE IF NOT EXISTS anomalies (
    id       INT AUTO_INCREMENT PRIMARY KEY,
    date     DATE NOT NULL UNIQUE,
    location VARCHAR(50) NOT NULL DEFAULT 'Bengaluru',
    pm25     FLOAT NOT NULL,
    score    FLOAT NOT NULL,                      -- higher = more unusual
    status   VARCHAR(20) NOT NULL DEFAULT 'Review'
);

-- Model evaluation results
CREATE TABLE IF NOT EXISTS model_metrics (
    id          INT AUTO_INCREMENT PRIMARY KEY,
    model_name  VARCHAR(30) NOT NULL UNIQUE,
    mae         FLOAT, rmse FLOAT, r2 FLOAT,
    is_selected BOOLEAN DEFAULT FALSE,
    trained_at  TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);
