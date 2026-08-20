"""
EazyConnecter - サーバー接続ランチャー
Python 3 + tkinter (標準ライブラリのみ)
認証情報はWindows DPAPIで暗号化して .credentials に保存
"""

import tkinter as tk
from tkinter import messagebox, simpledialog
import subprocess
import os, sys, re, json, ctypes, base64


# ─────────────────────────────────────────────────
# バージョン読み込み（VERSION.md）
# ─────────────────────────────────────────────────
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


# ─────────────────────────────────────────────────
# 1Password 連携
# モード:
#   op             : op CLI（Individual/Families/Teams/Business）
#   service_account: op CLI + Service Account トークン（Business）
#   connect        : 1Password Connect REST API（Business）
# ─────────────────────────────────────────────────
import shutil as _shutil
import urllib.request as _urllib_req
import urllib.error   as _urllib_err

def detect_op() -> str | None:
    """op コマンドのパスを返す。見つからない場合は None。"""
    return _shutil.which("op")


def _parse_op_fields(fields) -> tuple[str, str]:
    """op CLI / Connect API の fields レスポンスから (username, password) を抽出"""
    user = pw = ""
    if isinstance(fields, list):
        for f in fields:
            purpose = f.get("purpose", "").upper()
            fid     = (f.get("id") or "").lower()
            label   = (f.get("label") or "").lower()
            val     = f.get("value", "")
            if purpose == "USERNAME" or fid == "username" or label == "username":
                user = val
            elif purpose == "PASSWORD" or fid == "password" or label == "password":
                pw = val
    elif isinstance(fields, dict):
        user = fields.get("username", "")
        pw   = fields.get("password", "")
    return user, pw


def op_get_credential_cli(item: str, vault: str = "",
                           sa_token: str = "") -> tuple[str, str] | None:
    """
    op CLI で認証情報を取得。
    sa_token が指定された場合は Service Account モードで動作。
    """
    op = detect_op()
    if op is None:
        raise RuntimeError("op コマンドが見つかりません。1Password CLI をインストールしてください。")
    try:
        env = os.environ.copy()
        if sa_token:
            env["OP_SERVICE_ACCOUNT_TOKEN"] = sa_token

        cmd = [op, "item", "get", item,
               "--fields", "label=username,label=password",
               "--format", "json"]
        if vault:
            cmd += ["--vault", vault]

        result = subprocess.run(cmd, capture_output=True, text=True,
                                timeout=15, env=env)
        if result.returncode != 0:
            raise RuntimeError(result.stderr.strip())

        import json as _json
        fields = _json.loads(result.stdout)
        user, pw = _parse_op_fields(fields)
        return (user, pw) if (user or pw) else None
    except RuntimeError:
        raise
    except Exception as e:
        raise RuntimeError(f"1Password CLI エラー: {e}")


def op_get_credential_connect(item: str, vault: str = "",
                               host: str = "http://localhost:8080",
                               token: str = "") -> tuple[str, str] | None:
    """
    1Password Connect REST API で認証情報を取得。
    host  : Connect サーバーの URL（例: http://localhost:8080）
    token : Connect アクセストークン
    """
    import json as _json

    if not token:
        raise RuntimeError("Connect トークンが設定されていません。")

    headers = {
        "Authorization": f"Bearer {token}",
        "Content-Type":  "application/json",
    }

    def _req(url):
        req = _urllib_req.Request(url, headers=headers)
        with _urllib_req.urlopen(req, timeout=10) as r:
            return _json.loads(r.read().decode())

    try:
        # Vault ID を解決
        vaults = _req(f"{host}/v1/vaults")
        vault_id = None
        if vault:
            for v in vaults:
                if v.get("name","").lower() == vault.lower() or v.get("id") == vault:
                    vault_id = v["id"]
                    break
            if vault_id is None:
                raise RuntimeError(f"Vault '{vault}' が見つかりません。")
        else:
            if not vaults:
                raise RuntimeError("アクセス可能な Vault がありません。")
            vault_id = vaults[0]["id"]

        # アイテムを検索
        items = _req(f"{host}/v1/vaults/{vault_id}/items?filter=title eq "{item}"")
        if not items:
            # フィルター非対応サーバー向けに全件から検索
            items = _req(f"{host}/v1/vaults/{vault_id}/items")
            items = [i for i in items
                     if i.get("title","").lower() == item.lower()
                     or i.get("id") == item]
        if not items:
            raise RuntimeError(f"アイテム '{item}' が見つかりません。")

        item_id   = items[0]["id"]
        item_data = _req(f"{host}/v1/vaults/{vault_id}/items/{item_id}")
        user, pw  = _parse_op_fields(item_data.get("fields", []))
        return (user, pw) if (user or pw) else None

    except RuntimeError:
        raise
    except _urllib_err.URLError as e:
        raise RuntimeError(f"Connect サーバーに接続できません: {e}")
    except Exception as e:
        raise RuntimeError(f"1Password Connect エラー: {e}")


