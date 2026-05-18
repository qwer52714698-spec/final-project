from sqlalchemy.orm import Session
from sqlalchemy import func
import models, schemas
import json
import re
from datetime import datetime
from collections import defaultdict

MANUAL_STOCK_ALIASES = {
    "005930": ["삼성전자", "삼전"],
    "000660": ["sk하이닉스", "하이닉스"],
    "373220": ["lg에너지솔루션", "lg엔솔", "lg energy solution"],
    "006400": ["삼성sdi", "sdi"],
    "096770": ["sk이노베이션", "sk이노", "sk innovation"],
    "247540": ["에코프로비엠", "에코비엠", "ecopro bm"],
    "086520": ["에코프로", "ecopro"],
    "003670": ["포스코퓨처엠", "포퓨", "posco future m"],
    "020150": ["롯데에너지머티리얼즈", "롯데머티", "에너지머티리얼즈"],
    "010060": ["oci홀딩스", "oci"],
    "298050": ["효성첨단소재", "효첨"],
    "035420": ["naver", "네이버"],
    "035720": ["카카오"],
    "323410": ["카카오뱅크", "카뱅"],
    "005380": ["현대차", "현대자동차"],
    "000270": ["기아"],
    "012330": ["현대모비스", "모비스"],
    "204320": ["hl만도", "만도"],
    "086280": ["현대글로비스", "글로비스"],
    "018880": ["한온시스템", "한온"],
    "307950": ["현대오토에버", "오토에버"],
    "084370": ["한국타이어앤테크놀로지", "한국타이어", "한타"],
    "068270": ["셀트리온"],
    "259960": ["크래프톤", "krafton"],
    "251270": ["넷마블", "netmarble"],
    "018260": ["삼성sds", "sds", "삼성에스디에스"],
    "017670": ["sk텔레콤", "skt", "sk telecom"],
    "030200": ["kt", "케이티"],
    "036570": ["엔씨소프트", "엔씨", "nc소프트", "ncsoft"],
    "051910": ["lg화학", "lg chem"],
    "207940": ["삼성바이오로직스", "삼바", "samsung biologics"],
    "071050": ["한국금융지주", "한국금융", "한금지"],
    "091990": ["셀트리온헬스케어", "셀헬", "celltrion healthcare"],
    "120110": ["코오롱인더", "코오롱인더스트리", "kolon industries"],
    "139130": ["dgb금융지주", "dgb금융", "디지비금융"],
    "005490": ["posco홀딩스", "포스코홀딩스", "포홀", "posco"],
    "034020": ["두산에너빌리티", "두산에너빌", "에너빌"],
    "012450": ["한화에어로스페이스", "한화에어로"],
    "047810": ["한국항공우주", "kai", "한국항공우주산업"],
    "010140": ["삼성중공업", "삼중"],
    "023530": ["롯데쇼핑", "롯쇼"],
    "097950": ["cj제일제당", "cj제당"],
    "004370": ["농심", "nongshim"],
    "033780": ["kt&g", "케이티앤지"],
    "090430": ["아모레퍼시픽", "아모레"],
    "051900": ["lg생활건강", "lg생건", "엘지생활건강"],
    "005300": ["롯데칠성", "롯칠"],
    "271560": ["오리온", "orion"],
    "003230": ["삼양식품", "삼양"],
    "008770": ["호텔신라", "신라호텔"],
    "069960": ["현대백화점", "현백"],
}

# 1. 뉴스 데이터 저장 (팀원들의 models.News 구조에 맞게 수정)
def create_news_with_analysis(db: Session, news_data: dict, analysis_result):
    """
    팀원들의 News 모델은 sector_id(숫자)를 사용하며, 
    summary 대신 ai_summary라는 컬럼명을 사용합니다.
    """
    db_news = models.News(
        title=news_data.get("title"),
        content=news_data.get("content"),
        url=news_data.get("url"),
        published_at=news_data.get("published_at"),
        
        # 팀원들의 models.News 컬럼명에 맞게 매핑
        sector_id=news_data.get("sector_id"),  # 이제는 글자가 아니라 숫자 ID를 넣어야 함
        sentiment_label=analysis_result.get("sentiment_label"),
        sentiment_score=analysis_result.get("sentiment_score"),
        ai_summary=analysis_result.get("summary"), # summary -> ai_summary로 변경됨
    )
    
    db.add(db_news)
    db.commit()
    db.refresh(db_news)
    return db_news

