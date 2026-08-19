# EazyConnecter - exe ビルドスクリプト
# 実行: .\build_exe.ps1
# 出力:
#   dist\EazyConnecter.exe  ... メインツール
#   dist\EazyConnecter_Setup.exe ... セットアップウィザード
#   dist\servers.yaml               ... サーバーリスト
#   EazyConnecter_yyyyMMdd.zip      ... 配布用 ZIP（上記3ファイルをまとめたもの）

Set-Location (Split-Path -Parent $MyInvocation.MyCommand.Path)
Write-Host ""
Write-Host "=== EazyConnecter exe ビルド ===" -ForegroundColor Cyan

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
    "EazyConnecter.py"
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
    "setup.py"
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
Copy-Item "servers.yaml" "dist\" -Force
if (Test-Path "build") { Remove-Item "build"                    -Recurse -Force }
if (Test-Path "EazyConnecter.spec") { Remove-Item "EazyConnecter.spec"       -Force }
if (Test-Path "EazyConnecter_Setup.spec") { Remove-Item "EazyConnecter_Setup.spec" -Force }
# config.yaml は配布不要のため dist\ へはコピーしない
if (Test-Path "dist\config.yaml") { Remove-Item "dist\config.yaml"         -Force }
Write-Host "  OK" -ForegroundColor Green

# [5/5] ZIP圧縮
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
    "servers.yaml",
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
