import sys
import os

sys.path.append(os.path.join(os.path.dirname(__file__), ".."))

import pandas as pd
import numpy as np
import yaml
import vectorbt as vbt
from src.functions import (
    calculate_mti_signal,
    calculate_mti_trend,
    calculate_exit_price,
)


# DATA


def load_data(config):
    data = {}
    data_config = config["DATA_NAME_DAY"]
    start_date = config["BACKTESTING_DATES"]["START"]
    end_date = config["BACKTESTING_DATES"]["END"]

    for symbol, path in data_config.items():
        df = pd.read_csv(path, index_col="Time", parse_dates=True).sort_index()
        df = df.loc[start_date:end_date]
        if df.empty:
            raise ValueError(f"No data for {symbol}")
        data[symbol] = df

    return data


# INDICATORS


def calculate_indicators(data):
    indicators = {}

    for symbol, df in data.items():
        if len(df) < 90:
            continue

        mti_signal = calculate_mti_signal(df)
        mti_trend = calculate_mti_trend(mti_signal)

        exit_levels = pd.Series(index=df.index, dtype=float)
        for i in range(90, len(df)):
            current_color = mti_signal.iloc[i]
            window_df = df.iloc[i - 89 : i + 1]
            exit_price_series = calculate_exit_price(
                window_df, current_color, window=90
            )
            exit_levels.iloc[i] = exit_price_series.iloc[-1]

        indicators[symbol] = {
            "mti_signal": mti_signal,
            "mti_trend": mti_trend,
            "exit_level": exit_levels,
            "close": df["Close"],
        }

    return indicators


# SIGNALS


def generate_signals(indicators, days_under_exit=1):
    signals = {}

    for symbol, ind in indicators.items():
        mti_signal = ind["mti_signal"]
        exit_level = ind["exit_level"]
        close = ind["close"]

        entries = (mti_signal == "G") & (mti_signal.shift(1) != "G")

        below_exit = close < exit_level
        consecutive_below = pd.Series(0, index=close.index, dtype=int)
        count = 0
        for i in range(len(below_exit)):
            if below_exit.iloc[i] and not pd.isna(exit_level.iloc[i]):
                count += 1
            else:
                count = 0
            consecutive_below.iloc[i] = count

        exits = consecutive_below >= days_under_exit
        signals[symbol] = (entries, exits)

    return signals


# BACKTEST


def run_backtest(data, signals, config):
    symbols = list(signals.keys())
    if not symbols:
        raise RuntimeError("No signals generated")

    price = pd.DataFrame({s: data[s]["Close"] for s in symbols})
    entries = pd.DataFrame({s: signals[s][0] for s in symbols})
    exits = pd.DataFrame({s: signals[s][1] for s in symbols})

    portfolio = vbt.Portfolio.from_signals(
        close=price,
        entries=entries,
        exits=exits,
        size=config["SIZE"],
        size_type=config["SIZE_TYPE"],
        init_cash=config["INIT_BALANCE"],
        fees=config["FEES"],
        slippage=config["SLIPPAGE"],
        freq="D",
    )

    return portfolio


# OUTPUT


def save_results(portfolio, filename="results/backtesting_results.html"):
    os.makedirs(os.path.dirname(filename), exist_ok=True)
    portfolio.plot().write_html(filename)


def trade_log(portfolio, path="results/trades_log.csv"):
    trades = portfolio.trades.records_readable
    if not trades.empty:
        os.makedirs(os.path.dirname(path), exist_ok=True)
        trades.to_csv(path, index=False)
    return trades


# MAIN


def main():
    with open("config/backtesting_config.yaml", "r") as f:
        config = yaml.safe_load(f)

    data = load_data(config)
    indicators = calculate_indicators(data)
    days_under_exit = config.get("DAYS_UNDER_EXIT", 1)
    signals = generate_signals(indicators, days_under_exit)
    portfolio = run_backtest(data, signals, config)
    save_results(portfolio)
    trade_log(portfolio)

    return portfolio


if __name__ == "__main__":
    main()
