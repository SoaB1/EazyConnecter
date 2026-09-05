import type { ServerEntry, ServerGroup } from "../types";
import { ServerRow } from "./ServerRow";

interface Props {
  groups: ServerGroup[];
  filterFn: (srv: ServerEntry) => boolean;
  collapsed: Record<string, boolean>;
  onToggleGroup: (name: string) => void;
  selectedHost: string | null;
  onSelect: (host: string) => void;
  onConnect: (srv: ServerEntry) => void;
  onEditCredential: (srv: ServerEntry) => void;
}

export function ServerTable({
  groups,
  filterFn,
  collapsed,
  onToggleGroup,
  selectedHost,
  onSelect,
  onConnect,
  onEditCredential,
}: Props) {
  const visibleGroups = groups
    .map((g) => ({ ...g, servers: g.servers.filter(filterFn) }))
    .filter((g) => g.servers.length > 0);

  const total = visibleGroups.reduce((n, g) => n + g.servers.length, 0);

  return (
    <div className="ec-table">
      <div className="ec-tablehead">
        <div className="ec-tablehead__check" />
        <div>OS</div>
        <div>名前 / ホスト</div>
        <div>タグ</div>
        <div>メモ</div>
        <div>最終接続</div>
        <div>認証</div>
        <div className="ec-tablehead__ops">操作</div>
      </div>

      <div className="ec-tablebody">
        {visibleGroups.length === 0 && (
          <div className="ec-empty">条件に一致する接続先はありません</div>
        )}
        {visibleGroups.map((g) => {
          const isCollapsed = !!collapsed[g.name];
          return (
            <div key={g.name}>
              <div className="ec-grouphead" onClick={() => onToggleGroup(g.name)}>
                <span className="ec-grouphead__caret">{isCollapsed ? "▶" : "▼"}</span>
                <span className="ec-grouphead__name">{g.name}</span>
                <span className="ec-grouphead__count">{g.servers.length} 台</span>
              </div>
              {!isCollapsed &&
                g.servers.map((srv) => (
                  <ServerRow
                    key={srv.host}
                    srv={srv}
                    selected={selectedHost === srv.host}
                    onSelect={onSelect}
                    onConnect={onConnect}
                    onEditCredential={onEditCredential}
                  />
                ))}
            </div>
          );
        })}
      </div>

      <div className="ec-statusbar">
        <span>Enter 接続 · Ctrl+K 検索</span>
        <span className="ec-statusbar__right">
          表示 {total} / 全 {groups.reduce((n, g) => n + g.servers.length, 0)} 台
        </span>
      </div>
    </div>
  );
}
