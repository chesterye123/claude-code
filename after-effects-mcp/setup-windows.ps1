# One-shot Windows setup: build the server, install the After Effects panel,
# and register the server with Claude Code and/or Claude Desktop.
# Run via setup-windows.cmd (double-click), or:
#   powershell -NoProfile -ExecutionPolicy Bypass -File setup-windows.ps1

$Dir = $PSScriptRoot
Set-Location -LiteralPath $Dir
$Name = 'AfterEffectsMCP'

function Fail($msg) {
  Write-Host $msg -ForegroundColor Red
  exit 1
}

function Quote($s) { "'" + ($s -replace "'", "''") + "'" }

$node = Get-Command node -CommandType Application -ErrorAction SilentlyContinue | Select-Object -First 1
if (-not $node) {
  Fail 'Node.js is not installed. Install the LTS version from https://nodejs.org, then run this again.'
}
# Absolute path: Claude Desktop doesn't inherit your terminal's PATH.
$NodeBin = $node.Path
$major = [int](& $NodeBin -p 'parseInt(process.versions.node)')
if ($major -lt 18) {
  Fail "Node.js 18 or newer is required (found $(& $NodeBin --version))."
}
$Server = Join-Path $Dir 'build\index.js'

Write-Host '==> Installing dependencies and building'
Remove-Item -Recurse -Force -ErrorAction SilentlyContinue (Join-Path $Dir 'node_modules'), (Join-Path $Dir 'build')
& npm.cmd ci --no-audit --no-fund
if ($LASTEXITCODE -ne 0 -or -not (Test-Path -LiteralPath $Server)) {
  Fail 'npm ci / build failed. Scroll up for the error.'
}

Write-Host '==> Installing the bridge panel into After Effects (Windows may ask for admin permission)'
$src = Join-Path $Dir 'build\scripts\mcp-bridge-auto.jsx'
$srcHash = (Get-FileHash -LiteralPath $src).Hash
$aeDirs = @(Get-ChildItem -LiteralPath (Join-Path $env:ProgramFiles 'Adobe') -Directory -ErrorAction SilentlyContinue |
  Where-Object { $_.Name -like 'Adobe After Effects*' -and (Test-Path -LiteralPath (Join-Path $_.FullName 'Support Files')) })
$installed = @()
foreach ($ae in $aeDirs) {
  $panels = Join-Path $ae.FullName 'Support Files\Scripts\ScriptUI Panels'
  $dst = Join-Path $panels 'mcp-bridge-auto.jsx'
  try {
    New-Item -ItemType Directory -Force -Path $panels -ErrorAction Stop | Out-Null
    Copy-Item -LiteralPath $src -Destination $dst -Force -ErrorAction Stop
  } catch {
    # Program Files needs admin rights: copy from an elevated PowerShell (UAC prompt).
    $cmd = "New-Item -ItemType Directory -Force -Path $(Quote $panels) | Out-Null; Copy-Item -LiteralPath $(Quote $src) -Destination $(Quote $dst) -Force"
    $encoded = [Convert]::ToBase64String([Text.Encoding]::Unicode.GetBytes($cmd))
    try {
      Start-Process powershell -Verb RunAs -Wait -WindowStyle Hidden -ArgumentList '-NoProfile', '-EncodedCommand', $encoded
    } catch {
      Write-Host "    Admin permission was declined for $($ae.Name)." -ForegroundColor Yellow
    }
  }
  if ((Test-Path -LiteralPath $dst) -and (Get-FileHash -LiteralPath $dst).Hash -eq $srcHash) {
    $installed += $ae.Name
    Write-Host "    Installed into $($ae.Name)"
  }
}
if ($installed.Count -eq 0) {
  Write-Host '!!  Panel not installed automatically. Copy this file by hand:' -ForegroundColor Yellow
  Write-Host "      $src"
  Write-Host '    into: C:\Program Files\Adobe\Adobe After Effects <version>\Support Files\Scripts\ScriptUI Panels\'
}

$registered = $false

if (Get-Command claude -ErrorAction SilentlyContinue) {
  Write-Host '==> Registering with Claude Code (user scope)'
  & claude mcp remove -s user $Name 2>$null | Out-Null
  & claude mcp add -s user $Name $NodeBin $Server
  $registered = $true
}

# Standard installer uses %APPDATA%\Claude; the Microsoft Store build keeps it under Packages.
# Create the standard folder up front: it doesn't exist until Claude Desktop has been opened once.
$desktopDirs = @(Join-Path $env:APPDATA 'Claude')
New-Item -ItemType Directory -Force -Path $desktopDirs[0] | Out-Null
# The Store package name varies, so match any package that has a Claude settings folder.
$desktopDirs += @(Get-Item -Path "$env:LOCALAPPDATA/Packages/*/LocalCache/Roaming/Claude" -ErrorAction SilentlyContinue |
  Where-Object { $_.PSIsContainer } | ForEach-Object { $_.FullName })
$merge = @'
const fs = require('fs');
const { AE_MCP_CONFIG, AE_MCP_NAME, AE_MCP_NODE, AE_MCP_SERVER } = process.env;
const raw = fs.existsSync(AE_MCP_CONFIG) ? fs.readFileSync(AE_MCP_CONFIG, 'utf8').replace(/^\uFEFF/, '').trim() : '';
const cfg = raw ? JSON.parse(raw) : {};
cfg.mcpServers = { ...cfg.mcpServers, [AE_MCP_NAME]: { command: AE_MCP_NODE, args: [AE_MCP_SERVER] } };
fs.writeFileSync(AE_MCP_CONFIG, JSON.stringify(cfg, null, 2) + '\n');
'@
$mergeFile = Join-Path ([IO.Path]::GetTempPath()) 'ae-mcp-merge-config.cjs'
Set-Content -LiteralPath $mergeFile -Value $merge -Encoding ASCII
foreach ($desktopDir in $desktopDirs) {
  if (-not (Test-Path -LiteralPath $desktopDir)) { continue }
  Write-Host "==> Registering with Claude Desktop ($desktopDir)"
  $config = Join-Path $desktopDir 'claude_desktop_config.json'
  if (Test-Path -LiteralPath $config) {
    $backup = "$config.bak.$(Get-Date -Format yyyyMMddHHmmss)"
    Copy-Item -LiteralPath $config -Destination $backup
    Write-Host "    Backed up existing config to: $backup"
  }
  $env:AE_MCP_CONFIG = $config
  $env:AE_MCP_NAME = $Name
  $env:AE_MCP_NODE = $NodeBin
  $env:AE_MCP_SERVER = $Server
  & $NodeBin $mergeFile
  if ($LASTEXITCODE -ne 0) {
    Write-Host "    Could not update $config (is it valid JSON?). Your backup is untouched." -ForegroundColor Yellow
    continue
  }
  Write-Host '    Fully quit Claude Desktop (system tray > Quit) and reopen it to load it.'
  $registered = $true
}
Remove-Item -LiteralPath $mergeFile -ErrorAction SilentlyContinue

if (-not $registered) {
  Write-Host '!!  Could not register with Claude Desktop or Claude Code. Scroll up for the error.' -ForegroundColor Yellow
}

Write-Host ''
Write-Host 'Done. Last steps, in After Effects:'
Write-Host '  1. Edit > Preferences > Scripting & Expressions >'
Write-Host '     tick "Allow Scripts to Write Files and Access Network"'
Write-Host '  2. Restart After Effects'
Write-Host '  3. Window > mcp-bridge-auto.jsx  (keep this panel open with "Auto-run commands" ticked)'