def op_get_credential(item: str, vault: str = "",
                      mode: str = "op",
                      sa_token: str = "",
                      connect_host: str = "",
                      connect_token: str = "") -> tuple[str, str] | None:
    """
    モードに応じて認証情報を取得するディスパッチャ。
    mode: "op" | "service_account" | "connect"
    """
    if mode == "connect":
        return op_get_credential_connect(item, vault,
                                         connect_host or "http://localhost:8080",
                                         connect_token)
    elif mode == "service_account":
        return op_get_credential_cli(item, vault, sa_token)
    else:
        return op_get_credential_cli(item, vault)

# ─────────────────────────────────────────────────
# DPAPI 暗号化ストア（Windows標準API使用）
# ─────────────────────────────────────────────────
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


# ─────────────────────────────────────────────────
# YAML 簡易パーサー
# ─────────────────────────────────────────────────
def parse_yaml_config(path):
    defaults = {
        "ssh_default_client":     "windowsterminal",
        "ssh_teraterm_path":      r"C:\Program Files\teraterm\ttermpro.exe",
        "ssh_default_user":       "",
        "ssh_default_key":        "",
        "ssh_default_port":       "22",
        "rdp_width":              "",
        "rdp_height":             "",
        "rdp_multimon":           False,
        "gui_title":              "EazyConnecter",
        "gui_width":              760,
        "gui_height":             560,
        "gui_font_size":          10,
        # 1Password 連携設定
        "op_mode":                "op",            # op / service_account / connect
        "op_sa_token_enc":        "",              # Service Account トークン（DPAPI暗号化済み）
        "op_connect_host":        "http://localhost:8080",
        "op_connect_token_enc":   "",              # Connect トークン（DPAPI暗号化済み）
    }
    if not os.path.exists(path):
        return defaults
    section = ""
    with open(path, encoding="utf-8") as f:
        for raw in f:
            line = re.sub(r'\s*#.*$', '', raw)
            stripped = line.strip()
            if not stripped: continue
            indent = len(line) - len(line.lstrip())
            if indent == 0 and re.match(r'^(\w+):\s*$', stripped):
                section = re.match(r'^(\w+):', stripped).group(1); continue
            m = re.match(r'^([\w_]+):\s*"?([^"#]*)"?\s*$', stripped)
            if m:
                k, v = m.group(1).strip(), m.group(2).strip()
                key = f"{section}_{k}"
                if   key == "ssh_default_client": defaults["ssh_default_client"] = v
                elif key == "ssh_teraterm_path":  defaults["ssh_teraterm_path"]  = v
                elif key == "ssh_default_user":   defaults["ssh_default_user"]   = v
                elif key == "ssh_default_key":    defaults["ssh_default_key"]    = v
                elif key == "ssh_default_port":   defaults["ssh_default_port"]   = v
                elif key == "rdp_width":          defaults["rdp_width"]          = v
                elif key == "rdp_height":         defaults["rdp_height"]         = v
                elif key == "rdp_multimon":       defaults["rdp_multimon"]       = (v == "true")
                elif key == "gui_title":          defaults["gui_title"]          = v
                elif key == "gui_window_width":   defaults["gui_width"]          = int(v)
                elif key == "gui_window_height":  defaults["gui_height"]         = int(v)
                elif key == "gui_font_size":         defaults["gui_font_size"]          = int(v)
                elif key == "onepassword_mode":              defaults["op_mode"]                = v
                elif key == "onepassword_sa_token_enc":      defaults["op_sa_token_enc"]        = v
                elif key == "onepassword_connect_host":      defaults["op_connect_host"]        = v
                elif key == "onepassword_connect_token_enc": defaults["op_connect_token_enc"]   = v
    return defaults


def parse_yaml_servers(path):
    groups = []
    cur_group = cur_server = None
    in_groups = in_servers = False

    def new_server():
        return {"name":"","host":"","os":"linux","user":"","port":"","key":"","ssh_client":"","note":"","op_item":"","op_vault":""}

    with open(path, encoding="utf-8") as f:
        for raw in f:
            line = re.sub(r'\s*#.*$', '', raw)
            stripped = line.strip()
            if not stripped: continue
            indent = len(line) - len(line.lstrip())

            if indent == 0 and stripped == "groups:":
                in_groups = True; in_servers = False; continue
            if not in_groups: continue

            if indent == 2 and stripped == "-":
                if cur_server and cur_group is not None:
                    cur_group["servers"].append(cur_server); cur_server = None
                if cur_group is not None: groups.append(cur_group)
                cur_group = {"name":"","servers":[]}; in_servers = False; continue

            m = re.match(r'^-\s+name:\s*"?([^"#]*)"?\s*$', stripped)
            if indent == 2 and m:
                if cur_server and cur_group is not None:
                    cur_group["servers"].append(cur_server); cur_server = None
                if cur_group is not None: groups.append(cur_group)
                cur_group = {"name": m.group(1).strip(), "servers":[]}; in_servers = False; continue

            m = re.match(r'^name:\s*"?([^"#]*)"?\s*$', stripped)
            if indent == 4 and m and cur_group is not None and not in_servers:
                cur_group["name"] = m.group(1).strip(); continue

            if indent == 4 and stripped == "servers:":
                in_servers = True; continue
            if not in_servers: continue

            m = re.match(r'^-\s+name:\s*"?([^"#]*)"?\s*$', stripped)
            if indent == 6 and m:
                if cur_server: cur_group["servers"].append(cur_server)
                cur_server = new_server(); cur_server["name"] = m.group(1).strip(); continue

            if indent == 6 and stripped == "-":
                if cur_server: cur_group["servers"].append(cur_server)
                cur_server = new_server(); continue

            m = re.match(r'^([\w_]+):\s*"?([^"#]*)"?\s*$', stripped)
            if indent == 8 and m and cur_server is not None:
                k, v = m.group(1).strip(), m.group(2).strip()
                if k in cur_server: cur_server[k] = v
                continue
            # op_item / op_vault（YAMLのkeyがアンダースコア区切り）
            m2 = re.match(r"^(op_item|op_vault):\s*\"?([^\"#]*)\"?\s*$", stripped)
            if indent == 8 and m2 and cur_server is not None:
                cur_server[m2.group(1)] = m2.group(2).strip()
                continue

    if cur_server and cur_group is not None: cur_group["servers"].append(cur_server)
    if cur_group is not None: groups.append(cur_group)
    return groups


