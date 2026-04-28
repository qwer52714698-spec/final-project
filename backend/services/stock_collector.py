import yfinance as yf
import pandas as pd
from datetime import datetime, timedelta
from sqlalchemy.orm import Session
from database import SessionLocal
import models

SECTORS_META = {
    "반도체":    {"description": "메모리·시스템반도체·파운드리·장비 기업", "icon": "💾"},
    "2차전지":   {"description": "배터리·양극재·전해질 등 전기차 핵심 소재", "icon": "🔋"},
    "자동차":    {"description": "완성차·부품·자율주행 관련 기업", "icon": "🚗"},
    "AI/IT":     {"description": "인공지능·플랫폼·소프트웨어·통신 기업", "icon": "🤖"},
    "바이오/제약": {"description": "제약·바이오·의료기기 기업", "icon": "💊"},
    "금융":      {"description": "은행·증권·보험·카드 기업", "icon": "🏦"},
    "에너지/화학": {"description": "정유·화학·신재생에너지·소재 기업", "icon": "⚡"},
    "산업재":    {"description": "건설·철강·조선·기계·항공 기업", "icon": "🏭"},
    "소비재":    {"description": "식품·유통·패션·생활용품 기업", "icon": "🛒"},
}

SECTOR_STOCKS = {
    "반도체": [
        {"symbol": "005930.KS", "name": "삼성전자"},
        {"symbol": "000660.KS", "name": "SK하이닉스"},
        {"symbol": "042700.KS", "name": "한미반도체"},
        {"symbol": "357780.KS", "name": "솔브레인"},
        {"symbol": "240810.KS", "name": "원익IPS"},
        {"symbol": "288490.KS", "name": "유진테크"},
        {"symbol": "009150.KS", "name": "삼성전기"},
        {"symbol": "011070.KS", "name": "LG이노텍"},
        {"symbol": "000990.KS", "name": "DB하이텍"},
        {"symbol": "036930.KS", "name": "주성엔지니어링"},
        {"symbol": "033640.KS", "name": "네패스"},
        {"symbol": "058470.KS", "name": "리노공업"},
    ],
    "2차전지": [
        {"symbol": "373220.KS", "name": "LG에너지솔루션"},
        {"symbol": "006400.KS", "name": "삼성SDI"},
        {"symbol": "051910.KS", "name": "LG화학"},
        {"symbol": "096770.KS", "name": "SK이노베이션"},
        {"symbol": "247540.KS", "name": "에코프로비엠"},
        {"symbol": "086520.KS", "name": "에코프로"},
        {"symbol": "003670.KS", "name": "포스코퓨처엠"},
        {"symbol": "005070.KS", "name": "코스모신소재"},
        {"symbol": "020150.KS", "name": "롯데에너지머티리얼즈"},
        {"symbol": "010060.KS", "name": "OCI홀딩스"},
        {"symbol": "298050.KS", "name": "효성첨단소재"},
    ],
    "자동차": [
        {"symbol": "005380.KS", "name": "현대차"},
        {"symbol": "000270.KS", "name": "기아"},
        {"symbol": "012330.KS", "name": "현대모비스"},
        {"symbol": "011210.KS", "name": "현대위아"},
        {"symbol": "204320.KS", "name": "HL만도"},
        {"symbol": "086280.KS", "name": "현대글로비스"},
        {"symbol": "018880.KS", "name": "한온시스템"},
        {"symbol": "307950.KS", "name": "현대오토에버"},
        {"symbol": "004020.KS", "name": "현대제철"},
        {"symbol": "084370.KS", "name": "한국타이어앤테크놀로지"},
    ],
    "AI/IT": [
        {"symbol": "035420.KS", "name": "NAVER"},
        {"symbol": "035720.KS", "name": "카카오"},
        {"symbol": "259960.KS", "name": "크래프톤"},
        {"symbol": "036570.KS", "name": "엔씨소프트"},
        {"symbol": "251270.KS", "name": "넷마블"},
        {"symbol": "018260.KS", "name": "삼성SDS"},
        {"symbol": "017670.KS", "name": "SK텔레콤"},
        {"symbol": "030200.KS", "name": "KT"},
        {"symbol": "323410.KS", "name": "카카오뱅크"},
        {"symbol": "066570.KS", "name": "LG전자"},
        {"symbol": "377300.KS", "name": "카카오페이"},
        {"symbol": "032640.KS", "name": "LG유플러스"},
    ],
    "바이오/제약": [
        {"symbol": "207940.KS", "name": "삼성바이오로직스"},
        {"symbol": "068270.KS", "name": "셀트리온"},
        {"symbol": "128940.KS", "name": "한미약품"},
        {"symbol": "000100.KS", "name": "유한양행"},
        {"symbol": "185750.KS", "name": "종근당"},
        {"symbol": "006280.KS", "name": "녹십자"},
        {"symbol": "009290.KS", "name": "광동제약"},
        {"symbol": "000020.KS", "name": "동화약품"},
        {"symbol": "003850.KS", "name": "보령"},
        {"symbol": "326030.KS", "name": "SK바이오팜"},
        {"symbol": "069620.KS", "name": "대웅제약"},
        {"symbol": "091990.KS", "name": "셀트리온헬스케어"},
    ],
    "금융": [
        {"symbol": "105560.KS", "name": "KB금융"},
        {"symbol": "055550.KS", "name": "신한지주"},
        {"symbol": "086790.KS", "name": "하나금융지주"},
        {"symbol": "316140.KS", "name": "우리금융지주"},
        {"symbol": "032830.KS", "name": "삼성생명"},
        {"symbol": "000810.KS", "name": "삼성화재"},
        {"symbol": "006800.KS", "name": "미래에셋증권"},
        {"symbol": "005940.KS", "name": "NH투자증권"},
        {"symbol": "071050.KS", "name": "한국금융지주"},
        {"symbol": "005830.KS", "name": "DB손해보험"},
        {"symbol": "001450.KS", "name": "현대해상"},
        {"symbol": "139130.KS", "name": "DGB금융지주"},
    ],
    "에너지/화학": [
        {"symbol": "011170.KS", "name": "롯데케미칼"},
        {"symbol": "009830.KS", "name": "한화솔루션"},
        {"symbol": "011780.KS", "name": "금호석유화학"},
        {"symbol": "010950.KS", "name": "S-Oil"},
        {"symbol": "078930.KS", "name": "GS"},
        {"symbol": "000880.KS", "name": "한화"},
        {"symbol": "004800.KS", "name": "효성"},
        {"symbol": "120110.KS", "name": "코오롱인더"},
        {"symbol": "285130.KS", "name": "SK케미칼"},
        {"symbol": "003240.KS", "name": "태광산업"},
        {"symbol": "006650.KS", "name": "대한유화"},
        {"symbol": "002380.KS", "name": "KCC"},
    ],
    "산업재": [
        {"symbol": "005490.KS", "name": "POSCO홀딩스"},
        {"symbol": "000720.KS", "name": "현대건설"},
        {"symbol": "028050.KS", "name": "삼성엔지니어링"},
        {"symbol": "006360.KS", "name": "GS건설"},
        {"symbol": "015760.KS", "name": "한국전력"},
        {"symbol": "034020.KS", "name": "두산에너빌리티"},
        {"symbol": "329180.KS", "name": "현대중공업"},
        {"symbol": "012450.KS", "name": "한화에어로스페이스"},
        {"symbol": "047810.KS", "name": "한국항공우주"},
        {"symbol": "003490.KS", "name": "대한항공"},
        {"symbol": "010140.KS", "name": "삼성중공업"},
        {"symbol": "006260.KS", "name": "LS"},
        {"symbol": "047040.KS", "name": "대우건설"},
    ],
    "소비재": [
        {"symbol": "139480.KS", "name": "이마트"},
        {"symbol": "004170.KS", "name": "신세계"},
        {"symbol": "023530.KS", "name": "롯데쇼핑"},
        {"symbol": "097950.KS", "name": "CJ제일제당"},
        {"symbol": "004370.KS", "name": "농심"},
        {"symbol": "033780.KS", "name": "KT&G"},
        {"symbol": "090430.KS", "name": "아모레퍼시픽"},
        {"symbol": "051900.KS", "name": "LG생활건강"},
        {"symbol": "000080.KS", "name": "하이트진로"},
        {"symbol": "005300.KS", "name": "롯데칠성"},
        {"symbol": "271560.KS", "name": "오리온"},
        {"symbol": "003230.KS", "name": "삼양식품"},
        {"symbol": "008770.KS", "name": "호텔신라"},
        {"symbol": "069960.KS", "name": "현대백화점"},
    ],
}


