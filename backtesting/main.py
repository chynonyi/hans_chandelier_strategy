import sys
import os

sys.path.append(os.path.join(os.path.dirname(__file__), ".."))

import yaml
from src.functions import (
    load_data,
    calculate_indicators,
    generate_signals,
    run_backtest,
    save_backtesting_results,
    trade_log,
)


if __name__ == "__main__":
    with open("config/backtesting_config.yaml", "r") as f:
        config = yaml.safe_load(f)

    data = load_data(config)
    indicators = calculate_indicators(data)
    days_under_exit = config.get("DAYS_UNDER_EXIT")
    signals = generate_signals(indicators, days_under_exit)
    portfolio = run_backtest(data, signals, config)
    trade_log(days_under_exit, portfolio)
    save_backtesting_results(days_under_exit, portfolio)
