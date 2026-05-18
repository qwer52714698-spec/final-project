import requests
import time
from sqlalchemy import create_all
from database import SessionLocal
import models
SERVER_URL = os.environ.get("RENDER_EXTERNAL_URL", "http://localhost:8000")
def run_batch_analysis():
    db = SessionLocal()
    # 1. DB에 등록된 모든 종목 가져오기
    stocks = db.query(models.Stock).all()
    db.close()

    print(f"🚀 총 {len(stocks)}개 종목의 AI 분석을 시작합니다.")

    for stock in stocks:
        symbol = stock.symbol
        print(f"🔄 [{symbol}] {stock.name} 분석 중...")
        
        try:
            # 2. 우리가 만든 API를 내부적으로 호출
            response = requests.get(f"{SERVER_URL}/stocks/{symbol}/analyze")
            
            if response.status_code == 200:
                print(f"✅ {symbol} 완료: {response.json()['data']['prediction']}")
            else:
                print(f"❌ {symbol} 실패: {response.status_code}")
                
        except Exception as e:
            print(f"⚠️ {symbol} 에러 발생: {e}")
        
        # 서버 부하 방지 및 API 속도 제한 대응을 위해 1초간 휴식
        time.sleep(1)

    print("✨ 모든 종목의 분석 데이터가 슈퍼베이스에 기록되었습니다!")

if __name__ == "__main__":
    run_batch_analysis()