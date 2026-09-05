# EazyConnecter

Windows 向けサーバー接続ランチャー。YAML で管理したサーバーリストから RDP / SSH 接続を素早く起動できます。

![Python](https://img.shields.io/badge/Python-3.8%2B-blue)
![Platform](https://img.shields.io/badge/Platform-Windows-lightgrey)
![License](https://img.shields.io/badge/License-MIT-green)

## 機能

- **RDP 接続**（Windows サーバー）— `mstsc.exe` を自動起動
- **SSH 接続**（Linux サーバー）— Windows Terminal / TeraTerm / PowerShell に対応
- **認証情報の保存**（Windows DPAPI 暗号化）— RDP 自動ログイン・SSH パスワード自動入力
- **YAML によるサーバー管理**— グループ分け・個別設定対応
- **リアルタイム絞り込み検索**
- **ワンクリックリロード**— ツール再起動なしで設定を反映
- **セットアップウィザード**— 配布先 PC での初期設定を GUI でサポート

## スクリーンショット

> *(準備中)*

## ファイル構成

```
EazyConnecter/
├── src/
│   ├── EazyConnecter.py  # メインツール（pywebviewエントリーポイント）
│   ├── api.py            # pywebview js_api層
│   ├── core/             # ビジネスロジック（YAMLパーサー・DPAPI・1Password・接続処理）
│   └── setup.py          # セットアップウィザード
├── frontend/              # GUI本体（React + TypeScript, Vite）
├── scripts/build_exe.ps1 # exe ビルド & ZIP 生成スクリプト
├── config.yaml           # ツール設定
├── servers.yaml          # サーバーリスト
├── VERSION.md            # バージョン管理
└── .credentials          # 認証情報（DPAPI暗号化・自動生成）※ gitignore 対象
```

## 必要環境

### 開発・ビルド環境

| 要件 | バージョン |
|------|-----------|
| Python | 3.13 以上 |
| Node.js | 24 以上（フロントエンドビルド用） |
| Windows | 10 / 11 (64bit) |

### 配布先（エンドユーザー）

- Windows 10 / 11 (64bit)、Microsoft Edge WebView2 ランタイム（多くの環境でプリインストール済み）
- Python / Node.js **不要**（exe 化済み）

## セットアップ

### 開発環境での実行

```powershell
# リポジトリをクローン
git clone https://github.com/SoaB1/EazyConnecter.git
cd EazyConnecter

# Python依存関係
pip install -r requirements.txt

# フロントエンドをビルド
cd frontend && npm install && npm run build && cd ..

# 実行
python src\EazyConnecter.py
```

### exe のビルドと配布

```powershell
# 実行ポリシーの設定（初回のみ）
Set-ExecutionPolicy -Scope CurrentUser RemoteSigned

# ビルド実行
.\scripts\build_exe.ps1
```

`dist\` フォルダと `EazyConnecter_vX.Y.Z.zip` が生成されます。

**配布するファイル:**

```
EazyConnecter_vX.Y.Z.zip
├── EazyConnecter.exe        # メインツール
├── EazyConnecter_Setup.exe  # セットアップウィザード ← 配布先で最初に実行
└── servers.yaml             # サーバーリスト（事前に編集して同梱）
```

### エンドユーザーの手順

1. ZIP を展開
2. `EazyConnecter_Setup.exe` を実行
3. ウィザードに従って設定（配置先・SSH クライアント等）
4. 完了後 `EazyConnecter.exe` を起動

## 設定ファイル

### config.yaml

```yaml
ssh:
  default_client: windowsterminal  # windowsterminal / teraterm / powershell
  teraterm_path: "C:\\Program Files\\teraterm\\ttermpro.exe"
  default_user: ""
  default_key: ""
  default_port: 22

rdp:
  width: ""
  height: ""
  multimon: false

gui:
  title: "EazyConnecter"
  window_width: 760
  window_height: 560
  font_size: 10
```

### servers.yaml

```yaml
groups:
  - name: "グループ名"
    servers:
      - name: "サーバー表示名"
        host: 192.168.1.10
        os: windows          # windows / linux
        user: admin          # SSH ユーザー名（Linux のみ）
        port: 22             # SSH ポート（省略時 22）
        key: ""              # SSH 秘密鍵パス
        ssh_client: ""       # 個別クライアント指定（省略時は config.yaml の設定）
        note: "メモ"
```

## 認証情報の管理

「認証」ボタンからユーザー名・パスワードを登録できます。
保存先は実行ファイルと同フォルダの `.credentials`（Windows DPAPI 暗号化）。
**そのPCの、そのWindowsユーザーでしか復号できないため、ファイルを持ち出しても内容は読めません。**

| OS | 認証情報あり | 認証情報なし |
|---|---|---|
| Windows (RDP) | `cmdkey` で自動ログイン | 手動ログイン |
| Linux (TeraTerm) | `/passwd=` で自動入力 | 手動入力 |
| Linux (WT / PS) | クリップボードにコピー（30秒後クリア） | 手動入力 |

## バージョン管理

`VERSION.md` の `version:` 行がバージョンの唯一の参照元です。

```markdown
version: 1.3.0
```

ビルド時に自動で ZIP 名・GUI タイトルへ反映されます。

## ライセンス

MIT License
