"""Tiny helper functions so the rest of the code stays short."""
import mysql.connector
from config import DB_CONFIG


def get_connection():
    return mysql.connector.connect(**DB_CONFIG)


def fetch_all(sql, params=None):
    """Run a SELECT and return a list of dictionaries."""
    conn = get_connection()
    cur = conn.cursor(dictionary=True)
    cur.execute(sql, params or ())
    rows = cur.fetchall()
    cur.close(); conn.close()
    return rows


def execute(sql, params=None):
    """Run INSERT / UPDATE / DELETE and save the change."""
    conn = get_connection()
    cur = conn.cursor()
    cur.execute(sql, params or ())
    conn.commit()
    cur.close(); conn.close()
