import os
import anthropic
import requests
from bs4 import BeautifulSoup
from sqlalchemy import create_engine, text
from dotenv import load_dotenv

load_dotenv()

ANTHROPIC_API_KEY = os.getenv("ANTHROPIC_API_KEY")
DATABASE_URL      = os.getenv("DATABASE_URL")
engine            = create_engine(DATABASE_URL)
client            = anthropic.Anthropic(api_key=ANTHROPIC_API_KEY)

# 分析対象の外務省ページ
# 日本外務省の各国・地域情勢ページを使う
TARGETS = [
    {
        "country_a": "japan",
        "country_b": "usa",
        "url": "https://www.mofa.go.jp/mofaj/area/usa/index.html",
    },
    {
        "country_a": "japan",
        "country_b": "brazil",
        "url": "https://www.mofa.go.jp/mofaj/area/brazil/index.html",
    },
]


def fetch_page_text(url: str) -> str:
    """WebページからメインテキストをHTMLパースして取得する"""
    headers = {"User-Agent": "Mozilla/5.0"}
    res = requests.get(url, headers=headers, timeout=10)
    res.encoding = res.apparent_encoding

    soup = BeautifulSoup(res.text, "html.parser")

    # ナビゲーションやフッターを除いてメインコンテンツだけ取る
    for tag in soup(["script", "style", "nav", "footer", "header"]):
        tag.decompose()

    text = soup.get_text(separator="\n", strip=True)

    # 長すぎるとAPIのトークン制限に引っかかるので先頭3000文字に制限
    return text[:3000]


def analyze_relation(country_a: str, country_b: str, page_text: str) -> dict:
    """Claude APIでページテキストから外交関係を分析する"""

    prompt = f"""
以下は外務省のウェブサイトから取得した文章です。
{country_a} と {country_b} の二国間関係について分析し、
以下の項目を日本語で簡潔にまとめてください。

【文章】
{page_text}

【出力形式】
relation_type: （友好的 / 緊張 / 中立 / 同盟 のいずれか）
summary: （関係性の要約を100文字以内で）
"""

    message = client.messages.create(
        model="claude-sonnet-4-20250514",
        max_tokens=300,
        messages=[{"role": "user", "content": prompt}]
    )

    response_text = message.content[0].text

    # レスポンスをパースして辞書に変換
    result = {"relation_type": "中立", "summary": ""}
    for line in response_text.splitlines():
        if line.startswith("relation_type:"):
            result["relation_type"] = line.split(":", 1)[1].strip()
        elif line.startswith("summary:"):
            result["summary"] = line.split(":", 1)[1].strip()

    return result


def save_relation(country_a, country_b, relation_type, summary, source_url):
    """
    分析結果をDBに保存する（UPSERT: country_a, country_b が重複したら更新）
    """
    # 常に country_a < country_b の順序に統一（チェック制約に合わせる）
    if country_a > country_b:
        country_a, country_b = country_b, country_a
    
    try:
        with engine.begin() as conn:
            conn.execute(text("""
                INSERT INTO diplomatic_relations
                    (country_a, country_b, relation_type, summary, source_url)
                VALUES
                    (:a, :b, :rel, :sum, :url)
                ON CONFLICT (country_a, country_b)
                DO UPDATE SET
                    relation_type = EXCLUDED.relation_type,
                    summary = EXCLUDED.summary,
                    source_url = EXCLUDED.source_url,
                    updated_at = NOW()
            """), {
                "a":   country_a,
                "b":   country_b,
                "rel": relation_type,
                "sum": summary,
                "url": source_url,
            })
        print(f"  保存完了: {country_a} ↔ {country_b} | {relation_type}")
        print(f"  要約: {summary}")
    except Exception as e:
        print(f"  保存エラー: {e}")


def main():
    """
    外務省ページから外交関係データを取得・分析して DB に保存する
    """
    print("===== 外交関係データ取り込み開始 =====")
    
    for target in TARGETS:
        print(f"\n===== {target['country_a']} ↔ {target['country_b']} =====")

        print("  ページ取得中...")
        try:
            page_text = fetch_page_text(target["url"])
        except Exception as e:
            print(f"  取得失敗: {e}")
            continue

        print("  AI分析中...")
        try:
            result = analyze_relation(
                target["country_a"],
                target["country_b"],
                page_text,
            )
        except Exception as e:
            print(f"  分析失敗: {e}")
            continue

        save_relation(
            target["country_a"],
            target["country_b"],
            result["relation_type"],
            result["summary"],
            target["url"],
        )
    
    print("\n===== 外交関係データ取り込み完了 =====")


if __name__ == "__main__":
    main()