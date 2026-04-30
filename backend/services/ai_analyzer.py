from __future__ import annotations

import json
import logging
import re
import time
from typing import Any

from openai import OpenAI  # Gemini 대신 OpenAI 사용
from sqlalchemy.orm import Session

from config import settings
from database import SessionLocal
import models

HTML_TAG_RE = re.compile(r"<[^>]+>")
MULTISPACE_RE = re.compile(r"\s+")
NON_TEXT_RE = re.compile(r"[^\w\s가-힣.,!?%:/()-]")
JSON_BLOCK_RE = re.compile(r"\{.*\}", re.DOTALL)
MAX_CONTENT_LENGTH = 3000
MAX_SUMMARY_LENGTH = 300
RETRY_DELAYS = (1, 2)
LOW_INFO_MIN_LENGTH = 80
SHORT_ARTICLE_LENGTH = 180
MAX_STRONG_SCORE = 0.6
LOW_RELEVANCE_SCORE_CAP = 0.1
LOW_INFO_SUMMARY = "본문 정보가 부족해 중립적으로 처리했습니다."
LOW_RELEVANCE_SUMMARY = "투자 영향이 낮은 기사로 판단해 중립적으로 처리했습니다."
BATCH_LIMIT = 20

LOW_INFO_PATTERNS = (
    "기자명",
    "입력",
    "수정",
    "댓글 0",
    "공유하기",
    "기사검색",
    "로그인",
    "페이스북",
    "카카오톡",
    "url 복사",
    "글자크기",
    "구독 +",
)

LOW_RELEVANCE_PATTERNS = (
    "참배",
    "공모전",
    "행사",
    "사진",
    "출마",
    "기자회견",
    "방문",
    "개최",
)

logger = logging.getLogger(__name__)


def preprocess_news(title: str, content: str | None) -> str:
    merged = " ".join(part for part in [title, content or ""] if part)
    no_html = HTML_TAG_RE.sub(" ", merged)
    normalized = NON_TEXT_RE.sub(" ", no_html)
    clean_text = MULTISPACE_RE.sub(" ", normalized).strip()
    return clean_text[:MAX_CONTENT_LENGTH]


def build_analysis_prompt(news: models.News, sector_name: str) -> str:
    published_at_text = str(news.published_at) if news.published_at else ""
    content_text = preprocess_news(news.title or "", news.content or "")
    return f"""
너는 한국 주식 뉴스 감성 분석 AI다.
아래 뉴스를 읽고 투자 관점 기준의 감성 점수, 감성 라벨, 요약을 JSON 하나로만 반환하라.

목표:
- sentiment_score: -1.0 ~ 1.0 범위의 감성 점수
- sentiment_label: positive / negative / neutral 중 하나
- summary: 1~2문장 한국어 요약

규칙:
1. 감성 평가는 실제 투자자 관점에서 뉴스가 해당 섹터의 업황, 실적, 수주, 규제, 비용, 경쟁력에 미치는 영향을 기준으로 판단한다.
2. 단순 행사, 정치 일정, 사진 기사, 인사 기사, 정보 부족 기사라면 neutral에 가깝게 판단한다.
3. 기사 본문 정보가 부족하거나 제목만으로 판단해야 하는 경우 과도한 긍정/부정 해석을 하지 않는다.
4. 점수는 보수적으로 부여한다. 매우 강한 호재/악재가 명확하지 않다면 절대값을 크게 주지 않는다.
5. AI, 산업, 기술 키워드가 포함되어 있어도 실제 투자 영향이 약하면 neutral로 판단한다.
6. score가 0.15 초과면 positive, -0.15 미만이면 negative, 그 사이는 neutral에 가깝게 판단한다.
7. 요약은 기사 핵심 사실과 투자 관점을 함께 반영해 짧게 정리한다.
8. 설명문 없이 JSON 객체만 출력한다.

JSON 스키마:
{{
  "sentiment_score": float,
  "sentiment_label": "positive | negative | neutral",
  "summary": "string"
}}

섹터: {sector_name}
제목: {news.title}
본문: {content_text}
발행시각: {published_at_text}
""".strip()


def call_gpt(prompt: str, model: str = "gpt-4o-mini") -> dict[str, Any]:
    """Gemini 호출 함수를 GPT 호출 함수로 변경 (기존 구조 유지)"""
    if not settings.OPENAI_API_KEY:
        raise ValueError("OPENAI_API_KEY is not set.")

    client = OpenAI(api_key=settings.OPENAI_API_KEY)

    last_error: Exception | None = None
    for delay in (0, *RETRY_DELAYS):
        if delay:
            time.sleep(delay)
        try:
            # GPT 호출 방식으로 변경
            response = client.chat.completions.create(
                model=model,
                messages=[
                    {"role": "system", "content": "You are a helpful assistant that outputs JSON."},
                    {"role": "user", "content": prompt}
                ],
                temperature=0.2,
                response_format={"type": "json_object"}
            )
            # OpenAI 응답 구조에서 텍스트 추출
            raw_text = response.choices[0].message.content
            if not raw_text:
                raise ValueError("GPT response text is empty.")
            
            return parse_json_response(raw_text)
            
        except Exception as exc:
            last_error = exc
            logger.warning("GPT API request failed: %s", exc)
    else:
        raise ValueError(f"GPT API request failed after retries: {last_error}")


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
        return summary[:MAX_SUMMARY_LENGTH]
    return fallback_text[:MAX_SUMMARY_LENGTH] if fallback_text else "분석 완료"


