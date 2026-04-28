"""
DB 초기화 및 시드 데이터 생성 스크립트.
최초 1회 실행: python init_db.py
"""
from database import engine, SessionLocal, Base
import models
from datetime import datetime, timedelta
import random

SECTORS = [
    {"name": "반도체",    "description": "메모리·시스템반도체·파운드리 관련 기업",     "icon": "💾"},
    {"name": "2차전지",   "description": "배터리·양극재·전해질 등 전기차 핵심 소재",   "icon": "🔋"},
    {"name": "자동차",    "description": "완성차·부품·자율주행 관련 기업",             "icon": "🚗"},
    {"name": "AI/IT",     "description": "인공지능·플랫폼·소프트웨어 기업",            "icon": "🤖"},
    {"name": "바이오/제약","description": "제약·바이오·의료기기 기업",                  "icon": "💊"},
    {"name": "금융",      "description": "은행·증권·보험·카드 기업",                   "icon": "🏦"},
    {"name": "에너지/화학","description": "정유·화학·신재생에너지·소재 기업",           "icon": "⚡"},
    {"name": "산업재",    "description": "건설·철강·조선·기계·항공 기업",              "icon": "🏭"},
    {"name": "소비재",    "description": "식품·유통·패션·생활용품 기업",               "icon": "🛒"},
]

