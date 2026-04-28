from fastapi import APIRouter, Depends, HTTPException, BackgroundTasks
from sqlalchemy.orm import Session
from database import get_db
from dependencies import get_current_user
from services.stock_collector import collect_stock_prices
import models
import schemas
from typing import List

router = APIRouter(prefix="/stocks", tags=["주식"])


@router.get("/", response_model=List[schemas.StockResponse])
def get_stocks(sector_id: int = None, db: Session = Depends(get_db)):
    q = db.query(models.Stock)
    if sector_id:
        q = q.filter(models.Stock.sector_id == sector_id)
    return q.all()


@router.get("/sector/{sector_id}", response_model=List[schemas.StockWithPrices])
def get_sector_stocks_with_prices(
    sector_id: int,
    days: int = 30,
    db: Session = Depends(get_db),
):
    sector = db.query(models.Sector).filter(models.Sector.id == sector_id).first()
    if not sector:
        raise HTTPException(status_code=404, detail="섹터를 찾을 수 없습니다.")

    stocks = db.query(models.Stock).filter(models.Stock.sector_id == sector_id).all()
    result = []
    from datetime import datetime, timedelta
    cutoff = datetime.utcnow() - timedelta(days=days)

    for stock in stocks:
        prices = (
            db.query(models.StockPrice)
            .filter(
                models.StockPrice.stock_id == stock.id,
                models.StockPrice.date >= cutoff,
            )
            .order_by(models.StockPrice.date.asc())
            .all()
        )
        result.append(schemas.StockWithPrices(stock=stock, prices=prices))
    return result


@router.get("/{symbol}/prices", response_model=List[schemas.StockPriceResponse])
def get_stock_prices(
    symbol: str,
    days: int = 30,
    db: Session = Depends(get_db),
):
    stock = db.query(models.Stock).filter(models.Stock.symbol == symbol).first()
    if not stock:
        raise HTTPException(status_code=404, detail="종목을 찾을 수 없습니다.")

    from datetime import datetime, timedelta
    cutoff = datetime.utcnow() - timedelta(days=days)
    return (
        db.query(models.StockPrice)
        .filter(
            models.StockPrice.stock_id == stock.id,
            models.StockPrice.date >= cutoff,
        )
        .order_by(models.StockPrice.date.asc())
        .all()
    )


@router.post("/collect", summary="주가 데이터 수집 트리거")
def trigger_collect(background_tasks: BackgroundTasks):
    background_tasks.add_task(collect_stock_prices)
    return {"message": "주가 데이터 수집을 시작합니다."}