# 2. 최신 뉴스 목록 조회
def get_news_list(db: Session, skip: int = 0, limit: int = 10):
    return db.query(models.News).order_by(models.News.published_at.desc()).offset(skip).limit(limit).all()

# 3. 특정 섹터별 뉴스 모아보기 (ID 기반 조회로 변경)
def get_news_by_sector(db: Session, sector_id: int):
    return db.query(models.News).filter(models.News.sector_id == sector_id).all()

# 4. 섹터별 통계 가져오기 (팀원들 news.py에서 활용하던 로직)
def get_sector_stats(db: Session):
    return db.query(
        models.Sector.name,
        func.count(models.News.id).label("news_count"),
        func.avg(models.News.sentiment_score).label("avg_sentiment")
    ).join(models.News).group_by(models.Sector.name).all()


def _normalize_text(text: str) -> str:
    return re.sub(r"\s+", " ", (text or "").strip().lower())


def _build_stock_aliases(stock: models.Stock) -> list[str]:
    aliases = [stock.symbol.lower()]
    if "." in stock.symbol:
        aliases.append(stock.symbol.split(".")[0].lower())
    if stock.name:
        aliases.append(stock.name.lower())
        aliases.append(stock.name.lower().replace(" ", ""))
    aliases.extend(MANUAL_STOCK_ALIASES.get(stock.symbol, []))
    if "." in stock.symbol:
        aliases.extend(MANUAL_STOCK_ALIASES.get(stock.symbol.split(".")[0], []))
    return [alias.lower() for alias in aliases if alias]


def match_related_stocks(
    db: Session,
    title: str,
    content: str | None = None,
    sector_id: int | None = None,
) -> list[schemas.StockNewsMatch]:
    combined_text = _normalize_text(f"{title or ''} {content or ''}")
    def _match_from_stocks(stocks: list[models.Stock]) -> list[schemas.StockNewsMatch]:
        matches: list[schemas.StockNewsMatch] = []
        for stock in stocks:
            aliases = _build_stock_aliases(stock)
            match_type = None
            confidence = 0.0

            for alias in aliases:
                if alias and alias in combined_text:
                    normalized_name = stock.name.lower() if stock.name else ""
                    normalized_name_no_space = normalized_name.replace(" ", "")
                    normalized_symbol = stock.symbol.lower()
                    normalized_symbol_no_suffix = normalized_symbol.split(".")[0]

                    if stock.name and alias in {normalized_name, normalized_name_no_space}:
                        match_type = "name"
                        confidence = 0.95
                        break
                    if alias in {normalized_symbol, normalized_symbol_no_suffix}:
                        match_type = "symbol"
                        confidence = 0.9
                        break
                    match_type = "alias"
                    confidence = max(confidence, 0.8)

            if match_type:
                matches.append(
                    schemas.StockNewsMatch(
                        stock_id=stock.id,
                        symbol=stock.symbol,
                        stock_name=stock.name,
                        match_type=match_type,
                        confidence=confidence,
                    )
                )
        return matches

    sector_stocks = db.query(models.Stock).filter(models.Stock.sector_id == sector_id).all() if sector_id else []
    matches = _match_from_stocks(sector_stocks) if sector_stocks else []

    if not matches:
        all_stocks = db.query(models.Stock).all()
        matches = _match_from_stocks(all_stocks)

    matches.sort(key=lambda item: (-item.confidence, item.stock_id))
    return matches