STOCKS_BY_SECTOR = {
    "반도체": [
        {"symbol": "005930.KS", "name": "삼성전자",       "exchange": "KRX"},
        {"symbol": "000660.KS", "name": "SK하이닉스",     "exchange": "KRX"},
        {"symbol": "042700.KS", "name": "한미반도체",     "exchange": "KRX"},
        {"symbol": "357780.KS", "name": "솔브레인",       "exchange": "KRX"},
        {"symbol": "240810.KS", "name": "원익IPS",        "exchange": "KRX"},
        {"symbol": "288490.KS", "name": "유진테크",       "exchange": "KRX"},
        {"symbol": "009150.KS", "name": "삼성전기",       "exchange": "KRX"},
        {"symbol": "011070.KS", "name": "LG이노텍",       "exchange": "KRX"},
        {"symbol": "000990.KS", "name": "DB하이텍",       "exchange": "KRX"},
        {"symbol": "036930.KS", "name": "주성엔지니어링", "exchange": "KRX"},
        {"symbol": "033640.KS", "name": "네패스",         "exchange": "KRX"},
        {"symbol": "058470.KS", "name": "리노공업",       "exchange": "KRX"},
    ],
    "2차전지": [
        {"symbol": "373220.KS", "name": "LG에너지솔루션",     "exchange": "KRX"},
        {"symbol": "006400.KS", "name": "삼성SDI",            "exchange": "KRX"},
        {"symbol": "051910.KS", "name": "LG화학",             "exchange": "KRX"},
        {"symbol": "096770.KS", "name": "SK이노베이션",       "exchange": "KRX"},
        {"symbol": "247540.KS", "name": "에코프로비엠",       "exchange": "KRX"},
        {"symbol": "086520.KS", "name": "에코프로",           "exchange": "KRX"},
        {"symbol": "003670.KS", "name": "포스코퓨처엠",       "exchange": "KRX"},
        {"symbol": "005070.KS", "name": "코스모신소재",       "exchange": "KRX"},
        {"symbol": "020150.KS", "name": "롯데에너지머티리얼즈","exchange": "KRX"},
        {"symbol": "010060.KS", "name": "OCI홀딩스",          "exchange": "KRX"},
        {"symbol": "298050.KS", "name": "효성첨단소재",       "exchange": "KRX"},
    ],
    "자동차": [
        {"symbol": "005380.KS", "name": "현대차",             "exchange": "KRX"},
        {"symbol": "000270.KS", "name": "기아",               "exchange": "KRX"},
        {"symbol": "012330.KS", "name": "현대모비스",         "exchange": "KRX"},
        {"symbol": "011210.KS", "name": "현대위아",           "exchange": "KRX"},
        {"symbol": "204320.KS", "name": "HL만도",             "exchange": "KRX"},
        {"symbol": "086280.KS", "name": "현대글로비스",       "exchange": "KRX"},
        {"symbol": "018880.KS", "name": "한온시스템",         "exchange": "KRX"},
        {"symbol": "307950.KS", "name": "현대오토에버",       "exchange": "KRX"},
        {"symbol": "004020.KS", "name": "현대제철",           "exchange": "KRX"},
        {"symbol": "084370.KS", "name": "한국타이어앤테크놀로지","exchange": "KRX"},
    ],
    "AI/IT": [
        {"symbol": "035420.KS", "name": "NAVER",     "exchange": "KRX"},
        {"symbol": "035720.KS", "name": "카카오",    "exchange": "KRX"},
        {"symbol": "259960.KS", "name": "크래프톤",  "exchange": "KRX"},
        {"symbol": "036570.KS", "name": "엔씨소프트","exchange": "KRX"},
        {"symbol": "251270.KS", "name": "넷마블",    "exchange": "KRX"},
        {"symbol": "018260.KS", "name": "삼성SDS",   "exchange": "KRX"},
        {"symbol": "017670.KS", "name": "SK텔레콤",  "exchange": "KRX"},
        {"symbol": "030200.KS", "name": "KT",        "exchange": "KRX"},
        {"symbol": "323410.KS", "name": "카카오뱅크","exchange": "KRX"},
        {"symbol": "066570.KS", "name": "LG전자",    "exchange": "KRX"},
        {"symbol": "377300.KS", "name": "카카오페이","exchange": "KRX"},
        {"symbol": "032640.KS", "name": "LG유플러스","exchange": "KRX"},
    ],
    "바이오/제약": [
        {"symbol": "207940.KS", "name": "삼성바이오로직스","exchange": "KRX"},
        {"symbol": "068270.KS", "name": "셀트리온",        "exchange": "KRX"},
        {"symbol": "128940.KS", "name": "한미약품",        "exchange": "KRX"},
        {"symbol": "000100.KS", "name": "유한양행",        "exchange": "KRX"},
        {"symbol": "185750.KS", "name": "종근당",          "exchange": "KRX"},
        {"symbol": "006280.KS", "name": "녹십자",          "exchange": "KRX"},
        {"symbol": "009290.KS", "name": "광동제약",        "exchange": "KRX"},
        {"symbol": "000020.KS", "name": "동화약품",        "exchange": "KRX"},
        {"symbol": "003850.KS", "name": "보령",            "exchange": "KRX"},
        {"symbol": "326030.KS", "name": "SK바이오팜",      "exchange": "KRX"},
        {"symbol": "069620.KS", "name": "대웅제약",        "exchange": "KRX"},
        {"symbol": "091990.KS", "name": "셀트리온헬스케어","exchange": "KRX"},
    ],
    "금융": [
        {"symbol": "105560.KS", "name": "KB금융",      "exchange": "KRX"},
        {"symbol": "055550.KS", "name": "신한지주",    "exchange": "KRX"},
        {"symbol": "086790.KS", "name": "하나금융지주","exchange": "KRX"},
        {"symbol": "316140.KS", "name": "우리금융지주","exchange": "KRX"},
        {"symbol": "032830.KS", "name": "삼성생명",    "exchange": "KRX"},
        {"symbol": "000810.KS", "name": "삼성화재",    "exchange": "KRX"},
        {"symbol": "006800.KS", "name": "미래에셋증권","exchange": "KRX"},
        {"symbol": "005940.KS", "name": "NH투자증권",  "exchange": "KRX"},
        {"symbol": "071050.KS", "name": "한국금융지주","exchange": "KRX"},
        {"symbol": "005830.KS", "name": "DB손해보험",  "exchange": "KRX"},
        {"symbol": "001450.KS", "name": "현대해상",    "exchange": "KRX"},
        {"symbol": "139130.KS", "name": "DGB금융지주", "exchange": "KRX"},
    ],
    "에너지/화학": [
        {"symbol": "011170.KS", "name": "롯데케미칼",  "exchange": "KRX"},
        {"symbol": "009830.KS", "name": "한화솔루션",  "exchange": "KRX"},
        {"symbol": "011780.KS", "name": "금호석유화학","exchange": "KRX"},
        {"symbol": "010950.KS", "name": "S-Oil",       "exchange": "KRX"},
        {"symbol": "078930.KS", "name": "GS",          "exchange": "KRX"},
        {"symbol": "000880.KS", "name": "한화",        "exchange": "KRX"},
        {"symbol": "004800.KS", "name": "효성",        "exchange": "KRX"},
        {"symbol": "120110.KS", "name": "코오롱인더",  "exchange": "KRX"},
        {"symbol": "285130.KS", "name": "SK케미칼",    "exchange": "KRX"},
        {"symbol": "003240.KS", "name": "태광산업",    "exchange": "KRX"},
        {"symbol": "006650.KS", "name": "대한유화",    "exchange": "KRX"},
        {"symbol": "002380.KS", "name": "KCC",         "exchange": "KRX"},
    ],
    "산업재": [
        {"symbol": "005490.KS", "name": "POSCO홀딩스",    "exchange": "KRX"},
        {"symbol": "000720.KS", "name": "현대건설",        "exchange": "KRX"},
        {"symbol": "028050.KS", "name": "삼성엔지니어링",  "exchange": "KRX"},
        {"symbol": "006360.KS", "name": "GS건설",          "exchange": "KRX"},
        {"symbol": "015760.KS", "name": "한국전력",        "exchange": "KRX"},
        {"symbol": "034020.KS", "name": "두산에너빌리티",  "exchange": "KRX"},
        {"symbol": "329180.KS", "name": "현대중공업",      "exchange": "KRX"},
        {"symbol": "012450.KS", "name": "한화에어로스페이스","exchange": "KRX"},
        {"symbol": "047810.KS", "name": "한국항공우주",    "exchange": "KRX"},
        {"symbol": "003490.KS", "name": "대한항공",        "exchange": "KRX"},
        {"symbol": "010140.KS", "name": "삼성중공업",      "exchange": "KRX"},
        {"symbol": "006260.KS", "name": "LS",              "exchange": "KRX"},
        {"symbol": "047040.KS", "name": "대우건설",        "exchange": "KRX"},
    ],
    "소비재": [
        {"symbol": "139480.KS", "name": "이마트",    "exchange": "KRX"},
        {"symbol": "004170.KS", "name": "신세계",    "exchange": "KRX"},
        {"symbol": "023530.KS", "name": "롯데쇼핑",  "exchange": "KRX"},
        {"symbol": "097950.KS", "name": "CJ제일제당","exchange": "KRX"},
        {"symbol": "004370.KS", "name": "농심",      "exchange": "KRX"},
        {"symbol": "033780.KS", "name": "KT&G",      "exchange": "KRX"},
        {"symbol": "090430.KS", "name": "아모레퍼시픽","exchange": "KRX"},
        {"symbol": "051900.KS", "name": "LG생활건강","exchange": "KRX"},
        {"symbol": "000080.KS", "name": "하이트진로","exchange": "KRX"},
        {"symbol": "005300.KS", "name": "롯데칠성",  "exchange": "KRX"},
        {"symbol": "271560.KS", "name": "오리온",    "exchange": "KRX"},
        {"symbol": "003230.KS", "name": "삼양식품",  "exchange": "KRX"},
        {"symbol": "008770.KS", "name": "호텔신라",  "exchange": "KRX"},
        {"symbol": "069960.KS", "name": "현대백화점","exchange": "KRX"},
    ],
}

