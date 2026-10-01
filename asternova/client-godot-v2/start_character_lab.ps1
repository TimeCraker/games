param([string]$GodotPath, [string]$Scene = 'res://scenes/character_lab/character_lab.tscn')
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
# Windows PowerShell can launch a GUI executable asynchronously; LASTEXITCODE
# is then unset. Wait on the actual process, including for headless imports.
$quotedProject = '"' + $PSScriptRoot + '"'
$importProcess = Start-Process -FilePath $GodotPath -ArgumentList @('--headless', '--path', $quotedProject, '--editor', '--import') -WindowStyle Hidden -Wait -PassThru
if ($importProcess.ExitCode -ne 0) { throw 'Godot asset import failed.' }
$gameProcess = Start-Process -FilePath $GodotPath -ArgumentList @('--path', $quotedProject, '--resolution', '1440x900', $Scene) -WindowStyle Normal -Wait -PassThru
exit $gameProcess.ExitCode
