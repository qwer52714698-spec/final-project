from fastapi import APIRouter, Depends, HTTPException, BackgroundTasks
from sqlalchemy.orm import Session
from database import get_db
import models, schemas
from typing import List
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
    exact_pure = [stock for stock in preferred if stock.symbol == pure_symbol]
    if exact_pure:
        return exact_pure[0]

    exact_ks = [stock for stock in preferred if stock.symbol == f"{pure_symbol}.KS"]
    if exact_ks:
        return exact_ks[0]

    exact_kq = [stock for stock in preferred if stock.symbol == f"{pure_symbol}.KQ"]
    if exact_kq:
        return exact_kq[0]

    return preferred[0] if preferred else candidates[0]

@router.get("/{symbol}/analyze")
def analyze_stock(symbol: str, db: Session = Depends(get_db)):
    pure_symbol = symbol.split('.')[0]
    
    # 1. DB에서 종목 확인
    stock = _resolve_stock(db, symbol)
    
    # 2. 만약 DB에 종목이 없으면 강제로 생성 (Sector ID는 임의로 1번 할당)
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

        # 3. 예측 결과 저장 
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
    cutoff = datetime.utcnow() - timedelta(days=days)

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

    cutoff = datetime.utcnow() - timedelta(days=days)
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
