import pandas as pd
import numpy as np
from xgboost import XGBClassifier
from sklearn.model_selection import train_test_split
from .data_collector import MarketDataCollector

class StockPredictor:
    def __init__(self, ticker):
        self.ticker = ticker
        self.collector = MarketDataCollector()
        self.model = XGBClassifier(
            n_estimators=200,
            learning_rate=0.05,
            max_depth=6,
            random_state=42,
            eval_metric='logloss'
        )

    def prepare_features(self, df):
        df = df.copy()
        
        # 1. 타겟 생성 (내일 상승 여부)
        close_col = df['Close']
        if isinstance(close_col, pd.DataFrame):
            close_col = close_col.iloc[:, 0]
        df['target'] = (close_col.shift(-1) > close_col).astype(int)
        
        # 2. 기술적 지표 (MA, RSI 대용 변동성)
        df['ma5'] = close_col.rolling(5).mean()
        df['ma20'] = close_col.rolling(20).mean()
        df['volatility'] = close_col.pct_change().rolling(10).std()
        
        # 3. 수급 지표 (기관/외인 5일 추세)
        df['inst_5d'] = df['inst_net'].rolling(5).mean()
        df['foreign_5d'] = df['foreign_net'].rolling(5).mean()
        
        # 4. 거시 경제 지표 변화율 (금리, 환율, 유가, S&P500)
        df['int_change'] = df['interest_rate'].diff()
        df['ex_change'] = df['exchange_rate'].pct_change()
        df['oil_change'] = df['oil_price'].pct_change()
        df['sp500_change'] = df['sp500'].pct_change()
        
        # 5. 실적 및 밸류에이션 점수
        # 실적(op_income) 대비 현재 주가 수준 계산
        df['val_score'] = df['op_income'] / (close_col * df['Volume'].replace(0, 1))

        return df.dropna()

    def train_and_predict(self):
        raw_data = self.collector.fetch_all_indicators(self.ticker)
        if raw_data is None or len(raw_data) < 30:
            return {"error": "분석 가능한 데이터가 부족합니다."}

        data = self.prepare_features(raw_data)
        
        # 학습에 사용할 10대 핵심 피처 리스트
        feature_cols = [
            'Close', 'Volume', 'interest_rate', 'exchange_rate', 'oil_price', 
            'sp500', 'inst_5d', 'foreign_5d', 'volatility', 'val_score'
        ]
        
        X = data[feature_cols]
        # 멀티인덱스 등으로 인한 중복 컬럼 방지
        X = X.loc[:, ~X.columns.duplicated()]
        y = data['target']

        X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.1, shuffle=False)
        self.model.fit(X_train, y_train)

        last_data = X.tail(1)
        prob = self.model.predict_proba(last_data)[0][1]
        
        # 특성 중요도 추출 (어떤 요소가 주가에 큰 영향을 주었나)
        importances = self.model.feature_importances_
        importance_dict = {col: float(imp) for col, imp in zip(feature_cols, importances)}
        top_factors = dict(sorted(importance_dict.items(), key=lambda x: x[1], reverse=True)[:3])

        return {
            "prediction": "상승" if prob > 0.5 else "하락",
            "confidence": f"{round(prob * 100, 2)}%",
            "top_influencers": top_factors,
            "analysis_date": data.index[-1].strftime('%Y-%m-%d')
        }