"""
YouTube Shorts 自動生成・投稿パイプライン
エントリポイント
"""
import json
import os
import sys
from pathlib import Path

from dotenv import load_dotenv

load_dotenv()

OUTPUT_DIR = Path("output")

TEST_MODE = os.getenv("TEST_MODE", "false").lower() == "true"
FORCE_TERM = os.getenv("FORCE_TERM", "").strip()
MOCK_SCRIPT = os.getenv("MOCK_SCRIPT", "false").lower() == "true"

# API不要のサンプルデータ（MOCK_SCRIPT=true 時に使用）
_MOCK_DATA = {
    "term": "生成AI",
    "term_en": "Generative AI",
    "definition": "テキスト・画像・動画などを自動生成するAI技術",
    "use_case": "議事録の自動要約やコード補完ツールに活用されている",
    "point": "人間の指示で新コンテンツを生成",
    "narration": (
        "生成AIとは、テキストや画像などを自動で生成するAI技術です。"
        "ChatGPTやGeminiなどが代表例で、業務効率化やコンテンツ制作に広く活用されています。"
        "今後もDX推進の中核技術として注目が続きます。"
    ),
}


def run() -> None:
    from pipeline import research, script, slide, voice, video, upload

    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

    if MOCK_SCRIPT:
        print("[MOCK_SCRIPT] Gemini APIをスキップし、サンプルデータを使用します")
        data = _MOCK_DATA.copy()
        term = data["term"]
    else:
        # ---- 1. 用語選定 ----
        if FORCE_TERM:
            term = FORCE_TERM
            print(f"[FORCE_TERM] 用語を指定: {term}")
        else:
            print("用語を選定中...")
            term = research.pick_term()
            print(f"選定用語: {term}")

        # ---- 2. スクリプト生成 ----
        print("スクリプトを生成中...")
        data = script.generate(term)

    script_path = OUTPUT_DIR / "script.json"
    with open(script_path, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)
    print(f"スクリプト保存: {script_path}")

    # ---- 3. スライド生成 ----
    print("スライドを生成中...")
    slide_paths = slide.generate(data)

    # ---- 4. 音声合成 ----
    print("音声を合成中...")
    audio_path = voice.synthesize(data["narration"])

    # ---- 5. 動画合成 ----
    print("動画を合成中...")
    video_path = video.compose(slide_paths, audio_path)

    # ---- 6. テストモード / 本番モード分岐 ----
    if TEST_MODE:
        print("\n" + "=" * 50)
        print("TEST MODE: YouTubeへの投稿はスキップしました")
        if MOCK_SCRIPT:
            print("MOCK_SCRIPT: Gemini APIは使用していません")
        print("=" * 50)
        print(f"用語:         {data['term']} ({data['term_en']})")
        print(f"定義:         {data['definition']}")
        print(f"活用例:       {data['use_case']}")
        print(f"ポイント:     {data['point']}")
        print(f"ナレーション: {data['narration']}")
        print("=" * 50)
        print(f"動画ファイル: {video_path}")
        print(f"スクリプト:   {script_path}")
        for p in slide_paths:
            print(f"スライド:     {p}")
        print("=" * 50)
        print("used_terms.json は更新されていません")
    else:
        # 本番: YouTubeにメタデータ生成 → 投稿
        print("YouTubeメタデータを生成中...")
        metadata = script.generate_metadata(data)
        data.update(metadata)

        print("YouTubeに投稿中...")
        url = upload.post(data, video_path)
        print(f"投稿URL: {url}")

        # used_terms.json を更新
        research.mark_used(term)
        print(f"used_terms.json を更新しました: {term}")

        # 中間ファイルを削除（mp4とscript.jsonは残す）
        for p in slide_paths:
            p.unlink(missing_ok=True)
        audio_path.unlink(missing_ok=True)
        print("中間ファイル（スライド・音声）を削除しました")

        print("\n完了!")
        print(f"動画URL: {url}")


if __name__ == "__main__":
    try:
        run()
    except ConnectionRefusedError as e:
        print(f"\n[エラー] VOICEVOX接続エラー:\n{e}", file=sys.stderr)
        sys.exit(1)
    except FileNotFoundError as e:
        print(f"\n[エラー] ファイルが見つかりません:\n{e}", file=sys.stderr)
        sys.exit(1)
    except Exception as e:
        print(f"\n[エラー] 予期しないエラーが発生しました:\n{type(e).__name__}: {e}", file=sys.stderr)
        sys.exit(1)
