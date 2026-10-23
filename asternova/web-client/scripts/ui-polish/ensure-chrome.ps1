# ensure-chrome.ps1 — 保证 headless Chromium CDP(9333) 存活；死了就拉起
# 2026-09-25 修订（R8）：沙箱收紧后 AppData 写被拒 → 必须 --disable-features=Crashpad；
# 网络沙箱 ACL grant 报错为非致命噪声，可忽略。Edge(Chromium 153) 为主，Chrome 备选。
param()
$ErrorActionPreference = "SilentlyContinue"
$browsers = @(
  "C:\Program Files (x86)\Microsoft\Edge\Application\msedge.exe",
  "C:\Program Files\Google\Chrome\Application\chrome.exe"
)
$profileDir = (Split-Path -Parent $PSScriptRoot) + "\edge-profile"
for ($i = 0; $i -lt 10; $i++) {
  try {
    $v = Invoke-RestMethod "http://127.0.0.1:9333/json/version" -TimeoutSec 3
    if ($v.Browser) { Write-Output "CDP_READY"; exit 0 }
  } catch {}
  foreach ($exe in $browsers) {
    if (-not (Test-Path $exe)) { continue }
    $flags = @("--headless=new","--no-sandbox","--disable-gpu","--disable-dev-shm-usage","--disable-features=Crashpad","--no-first-run","--window-size=1440,900","--remote-debugging-port=9333","--remote-allow-origins=*","--user-data-dir=$profileDir","about:blank")
    Start-Process -FilePath $exe -ArgumentList $flags -WindowStyle Hidden | Out-Null
    break
  }
  Start-Sleep -Seconds 6
}
Write-Output "CDP_FAILED"
exit 1
