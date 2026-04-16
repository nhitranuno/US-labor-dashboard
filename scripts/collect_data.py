import requests
import pandas as pd
from datetime import datetime
import os

# ============================================================
# BLS Monthly Data Collection Script
# Fetches new data and appends it to the existing CSV.
# Run once manually to backfill, then monthly via GitHub Actions.
# ============================================================

API_KEY = "c3c57b9468ba465c8467e924e2de93ef"
BASE_URL = "https://api.bls.gov/publicAPI/v2/timeseries/data/"
DATA_PATH = "data/labor_data.csv"

SERIES = {
    "CES0000000001": "Total Nonfarm Employment",
    "LNS14000000":   "Unemployment Rate",
    "LNS11300000":   "Labor Force Participation Rate",
    "CES2000000001": "Construction Employment",
    "CES3000000001": "Manufacturing Employment",
    "CES6500000001": "Education & Health Employment",
    "CES0500000003": "Avg Hourly Earnings",
    "CES0500000002": "Avg Weekly Hours"
}

def fetch_bls_data(series_ids, start_year, end_year):
    """
    Call BLS API v2 for a list of series between start_year and end_year.
    Returns a tidy DataFrame with columns: date, series_id, series_name, value.
    Skips missing values (e.g. govt shutdown months marked as '-').
    """
    payload = {
        "seriesid": series_ids,
        "startyear": str(start_year),
        "endyear":   str(end_year),
        "registrationkey": API_KEY
    }
    response = requests.post(BASE_URL, json=payload)
    data = response.json()

    rows = []
    for series in data["Results"]["series"]:
        sid = series["seriesID"]
        name = SERIES.get(sid, sid)
        for obs in series["data"]:
            if obs["value"] == "-":
                continue
            month_num = obs["period"].replace("M", "")
            date = pd.Timestamp(f"{obs['year']}-{month_num}-01")
            rows.append({
                "date":        date,
                "series_id":   sid,
                "series_name": name,
                "value":       float(obs["value"])
            })

    df = pd.DataFrame(rows)
    df = df.sort_values(["series_id", "date"]).reset_index(drop=True)
    return df

def update_data():
    """
    Main function: loads existing CSV, fetches only NEW months from BLS,
    appends them, and saves back to CSV. Skips if already up to date.
    """
    current_year = datetime.now().year

    if os.path.exists(DATA_PATH):
        existing = pd.read_csv(DATA_PATH, parse_dates=["date"])
        last_date = existing["date"].max()
        print(f"Existing data found. Last date: {last_date.strftime('%Y-%m')}")
        fetch_from_year = last_date.year
    else:
        existing = pd.DataFrame()
        fetch_from_year = current_year - 2
        print("No existing data found. Fetching full history...")

    print(f"Fetching BLS data from {fetch_from_year} to {current_year}...")
    new_data = fetch_bls_data(
        series_ids=list(SERIES.keys()),
        start_year=fetch_from_year,
        end_year=current_year
    )

    if not existing.empty:
        combined = pd.concat([existing, new_data], ignore_index=True)
        combined = combined.drop_duplicates(subset=["date", "series_id"], keep="last")
    else:
        combined = new_data

    combined = combined.sort_values(["series_id", "date"]).reset_index(drop=True)
    combined.to_csv(DATA_PATH, index=False)

    print(f"Data updated! Total rows: {len(combined)}")
    print(f"Date range: {combined['date'].min().strftime('%Y-%m')} to {combined['date'].max().strftime('%Y-%m')}")

if __name__ == "__main__":
    os.makedirs("data", exist_ok=True)
    update_data()
