# Data Source Policy

## Core Principles

- 데이터가 확인되지 않으면 수치를 지어내지 않는다.
- OHLCV 데이터가 있을 때만 RSI, MACD, Bollinger Band를 계산한다.
- 재무제표, 실적, 뉴스 확인에 실패하면 "확인 실패"와 실패 이유를 표시한다.
- 이미지 기반 분석과 실제 데이터 기반 분석은 별도 섹션으로 분리한다.
- 모든 데이터에는 출처와 기준일 또는 조회 시각을 표시한다.
- 인터넷 접근이 막힌 환경에서는 예외를 잡고 가능한 분석만 제공한다.

## Preferred Sources

1. yfinance
   - 해외 주식 및 일부 한국 주식의 OHLCV, 기본 지표, 뉴스 확인에 사용한다.
   - 한국 주식은 `005930.KS`, `000660.KS` 같은 형식을 우선 사용한다.
2. pykrx
   - 설치되어 있을 때 한국 주식 OHLCV 보조 데이터 소스로 사용한다.
   - 설치되어 있지 않으면 경고만 남기고 계속 진행한다.
3. Environment-variable API sources
   - 외부 API 키가 필요한 기능은 환경변수 기반으로만 사용한다.
   - 예: `DART_API_KEY`, `API_K_DART`, `NAVER_CLIENT_ID`, `NAVER_CLIENT_SECRET`

## Failure Reporting

실패 메시지는 사용자가 판단할 수 있게 구체적으로 쓴다.

예:

- `yfinance OHLCV 확인 실패: 네트워크 연결 오류`
- `pykrx 확인 실패: pykrx가 설치되어 있지 않음`
- `뉴스 확인 실패: 사용 가능한 뉴스 데이터 없음`
- `재무제표 확인 실패: yfinance에서 재무 데이터가 비어 있음`

## Report Rule

데이터 확인에 실패해도 리포트를 중단하지 않는다. 대신 다음 순서로 출력한다.

1. 확인된 데이터 기반 분석
2. 실패한 데이터 소스와 이유
3. 이미지 기반 분석
4. 최종 해석과 리스크 관리
5. 투자 참고용 disclaimer