SAMPLE_PRICES = {
    # 반도체
    "005930.KS": 75000,  "000660.KS": 180000, "042700.KS": 95000,
    "357780.KS": 280000, "240810.KS": 38000,  "288490.KS": 42000,
    "009150.KS": 140000, "011070.KS": 180000, "000990.KS": 35000,
    "036930.KS": 22000,  "033640.KS": 18000,  "058470.KS": 85000,
    # 2차전지
    "373220.KS": 380000, "006400.KS": 310000, "051910.KS": 320000,
    "096770.KS": 190000, "247540.KS": 140000, "086520.KS": 700000,
    "003670.KS": 200000, "005070.KS": 30000,  "020150.KS": 50000,
    "010060.KS": 90000,  "298050.KS": 55000,
    # 자동차
    "005380.KS": 240000, "000270.KS": 110000, "012330.KS": 260000,
    "011210.KS": 55000,  "204320.KS": 48000,  "086280.KS": 200000,
    "018880.KS": 6000,   "307950.KS": 180000, "004020.KS": 30000,
    "084370.KS": 55000,
    # AI/IT
    "035420.KS": 195000, "035720.KS": 42000,  "259960.KS": 220000,
    "036570.KS": 180000, "251270.KS": 55000,  "018260.KS": 170000,
    "017670.KS": 55000,  "030200.KS": 45000,  "323410.KS": 24000,
    "066570.KS": 110000, "377300.KS": 22000,  "032640.KS": 12000,
    # 바이오/제약
    "207940.KS": 750000, "068270.KS": 180000, "128940.KS": 320000,
    "000100.KS": 85000,  "185750.KS": 140000, "006280.KS": 130000,
    "009290.KS": 8000,   "000020.KS": 7000,   "003850.KS": 12000,
    "326030.KS": 65000,  "069620.KS": 95000,  "091990.KS": 18000,
    # 금융
    "105560.KS": 68000,  "055550.KS": 45000,  "086790.KS": 55000,
    "316140.KS": 14000,  "032830.KS": 80000,  "000810.KS": 310000,
    "006800.KS": 9000,   "005940.KS": 12000,  "071050.KS": 70000,
    "005830.KS": 90000,  "001450.KS": 38000,  "139130.KS": 8000,
    # 에너지/화학
    "011170.KS": 90000,  "009830.KS": 35000,  "011780.KS": 130000,
    "010950.KS": 130000, "078930.KS": 48000,  "000880.KS": 32000,
    "004800.KS": 55000,  "120110.KS": 38000,  "285130.KS": 100000,
    "003240.KS": 28000,  "006650.KS": 110000, "002380.KS": 270000,
    # 산업재
    "005490.KS": 380000, "000720.KS": 28000,  "028050.KS": 33000,
    "006360.KS": 18000,  "015760.KS": 22000,  "034020.KS": 22000,
    "329180.KS": 130000, "012450.KS": 280000, "047810.KS": 65000,
    "003490.KS": 22000,  "010140.KS": 11000,  "006260.KS": 110000,
    "047040.KS": 5000,
    # 소비재
    "139480.KS": 65000,  "004170.KS": 170000, "023530.KS": 60000,
    "097950.KS": 330000, "004370.KS": 380000, "033780.KS": 95000,
    "090430.KS": 120000, "051900.KS": 200000, "000080.KS": 22000,
    "005300.KS": 160000, "271560.KS": 100000, "003230.KS": 650000,
    "008770.KS": 65000,  "069960.KS": 55000,
}

