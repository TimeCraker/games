param([string]$GodotPath, [switch]$Static)
$ErrorActionPreference = 'Stop'
$purpleScene = if ($Static) {
    'res://scenes/character_lab/purple_static_review.tscn'
} else {
    'res://scenes/character_lab/purple_rig_review.tscn'
}
& (Join-Path $PSScriptRoot 'start_character_lab.ps1') -GodotPath $GodotPath -Scene $purpleScene
