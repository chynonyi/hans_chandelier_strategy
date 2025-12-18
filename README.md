# Strategy Overview, Backtest Interpretation and MTI + Chandelier Exit (1 / 2 / 3 Days Under Exit)

**MTI + Chandelier Exit (Daily Timeframe)**

---

## 1. Strategy Overview

This strategy combines a **Market Trend Indicator (MTI)** for regime detection with a **Chandelier Exit–based trailing stop**.
It is designed for **daily data** and operates as a **trend-following system with volatility-adjusted exits**.

The strategy should be understood primarily as an **entry + exit framework**, not as a standalone alpha generator.

---

## 1.1 Market Trend Indicator (MTI)

The MTI classifies market conditions into three discrete states:

* **G (Green)** — bullish / upward trend
* **Y (Yellow)** — neutral or transition phase
* **R (Red)** — bearish / downward trend

The MTI logic is derived from:

* the relationship between **SMA(20)** and **SMA(50)**,
* the position of price relative to **SMA(20)**,
* the slope (direction) of **SMA(20)**.

The MTI state is recalculated daily and used both for **entry timing** and **exit sensitivity**.

---

## 1.2 Entry Logic

A **long entry** is triggered when:

* the MTI signal switches **to Green (G)**,
* and no long position is currently open.

This rule prevents repeated entries during the same bullish regime and ensures that each trend is traded only once.

---

## 1.3 Exit Logic (Chandelier Exit)

Exits are based on the **Chandelier Exit**, which adapts dynamically to volatility via **ATR**.

The ATR multiplier is **state-dependent**:

| MTI State  | ATR Multiplier |
| ---------- | -------------- |
| Green (G)  | 3.0            |
| Yellow (Y) | 2.0            |
| Red (R)    | 1.5            |

An additional confirmation filter is applied:

* the position is closed only if the **closing price remains below the Chandelier Exit level for N consecutive days**
* `days_under_exit` is configurable via the config file

This filter reduces premature exits caused by short-term noise.

---

## 2. Backtesting Process

### 2.1 Data

* Price data is loaded via the **Financial Modeling Prep (FMP)** service using `data/load_data_fmp.py`.
* For **daily timeframes**, FMP is preferred over Insight Sentry due to higher data consistency.
* For each ticker:

  * data is sorted chronologically,
  * a unified date range (from the config file) is applied.

---

### 2.2 Indicator Calculation

For each asset:

1. MTI state (color) is computed.
2. MTI trend transitions are detected.
3. For each trading day (after sufficient history is available):

   * the Chandelier Exit is recalculated on a **rolling window**,
   * the corresponding exit level is stored.

All calculations are performed **without look-ahead bias** — only information available at that time is used.

---

### 2.3 Backtest Execution

The backtest is run using **synchronous multi-asset logic**.

**Baseline assumptions:**

* **Commissions:** 0
* **Slippage:** 0
* **Position size:** fixed 100 USD per trade
* **Initial capital:** 10,000 USD

All parameters (fees, slippage, sizing, capital, exit confirmation days) are **fully configurable**.

---

## 3. Backtest Horizons and Results

Two distinct evaluation horizons are presented.

---

## 3.1 Long-Term Results (11 Years: 2015–2025)

The primary evaluation covers **~11 years of data**, including multiple market regimes.

### Observations

* Returns are generally **below buy & hold**.
* Maximum drawdowns range from **~25% to ~45%**.
* Drawdown durations often exceed **2–3 years**.
* Sharpe Ratios typically fall between **0.3 and 0.9**.
* Calmar Ratios are mostly **below 0.5**.

### Interpretation

* The strategy does **not generate persistent alpha** across full cycles.
* Performance is largely driven by:

  * market beta,
  * convex payoff from a small number of strong trends.
* Risk-adjusted returns are **not sufficient** to justify the strategy as a standalone investment.
* The strategy does **not consistently reduce drawdowns** versus holding the underlying asset.

---

## 3.2 Short-Term Results (2 Years: 2024–2025)

