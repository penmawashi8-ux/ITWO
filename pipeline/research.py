"""
用語リサーチモジュール
Gemini REST APIを使って最新IT用語を1つ選定する
"""
import json
import os
import time
from pathlib import Path

import requests
from dotenv import load_dotenv

load_dotenv()

USED_TERMS_PATH = Path(__file__).parent.parent / "used_terms.json"
MODEL = os.getenv("GEMINI_MODEL", "gemini-2.5-flash")
MAX_RETRIES = 4


def _load_used_terms() -> list[str]:
    if not USED_TERMS_PATH.exists():
        return []
    with open(USED_TERMS_PATH, encoding="utf-8") as f:
        return json.load(f)


def mark_used(term: str) -> None:
    """used_terms.jsonに用語を追加する"""
    terms = _load_used_terms()
    if term not in terms:
        terms.append(term)
    with open(USED_TERMS_PATH, "w", encoding="utf-8") as f:
        json.dump(terms, f, ensure_ascii=False, indent=2)


def _extract_text(data: dict) -> str:
    """Geminiレスポンスからテキストを抽出する（parts構造・直接text両対応）"""
    candidate = data["candidates"][0]
    content = candidate.get("content", {})

    if "parts" in content:
        # 思考モデル: thought=True のpartを除いた最後のtextを使う
        text_parts = [p["text"] for p in content["parts"] if not p.get("thought") and "text" in p]
        raw = text_parts[-1] if text_parts else content["parts"][-1].get("text", "")
    elif "text" in content:
        raw = content["text"]
    else:
        raise ValueError(f"不明なレスポンス構造: {list(content.keys())}")

    # markdownコードブロックを除去
    raw = raw.strip()
    if raw.startswith("```"):
        lines = raw.splitlines()
        inner = [l for l in lines[1:] if l.strip() != "```"]
        raw = "\n".join(inner).strip()
    return raw


def _call_gemini(prompt: str, max_tokens: int = 256) -> str:
    """Gemini REST APIを呼び出す（リトライなし・エラー詳細ログ付き）"""
    api_key = os.environ["GEMINI_API_KEY"]
    model = os.getenv("GEMINI_MODEL", MODEL)
    url = f"https://generativelanguage.googleapis.com/v1beta/models/{model}:generateContent"

    print(f"[Gemini] モデル: {model}")
    print(f"[Gemini] APIキー末尾4文字: ...{api_key[-4:]}")

    payload = {
        "contents": [{"parts": [{"text": prompt}]}],
        "generationConfig": {
            "maxOutputTokens": max_tokens,
            "thinkingConfig": {"thinkingBudget": 0},
        },
    }

    resp = requests.post(
        url,
        params={"key": api_key},
        json=payload,
        timeout=30,
    )

    print(f"[Gemini] ステータスコード: {resp.status_code}")
    if not resp.ok:
        print(f"[Gemini] エラーレスポンス:\n{resp.text}")
        resp.raise_for_status()

    data = resp.json()
    print(f"[Gemini] レスポンス全体: {json.dumps(data, ensure_ascii=False)[:600]}")
    raw = _extract_text(data)
    print(f"[Gemini] 抽出テキスト: {raw[:200]}")
    return raw


def pick_term() -> str:
    """Gemini APIを使って最新IT用語を1つ選定して返す"""
    used_terms = _load_used_terms()
    exclude_list = "、".join(used_terms) if used_terms else "（なし）"

    prompt = f"""あなたはITエンジニア・DX推進担当者向けのYouTube Shortsコンテンツを作成しています。
今日取り上げるべき最新IT用語を1つ選んでください。

【条件】
- 対象: ITエンジニア・DX推進担当者が知るべき最新用語
- 優先度高: 直近3ヶ月以内に注目された用語
- 除外する用語: {exclude_list}

【出力形式】
以下のJSON形式のみで出力してください。前置きや説明は一切不要です。
{{"term": "用語名"}}"""

    raw = _call_gemini(prompt, max_tokens=256)
    data = json.loads(raw)
    return data["term"]
