import requests
import pandas as pd
import time
import os
from dotenv import load_dotenv
from tqdm import tqdm
from datetime import datetime
import yaml


# LOAD CONFIG

with open("config/data_config.yaml", "r") as fp:
    cfg = yaml.safe_load(fp)

load_dotenv()
FMP_API_KEY = os.getenv("FMP_API_KEY")

tokens = [t.strip() for t in cfg["TOKENS"].split(",")]

start_year = cfg["Time interval"]["Start_year"]
start_month = cfg["Time interval"]["Start_month"]
end_year = cfg["Time interval"]["End_year"]
end_month = cfg["Time interval"]["End_month"]

FREQ = cfg["Frequency"]
data_folder = "data"
os.makedirs(data_folder, exist_ok=True)

# Month it
months = []
year = start_year
month = start_month
while (year < end_year) or (year == end_year and month <= end_month):
    months.append(f"{year}-{month:02d}")
    month += 1
    if month > 12:
        month = 1
        year += 1

print("Months to fetch:", months)


# LOAD DATA FOR ALL TICKERS

for token in tokens:
    exchange, symbol = token.split(":")
    print(f"\nFetching data for {symbol} ({exchange})...")
    data_df = None

    for month in tqdm(months):
        start_date = f"{month}-01"
        end_date = (pd.to_datetime(start_date) + pd.offsets.MonthEnd(0)).strftime(
            "%Y-%m-%d"
        )

        url = f"https://financialmodelingprep.com/api/v3/historical-price-full/{symbol}?from={start_date}&to={end_date}&apikey={FMP_API_KEY}"

        success = False
        while not success:
            response = requests.get(url)
            if response.status_code == 200:
                data = response.json()
                if "historical" in data:
                    df_month = pd.DataFrame(data["historical"])
                    if data_df is None:
                        data_df = df_month
                    else:
                        data_df = pd.concat([data_df, df_month], ignore_index=True)
                success = True
                time.sleep(1)
            else:
                print(
                    f"Request failed for {month} ({response.status_code}), retrying in 60s..."
                )
                time.sleep(60)

    # SAVE TO CSV

    if data_df is not None and not data_df.empty:
        data_df["date"] = pd.to_datetime(data_df["date"])
        data_df = data_df.rename(
            columns={
                "date": "Time",
                "open": "Open",
                "high": "High",
                "low": "Low",
                "close": "Close",
                "volume": "Volume",
            }
        )
        data_df = data_df.set_index("Time")
        csv_path = os.path.join(data_folder, f"{symbol}_{FREQ}.csv")
        data_df.to_csv(csv_path)
        print(f"Saved {symbol} data to {csv_path}")
    else:
        print(f"No data fetched for {symbol}")


tickers = {
    "GOOG": "data/GOOG_DAY.csv",
    "AVGO": "data/AVGO_DAY.csv",
    "LLY": "data/LLY_DAY.csv",
    "GS": "data/GS_DAY.csv",
    "AXP": "data/AXP_DAY.csv",
    "MRK": "data/MRK_DAY.csv",
    "ISRG": "data/ISRG_DAY.csv",
    "MU": "data/MU_DAY.csv",
    "STX": "data/STX_DAY.csv",
}

for symbol, path in tickers.items():
    df = pd.read_csv(path)
    df["Time"] = pd.to_datetime(df["Time"])
    df = df.sort_values("Time")
    df.to_csv(path, index=False)
