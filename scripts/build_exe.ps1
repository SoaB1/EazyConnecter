# EazyConnecter - exe ビルドスクリプト
# 実行: .\build_exe.ps1
# 出力:
#   dist\EazyConnecter.exe          ... メインツール
#   dist\EazyConnecter_Setup.exe    ... セットアップウィザード
#   dist\servers.yaml               ... サーバーリスト
#   EazyConnecter_vX.Y.Z.zip        ... 配布用 ZIP（上記3ファイルをまとめたもの）

# scripts/ から実行されるのでルートディレクトリへ移動
Set-Location (Join-Path (Split-Path -Parent $MyInvocation.MyCommand.Path) "..")
Write-Host ""
Write-Host "=== EazyConnecter exe ビルド ===" -ForegroundColor Cyan

# [0/5] SVG → ICO 変換
Write-Host ""
Write-Host "[0/5] アイコンを変換中..." -ForegroundColor Yellow

if (-not (Test-Path "img/icon.ico")) {
    if (Test-Path "img/icon.svg") {
        # Pillow で SVG→ICO 変換（cairosvg + Pillow）
        $convertScript = @"
try:
    import cairosvg, io
    from PIL import Image
    sizes = [16, 32, 48, 64, 128, 256]
    imgs = []
    for s in sizes:
        png = cairosvg.svg2png(url='img/icon.svg', output_width=s, output_height=s)
        imgs.append(Image.open(io.BytesIO(png)).convert('RGBA'))
    imgs[0].save('icon.ico', format='ICO', sizes=[(i.width, i.height) for i in imgs],
                 append_images=imgs[1:])
    print('OK: cairosvg')
except Exception as e1:
    try:
        from PIL import Image
        img = Image.open('img/icon.svg').convert('RGBA')
        img.save('icon.ico', format='ICO', sizes=[(256,256),(128,128),(64,64),(48,48),(32,32),(16,16)])
        print('OK: pillow')
    except Exception as e2:
        print(f'SKIP: {e2}')
"@
        $convertScript | python
        if (-not (Test-Path "icon.ico")) {
            Write-Host "  cairosvg/Pillow が無い場合は pip install cairosvg pillow を実行してください" -ForegroundColor Yellow
            Write-Host "  icon.ico なしでビルドを続行します" -ForegroundColor Yellow
        }
        else {
            Write-Host "  icon.svg → icon.ico 変換完了" -ForegroundColor Green
        }
    }
    else {
        Write-Host "  icon.svg が見つかりません（スキップ）" -ForegroundColor Yellow
    }
}
else {
    Write-Host "  icon.ico は既に存在します（スキップ）" -ForegroundColor Green
}

# [1/6] フロントエンド（React）をビルド
Write-Host ""
Write-Host "[1/6] フロントエンドをビルド中..." -ForegroundColor Yellow
Push-Location frontend
npm ci
if ($LASTEXITCODE -ne 0) {
    Write-Host "[エラー] npm ci に失敗しました。" -ForegroundColor Red
    Pop-Location
    exit 1
}
npm run build
if ($LASTEXITCODE -ne 0) {
    Write-Host "[エラー] フロントエンドのビルドに失敗しました。" -ForegroundColor Red
    Pop-Location
    exit 1
}
Pop-Location
Write-Host "  OK" -ForegroundColor Green

# [2/6] Python依存パッケージ確認
Write-Host ""
Write-Host "[2/6] Python依存パッケージを確認中..." -ForegroundColor Yellow
python -m PyInstaller --version 2>&1 | Out-Null
if ($LASTEXITCODE -ne 0) {
    Write-Host "  PyInstaller をインストール中..." -ForegroundColor Yellow
    python -m pip install pyinstaller
    if ($LASTEXITCODE -ne 0) {
        Write-Host "[エラー] PyInstaller のインストールに失敗しました。" -ForegroundColor Red
        exit 1
    }
}
python -c "import webview" 2>&1 | Out-Null
if ($LASTEXITCODE -ne 0) {
    Write-Host "  pywebview をインストール中..." -ForegroundColor Yellow
    python -m pip install pywebview
    if ($LASTEXITCODE -ne 0) {
        Write-Host "[エラー] pywebview のインストールに失敗しました。" -ForegroundColor Red
        exit 1
    }
}
Write-Host "  OK" -ForegroundColor Green

# [3/6] EazyConnecter.exe ビルド
Write-Host ""
Write-Host "[3/6] EazyConnecter.exe をビルド中..." -ForegroundColor Yellow