SAMPLE_NEWS = {
    "반도체": [
        ("삼성전자, HBM3E 양산 확대로 AI 수요 선점", "positive", 0.82, "HBM3E 양산 확대"),
        ("SK하이닉스, 엔비디아와 HBM4 공급 계약 체결", "positive", 0.91, "엔비디아 HBM4 계약"),
        ("반도체 재고 조정 장기화 우려…2분기 실적 하향", "negative", -0.65, "재고 조정 우려"),
        ("TSMC, 日 구마모토 2공장 착공…삼성 파운드리 경쟁 심화", "negative", -0.44, "경쟁 심화"),
        ("메모리 가격 반등…DRAM 현물가 3주 연속 상승", "positive", 0.70, "메모리 가격 반등"),
    ],
    "2차전지": [
        ("LG엔솔, 미국 IRA 첨단제조 세액공제 최대 수혜", "positive", 0.88, "IRA 세액공제 수혜"),
        ("전기차 수요 둔화에 배터리 업체 수주 감소 우려", "negative", -0.71, "수요 둔화 우려"),
        ("삼성SDI, 전고체 배터리 2027년 양산 목표 발표", "positive", 0.79, "전고체 배터리 발표"),
        ("리튬 가격 하락세 지속…배터리 소재株 약세", "negative", -0.55, "리튬 가격 하락"),
        ("현대차·기아, 국산 배터리 채용 확대 방침", "positive", 0.65, "국산 배터리 확대"),
    ],
    "자동차": [
        ("현대차, 미국 조지아 전기차 공장 본격 가동", "positive", 0.80, "미국 공장 가동"),
        ("기아 EV9, 미국 올해의 차 수상…글로벌 브랜드 위상 상승", "positive", 0.86, "EV9 올해의 차"),
        ("중국 전기차 공세에 국내 완성차 점유율 하락 우려", "negative", -0.60, "중국 경쟁 심화"),
        ("자동차 강판 가격 인상으로 제조 원가 압박", "negative", -0.48, "원가 압박"),
        ("현대차 그룹, 美 소프트웨어 정의 차량(SDV) 투자 확대", "positive", 0.72, "SDV 투자"),
    ],
    "AI/IT": [
        ("NAVER, 초거대AI 하이퍼클로바X 기업용 서비스 확대", "positive", 0.83, "하이퍼클로바X 확대"),
        ("카카오, 카카오페이·뱅크 분리 리스크 완화", "positive", 0.58, "분리 리스크 완화"),
        ("네이버웹툰 美 나스닥 상장 성공…글로벌 플랫폼 도약", "positive", 0.90, "나스닥 상장"),
        ("카카오, 개인정보 유출 사고로 과징금 부과 우려", "negative", -0.67, "개인정보 과징금"),
        ("AI 검색 경쟁 심화…구글·오픈AI 공세에 네이버 긴장", "negative", -0.50, "AI 검색 경쟁"),
    ],
    "바이오/제약": [
        ("삼성바이오로직스, 글로벌 CMO 수주 사상 최대 달성", "positive", 0.88, "CMO 최대 수주"),
        ("셀트리온, 램시마SC 유럽 시장 점유율 30% 돌파", "positive", 0.80, "램시마SC 유럽 확대"),
        ("한미약품, 비만치료제 임상 3상 결과 기대 이하", "negative", -0.62, "비만치료제 임상 실망"),
        ("바이오 임상 실패 잇따라…섹터 투자 심리 위축", "negative", -0.55, "임상 실패 우려"),
        ("유한양행, 레이저티닙 미국 FDA 허가 획득", "positive", 0.93, "FDA 허가 획득"),
    ],
    "금융": [
        ("KB금융, 역대 최대 순이익 달성…주주환원 확대 발표", "positive", 0.85, "최대 순이익 달성"),
        ("신한지주, 디지털 전환 가속…비용 효율화 성과", "positive", 0.72, "디지털 전환 성과"),
        ("기준금리 동결…은행 NIM 압박 지속 우려", "negative", -0.48, "NIM 압박 우려"),
        ("가계부채 규제 강화로 은행 대출 성장 둔화 전망", "negative", -0.55, "대출 성장 둔화"),
        ("보험사, 새 회계기준(IFRS17) 호실적…배당 확대 기대", "positive", 0.68, "IFRS17 호실적"),
    ],
    "에너지/화학": [
        ("한화솔루션, 미국 태양광 모듈 공장 증설 확정", "positive", 0.78, "태양광 공장 증설"),
        ("국제 유가 급락…정유·화학株 실적 악화 우려", "negative", -0.65, "유가 급락 우려"),
        ("롯데케미칼, 에틸렌 스프레드 개선으로 흑자 전환 기대", "positive", 0.60, "흑자 전환 기대"),
        ("중국 화학 제품 공급 과잉으로 국내 업체 마진 악화", "negative", -0.58, "중국 공급 과잉"),
        ("S-Oil, 샤힌 프로젝트 완공 임박…정제 마진 개선 전망", "positive", 0.74, "샤힌 프로젝트"),
    ],
    "산업재": [
        ("한화에어로스페이스, K방산 수출 수주 잔고 사상 최대", "positive", 0.92, "방산 수출 최대"),
        ("현대중공업, LNG 운반선 수주 호조 지속", "positive", 0.81, "LNG 수주 호조"),
        ("POSCO홀딩스, 중국산 저가 철강 공세에 수익성 악화", "negative", -0.60, "철강 수익성 악화"),
        ("건설사, 해외 프로젝트 손실 반영으로 실적 쇼크", "negative", -0.68, "해외 손실 쇼크"),
        ("한국전력, 전기요금 인상 허용…실적 개선 기대", "positive", 0.70, "전기요금 인상"),
    ],
    "소비재": [
        ("삼양식품, 불닭볶음면 글로벌 매출 2조 돌파", "positive", 0.90, "글로벌 매출 2조"),
        ("아모레퍼시픽, 중국 소비 회복으로 실적 턴어라운드", "positive", 0.76, "중국 실적 회복"),
        ("이마트, 쿠팡 공세로 오프라인 유통 적자 지속", "negative", -0.62, "오프라인 유통 적자"),
        ("고금리·고물가 장기화…소비 위축 심화 우려", "negative", -0.50, "소비 위축 우려"),
        ("KT&G, 궐련형 전자담배 해외 점유율 상승", "positive", 0.65, "해외 점유율 상승"),
    ],
}


