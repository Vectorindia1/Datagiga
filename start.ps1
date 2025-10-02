$ErrorActionPreference = "Stop"

# Ensure relative paths resolve from the repo root (where this script lives)
Set-Location -Path (Split-Path -Parent $MyInvocation.MyCommand.Path)

function Get-Python311 {
  $candidates = @(
    "$env:LOCALAPPDATA\Programs\Python\Python311\python.exe",
    "C:\\Python311\\python.exe"
  )
  foreach ($c in $candidates) {
    if (Test-Path $c) { return @{Exe=$c; Args=@()} }
  }
  if (Get-Command py -ErrorAction SilentlyContinue) { return @{Exe="py"; Args=@("-3")} }
  if (Get-Command python -ErrorAction SilentlyContinue) { return @{Exe="python"; Args=@()} }
  return $null
}

# 1) Detect/install Python 3.11
$py = Get-Python311
if (-not $py) {
  Write-Host "Installing Python 3.11 via winget..."
  winget install -e --id Python.Python.3.11 --accept-source-agreements --accept-package-agreements | Out-Null
  $py = Get-Python311
  if (-not $py) { throw "Python 3.11 not found after installation." }
}

# 2) Create venv (idempotent)
Write-Host "Creating virtual environment at .\\.venv ..."
& $py.Exe @($py.Args + @("-m","venv",".\.venv"))

$venvPy  = ".\.venv\Scripts\python.exe"
$venvPip = ".\.venv\Scripts\pip.exe"
if (-not (Test-Path $venvPy)) { throw "Virtual environment python not found at $venvPy" }

# 3) Upgrade pip + install deps
Write-Host "Upgrading pip and installing backend requirements..."
& $venvPy -m pip install -U pip
& $venvPip install -r ".\gigasheet-local\backend\requirements.txt"

# 4) Start server in background with logs
Write-Host "Starting FastAPI backend (background) ..."
$logOut = ".\backend.log"
$logErr = ".\backend.err.log"
$pidFile = ".\server.pid"

# stop existing instance if present
if (Test-Path $pidFile) {
  try {
    $oldPid = Get-Content $pidFile | Select-Object -First 1
    if ($oldPid) { Stop-Process -Id [int]$oldPid -ErrorAction SilentlyContinue }
  } catch {}
  Remove-Item $pidFile -ErrorAction SilentlyContinue
}

$proc = Start-Process -FilePath $venvPy `
  -ArgumentList "gigasheet-local\backend\main.py" `
  -WorkingDirectory (Get-Location).Path `
  -RedirectStandardOutput $logOut `
  -RedirectStandardError $logErr `
  -PassThru `
  -WindowStyle Hidden

$proc.Id | Out-File -FilePath $pidFile -Encoding ascii

# 5) Verify server responds
Write-Host "Waiting for server on http://localhost:8000 ..."
$ok = $false
for ($i=0; $i -lt 30; $i++) {
  Start-Sleep -Seconds 1
  try {
    $resp = Invoke-RestMethod -Uri "http://localhost:8000/" -TimeoutSec 2
    if ($resp) { $ok = $true; break }
  } catch {}
}

if ($ok) {
  Write-Host "`nServer is up at http://localhost:8000 and http://localhost:8000/docs`n"
} else {
  Write-Warning "Server did not respond in time. Showing recent logs:"
  if (Test-Path $logErr) { Write-Host "`n=== backend.err.log (tail) ==="; Get-Content $logErr -Tail 100 }
  if (Test-Path $logOut) { Write-Host "`n=== backend.log (tail) ==="; Get-Content $logOut -Tail 100 }
}
