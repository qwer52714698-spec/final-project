from fastapi import APIRouter, Depends, HTTPException, BackgroundTasks
from sqlalchemy.orm import Session
from database import get_db
import models, schemas
from typing import List
import numpy as np
from services.predictor import StockPredictor
from datetime import datetime, timedelta

router = APIRouter(prefix="/stocks", tags=["주식"])


def _resolve_stock(db: Session, symbol: str):
    pure_symbol = symbol.split(".")[0]
    candidate_symbols = [pure_symbol, f"{pure_symbol}.KS", f"{pure_symbol}.KQ"]
    candidates = db.query(models.Stock).filter(models.Stock.symbol.in_(candidate_symbols)).all()
    if not candidates:
        return None

    preferred = [stock for stock in candidates if stock.name and not stock.name.startswith("Stock_")]
    for candidate_symbol in [pure_symbol, f"{pure_symbol}.KS", f"{pure_symbol}.KQ"]:
        for stock in preferred:
            if stock.symbol == candidate_symbol:
                return stock

    return preferred[0] if preferred else candidates[0]


def _label_from_return(return_rate: float) -> str:
    if return_rate > 0.005:
        return "상승"
    if return_rate < -0.005:
        return "하락"
    return "횡보"

@router.get("/{symbol}/analyze")
def analyze_stock(symbol: str, db: Session = Depends(get_db)):
    pure_symbol = symbol.split('.')[0]
    
    stock = _resolve_stock(db, symbol)
    
    if not stock:
        print(f"🛠️ {pure_symbol} 종목이 없어 새로 생성합니다.")
        new_stock = models.Stock(
            symbol=pure_symbol,
            name=f"Stock_{pure_symbol}",
            sector_id=1,
            exchange="KRX"
        )
        db.add(new_stock)
        db.commit()
        db.refresh(new_stock)
        stock = new_stock

    try:
        ticker = f"{pure_symbol}.KS" if not pure_symbol.endswith(('.KS', '.KQ')) else pure_symbol
        predictor = StockPredictor(ticker)
        analysis_result = predictor.train_and_predict()
        
        if "error" in analysis_result:
            raise HTTPException(status_code=500, detail=analysis_result["error"])

        new_prediction = models.StockPrediction(
            stock_id=stock.id,
            ticker=ticker,
            prediction=analysis_result["prediction"],
            confidence=analysis_result["confidence"],
            important_factors=analysis_result["top_influencers"]
        )
        db.add(new_prediction)
        db.commit()
        print(f"✨ [DB 저장 완료] {pure_symbol} 분석 데이터가 테이블에 기록되었습니다.")

        return {"status": "success", "data": analysis_result}

    except Exception as e:
        print(f"❌ 분석 중 에러 발생: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/{symbol}/evaluation", response_model=schemas.StockPredictionEvaluationResponse)