# ─────────────────────────────────────────────────
# 認証情報登録ダイアログ
# ─────────────────────────────────────────────────
class CredentialDialog(tk.Toplevel):
    def __init__(self, parent, srv, store: CredentialStore):
        super().__init__(parent)
        self.title(f"認証情報  —  {srv['name']}")
        self.resizable(False, False)
        self.grab_set()
        self.result  = None
        self.srv     = srv
        self.store   = store
        self.cfg     = cfg or {}
        self._op_mode = self.cfg.get('op_mode', 'op')
        self._op_available = (detect_op() is not None or self._op_mode == 'connect')

        font    = ("Meiryo UI", 10)
        font_sm = ("Meiryo UI", 9)
        font_b  = ("Meiryo UI", 10, "bold")
        CLR_OP  = "#1A7F4B"   # 1Password グリーン

        # 既存データがあれば初期値にセット
        existing  = store.get(srv["host"])
        init_user = existing[0] if existing else (srv.get("user","") or "")
        init_pass = existing[1] if existing else ""

        tk.Label(self, text=f"ホスト:  {srv['host']}", font=font_sm,
                 fg="#555").pack(anchor="w", padx=12, pady=(12,0))

        # ── 1Password セクション ─────────────────
        op_item  = srv.get("op_item","")
        op_vault = srv.get("op_vault","")

        op_fr = tk.LabelFrame(self, text=" 1Password ", font=font_sm,
                              fg=CLR_OP, padx=8, pady=6)
        op_fr.pack(fill="x", padx=12, pady=(8,4))

        # アイテム名
        tk.Label(op_fr, text="アイテム名 (op_item)", font=font_sm).grid(
            row=0, column=0, sticky="w", pady=2)
        self.ent_op_item = tk.Entry(op_fr, font=font, width=26)
        self.ent_op_item.insert(0, op_item)
        self.ent_op_item.grid(row=0, column=1, padx=(6,0), pady=2, sticky="ew")

        # Vault名
        tk.Label(op_fr, text="Vault名 (省略可)", font=font_sm).grid(
            row=1, column=0, sticky="w", pady=2)
        self.ent_op_vault = tk.Entry(op_fr, font=font, width=26)
        self.ent_op_vault.insert(0, op_vault)
        self.ent_op_vault.grid(row=1, column=1, padx=(6,0), pady=2, sticky="ew")
        op_fr.columnconfigure(1, weight=1)

        # 取得タイミング
        self.op_mode = tk.StringVar(value="always")
        mode_fr = tk.Frame(op_fr)
        mode_fr.grid(row=2, column=0, columnspan=2, sticky="w", pady=(4,0))
        tk.Radiobutton(mode_fr, text="接続のたびに1Passwordから取得",
                       variable=self.op_mode, value="always",
                       font=font_sm).pack(side="left", padx=(0,10))
        tk.Radiobutton(mode_fr, text="DPAPIに保存して使い回す",
                       variable=self.op_mode, value="dpapi",
                       font=font_sm).pack(side="left")

        # 取得ボタン
        mode_labels = {
            'op':              'op CLI (Individual/Families/Teams/Business)',
            'service_account': 'Service Account (Business)',
            'connect':         '1Password Connect (Business)',
        }
        mode_label = mode_labels.get(self._op_mode, self._op_mode)
        tk.Label(op_fr, text=f'接続モード: {mode_label}', font=font_sm,
                 fg='#555').grid(row=3, column=0, columnspan=2, sticky='w', pady=(2,6))

        op_state = "normal" if self._op_available else "disabled"
        op_hint  = "" if self._op_available else "  (op コマンドが見つかりません)"
        btn_op_fr = tk.Frame(op_fr)
        btn_op_fr.grid(row=3, column=0, columnspan=2, sticky="w", pady=(6,0))
        tk.Button(btn_op_fr, text="1Passwordから取得してフォームに入力",
                  font=font_sm, bg=CLR_OP, fg="white", relief="flat",
                  state=op_state, cursor="hand2",
                  command=self._fetch_from_op).pack(side="left")
        if op_hint:
            tk.Label(btn_op_fr, text=op_hint, font=font_sm, fg="#C00").pack(side="left", padx=6)

        # ── 手動入力セクション ────────────────────
        tk.Label(self, text="ユーザー名", font=font).pack(anchor="w", padx=12, pady=(8,4))
        self.ent_user = tk.Entry(self, font=font, width=34)
        self.ent_user.insert(0, init_user)
        self.ent_user.pack(padx=12, pady=(0,4), fill="x")

        tk.Label(self, text="パスワード", font=font).pack(anchor="w", padx=12, pady=(4,4))
        self.ent_pass = tk.Entry(self, font=font, width=34, show="●")
        self.ent_pass.insert(0, init_pass)
        self.ent_pass.pack(padx=12, pady=(0,4), fill="x")

        self.show_pw = tk.BooleanVar(value=False)
        tk.Checkbutton(self, text="パスワードを表示", variable=self.show_pw,
                       font=font_sm, command=self._toggle_pw).pack(anchor="w", padx=12)

        # ── ボタン行 ──────────────────────────────
        btn_fr = tk.Frame(self)
        btn_fr.pack(fill="x", padx=12, pady=12)
        tk.Button(btn_fr, text="保存", font=font, width=10,
                  bg="#0078D4", fg="white", relief="flat",
                  command=self._save).pack(side="left", padx=(0,6))
        tk.Button(btn_fr, text="削除", font=font, width=10,
                  bg="#C84614", fg="white", relief="flat",
                  command=self._delete).pack(side="left", padx=(0,6))
        tk.Button(btn_fr, text="キャンセル", font=font, width=10,
                  relief="flat", command=self.destroy).pack(side="right")

        self.center(parent)
        self.ent_op_item.focus_set()
        self.bind("<Escape>", lambda _: self.destroy())

    def _fetch_from_op(self):
        """1Password から認証情報を取得してフォームに入力"""
        item  = self.ent_op_item.get().strip()
        vault = self.ent_op_vault.get().strip()
        if not item:
            messagebox.showwarning("入力エラー", "アイテム名を入力してください。", parent=self)
            return
        try:
            _s = CredentialStore.__new__(CredentialStore)
            _s.__dict__.update({'path':'','_data':{}})
            sa_token    = ''
            connect_tok = ''
            connect_host = self.cfg.get('op_connect_host','http://localhost:8080')
            if self.cfg.get('op_sa_token_enc'):
                try: sa_token = _s._dpapi_decrypt(self.cfg['op_sa_token_enc'])
                except Exception: pass
            if self.cfg.get('op_connect_token_enc'):
                try: connect_tok = _s._dpapi_decrypt(self.cfg['op_connect_token_enc'])
                except Exception: pass
            cred = op_get_credential(
                item, vault,
                mode=self._op_mode,
                sa_token=sa_token,
                connect_host=connect_host,
                connect_token=connect_tok,
            )
            if cred is None:
                messagebox.showwarning("取得失敗", "認証情報が取得できませんでした。", parent=self)
                return
            user, pw = cred
            self.ent_user.delete(0, "end"); self.ent_user.insert(0, user)
            self.ent_pass.delete(0, "end"); self.ent_pass.insert(0, pw)
        except RuntimeError as e:
            messagebox.showerror("1Password エラー", str(e), parent=self)

    def _toggle_pw(self):
        self.ent_pass.config(show="" if self.show_pw.get() else "●")

    def _save(self):
        op_item  = self.ent_op_item.get().strip()
        op_vault = self.ent_op_vault.get().strip()
        op_mode  = self.op_mode.get()
        self.result = ("save",
                       self.ent_user.get(),
                       self.ent_pass.get(),
                       op_item, op_vault, op_mode)
        self.destroy()

    def _delete(self):
        self.result = ("delete", "", "", "", "", "")
        self.destroy()

    def center(self, parent):
        self.update_idletasks()
        pw, ph = parent.winfo_width(), parent.winfo_height()
        px, py = parent.winfo_rootx(), parent.winfo_rooty()
        w, h   = self.winfo_width(), self.winfo_height()
        self.geometry(f"+{px+(pw-w)//2}+{py+(ph-h)//2}")