def build_daily_stock_news_features(
    db: Session,
    stock_id: int,
    start_date: datetime,
    end_date: datetime,
) -> list[schemas.DailyStockNewsFeature]:
    from services.ai_analyzer import build_news_signal_metadata

    stock = db.query(models.Stock).filter(models.Stock.id == stock_id).first()
    if not stock:
        return []

    news_items = (
        db.query(models.News)
        .join(models.NewsStockMap, models.NewsStockMap.news_id == models.News.id)
        .filter(
            models.NewsStockMap.stock_id == stock_id,
            models.News.published_at >= start_date,
            models.News.published_at <= end_date,
        )
        .order_by(models.News.published_at.asc())
        .all()
    )

    grouped: dict[datetime, list[models.News]] = defaultdict(list)
    for news in news_items:
        grouped[news.published_at.date()].append(news)

    results: list[schemas.DailyStockNewsFeature] = []
    for date_key, items in sorted(grouped.items()):
        scores = [float(item.sentiment_score or 0.0) for item in items]
        signal_meta = [build_news_signal_metadata(item) for item in items]
        impact_scores = [float(meta.get("impact_score", 0.0) or 0.0) for meta in signal_meta]
        positive_count = sum(1 for item in items if item.sentiment_label == "positive")
        negative_count = sum(1 for item in items if item.sentiment_label == "negative")
        neutral_count = sum(1 for item in items if item.sentiment_label == "neutral")
        event_type_counts: dict[str, int] = defaultdict(int)

        for meta in signal_meta:
            event_type = str(meta.get("event_type") or "other")
            event_type_counts[event_type] += 1

        results.append(
            schemas.DailyStockNewsFeature(
                date=datetime.combine(date_key, datetime.min.time()),
                stock_id=stock_id,
                news_count=len(items),
                avg_sentiment_score=round(sum(scores) / len(scores), 3) if scores else 0.0,
                avg_impact_score=round(sum(impact_scores) / len(impact_scores), 3) if impact_scores else 0.0,
                positive_count=positive_count,
                negative_count=negative_count,
                neutral_count=neutral_count,
                event_type_counts=dict(event_type_counts),
            )
        )

    return results


def sync_news_stock_matches(
    db: Session,
    news_id: int,
    title: str,
    content: str | None = None,
    sector_id: int | None = None,
) -> list[models.NewsStockMap]:
    matches = match_related_stocks(db, title=title, content=content, sector_id=sector_id)

    db.query(models.NewsStockMap).filter(models.NewsStockMap.news_id == news_id).delete()
    db.flush()

    rows: list[models.NewsStockMap] = []
    for match in matches:
        row = models.NewsStockMap(
            news_id=news_id,
            stock_id=match.stock_id,
            match_type=match.match_type,
            confidence=match.confidence,
        )
        db.add(row)
        rows.append(row)

    db.flush()
    return rows


def rebuild_daily_stock_news_features(
    db: Session,
    stock_id: int,
    start_date: datetime,
    end_date: datetime,
) -> list[models.DailyStockNewsFeature]:
    stock = db.query(models.Stock).filter(models.Stock.id == stock_id).first()
    stock_label = stock.symbol if stock else str(stock_id)
    print(f"🧱 [종목 집계] 시작 stock={stock_label}")

    daily_rows = build_daily_stock_news_features(db, stock_id, start_date, end_date)
    print(f"🧱 [종목 집계] 계산 완료 stock={stock_label}, 일자 {len(daily_rows)}건")

    db.query(models.DailyStockNewsFeature).filter(
        models.DailyStockNewsFeature.stock_id == stock_id,
        models.DailyStockNewsFeature.date >= start_date.date(),
        models.DailyStockNewsFeature.date <= end_date.date(),
    ).delete()
    db.flush()

    saved_rows: list[models.DailyStockNewsFeature] = []
    for item in daily_rows:
        counts = item.event_type_counts or {}
        row = models.DailyStockNewsFeature(
            stock_id=stock_id,
            date=item.date.date(),
            news_count=item.news_count,
            avg_sentiment_score=item.avg_sentiment_score,
            avg_impact_score=item.avg_impact_score,
            positive_count=item.positive_count,
            negative_count=item.negative_count,
            neutral_count=item.neutral_count,
            earnings_count=counts.get("earnings", 0),
            policy_regulation_count=counts.get("policy_regulation", 0),
            supply_contract_count=counts.get("supply_contract", 0),
            labor_legal_count=counts.get("labor_legal", 0),
        )
        db.add(row)
        saved_rows.append(row)

    db.flush()
    print(f"🧱 [종목 집계] 저장 완료 stock={stock_label}, 저장 행 {len(saved_rows)}건")
    return saved_rows