def ensure_sectors_exist(db: Session):
    existing = {s.name for s in db.query(models.Sector).all()}
    for name, meta in SECTORS_META.items():
        if name not in existing:
            db.add(models.Sector(name=name, **meta))
    db.commit()


def ensure_stocks_exist(db: Session):
    sector_map = {s.name: s for s in db.query(models.Sector).all()}
    existing_symbols = {s.symbol for s in db.query(models.Stock).all()}
    added = 0
    for sector_name, stocks in SECTOR_STOCKS.items():
        sector = sector_map.get(sector_name)
        if not sector:
            continue
        for s in stocks:
            if s["symbol"] in existing_symbols:
                continue
            db.add(models.Stock(
                sector_id=sector.id,
                symbol=s["symbol"],
                name=s["name"],
                exchange="KRX",
            ))
            existing_symbols.add(s["symbol"])
            added += 1
    db.commit()
    if added:
        print(f"[종목] 신규 {added}개 추가")


def _fetch_prices_batch(symbols: list, start: str, end: str) -> dict:
    if not symbols:
        return {}
    try:
        raw = yf.download(
            symbols,
            start=start,
            end=end,
            group_by="ticker",
            auto_adjust=True,
            progress=False,
            threads=True,
        )
        if raw.empty:
            return {}
        result = {}
        if len(symbols) == 1:
            result[symbols[0]] = raw
        else:
            for sym in symbols:
                try:
                    df = raw[sym].dropna(how="all")
                    if not df.empty:
                        result[sym] = df
                except (KeyError, TypeError):
                    pass
        return result
    except Exception as e:
        print(f"[주가수집] 배치 오류: {e}")
        return {}


