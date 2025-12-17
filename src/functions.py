import pandas as pd
import numpy as np
import vectorbt as vbt
from typing import Tuple
import matplotlib.pyplot as plt
from matplotlib.backends.backend_pdf import PdfPages
import os

# MTI SIGNAL


def calculate_mti_signal(df: pd.DataFrame) -> pd.Series:
    price = df["Close"]

    sma20 = price.rolling(20).mean()
    sma50 = price.rolling(50).mean()

    mask1 = sma20 > sma50
    mask2 = price > sma20
    mask3 = sma20 > sma20.shift(7)
    mask4 = sma20 < sma50

    red_mask = mask4
    green_mask = mask1 & mask2 & mask3

    signals = pd.Series("Y", index=df.index)
    signals.loc[red_mask] = "R"
    signals.loc[green_mask] = "G"

    return signals


# MTI TREND


def calculate_mti_trend(signals: pd.Series) -> pd.Series:
    trend_map = {
        ("R", "Y"): "up",
        ("R", "G"): "up-b",
        ("R", "R"): "left",
        ("G", "Y"): "down",
        ("G", "G"): "s-right",
        ("G", "R"): "down-b",
        ("Y", "G"): "up",
        ("Y", "R"): "down",
    }

    trends = []

    for i in range(len(signals)):
        if i == 0:
            trends.append("unknown")
            continue

        prev = signals.iloc[i - 1]
        curr = signals.iloc[i]

        if (prev, curr) in trend_map:
            trend = trend_map[(prev, curr)]

        elif prev == "Y" and curr == "Y":
            if i >= 2:
                third = signals.iloc[i - 2]
                if third == "R":
                    trend = "s-right"
                elif third == "G":
                    trend = "left"
                else:
                    trend = "right"
            else:
                trend = "right"

        else:
            trend = "unknown"

        trends.append(trend)

    return pd.Series(trends, index=signals.index)


# CHANDELIER EXIT


def chandelier_exit(
    df: pd.DataFrame,
    length: int = 22,
    mult: float = 3.0,
    use_close: bool = True,
) -> pd.DataFrame:

    result = df.copy()

    high = df["High"]
    low = df["Low"]
    close = df["Close"]

    tr = pd.concat(
        [
            high - low,
            (high - close.shift(1)).abs(),
            (low - close.shift(1)).abs(),
        ],
        axis=1,
    ).max(axis=1)

    atr = tr.ewm(alpha=1 / length, adjust=False).mean()
    atr_mult = mult * atr

    highest = close.rolling(length).max() if use_close else high.rolling(length).max()
    long_stop = highest - atr_mult

    long_stop_prev = long_stop.shift(1)
    close_prev = close.shift(1)

    for i in range(1, len(long_stop)):
        if close_prev.iloc[i] > long_stop_prev.iloc[i]:
            long_stop.iloc[i] = max(long_stop.iloc[i], long_stop_prev.iloc[i])

    lowest = close.rolling(length).min() if use_close else low.rolling(length).min()
    short_stop = lowest + atr_mult
    short_stop_prev = short_stop.shift(1)

    for i in range(1, len(short_stop)):
        if close_prev.iloc[i] < short_stop_prev.iloc[i]:
            short_stop.iloc[i] = min(short_stop.iloc[i], short_stop_prev.iloc[i])

    direction = pd.Series(1, index=df.index, dtype=int)

    for i in range(1, len(direction)):
        if close.iloc[i] > short_stop_prev.iloc[i]:
            direction.iloc[i] = 1
        elif close.iloc[i] < long_stop_prev.iloc[i]:
            direction.iloc[i] = -1
        else:
            direction.iloc[i] = direction.iloc[i - 1]

    result["long_stop"] = long_stop
    result["short_stop"] = short_stop
    result["direction"] = direction
    result["atr"] = atr

    return result


# EXIT PRICE


def calculate_exit_price(
    df: pd.DataFrame,
    mti_color: str,
    window: int = 90,
) -> pd.Series:

    color = mti_color[0]

    mult = {"G": 3, "Y": 2, "R": 1.5}.get(color, 3)

    result = chandelier_exit(df, length=22, mult=mult)

    return result["long_stop"]


# DATA


def load_data(config):
    data = {}
    data_config = config["DATA_NAME_DAY"]
    start_date = config["BACKTESTING_DATES"]["START"]
    end_date = config["BACKTESTING_DATES"]["END"]

    for symbol, path in data_config.items():
        df = pd.read_csv(path)
        df["Time"] = pd.to_datetime(df["Time"])
        df = df.set_index("Time")
        df = df.sort_index()

        df = df.loc[start_date:end_date]
        df = df.loc[start_date:end_date]
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


