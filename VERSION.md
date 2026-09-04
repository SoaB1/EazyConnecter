# EazyConnecter バージョン情報

## Current

version: 2.3.1
date: 2026-08-20

## Changelog

### 2.3.1 (2026-08-20)
- フィルターラベルのフォントをMeiryo UI・サイズ拡大（文字化け・視認性修正）
- サーバー行の文字色をCLR_FGに統一（背景と同化する問題を修正）
- 旧_make_rowコードを新ダークテーマ版に完全差し替え
- ボタンのpadding増加・フィルター入力欄のhighlightthickness増加

### 2.3.0 (2026-08-20)
- UIをダークテーマに全面刷新
  - カラーパレット: ネイビー背景 + 電光ブルーアクセント
  - ヘッダーを細くしコンテンツ面積を拡大
  - サーバー行の左端カラーバーでOS種別を視覚化
  - ホスト名にConsolas等幅フォントを使用
  - フィルターバーをグループヘッダー色で統合
  - ボタンテキストを英語に統一 (connect / auth)

### 2.2.0 (2026-08-20)
- フィルターを name / host / note の3入力に分割
- グループヘッダーをクリックで折りたたみ可能に（▶/▼トグル）
- ヘッダーに設定フォルダをエクスプローラーで開くボタンを追加

### 2.1.3 (2026-08-20)
- CredentialDialog の __init__ に cfg パラメータが抜けていた問題を修正（認証ボタンが無反応になるバグ）

### 2.1.2 (2026-08-20)
- setup.py の複数箇所で未終端文字列・f文字列のSyntaxErrorを修正

### 2.1.1 (2026-08-20)
- EazyConnecter.py のf文字列内クォート衝突によるSyntaxErrorを修正

### 2.1.0 (2026-08-19)
- セットアップウィザードに 1Password ステップを追加
  - op CLI / 1Password 本体アプリの検出
  - 未インストール時に winget で自動インストール
  - 連携モード（op / service_account / connect）の選択
  - 選択したモードを config.yaml に自動反映

### 2.0.0 (2026-08-19)
- 1Password 連携機能を追加（大規模機能追加）
  - op CLI モード（Individual/Families/Teams/Business）
    - op コマンド自動検出
    - 認証ダイアログに 1Password セクションを追加
    - 取得タイミング: 接続のたびに取得 / DPAPI に保存して使い回す
  - Service Account モード（Business）
    - op CLI + Service Account トークンで無人認証
    - トークンは DPAPI 暗号化してローカル保存
  - 1Password Connect モード（Business）
    - Connect REST API 経由で取得（op コマンド不要）
    - urllib のみ使用（外部ライブラリ不要）
  - config.yaml に onepassword セクションを追加
  - servers.yaml に op_item / op_vault フィールドを追加
  - 認証ダイアログに現在のモードを表示

### 1.6.4 (2026-08-19)
- icon.ico を img/ フォルダで直接管理（リポジトリにコミット）
- build.yml / build_exe.ps1 のアイコン変換ステップを削除
- img/icon.ico を直接 PyInstaller に渡すよう変更

### 1.6.3 (2026-08-19)
- build.yml の --icon オプションを icon.ico 存在時のみ渡すよう変更（アイコン変換スキップ時のビルドエラーを修正）

### 1.6.2 (2026-08-19)
- svg2ico.py の日本語メッセージを英語化（CI環境のcp1252エンコードエラーを修正）
- UTF-8出力を強制するよう変更

### 1.6.1 (2026-08-19)
- svg2ico.py を Inkscape 優先方式に変更（cairosvg の Cairo DLL 不足エラーを修正）
- build.yml の pip install から cairosvg を削除し pillow のみに変更

### 1.6.0 (2026-08-19)
- フォルダ構成を整理
  - src/: EazyConnecter.py, setup.py
  - scripts/: build_exe.ps1, svg2ico.py
  - config/: config.yaml, servers.yaml（テンプレート）
  - img/: icon.svg
- 各スクリプトのファイル参照パスを新構成に合わせて修正
- .gitignore に dist/ .old/ を追加

### 1.5.2 (2026-08-19)
- build.yml の SVG→ICO 変換処理をヒアドキュメントから scripts/svg2ico.py に変更（YAMLシンタックスエラーを修正）
- build_exe.ps1 も同スクリプトを使用するよう統一

### 1.5.1 (2026-08-19)
- icon.svg を img/ フォルダへ移動
- build_exe.ps1 / build.yml のアイコンパスを img/icon.svg に更新

### 1.5.0 (2026-08-19)
- アイコン (icon.svg) を追加
- build_exe.ps1 / build.yml でSVG→ICO自動変換・exeへの組み込みに対応

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
