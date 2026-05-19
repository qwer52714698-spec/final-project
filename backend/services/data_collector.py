import yfinance as yf
import pandas as pd
from pykrx import stock as krx
from datetime import datetime, timedelta
from database import SessionLocal
import models
import crud

class MarketDataCollector:
    def __init__(self):
        # ✅ 공통 거시 데이터 캐시 (금리/환율/유가/S&P500)
        # 한 번만 받아두고 모든 종목이 재사용
        self._macro_cache = None
        self._macro_cache_date = None

    def _get_macro_data(self, start, end):
        # 오늘 이미 받아둔 데이터가 있으면 재사용
        today = datetime.now().date()
        if self._macro_cache is not None and self._macro_cache_date == today:
            return self._macro_cache

        print("📡 공통 거시 데이터 수집 중... (금리/환율/유가/S&P500)")

        def get_clean_data(t, s, e):
            df = yf.download(t, start=s, end=e, progress=False)
            if isinstance(df.columns, pd.MultiIndex):
                df.columns = df.columns.droplevel(1)
            return df

        try:
            tnx    = get_clean_data("^TNX",  start, end)[['Close']].rename(columns={'Close': 'interest_rate'})
            usdkrw = get_clean_data("KRW=X", start, end)[['Close']].rename(columns={'Close': 'exchange_rate'})
            wti    = get_clean_data("CL=F",  start, end)[['Close']].rename(columns={'Close': 'oil_price'})
            sp500  = get_clean_data("^GSPC", start, end)[['Close']].rename(columns={'Close': 'sp500'})
            macro  = pd.concat([tnx, usdkrw, wti, sp500], axis=1).ffill()
        except Exception as e:
            print(f"⚠️ 거시 데이터 수집 실패, 빈 데이터로 대체: {e}")
            macro = pd.DataFrame(columns=['interest_rate', 'exchange_rate', 'oil_price', 'sp500'])

        # 캐시에 저장
        self._macro_cache = macro
        self._macro_cache_date = today
        print("✅ 공통 거시 데이터 수집 완료 (이후 종목은 재사용)")
        return self._macro_cache

    def fetch_all_indicators(self, ticker: str, days: int = 365, use_news_features: bool = False):
        end_date = datetime.now()
        start_date = end_date - timedelta(days=days)
        start_str = start_date.strftime('%Y%m%d')
        end_str = end_date.strftime('%Y%m%d')
        pure_ticker = ticker.split('.')[0]

        print(f"📊 {ticker} 데이터 수집 및 보강 시작...")

        # 1. 종목 주가만 다운로드 (거시 데이터는 캐시에서 가져옴)
        base_df = self._get_stock_data(ticker, start_date, end_date)

        # 2. 공통 거시 데이터 캐시에서 가져오기
        macro_df = self._get_macro_data(start_date, end_date)

        # 3. 국내 수급 데이터 수집
        try:
            investor_df = krx.get_market_net_purchases_of_equities_by_ticker(start_str, end_str, pure_ticker)
            if not investor_df.empty:
                inst_col = [c for c in investor_df.columns if '기관' in c]
                for_col  = [c for c in investor_df.columns if '외국인' in c]

                new_data = pd.DataFrame(index=investor_df.index)
                new_data['inst_net']    = investor_df[inst_col[0]] if inst_col else 0
                new_data['foreign_net'] = investor_df[for_col[0]]  if for_col  else 0
                investor_df = new_data
            else:
                investor_df = pd.DataFrame(0.0, index=base_df.index, columns=['inst_net', 'foreign_net'])
        except:
            investor_df = pd.DataFrame(0.0, index=base_df.index, columns=['inst_net', 'foreign_net'])

        # 4. 기업 실적 수집
        stock_info = yf.Ticker(ticker)
        try:
            financials = stock_info.quarterly_financials
            latest_op_income = financials.loc['Operating Income'].iloc[0]
        except:
            latest_op_income = 0

        # 5. 데이터 통합 (종목 주가 + 거시 데이터 + 수급 데이터)
        final_df = base_df.join(macro_df, how='left')
        final_df = final_df.join(investor_df, how='left')
        final_df['inst_net']    = final_df['inst_net'].fillna(0)
        final_df['foreign_net'] = final_df['foreign_net'].fillna(0)
        final_df['op_income']   = latest_op_income
        if use_news_features:
            final_df = self._merge_news_features(final_df, pure_ticker, start_date, end_date)

        return final_df.ffill().fillna(0)

    def _merge_news_features(self, base_df: pd.DataFrame, pure_ticker: str, start_date: datetime, end_date: datetime) -> pd.DataFrame:
        feature_columns = [
            'news_count',
            'avg_sentiment_score',
            'avg_impact_score',
            'positive_count',
            'negative_count',
            'neutral_count',
            'earnings_count',
            'policy_regulation_count',
            'supply_contract_count',
            'labor_legal_count',
        ]
        news_feature_df = pd.DataFrame(index=base_df.index.copy())
        for column in feature_columns:
            news_feature_df[column] = 0.0

        db = SessionLocal()
        try:
            stock = crud.resolve_stock_by_symbol(db, pure_ticker)
            if not stock:
                return base_df.join(news_feature_df, how='left')

            daily_features = crud.get_stored_daily_stock_news_features(db, stock.id, start_date, end_date)
            if not daily_features:
                return base_df.join(news_feature_df, how='left')

            rows = []
            for item in daily_features:
                rows.append(
                    {
                        'date': pd.Timestamp(item.date),
                        'news_count': item.news_count,
                        'avg_sentiment_score': item.avg_sentiment_score,
                        'avg_impact_score': item.avg_impact_score,
                        'positive_count': item.positive_count,
                        'negative_count': item.negative_count,
                        'neutral_count': item.neutral_count,
                        'earnings_count': item.earnings_count,
                        'policy_regulation_count': item.policy_regulation_count,
                        'supply_contract_count': item.supply_contract_count,
                        'labor_legal_count': item.labor_legal_count,
                    }
                )

            feature_frame = pd.DataFrame(rows)
            if feature_frame.empty:
                return base_df.join(news_feature_df, how='left')

            feature_frame = feature_frame.set_index('date')
            base_with_date_index = base_df.copy()
            base_with_date_index.index = pd.to_datetime(base_with_date_index.index).normalize()
            merged = base_with_date_index.join(feature_frame, how='left')

            for column in feature_columns:
                merged[column] = merged[column].fillna(0.0)

            return merged
        finally:
            db.close()

    def _get_stock_data(self, ticker, start, end):
        # ✅ 종목 주가만 따로 다운로드
        def get_clean_data(t, s, e):
            df = yf.download(t, start=s, end=e, progress=False)
            if isinstance(df.columns, pd.MultiIndex):
                df.columns = df.columns.droplevel(1)
            return df

        return get_clean_data(ticker, start, end)
