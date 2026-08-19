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

if (-not (Test-Path "icon.ico")) {
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

# [1/4] PyInstaller 確認
Write-Host ""
Write-Host "[1/4] PyInstaller を確認中..." -ForegroundColor Yellow
python -m PyInstaller --version 2>&1 | Out-Null
if ($LASTEXITCODE -ne 0) {
    Write-Host "  インストール中..." -ForegroundColor Yellow
    python -m pip install pyinstaller
    if ($LASTEXITCODE -ne 0) {
        Write-Host "[エラー] PyInstaller のインストールに失敗しました。" -ForegroundColor Red
        exit 1
    }
}
Write-Host "  OK" -ForegroundColor Green

# [2/4] EazyConnecter.exe ビルド
Write-Host ""
Write-Host "[2/4] EazyConnecter.exe をビルド中..." -ForegroundColor Yellow

$args1 = @(
    "-m", "PyInstaller",
    "--onefile",
    "--windowed",
    "--name", "EazyConnecter",
    "--add-data", "VERSION.md;.",
    "--icon", "img/icon.ico",
    "src/EazyConnecter.py"
)
python @args1
if ($LASTEXITCODE -ne 0) {
    Write-Host "[エラー] EazyConnecter.exe のビルドに失敗しました。" -ForegroundColor Red
    exit 1
}
Write-Host "  OK" -ForegroundColor Green

# [3/4] EazyConnecter_Setup.exe ビルド
Write-Host ""
Write-Host "[3/4] EazyConnecter_Setup.exe をビルド中..." -ForegroundColor Yellow

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

# [4/5] 後処理
Write-Host ""
Write-Host "[4/5] 後処理中..." -ForegroundColor Yellow
Copy-Item "config/servers.yaml" "dist\" -Force
if (Test-Path "build") { Remove-Item "build"                    -Recurse -Force }
if (Test-Path "EazyConnecter.spec") { Remove-Item "EazyConnecter.spec"       -Force }
if (Test-Path "EazyConnecter_Setup.spec") { Remove-Item "EazyConnecter_Setup.spec" -Force }
# config.yaml は配布不要のため dist\ へはコピーしない
if (Test-Path "dist\config.yaml") { Remove-Item "dist\config.yaml"         -Force }
Write-Host "  OK" -ForegroundColor Green

# # [5/5] ZIP圧縮
Write-Host ""
Write-Host "[5/5] 配布用 ZIP を作成中..." -ForegroundColor Yellow

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
$distPath = Join-Path (Get-Location) "dist"

# 配布対象ファイル（config.yaml は除外）
$targets = @(
    "EazyConnecter.exe",
    "EazyConnecter_Setup.exe",
    "config/servers.yaml",
    "VERSION.md"
)

# 既存ZIPを削除
if (Test-Path $zipPath) { Remove-Item $zipPath -Force }

# System.IO.Compression で ZIP 作成（PowerShell 5以降標準）
Add-Type -AssemblyName System.IO.Compression.FileSystem
$zip = [System.IO.Compression.ZipFile]::Open($zipPath, "Create")
foreach ($fname in $targets) {
    $fpath = Join-Path $distPath $fname
    if (Test-Path $fpath) {
        [System.IO.Compression.ZipFileExtensions]::CreateEntryFromFile(
            $zip, $fpath, $fname, "Optimal") | Out-Null
        Write-Host "  + $fname" -ForegroundColor Gray
    }
    else {
        Write-Host "  ! $fname が見つかりません（スキップ）" -ForegroundColor Yellow
    }
}
$zip.Dispose()

Write-Host "  OK" -ForegroundColor Green
Write-Host ""
Write-Host "=== ビルド完了 ===" -ForegroundColor Green
Write-Host ""
Write-Host "  配布用 ZIP : $zipName" -ForegroundColor Cyan
Write-Host "  内容:"
foreach ($fname in $targets) {
    if ($fname -eq "EazyConnecter_Setup.exe") {
        Write-Host "    $fname  ← 配布先で最初に実行" -ForegroundColor White
    }
    else {
        Write-Host "    $fname"
    }
}
Write-Host ""
Write-Host "  ※ config.yaml はウィザードが生成するため ZIP に含めていません。"
Write-Host ""
