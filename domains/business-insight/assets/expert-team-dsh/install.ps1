# 薄封装：找 Python 然后转调 install.py。业务逻辑只有一份，在 .py 里。
$ErrorActionPreference = "Stop"
[Console]::OutputEncoding = [System.Text.Encoding]::UTF8
$env:PYTHONUTF8 = "1"
Set-Location $PSScriptRoot
foreach ($py in @("python", "python3")) {
  if (Get-Command $py -ErrorAction SilentlyContinue) { & $py install.py @args; exit $LASTEXITCODE }
}
if (Get-Command py -ErrorAction SilentlyContinue) { & py -3 install.py @args; exit $LASTEXITCODE }
Write-Error "找不到 Python。装一个 Python 3.8+ 后重试。"
exit 1
