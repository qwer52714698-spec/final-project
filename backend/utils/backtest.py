from sqlalchemy.orm import Session
from datetime import datetime, timedelta
import models

def calculate_recent_win_rate(symbol: str, db: Session) -> dict:
    # 1. 최근 5영업일 동안 실제 주가 데이터가 들어와서 '검증 가능한' 예측 데이터 조회
    # (오늘 예측한 건 내일 주가가 와야 검증되므로, 검증일 기준 최근 5개를 가져옴)
    predictions = (
        db.query(models.StockPrediction)
        .filter(models.StockPrediction.symbol == symbol)
        .order_by(models.StockPrediction.analysis_date.desc())
        .limit(5)
        .all()
    )
    
    if not predictions:
        return {"win_rate": 0.0, "details": []}
        
    correct_count = 0
    details = []
    
    for pred in predictions:
        # 예측 기준일(analysis_date)의 주가와 그 다음 영업일(실제 타겟일)의 주가를 DB에서 조회
        current_date = datetime.strptime(pred.analysis_date, "%Y-%m-%d")
        
        # 다음날 주가 데이터 가져오기
        next_price = (
            db.query(models.StockPrice)
            .filter(models.StockPrice.symbol == symbol, models.StockPrice.date > current_date)
            .order_by(models.StockPrice.date.asc())
            .first()
        )
        
        # 예측 당일 주가 데이터 가져오기
        current_price = (
            db.query(models.StockPrice)
            .filter(models.StockPrice.symbol == symbol, models.StockPrice.date == current_date)
            .first()
        )
        
        if next_price and current_price:
            # 실제 상승/하락 여부 판별
            if next_price.close > current_price.close:
                actual_move = "상승"
            elif next_price.close < current_price.close:
                actual_move = "하락"
            else:
                actual_move = "횡보"
                
            # AI 예측과 실제 결과 비교
            is_correct = (pred.prediction == actual_move)
            if is_correct:
                correct_count += 1
                
            details.append({
                "date": pred.analysis_date,
                "predicted": pred.prediction,
                "actual": actual_move,
                "is_correct": is_correct
            })
            
    # 최근 5일 최종 승률 계산
    total_valid = len(details)
    win_rate = (correct_count / total_valid) * 100 if total_valid > 0 else 0.0
    
    return {
        "win_rate": round(win_rate, 1),
        "details": details
    }