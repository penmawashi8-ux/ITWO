"""
YouTube投稿モジュール
YouTube Data API v3で動画を投稿する
"""
import os
from pathlib import Path

from dotenv import load_dotenv
from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow
from googleapiclient.discovery import build
from googleapiclient.http import MediaFileUpload

load_dotenv()

SCOPES = ["https://www.googleapis.com/auth/youtube.upload"]
CATEGORY_ID = "27"  # 教育


def _get_credentials() -> Credentials:
    """OAuth2認証情報を取得する"""
    client_secret_path = os.getenv(
        "YOUTUBE_CLIENT_SECRET_PATH", "./client_secret.json"
    )
    token_path = os.getenv("YOUTUBE_TOKEN_PATH", "./token.json")

    creds = None

    if Path(token_path).exists():
        creds = Credentials.from_authorized_user_file(token_path, SCOPES)

    if not creds or not creds.valid:
        if creds and creds.expired and creds.refresh_token:
            creds.refresh(Request())
        else:
            if not Path(client_secret_path).exists():
                raise FileNotFoundError(
                    f"client_secret.json が見つかりません: {client_secret_path}\n"
                    "Google Cloud Consoleで OAuth2クライアントIDを作成し、\n"
                    "JSONをダウンロードして配置してください。"
                )
            flow = InstalledAppFlow.from_client_secrets_file(
                client_secret_path, SCOPES
            )
            creds = flow.run_local_server(port=0)

        with open(token_path, "w") as f:
            f.write(creds.to_json())

    return creds


def auth_only() -> None:
    """
    YouTube OAuth2認証のみを行い、token.jsonを生成する
    初回認証時に実行するユーティリティ関数
    """
    creds = _get_credentials()
    token_path = os.getenv("YOUTUBE_TOKEN_PATH", "./token.json")
    print(f"認証成功。token.json を保存しました: {token_path}")
    print(
        "token.json の内容を GitHub Secrets の YOUTUBE_TOKEN に登録してください。"
    )


def post(data: dict, video_path: Path) -> str:
    """
    YouTube Shortsとして動画を投稿する

    Args:
        data: スクリプトデータ（script.py の generate() 戻り値）
              + metadata（title, description, tags）を含む
        video_path: 動画ファイルのPath

    Returns:
        投稿した動画のURL
    """
    creds = _get_credentials()
    youtube = build("youtube", "v3", credentials=creds)

    term = data["term"]
    title = data.get("title", f"【30秒】{term}とは？#Shorts")
    description = data.get(
        "description",
        f"{term}を30秒で解説します。\n\n{data.get('definition', '')}\n\n#Shorts #ITエンジニア #DX",
    )
    tags = data.get("tags", [term, "ITエンジニア", "DX", "Shorts", "IT用語"])

    body = {
        "snippet": {
            "title": title,
            "description": description,
            "tags": tags,
            "categoryId": CATEGORY_ID,
        },
        "status": {
            "privacyStatus": "public",
            "selfDeclaredMadeForKids": False,
        },
    }

    media = MediaFileUpload(
        str(video_path),
        mimetype="video/mp4",
        resumable=True,
        chunksize=1024 * 1024,  # 1MB chunks
    )

    print(f"YouTube投稿中: {title}")
    request = youtube.videos().insert(
        part="snippet,status",
        body=body,
        media_body=media,
    )

    response = None
    while response is None:
        status, response = request.next_chunk()
        if status:
            pct = int(status.progress() * 100)
            print(f"  アップロード進捗: {pct}%")

    video_id = response["id"]
    url = f"https://www.youtube.com/shorts/{video_id}"
    print(f"投稿完了: {url}")
    return url
