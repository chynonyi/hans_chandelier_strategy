import pandas as pd
import numpy as np
from typing import Tuple


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
