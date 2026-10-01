param(
    [string]$BlenderPath,
    [string]$SourceRoot,
    [string]$OutputDirectory
)
$ErrorActionPreference = 'Stop'
if (-not $BlenderPath) {
    $command = Get-Command blender -ErrorAction SilentlyContinue
    if ($command) { $BlenderPath = $command.Source }
}
if (-not $BlenderPath -or -not (Test-Path -LiteralPath $BlenderPath)) {
    throw 'Pass -BlenderPath with the installed Blender executable.'
}
if (-not $OutputDirectory) {
    $OutputDirectory = Join-Path ([IO.Path]::GetTempPath()) ('asternova-characters-' + (Get-Date -Format 'yyyyMMdd-HHmmss'))
}
$OutputDirectory = [IO.Path]::GetFullPath($OutputDirectory)
$assembly = Join-Path $OutputDirectory 'assembly'
$rigged = Join-Path $OutputDirectory 'rigged'
New-Item -ItemType Directory -Force -Path $OutputDirectory | Out-Null
if (-not $SourceRoot) {
    $config = [IO.File]::ReadAllText((Join-Path $PSScriptRoot 'characters.json')) | ConvertFrom-Json
    $SourceRoot = $config.source_root
}
& $BlenderPath -b --factory-startup --python-exit-code 1 -P (Join-Path $PSScriptRoot 'inspect_assets.py') -- --source-root $SourceRoot --report (Join-Path $OutputDirectory 'source_manifest.json')
if ($LASTEXITCODE -ne 0) { throw 'Source asset inspection failed.' }
$arguments = @('-b', '--factory-startup', '--python-exit-code', '1', '-t', '8', '-P', (Join-Path $PSScriptRoot 'build_characters.py'), '--', '--output', $assembly)
if ($SourceRoot) { $arguments += @('--source-root', $SourceRoot) }
& $BlenderPath @arguments
if ($LASTEXITCODE -ne 0) { throw 'Character assembly failed.' }
foreach ($name in @('white', 'orange', 'purple')) {
    & $BlenderPath -b --factory-startup --python-exit-code 1 -t 8 -P (Join-Path $PSScriptRoot 'rig_characters.py') -- --assembly (Join-Path $assembly ($name + '_assembly.blend')) --output $rigged --character $name
    if ($LASTEXITCODE -ne 0) { throw ('Rigging failed: ' + $name) }
}
& $BlenderPath -b --factory-startup --python-exit-code 1 -P (Join-Path $PSScriptRoot 'validate_glb.py') -- $rigged --report (Join-Path $OutputDirectory 'glb_validation.json')
if ($LASTEXITCODE -ne 0) { throw 'Exported GLB validation failed.' }
& $BlenderPath -b --factory-startup --python-exit-code 1 -t 8 -P (Join-Path $PSScriptRoot 'inspect_deformation.py') -- --directory $rigged --report (Join-Path $OutputDirectory 'deformation_report.json')
if ($LASTEXITCODE -ne 0) { throw 'Deformation inspection failed.' }
Write-Host ('Generated Blender projects, GLBs and review renders: ' + $OutputDirectory)
Write-Host 'Review the renders before replacing approved game assets.'