def evaluate_stock_predictions(symbol: str, limit: int = 30, db: Session = Depends(get_db)):
    stock = _resolve_stock(db, symbol)
    if not stock:
        raise HTTPException(status_code=404, detail="종목을 찾을 수 없습니다.")

    predictions = (
        db.query(models.StockPrediction)
        .filter(models.StockPrediction.stock_id == stock.id)
        .order_by(models.StockPrediction.created_at.desc(), models.StockPrediction.id.desc())
        .all()
    )
    if not predictions:
        raise HTTPException(status_code=404, detail="평가할 예측 기록이 없습니다.")

    prices = (
        db.query(models.StockPrice)
        .filter(models.StockPrice.stock_id == stock.id)
        .order_by(models.StockPrice.date.asc())
        .all()
    )
    # 같은 날짜에 중복 저장된 가격 row가 있을 수 있어 날짜별 마지막 row만 남긴다.
    latest_price_per_day = {}
    for price in prices:
        latest_price_per_day[price.date.date()] = price
    unique_prices = [latest_price_per_day[day] for day in sorted(latest_price_per_day.keys())]

    if len(unique_prices) < 2:
        raise HTTPException(status_code=404, detail="평가할 실제 가격 데이터가 부족합니다.")

    latest_prediction_per_day = {}
    for prediction in predictions:
        prediction_day = prediction.created_at.date()
        if prediction_day not in latest_prediction_per_day:
            latest_prediction_per_day[prediction_day] = prediction

    ordered_predictions = sorted(
        latest_prediction_per_day.values(),
        key=lambda item: item.created_at,
        reverse=True,
    )

    items: list[schemas.StockPredictionEvaluationItem] = []
    for prediction in ordered_predictions:
        prediction_day = prediction.created_at.date()

        base_price = None
        next_price = None
        for idx, price in enumerate(unique_prices):
            price_day = price.date.date()
            if price_day <= prediction_day:
                base_price = price
            elif price_day > prediction_day and base_price is not None:
                next_price = price
                break

        if not base_price or not next_price or not base_price.close or not next_price.close:
            continue

        actual_return = (next_price.close - base_price.close) / base_price.close
        actual_label = _label_from_return(actual_return)
        matched = prediction.prediction == actual_label

        items.append(
            schemas.StockPredictionEvaluationItem(
                prediction_date=prediction.created_at,
                base_price_date=base_price.date,
                next_price_date=next_price.date,
                predicted_label=prediction.prediction,
                actual_label=actual_label,
                actual_return_pct=round(actual_return * 100, 3),
                confidence=prediction.confidence,
                matched=matched,
            )
        )

        if len(items) >= limit:
            break

    if not items:
        raise HTTPException(status_code=404, detail="평가 가능한 예측-실제 결과 쌍이 없습니다.")

    matched_count = sum(1 for item in items if item.matched)
    accuracy_pct = round((matched_count / len(items)) * 100, 2)

    return schemas.StockPredictionEvaluationResponse(
        symbol=stock.symbol,
        evaluated_count=len(items),
        matched_count=matched_count,
        accuracy_pct=accuracy_pct,
        items=items,
    )