# ─────────────────────────────────────────────────
# 接続処理
# ─────────────────────────────────────────────────
def connect_server(srv, cfg, store: CredentialStore):
    addr = srv["host"]
    os_  = srv["os"].lower()
    # 1Password 連携設定をcfgから取得
    op_mode         = cfg.get("op_mode", "op")
    op_sa_token     = ""
    op_connect_host = cfg.get("op_connect_host", "http://localhost:8080")
    op_connect_tok  = ""

    # DPAPI 復号（トークンが保存されている場合）
    _store_tmp = CredentialStore.__new__(CredentialStore)
    _store_tmp.__dict__.update({"path":"","_data":{}})
    if cfg.get("op_sa_token_enc"):
        try:
            op_sa_token = _store_tmp._dpapi_decrypt(cfg["op_sa_token_enc"])
        except Exception:
            pass
    if cfg.get("op_connect_token_enc"):
        try:
            op_connect_tok = _store_tmp._dpapi_decrypt(cfg["op_connect_token_enc"])
        except Exception:
            pass

    def _fetch_from_1p(item, vault):
        return op_get_credential(
            item, vault,
            mode=op_mode,
            sa_token=op_sa_token,
            connect_host=op_connect_host,
            connect_token=op_connect_tok,
        )

    # 1Password "always" モードなら毎回取得
    op_info = store.get_op_info(addr)
    if op_info and op_info["op_item"] and op_info["op_mode"] == "always":
        try:
            cred = _fetch_from_1p(op_info["op_item"], op_info["op_vault"])
        except Exception:
            cred = store.get(addr)   # 失敗時はDPAPIにフォールバック
    else:
        cred = store.get(addr)   # (username, password) or None

    # servers.yaml の op_item が直接指定されていてストアに登録がない場合も取得を試みる
    if cred is None and srv.get("op_item",""):
        try:
            cred = _fetch_from_1p(srv["op_item"], srv.get("op_vault",""))
        except Exception:
            pass

    # ── Windows → RDP ───────────────────────────
    if os_ == "windows":
        args = ["/v:" + addr]
        if cfg["rdp_width"] and cfg["rdp_height"]:
            args += [f"/w:{cfg['rdp_width']}", f"/h:{cfg['rdp_height']}"]
        if cfg["rdp_multimon"]:
            args.append("/multimon")

        if cred:
            # cmdkey で資格情報を一時登録 → mstsc 起動 → 登録削除
            u, p = cred
            subprocess.run(["cmdkey", f"/generic:{addr}", f"/user:{u}", f"/pass:{p}"],
                           capture_output=True)
            subprocess.Popen(["mstsc.exe"] + args)
            # 5秒後に削除（mstscが資格情報を読み込む時間を確保）
            import threading
            threading.Timer(5.0, lambda: subprocess.run(
                ["cmdkey", f"/delete:{addr}"], capture_output=True)).start()
        else:
            subprocess.Popen(["mstsc.exe"] + args)
        return

    # ── Linux → SSH ─────────────────────────────
    user   = srv["user"]       or cfg["ssh_default_user"]
    port   = srv["port"]       or cfg["ssh_default_port"]
    key    = srv["key"]        or cfg["ssh_default_key"]
    client = srv["ssh_client"] or cfg["ssh_default_client"]

    # 認証情報ストアのユーザーで上書き
    password = None
    if cred:
        user, password = cred

    target = f"{user}@{addr}" if user else addr

    ssh_args = []
    if port and port != "22": ssh_args += ["-p", port]
    if key:                   ssh_args += ["-i", key]
    ssh_args.append(target)
    ssh_str = " ".join(ssh_args)

    if client == "teraterm":
        ttp = cfg["ssh_teraterm_path"]
        if not os.path.exists(ttp):
            messagebox.showerror("エラー",
                f"TeraTerm が見つかりません:\n{ttp}\n\nconfig.yaml の teraterm_path を確認してください。")
            return
        ta = f"{addr} /ssh /auth=password"
        if user:                          ta += f" /user={user}"
        if port and port != "22":         ta += f" /port={port}"
        if key:                           ta += f' /ssh /auth=publickey /keyfile="{key}"'
        if password:                      ta += f" /passwd={password}"
        subprocess.Popen([ttp] + ta.split())

    elif client == "windowsterminal":
        if password:
            # パスワードありの場合: PowerShell + sshpass相当スクリプトで自動入力
            _ssh_with_password(addr, user, port, key, password)
        else:
            try:    subprocess.Popen(["wt.exe", "ssh"] + ssh_args)
            except: subprocess.Popen(["powershell.exe", "-NoExit", "-Command", f"ssh {ssh_str}"])

    else:
        if password:
            _ssh_with_password(addr, user, port, key, password)
        else:
            subprocess.Popen(["powershell.exe", "-NoExit", "-Command", f"ssh {ssh_str}"])


