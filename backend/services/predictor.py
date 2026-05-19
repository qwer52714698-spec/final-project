import pandas as pd
import numpy as np
from xgboost import XGBClassifier, XGBRegressor
from sklearn.model_selection import train_test_split
from .data_collector import MarketDataCollector

class StockPredictor:
    def __init__(self, ticker):
        self.ticker = ticker
        self.collector = MarketDataCollector()
        # 다중 분류를 위해 eval_metric을 mlogloss로 변경
        self.model = XGBClassifier(
            n_estimators=200,
            learning_rate=0.05,
            max_depth=6,
            random_state=42,
            objective='multi:softprob', # 다중 분류 확률값 출력 설정
            num_class=3,                # 클래스: 0(하락), 1(횡보), 2(상승)
            eval_metric='mlogloss'
        )
        # 다음날 종가 예측용 회귀 모델
        self.regressor = XGBRegressor(
            n_estimators=200,
            learning_rate=0.05,
            max_depth=6,
            random_state=42
        )

    def prepare_features(self, df):
        df = df.copy()
        
        # 1. 타겟 생성 (내일 변동률 기준 3진 분류)
        close_col = df['Close']
        if isinstance(close_col, pd.DataFrame):
            close_col = close_col.iloc[:, 0]
        
        # 내일 수익률 계산
        tomorrow_return = (close_col.shift(-1) - close_col) / close_col
        
        # 레이블링: 상승(2): > 0.5%, 하락(0): < -0.5%, 횡보(1): 그 사이
        df['target'] = 1 # 기본 횡보
        df.loc[tomorrow_return > 0.005, 'target'] = 2
        df.loc[tomorrow_return < -0.005, 'target'] = 0

        # 회귀 타겟: 다음날 실제 종가
        df['next_close'] = close_col.shift(-1)
        
        # 2. 기술적 지표
        df['ma5'] = close_col.rolling(5).mean()
        df['ma20'] = close_col.rolling(20).mean()
        df['volatility'] = close_col.pct_change().rolling(10).std()
        
        # 3. 수급 지표
        df['inst_5d'] = df['inst_net'].rolling(5).mean()
        df['foreign_5d'] = df['foreign_net'].rolling(5).mean()
        
        # 4. 거시 경제 지표 변화율
        df['int_change'] = df['interest_rate'].diff()
        df['ex_change'] = df['exchange_rate'].pct_change()
        df['oil_change'] = df['oil_price'].pct_change()
        df['sp500_change'] = df['sp500'].pct_change()
        
        # 5. 실적 및 밸류에이션 점수
        df['val_score'] = df['op_income'] / (close_col * df['Volume'].replace(0, 1))

        return df.dropna()

    def train_and_predict(self):
        raw_data = self.collector.fetch_all_indicators(self.ticker)
        if raw_data is None or len(raw_data) < 30:
            return {"error": "분석 가능한 데이터가 부족합니다."}

        data = self.prepare_features(raw_data)
        
        feature_cols = [
            'Close', 'Volume', 'interest_rate', 'exchange_rate', 'oil_price', 
            'sp500', 'inst_5d', 'foreign_5d', 'volatility', 'val_score'
        ]
        
        X = data[feature_cols]
        X = X.loc[:, ~X.columns.duplicated()]
        y = data['target']

        # 데이터가 너무 적으면 split 시 에러가 날 수 있으므로 shuffle=False 유지
        X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.1, shuffle=False)
        self.model.fit(X_train, y_train)

        # 회귀 모델 학습 (다음날 종가 예측)
        y_reg = data.loc[X_train.index, 'next_close']
        self.regressor.fit(X_train, y_reg)

        # 내일 방향 예측
        last_data = X.tail(1)
        probs = self.model.predict_proba(last_data)[0] # [하락확률, 횡보확률, 상승확률]
        pred_class = np.argmax(probs) # 가장 높은 확률의 인덱스

        # 결과 매핑
        mapping = {0: "하락", 1: "횡보", 2: "상승"}
        prediction = mapping[pred_class]
        confidence = probs[pred_class]

        # 특성 중요도 추출
        importances = self.model.feature_importances_
        importance_dict = {col: float(imp) for col, imp in zip(feature_cols, importances)}
        top_factors = dict(sorted(importance_dict.items(), key=lambda x: x[1], reverse=True)[:3])

        # 백테스트: 최근 5영업일 기준 수익률 계산
        close_series = data['Close']
        if isinstance(close_series, pd.DataFrame):
            close_series = close_series.iloc[:, 0]

        actual_returns_list = []
        predicted_returns_list = []

        # X.index[-6:-1] = 마지막 5영업일 (각 날짜의 다음날 데이터 존재)
        for idx in X.index[-6:-1]:
            pos = data.index.get_loc(idx)
            if pos + 1 >= len(data):
                continue
            row_probs = self.model.predict_proba(X.loc[[idx]])[0]
            if np.argmax(row_probs) == 2:  # 상승 예측 → 매수
                cur = float(close_series.iloc[pos])
                nxt = float(close_series.iloc[pos + 1])
                pred_price = float(self.regressor.predict(X.loc[[idx]])[0])
                actual_returns_list.append((nxt - cur) / cur * 100)
                predicted_returns_list.append((pred_price - cur) / cur * 100)

        if actual_returns_list:
            cumulative_actual = round(sum(actual_returns_list), 2)
            cumulative_predicted = round(sum(predicted_returns_list), 2)
            win_rate = round(sum(1 for r in actual_returns_list if r > 0) / len(actual_returns_list) * 100, 1)
        else:
            cumulative_actual = 0.0
            cumulative_predicted = 0.0
            win_rate = 0.0

        return {
            "prediction": prediction,
            "confidence": f"{round(confidence * 100, 2)}%",
            "top_influencers": top_factors,
            "analysis_date": data.index[-1].strftime('%Y-%m-%d'),
            "actual_return": cumulative_actual,
            "predicted_return": cumulative_predicted,
            "win_rate": win_rate,
            "period_start": X.index[-6].strftime('%Y-%m-%d'),
            "period_end": X.index[-2].strftime('%Y-%m-%d'),
        }