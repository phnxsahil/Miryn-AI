$ErrorActionPreference = "Stop"

$redisDir = Join-Path $PSScriptRoot "redis"
$redisServer = Join-Path $redisDir "redis-server.exe"
$redisCli = Join-Path $redisDir "redis-cli.exe"

if (!(Test-Path $redisServer)) {
  throw "redis-server.exe not found at $redisServer"
}

Write-Host "Starting Redis on 127.0.0.1:6379..."
Start-Process -FilePath $redisServer -ArgumentList "--bind", "127.0.0.1", "--port", "6379" -WorkingDirectory $redisDir

Start-Sleep -Seconds 2

if (Test-Path $redisCli) {
  Write-Host "Checking Redis health..."
  $pingResult = & $redisCli -h 127.0.0.1 -p 6379 ping
  $pingExitCode = $LASTEXITCODE
  if ($pingExitCode -ne 0 -or $pingResult -ne "PONG") {
    Write-Error "Redis health check failed. ExitCode=$pingExitCode Output=$pingResult"
    exit 1
  }
  Write-Host "Redis is healthy: $pingResult"
} else {
  Write-Host "redis-cli.exe not found, skip ping check."
}
