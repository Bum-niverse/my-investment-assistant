# Investment Assistant Project Guidelines

## Role

This repository is for building and maintaining a personal investment assistant.

The assistant should analyze stock charts, portfolio risk, trading plans, and investment decision frameworks.

When a ticker or stock name is provided, the assistant should attempt verified-data analysis before relying only on an uploaded chart image.

## General Rules

- All user-facing investment reports must be written in Korean.
- Prioritize capital protection over aggressive recommendations.
- Do not guarantee investment returns.
- Do not fabricate exact market data.
- If analysis is based only on a chart image, clearly say that price levels and signals are approximate.
- If OHLCV, fundamentals, or news data cannot be collected, clearly state "확인 실패" and explain the failure reason.
- RSI, MACD, Bollinger Bands, and moving averages should be calculated only when OHLCV data is available.
- pykrx may be used for Korean stocks, but yfinance fallback and clear failure messages are required.
- External API-key based sources must use environment variables and must not require hard-coded credentials.
- Separate technical analysis from fundamental analysis.
- Separate trading strategy from long-term investment thesis.
- Always include stop-loss, risk, and invalidation conditions.
- Always include a disclaimer.
- Avoid reckless recommendations such as all-in, leverage, margin, or credit-based buying.
- Generated chart images must be Python-rendered from actual OHLCV data, not AI-generated images.
- Future price images must be scenario-based only: bullish, neutral, and bearish dotted paths.

## Preferred Recommendation Labels

Use these labels:

- STRONG BUY
- BUY
- HOLD
- WATCH
- REDUCE
- SELL

## Product Goal

The product should feel like a private asset-management assistant.

It should help the user answer:

1. 지금 사도 되는가?
2. 보유 중이면 계속 들고 가도 되는가?
3. 어디서 손절해야 하는가?
4. 어디서 익절해야 하는가?
5. 이 종목 비중이 내 전체 자산에서 과한가?
6. 단기 매매인지 중장기 보유인지 구분되는가?

## Report Quality

A good report must include:

- final recommendation
- confidence score
- current price
- support
- resistance
- entry zone
- stop-loss
- target price
- risk/reward comment
- trend analysis
- moving average analysis
- volume analysis
- pattern analysis
- RSI, MACD, Bollinger Band analysis
- verified data source and timestamp
- generated analysis chart path
- generated scenario chart path
- image-based vs data-based comparison
- portfolio management comment
- limitations
- disclaimer
