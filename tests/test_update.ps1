<#
.SYNOPSIS
    Test script for update.ps1
#>

$ErrorActionPreference = "Stop"

# --- Test Setup ---
$TestTmpDir = [System.IO.Path]::GetTempPath() + [System.IO.Path]::GetRandomFileName()
New-Item -ItemType Directory -Force -Path $TestTmpDir | Out-Null
$UpdateScriptPath = Resolve-Path (Join-Path $PSScriptRoot ".." "update.ps1")

Write-Host "Running tests in $TestTmpDir"

# Cleanup
function Cleanup {
    if (Test-Path $TestTmpDir) {
        Remove-Item -Recurse -Force $TestTmpDir -ErrorAction SilentlyContinue
    }
}

try {
    # 1. Mock Environment
    $FakeHome = Join-Path $TestTmpDir "fake_home"
    $FakeProject = Join-Path $TestTmpDir "fake_project"
    $FakeBin = Join-Path $FakeHome "bin"
    New-Item -ItemType Directory -Force -Path $FakeBin | Out-Null
    New-Item -ItemType Directory -Force -Path $FakeProject | Out-Null

    # Add FakeBin to PATH
    $env:PATH = "$FakeBin$([System.IO.Path]::PathSeparator)$env:PATH"

    # Create Mock Scripts (Simulating environment)
    # git mock
    Set-Content -Path (Join-Path $FakeBin "git") -Value "#!/bin/bash`nif [[ `"`$1`" == `"rev-parse`" ]]; then echo `"$FakeProject`"; elif [[ `"`$1`" == `"clone`" ]]; then mkdir -p `"`$3/.git`"; echo `"Mock cloned`"; elif [[ `"`$1`" == `"pull`" ]]; then echo `"Mock pull successful`"; elif [[ `"`$1`" == `"ls-files`" ]]; then exit 0; elif [[ `"`$1`" == `"checkout`" ]]; then echo `"Mock checkout successful`"; else echo `"Mock git`"; fi"
    if ($IsLinux) { chmod +x (Join-Path $FakeBin "git") }

    # 2. Setup Fake Project
    $SettingsDir = Join-Path $FakeProject ".gemini"
    New-Item -ItemType Directory -Force -Path $SettingsDir | Out-Null
    $SettingsFile = Join-Path $SettingsDir "settings.json"
    Set-Content -Path $SettingsFile -Value '{"context": {"includeDirectories": []}}'
    
    # Create a dummy client library to update
    $PyDir = Join-Path $FakeProject "client_libs/google-ads-python"
    New-Item -ItemType Directory -Force -Path $PyDir | Out-Null
    New-Item -ItemType Directory -Force -Path (Join-Path $PyDir ".git") | Out-Null
    
    # Include in settings
    $SettingsJson = Get-Content -Raw $SettingsFile | ConvertFrom-Json
    $SettingsJson.context.includeDirectories += (Get-Item -LiteralPath $PyDir).FullName
    $SettingsJson | ConvertTo-Json -Depth 10 | Set-Content -LiteralPath $SettingsFile -Encoding UTF8

    # --- Test Case 1: Default update.ps1 ---
    Write-Host "--- Test Case 1: Default Update ---"
    & $UpdateScriptPath
    if ($LASTEXITCODE -ne 0) { throw "update.ps1 failed" }
    Write-Host "PASS: Default run successful"

    # --- Test Case 2: Run update.ps1 with valid ContextDir ---
    Write-Host "--- Test Case 2: Add valid context directory ---"
    $ValidDir = Join-Path $TestTmpDir "valid_dir"
    New-Item -ItemType Directory -Force -Path $ValidDir | Out-Null
    
    & $UpdateScriptPath -ContextDir $ValidDir
    if ($LASTEXITCODE -ne 0) { throw "update.ps1 failed with ContextDir" }

    $Settings = Get-Content -Raw $SettingsFile | ConvertFrom-Json
    $IncludedDirs = $Settings.context.includeDirectories
    $AbsValidDir = (Get-Item -LiteralPath $ValidDir).FullName
    if ($IncludedDirs -contains $AbsValidDir) { Write-Host "PASS: valid context_dir added" } else { throw "FAIL: missing valid context_dir" }

    # --- Test Case 3: Run update.ps1 with invalid ContextDir ---
    Write-Host "--- Test Case 3: Add invalid context directory ---"
    $InvalidDir = Join-Path $TestTmpDir "non_existent_dir"
    
    & $UpdateScriptPath -ContextDir $InvalidDir
    if ($LASTEXITCODE -ne 0) { throw "update.ps1 failed with invalid ContextDir" }

    # Verify it was NOT added
    $Settings = Get-Content -Raw $SettingsFile | ConvertFrom-Json
    if ($Settings.context.includeDirectories -contains $InvalidDir) { throw "FAIL: non_existent_dir added" } else { Write-Host "PASS: non_existent_dir not added" }

    # --- Test Case 4: Mixed list ---
    Write-Host "--- Test Case 4: Mixed list valid and invalid ---"
    $ValidDir2 = Join-Path $TestTmpDir "valid_dir2"
    New-Item -ItemType Directory -Force -Path $ValidDir2 | Out-Null
    $InvalidDir2 = Join-Path $TestTmpDir "non_existent_dir2"

    & $UpdateScriptPath -ContextDir "$ValidDir2,$InvalidDir2"
    if ($LASTEXITCODE -ne 0) { throw "update.ps1 failed with mixed list" }

    $Settings = Get-Content -Raw $SettingsFile | ConvertFrom-Json
    $IncludedDirs = $Settings.context.includeDirectories
    $AbsValidDir2 = (Get-Item -LiteralPath $ValidDir2).FullName
    if ($IncludedDirs -contains $AbsValidDir2) { Write-Host "PASS: valid_dir2 added" } else { throw "FAIL: missing valid_dir2" }
    if ($IncludedDirs -contains $InvalidDir2) { throw "FAIL: invalid_dir2 added" } else { Write-Host "PASS: invalid_dir2 missing" }

    Write-Host "ALL TESTS PASSED"

}
catch {
    Write-Error "Test Failed: $_"
    exit 1
}
finally {
    Cleanup
}
