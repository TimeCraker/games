$ProjectRoot = "C:\Users\TimeCraker\Desktop\asternova-web-client"
$DocsDir = Join-Path -Path $ProjectRoot -ChildPath "docs"
$WikiDir = Join-Path -Path $ProjectRoot -ChildPath ".wiki.git"
# 假设前端项目也有一个 Wiki，如果没有可以把这行改成你实际的 Wiki 地址
$WikiRepoUrl = "https://github.com/TimeCraker/asternova-web-client.wiki.git"

if (-not (Test-Path -Path $DocsDir)) {
    New-Item -ItemType Directory -Path $DocsDir | Out-Null
    Write-Host "Success: Created output directory." -ForegroundColor Green
}

Write-Host "Starting frontend document generation task..." -ForegroundColor Cyan

# 1. Project Tree (过滤掉巨无霸文件夹 node_modules 和 .next)
$TreeOutputPath = Join-Path -Path $DocsDir -ChildPath "project_tree.txt"
Write-Host "-> [1/3] Generating Project Tree (Filtered)..."
Push-Location -Path $ProjectRoot
# 使用 findstr 剔除不需要的目录结构，保持树状图清爽
cmd /c "tree /f /a | findstr /V /I `"node_modules \.next \.git public`"" | Out-File -FilePath $TreeOutputPath -Encoding utf8
Pop-Location

# 2. Merge Code (前端定制版：只抓取 ts, tsx, js, jsx, css)
$CodeOutputPath = Join-Path -Path $DocsDir -ChildPath "all_code_merged.txt"
Write-Host "-> [2/3] Merging React/Next.js source files..."
Get-ChildItem -Path $ProjectRoot -Include *.ts,*.tsx,*.js,*.jsx,*.css -Recurse | 
    Where-Object { $_.FullName -notmatch "node_modules" -and $_.FullName -notmatch "\.next" -and $_.FullName -notmatch "public" } | 
    ForEach-Object {
        $content = Get-Content $_.FullName -Encoding UTF8
        "`n--- FILE: $($_.FullName) ---`n"
        $content
    } | Out-File -FilePath $CodeOutputPath -Encoding UTF8

# 3. Sync GitHub Wiki
Write-Host "-> [3/3] Syncing and Merging Wiki notes..."
if (-not (Test-Path -Path $WikiDir)) {
    Write-Host "   Wiki directory not found. Cloning from GitHub..." -ForegroundColor Yellow
    Push-Location -Path $ProjectRoot
    git clone $WikiRepoUrl ".wiki.git"
    Pop-Location
} else {
    Write-Host "   Wiki directory exists. Pulling latest changes..." -ForegroundColor Yellow
    Push-Location -Path $WikiDir
    git pull
    Pop-Location
}

# 4. Merge Wiki
$WikiOutputPath = Join-Path -Path $DocsDir -ChildPath "all_wiki_merged.txt"
if (Test-Path -Path $WikiDir) {
    Get-ChildItem -Path $WikiDir -Filter *.md -Recurse | 
        ForEach-Object {
            $header = "`n--- WIKI PAGE: $($_.Name) ---`n"
            Write-Output $header
            Get-Content $_.FullName -Encoding UTF8
        } | Out-File -FilePath $WikiOutputPath -Encoding UTF8
    Write-Host "   Wiki notes successfully merged." -ForegroundColor Green
} else {
    Write-Host "   Warning: Failed to process Wiki directory." -ForegroundColor Red
}

Write-Host "DONE! All frontend files saved to $DocsDir" -ForegroundColor Green