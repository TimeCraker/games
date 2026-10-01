param([string]$GodotPath)
$ErrorActionPreference = 'Stop'
if (-not $GodotPath) {
    $godotCommand = Get-Command godot -ErrorAction SilentlyContinue
    if ($godotCommand) { $GodotPath = $godotCommand.Source }
}
if (-not $GodotPath) {
    $godotDirectory = Join-Path $env:USERPROFILE 'tools\godot'
    $candidate = Get-ChildItem -LiteralPath $godotDirectory -Filter 'Godot*win64.exe' -ErrorAction SilentlyContinue |
        Where-Object Name -NotMatch 'console' | Sort-Object Name -Descending | Select-Object -First 1
    if ($candidate) { $GodotPath = $candidate.FullName }
}
if (-not $GodotPath -or -not (Test-Path -LiteralPath $GodotPath)) {
    throw 'Godot executable not found. Pass -GodotPath with the installed executable.'
}
& $GodotPath --headless --path $PSScriptRoot --editor --import
if ($LASTEXITCODE -ne 0) { throw 'Godot asset import failed.' }
& $GodotPath --path $PSScriptRoot 'res://scenes/character_lab/character_lab.tscn'
exit $LASTEXITCODE
