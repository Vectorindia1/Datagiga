$ErrorActionPreference = "Stop"

Set-Location -Path (Split-Path -Parent $MyInvocation.MyCommand.Path)

$pidFile = ".\server.pid"
if (Test-Path $pidFile) {
  try {
    $pid = Get-Content $pidFile | Select-Object -First 1
    if ($pid) {
      Write-Host "Stopping server PID $pid ..."
      Stop-Process -Id [int]$pid -ErrorAction SilentlyContinue
    }
  } catch {
    Write-Warning "Could not stop process from PID file. It may already be stopped."
  }
  Remove-Item $pidFile -ErrorAction SilentlyContinue
  Write-Host "Server stopped."
} else {
  Write-Host "No server.pid found. Nothing to stop."
}
