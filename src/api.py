"""
pywebview の js_api 層。
React 側からは window.pywebview.api.<method>() (Promiseベース) で呼び出す。
どのメソッドも例外を投げず、{"ok": bool, ...} 形式の辞書を返す規約に統一する。
"""
import os
import subprocess

from core.config import parse_yaml_config, parse_yaml_servers
from core.connect import connect_server
from core.credentials import CredentialStore
from core.onepassword import op_get_credential
from core.version import load_version


class Api:
    def __init__(self, base_dir: str):
        self.base_dir = base_dir
        self.store = CredentialStore(os.path.join(base_dir, ".credentials"))
        self._load()

    # ── データ読み込み ────────────────────────────
    def _load(self):
        self.cfg     = parse_yaml_config(os.path.join(self.base_dir, "config.yaml"))
        self.groups  = parse_yaml_servers(os.path.join(self.base_dir, "servers.yaml"))
        self.version = load_version(self.base_dir)

    def _find_server(self, host: str):
        for g in self.groups:
            for s in g["servers"]:
                if s["host"] == host:
                    return s
        return None

    def _serialize(self) -> dict:
        groups = []
        for g in self.groups:
            servers = []
            for s in g["servers"]:
                d = dict(s)
                op_info = self.store.get_op_info(s["host"])
                d["has_credential"]   = self.store.has(s["host"])
                d["auth_mode"]        = (op_info or {}).get("op_mode", "")
                d["auth_has_op_item"] = bool((op_info or {}).get("op_item", ""))
                servers.append(d)
            groups.append({"name": g["name"], "servers": servers})
        return {
            "version": self.version,
            "config":  self.cfg,
            "groups":  groups,
        }

    # ── 公開API：起動時データ取得・リロード ─────────
    def get_bootstrap(self) -> dict:
        return self._serialize()

    def reload(self) -> dict:
        self._load()
        return self._serialize()

    # ── 公開API：接続 ─────────────────────────────
    def connect(self, host: str) -> dict:
        srv = self._find_server(host)
        if srv is None:
            return {"ok": False, "error": f"サーバーが見つかりません: {host}"}
        try:
            result = connect_server(srv, self.cfg, self.store)
            return {"ok": True, "notice": (result or {}).get("notice")}
        except Exception as e:
            return {"ok": False, "error": str(e)}

    # ── 公開API：認証情報 ─────────────────────────
    def get_credential(self, host: str) -> dict:
        """認証情報登録ダイアログを開いた時にだけ、平文を1回返す"""
        cred = self.store.get(host)
        if cred is None:
            return {"ok": False}
        username, password = cred
        return {"ok": True, "username": username, "password": password}

    def save_credential(self, host: str, username: str, password: str,
                         op_item: str, op_vault: str, op_mode: str) -> dict:
        if not op_item and (not username or not password):
            return {"ok": False, "error":
                     "ユーザー名とパスワードを入力するか、1Passwordのアイテム名を指定してください。"}
        try:
            self.store.set(host, username, password, op_item, op_vault, op_mode)
            srv = self._find_server(host)
            if srv is not None:
                # servers.yaml 自体は書き換えず、メモリ上の表示だけ更新する
                srv["op_item"]  = op_item
                srv["op_vault"] = op_vault
            return {"ok": True}
        except Exception as e:
            return {"ok": False, "error": str(e)}

    def delete_credential(self, host: str) -> dict:
        try:
            self.store.delete(host)
            return {"ok": True}
        except Exception as e:
            return {"ok": False, "error": str(e)}

    def fetch_from_1password(self, item: str, vault: str) -> dict:
        if not item:
            return {"ok": False, "error": "アイテム名を入力してください。"}
        try:
            sa_token, connect_tok = "", ""
            if self.cfg.get("op_sa_token_enc"):
                try:
                    sa_token = self.store._dpapi_decrypt(self.cfg["op_sa_token_enc"])
                except Exception:
                    pass
            if self.cfg.get("op_connect_token_enc"):
                try:
                    connect_tok = self.store._dpapi_decrypt(self.cfg["op_connect_token_enc"])
                except Exception:
                    pass
            cred = op_get_credential(
                item, vault,
                mode=self.cfg.get("op_mode", "op"),
                sa_token=sa_token,
                connect_host=self.cfg.get("op_connect_host", "http://localhost:8080"),
                connect_token=connect_tok,
            )
            if cred is None:
                return {"ok": False, "error": "認証情報が取得できませんでした。"}
            username, password = cred
            return {"ok": True, "username": username, "password": password}
        except Exception as e:
            return {"ok": False, "error": str(e)}

    # ── 公開API：その他 ───────────────────────────
    def open_config_folder(self) -> dict:
        try:
            subprocess.Popen(["explorer", self.base_dir])
            return {"ok": True}
        except Exception as e:
            return {"ok": False, "error": str(e)}
