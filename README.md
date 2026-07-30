# Personal Investment Assistant

A Python-based research toolkit for producing evidence-aware stock and portfolio analysis reports.

The project combines verified market data with technical indicators, chart generation, scenario planning, and explicit risk controls. It is designed as a personal decision-support tool, not as an automated trading system.

## Key Features

- Collects OHLCV and market information with `pykrx` and `yfinance` fallbacks
- Calculates moving averages, RSI, MACD, Bollinger Bands, support, and resistance
- Generates analysis charts from actual market data
- Separates technical analysis, fundamentals, trading plans, and long-term theses
- Produces bullish, neutral, and bearish scenarios with invalidation conditions
- Includes position sizing, stop-loss, target, and portfolio-risk considerations

## Setup

```bash
python -m venv .venv
pip install -r requirements.txt
```

Review the scripts in `scripts/` before running an analysis. Generated reports and charts are intentionally excluded from version control where they may contain time-sensitive or personal information.

## Data and Safety

- Exact market figures should be reported only when verified data is available.
- API credentials must be supplied through environment variables.
- This repository does not guarantee returns or provide individualized financial advice.
- All investment decisions remain the user's responsibility.