A secondary analysis focuses on the **last ~2 years**, using the **same strategy logic** but a more aggressive exit configuration:

* **Exit after 1 consecutive close below the Chandelier Exit level**

### Observed Characteristics

* Sharpe Ratios: **~1.5–2.2**
* Calmar Ratios: **~2.5–6.7**
* Maximum drawdowns reduced to **~11–26%**
* In some cases, returns are comparable to or exceed benchmarks

---

## 4. Why Recent Results Are Significantly Better

The improved performance in 2024–2025 should be interpreted carefully.

### Key drivers

1. **Market regime**

   * Strong, persistent trends (AI, semiconductors, large-cap growth).
   * Highly favorable conditions for trailing-stop strategies.

2. **Higher exit sensitivity**

   * Faster exits reduce time spent in drawdowns.
   * Upside participation increases.
   * Market exposure (beta) becomes higher.
   * Regime dependency increases.

3. **Small sample size**

   * Only **5–8 trades per ticker**.
   * One or two trades dominate total PnL.
   * Risk-adjusted metrics are **statistically unstable**.

---

## 5. Correct Interpretation

### What the results show

* The MTI + Chandelier Exit framework performs **very well in strong trending environments**.
* As an **exit overlay**, it can materially improve risk-adjusted performance under favorable regimes.

### What the results do not show

* Long-term robustness across market regimes.
* Stable alpha independent of market direction.
* Parameter stability across cycles.

---

## 6. 11-Year vs 2-Year Comparison

| Aspect                 | 11 Years (2015–2025) | 2 Years (2024–2025) |
| ---------------------- | -------------------- | ------------------- |
| Regime coverage        | Full market cycle    | Trend-dominated     |
| Statistical robustness | Higher               | Low                 |
| Sharpe Ratio           | 0.3–0.9              | 1.5–2.2             |
| Drawdowns              | Long and deep        | Shorter and smaller |
| Overfitting risk       | Low                  | High                |
| Investment reliability | Moderate / Low       | Preliminary         |

---

## Output and Reporting

For each ticker, a **separate PDF report** is generated, including:

* Total Return
* Maximum Drawdown
* Sharpe Ratio
* Win Rate
* Profit Factor
* Number of Trades
* Average Trade Duration

All metrics are reported **per individual asset**, not averaged across tickers.


Ниже — **точный, профессиональный перевод на английский**, без упрощений и «маркетинга», в формате, готовом для вставки в README.

---

## Exit Confirmation Sensitivity Analysis

**MTI + Chandelier Exit (1 / 2 / 3 Days Under Exit)**

The analysis is conducted **in-sample**, with **no changes to entry logic, position sizing, or parameters**, except for `days_under_exit`.

---

## 1. Long-Term Horizon (2015–2025)

### 1.1 GOOG

| Exit Delay | Total Return | Max DD | Sharpe | Calmar | Trades |
| ---------- | ------------ | ------ | ------ | ------ | ------ |
| 1 day      | 170%         | 22.4%  | 0.92   | 0.63   | 56     |
| 2 days     | 173%         | 28.3%  | 0.90   | 0.50   | 46     |
| 3 days     | 190%         | 30.0%  | 0.95   | 0.50   | 42     |

**Interpretation:**

Increasing `days_under_exit`:

* reduces turnover,
* increases trend holding duration,
* increases both drawdown magnitude and duration.

The Sharpe Ratio changes only marginally, implying that **risk increases faster than reward**.

The 3-day exit delivers the highest nominal return but exhibits a **worse tail-risk profile**.

---

### 1.2 LLY

| Exit Delay | Total Return | Max DD | Sharpe | Calmar | Trades |
| ---------- | ------------ | ------ | ------ | ------ | ------ |
| 1 day      | 248%         | 23.2%  | 0.95   | 0.77   | 54     |
| 2 days     | 266%         | 25.8%  | 0.94   | 0.73   | 43     |
| 3 days     | 187%         | 29.1%  | 0.77   | 0.52   | 41     |

