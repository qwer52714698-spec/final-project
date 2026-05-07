from __future__ import annotations

import json
import logging
import re
import time
from dataclasses import dataclass, field
from datetime import datetime
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
    "댓글수",
    "공유하기",
    "기사공유하기",
    "기사검색",
    "로그인",
    "페이스북",
    "카카오톡",
    "url 복사",
    "url복사",
    "글자크기",
    "구독 +",
    "북마크",
    "프린트",
    "다른기사 보기",
    "기사스크랩하기",
    "등록순",
    "최신순",
    "추천순",
    "답글순",
    "본문 글씨",
    "광고문의",
    "제보",
    "회원가입",
    "정기구독자",
    "e book 보기",
    "바로가기",
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
    "예비후보",
    "포토뉴스",
    "어린이날",
    "축제",
    "학술대회",
    "문화제",
    "공청회",
    "시민단체",
    "저널리즘",
    "k 팝",
    "k-팝",
    "드라마",
    "전통 리듬",
)

INVESTMENT_SIGNAL_PATTERNS = (
    "실적",
    "영업익",
    "매출",
    "수주",
    "계약",
    "합병",
    "투자",
    "인수",
    "규제",
    "배당",
    "증설",
    "출시",
    "공급",
    "시장",
    "점유율",
    "수요",
    "가격",
    "원가",
    "정책",
    "가이던스",
    "성장",
    "적자",
    "흑자",
    "판결",
    "노조",
    "인플레이션",
    "금리",
)

EVENT_TYPE_CANDIDATES = (
    "earnings",
    "rates_inflation",
    "macro",
    "policy_regulation",
    "supply_contract",
    "mna_investment",
    "innovation_product",
    "labor_legal",
    "geopolitical",
    "other",
)

logger = logging.getLogger(__name__)


@dataclass
class AnalysisResult:
    news_id: int
    sentiment_score: float
    sentiment_label: str
    summary: str
    keywords: list[str] = field(default_factory=list)
    event_type: str | None = None
    impact_score: float | None = None
    created_at: datetime | None = None
    updated_at: datetime | None = None


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
- impact_score: 0.0 ~ 1.0 범위의 시장 영향도 점수
- event_type: 아래 후보 중 하나
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
9. impact_score는 감정 방향과 별개로, 해당 뉴스가 실제 시장/섹터/종목에 줄 수 있는 영향의 크기를 평가한다.
10. event_type은 다음 중 가장 가까운 하나만 고른다:
   earnings, rates_inflation, macro, policy_regulation, supply_contract, mna_investment, innovation_product, labor_legal, geopolitical, other