def get_stored_daily_stock_news_features(
    db: Session,
    stock_id: int,
    start_date: datetime,
    end_date: datetime,
) -> list[models.DailyStockNewsFeature]:
    return (
        db.query(models.DailyStockNewsFeature)
        .filter(
            models.DailyStockNewsFeature.stock_id == stock_id,
            models.DailyStockNewsFeature.date >= start_date.date(),
            models.DailyStockNewsFeature.date <= end_date.date(),
        )
        .order_by(models.DailyStockNewsFeature.date.asc())
        .all()
    )


def refresh_news_feature_store(
    db: Session,
    start_date: datetime,
    end_date: datetime,
) -> dict[str, int]:
    print(
        f"🧩 [뉴스 feature] 집계 시작 "
        f"({start_date.strftime('%Y-%m-%d')} ~ {end_date.strftime('%Y-%m-%d')})"
    )
    news_items = (
        db.query(models.News)
        .filter(
            models.News.published_at >= start_date,
            models.News.published_at <= end_date,
        )
        .order_by(models.News.published_at.asc())
        .all()
    )
    print(f"🧩 [뉴스 feature] 대상 뉴스 {len(news_items)}건")

    affected_stock_ids: set[int] = set()
    for index, news in enumerate(news_items, start=1):
        matches = sync_news_stock_matches(
            db,
            news_id=news.id,
            title=news.title,
            content=news.content,
            sector_id=news.sector_id,
        )
        for match in matches:
            affected_stock_ids.add(match.stock_id)

        if index % 50 == 0 or index == len(news_items):
            print(
                f"🧩 [뉴스 feature] 뉴스 매핑 진행 "
                f"{index}/{len(news_items)}건, 누적 종목 {len(affected_stock_ids)}개"
            )

    rebuilt_rows = 0
    stock_ids = sorted(affected_stock_ids)
    print(f"🧩 [뉴스 feature] 집계 대상 종목 {len(stock_ids)}개")
    for index, stock_id in enumerate(stock_ids, start=1):
        rebuilt_rows += len(rebuild_daily_stock_news_features(db, stock_id, start_date, end_date))
        if index % 20 == 0 or index == len(stock_ids):
            print(
                f"🧩 [뉴스 feature] 종목 집계 진행 "
                f"{index}/{len(stock_ids)}개, 누적 행 {rebuilt_rows}건"
            )

    db.commit()
    print(
        f"🧩 [뉴스 feature] 집계 완료 "
        f"(뉴스 {len(news_items)}건, 종목 {len(affected_stock_ids)}개, 행 {rebuilt_rows}건)"
    )
    return {
        "news_count": len(news_items),
        "matched_stock_count": len(affected_stock_ids),
        "daily_feature_rows": rebuilt_rows,
    }


def get_news_feature_coverage(
    db: Session,
    zero_only: bool = False,
    limit: int = 50,
) -> list[schemas.NewsFeatureCoverageItem]:
    map_counts = dict(
        db.query(
            models.NewsStockMap.stock_id,
            func.count(models.NewsStockMap.id),
        )
        .group_by(models.NewsStockMap.stock_id)
        .all()
    )
    daily_counts = dict(
        db.query(
            models.DailyStockNewsFeature.stock_id,
            func.count(models.DailyStockNewsFeature.id),
        )
        .group_by(models.DailyStockNewsFeature.stock_id)
        .all()
    )

    stocks = db.query(models.Stock).order_by(models.Stock.symbol.asc()).all()
    items: list[schemas.NewsFeatureCoverageItem] = []
    for stock in stocks:
        if stock.name and stock.name.startswith("Stock_"):
            continue
        map_count = int(map_counts.get(stock.id, 0) or 0)
        daily_count = int(daily_counts.get(stock.id, 0) or 0)
        has_coverage = map_count > 0 and daily_count > 0
        if zero_only and has_coverage:
            continue

        items.append(
            schemas.NewsFeatureCoverageItem(
                stock_id=stock.id,
                symbol=stock.symbol,
                stock_name=stock.name,
                sector_id=stock.sector_id,
                news_stock_map_count=map_count,
                daily_feature_count=daily_count,
                has_coverage=has_coverage,
            )
        )

    items.sort(
        key=lambda item: (
            item.has_coverage,
            item.daily_feature_count,
            item.news_stock_map_count,
            item.symbol,
        )
    )
    return items[:limit]