def _ssh_with_password(addr, user, port, key, password):
    """
    PowerShell + plink (PuTTY) があれば使い、なければ
    Windows Terminal で SSH 接続後にパスワードをクリップボードへコピーして通知する。
    """
    # plink があればそちらで自動入力（最も確実）
    plink_paths = [
        r"C:\Program Files\PuTTY\plink.exe",
        r"C:\Program Files (x86)\PuTTY\plink.exe",
        os.path.join(os.environ.get("LOCALAPPDATA",""), r"Programs\PuTTY\plink.exe"),
    ]
    plink = next((p for p in plink_paths if os.path.exists(p)), None)

    port_arg = ["-P", port] if port and port != "22" else []
    key_arg  = ["-i", key]  if key else []
    target   = f"{user}@{addr}" if user else addr

    if plink:
        cmd = [plink, "-ssh", "-pw", password] + port_arg + key_arg + [target]
        subprocess.Popen(["wt.exe", "--", "cmd", "/k"] + cmd,
                         creationflags=subprocess.CREATE_NEW_CONSOLE)
        return

    # plink なし → Windows Terminal / PowerShell でSSH接続、パスワードをクリップボードへ
    ssh_parts = ["ssh"]
    if port and port != "22": ssh_parts += ["-p", port]
    if key:                   ssh_parts += ["-i", key]
    ssh_parts.append(target)
    ssh_str = " ".join(ssh_parts)

    # クリップボードへパスワードをコピー
    try:
        import tkinter as _tk
        _r = _tk.Tk(); _r.withdraw()
        _r.clipboard_clear()
        _r.clipboard_append(password)
        _r.update()
        _r.after(30000, _r.destroy)  # 30秒後に自動クリア
        _r.mainloop()
    except Exception:
        pass

    try:    subprocess.Popen(["wt.exe", "pwsh", "-NoExit", "-Command", ssh_str])
    except: subprocess.Popen(["powershell.exe", "-NoExit", "-Command", ssh_str])

    messagebox.showinfo("パスワードをコピーしました",
        f"SSHを起動しました。\n\nパスワードはクリップボードにコピー済みです。\n"
        f"ターミナルで Ctrl+V またはマウス右クリックで貼り付けてください。\n\n"
        f"（30秒後にクリップボードは自動クリアされます）")