JSON 스키마:
{{
  "sentiment_score": float,
  "sentiment_label": "positive | negative | neutral",
  "impact_score": float,
  "event_type": "earnings | rates_inflation | macro | policy_regulation | supply_contract | mna_investment | innovation_product | labor_legal | geopolitical | other",
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


def normalize_event_type(value: Any, title: str, clean_text: str) -> str:
    event_type = str(value or "").strip().lower()
    if event_type in EVENT_TYPE_CANDIDATES:
        return event_type
    combined = f"{title} {clean_text}".lower()
    if any(token in combined for token in ("영업익", "매출", "실적", "흑자", "적자", "가이던스")):
        return "earnings"
    if any(token in combined for token in ("금리", "물가", "인플레이션", "cpi", "환율")):
        return "rates_inflation"
    if any(token in combined for token in ("노조", "파업", "업무방해", "부당노동행위", "법적 대응", "임금 미지급")):
        return "labor_legal"
    if any(token in combined for token in ("ai", "신제품", "출시", "플랫폼", "기술", "혁신", "자율주행", "반도체", "스마트카")):
        return "innovation_product"
    if any(token in combined for token in ("수주", "공급", "공급망", "계약", "공급 계약", "유통 계약", "사업 확대")):
        return "supply_contract"
    if any(token in combined for token in ("인수", "합병", "투자", "지분", "유치")):
        return "mna_investment"
    if any(token in combined for token in ("규제", "정책", "정부", "식약처", "대법원", "판결", "행정", "입법")):
        return "policy_regulation"
    if any(token in combined for token in ("전쟁", "리스크", "지정학", "중동", "수출 규제")):
        return "geopolitical"
    if any(token in combined for token in ("경기", "불황", "호황", "소비자물가", "성장세", "물가", "인플레")):
        return "macro"
    return "other"


def normalize_impact_score(value: Any, score: float, clean_text: str, event_type: str) -> float:
    impact = clamp(value, 0.0, 1.0, abs(score))
    if len(clean_text) < SHORT_ARTICLE_LENGTH:
        impact *= 0.8
    if event_type in {"earnings", "rates_inflation", "policy_regulation", "supply_contract", "geopolitical"}:
        impact += 0.1
    if event_type == "other":
        impact *= 0.8
    return round(max(0.0, min(impact, 1.0)), 3)


def build_low_info_result(news: models.News, clean_text: str) -> AnalysisResult:
    event_type = normalize_event_type(None, news.title or "", clean_text)
    base_impact_by_event = {
        "earnings": 0.35,
        "rates_inflation": 0.45,
        "macro": 0.3,
        "policy_regulation": 0.4,
        "supply_contract": 0.35,
        "mna_investment": 0.35,
        "innovation_product": 0.3,
        "labor_legal": 0.35,
        "geopolitical": 0.45,
        "other": 0.0,
    }

    combined = f"{news.title or ''} {clean_text}".lower()
    negative_signal_tokens = (
        "물가",
        "금리",
        "인플레",
        "노조",
        "판결",
        "반발",
        "제동",
        "하락",
        "우려",
        "악재",
        "부당노동행위",
        "임금 미지급",
        "규제",
        "리스크",
    )
    positive_signal_tokens = (
        "영업익",
        "매출",
        "흑자",
        "수주",
        "계약",
        "공급",
        "투자",
        "인수",
        "승인",
        "확대",
        "성장",
        "호조",
        "출시",
    )

    if event_type in {"rates_inflation", "labor_legal", "geopolitical"}:
        sentiment_score = -0.2
    elif event_type in {"earnings", "supply_contract", "mna_investment", "innovation_product"}:
        sentiment_score = 0.2
    elif event_type == "policy_regulation":
        sentiment_score = -0.1
    else:
        sentiment_score = 0.0

    if any(token in combined for token in positive_signal_tokens):
        sentiment_score = max(sentiment_score, 0.2)
    if any(token in combined for token in negative_signal_tokens):
        sentiment_score = min(sentiment_score, -0.2)

    sentiment_label = normalize_label(sentiment_score, sentiment_score)

    impact_score = base_impact_by_event.get(event_type, 0.0)
    if impact_score == 0.0:
        summary = LOW_INFO_SUMMARY
    else:
        summary = "본문 정보는 제한적이지만 제목 기준으로 약한 영향도를 추정했습니다."

    return _build_result(
        news,
        round(sentiment_score, 3),
        sentiment_label,
        summary,
        event_type=event_type,
        impact_score=impact_score,
    )


def is_low_information_article(clean_text: str) -> bool:
    text_lower = clean_text.lower()
    word_count = len(clean_text.split())
    if len(clean_text) < 80:
        return True

    pattern_hits = sum(pattern.lower() in text_lower for pattern in LOW_INFO_PATTERNS)
    if pattern_hits >= 3:
        return True

    if len(clean_text) < 140 and pattern_hits >= 2:
        return True

    if word_count < 18 and pattern_hits >= 2:
        return True

    if word_count < 10:
        return True

    return False


def is_low_relevance_article(title: str, clean_text: str) -> bool:
    combined = f"{title} {clean_text}".lower()
    has_low_relevance_signal = any(pattern.lower() in combined for pattern in LOW_RELEVANCE_PATTERNS)
    has_investment_signal = any(pattern.lower() in combined for pattern in INVESTMENT_SIGNAL_PATTERNS)

    if has_low_relevance_signal and not has_investment_signal:
        return True

    government_like_patterns = (
        "시장 예비후보",
        "군수",
        "도지사",
        "입법",
        "학회",
        "행사",
        "큰잔치",
    )
    if any(pattern in combined for pattern in government_like_patterns) and not has_investment_signal:
        return True

    culture_like_patterns = (
        "k-컬처",
        "k 팝",
        "공연",
        "팬 커뮤니티",
        "예술",
        "문화",
    )
    if any(pattern in combined for pattern in culture_like_patterns) and not has_investment_signal:
        return True

    return False


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


def _build_result(
    news: models.News,
    sentiment_score: float,
    sentiment_label: str,
    summary: str,
    *,
    keywords: list[str] | None = None,
    event_type: str | None = None,
    impact_score: float | None = None,
) -> AnalysisResult:
    now = datetime.utcnow()
    return AnalysisResult(
        news_id=news.id,
        sentiment_score=sentiment_score,
        sentiment_label=sentiment_label,
        summary=summary,
        keywords=keywords or [],
        event_type=event_type,
        impact_score=impact_score,
        created_at=now,
        updated_at=now,
    )


def analyze_news_result(news: models.News, sector_name: str) -> AnalysisResult:
    clean_text = preprocess_news(news.title or "", news.content or "")
    if not clean_text:
        return build_low_info_result(news, clean_text)
    if is_low_information_article(clean_text):
        return build_low_info_result(news, clean_text)

    low_relevance = is_low_relevance_article(news.title or "", clean_text)
    if low_relevance:
        return _build_result(news, 0.0, "neutral", LOW_RELEVANCE_SUMMARY, event_type="other", impact_score=0.05)

    prompt = build_analysis_prompt(news, sector_name)
    result = call_gpt(prompt)

    score = clamp(result.get("sentiment_score"), -1.0, 1.0, 0.0)
    score = adjust_score(score, clean_text, low_relevance=low_relevance)
    label = normalize_label(result.get("sentiment_label"), score)
    event_type = normalize_event_type(result.get("event_type"), news.title or "", clean_text)
    impact_score = normalize_impact_score(result.get("impact_score"), score, clean_text, event_type)
    summary = normalize_summary(result.get("summary"), clean_text)
    return _build_result(news, score, label, summary, event_type=event_type, impact_score=impact_score)


def analyze_news_item(news: models.News, sector_name: str) -> tuple[float, str, str]:
    result = analyze_news_result(news, sector_name)
    return result.sentiment_score, result.sentiment_label, result.summary


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
                analysis = build_low_info_result(news, clean_text)
                news.sentiment_score = analysis.sentiment_score
                news.sentiment_label = analysis.sentiment_label
                news.ai_summary = analysis.summary
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
                analysis = analyze_news_result(news, sector_name)
            except Exception as exc:
                logger.warning("[AI분석] GPT 분석 실패. 휴리스틱 fallback 사용. news_id=%s error=%s", news.id, exc)
                try:
                    score, label, summary = heuristic_fallback_analysis(news, sector_name)
                    event_type = normalize_event_type(None, news.title or "", clean_text)
                    impact_score = normalize_impact_score(None, score, clean_text, event_type)
                    analysis = _build_result(
                        news,
                        score,
                        label,
                        summary,
                        event_type=event_type,
                        impact_score=impact_score,
                    )
                    fallback_count += 1
                except Exception as fallback_exc:
                    db.rollback()
                    logger.exception("[AI분석] fallback 분석도 실패했습니다. news_id=%s error=%s", news.id, fallback_exc)
                    continue

            try:
                news.sentiment_score = analysis.sentiment_score
                news.sentiment_label = analysis.sentiment_label
                news.ai_summary = analysis.summary
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
