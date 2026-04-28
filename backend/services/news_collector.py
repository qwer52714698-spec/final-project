import requests
import re
from bs4 import BeautifulSoup
from datetime import datetime
from sqlalchemy.orm import Session
from database import SessionLocal
from config import settings
import models

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
        for keyword in keywords[:2]:
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
                if not url:
                    continue
                if db.query(models.News).filter(models.News.url == url).first():
                    continue

                title = strip_html(item.get("title", ""))
                description = strip_html(item.get("description", ""))
                content = fetch_article_content(url) or description
                published_at = parse_naver_date(item.get("pubDate", ""))

                try:
                    news = models.News(
                        sector_id=sector_id,
                        title=title,
                        content=content,
                        url=url,
                        published_at=published_at,
                    )
                    db.add(news)
                    db.commit()
                except Exception:
                    db.rollback()
        print(f"[뉴스수집] {sector_name} 완료")
    except Exception as e:
        db.rollback()
        print(f"[뉴스수집] 오류: {e}")
    finally:
        db.close()


def collect_all_news():
    db: Session = SessionLocal()
    try:
        sectors = db.query(models.Sector).all()
        sector_list = [(s.id, s.name) for s in sectors]
    finally:
        db.close()

    for sector_id, sector_name in sector_list:
        collect_news_for_sector(sector_id, sector_name)
