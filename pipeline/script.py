"""
スクリプト生成モジュール
Claude APIで用語の解説コンテンツを生成する
"""
import json
import os

import anthropic
from dotenv import load_dotenv

load_dotenv()

MODEL = "claude-sonnet-4-20250514"


def generate(term: str) -> dict:
    """
    Claude APIで用語の解説コンテンツを生成する

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

    client = anthropic.Anthropic(api_key=os.environ["ANTHROPIC_API_KEY"])
    message = client.messages.create(
        model=MODEL,
        max_tokens=512,
        messages=[{"role": "user", "content": prompt}],
    )

    raw = message.content[0].text.strip()
    # コードブロックがあれば除去
    if raw.startswith("```"):
        lines = raw.splitlines()
        raw = "\n".join(lines[1:-1] if lines[-1] == "```" else lines[1:])

    data = json.loads(raw)

    required_keys = {"term", "term_en", "definition", "use_case", "point", "narration"}
    missing = required_keys - data.keys()
    if missing:
        raise ValueError(f"スクリプト生成レスポンスにキーが不足しています: {missing}")

    return data


def generate_metadata(data: dict) -> dict:
    """
    Claude APIでYouTube投稿用のタイトル・説明文・タグを生成する

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

    client = anthropic.Anthropic(api_key=os.environ["ANTHROPIC_API_KEY"])
    message = client.messages.create(
        model=MODEL,
        max_tokens=512,
        messages=[{"role": "user", "content": prompt}],
    )

    raw = message.content[0].text.strip()
    if raw.startswith("```"):
        lines = raw.splitlines()
        raw = "\n".join(lines[1:-1] if lines[-1] == "```" else lines[1:])

    return json.loads(raw)
