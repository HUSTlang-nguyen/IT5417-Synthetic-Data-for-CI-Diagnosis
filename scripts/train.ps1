[CmdletBinding(DefaultParameterSetName='Model')]
param(
    [Parameter(Mandatory=$true, Position=0, ParameterSetName='Model')]
    [ValidateSet('M0','M1','M2','M5')][string]$Model,
    [Parameter(ParameterSetName='Model')][string]$Resume,
    [Parameter(ParameterSetName='Model')][switch]$Smoke,
    [Parameter(Mandatory=$true, ParameterSetName='Check')][switch]$Check,
    [ValidateSet(1024,2048)][int]$Context=2048
)
$ErrorActionPreference='Stop'
$projectRoot=Split-Path -Parent $PSScriptRoot
$pythonPath=Join-Path $projectRoot '.cache/ml-v1/Scripts/python.exe'
if (-not (Test-Path -LiteralPath $pythonPath)) { throw 'Isolated ML environment missing; see docs/training-runbook.md' }
$arguments=@('-m','ci_demo.sft','--manual','--context',"$Context")
if ($Check) { $arguments+='--check' } else { $arguments+=@('--model',$Model) }
if ($Resume) { $arguments+=@('--resume',$Resume) }
if ($Smoke) { $arguments+='--smoke' }
Push-Location -LiteralPath $projectRoot
try {
    & $pythonPath @arguments
    if ($LASTEXITCODE -ne 0) { throw "Learning command stopped (exit $LASTEXITCODE); inspect the printed run folder before resuming." }
} finally { Pop-Location }
