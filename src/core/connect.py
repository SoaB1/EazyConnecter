"""RDP/SSH 接続処理（GUI非依存。UIへは例外送出 or 戻り値のnoticeで結果を伝える）"""
import ctypes
import os
import subprocess
import threading

from .onepassword import op_get_credential


class ConnectError(RuntimeError):
    """接続処理で発生した、ユーザーに見せてよいエラー"""


def connect_server(srv, cfg, store) -> dict:
    """
    srv へ接続する。
    戻り値: {"notice": str | None}（noticeはUIに軽く通知したい情報、例: クリップボードコピー完了）
    失敗時は ConnectError を送出する。
    """
    addr = srv["host"]
    os_  = srv["os"].lower()

    op_mode         = cfg.get("op_mode", "op")
    op_sa_token     = ""
    op_connect_host = cfg.get("op_connect_host", "http://localhost:8080")
    op_connect_tok  = ""

    if cfg.get("op_sa_token_enc"):
        try:
            op_sa_token = store._dpapi_decrypt(cfg["op_sa_token_enc"])
        except Exception:
            pass
    if cfg.get("op_connect_token_enc"):
        try:
            op_connect_tok = store._dpapi_decrypt(cfg["op_connect_token_enc"])
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
    if cred is None and srv.get("op_item", ""):
        try:
            cred = _fetch_from_1p(srv["op_item"], srv.get("op_vault", ""))
        except Exception:
            pass

    if os_ == "windows":
        return _connect_rdp(addr, cfg, cred)
    return _connect_ssh(srv, cfg, addr, cred)


def _connect_rdp(addr, cfg, cred) -> dict:
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
        threading.Timer(5.0, lambda: subprocess.run(
            ["cmdkey", f"/delete:{addr}"], capture_output=True)).start()
    else:
        subprocess.Popen(["mstsc.exe"] + args)
    return {"notice": None}


def _connect_ssh(srv, cfg, addr, cred) -> dict:
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
            raise ConnectError(
                f"TeraTerm が見つかりません:\n{ttp}\n\nconfig.yaml の teraterm_path を確認してください。")
        ta = f"{addr} /ssh /auth=password"
        if user:                          ta += f" /user={user}"
        if port and port != "22":         ta += f" /port={port}"
        if key:                           ta += f' /ssh /auth=publickey /keyfile="{key}"'
        if password:                      ta += f" /passwd={password}"
        subprocess.Popen([ttp] + ta.split())
        return {"notice": None}

    if client == "windowsterminal":
        if password:
            return _ssh_with_password(addr, user, port, key, password)
        try:    subprocess.Popen(["wt.exe", "ssh"] + ssh_args)
        except: subprocess.Popen(["powershell.exe", "-NoExit", "-Command", f"ssh {ssh_str}"])
        return {"notice": None}

    if password:
        return _ssh_with_password(addr, user, port, key, password)
    subprocess.Popen(["powershell.exe", "-NoExit", "-Command", f"ssh {ssh_str}"])
    return {"notice": None}


def _ssh_with_password(addr, user, port, key, password) -> dict:
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
        return {"notice": None}

    # plink なし → Windows Terminal / PowerShell でSSH接続、パスワードをクリップボードへ
    ssh_parts = ["ssh"]
    if port and port != "22": ssh_parts += ["-p", port]
    if key:                   ssh_parts += ["-i", key]
    ssh_parts.append(target)
    ssh_str = " ".join(ssh_parts)

    _set_clipboard_text(password)
    threading.Timer(30.0, _clear_clipboard).start()  # 30秒後に自動クリア

    try:    subprocess.Popen(["wt.exe", "pwsh", "-NoExit", "-Command", ssh_str])
    except: subprocess.Popen(["powershell.exe", "-NoExit", "-Command", ssh_str])

    return {"notice": (
        "SSHを起動しました。パスワードはクリップボードにコピー済みです。"
        "ターミナルで Ctrl+V または右クリックで貼り付けてください"
        "（30秒後に自動クリアされます）。"
    )}


# ── クリップボード（Windows標準APIのみ、tkinter非依存） ──────────
def _set_clipboard_text(text: str) -> bool:
    CF_UNICODETEXT = 13
    GMEM_MOVEABLE  = 0x0002
    user32   = ctypes.windll.user32
    kernel32 = ctypes.windll.kernel32
    if not user32.OpenClipboard(0):
        return False
    try:
        user32.EmptyClipboard()
        data = text.encode("utf-16-le") + b"\x00\x00"
        hglob = kernel32.GlobalAlloc(GMEM_MOVEABLE, len(data))
        if not hglob:
            return False
        lp = kernel32.GlobalLock(hglob)
        ctypes.memmove(lp, data, len(data))
        kernel32.GlobalUnlock(hglob)
        user32.SetClipboardData(CF_UNICODETEXT, hglob)
    finally:
        user32.CloseClipboard()
    return True


def _clear_clipboard():
    user32 = ctypes.windll.user32
    if user32.OpenClipboard(0):
        try:
            user32.EmptyClipboard()
        finally:
            user32.CloseClipboard()
