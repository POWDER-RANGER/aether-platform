<#
.SYNOPSIS
  Workstation verification for Aether: checks tools, authentication, identity and paths on this machine.
  It says nothing about whether the repository's code works; that is repository verification (pytest, CI).

.EXAMPLE
  powershell -ExecutionPolicy Bypass -File scripts\workstation\Test-Workstation.ps1 `
    -GhExe "$env:USERPROFILE\Aether\tools\gh\2.103.2\bin\gh.exe" `
    -Python "$env:USERPROFILE\Aether\powder-ranger-bot\.venv\Scripts\python.exe"
#>
param(
  [Parameter(Mandatory)] [string] $GhExe,
  [Parameter(Mandatory)] [string] $Python,
  [string] $Repo,
  [string] $Remote = 'POWDER-RANGER/aether-platform'
)
if (-not $Repo) { $Repo = (Resolve-Path (Join-Path (Split-Path -Parent $MyInvocation.MyCommand.Path) '..\..')).Path }
$results = [System.Collections.Generic.List[object]]::new()
function Git-Out { $o = git -C $Repo @args 2>$null; if ($LASTEXITCODE -or -not $o) { throw "git $args failed in $Repo" }; "$o".Trim() }
function Check([string]$Name, [scriptblock]$Test) {
  try { $detail = & $Test; $ok = $true } catch { $detail = $_.Exception.Message; $ok = $false }
  $results.Add([pscustomobject]@{ Check = $Name; Status = $(if ($ok) { 'PASS' } else { 'FAIL' }); Detail = "$detail" })
}

Check 'gh executable'      { if (-not (Test-Path $GhExe)) { throw "not found: $GhExe" }; (& $GhExe --version | Select-Object -First 1) }
Check 'GH_CONFIG_DIR set'  { $d = [Environment]::GetEnvironmentVariable('GH_CONFIG_DIR', 'User'); if (-not $d -or -not (Test-Path $d)) { throw 'unset or missing' }; $d }
Check 'gh authenticated'   { $env:GH_CONFIG_DIR = [Environment]::GetEnvironmentVariable('GH_CONFIG_DIR', 'User'); & $GhExe auth status --hostname github.com 2>&1 | Out-Null; if ($LASTEXITCODE) { throw 'not logged in' }; 'github.com' }
Check 'git present'        { (git --version) }
Check 'repo remote'        { $u = Git-Out remote get-url origin; if ($u -notmatch [regex]::Escape($Remote)) { throw "origin is $u" }; $u }
Check 'repo identity'      { $e = Git-Out config user.email; if ($e -notmatch 'users\.noreply\.github\.com$') { throw "user.email is '$e' (use the GitHub noreply address)" }; $e }
Check 'python interpreter' { if (-not (Test-Path $Python)) { throw "not found: $Python" }; (& $Python --version) }
Check 'pytest importable'  { & $Python -c "import pytest; print(pytest.__version__)"; if ($LASTEXITCODE) { throw 'pytest missing' } }

$extended = [ordered]@{}

# Read-only inventory. Missing optional components are reported, never installed or changed.
$driverRows = @()
$drivers = @(Get-CimInstance Win32_SystemDriver -ErrorAction SilentlyContinue |
  Where-Object { $_.Name -match 'ViGEm|HidHide' })
foreach ($driver in $drivers) {
  $driverPath = [string]$driver.PathName
  $driverPath = $driverPath.Trim('"') -replace '^\\SystemRoot', $env:SystemRoot
  $driverVersion = $null
  if (Test-Path -LiteralPath $driverPath) {
    $driverVersion = (Get-Item -LiteralPath $driverPath).VersionInfo.FileVersion
  }
  $driverRows += [pscustomobject]@{
    Name = $driver.Name
    State = $driver.State
    StartMode = $driver.StartMode
    PathName = $driver.PathName
    FileVersion = $driverVersion
  }
}
$extended['controller_drivers'] = @{
  ViGEmBus = @($driverRows | Where-Object { $_.Name -match 'ViGEm' })
  HidHide = @($driverRows | Where-Object { $_.Name -match 'HidHide' })
  note = 'Inventory only; no driver installation, removal, or configuration changes.'
}

$nvidia = Get-Command nvidia-smi -ErrorAction SilentlyContinue
if ($nvidia) {
  $gpu = & $nvidia.Source --query-gpu=name,driver_version,memory.free,memory.total --format=csv,noheader 2>&1
  $extended['nvidia_smi'] = @{ status = $(if ($LASTEXITCODE -eq 0) { 'AVAILABLE' } else { 'QUERY_FAILED' }); output = @($gpu) }
} else {
  $extended['nvidia_smi'] = @{ status = 'NOT_FOUND' }
}

try {
  $tags = Invoke-RestMethod -Uri 'http://127.0.0.1:11434/api/tags' -TimeoutSec 3
  $extended['ollama'] = @{ status = 'REACHABLE'; models = @($tags.models | ForEach-Object { $_.name }) }
} catch {
  $extended['ollama'] = @{ status = 'UNREACHABLE'; detail = $_.Exception.Message }
}

$tesseract = Get-Command tesseract -ErrorAction SilentlyContinue
$extended['tesseract'] = if ($tesseract) {
  @{ status = 'AVAILABLE'; version = (& $tesseract.Source --version 2>&1 | Select-Object -First 1) }
} else { @{ status = 'NOT_FOUND' } }

$dxcam = & $Python -c "import importlib.util; print('AVAILABLE' if importlib.util.find_spec('dxcam') else 'NOT_FOUND')" 2>&1
$extended['dxcam'] = @{ status = "$dxcam".Trim() }

$driveRoot = [System.IO.Path]::GetPathRoot($Repo)
$drive = [System.IO.DriveInfo]::new($driveRoot)
$extended['repo_drive'] = @{
  root = $driveRoot
  total_bytes = $drive.TotalSize
  free_bytes = $drive.AvailableFreeSpace
}

$report = [ordered]@{
  timestamp_utc = [DateTime]::UtcNow.ToString('o')
  git_revision = (Git-Out rev-parse HEAD)
  repository = $Repo
  workstation = @{
    computer = $env:COMPUTERNAME
    os = (Get-CimInstance Win32_OperatingSystem | Select-Object -ExpandProperty Caption)
    gpu = $extended['nvidia_smi']
  }
  baseline_checks = @($results)
  extended_read_only_inventory = $extended
}
$stamp = [DateTime]::UtcNow.ToString('yyyyMMddTHHmmssZ')
$evidenceDir = Join-Path $Repo 'evidence\workstation'
New-Item -ItemType Directory -Path $evidenceDir -Force | Out-Null
$reportPath = Join-Path $evidenceDir "$stamp.json"
$report | ConvertTo-Json -Depth 8 | Set-Content -Path $reportPath -Encoding UTF8

$results | Format-Table -AutoSize | Out-String -Width 200 | Write-Output
Write-Output "Read-only workstation report: $reportPath"
if ($results.Status -contains 'FAIL') { exit 1 } else { exit 0 }