def is_low_information_article(clean_text: str) -> bool:
    text_lower = clean_text.lower()
    if len(clean_text) < 120:
        return True

    pattern_hits = sum(pattern.lower() in text_lower for pattern in LOW_INFO_PATTERNS)
    if pattern_hits >= 2:
        return True

    return False


def is_low_relevance_article(title: str, clean_text: str) -> bool:
    combined = f"{title} {clean_text}".lower()
    return any(pattern.lower() in combined for pattern in LOW_RELEVANCE_PATTERNS)


def adjust_score(score: float, clean_text: str, low_relevance: bool) -> float:
    adjusted = score

    if len(clean_text) < SHORT_ARTICLE_LENGTH:
        adjusted *= 0.6

    if low_relevance:
        adjusted = max(min(adjusted, LOW_RELEVANCE_SCORE_CAP), -LOW_RELEVANCE_SCORE_CAP)

    adjusted = max(min(adjusted, MAX_STRONG_SCORE), -MAX_STRONG_SCORE)
    return round(adjusted, 3)


def heuristic_fallback_analysis(news: models.News, sector_name: str) -> tuple[float, str, str]:
    clean_text = preprocess_news(news.title or "", news.content or "")
    positive_tokens = ("상승", "호재", "확대", "성장", "개선", "수주", "실적")
    negative_tokens = ("하락", "악재", "우려", "축소", "부진", "적자", "충격")

    score = 0.0
    if any(token in clean_text for token in positive_tokens):
        score += 0.35
    if any(token in clean_text for token in negative_tokens):
        score -= 0.35

    if score > 0.15:
        label = "positive"
    elif score < -0.15:
        label = "negative"
    else:
        label = "neutral"

    summary = clean_text[:MAX_SUMMARY_LENGTH] if clean_text else f"{sector_name} 뉴스 분석 완료"
    return round(score, 3), label, summary


def analyze_news_item(news: models.News, sector_name: str) -> tuple[float, str, str]:
    clean_text = preprocess_news(news.title or "", news.content or "")
    if not clean_text:
        return 0.0, "neutral", "본문이 비어 있어 기본 분석 결과를 저장했습니다."
    if is_low_information_article(clean_text):
        return 0.0, "neutral", LOW_INFO_SUMMARY

    low_relevance = is_low_relevance_article(news.title or "", clean_text)
    if low_relevance:
        return 0.0, "neutral", LOW_RELEVANCE_SUMMARY

    prompt = build_analysis_prompt(news, sector_name)
    result = call_gpt(prompt)

    score = clamp(result.get("sentiment_score"), -1.0, 1.0, 0.0)
    score = adjust_score(score, clean_text, low_relevance=low_relevance)
    label = normalize_label(result.get("sentiment_label"), score)
    summary = normalize_summary(result.get("summary"), clean_text)
    return score, label, summary


def analyze_pending_news(limit: int = BATCH_LIMIT) -> int:
    db: Session = SessionLocal()
    processed_count = 0
    low_info_count = 0
    fallback_count = 0
    start_time = time.time()

    try:
        pending_news = (
            db.query(models.News)
            .filter((models.News.ai_summary.is_(None)) | (models.News.ai_summary == ""))
            .order_by(models.News.published_at.desc())
            .limit(limit)
            .all()
        )
        logger.info("[AI분석] 대상 뉴스 %s건 (limit=%s)", len(pending_news), limit)

        for news in pending_news:
            sector = db.query(models.Sector).filter(models.Sector.id == news.sector_id).first()
            sector_name = sector.name if sector else "일반"
            clean_text = preprocess_news(news.title or "", news.content or "")

            if not clean_text or is_low_information_article(clean_text):
                news.sentiment_score = 0.0
                news.sentiment_label = "neutral"
                news.ai_summary = LOW_INFO_SUMMARY
                try:
                    db.commit()
                    processed_count += 1
                    low_info_count += 1
                    logger.info("[AI분석] 저품질 기사 중립 처리 news_id=%s", news.id)
                except Exception as exc:
                    db.rollback()
                    logger.exception("[AI분석] 저품질 기사 저장 실패. news_id=%s error=%s", news.id, exc)
                continue

            try:
                score, label, summary = analyze_news_item(news, sector_name)
            except Exception as exc:
                logger.warning("[AI분석] GPT 분석 실패. 휴리스틱 fallback 사용. news_id=%s error=%s", news.id, exc)
                try:
                    score, label, summary = heuristic_fallback_analysis(news, sector_name)
                    fallback_count += 1
                except Exception as fallback_exc:
                    db.rollback()
                    logger.exception("[AI분석] fallback 분석도 실패했습니다. news_id=%s error=%s", news.id, fallback_exc)
                    continue

            try:
                news.sentiment_score = score
                news.sentiment_label = label
                news.ai_summary = summary
                db.commit()
                processed_count += 1
            except Exception as exc:
                db.rollback()
                logger.exception("[AI분석] DB 저장 실패. news_id=%s error=%s", news.id, exc)

        elapsed = round(time.time() - start_time, 2)
        logger.info(
            "[AI분석] 완료: 처리=%s건, 저품질중립=%s건, fallback=%s건, 소요=%s초",
            processed_count,
            low_info_count,
            fallback_count,
            elapsed,
        )
        return processed_count
    finally:
        db.close()
