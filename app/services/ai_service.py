from __future__ import annotations

import json
import os
import re
from dataclasses import asdict, dataclass
from datetime import datetime, timezone
from typing import Any

from dotenv import load_dotenv
from openai import OpenAI

load_dotenv()

HTML_TAG_RE = re.compile(r"<[^>]+>")
MULTISPACE_RE = re.compile(r"\s+")
NON_TEXT_RE = re.compile(r"[^\w\s가-힣.,!?%:/()-]")

SECTOR_CANDIDATES = [
    "반도체",
    "AI",
    "자동차",
    "2차전지",
    "금융",
    "바이오",
    "플랫폼",
    "에너지",
    "통신",
    "유통",
    "기타",
]

EVENT_TYPE_CANDIDATES = [
    "실적발표",
    "투자확대",
    "금리인상",
    "금리인하",
    "정책발표",
    "계약체결",
    "규제",
    "인수합병",
    "신제품출시",
    "수요증가",
    "공급차질",
    "기타",
]


@dataclass
class AnalysisResult:
    news_id: int | None
    sentiment_label: str
    sentiment_score: float
    keywords: list[str]
    sector: str
    event_type: str
    importance_score: float
    freshness_score: float
    impact_score: float
    summary: str
    created_at: str

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)

    def to_db_payload(self) -> dict[str, Any]:
        payload = self.to_dict()
        payload["keywords"] = json.dumps(self.keywords, ensure_ascii=False)
        return payload


def preprocess_news(title: str, content: str | None) -> str:
    merged = " ".join(part for part in [title, content or ""] if part)
    no_html = HTML_TAG_RE.sub(" ", merged)
    normalized = NON_TEXT_RE.sub(" ", no_html)
    return MULTISPACE_RE.sub(" ", normalized).strip()


def build_analysis_prompt(title: str, content: str | None, created_at: Any = None) -> str:
    content_text = content or ""
    created_at_text = str(created_at) if created_at else ""
    return f"""
너는 주식 뉴스 분석 AI다.
입력된 뉴스 텍스트를 읽고, 투자 판단에 활용할 수 있도록 아래 항목들을 분석하라.

목표:
- 뉴스의 감성을 positive / negative / neutral 중 하나로 분류
- 감성 점수를 -1.0 ~ 1.0 범위로 산출
- 핵심 키워드를 3~5개 추출
- 뉴스가 영향을 주는 산업 섹터를 분류
- 이벤트 종류를 분류
- 뉴스 중요도를 0.0 ~ 1.0 범위로 평가
- 최신성을 0.0 ~ 1.0 범위로 평가
- 최종 투자 영향 점수를 -1.0 ~ 1.0 범위로 산출
- 뉴스 내용을 1~2문장으로 요약

출력 형식은 반드시 JSON 객체 하나로만 반환하라.
설명문, 마크다운, 코드블록 없이 JSON만 출력하라.

JSON 스키마:
{{
  "sentiment_label": "positive | negative | neutral",
  "sentiment_score": float,
  "keywords": ["string", "string", "string"],
  "sector": "string",
  "event_type": "string",
  "importance_score": float,
  "freshness_score": float,
  "impact_score": float,
  "summary": "string"
}}

규칙:
1. sentiment_score는 -1.0 ~ 1.0 범위로 반환한다.
2. importance_score와 freshness_score는 0.0 ~ 1.0 범위로 반환한다.
3. impact_score는 실제 주가/섹터에 미칠 수 있는 종합 영향을 기준으로 -1.0 ~ 1.0 범위에서 반환한다.
4. keywords는 핵심 키워드 3~5개를 배열로 반환한다.
5. sector는 가능한 경우 다음 중 하나를 우선 사용한다: {", ".join(SECTOR_CANDIDATES)}.
6. event_type은 가능한 경우 다음 중 하나를 우선 사용한다: {", ".join(EVENT_TYPE_CANDIDATES)}.
7. 추측하지 말고 뉴스 내용에 근거해 판단한다.

입력 뉴스:
제목: {title}
본문: {content_text}
작성시각: {created_at_text}
""".strip()


def get_openai_client() -> OpenAI:
    api_key = os.getenv("OPENAI_API_KEY")
    if not api_key:
        raise ValueError("OPENAI_API_KEY is not set.")
    return OpenAI(api_key=api_key)


def analyze_news_with_gpt(
    clean_text: str,
    title: str,
    content: str | None,
    created_at: Any = None,
    model: str = "gpt-4o-mini",
) -> dict[str, Any]:
    client = get_openai_client()
    prompt = build_analysis_prompt(title=title, content=content or clean_text, created_at=created_at)

    response = client.chat.completions.create(
        model=model,
        response_format={"type": "json_object"},
        messages=[
            {
                "role": "system",
                "content": "너는 투자 뉴스 분석 결과를 JSON으로만 반환하는 금융 뉴스 분석기다.",
            },
            {
                "role": "user",
                "content": prompt,
            },
        ],
        temperature=0.2,
    )

    raw_text = response.choices[0].message.content or "{}"
    return json.loads(raw_text)


def clamp(value: Any, minimum: float, maximum: float, default: float) -> float:
    try:
        numeric = float(value)
    except (TypeError, ValueError):
        return default
    return max(min(numeric, maximum), minimum)


def normalize_keywords(value: Any) -> list[str]:
    if isinstance(value, list):
        keywords = [str(item).strip() for item in value if str(item).strip()]
        return keywords[:5]
    if isinstance(value, str) and value.strip():
        return [item.strip() for item in value.split(",") if item.strip()][:5]
    return []


def normalize_label(value: Any) -> str:
    label = str(value or "").strip().lower()
    if label in {"positive", "negative", "neutral"}:
        return label
    return "neutral"


def normalize_choice(value: Any, candidates: list[str], default: str = "기타") -> str:
    text = str(value or "").strip()
    return text if text in candidates else default


def validate_analysis_result(result: dict[str, Any], news_id: int | None = None) -> AnalysisResult:
    summary = str(result.get("summary", "")).strip()
    if not summary:
        raise ValueError("summary is missing from AI analysis result.")

    return AnalysisResult(
        news_id=news_id,
        sentiment_label=normalize_label(result.get("sentiment_label")),
        sentiment_score=clamp(result.get("sentiment_score"), -1.0, 1.0, 0.0),
        keywords=normalize_keywords(result.get("keywords")),
        sector=normalize_choice(result.get("sector"), SECTOR_CANDIDATES),
        event_type=normalize_choice(result.get("event_type"), EVENT_TYPE_CANDIDATES),
        importance_score=clamp(result.get("importance_score"), 0.0, 1.0, 0.5),
        freshness_score=clamp(result.get("freshness_score"), 0.0, 1.0, 0.5),
        impact_score=clamp(result.get("impact_score"), -1.0, 1.0, 0.0),
        summary=summary,
        created_at=datetime.now(timezone.utc).isoformat(),
    )


def analyze_single_news(news: Any, model: str = "gpt-4o-mini") -> AnalysisResult:
    title = getattr(news, "title", "") or ""
    content = getattr(news, "content", "") or ""
    news_id = getattr(news, "id", None)
    created_at = getattr(news, "created_at", None)

    clean_text = preprocess_news(title, content)
    raw_result = analyze_news_with_gpt(
        clean_text=clean_text,
        title=title,
        content=clean_text,
        created_at=created_at,
        model=model,
    )
    return validate_analysis_result(raw_result, news_id=news_id)