def collect_stock_prices():
    db: Session = SessionLocal()
    try:
        ensure_sectors_exist(db)
        ensure_stocks_exist(db)

        stocks = db.query(models.Stock).all()
        if not stocks:
            return

        end = datetime.utcnow()
        start = end - timedelta(days=90)
        start_str = start.strftime("%Y-%m-%d")
        end_str   = end.strftime("%Y-%m-%d")

        symbols   = [s.symbol for s in stocks]
        stock_map = {s.symbol: s for s in stocks}

        print(f"[주가수집] 총 {len(symbols)}개 종목 배치 수집 시작")

        BATCH = 100
        for i in range(0, len(symbols), BATCH):
            batch = symbols[i:i + BATCH]
            bn = i // BATCH + 1
            total_b = (len(symbols) + BATCH - 1) // BATCH
            print(f"[주가수집] 배치 {bn}/{total_b} ({len(batch)}개)")

            price_data = _fetch_prices_batch(batch, start_str, end_str)

            for symbol in batch:
                stock = stock_map[symbol]
                hist  = price_data.get(symbol)
                if hist is None or hist.empty:
                    continue
                try:
                    existing_dates = {
                        p.date.date()
                        for p in db.query(models.StockPrice)
                        .filter(models.StockPrice.stock_id == stock.id)
                        .all()
                    }
                    new_prices = []
                    for date_idx, row in hist.iterrows():
                        d = date_idx.to_pydatetime().replace(tzinfo=None)
                        if d.date() in existing_dates:
                            continue
                        close = row.get("Close")
                        if pd.isna(close):
                            continue
                        new_prices.append(models.StockPrice(
                            stock_id=stock.id,
                            date=d,
                            open=float(row.get("Open") or 0),
                            high=float(row.get("High") or 0),
                            low=float(row.get("Low") or 0),
                            close=float(close),
                            volume=int(row.get("Volume") or 0),
                        ))
                    if new_prices:
                        db.bulk_save_objects(new_prices)
                        db.commit()
                        print(f"[주가수집] {stock.name}: {len(new_prices)}건")
                except Exception as e:
                    db.rollback()
                    print(f"[주가수집] {symbol} 오류: {e}")

        print("[주가수집] 완료")
    except Exception as e:
        db.rollback()
        print(f"[주가수집] 전체 오류: {e}")
    finally:
        db.close()
