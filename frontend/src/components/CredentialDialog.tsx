import { useEffect, useState } from "react";
import { deleteCredential, fetchFrom1Password, getCredential, saveCredential } from "../api/client";
import type { ServerEntry } from "../types";

const MODE_LABELS: Record<string, string> = {
  op: "op CLI (Individual/Families/Teams/Business)",
  service_account: "Service Account (Business)",
  connect: "1Password Connect (Business)",
};

interface Props {
  srv: ServerEntry;
  connectionMode: string; // config.op_mode ("op" | "service_account" | "connect")
  onClose: () => void;
  onSaved: (message: string) => void;
  onError: (message: string) => void;
}

export function CredentialDialog({ srv, connectionMode, onClose, onSaved, onError }: Props) {
  const [opItem, setOpItem] = useState(srv.op_item ?? "");
  const [opVault, setOpVault] = useState(srv.op_vault ?? "");
  const [opTiming, setOpTiming] = useState<"always" | "dpapi">("always");
  const [username, setUsername] = useState(srv.user ?? "");
  const [password, setPassword] = useState("");
  const [showPw, setShowPw] = useState(false);
  const [busy, setBusy] = useState(false);

  useEffect(() => {
    let cancelled = false;
    getCredential(srv.host).then((res) => {
      if (cancelled) return;
      if (res.ok) {
        if (res.username) setUsername(res.username);
        if (res.password) setPassword(res.password);
      }
    });
    return () => {
      cancelled = true;
    };
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [srv.host]);

  useEffect(() => {
    const onKey = (e: KeyboardEvent) => {
      if (e.key === "Escape") onClose();
    };
    window.addEventListener("keydown", onKey);
    return () => window.removeEventListener("keydown", onKey);
  }, [onClose]);

  const handleFetch1p = async () => {
    if (!opItem.trim()) {
      onError("アイテム名を入力してください。");
      return;
    }
    setBusy(true);
    try {
      const res = await fetchFrom1Password(opItem.trim(), opVault.trim());
      if (!res.ok) {
        onError(res.error ?? "認証情報が取得できませんでした。");
        return;
      }
      setUsername(res.username ?? "");
      setPassword(res.password ?? "");
    } finally {
      setBusy(false);
    }
  };

  const handleSave = async () => {
    setBusy(true);
    try {
      const res = await saveCredential(srv.host, username, password, opItem.trim(), opVault.trim(), opTiming);
      if (!res.ok) {
        onError(res.error ?? "保存に失敗しました。");
        return;
      }
      onSaved(`認証情報を保存しました: ${srv.name}`);
    } finally {
      setBusy(false);
    }
  };

  const handleDelete = async () => {
    setBusy(true);
    try {
      const res = await deleteCredential(srv.host);
      if (!res.ok) {
        onError(res.error ?? "削除に失敗しました。");
        return;
      }
      onSaved(`認証情報を削除しました: ${srv.name}`);
    } finally {
      setBusy(false);
    }
  };

  const modeLabel = MODE_LABELS[connectionMode] ?? connectionMode;

  return (
    <div className="ec-modal-backdrop" onMouseDown={onClose}>
      <div className="ec-modal" onMouseDown={(e) => e.stopPropagation()}>
        <div className="ec-modal__title">認証情報 — {srv.name}</div>
        <div className="ec-modal__host">ホスト: {srv.host}</div>

        <fieldset className="ec-op-fieldset">
          <legend>1Password</legend>
          <label className="ec-field">
            <span>アイテム名 (op_item)</span>
            <input value={opItem} onChange={(e) => setOpItem(e.target.value)} />
          </label>
          <label className="ec-field">
            <span>Vault名 (省略可)</span>
            <input value={opVault} onChange={(e) => setOpVault(e.target.value)} />
          </label>
          <div className="ec-radio-row">
            <label>
              <input
                type="radio"
                name="op-timing"
                checked={opTiming === "always"}
                onChange={() => setOpTiming("always")}
              />
              接続のたびに1Passwordから取得
            </label>
            <label>
              <input
                type="radio"
                name="op-timing"
                checked={opTiming === "dpapi"}
                onChange={() => setOpTiming("dpapi")}
              />
              DPAPIに保存して使い回す
            </label>
          </div>
          <div className="ec-op-mode-label">接続モード: {modeLabel}</div>
          <button className="ec-btn ec-btn--op" disabled={busy} onClick={handleFetch1p}>
            1Passwordから取得してフォームに入力
          </button>
        </fieldset>

        <label className="ec-field">
          <span>ユーザー名</span>
          <input value={username} onChange={(e) => setUsername(e.target.value)} />
        </label>
        <label className="ec-field">
          <span>パスワード</span>
          <input
            type={showPw ? "text" : "password"}
            value={password}
            onChange={(e) => setPassword(e.target.value)}
          />
        </label>
        <label className="ec-checkbox-row">
          <input type="checkbox" checked={showPw} onChange={(e) => setShowPw(e.target.checked)} />
          パスワードを表示
        </label>

        <div className="ec-modal__actions">
          <button className="ec-btn ec-btn--primary" disabled={busy} onClick={handleSave}>
            保存
          </button>
          <button className="ec-btn ec-btn--danger" disabled={busy} onClick={handleDelete}>
            削除
          </button>
          <button className="ec-btn ec-btn--ghost" onClick={onClose}>
            キャンセル
          </button>
        </div>
      </div>
    </div>
  );
}
