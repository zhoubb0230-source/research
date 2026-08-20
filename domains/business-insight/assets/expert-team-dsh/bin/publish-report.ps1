<#
.SYNOPSIS
    唯一的报告发布通道 —— 防编造第三道闸（Windows）

.DESCRIPTION
    薄封装，逻辑在 publish_report.py 里（跨平台、已测试）。
    校验不过就不落盘，没有旁路。

.EXAMPLE
    .\publish-report.ps1 -Draft .\draft.md -Evidence .\batch\evidence.jsonl -PublishDir .\published
#>
[CmdletBinding()]
param(
    [Parameter(Mandatory = $true, Position = 0)] [string]$Draft,
    [Parameter(Mandatory = $true, Position = 1)] [string]$Evidence,
    [Parameter(Mandatory = $true, Position = 2)] [string]$PublishDir
)

$ErrorActionPreference = 'Stop'
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
if (-not $py) { Write-Error "找不到 Python 3。"; exit 2 }

$scriptDir = Split-Path -Parent $MyInvocation.MyCommand.Path
$target = Join-Path $scriptDir 'publish_report.py'

$argv = @()
$argv += $py.Prefix
$argv += $target
$argv += @($Draft, $Evidence, $PublishDir)

& $py.Exe @argv
exit $LASTEXITCODE
