import sys
import os
import requests
import re
from bs4 import BeautifulSoup
from datetime import datetime
from sqlalchemy.orm import Session
from database import SessionLocal
from config import settings
import models
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
        headers = {
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
        }
        resp = requests.get(url, timeout=10, headers=headers)
        if resp.status_code != 200:
            return ""
        soup = BeautifulSoup(resp.text, "html.parser")
        
        selectors = [
            "#newsct_article",
            "#articleBodyContents",
            "#articleBody",
            ".article_body",
            "article",
            "#articeBody",
            "[font=paragraph]"
        ]
        
        for selector in selectors:
            article = soup.select_one(selector)
            if article:
                for element in article(["script", "style", "iframe", "button", "a"]):
                    element.extract()
                content = article.get_text(separator=" ", strip=True)
                if len(content) > 100:
                    return " ".join(content.split())[:2000]
                    
        if soup.body:
            body_text = soup.body.get_text()
            lines = [line.strip() for line in body_text.splitlines() if len(line.strip()) > 30]
            fallback = " ".join(lines)
            if len(fallback) > 100:
                return " ".join(fallback.split())[:2000]
    except Exception:
        pass
    return ""

def collect_news_for_sector(sector_id: int, sector_name: str):
    if not settings.NAVER_CLIENT_ID or not settings.NAVER_CLIENT_SECRET:
        print(f"[News Collection] Naver API Key is not set. Sector: {sector_name}")
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
                print(f"[News Collection] API Request Failed: {e}")
                continue

            for item in data.get("items", []):
                url = item.get("originallink") or item.get("link", "")
                if not url or db.query(models.News).filter(models.News.url == url).first():
                    continue

                title = strip_html(item.get("title", ""))
                description = strip_html(item.get("description", ""))
                content = fetch_article_content(url)
                if not content or len(content) < 50:
                    content = description
                    
                published_at = parse_naver_date(item.get("pubDate", ""))

                try:
                    temp_news = models.News(title=title, content=content, published_at=published_at, sector_id=sector_id)
                    print(f"[AI Analyzing] {title[:25]}...")
                    score, label, summary = analyze_news_item(temp_news, sector_name)
                    
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
                    print(f"[Analysis/Save Error] {e}")
                    db.rollback()
                    
        print(f"[News Collection Completed] {sector_name}")
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

    db = SessionLocal()
    today_count = db.query(models.News).filter(
        models.News.published_at >= datetime.utcnow().replace(hour=0, minute=0, second=0, microsecond=0)
    ).count()
    db.close()

    print("\n==========================================")
    print("All Sector News Collection and Analysis Completed")
    print(f"Today Newly Collected News: Total {today_count}")
    print("==========================================")

    with open("collect_result.txt", "w") as f:
        f.write(str(today_count))

if __name__ == "__main__":
    print("Starting News Collection and GPT-4o-mini Analysis Engine...")
    collect_all_news()