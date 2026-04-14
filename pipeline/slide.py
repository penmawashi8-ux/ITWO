"""
スライド画像生成モジュール
Pillowで4枚のスライド画像を生成する
"""
import textwrap
from pathlib import Path

from PIL import Image, ImageDraw, ImageFont

OUTPUT_DIR = Path(__file__).parent.parent / "output"

# デザイン定数
WIDTH = 1080
HEIGHT = 1920
BG_COLOR = "#1a2744"
ACCENT_COLOR = "#f0a500"
TEXT_COLOR = "#ffffff"
PADDING = 80

FONT_SIZE_TITLE = 80
FONT_SIZE_BODY = 48
FONT_SIZE_SMALL = 36
FONT_SIZE_BADGE = 32


def _find_font(bold: bool = True) -> str:
    """Noto Sans JPフォントのパスを自動検索する"""
    candidates = []
    if bold:
        candidates = [
            "/usr/share/fonts/opentype/noto/NotoSansCJK-Bold.ttc",
            "/usr/share/fonts/opentype/noto/NotoSansCJKjp-Bold.otf",
            "/usr/share/fonts/noto-cjk/NotoSansCJK-Bold.ttc",
            "/usr/share/fonts/truetype/noto/NotoSansCJK-Bold.ttc",
            "/usr/share/fonts/truetype/noto/NotoSansJP-Bold.ttf",
            "/usr/share/fonts/opentype/noto/NotoSansCJK-Regular.ttc",
            "/usr/share/fonts/noto-cjk/NotoSansCJK-Regular.ttc",
        ]
    else:
        candidates = [
            "/usr/share/fonts/opentype/noto/NotoSansCJK-Regular.ttc",
            "/usr/share/fonts/noto-cjk/NotoSansCJK-Regular.ttc",
            "/usr/share/fonts/truetype/noto/NotoSansCJK-Regular.ttc",
            "/usr/share/fonts/truetype/noto/NotoSansJP-Regular.ttf",
        ]

    for path in candidates:
        if Path(path).exists():
            return path

    # フォールバック: システムのデフォルト
    return None


def _get_font(size: int, bold: bool = True) -> ImageFont.FreeTypeFont:
    font_path = _find_font(bold)
    if font_path:
        try:
            return ImageFont.truetype(font_path, size)
        except Exception:
            pass
    return ImageFont.load_default()


def _new_canvas() -> tuple[Image.Image, ImageDraw.ImageDraw]:
    img = Image.new("RGB", (WIDTH, HEIGHT), BG_COLOR)
    draw = ImageDraw.Draw(img)
    return img, draw


def _draw_accent_line(draw: ImageDraw.ImageDraw, y: int) -> None:
    """アクセントカラーの水平線を描画する"""
    draw.rectangle([PADDING, y, WIDTH - PADDING, y + 6], fill=ACCENT_COLOR)


def _wrap_text(text: str, max_chars: int) -> list[str]:
    """日本語テキストを折り返す"""
    return textwrap.wrap(text, width=max_chars)


