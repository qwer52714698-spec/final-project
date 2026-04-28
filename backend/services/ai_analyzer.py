from __future__ import annotations

import json
import re
from typing import Any

import requests
from sqlalchemy.orm import Session

from config import settings
from database import SessionLocal
import models

HTML_TAG_RE = re.compile(r"<[^>]+>")
MULTISPACE_RE = re.compile(r"\s+")
NON_TEXT_RE = re.compile(r"[^\w\s가-힣.,!?%:/()-]")
JSON_BLOCK_RE = re.compile(r"\{.*\}", re.DOTALL)


def preprocess_news(title: str, content: str | None) -> str:
    merged = " ".join(part for part in [title, content or ""] if part)
    no_html = HTML_TAG_RE.sub(" ", merged)
    normalized = NON_TEXT_RE.sub(" ", no_html)
    return MULTISPACE_RE.sub(" ", normalized).strip()


def build_analysis_prompt(news: models.News, sector_name: str) -> str:
    published_at_text = str(news.published_at) if news.published_at else ""
    return f"""
너는 한국 주식 뉴스 감성 분석 AI다.
아래 뉴스를 읽고 감성 점수, 감성 라벨, 요약을 JSON 하나로만 반환하라.

목표:
- sentiment_score: -1.0 ~ 1.0 범위의 감성 점수
- sentiment_label: positive / negative / neutral 중 하나
- summary: 1~2문장 한국어 요약

규칙:
1. 감성 평가는 실제 투자자 관점에서 뉴스가 해당 섹터에 미치는 영향을 기준으로 판단한다.
2. score가 0.15 초과면 positive, -0.15 미만이면 negative, 그 사이는 neutral에 가깝게 판단한다.
3. 요약은 핵심 사실과 시장 의미를 짧게 정리한다.
4. 설명문 없이 JSON 객체만 출력한다.

JSON 스키마:
{{
  "sentiment_score": float,
  "sentiment_label": "positive | negative | neutral",
  "summary": "string"
}}

섹터: {sector_name}
제목: {news.title}
본문: {news.content or ""}
발행시각: {published_at_text}
""".strip()


def call_gemini(prompt: str, model: str = "gemini-1.5-flash") -> dict[str, Any]:
    if not settings.GEMINI_API_KEY:
        raise ValueError("GEMINI_API_KEY is not set.")

    url = (
        f"https://generativelanguage.googleapis.com/v1beta/models/"
        f"{model}:generateContent?key={settings.GEMINI_API_KEY}"
    )
    payload = {
        "contents": [
            {
                "parts": [
                    {"text": prompt}
                ]
            }
        ],
        "generationConfig": {
            "temperature": 0.2,
            "responseMimeType": "application/json",
        },
    }

    response = requests.post(url, json=payload, timeout=30)
    response.raise_for_status()
    data = response.json()

    candidates = data.get("candidates", [])
    if not candidates:
        raise ValueError("Gemini response has no candidates.")

    parts = candidates[0].get("content", {}).get("parts", [])
    raw_text = "".join(part.get("text", "") for part in parts if isinstance(part, dict)).strip()
    if not raw_text:
        raise ValueError("Gemini response text is empty.")

    return parse_json_response(raw_text)


def parse_json_response(raw_text: str) -> dict[str, Any]:
    try:
        return json.loads(raw_text)
    except json.JSONDecodeError:
        match = JSON_BLOCK_RE.search(raw_text)
        if not match:
            raise ValueError("Failed to parse JSON from model response.")
        return json.loads(match.group(0))


def clamp(value: Any, minimum: float, maximum: float, default: float) -> float:
    try:
        numeric = float(value)
    except (TypeError, ValueError):
        return default
    return max(min(numeric, maximum), minimum)


def normalize_label(value: Any, score: float) -> str:
    label = str(value or "").strip().lower()
    if label in {"positive", "negative", "neutral"}:
        return label
    if score > 0.15:
        return "positive"
    if score < -0.15:
        return "negative"
    return "neutral"


def normalize_summary(value: Any, fallback_text: str) -> str:
    summary = str(value or "").strip()
    if summary:
        return summary
    return fallback_text[:200] if fallback_text else "분석 완료"


def analyze_news_item(news: models.News, sector_name: str) -> tuple[float, str, str]:
    clean_text = preprocess_news(news.title or "", news.content or "")
    prompt = build_analysis_prompt(news, sector_name)
    result = call_gemini(prompt)

    score = clamp(result.get("sentiment_score"), -1.0, 1.0, 0.0)
    label = normalize_label(result.get("sentiment_label"), score)
    summary = normalize_summary(result.get("summary"), clean_text)
    return score, label, summary


def analyze_pending_news(limit: int = 50) -> int:
    db: Session = SessionLocal()
    processed_count = 0

    try:
        pending_news = (
            db.query(models.News)
            .filter(models.News.ai_summary.is_(None))
            .order_by(models.News.published_at.desc())
            .limit(limit)
            .all()
        )

        for news in pending_news:
            sector = db.query(models.Sector).filter(models.Sector.id == news.sector_id).first()
            sector_name = sector.name if sector else "일반"

            try:
                score, label, summary = analyze_news_item(news, sector_name)
                news.sentiment_score = score
                news.sentiment_label = label
                news.ai_summary = summary
                db.commit()
                processed_count += 1
            except Exception as exc:
                db.rollback()
                print(f"[AI분석] 뉴스 ID {news.id} 처리 실패: {exc}")

        return processed_count
    finally:
        db.close()
