<#
.SYNOPSIS
    业务洞察专家团 · DeepSeek Harness 安装（Windows）

.DESCRIPTION
    本脚本只做一件事：找到可用的 Python，然后调用 install.py。
    生成逻辑全部在 install.py 里（跨平台、已测试），本封装不含业务逻辑——
    这样 Windows 与 Linux 跑的是同一份代码，不会出现两边行为不一致。

.PARAMETER Target
    项目目录。dsh 以最近的含 .git 的祖先目录为项目根。

.PARAMETER Write
    真正写入；不加则只预演。

.EXAMPLE
    .\install.ps1 -Target D:\work\insight-trial
    .\install.ps1 -Target D:\work\insight-trial -Write
#>
[CmdletBinding()]
param(
    [Parameter(Mandatory = $true, Position = 0)]
    [string]$Target,

    [switch]$Write
)

$ErrorActionPreference = 'Stop'

# Windows 控制台编码：确保中文与 ✓/✗ 不乱码
try { [Console]::OutputEncoding = [System.Text.Encoding]::UTF8 } catch { }
$env:PYTHONUTF8 = '1'
$env:PYTHONIOENCODING = 'utf-8'

function Find-Python {
    foreach ($candidate in @('python', 'python3', 'py')) {
        $cmd = Get-Command $candidate -ErrorAction SilentlyContinue
        if (-not $cmd) { continue }
        try {
            $args = if ($candidate -eq 'py') { @('-3', '--version') } else { @('--version') }
            $out = & $candidate @args 2>&1
            if ($LASTEXITCODE -eq 0 -and $out -match 'Python 3\.') {
                return @{ Exe = $candidate; Prefix = $(if ($candidate -eq 'py') { @('-3') } else { @() }) }
            }
        } catch { }
    }
    return $null
}

$py = Find-Python
if (-not $py) {
    Write-Error "找不到 Python 3。请先安装（https://www.python.org/downloads/windows/），或把它加进 PATH。"
    exit 2
}

$scriptDir = Split-Path -Parent $MyInvocation.MyCommand.Path
$installPy = Join-Path $scriptDir 'install.py'
if (-not (Test-Path -LiteralPath $installPy)) {
    Write-Error "找不到 $installPy"
    exit 2
}

$argv = @()
$argv += $py.Prefix
$argv += $installPy
$argv += $Target
if ($Write) { $argv += '--write' }

& $py.Exe @argv
exit $LASTEXITCODE
