import yfinance as yf
import pandas as pd
from pykrx import stock as krx
from datetime import datetime, timedelta

class MarketDataCollector:
    def fetch_all_indicators(self, ticker: str, days: int = 365):
        end_date = datetime.now()
        start_date = end_date - timedelta(days=days)
        start_str = start_date.strftime('%Y%m%d')
        end_str = end_date.strftime('%Y%m%d')
        pure_ticker = ticker.split('.')[0]

        print(f"📊 {ticker} 데이터 수집 및 보강 시작...")

        # 1. 기본 지표 수집
        base_df = self._get_base_indicators(ticker, start_date, end_date)
        
        # 2. 국내 수급 데이터 수집 (에러 방지 로직 강화)
        try:
            investor_df = krx.get_market_net_purchases_of_equities_by_ticker(start_str, end_str, pure_ticker)
            if not investor_df.empty:
                # '기관'이나 '외국인' 단어가 포함된 컬럼 찾기
                inst_col = [c for c in investor_df.columns if '기관' in c]
                for_col = [c for c in investor_df.columns if '외국인' in c]
                
                new_data = pd.DataFrame(index=investor_df.index)
                new_data['inst_net'] = investor_df[inst_col[0]] if inst_col else 0
                new_data['foreign_net'] = investor_df[for_col[0]] if for_col else 0
                investor_df = new_data
            else:
                investor_df = pd.DataFrame(index=base_df.index, columns=['inst_net', 'foreign_net']).fillna(0)
        except:
            investor_df = pd.DataFrame(index=base_df.index, columns=['inst_net', 'foreign_net']).fillna(0)
            
        # 3. 기업 실적 수집
        stock_info = yf.Ticker(ticker)
        try:
            financials = stock_info.quarterly_financials
            latest_op_income = financials.loc['Operating Income'].iloc[0]
        except:
            latest_op_income = 0

        # 4. 데이터 통합
        final_df = base_df.join(investor_df, how='left')
        final_df['inst_net'] = final_df['inst_net'].fillna(0)
        final_df['foreign_net'] = final_df['foreign_net'].fillna(0)
        final_df['op_income'] = latest_op_income
        
        return final_df.ffill().fillna(0)

    def _get_base_indicators(self, ticker, start, end):
        def get_clean_data(t, s, e):
            df = yf.download(t, start=s, end=e)
            if isinstance(df.columns, pd.MultiIndex):
                df.columns = df.columns.droplevel(1)
            return df

        stock = get_clean_data(ticker, start, end)
        tnx = get_clean_data("^TNX", start, end)[['Close']].rename(columns={'Close': 'interest_rate'})
        usdkrw = get_clean_data("KRW=X", start, end)[['Close']].rename(columns={'Close': 'exchange_rate'})
        wti = get_clean_data("CL=F", start, end)[['Close']].rename(columns={'Close': 'oil_price'})
        sp500 = get_clean_data("^GSPC", start, end)[['Close']].rename(columns={'Close': 'sp500'})
        
        return pd.concat([stock, tnx, usdkrw, wti, sp500], axis=1).ffill()