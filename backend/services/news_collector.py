import requests
import re
from bs4 import BeautifulSoup
from datetime import datetime
from sqlalchemy.orm import Session
from database import SessionLocal
from config import settings
import models

# ✨ 조장님이 알려주신 AI 분석 엔진 가져오기
from services.ai_analyzer import analyze_news_item

SECTOR_KEYWORDS = {
    "반도체": ["반도체", "삼성전자", "SK하이닉스", "메모리"],
    "2차전지": ["2차전지", "배터리", "LG에너지솔루션", "삼성SDI", "전기차 배터리"],
    "자동차": ["현대차", "기아차", "자동차", "전기차"],
    "AI/IT": ["인공지능", "AI", "NAVER", "카카오", "IT"],
    "바이오/제약": ["바이오", "제약", "신약", "임상시험"],
    "금융": ["금융", "은행", "증권", "보험", "금리"],
    "에너지/화학": ["정유", "화학", "에너지", "유가", "LG화학"],
    "산업재": ["건설", "철강", "조선", "기계", "포스코"],
    "소비재": ["유통", "식품", "소비", "유통업", "이마트"],
}

def strip_html(text: str) -> str:
    return re.sub(r"<[^>]+>", "", text).strip()

def parse_naver_date(date_str: str) -> datetime:
    try:
        return datetime.strptime(date_str, "%a, %d %b %Y %H:%M:%S %z").replace(tzinfo=None)
    except Exception:
        return datetime.utcnow()

def fetch_article_content(url: str) -> str:
    try:
        resp = requests.get(url, timeout=5, headers={"User-Agent": "Mozilla/5.0"})
        soup = BeautifulSoup(resp.text, "html.parser")
        article = soup.find("article") or soup.find(id="newsct_article") or soup.find(class_="article_body")
        if article:
            return article.get_text(separator=" ", strip=True)[:2000]
    except Exception:
        pass
    return ""

def collect_news_for_sector(sector_id: int, sector_name: str):
    if not settings.NAVER_CLIENT_ID or not settings.NAVER_CLIENT_SECRET:
        print(f"[뉴스수집] Naver API 키가 설정되지 않았습니다. 섹터: {sector_name}")
        return

    keywords = SECTOR_KEYWORDS.get(sector_name, [sector_name])
    db: Session = SessionLocal()
    
    try:
        for keyword in keywords[:2]: # 섹터당 상위 2개 키워드만 사용 (API 할당량 고려)
            params = {"query": keyword, "display": 10, "sort": "date"}
            headers = {
                "X-Naver-Client-Id": settings.NAVER_CLIENT_ID,
                "X-Naver-Client-Secret": settings.NAVER_CLIENT_SECRET,
            }
            try:
                resp = requests.get(
                    "https://openapi.naver.com/v1/search/news.json",
                    params=params,
                    headers=headers,
                    timeout=10,
                )
                data = resp.json()
            except Exception as e:
                print(f"[뉴스수집] API 요청 실패: {e}")
                continue

            for item in data.get("items", []):
                url = item.get("originallink") or item.get("link", "")
                if not url or db.query(models.News).filter(models.News.url == url).first():
                    continue

                title = strip_html(item.get("title", ""))
                description = strip_html(item.get("description", ""))
                content = fetch_article_content(url) or description
                published_at = parse_naver_date(item.get("pubDate", ""))

                # 🚀 [AI분석 통합] 저장하기 전 GPT-4o-mini로 분석 수행
                try:
                    # 분석을 위해 임시 News 객체 생성 (DB 저장 전 데이터 전달용)
                    temp_news = models.News(title=title, content=content, published_at=published_at, sector_id=sector_id)
                    
                    print(f"[AI분석 중] {title[:25]}...")
                    score, label, summary = analyze_news_item(temp_news, sector_name)
                    
                    # 분석 결과와 함께 최종 저장
                    new_news = models.News(
                        sector_id=sector_id,
                        title=title,
                        content=content,
                        url=url,
                        published_at=published_at,
                        sentiment_score=score,
                        sentiment_label=label,
                        ai_summary=summary
                    )
                    db.add(new_news)
                    db.commit()
                except Exception as e:
                    print(f"[분석/저장 오류] {e}")
                    db.rollback()
                    
        print(f"[뉴스수집 완료] {sector_name}")
    finally:
        db.close()

def collect_all_news():
    db: Session = SessionLocal()
    total_collected = 0  # 📊 오늘 수집한 총 개수 카운터 추가
    
    try:
        sectors = db.query(models.Sector).all()
        sector_list = [(s.id, s.name) for s in sectors]
    finally:
        db.close()

    for sector_id, sector_name in sector_list:
        # 각 섹터별로 몇 개 수집했는지 반환받도록 로직을 살짝 수정해야 하지만,
        # 일단 전체 DB 조회를 통해 오늘 날짜 데이터를 세는 방식이 가장 정확합니다.
        collect_news_for_sector(sector_id, sector_name)

    # 🏁 최종 결과 집계 (오늘 날짜로 저장된 뉴스 개수 확인)
    db = SessionLocal()
    today_count = db.query(models.News).filter(
        models.News.published_at >= datetime.utcnow().replace(hour=0, minute=0, second=0, microsecond=0)
    ).count()
    db.close()

    print(f"\n==========================================")
    print(f"✅ 모든 섹터 뉴스 수집 및 분석 완료!")
    print(f"📊 오늘 신규 수집된 뉴스: 총 {today_count}개")
    print(f"==========================================")

    # 📝 깃허브 Actions에서 읽을 수 있게 파일로 기록 (이게 핵심!)
    with open("collect_result.txt", "w") as f:
        f.write(str(today_count))

if __name__ == "__main__":
    print("🚀 뉴스 수집 및 GPT-4o-mini 분석 엔진 가동...")
    collect_all_news()