def seed_demo_news(db, sector_id: int, sector_name: str):
    items = SAMPLE_NEWS.get(sector_name, [])
    for i, (title, label, score, summary) in enumerate(items):
        published = datetime.utcnow() - timedelta(hours=i * 6 + random.randint(0, 5))
        db.add(models.News(
            sector_id=sector_id,
            title=title,
            content=f"{title}에 관한 상세 내용입니다. 시장 전문가들은 이 뉴스가 {sector_name} 섹터에 중요한 영향을 미칠 것으로 분석하고 있습니다.",
            url=f"https://news.example.com/{sector_name}/{i+1}",
            published_at=published,
            sentiment_score=score,
            sentiment_label=label,
            ai_summary=summary,
        ))


def seed_demo_prices(db, stock_id: int, symbol: str):
    base_price = SAMPLE_PRICES.get(symbol, 100000)
    end = datetime.utcnow()
    for day in range(60, 0, -1):
        d = end - timedelta(days=day)
        if d.weekday() >= 5:
            continue
        change = random.uniform(-0.03, 0.03)
        close = int(base_price * (1 + change))
        open_ = int(close * random.uniform(0.985, 1.015))
        high = int(max(open_, close) * random.uniform(1.001, 1.02))
        low = int(min(open_, close) * random.uniform(0.98, 0.999))
        volume = random.randint(500000, 5000000)
        db.add(models.StockPrice(
            stock_id=stock_id,
            date=d.replace(hour=0, minute=0, second=0, microsecond=0),
            open=open_, high=high, low=low, close=close, volume=volume,
        ))
        base_price = close


def main():
    print("DB 테이블 생성 중...")
    Base.metadata.create_all(bind=engine)

    db = SessionLocal()
    try:
        if db.query(models.Sector).count() > 0:
            print("이미 초기화되어 있습니다. 건너뜁니다.")
            return

        print("섹터 생성 중...")
        for s in SECTORS:
            db.add(models.Sector(**s))
        db.commit()

        sector_map = {s.name: s.id for s in db.query(models.Sector).all()}

        print("종목 및 주가 데이터 생성 중...")
        for sector_name, stocks in STOCKS_BY_SECTOR.items():
            sector_id = sector_map[sector_name]
            for st in stocks:
                stock = models.Stock(sector_id=sector_id, **st)
                db.add(stock)
                db.flush()
                seed_demo_prices(db, stock.id, st["symbol"])

        print("샘플 뉴스 생성 중...")
        for sector_name, sector_id in sector_map.items():
            seed_demo_news(db, sector_id, sector_name)

        db.commit()
        print("초기화 완료!")
    except Exception as e:
        db.rollback()
        print(f"오류: {e}")
        raise
    finally:
        db.close()


if __name__ == "__main__":
    main()
