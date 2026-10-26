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

$results | Format-Table -AutoSize | Out-String -Width 200 | Write-Output
if ($results.Status -contains 'FAIL') { exit 1 } else { exit 0 }
