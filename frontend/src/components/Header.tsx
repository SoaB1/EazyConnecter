interface Props {
  title: string;
  version: string;
  onReload: () => void;
  onOpenConfig: () => void;
  onAddServer: () => void;
}

export function Header({ title, version, onReload, onOpenConfig, onAddServer }: Props) {
  return (
    <header className="ec-header">
      <span className="ec-header__accent" />
      <span className="ec-header__title">{title}</span>
      <span className="ec-header__version">v{version}</span>
      <div className="ec-header__actions">
        <button className="ec-hbtn" onClick={onReload} title="一覧を更新">
          ↺
        </button>
        <button className="ec-hbtn" onClick={onOpenConfig} title="設定フォルダを開く">
          ⊞&nbsp;設定
        </button>
        <button className="ec-hbtn" onClick={onAddServer} title="接続先を追加">
          ＋&nbsp;接続先を追加
        </button>
      </div>
    </header>
  );
}