# ─────────────────────────────────────────────────
# GUI
# ─────────────────────────────────────────────────
class App:
    CLR_BG     = "#F5F6FA"
    CLR_PANEL  = "#FFFFFF"
    CLR_ACCENT = "#0078D4"
    CLR_GROUP  = "#E1EEFF"
    CLR_HOVER  = "#D2E6FF"
    CLR_WIN    = "#0078D4"
    CLR_LIN    = "#C84614"
    CLR_NOTE   = "#6E6E6E"
    CLR_SEP    = "#E1E4EB"
    CLR_STATUS = "#D7DEF0"
    CLR_WHITE  = "#FFFFFF"
    CLR_HDR_FG = "#FFFFFF"
    CLR_CRED   = "#107C10"   # 認証情報登録済みバッジ色

    def __init__(self, root, base_dir):
        self.root     = root
        self.base_dir = base_dir
        self.version  = load_version(base_dir)
        self.store    = CredentialStore(os.path.join(base_dir, ".credentials"))
        self._load_data()
        self._build_layout()
        self._render_list()

    def _load_data(self):
        self.cfg    = parse_yaml_config( os.path.join(self.base_dir, "config.yaml"))
        self.groups = parse_yaml_servers(os.path.join(self.base_dir, "servers.yaml"))
        fs = self.cfg["gui_font_size"]
        self.font_normal = ("Meiryo UI", fs)
        self.font_bold   = ("Meiryo UI", fs, "bold")
        self.font_small  = ("Meiryo UI", fs - 1)
        self.font_badge  = ("Meiryo UI", 8, "bold")
        self.font_title  = ("Meiryo UI", fs + 2, "bold")

    def _build_layout(self):
        cfg = self.cfg
        self.root.title(f"{cfg['gui_title']}  v{self.version}")
        self.root.geometry(f"{cfg['gui_width']}x{cfg['gui_height']}")
        self.root.minsize(540, 400)
        self.root.configure(bg=self.CLR_BG)

        # ヘッダー
        self.hdr_frame = tk.Frame(self.root, bg=self.CLR_ACCENT, height=44)
        self.hdr_frame.pack(side="top", fill="x")
        self.hdr_frame.pack_propagate(False)
        self.lbl_title = tk.Label(
            self.hdr_frame, text=f"  {cfg['gui_title']}  v{self.version}",
            font=self.font_title, bg=self.CLR_ACCENT, fg=self.CLR_HDR_FG, anchor="w")
        self.lbl_title.pack(side="left", fill="both", expand=True, padx=4)
        tk.Button(self.hdr_frame, text="⟳  リロード",
                  font=("Meiryo UI", cfg["gui_font_size"] - 1),
                  bg="#005A9E", fg=self.CLR_WHITE, relief="flat", bd=0,
                  cursor="hand2", activebackground="#004578",
                  activeforeground=self.CLR_WHITE, padx=10,
                  command=self._reload).pack(side="right", padx=8, pady=8, fill="y")

        # 検索バー
        search_fr = tk.Frame(self.root, bg=self.CLR_BG, height=36)
        search_fr.pack(side="top", fill="x")
        search_fr.pack_propagate(False)
        self.search_var = tk.StringVar()
        self.search_var.trace_add("write", lambda *_: self._render_list())
        self._placeholder      = "サーバー名 / ホスト / メモで絞り込み..."
        self._placeholder_active = True
        self.search_entry = tk.Entry(search_fr, textvariable=self.search_var,
                                     font=self.font_normal, relief="solid", bd=1, fg="#888888")
        self.search_entry.insert(0, self._placeholder)
        self.search_entry.pack(fill="x", padx=8, pady=5)
        self.search_entry.bind("<FocusIn>",  self._on_search_focus)
        self.search_entry.bind("<FocusOut>", self._on_search_blur)

        # ステータスバー
        self.status_var = tk.StringVar(value="接続先を選択してダブルクリックで接続")
        status_fr = tk.Frame(self.root, bg=self.CLR_STATUS, height=28)
        status_fr.pack(side="bottom", fill="x")
        status_fr.pack_propagate(False)
        tk.Label(status_fr, textvariable=self.status_var,
                 font=self.font_small, bg=self.CLR_STATUS,
                 anchor="w", padx=8).pack(fill="both", expand=True)

        # スクロールエリア
        container = tk.Frame(self.root, bg=self.CLR_BG)
        container.pack(side="top", fill="both", expand=True)
        self.canvas = tk.Canvas(container, bg=self.CLR_BG, highlightthickness=0, bd=0)
        sb = tk.Scrollbar(container, orient="vertical", command=self.canvas.yview)
        self.canvas.configure(yscrollcommand=sb.set)
        sb.pack(side="right", fill="y")
        self.canvas.pack(side="left", fill="both", expand=True)
        self.inner    = tk.Frame(self.canvas, bg=self.CLR_BG)
        self.inner_id = self.canvas.create_window((0,0), window=self.inner, anchor="nw")
        self.inner.bind("<Configure>",  lambda _: self.canvas.configure(
                                         scrollregion=self.canvas.bbox("all")))
        self.canvas.bind("<Configure>", self._on_canvas_configure)
        self.canvas.bind("<MouseWheel>", self._on_mousewheel)
        self.inner.bind("<MouseWheel>",  self._on_mousewheel)

    # ── リロード ───────────────────────────────────
    def _reload(self):
        try:
            self._load_data()
            self.root.title(f"{self.cfg['gui_title']}  v{self.version}")
            self.lbl_title.config(text=f"  {self.cfg['gui_title']}  v{self.version}",
                                  font=self.font_title)
            self._reset_search()
            self._render_list()
            self.status_var.set("リロード完了")
        except Exception as e:
            messagebox.showerror("リロードエラー", str(e))

    def _reset_search(self):
        self.search_var.set("")
        self.search_entry.delete(0, "end")
        self.search_entry.insert(0, self._placeholder)
        self.search_entry.config(fg="#888888")
        self._placeholder_active = True

    def _on_search_focus(self, _):
        if self._placeholder_active:
            self.search_entry.delete(0, "end")
            self.search_entry.config(fg="#000000")
            self._placeholder_active = False

    def _on_search_blur(self, _):
        if self.search_var.get() == "":
            self.search_entry.insert(0, self._placeholder)
            self.search_entry.config(fg="#888888")
            self._placeholder_active = True

    def _get_filter(self):
        return "" if self._placeholder_active else self.search_var.get()

    def _on_canvas_configure(self, event):
        self.canvas.itemconfig(self.inner_id, width=event.width)
        self._render_list()

    def _on_mousewheel(self, event):
        self.canvas.yview_scroll(-1 * (event.delta // 120), "units")

    # ── リスト描画 ─────────────────────────────────
    def _render_list(self):
        for w in self.inner.winfo_children():
            w.destroy()
        flt   = self._get_filter().lower()
        total = 0
        W     = max(self.canvas.winfo_width() - 4, 300)

        for grp in self.groups:
            servers = [s for s in grp["servers"] if not flt or
                       flt in s["name"].lower() or
                       flt in s["host"].lower()  or
                       flt in s["note"].lower()]
            if not servers: continue

            gh = tk.Frame(self.inner, bg=self.CLR_GROUP, height=26)
            gh.pack(fill="x", pady=(4,0))
            gh.pack_propagate(False)
            tk.Label(gh, text=f"  {grp['name']}  ({len(servers)})",
                     font=self.font_bold, bg=self.CLR_GROUP,
                     fg=self.CLR_ACCENT, anchor="w").pack(fill="both", expand=True)

            for srv in servers:
                self._make_row(srv, W)
                total += 1

        self.status_var.set(
            f"{total} 件がヒット (フィルター: {flt})" if flt else
            f"接続先を選択してダブルクリックで接続  — 合計 {total} 台")

    # ── サーバー行 ─────────────────────────────────
    def _make_row(self, srv, W):
        os_        = srv["os"].lower()
        bg_badge   = self.CLR_WIN if os_ == "windows" else self.CLR_LIN
        badge_text = "Windows"    if os_ == "windows" else "Linux"
        has_cred   = self.store.has(srv["host"])

        row = tk.Frame(self.inner, bg=self.CLR_PANEL, height=54)
        row.pack(fill="x", pady=(0,1))
        row.pack_propagate(False)

        # OSバッジ
        badge = tk.Label(row, text=badge_text, font=self.font_badge,
                         bg=bg_badge, fg=self.CLR_WHITE, width=7, relief="flat")
        badge.place(x=10, y=15, height=24)

        # 認証情報バッジ（登録済みの場合のみ）
        if has_cred:
            cred_badge = tk.Label(row, text="鍵", font=("Meiryo UI", 8, "bold"),
                                  bg=self.CLR_CRED, fg=self.CLR_WHITE, width=2, relief="flat")
            cred_badge.place(x=82, y=15, height=24)
            name_x = 110
        else:
            name_x = 86

        # サーバー名
        lbl_name = tk.Label(row, text=srv["name"], font=self.font_bold,
                            bg=self.CLR_PANEL, fg="#1A1A1A", anchor="w")
        lbl_name.place(x=name_x, y=7, height=22, width=W - name_x - 140)

        # ホスト
        lbl_host = tk.Label(row, text=srv["host"], font=self.font_small,
                            bg=self.CLR_PANEL, fg=self.CLR_ACCENT, anchor="w")
        lbl_host.place(x=name_x, y=30, height=18, width=180)

        # メモ
        if srv["note"]:
            lbl_note = tk.Label(row, text=srv["note"], font=self.font_small,
                                bg=self.CLR_PANEL, fg=self.CLR_NOTE, anchor="w")
            lbl_note.place(x=name_x+180, y=30, height=18, width=max(W - name_x - 330, 40))

        # 認証情報ボタン
        btn_cred = tk.Button(row, text="認証", font=("Meiryo UI", 9),
                             bg=self.CLR_CRED if has_cred else "#888888",
                             fg=self.CLR_WHITE, relief="flat", cursor="hand2", bd=0,
                             activebackground="#0a5c0a", activeforeground=self.CLR_WHITE,
                             command=lambda s=srv: self._edit_credential(s))
        btn_cred.place(x=W - 136, y=13, width=46, height=28)

        # 接続ボタン
        btn = tk.Button(row, text="接続", font=self.font_normal,
                        bg=self.CLR_ACCENT, fg=self.CLR_WHITE,
                        relief="flat", cursor="hand2", bd=0,
                        activebackground="#106EBE", activeforeground=self.CLR_WHITE,
                        command=lambda s=srv: self._do_connect(s))
        btn.place(x=W - 82, y=13, width=58, height=28)

        sep = tk.Frame(row, bg=self.CLR_SEP, height=1)
        sep.place(x=0, rely=1.0, relwidth=1.0, anchor="sw")

        hover_widgets = [row, badge, lbl_name, lbl_host]

        def on_enter(_, r=row, hw=hover_widgets, bc=bg_badge, b=btn, ba=badge):
            r.config(bg=self.CLR_HOVER)
            for w in hw: w.config(bg=self.CLR_HOVER)
            ba.config(bg=bc); b.config(bg=self.CLR_ACCENT)

        def on_leave(_, r=row, hw=hover_widgets, bc=bg_badge, b=btn, ba=badge):
            r.config(bg=self.CLR_PANEL)
            for w in hw: w.config(bg=self.CLR_PANEL)
            ba.config(bg=bc); b.config(bg=self.CLR_ACCENT)

        def on_dbl(_, s=srv): self._do_connect(s)

        for w in hover_widgets:
            w.bind("<Enter>",      on_enter)
            w.bind("<Leave>",      on_leave)
            w.bind("<Double-1>",   on_dbl)
            w.bind("<MouseWheel>", self._on_mousewheel)

    # ── 認証情報編集 ───────────────────────────────
    def _edit_credential(self, srv):
        dlg = CredentialDialog(self.root, srv, self.store, self.cfg)
        self.root.wait_window(dlg)
        if dlg.result is None:
            return
        action, user, pw, op_item, op_vault, op_mode = dlg.result
        if action == "save":
            # op_item があればユーザー/パスは省略可
            if not op_item and (not user or not pw):
                messagebox.showwarning("入力エラー",
                    "ユーザー名とパスワードを入力するか、1Passwordのアイテム名を指定してください。")
                return
            self.store.set(srv["host"], user, pw, op_item, op_vault, op_mode)
            # servers.yaml の op_item も更新（メモリ上のみ）
            srv["op_item"]  = op_item
            srv["op_vault"] = op_vault
            self.status_var.set(f"認証情報を保存しました: {srv['name']}")
        elif action == "delete":
            self.store.delete(srv["host"])
            self.status_var.set(f"認証情報を削除しました: {srv['name']}")
        self._render_list()

    # ── 接続 ───────────────────────────────────────
    def _do_connect(self, srv):
        try:
            connect_server(srv, self.cfg, self.store)
            self.status_var.set(f"接続を開始しました: {srv['name']}  [{srv['host']}]")
        except Exception as e:
            messagebox.showerror("接続エラー", str(e))


# ─────────────────────────────────────────────────
# エントリーポイント
# ─────────────────────────────────────────────────
def main():
    # exe化時: 実行ファイルのディレクトリ
    # 開発時(src/から実行): 一つ上のルートディレクトリ
    exe_dir = os.path.dirname(os.path.abspath(sys.argv[0]))
    if os.path.basename(exe_dir).lower() == "src":
        base = os.path.dirname(exe_dir)
    else:
        base = exe_dir
    root = tk.Tk()
    App(root, base)
    root.mainloop()

if __name__ == "__main__":
    main()