def generate_signals(indicators, days_under_exit):
    signals = {}

    for symbol, ind in indicators.items():
        mti_signal = ind["mti_signal"]
        exit_level = ind["exit_level"]
        close = ind["close"]

        entries = (mti_signal == "G") & (mti_signal.shift(1) != "G")

        under_exit = close < exit_level
        repeating_under = pd.Series(0, index=close.index, dtype=int)
        number = 0
        for i in range(len(under_exit)):
            if under_exit.iloc[i] and not pd.isna(exit_level.iloc[i]):
                number += 1
            else:
                number = 0
            repeating_under.iloc[i] = number

        exits = repeating_under >= days_under_exit
        signals[symbol] = (entries, exits)

    return signals


# BACKTEST


def run_backtest(data, signals, config):
    symbols = list(signals.keys())

    price_dict = {}
    for ticker in symbols:
        price_dict[ticker] = data[ticker]["Close"]
    price = pd.DataFrame(price_dict)

    entries_dict = {}
    for ticker in symbols:
        entries_dict[ticker] = signals[ticker][0]
    entries = pd.DataFrame(entries_dict)

    exits_dict = {}
    for ticker in symbols:
        exits_dict[ticker] = signals[ticker][1]
    exits = pd.DataFrame(exits_dict)

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


# def save_backtesting_results(pf, output_dir="results"):

#     os.makedirs(output_dir, exist_ok=True)

#     for symbol in pf.symbols:
#         stats = pf[symbol].stats()
#         stats_df = stats.to_frame(name="Value")

#         pdf_path = os.path.join(output_dir, f"{symbol}_bcts_res.pdf")

#         with PdfPages(pdf_path) as pdf:
#             fig_height = max(6, len(stats_df) * 0.35)
#             fig, ax = plt.subplots(figsize=(8.5, fig_height))
#             ax.axis("off")

#             table = ax.table(
#                 cellText=stats_df.values,
#                 rowLabels=stats_df.index,
#                 colLabels=stats_df.columns,
#                 cellLoc="center",
#                 loc="center",
#             )

#             table.auto_set_font_size(False)
#             table.set_fontsize(9)
#             table.scale(1, 1.3)

#             pdf.savefig(fig, bbox_inches="tight")
#             plt.close(fig)

#         print(f"PDF saved for {symbol} in {pdf_path}")


def trade_log(days_under_exit, portfolio, output_dir="results"):

    path = os.path.join(output_dir, f"trades_log_{days_under_exit}.csv")
    trades = portfolio.trades.records_readable
    if not trades.empty:
        os.makedirs(os.path.dirname(path), exist_ok=True)
        trades.to_csv(path, index=False)
    return trades


def save_backtesting_results(days_under_exit, pf, output_dir="results"):
    os.makedirs(output_dir, exist_ok=True)

    try:
        if hasattr(pf.wrapper, "columns"):
            symbols = pf.wrapper.columns.tolist()
        elif hasattr(pf, "close"):
            symbols = pf.close.columns.tolist()
        else:
            symbols = list(pf.wrapper.columns)

    except Exception as e:
        print(f"Error getting symbols: {e}")
        print("Available attributes:", dir(pf))
        print("Wrapper columns:", pf.wrapper.columns)
        return

    print(f"\nGenerating PDFs for {len(symbols)} symbols: {symbols}")

    for symbol in symbols:
        try:
            print(f"\nProcessing {symbol}...")

            symbol_pf = pf[symbol]
            stats = symbol_pf.stats()
            stats_df = stats.to_frame(name="Value")

            pdf_path = os.path.join(
                output_dir, f"{symbol}_report_{days_under_exit}.pdf"
            )

            with PdfPages(pdf_path) as pdf:
                fig_height = max(6, len(stats_df) * 0.35)
                fig, ax = plt.subplots(figsize=(8.5, fig_height))
                ax.axis("off")

                table = ax.table(
                    cellText=stats_df.values,
                    rowLabels=stats_df.index,
                    colLabels=stats_df.columns,
                    cellLoc="center",
                    loc="center",
                )

                table.auto_set_font_size(False)
                table.set_fontsize(9)
                table.scale(1, 1.3)

                pdf.savefig(fig, bbox_inches="tight")
                plt.close(fig)

            print(f"Saved: {pdf_path}")

        except Exception as e:
            print(f"Error for {symbol}: {e}")
            import traceback

            traceback.print_exc()

    print(f"All PDFs saved to: {os.path.abspath(output_dir)}/")
