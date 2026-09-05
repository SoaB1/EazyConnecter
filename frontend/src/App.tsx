import { useCallback, useEffect, useMemo, useRef, useState } from "react";
import "./App.css";
import { CredentialDialog } from "./components/CredentialDialog";
import { Header } from "./components/Header";
import { SearchBar } from "./components/SearchBar";
import { ServerTable } from "./components/ServerTable";
import { TagChips } from "./components/TagChips";
import { Toast } from "./components/Toast";
import { connect as apiConnect, openConfigFolder } from "./api/client";
import { useBootstrap } from "./hooks/useBootstrap";
import { useToast } from "./hooks/useToast";
import type { ServerEntry } from "./types";

export default function App() {
  const { data, loading, error, reload } = useBootstrap();
  const { toast, show: showToast } = useToast();

  const [query, setQuery] = useState("");
  const [activeTag, setActiveTag] = useState("");
  const [selectedHost, setSelectedHost] = useState<string | null>(null);
  const [collapsed, setCollapsed] = useState<Record<string, boolean>>({});
  const [credentialSrv, setCredentialSrv] = useState<ServerEntry | null>(null);
  const searchRef = useRef<HTMLInputElement>(null);

  const allServers = useMemo(
    () => (data ? data.groups.flatMap((g) => g.servers) : []),
    [data]
  );

  const tagCounts = useMemo(() => {
    const counts = new Map<string, number>();
    for (const s of allServers) {
      for (const t of (s.tags || "").split(",").map((x) => x.trim()).filter(Boolean)) {
        counts.set(t, (counts.get(t) ?? 0) + 1);
      }
    }
    return [...counts.entries()]
      .sort((a, b) => a[0].localeCompare(b[0], "ja"))
      .map(([tag, count]) => ({ tag, count }));
  }, [allServers]);

  const filterFn = useCallback(
    (srv: ServerEntry) => {
      const tags = (srv.tags || "").split(",").map((t) => t.trim()).filter(Boolean);
      if (activeTag && !tags.includes(activeTag)) return false;
      const q = query.trim().toLowerCase();
      if (!q) return true;
      return (
        srv.name.toLowerCase().includes(q) ||
        srv.host.toLowerCase().includes(q) ||
        (srv.note || "").toLowerCase().includes(q) ||
        tags.some((t) => t.toLowerCase().includes(q))
      );
    },
    [query, activeTag]
  );

  const handleConnect = useCallback(
    async (srv: ServerEntry) => {
      setSelectedHost(srv.host);
      const res = await apiConnect(srv.host);
      if (!res.ok) {
        showToast(res.error ?? "接続に失敗しました。", "error");
        return;
      }
      showToast(res.notice ?? `接続を開始しました: ${srv.name}  [${srv.host}]`, "info");
    },
    [showToast]
  );

  useEffect(() => {
    const onKey = (e: KeyboardEvent) => {
      if ((e.ctrlKey || e.metaKey) && e.key.toLowerCase() === "k") {
        e.preventDefault();
        searchRef.current?.focus();
        return;
      }
      if (e.key === "Enter" && selectedHost) {
        const tag = (document.activeElement?.tagName || "").toLowerCase();
        if (tag === "input" || tag === "textarea") return;
        const srv = allServers.find((s) => s.host === selectedHost);
        if (srv) handleConnect(srv);
      }
    };
    window.addEventListener("keydown", onKey);
    return () => window.removeEventListener("keydown", onKey);
  }, [selectedHost, allServers, handleConnect]);

  if (loading && !data) {
    return <div className="ec-app ec-app--loading">読み込み中…</div>;
  }
  if (error && !data) {
    return <div className="ec-app ec-app--error">読み込みエラー: {error}</div>;
  }
  if (!data) return null;

  return (
    <div className="ec-app">
      <Header
        title={data.config.gui_title}
        version={data.version}
        onReload={async () => {
          await reload();
          showToast("リロード完了");
        }}
        onOpenConfig={() => openConfigFolder()}
        onAddServer={() =>
          showToast("servers.yaml を直接編集して「↺」ボタンでリロードしてください。")
        }
      />
      <SearchBar ref={searchRef} value={query} onChange={setQuery} />
      <TagChips
        tags={tagCounts}
        activeTag={activeTag}
        onToggle={(t) => setActiveTag((cur) => (cur === t ? "" : t))}
      />
      <ServerTable
        groups={data.groups}
        filterFn={filterFn}
        collapsed={collapsed}
        onToggleGroup={(name) =>
          setCollapsed((prev) => ({ ...prev, [name]: !prev[name] }))
        }
        selectedHost={selectedHost}
        onSelect={setSelectedHost}
        onConnect={handleConnect}
        onEditCredential={setCredentialSrv}
      />
      {credentialSrv && (
        <CredentialDialog
          srv={credentialSrv}
          connectionMode={data.config.op_mode}
          onClose={() => setCredentialSrv(null)}
          onSaved={async (message) => {
            setCredentialSrv(null);
            await reload();
            showToast(message);
          }}
          onError={(message) => showToast(message, "error")}
        />
      )}
      <Toast toast={toast} />
    </div>
  );
}
