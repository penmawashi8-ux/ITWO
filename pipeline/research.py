"""
用語リサーチモジュール
Gemini APIを使って最新IT用語を1つ選定する
"""
import json
import os
import time
from pathlib import Path

from dotenv import load_dotenv
from google import genai

load_dotenv()

USED_TERMS_PATH = Path(__file__).parent.parent / "used_terms.json"
MODEL = "gemini-2.0-flash-lite"
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


def _generate_with_retry(prompt: str, max_tokens: int = 64) -> str:
    """クォータエラー時に指数バックオフでリトライする"""
    client = genai.Client(api_key=os.environ["GEMINI_API_KEY"])
    wait = 60
    for attempt in range(MAX_RETRIES):
        try:
            response = client.models.generate_content(
                model=MODEL,
                contents=prompt,
                config={"max_output_tokens": max_tokens},
            )
            raw = response.text.strip()
            if raw.startswith("```"):
                lines = raw.splitlines()
                raw = "\n".join(lines[1:-1] if lines[-1] == "```" else lines[1:])
            return raw
        except Exception as e:
            if "429" in str(e) or "ResourceExhausted" in str(e):
                if attempt < MAX_RETRIES - 1:
                    print(f"クォータ超過。{wait}秒後にリトライします... ({attempt + 1}/{MAX_RETRIES})")
                    time.sleep(wait)
                    wait *= 2
                else:
                    raise RuntimeError(
                        "Gemini APIのクォータを超過しました。しばらく時間をおいてから再実行してください。\n"
                        "無料枠の上限に達した可能性があります。Google AI Studioで使用状況を確認してください。"
                    ) from e
            else:
                raise
    raise RuntimeError("リトライ上限に達しました")


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

    raw = _generate_with_retry(prompt, max_tokens=64)
    data = json.loads(raw)
    return data["term"]
