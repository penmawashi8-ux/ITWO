"""
スクリプト生成モジュール
Gemini REST APIで用語の解説コンテンツを生成する
"""
import json
import os

import requests
from dotenv import load_dotenv

load_dotenv()

MODEL = os.getenv("GEMINI_MODEL", "gemini-2.5-flash")
MAX_RETRIES = 4


def _call_gemini(prompt: str, max_tokens: int = 512) -> str:
    """Gemini REST APIを呼び出す（リトライ付き）"""
    api_key = os.environ["GEMINI_API_KEY"]
    model = os.getenv("GEMINI_MODEL", MODEL)
    url = f"https://generativelanguage.googleapis.com/v1beta/models/{model}:generateContent"

    payload = {
        "contents": [{"parts": [{"text": prompt}]}],
        "generationConfig": {
            "maxOutputTokens": max_tokens,
            "responseMimeType": "application/json",
        },
    }

    resp = requests.post(
        url,
        params={"key": api_key},
        json=payload,
        timeout=30,
    )

    if not resp.ok:
        print(f"[Gemini] エラーレスポンス:\n{resp.text}")
        resp.raise_for_status()

    data = resp.json()
    parts = data["candidates"][0]["content"]["parts"]
    # 思考モデルは parts[-1] が実際の回答
    raw = parts[-1]["text"].strip()
    return raw


def generate(term: str) -> dict:
    """
    Gemini APIで用語の解説コンテンツを生成する

    Returns:
        dict with keys: term, term_en, definition, use_case, point, narration
    """
    prompt = f"""あなたはITエンジニア・DX推進担当者向けのYouTube Shortsコンテンツを作成しています。
以下の用語について解説コンテンツを作成してください。

【用語】{term}

【出力形式】
以下のJSON形式のみで出力してください。前置きやマークダウン記法は一切不要です。

{{
  "term": "用語名（日本語）",
  "term_en": "English name",
  "definition": "30字以内の定義",
  "use_case": "活用例（40字以内）",
  "point": "覚えるポイント（20字以内）",
  "narration": "ナレーション全文（150字以内・です/ます調）"
}}

【制約】
- definition は30字以内
- use_case は40字以内
- point は20字以内
- narration は150字以内、です/ます調で自然な口語
- narration は「{term}とは、」から始めること
- すべての値は日本語（term_en のみ英語）"""

    data = json.loads(_call_gemini(prompt))

    required_keys = {"term", "term_en", "definition", "use_case", "point", "narration"}
    missing = required_keys - data.keys()
    if missing:
        raise ValueError(f"スクリプト生成レスポンスにキーが不足しています: {missing}")

    return data


def generate_metadata(data: dict) -> dict:
    """
    Gemini APIでYouTube投稿用のタイトル・説明文・タグを生成する

    Returns:
        dict with keys: title, description, tags
    """
    term = data["term"]
    definition = data["definition"]
    use_case = data["use_case"]

    prompt = f"""YouTube Shortsの動画メタデータを生成してください。

【用語】{term}
【定義】{definition}
【活用例】{use_case}

【出力形式】
以下のJSON形式のみで出力してください。前置きは不要です。

{{
  "title": "【30秒】{term}とは？#Shorts",
  "description": "動画説明文（200字以内）",
  "tags": ["タグ1", "タグ2", "タグ3", "タグ4", "タグ5"]
}}

【制約】
- title は「【30秒】{term}とは？#Shorts」の形式を守る
- description は200字以内、ITエンジニア向けに分かりやすく
- tags は5〜10個、関連するIT用語・技術キーワードを含める"""

    return json.loads(_call_gemini(prompt))
