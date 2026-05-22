import pandas as pd
import numpy as np
from xgboost import XGBClassifier, XGBRegressor
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
            objective='multi:softprob',
            num_class=3,
            eval_metric='mlogloss'
        )
        self.regressor = XGBRegressor(
            n_estimators=200,
            learning_rate=0.05,
            max_depth=6,
            random_state=42
        )

    def prepare_features(self, df):
        df = df.copy()
        
        close_col = df['Close']
        if isinstance(close_col, pd.DataFrame):
            close_col = close_col.iloc[:, 0]
        
        tomorrow_return = (close_col.shift(-1) - close_col) / close_col
        
        df['target'] = 1
        df.loc[tomorrow_return > 0.005, 'target'] = 2
        df.loc[tomorrow_return < -0.005, 'target'] = 0

        df['next_close'] = close_col.shift(-1)
        
        df['ma5'] = close_col.rolling(5).mean()
        df['ma20'] = close_col.rolling(20).mean()
        df['volatility'] = close_col.pct_change().rolling(10).std()
        
        df['inst_5d'] = df['inst_net'].rolling(5).mean()
        df['foreign_5d'] = df['foreign_net'].rolling(5).mean()
        
        df['int_change'] = df['interest_rate'].diff()
        df['ex_change'] = df['exchange_rate'].pct_change()
        df['oil_change'] = df['oil_price'].pct_change()
        df['sp500_change'] = df['sp500'].pct_change()
        
        df['val_score'] = df['op_income'] / (close_col * df['Volume'].replace(0, 1))

        df = df.ffill().bfill()
        return df

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

        X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.1, shuffle=False)
        self.model.fit(X_train, y_train)

        y_reg = data.loc[X_train.index, 'next_close']
        self.regressor.fit(X_train, y_reg)

        last_data = X.tail(1)
        probs = self.model.predict_proba(last_data)[0]
        pred_class = np.argmax(probs)

        mapping = {0: "하락", 1: "횡보", 2: "상승"}
        prediction = mapping[pred_class]
        confidence = probs[pred_class]

        predicted_next_price = round(float(self.regressor.predict(last_data)[0]), 2)

        importances = self.model.feature_importances_
        importance_dict = {col: float(imp) for col, imp in zip(feature_cols, importances)}
        top_factors = dict(sorted(importance_dict.items(), key=lambda x: x[1], reverse=True)[:3])

        close_series = data['Close']
        if isinstance(close_series, pd.DataFrame):
            close_series = close_series.iloc[:, 0]

        actual_returns_list = []
        predicted_returns_list = []

        for idx in X.index[-6:-1]:
            pos = data.index.get_loc(idx)
            if pos + 1 >= len(data):
                continue
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
            "period_end": X.index[-1].strftime('%Y-%m-%d'),
            "predicted_next_close": predicted_next_price,
        }