import pandas as pd
import numpy as np
import xgboost as xgb
from xgboost import XGBClassifier
from sklearn.model_selection import train_test_split
from .data_collector import MarketDataCollector


class StockPredictor:
    def __init__(self, ticker, use_news_features: bool = False):
        self.ticker = ticker
        self.use_news_features = use_news_features
        self.collector = MarketDataCollector()
        self.model = self._create_model()
        self.base_feature_cols = [
            'Close', 'Volume', 'interest_rate', 'exchange_rate', 'oil_price',
            'sp500', 'inst_5d', 'foreign_5d', 'volatility', 'val_score',
            'ma5', 'ma20', 'int_change', 'ex_change', 'oil_change', 'sp500_change',
        ]
        self.news_feature_cols = [
            'news_count', 'avg_sentiment_score', 'avg_impact_score',
            'positive_count', 'negative_count', 'neutral_count',
            'earnings_count', 'policy_regulation_count',
            'supply_contract_count', 'labor_legal_count',
            'news_count_3d', 'news_count_5d',
            'sentiment_3d', 'impact_3d', 'impact_pressure',
            'positive_ratio', 'negative_ratio',
            'policy_regulation_5d', 'supply_contract_5d',
            'labor_legal_5d', 'negative_impact_3d',
            'negative_burst_3d', 'positive_burst_3d', 'news_presence',
        ]

    def _create_model(self):
        return XGBClassifier(
            n_estimators=300,
            learning_rate=0.03,
            max_depth=4,
            min_child_weight=3,
            subsample=0.8,
            colsample_bytree=0.8,
            reg_lambda=2.0,
            reg_alpha=0.5,
            random_state=42,
            objective='multi:softprob',
            num_class=3,
            eval_metric='mlogloss'
        )

    def get_feature_cols(self) -> list[str]:
        return self.base_feature_cols + (self.news_feature_cols if self.use_news_features else [])

    def prepare_features(self, df):
        df = df.copy()

        close_col = df['Close']
        if isinstance(close_col, pd.DataFrame):
            close_col = close_col.iloc[:, 0]

        tomorrow_return = (close_col.shift(-1) - close_col) / close_col
        df['target'] = 1
        df.loc[tomorrow_return > 0.005, 'target'] = 2
        df.loc[tomorrow_return < -0.005, 'target'] = 0

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

        if self.use_news_features:
            news_total = (
                df['positive_count'].fillna(0)
                + df['negative_count'].fillna(0)
                + df['neutral_count'].fillna(0)
            ).replace(0, np.nan)
            df['news_count_3d'] = df['news_count'].rolling(3, min_periods=1).sum()
            df['news_count_5d'] = df['news_count'].rolling(5, min_periods=1).sum()
            df['sentiment_3d'] = df['avg_sentiment_score'].rolling(3, min_periods=1).mean()
            df['impact_3d'] = df['avg_impact_score'].rolling(3, min_periods=1).mean()
            df['impact_pressure'] = df['avg_impact_score'] * df['news_count']
            df['positive_ratio'] = (df['positive_count'] / news_total).fillna(0)
            df['negative_ratio'] = (df['negative_count'] / news_total).fillna(0)
            df['policy_regulation_5d'] = df['policy_regulation_count'].rolling(5, min_periods=1).sum()
            df['supply_contract_5d'] = df['supply_contract_count'].rolling(5, min_periods=1).sum()
            df['labor_legal_5d'] = df['labor_legal_count'].rolling(5, min_periods=1).sum()
            df['negative_burst_3d'] = df['negative_count'].rolling(3, min_periods=1).sum()
            df['positive_burst_3d'] = df['positive_count'].rolling(3, min_periods=1).sum()
            df['news_presence'] = (df['news_count_3d'] > 0).astype(float)
            df['negative_impact_3d'] = df['negative_ratio'] * df['impact_3d']

        return df.dropna()

    def _build_sample_weights(self, X_train: pd.DataFrame, y_train: pd.Series) -> np.ndarray:
        class_counts = y_train.value_counts().to_dict()
        total_count = len(y_train)
        class_weight_map = {
            cls: (total_count / (len(class_counts) * count))
            for cls, count in class_counts.items()
            if count > 0
        }
        class_weights = y_train.map(class_weight_map).astype(float).to_numpy()

        if not self.use_news_features:
            return class_weights

        news_signal_strength = (
            X_train['news_presence'].fillna(0)
            + X_train['impact_3d'].abs().fillna(0) * 12
            + X_train['negative_impact_3d'].fillna(0) * 20
            + X_train['policy_regulation_5d'].fillna(0) * 0.5
            + X_train['negative_burst_3d'].fillna(0) * 0.2
        )
        news_weights = 1.0 + np.clip(news_signal_strength, 0, 4)
        return class_weights * news_weights.to_numpy(dtype=float)

    def _temper_probabilities(self, probs: np.ndarray, temperature: float = 1.4) -> np.ndarray:
        if temperature <= 1.0:
            return probs
        safe_probs = np.clip(probs, 1e-9, 1.0)
        adjusted = np.power(safe_probs, 1.0 / temperature)
        adjusted_sum = adjusted.sum()
        return adjusted / adjusted_sum if adjusted_sum else probs

    def _extract_top_contributors(self, feature_cols: list[str], last_data: pd.DataFrame) -> dict[str, float]:
        try:
            booster = self.model.get_booster()
            dmatrix = xgb.DMatrix(last_data[feature_cols], feature_names=feature_cols)
            contribs = np.asarray(booster.predict(dmatrix, pred_contribs=True))

            if contribs.ndim == 2:
                sample_contribs = np.abs(contribs[0, :-1])
            elif contribs.ndim == 3:
                arr = contribs[0]
                if arr.shape[1] == len(feature_cols) + 1:
                    per_class = arr[:, :-1]
                elif arr.shape[0] == len(feature_cols) + 1:
                    per_class = arr[:-1, :].T
                else:
                    raise ValueError("Unexpected pred_contribs shape")
                sample_contribs = np.mean(np.abs(per_class), axis=0)
            else:
                raise ValueError("Unexpected pred_contribs ndim")

            contribution_dict = {
                col: float(val) for col, val in zip(feature_cols, sample_contribs, strict=False)
            }
            return dict(sorted(contribution_dict.items(), key=lambda x: x[1], reverse=True)[:10])
        except Exception:
            importances = self.model.feature_importances_
            importance_dict = {col: float(imp) for col, imp in zip(feature_cols, importances)}
            return dict(sorted(importance_dict.items(), key=lambda x: x[1], reverse=True)[:10])

    def train_and_predict(self):
        raw_data = self.collector.fetch_all_indicators(self.ticker, use_news_features=self.use_news_features)
        if raw_data is None or len(raw_data) < 30:
            return {"error": "분석 가능한 데이터가 부족합니다."}

        data = self.prepare_features(raw_data)
        if data is None or data.empty:
            return {"error": "전처리 후 학습 가능한 데이터가 없습니다."}

        feature_cols = self.get_feature_cols()
        X = data[feature_cols]
        X = X.loc[:, ~X.columns.duplicated()]
        y = data['target']

        if self.use_news_features:
            news_stats = []
            for col in self.news_feature_cols:
                series = X[col]
                nonzero_count = int((series != 0).sum())
                mean_value = float(series.mean()) if len(series) else 0.0
                last_value = float(series.iloc[-1]) if len(series) else 0.0
                news_stats.append(
                    f"{col}(nonzero={nonzero_count}, mean={mean_value:.4f}, last={last_value:.4f})"
                )
            print(f"🧠 [predictor 뉴스 통계] {self.ticker}: " + ", ".join(news_stats))

        if len(X) < 10 or len(y) < 10:
            return {"error": "학습용 데이터가 부족해 예측을 수행할 수 없습니다."}

        X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.1, shuffle=False)
        if len(X_train) == 0 or len(y_train) == 0:
            return {"error": "학습 구간 데이터가 비어 있어 예측을 수행할 수 없습니다."}

        sample_weights = self._build_sample_weights(X_train, y_train)
        self.model.fit(X_train, y_train, sample_weight=sample_weights)

        last_data = X.tail(1)
        probs = self.model.predict_proba(last_data)[0]
        probs = self._temper_probabilities(probs)
        pred_class = int(np.argmax(probs))

        mapping = {0: "하락", 1: "횡보", 2: "상승"}
        prediction = mapping[pred_class]
        confidence = probs[pred_class]
        top_factors = self._extract_top_contributors(feature_cols, last_data)

        return {
            "prediction": prediction,
            "confidence": f"{round(confidence * 100, 2)}%",
            "top_influencers": top_factors,
            "analysis_date": data.index[-1].strftime('%Y-%m-%d')
        }
