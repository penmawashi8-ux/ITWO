"""
音声合成モジュール
VOICEVOXでナレーション音声を生成する
"""
import os
from pathlib import Path

import requests
from dotenv import load_dotenv

load_dotenv()

OUTPUT_DIR = Path(__file__).parent.parent / "output"
SPEAKER_ID = 1  # ずんだもん


def _get_voicevox_url() -> str:
    return os.getenv("VOICEVOX_URL", "http://localhost:50021")


def _check_voicevox() -> None:
    url = _get_voicevox_url()
    try:
        resp = requests.get(f"{url}/version", timeout=5)
        resp.raise_for_status()
    except requests.exceptions.ConnectionError:
        raise ConnectionRefusedError(
            f"VOICEVOXエンジンに接続できません（{url}）。\n"
            "以下のコマンドでVOICEVOXを起動してから再実行してください:\n"
            "  docker run -d -p 50021:50021 voicevox/voicevox_engine:cpu-ubuntu20.04-latest"
        )
    except requests.exceptions.Timeout:
        raise ConnectionRefusedError(
            f"VOICEVOXエンジンへの接続がタイムアウトしました（{url}）。\n"
            "エンジンが起動中の場合はしばらく待ってから再実行してください。"
        )


def synthesize(narration: str) -> Path:
    """
    VOICEVOXでナレーション音声を生成する

    Args:
        narration: ナレーションテキスト

    Returns:
        生成した音声ファイルのPath（output/narration.wav）
    """
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    url = _get_voicevox_url()

    _check_voicevox()

    # 音声合成クエリを作成
    query_resp = requests.post(
        f"{url}/audio_query",
        params={"text": narration, "speaker": SPEAKER_ID},
        timeout=30,
    )
    query_resp.raise_for_status()
    query = query_resp.json()

    # 読み上げ速度を少し上げる（Shorts向け）
    query["speedScale"] = 1.1

    # 音声合成を実行
    synth_resp = requests.post(
        f"{url}/synthesis",
        params={"speaker": SPEAKER_ID},
        json=query,
        timeout=60,
    )
    synth_resp.raise_for_status()

    output_path = OUTPUT_DIR / "narration.wav"
    with open(output_path, "wb") as f:
        f.write(synth_resp.content)

    print(f"音声保存: {output_path}")
    return output_path