def _draw_text_centered(
    draw: ImageDraw.ImageDraw,
    text: str,
    y: int,
    font: ImageFont.FreeTypeFont,
    color: str = TEXT_COLOR,
    max_width: int = WIDTH - PADDING * 2,
) -> int:
    """中央揃えでテキストを描画し、次のy座標を返す"""
    lines = _wrap_text(text, max_chars=max(1, max_width // (font.size // 2 + 2)))
    line_height = font.size + 16
    for line in lines:
        bbox = draw.textbbox((0, 0), line, font=font)
        text_w = bbox[2] - bbox[0]
        x = (WIDTH - text_w) // 2
        draw.text((x, y), line, font=font, fill=color)
        y += line_height
    return y


def _draw_slide_number(draw: ImageDraw.ImageDraw, current: int, total: int = 4) -> None:
    """右下にスライド番号を描画する"""
    font = _get_font(28, bold=False)
    text = f"{current}/{total}"
    bbox = draw.textbbox((0, 0), text, font=font)
    tw = bbox[2] - bbox[0]
    draw.text(
        (WIDTH - PADDING - tw, HEIGHT - PADDING - 28),
        text,
        font=font,
        fill=ACCENT_COLOR,
    )


def _slide_cover(data: dict) -> Image.Image:
    """1枚目: 表紙スライド"""
    img, draw = _new_canvas()

    # ゴールドの上部アクセントバー
    draw.rectangle([0, 0, WIDTH, 12], fill=ACCENT_COLOR)

    # 「30秒でわかる」バッジ
    badge_font = _get_font(FONT_SIZE_BADGE)
    badge_text = "30秒でわかる"
    badge_bbox = draw.textbbox((0, 0), badge_text, font=badge_font)
    bw = badge_bbox[2] - badge_bbox[0] + 40
    bh = badge_bbox[3] - badge_bbox[1] + 20
    bx = (WIDTH - bw) // 2
    by = 200
    draw.rounded_rectangle([bx, by, bx + bw, by + bh], radius=8, fill=ACCENT_COLOR)
    draw.text(
        (bx + 20, by + 10),
        badge_text,
        font=badge_font,
        fill="#1a2744",
    )

    # 用語名（日本語・大）
    term_font = _get_font(FONT_SIZE_TITLE)
    term_y = by + bh + 80
    term_y = _draw_text_centered(draw, data["term"], term_y, term_font, TEXT_COLOR)

    # アクセントライン
    _draw_accent_line(draw, term_y + 30)

    # 英語名（小）
    en_font = _get_font(FONT_SIZE_SMALL, bold=False)
    en_y = term_y + 60
    _draw_text_centered(draw, data["term_en"], en_y, en_font, ACCENT_COLOR)

    # ゴールドの下部アクセントバー
    draw.rectangle([0, HEIGHT - 12, WIDTH, HEIGHT], fill=ACCENT_COLOR)

    _draw_slide_number(draw, 1)
    return img


def _slide_definition(data: dict) -> Image.Image:
    """2枚目: 定義スライド"""
    img, draw = _new_canvas()
    draw.rectangle([0, 0, WIDTH, 12], fill=ACCENT_COLOR)

    # セクションラベル
    label_font = _get_font(FONT_SIZE_SMALL)
    label_y = 120
    _draw_text_centered(draw, "定義", label_y, label_font, ACCENT_COLOR)
    _draw_accent_line(draw, label_y + FONT_SIZE_SMALL + 20)

    # 用語名
    term_font = _get_font(FONT_SIZE_BODY + 12)
    term_y = label_y + FONT_SIZE_SMALL + 60
    term_y = _draw_text_centered(draw, data["term"], term_y, term_font, TEXT_COLOR)

    # 定義テキスト
    body_font = _get_font(FONT_SIZE_BODY)
    def_y = HEIGHT // 2 - 100
    _draw_text_centered(draw, data["definition"], def_y, body_font, TEXT_COLOR)

    draw.rectangle([0, HEIGHT - 12, WIDTH, HEIGHT], fill=ACCENT_COLOR)
    _draw_slide_number(draw, 2)
    return img


def _slide_usecase(data: dict) -> Image.Image:
    """3枚目: 活用例スライド"""
    img, draw = _new_canvas()
    draw.rectangle([0, 0, WIDTH, 12], fill=ACCENT_COLOR)

    label_font = _get_font(FONT_SIZE_SMALL)
    label_y = 120
    _draw_text_centered(draw, "活用例", label_y, label_font, ACCENT_COLOR)
    _draw_accent_line(draw, label_y + FONT_SIZE_SMALL + 20)

    # 用語名
    term_font = _get_font(FONT_SIZE_BODY + 12)
    term_y = label_y + FONT_SIZE_SMALL + 60
    term_y = _draw_text_centered(draw, data["term"], term_y, term_font, TEXT_COLOR)

    # 活用例
    body_font = _get_font(FONT_SIZE_BODY)
    uc_y = HEIGHT // 2 - 100

    # チェックマーク付きで表示
    check_font = _get_font(FONT_SIZE_BODY)
    uc_text = f"✓ {data['use_case']}"
    lines = _wrap_text(uc_text, max_chars=18)
    line_height = FONT_SIZE_BODY + 20
    total_h = len(lines) * line_height
    start_y = HEIGHT // 2 - total_h // 2

    for line in lines:
        bbox = draw.textbbox((0, 0), line, font=body_font)
        tw = bbox[2] - bbox[0]
        x = (WIDTH - tw) // 2
        draw.text((x, start_y), line, font=check_font, fill=TEXT_COLOR)
        start_y += line_height

    draw.rectangle([0, HEIGHT - 12, WIDTH, HEIGHT], fill=ACCENT_COLOR)
    _draw_slide_number(draw, 3)
    return img


def _slide_summary(data: dict) -> Image.Image:
    """4枚目: まとめスライド"""
    img, draw = _new_canvas()
    draw.rectangle([0, 0, WIDTH, 12], fill=ACCENT_COLOR)

    label_font = _get_font(FONT_SIZE_SMALL)
    label_y = 120
    _draw_text_centered(draw, "覚えるポイント", label_y, label_font, ACCENT_COLOR)
    _draw_accent_line(draw, label_y + FONT_SIZE_SMALL + 20)

    # 用語名
    term_font = _get_font(FONT_SIZE_BODY + 12)
    term_y = label_y + FONT_SIZE_SMALL + 60
    term_y = _draw_text_centered(draw, data["term"], term_y, term_font, TEXT_COLOR)

    # ポイントを強調表示
    point_font = _get_font(FONT_SIZE_BODY + 8)
    point_text = data["point"]
    point_bbox = draw.textbbox((0, 0), point_text, font=point_font)
    pw = point_bbox[2] - point_bbox[0] + 60
    ph = point_bbox[3] - point_bbox[1] + 40
    px = (WIDTH - pw) // 2
    py = HEIGHT // 2 - ph // 2

    # 背景ボックス（アクセントカラー）
    draw.rounded_rectangle([px, py, px + pw, py + ph], radius=12, fill=ACCENT_COLOR)
    draw.text(
        (px + 30, py + 20),
        point_text,
        font=point_font,
        fill="#1a2744",
    )

    # フォローCTA
    cta_font = _get_font(FONT_SIZE_SMALL - 4, bold=False)
    cta_y = HEIGHT - 200
    _draw_text_centered(
        draw,
        "フォローして毎日IT用語をマスター！",
        cta_y,
        cta_font,
        ACCENT_COLOR,
    )

    draw.rectangle([0, HEIGHT - 12, WIDTH, HEIGHT], fill=ACCENT_COLOR)
    _draw_slide_number(draw, 4)
    return img


def generate(data: dict) -> list[Path]:
    """
    4枚のスライド画像を生成してoutput/に保存する

    Returns:
        生成したスライド画像のPathリスト（slide_0.png 〜 slide_3.png）
    """
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

    slides = [
        _slide_cover(data),
        _slide_definition(data),
        _slide_usecase(data),
        _slide_summary(data),
    ]

    paths = []
    for i, slide in enumerate(slides):
        path = OUTPUT_DIR / f"slide_{i}.png"
        slide.save(str(path))
        paths.append(path)
        print(f"スライド保存: {path}")

    return paths
