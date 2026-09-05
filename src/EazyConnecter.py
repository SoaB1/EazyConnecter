"""
EazyConnecter - サーバー接続ランチャー
Python 3 (pywebview) + React
ビジネスロジックは core/ 以下、GUIは frontend/ (React, pywebviewでホスト) 側。
"""
import os
import sys

import webview

from api import Api


def _base_dir() -> str:
    # exe化時: 実行ファイルのディレクトリ
    # 開発時(src/から実行): 一つ上のルートディレクトリ
    exe_dir = os.path.dirname(os.path.abspath(sys.argv[0]))
    if os.path.basename(exe_dir).lower() == "src":
        return os.path.dirname(exe_dir)
    return exe_dir


def _frontend_entry(base_dir: str) -> str:
    if hasattr(sys, "_MEIPASS"):
        return os.path.join(sys._MEIPASS, "frontend_dist", "index.html")
    return os.path.join(base_dir, "frontend", "dist", "index.html")


def main():
    base_dir = _base_dir()
    api = Api(base_dir)
    cfg = api.cfg

    # 開発時: EAZYCONNECTER_DEV_URL=http://localhost:5173 で Vite dev サーバーに接続
    dev_url = os.environ.get("EAZYCONNECTER_DEV_URL")
    target = dev_url or _frontend_entry(base_dir)

    webview.create_window(
        f"{cfg['gui_title']}  v{api.version}",
        target,
        js_api=api,
        width=cfg["gui_width"],
        height=cfg["gui_height"],
        min_size=(600, 450),
    )
    webview.start(http_server=True)


if __name__ == "__main__":
    main()
