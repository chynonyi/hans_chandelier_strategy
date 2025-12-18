## 1. Strategy Overview

The strategy is based on a combination of the **MTI (Market Trend Indicator)** and the **Chandelier Exit**, and is designed for trading on **daily timeframes**.

---

### 1.1 MTI Signal (Market Trend Indicator)

MTI classifies market conditions into three color states:

* **G (Green)** — bullish / upward trend
* **Y (Yellow)** — neutral or transition phase
* **R (Red)** — bearish / downward trend

The indicator logic is based on:

* the relationship between **SMA(20)** and **SMA(50)**,
* the position of price relative to **SMA(20)**,
* the slope (direction) of **SMA(20)**.

---

### 1.2 Entry Logic

A **long entry** is triggered when:

* the MTI signal switches **to Green (G)**,
* and a long position is **not already open**.

This prevents repeated entries during an ongoing bullish regime.

---

### 1.3 Exit Logic

Exits are based on the **Chandelier Exit**, which dynamically adapts to market volatility using **ATR**.

The ATR multiplier depends on the current MTI color:

* **G → 3.0**
* **Y → 2.0**
* **R → 1.5**

An additional confirmation filter is applied:

* the position is closed only if the price remains **below the exit level** for **N consecutive days**
  (`days_under_exit`, configurable via the config file).

This reduces premature exits caused by short-term noise.

---

## 2. Backtesting Process

### 2.1 Data

Price data can be loaded from the **FMP service** by running `data/load_data_fmp.py`.

For **daily timeframes**, FMP is preferred over Insight Sentry, as it provides more accurate daily data.

For each ticker:

* data is sorted chronologically,
* a unified date range from the configuration file is applied.

---

### 2.2 Indicator Calculation

For each ticker:

1. The MTI signal (color) is calculated.
2. The MTI trend (transition direction) is calculated.
3. For each trading day (after sufficient historical data is available):

   * the Chandelier Exit is recalculated on a **rolling window**,
   * the corresponding exit level is stored.

All calculations are performed **without look-ahead bias**
(i.e., using only information available at that point in time).

---

### 2.3 Backtest Execution

The backtest is executed using **synchronous multi-asset trading**.

**Baseline backtest assumptions:**

* **No commissions** (fees = 0)
* **No slippage** (slippage = 0)
* **Fixed position size:** 100 USD per trade
* **Initial portfolio balance:** 10,000 USD

All of the above parameters — including position size, fee structure, slippage, and initial capital — are **fully configurable via the configuration file** and can be adjusted as needed.

---

## 3. Results

### 3.1 Output Format

A **separate PDF report is generated for each ticker**, containing:

* key portfolio metrics:

  * Total Return
  * Max Drawdown
  * Sharpe Ratio
  * Win Rate
  * Profit Factor
  * Number of Trades
  * Average Trade Duration

All metrics are aggregated **per individual asset**, not averaged across tickers.
