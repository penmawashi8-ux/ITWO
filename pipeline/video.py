"""
動画合成モジュール
FFmpegでスライド画像と音声を合成して縦型動画を作る
"""
import json
import subprocess
from pathlib import Path

OUTPUT_DIR = Path(__file__).parent.parent / "output"

WIDTH = 1080
HEIGHT = 1920
FPS = 30


def _get_audio_duration(audio_path: Path) -> float:
    """FFprobeで音声の長さ（秒）を取得する"""
    result = subprocess.run(
        [
            "ffprobe",
            "-v", "quiet",
            "-print_format", "json",
            "-show_streams",
            str(audio_path),
        ],
        capture_output=True,
        text=True,
        check=True,
    )
    info = json.loads(result.stdout)
    for stream in info["streams"]:
        if stream.get("codec_type") == "audio":
            return float(stream["duration"])
    raise ValueError(f"音声ストリームが見つかりません: {audio_path}")


def compose(slide_paths: list[Path], audio_path: Path) -> Path:
    """
    FFmpegでスライド画像と音声を合成して動画を生成する

    各スライドに音声の長さを均等に割り当てる

    Args:
        slide_paths: スライド画像のPathリスト（4枚）
        audio_path: 音声ファイルのPath

    Returns:
        生成した動画ファイルのPath（output/final.mp4）
    """
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

    duration = _get_audio_duration(audio_path)
    slide_duration = duration / len(slide_paths)

    print(f"音声長さ: {duration:.2f}秒 / スライド1枚あたり: {slide_duration:.2f}秒")

    output_path = OUTPUT_DIR / "final.mp4"

    # 各スライドをloop入力として指定し、filterでconcatする
    cmd = ["ffmpeg", "-y"]

    # 各スライドを入力として追加
    for slide_path in slide_paths:
        cmd += ["-loop", "1", "-t", str(slide_duration), "-i", str(slide_path)]

    # 音声入力
    cmd += ["-i", str(audio_path)]

    # filterグラフ: 各スライドをscale→concat
    n = len(slide_paths)
    filter_parts = []
    for i in range(n):
        filter_parts.append(
            f"[{i}:v]scale={WIDTH}:{HEIGHT}:force_original_aspect_ratio=decrease,"
            f"pad={WIDTH}:{HEIGHT}:(ow-iw)/2:(oh-ih)/2,setsar=1,fps={FPS}[v{i}]"
        )
    concat_inputs = "".join(f"[v{i}]" for i in range(n))
    filter_parts.append(f"{concat_inputs}concat=n={n}:v=1:a=0[vout]")
    filter_str = ";".join(filter_parts)

    audio_idx = n  # 音声は最後の入力
    cmd += [
        "-filter_complex", filter_str,
        "-map", "[vout]",
        "-map", f"{audio_idx}:a",
        "-c:v", "libx264",
        "-preset", "fast",
        "-crf", "23",
        "-c:a", "aac",
        "-b:a", "128k",
        "-shortest",
        "-movflags", "+faststart",
        str(output_path),
    ]

    print("FFmpeg実行中...")
    result = subprocess.run(cmd, capture_output=True, text=True)
    if result.returncode != 0:
        raise RuntimeError(
            f"FFmpegが失敗しました (returncode={result.returncode}):\n{result.stderr}"
        )

    print(f"動画保存: {output_path}")
    return output_path
