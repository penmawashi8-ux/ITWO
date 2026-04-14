# YouTube Shorts 自動生成・投稿システム

ITエンジニア向けDX用語解説YouTube Shortsを毎日自動生成・投稿するシステムです。

## 概要

- **Claude API** で最新IT用語を自動選定し、解説スクリプトを生成
- **Pillow** でスライド画像を生成（1080x1920 縦型）
- **VOICEVOX** でナレーション音声を合成
- **FFmpeg** でスライド+音声を合成して動画を生成
- **GitHub Actions** で毎日JST 10:00に自動実行

## ファイル構成

```
project/
├── CLAUDE.md                          # プロジェクト仕様書
├── main.py                            # パイプライン実行エントリポイント
├── requirements.txt                   # Python依存パッケージ
├── used_terms.json                    # 投稿済み用語リスト
├── .env.example                       # 環境変数サンプル
├── pipeline/
│   ├── research.py                    # 用語リサーチ（Claude API）
│   ├── script.py                      # 解説スクリプト生成（Claude API）
│   ├── slide.py                       # スライド画像生成（Pillow）
│   ├── voice.py                       # 音声合成（VOICEVOX）
│   ├── video.py                       # 動画合成（FFmpeg）
│   └── upload.py                      # YouTube投稿（Data API v3）
└── .github/
    └── workflows/
        ├── test_video.yml             # テスト用（手動実行・Artifact出力）
        └── post_short.yml             # 本番用（毎日自動投稿）
```

## セットアップ

### 1. 依存パッケージのインストール

```bash
pip install -r requirements.txt
```

### 2. システム依存のインストール

```bash
# Ubuntu/Debian
sudo apt-get install -y ffmpeg fonts-noto-cjk
```

### 3. 環境変数の設定

```bash
cp .env.example .env
# .env を編集して ANTHROPIC_API_KEY を設定
```

### 4. VOICEVOXの起動

```bash
docker run -d -p 50021:50021 voicevox/voicevox_engine:cpu-ubuntu20.04-latest
```

### 5. ローカルテスト

```bash
TEST_MODE=true python main.py
```

`output/final.mp4` を再生して動画を確認してください。

特定の用語で試す場合:

```bash
TEST_MODE=true FORCE_TERM="生成AI" python main.py
```

## GitHub Secrets の登録

| Secret名 | 説明 |
|----------|------|
| `ANTHROPIC_API_KEY` | Anthropic Console → API Keys |
| `YOUTUBE_CLIENT_SECRET` | Google Cloud Console → OAuth2クライアントIDのJSON全文 |
| `YOUTUBE_TOKEN` | ローカルで初回認証後に生成される token.json の中身 |

## YouTube初回認証手順

1. [Google Cloud Console](https://console.cloud.google.com/) で YouTube Data API v3 を有効化
2. OAuth 2.0 クライアントID（デスクトップアプリ）を作成・ダウンロード
3. ダウンロードしたJSONを `client_secret.json` として配置
4. 以下を実行してブラウザで認証:
   ```bash
   python -c "from pipeline.upload import auth_only; auth_only()"
   ```
5. `token.json` が生成される
6. `token.json` の中身を GitHub Secrets の `YOUTUBE_TOKEN` に登録
7. `client_secret.json` の中身を GitHub Secrets の `YOUTUBE_CLIENT_SECRET` に登録

## GitHub Actions ワークフロー

### テスト実行（手動）

GitHub → Actions → **Test Video Generation** → Run workflow

- `term` を空欄にすると自動選定
- 用語を入力すると指定用語で生成
- 動画・スクリプト・スライドが Artifact としてダウンロード可能（7日間保存）

### 本番自動投稿

毎日 JST 10:00 に自動実行（`post_short.yml`）。

手動でも実行可能: Actions → **Post YouTube Short** → Run workflow

## 動画仕様

- 解像度: 1080x1920（9:16縦型）
- 長さ: 25〜30秒（ナレーション長に依存）
- フレームレート: 30fps
- スライド: 4枚構成（表紙→定義→活用例→まとめ）

## 注意事項

- `output/`, `client_secret.json`, `token.json` は `.gitignore` で除外済み
- `used_terms.json` は投稿のたびに自動更新・コミットされる（`[skip ci]`タグ付き）
- Claude APIモデル: `claude-sonnet-4-20250514`
- VOICEVOXスピーカー: ずんだもん（ID: 1）
