"""バージョン読み込み（VERSION.md）"""
import os
import re
import sys


def load_version(base_dir: str) -> str:
    """
    VERSION.md の "version: X.Y.Z" 行からバージョン文字列を返す。
    exe化時は sys._MEIPASS も検索する。見つからない場合は "unknown" を返す。
    """
    candidates = [base_dir]
    if hasattr(sys, "_MEIPASS"):
        candidates.insert(0, sys._MEIPASS)
    for d in candidates:
        path = os.path.join(d, "VERSION.md")
        if not os.path.exists(path):
            continue
        with open(path, encoding="utf-8") as f:
            for line in f:
                m = re.match(r"^\s*version:\s*([0-9]+\.[0-9]+\.[0-9]+)", line)
                if m:
                    return m.group(1)
    return "unknown"
