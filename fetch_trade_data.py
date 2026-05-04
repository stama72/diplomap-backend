import os
import time
import requests
from sqlalchemy import create_engine, text
from dotenv import load_dotenv

load_dotenv()

API_KEY      = os.getenv("COMTRADE_API_KEY")
DATABASE_URL = os.getenv("DATABASE_URL")
engine       = create_engine(DATABASE_URL)

REPORTERS = {
    "392": "japan",
    "842": "usa",
    "76":  "brazil",
}

PARTNERS = {
    "392": "japan",
    "842": "usa",
    "76":  "brazil",
}

CATEGORIES = {
    "food":   ["02", "04", "07", "08", "10"],
    "energy": ["27"],
}

YEARS = [2020, 2021, 2022, 2023, 2024, 2025]

# 1リクエストごとに待つ秒数
REQUEST_INTERVAL = 2

def fetch_and_save(reporter_code, partner_code, cmd_code, category, year, retry=3):
    """
    1件分のデータをAPIから取得してDBに保存する（リトライあり）
    """

    url = "https://comtradeapi.un.org/data/v1/get/C/A/HS"
    params = {
        "reporterCode": reporter_code,
        "partnerCode":  partner_code,
        "cmdCode":      cmd_code,
        "period":       year,
        "flowCode":     "X",
        "subscription-key": API_KEY,
    }

    for attempt in range(retry):
        res = requests.get(url, params=params)

        if res.status_code == 200:
            break

        if res.status_code == 429:
            # エラーメッセージから待機秒数を取得、取れなければ15秒待つ
            try:
                msg = res.json().get("message", "")
                wait = int(''.join(filter(str.isdigit, msg.split("in")[-1]))) + 1
            except Exception:
                wait = 15
            print(f"  Rate limit: {wait}秒待機します... (試行 {attempt + 1}/{retry})")
            time.sleep(wait)
            continue

        print(f"  エラー: {res.status_code} {res.text[:100]}")
        return

    else:
        print(f"  リトライ上限に達しました。スキップします。")
        return

    data = res.json()
    records = data.get("data", [])

    if not records:
        print(f"  データなし")
        return

    total_value = sum(r.get("primaryValue", 0) for r in records)
    if total_value == 0:
        return

    value_oku = round(total_value * 150 / 1e8, 1)

    from_id = REPORTERS[reporter_code]
    to_id   = PARTNERS[partner_code]

    # UPSERT（既存の場合はスキップ）
    try:
        with engine.begin() as conn:
            conn.execute(text("""
                INSERT INTO trade_links (from_country, to_country, value, category, year)
                VALUES (:from_c, :to_c, :value, :category, :year)
                ON CONFLICT (from_country, to_country, category, year) DO NOTHING
            """), {
                "from_c":   from_id,
                "to_c":     to_id,
                "value":    value_oku,
                "category": category,
                "year":     year,
            })
        print(f"  保存完了: {from_id} → {to_id} | {category} | {year}年 | {value_oku}億円")
    except Exception as e:
        print(f"  保存エラー: {e}")
        return

    # 次のリクエストまで待機
    time.sleep(REQUEST_INTERVAL)


def main():
    """
    全年、全レポーター、全パートナー、全カテゴリ、全商品コードの組み合わせで
    取引データを取得して DB に保存する
    """
    print("===== 取引データ取り込み開始 =====")
    
    for year in YEARS:
        print(f"\n===== {year}年 =====")
        for r_code in REPORTERS:
            for p_code in PARTNERS:
                if r_code == p_code:
                    continue
                for category, cmd_codes in CATEGORIES.items():
                    r_name = REPORTERS[r_code]
                    p_name = PARTNERS[p_code]
                    print(f"{r_name} → {p_name} [{category}]")
                    for cmd_code in cmd_codes:
                        fetch_and_save(r_code, p_code, cmd_code, category, year)
    
    print("\n===== 取引データ取り込み完了 =====")


if __name__ == "__main__":
    main()