import { useState } from "react";
import type { ServerEntry } from "../types";

const TAG_COLORS: Record<string, [string, string]> = {
  本番: ["#6E4BDB", "#E8E0FF"],
  検証: ["#1A7F4B", "#D0F0E0"],
  踏み台: ["#0077A8", "#C8E8F8"],
  鍵認証: ["#B05000", "#FFE8C8"],
  Web: ["#444444", "#E0E0E0"],
  DB: ["#8B0000", "#FFD0D0"],
  監視: ["#006060", "#C0F0F0"],
};
const TAG_FALLBACK: [string, string] = ["#30363D", "#8B949E"];

interface Props {
  srv: ServerEntry;
  selected: boolean;
  onSelect: (host: string) => void;
  onConnect: (srv: ServerEntry) => void;
  onEditCredential: (srv: ServerEntry) => void;
}

export function ServerRow({ srv, selected, onSelect, onConnect, onEditCredential }: Props) {
  const [menuOpen, setMenuOpen] = useState(false);
  const isWindows = srv.os.toLowerCase() === "windows";
  const osLabel = isWindows ? "WIN" : "LNX";
  const barColor = isWindows ? "var(--ec-win)" : "var(--ec-lin)";
  const tags = (srv.tags || "").split(",").map((t) => t.trim()).filter(Boolean);
  const hostText = srv.port && srv.port !== "22" ? `${srv.host}:${srv.port}` : srv.host;
  const authLabel = srv.has_credential
    ? srv.auth_has_op_item
      ? "🔑 1P"
      : "🔑 PW"
    : "—";

  return (
    <div
      className={`ec-row${selected ? " ec-row--selected" : ""}`}
      style={{ boxShadow: `inset 3px 0 0 ${barColor}` }}
      onClick={() => onSelect(srv.host)}
      onDoubleClick={() => onConnect(srv)}
    >
      <div className="ec-row__check" onClick={(e) => e.stopPropagation()}>
        {/* 複数選択は次フェーズで実装予定。現時点は表示のみ */}
        <input type="checkbox" disabled />
      </div>
      <div className="ec-row__os" style={{ background: barColor }}>
        {osLabel}
      </div>
      <div className="ec-row__name">
        <span
          className="ec-row__dot"
          style={{ background: srv.has_credential ? "var(--ec-cred)" : "var(--ec-fg-sub)" }}
        />
        <div className="ec-row__namewrap">
          <div className="ec-row__namehost">{srv.name}</div>
          <div className="ec-row__addr">{hostText}</div>
        </div>
      </div>
      <div className="ec-row__tags">
        {tags.map((t) => {
          const [bg, fg] = TAG_COLORS[t] ?? TAG_FALLBACK;
          return (
            <span key={t} className="ec-tag" style={{ background: bg, color: fg }}>
              {t}
            </span>
          );
        })}
      </div>
      <div className="ec-row__note">{srv.note}</div>
      <div className="ec-row__last">—</div>
      <div className={`ec-row__auth${srv.has_credential ? " ec-row__auth--set" : ""}`}>
        {authLabel}
      </div>
      <div className="ec-row__ops" onClick={(e) => e.stopPropagation()}>
        <button
          className="ec-btn ec-btn--connect"
          onClick={() => onConnect(srv)}
        >
          接続
        </button>
        <div className="ec-menu-wrap">
          <button
            className="ec-btn ec-btn--ghost"
            onClick={() => setMenuOpen((v) => !v)}
            title="その他の操作"
          >
            ⋯
          </button>
          {menuOpen && (
            <>
              <div className="ec-menu-backdrop" onClick={() => setMenuOpen(false)} />
              <div className="ec-menu">
                <button
                  onClick={() => {
                    setMenuOpen(false);
                    onEditCredential(srv);
                  }}
                >
                  認証を登録
                </button>
                <button
                  onClick={() => {
                    setMenuOpen(false);
                    onConnect(srv);
                  }}
                >
                  接続
                </button>
              </div>
            </>
          )}
        </div>
      </div>
    </div>
  );
}