**Interpretation:**

The 3-day exit clearly deteriorates performance:

* lower Sharpe,
* worse Calmar,
* higher drawdowns.

The 2-day exit maximizes nominal returns but does **not** improve risk-adjusted metrics.

The 1-day exit delivers the **most stable performance profile**.

---

### 1.3 STX

| Exit Delay | Total Return | Max DD | Sharpe | Calmar | Trades |
| ---------- | ------------ | ------ | ------ | ------ | ------ |
| 1 day      | 109%         | 21.3%  | 0.63   | 0.48   | 58     |
| 2 days     | 133%         | 19.4%  | 0.70   | 0.61   | 45     |
| 3 days     | 121%         | 25.7%  | 0.66   | 0.43   | 37     |

**Interpretation:**

STX benefits from a **moderate exit delay**.

The 2-day exit delivers:

* the highest Sharpe,
* the lowest drawdown,
* the best Calmar ratio.

The 3-day exit again worsens tail-risk characteristics.

---

### 1.4 Summary for 2015–2025

**General pattern:**

* `days_under_exit = 1`

  * lower drawdowns,
  * higher turnover,
  * more stable risk-adjusted metrics.

* `days_under_exit = 3`

  * higher nominal returns in strong trends,
  * worse drawdowns and recovery,
  * stronger regime dependency.

The optimal setting is **asset-dependent**, but:

* **1–2 days dominate** across assets,
* 3 days are **rarely justified** over long horizons.

---

## 2. Short-Term Horizon (2024–2025)

A key characteristic of this period is a **trend-dominated regime combined with a small number of trades**.

---

### 2.1 GOOG

| Exit Delay | Return | Max DD | Sharpe | Calmar | Trades |
| ---------- | ------ | ------ | ------ | ------ | ------ |
| 1 day      | 91%    | 11.9%  | 1.99   | 5.18   | 8      |
| 2 days     | 104%   | 10.1%  | 2.11   | 6.90   | 6      |
| 3 days     | 115%   | 11.3%  | 2.23   | 6.77   | 5      |

**Interpretation:**

All variants appear **exceptionally strong**.

The improvement in metrics is driven by:

* strong, persistent trends,
* low pullback volatility,
* dominance of one or two trades in total PnL.

Differences between the 2-day and 3-day exits are **not statistically significant**.

---

### 2.2 LLY

| Exit Delay | Return | Max DD | Sharpe | Calmar |
| ---------- | ------ | ------ | ------ | ------ |
| 1 day      | 19.8%  | 21.1%  | 0.77   | 0.68   |
| 2 days     | 20.1%  | 25.8%  | 0.72   | 0.56   |
| 3 days     | 13.7%  | 29.1%  | 0.53   | 0.34   |

**Interpretation:**

Even in a bullish regime, LLY:

* does not benefit from slower exits.

The 3-day exit is **strictly dominated**.

---

### 2.3 STX

| Exit Delay | Return | Max DD | Sharpe | Calmar |
| ---------- | ------ | ------ | ------ | ------ |
| 1 day      | 98%    | 21.6%  | 1.74   | 3.05   |
| 2 days     | 104%   | 19.9%  | 1.78   | 3.49   |
| 3 days     | 98%    | 26.5%  | 1.68   | 2.49   |

**Interpretation:**

The long-term pattern repeats:

* the **2-day exit is optimal**.

The 3-day exit increases tail risk without sufficient compensation.

---

## 3. Key Conclusions (Across Horizons)

### 3.1 Structural Effects of `days_under_exit`

Increasing the number of days under the exit level:

* reduces the number of trades,
* increases average holding duration,
* amplifies beta exposure.

Risk-adjusted metrics **do not improve monotonically**.

---

### 3.2 Regime Dependency

During **trend-dominated periods (2024–2025)**:

* all variants appear strong,
* differences are unstable,
* the risk of over-interpretation is high.

Across a **full market cycle (2015–2025)**:

* differences become economically meaningful,
* **tail risk becomes the dominant factor**.
