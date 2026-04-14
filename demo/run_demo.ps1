# Windows PowerShell version of run_demo.sh
# Usage: .\demo\run_demo.ps1 [-Scenario cache_invalidation] [-Provider mock]

param(
  [string]$Scenario = "cache_invalidation",
  [string]$Provider = $env:CODELENS_PROVIDER
)

if (-not $Provider) { $Provider = "mock" }

$ErrorActionPreference = "Stop"
$ScriptDir = Split-Path -Parent $MyInvocation.MyCommand.Path
$ScenarioDir = Join-Path $ScriptDir "scenarios\$Scenario"

if (-not (Test-Path $ScenarioDir)) {
  Write-Error "Scenario not found: $ScenarioDir"
}

$WorkDir = New-Item -ItemType Directory -Path ([System.IO.Path]::GetTempPath()) -Name ("codelens-demo-" + [guid]::NewGuid())
try {
  Set-Location $WorkDir
  git init -q | Out-Null
  git symbolic-ref HEAD refs/heads/main | Out-Null
  git config user.email "demo@codelens.dev"
  git config user.name "CodeLens Demo"

  Copy-Item -Recurse -Force "$ScenarioDir\before\*" .
  git add -A | Out-Null
  git commit -q -m "baseline" | Out-Null

  git checkout -q -b feature | Out-Null
  Get-ChildItem -Force | Where-Object { $_.Name -ne ".git" } | Remove-Item -Recurse -Force
  Copy-Item -Recurse -Force "$ScenarioDir\after\*" .
  git add -A | Out-Null
  git commit -q -m "feature change" | Out-Null

  if ($Provider -eq "mock") {
    $env:CODELENS_MOCK_SCRIPT = "$ScenarioDir\mock_responses.json"
    @"
[provider]
name = "mock"
model = "mock"
"@ | Out-File -Encoding utf8 .codelens.toml
  }

  Write-Host "==> Running CodeLens on scenario: $Scenario (provider=$Provider)`n"
  codelens --base main --head feature --pr-body "$ScenarioDir\PR_BODY.md" --repo $WorkDir.FullName
}
finally {
  Set-Location $ScriptDir
  Remove-Item -Recurse -Force $WorkDir -ErrorAction SilentlyContinue
}
