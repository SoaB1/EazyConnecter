"""DPAPI 暗号化ストア（Windows標準API使用）"""
import base64
import ctypes
import json
import os


class CredentialStore:
    """
    認証情報を DPAPI で暗号化して .credentials ファイルに保存。
    そのPCの、そのWindowsユーザーでしか復号できない。
    """

    CRYPTPROTECT_UI_FORBIDDEN = 0x01

    def __init__(self, path):
        self.path = path
        self._data = {}
        self._load()

    # ── 内部: DPAPI encrypt/decrypt ──────────────
    def _dpapi_encrypt(self, plaintext: str) -> str:
        data   = plaintext.encode("utf-8")
        blob_in = self._make_blob(data)
        blob_out = self._DATA_BLOB()
        ok = ctypes.windll.crypt32.CryptProtectData(
            ctypes.byref(blob_in), None, None, None, None,
            self.CRYPTPROTECT_UI_FORBIDDEN,
            ctypes.byref(blob_out))
        if not ok:
            raise RuntimeError("DPAPI暗号化に失敗しました")
        enc = ctypes.string_at(blob_out.pbData, blob_out.cbData)
        ctypes.windll.kernel32.LocalFree(blob_out.pbData)
        return base64.b64encode(enc).decode("ascii")

    def _dpapi_decrypt(self, b64: str) -> str:
        data    = base64.b64decode(b64)
        blob_in = self._make_blob(data)
        blob_out = self._DATA_BLOB()
        ok = ctypes.windll.crypt32.CryptUnprotectData(
            ctypes.byref(blob_in), None, None, None, None,
            self.CRYPTPROTECT_UI_FORBIDDEN,
            ctypes.byref(blob_out))
        if not ok:
            raise RuntimeError("DPAPI復号に失敗しました（別ユーザー/別PCのデータ）")
        dec = ctypes.string_at(blob_out.pbData, blob_out.cbData)
        ctypes.windll.kernel32.LocalFree(blob_out.pbData)
        return dec.decode("utf-8")

    class _DATA_BLOB(ctypes.Structure):
        _fields_ = [("cbData", ctypes.c_ulong), ("pbData", ctypes.POINTER(ctypes.c_char))]

    def _make_blob(self, data: bytes):
        buf  = ctypes.create_string_buffer(data)
        blob = self._DATA_BLOB()
        blob.cbData = len(data)
        blob.pbData = ctypes.cast(buf, ctypes.POINTER(ctypes.c_char))
        return blob

    # ── ファイルIO ────────────────────────────────
    def _load(self):
        if os.path.exists(self.path):
            with open(self.path, encoding="utf-8") as f:
                self._data = json.load(f)

    def _save(self):
        with open(self.path, "w", encoding="utf-8") as f:
            json.dump(self._data, f, indent=2)

    # ── 公開API ───────────────────────────────────
    def set(self, host: str, username: str, password: str,
            op_item: str = "", op_vault: str = "", op_mode: str = "dpapi"):
        """認証情報を暗号化して保存"""
        enc = self._dpapi_encrypt(password) if password else ""
        self._data[host] = {
            "username":     username,
            "password_enc": enc,
            "op_item":      op_item,
            "op_vault":     op_vault,
            "op_mode":      op_mode,  # "always" or "dpapi"
        }
        self._save()

    def get(self, host: str):
        """復号して (username, password) を返す。未登録なら None"""
        if host not in self._data:
            return None
        entry = self._data[host]
        enc = entry.get("password_enc", "")
        pw  = self._dpapi_decrypt(enc) if enc else ""
        return entry["username"], pw

    def get_op_info(self, host: str) -> dict | None:
        """1Password 連携情報を返す。未登録なら None"""
        if host not in self._data:
            return None
        e = self._data[host]
        return {
            "op_item":  e.get("op_item",""),
            "op_vault": e.get("op_vault",""),
            "op_mode":  e.get("op_mode","dpapi"),
        }

    def delete(self, host: str):
        if host in self._data:
            del self._data[host]
            self._save()

    def has(self, host: str) -> bool:
        return host in self._data
