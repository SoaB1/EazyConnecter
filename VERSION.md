# EazyConnecter バージョン情報

## Current

version: 1.4.0
date: 2026-08-19

## Changelog

### 1.4.0 (2026-08-19)
- バージョン表示をヘッダータイトルに直接組み込み（"EazyConnecter  vX.Y.Z"形式）
- `load_version` が exe 化時に `sys._MEIPASS` を優先参照するよう修正（vunknown問題を解消）
- `build_exe.ps1` で `VERSION.md` を exe に同梱（`--add-data`）・ZIP にも含めるよう対応
- GitHub Actions ワークフローを追加（VERSION.md 更新時に自動ビルド・リリース）

### 1.3.0 (2026-08-19)
- セットアップウィザードのコンテンツエリアをスクロール対応に変更
- SSH設定ページでフッターボタンが隠れる問題を修正

### 1.2.0 (2026-08-19)
- VERSION.md によるバージョン管理を導入
- タイトルバー・ヘッダーにバージョン番号を表示
- ビルド生成ZIPファイル名にバージョン番号を反映 (EazyConnecter_vX.Y.Z.zip)

### 1.1.0 (2026-08-19)
- セットアップウィザード (EazyConnecter_Setup.exe) を追加
  - 配置先フォルダ選択・自動補完（末尾が EazyConnecter でない場合に補完）
  - TeraTerm パス自動検出・手動指定
  - デフォルトSSHクライアント選択
  - デフォルトSSHユーザー名設定
  - デスクトップ・スタートメニューへのショートカット作成（チェックボックス選択）
  - config.yaml 自動生成
- build_exe.ps1 で EazyConnecter_Setup.exe もビルド対象に追加
- ビルド後に配布用 ZIP を自動生成

### 1.0.0 (2026-08-19)
- 初回リリース
- サーバーリスト表示・RDP/SSH 接続 (Windows Terminal / TeraTerm / PowerShell)
- YAML形式のサーバーリスト・設定ファイル管理 (servers.yaml / config.yaml)
- グループ表示・リアルタイム絞り込み検索
- 認証情報の DPAPI 暗号化保存 (.credentials)
  - RDP: cmdkey による自動ログイン
  - SSH TeraTerm: /passwd= オプションで自動入力
  - SSH WT/PS: クリップボード経由（30秒後自動クリア）
- config.yaml / servers.yaml のリロード機能
- build_exe.ps1 による exe ビルド自動化
