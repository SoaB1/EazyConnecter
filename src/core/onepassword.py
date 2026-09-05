"""
1Password 連携
モード:
  op             : op CLI（Individual/Families/Teams/Business）
  service_account: op CLI + Service Account トークン（Business）
  connect        : 1Password Connect REST API（Business）
"""
import json as _json
import os
import shutil as _shutil
import subprocess
import urllib.error as _urllib_err
import urllib.request as _urllib_req


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
        items = _req(f"{host}/v1/vaults/{vault_id}/items?filter=title eq '{item}'")
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