@router.get("/{symbol}/backtest", response_model=schemas.StockBacktestResponse)
def backtest_stock_predictions(
    symbol: str,
    lookback_days: int = 365,
    eval_points: int = 20,
    min_train_size: int = 60,
    use_news_features: bool = False,
):
    pure_symbol = symbol.split('.')[0]
    ticker = f"{pure_symbol}.KS" if not pure_symbol.endswith(('.KS', '.KQ')) else pure_symbol

    predictor = StockPredictor(ticker, use_news_features=use_news_features)
    raw_data = predictor.collector.fetch_all_indicators(ticker, days=lookback_days, use_news_features=use_news_features)
    if raw_data is None or len(raw_data) < min_train_size + 5:
        raise HTTPException(status_code=404, detail="백테스트에 필요한 시계열 데이터가 부족합니다.")

    data = predictor.prepare_features(raw_data)
    if data is None or data.empty or len(data) < min_train_size + 5:
        raise HTTPException(status_code=404, detail="백테스트에 필요한 전처리 데이터가 부족합니다.")

    feature_cols = predictor.get_feature_cols()
    X = data[feature_cols]
    X = X.loc[:, ~X.columns.duplicated()]
    y = data['target']

    max_eval_points = max(0, len(X) - min_train_size)
    eval_points = min(eval_points, max_eval_points)
    if eval_points <= 0:
        raise HTTPException(status_code=404, detail="백테스트 가능한 평가 구간이 없습니다.")

    mapping = {0: "하락", 1: "횡보", 2: "상승"}
    items: list[schemas.StockBacktestItem] = []
    start_idx = len(X) - eval_points

    for idx in range(start_idx, len(X)):
        X_train = X.iloc[:idx]
        y_train = y.iloc[:idx]
        X_eval = X.iloc[idx:idx + 1]
        if len(X_train) < min_train_size or X_eval.empty:
            continue

        model = predictor._create_model()
        sample_weights = predictor._build_sample_weights(X_train, y_train)
        model.fit(X_train, y_train, sample_weight=sample_weights)
        probs = model.predict_proba(X_eval)[0]
        probs = predictor._temper_probabilities(probs)
        pred_class = int(np.argmax(probs))
        predicted_label = mapping[pred_class]
        confidence = f"{round(float(probs[pred_class]) * 100, 2)}%"

        actual_target = int(y.iloc[idx])
        actual_label = mapping[actual_target]

        close_series = data['Close']
        if hasattr(close_series, "iloc"):
            if idx + 1 >= len(close_series):
                continue
            base_close = float(close_series.iloc[idx])
            next_close = float(close_series.iloc[idx + 1])
        else:
            continue

        actual_return_pct = round(((next_close - base_close) / base_close) * 100, 3) if base_close else 0.0
        matched = predicted_label == actual_label

        items.append(
            schemas.StockBacktestItem(
                analysis_date=data.index[idx].strftime('%Y-%m-%d'),
                predicted_label=predicted_label,
                actual_label=actual_label,
                actual_return_pct=actual_return_pct,
                confidence=confidence,
                matched=matched,
            )
        )

    if not items:
        raise HTTPException(status_code=404, detail="백테스트 결과를 생성할 수 없습니다.")

    matched_count = sum(1 for item in items if item.matched)
    accuracy_pct = round((matched_count / len(items)) * 100, 2)

    return schemas.StockBacktestResponse(
        symbol=f"{ticker}{' (news)' if use_news_features else ' (baseline)'}",
        evaluated_count=len(items),
        matched_count=matched_count,
        accuracy_pct=accuracy_pct,
        items=items,
    )

@router.get("/", response_model=List[schemas.StockResponse])
def get_stocks(sector_id: int = None, db: Session = Depends(get_db)):
    q = db.query(models.Stock)
    if sector_id:
        q = q.filter(models.Stock.sector_id == sector_id)
    return q.all()

@router.get("/sector/{sector_id}", response_model=List[schemas.StockWithPrices])
def get_sector_stocks_with_prices(sector_id: int, days: int = 90, db: Session = Depends(get_db)):
    sector = db.query(models.Sector).filter(models.Sector.id == sector_id).first()
    if not sector:
        raise HTTPException(status_code=404, detail="섹터를 찾을 수 없습니다.")

    stocks = db.query(models.Stock).filter(models.Stock.sector_id == sector_id).all()
    result = []
    cutoff = (datetime.now() - timedelta(days=days)).date()

    for stock in stocks:
        prices = (
            db.query(models.StockPrice)
            .filter(models.StockPrice.stock_id == stock.id, models.StockPrice.date >= cutoff)
            .order_by(models.StockPrice.date.asc())
            .all()
        )
        result.append(schemas.StockWithPrices(stock=stock, prices=prices))
    return result

@router.get("/{symbol}/prices", response_model=List[schemas.StockPriceResponse])
def get_stock_prices(symbol: str, days: int = 90, db: Session = Depends(get_db)):
    stock = _resolve_stock(db, symbol)
    if not stock:
        raise HTTPException(status_code=404, detail="종목을 찾을 수 없습니다.")

    cutoff = (datetime.now() - timedelta(days=days)).date()
    return (
        db.query(models.StockPrice)
        .filter(models.StockPrice.stock_id == stock.id, models.StockPrice.date >= cutoff)
        .order_by(models.StockPrice.date.asc())
        .all()
    )

@router.post("/collect")
def trigger_collect(background_tasks: BackgroundTasks):
    from services.stock_collector import collect_stock_prices
    background_tasks.add_task(collect_stock_prices)
    return {"message": "주가 데이터 수집을 시작합니다."}