$args1 = @(
    "-m", "PyInstaller",
    "--onefile",
    "--windowed",
    "--name", "EazyConnecter",
    "--paths", "src",
    "--add-data", "VERSION.md;.",
    "--add-data", "frontend/dist;frontend_dist",
    "--icon", "img/icon.ico",
    "src/EazyConnecter.py"
)
python @args1
if ($LASTEXITCODE -ne 0) {
    Write-Host "[エラー] EazyConnecter.exe のビルドに失敗しました。" -ForegroundColor Red
    exit 1
}
Write-Host "  OK" -ForegroundColor Green

# [4/6] EazyConnecter_Setup.exe ビルド
Write-Host ""
Write-Host "[4/6] EazyConnecter_Setup.exe をビルド中..." -ForegroundColor Yellow

$args2 = @(
    "-m", "PyInstaller",
    "--onefile",
    "--windowed",
    "--name", "EazyConnecter_Setup",
    "--add-data", "VERSION.md;.",
    "--icon", "img/icon.ico",
    "src/setup.py"
)
python @args2
if ($LASTEXITCODE -ne 0) {
    Write-Host "[エラー] EazyConnecter_Setup.exe のビルドに失敗しました。" -ForegroundColor Red
    exit 1
}
Write-Host "  OK" -ForegroundColor Green

# [5/6] 後処理
Write-Host ""
Write-Host "[5/6] 後処理中..." -ForegroundColor Yellow
Copy-Item "config/servers.yaml" "dist\" -Force
if (Test-Path "build") { Remove-Item "build"                    -Recurse -Force }
if (Test-Path "EazyConnecter.spec") { Remove-Item "EazyConnecter.spec"       -Force }
if (Test-Path "EazyConnecter_Setup.spec") { Remove-Item "EazyConnecter_Setup.spec" -Force }
# config.yaml は配布不要のため dist\ へはコピーしない
if (Test-Path "dist\config.yaml") { Remove-Item "dist\config.yaml"         -Force }
Write-Host "  OK" -ForegroundColor Green

# [6/6] ZIP圧縮
Write-Host ""
Write-Host "[6/6] 配布用 ZIP を作成中..." -ForegroundColor Yellow

# VERSION.md からバージョン番号を取得
$version = "unknown"
if (Test-Path "VERSION.md") {
    $match = Select-String -Path "VERSION.md" -Pattern "^version:\s*([0-9]+\.[0-9]+\.[0-9]+)"
    if ($match) {
        $version = $match.Matches[0].Groups[1].Value
    }
}
Write-Host "  バージョン: $version" -ForegroundColor Gray

$zipName = "EazyConnecter_v${version}.zip"
$zipPath = Join-Path (Get-Location) $zipName
$root     = Get-Location

# 配布対象ファイル（config.yaml は除外。src=実ファイルの場所、dst=ZIP内でのファイル名）
$targets = @(
    @{ src = "dist\EazyConnecter.exe";       dst = "EazyConnecter.exe"       },
    @{ src = "dist\EazyConnecter_Setup.exe"; dst = "EazyConnecter_Setup.exe" },
    @{ src = "dist\servers.yaml";            dst = "servers.yaml"            },
    @{ src = "VERSION.md";                   dst = "VERSION.md"              }
)

# 既存ZIPを削除
if (Test-Path $zipPath) { Remove-Item $zipPath -Force }

# System.IO.Compression で ZIP 作成（PowerShell 5以降標準）
Add-Type -AssemblyName System.IO.Compression.FileSystem
$zip = [System.IO.Compression.ZipFile]::Open($zipPath, "Create")
foreach ($t in $targets) {
    $fpath = Join-Path $root $t.src
    if (Test-Path $fpath) {
        [System.IO.Compression.ZipFileExtensions]::CreateEntryFromFile(
            $zip, $fpath, $t.dst, "Optimal") | Out-Null
        Write-Host "  + $($t.dst)" -ForegroundColor Gray
    }
    else {
        Write-Host "  ! $($t.src) が見つかりません（スキップ）" -ForegroundColor Yellow
    }
}
$zip.Dispose()

Write-Host "  OK" -ForegroundColor Green
Write-Host ""
Write-Host "=== ビルド完了 ===" -ForegroundColor Green
Write-Host ""
Write-Host "  配布用 ZIP : $zipName" -ForegroundColor Cyan
Write-Host "  内容:"
foreach ($t in $targets) {
    if ($t.dst -eq "EazyConnecter_Setup.exe") {
        Write-Host "    $($t.dst)  ← 配布先で最初に実行" -ForegroundColor White
    }
    else {
        Write-Host "    $($t.dst)"
    }
}
Write-Host ""
Write-Host "  ※ config.yaml はウィザードが生成するため ZIP に含めていません。"
Write-Host ""
