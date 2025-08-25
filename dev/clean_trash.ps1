#!/usr/bin/env pwsh

# PowerShell cleanup script with nice formatting
# Equivalent to clean_trash.sh but with enhanced logging

function Write-Header {
    param([string]$Title)
    Write-Host ""
    Write-Host "============================================" -ForegroundColor Cyan
    Write-Host "  $Title" -ForegroundColor White
    Write-Host "============================================" -ForegroundColor Cyan
}

function Write-Step {
    param([string]$Message)
    Write-Host "-> $Message" -ForegroundColor Yellow
}

function Write-Success {
    param([string]$Message)
    Write-Host "[OK] $Message" -ForegroundColor Green
}

function Write-Warning {
    param([string]$Message)
    Write-Host "[WARN] $Message" -ForegroundColor Magenta
}

function Write-Error {
    param([string]$Message)
    Write-Host "[ERROR] $Message" -ForegroundColor Red
}

# Start cleanup
Write-Header "MAPS4FS API CLEANUP SCRIPT"
Write-Host "Starting cleanup process..." -ForegroundColor White

# Directories to be removed
$dirs = @(".mypy_cache", ".pytest_cache", "htmlcov", "dist", "archives", "cache", "logs", "maps", "temp", "osmps", "map_directory", "tests/data", "mfsrootdir")

# Files to be removed
$files = @(".coverage", "queue.json")

# Remove directories
Write-Header "REMOVING DIRECTORIES"
foreach ($dir in $dirs) {
    if (Test-Path $dir) {
        Write-Step "Removing directory: $dir"
        try {
            Remove-Item -Path $dir -Recurse -Force -ErrorAction Stop
            Write-Success "Successfully removed: $dir"
        }
        catch {
            Write-Error "Failed to remove directory: $dir - $($_.Exception.Message)"
        }
    }
    else {
        Write-Warning "Directory not found: $dir"
    }
}

# Remove files
Write-Header "REMOVING FILES"
foreach ($file in $files) {
    if (Test-Path $file) {
        Write-Step "Removing file: $file"
        try {
            Remove-Item -Path $file -Force -ErrorAction Stop
            Write-Success "Successfully removed: $file"
        }
        catch {
            Write-Error "Failed to remove file: $file - $($_.Exception.Message)"
        }
    }
    else {
        Write-Warning "File not found: $file"
    }
}

# Remove __pycache__ directories
Write-Header "REMOVING __pycache__ DIRECTORIES"
Write-Step "Searching for __pycache__ directories (excluding .venv)..."

$pycacheDirs = Get-ChildItem -Path . -Name "__pycache__" -Recurse -Directory -Force -ErrorAction SilentlyContinue | Where-Object { $_ -notlike ".venv*" -and $_ -notlike "*\.venv\*" }
$pycacheCount = $pycacheDirs.Count

if ($pycacheCount -gt 0) {
    Write-Step "Found $pycacheCount __pycache__ directories"
    foreach ($pycacheDir in $pycacheDirs) {
        try {
            Remove-Item -Path $pycacheDir -Recurse -Force -ErrorAction Stop
            Write-Success "Removed: $pycacheDir"
        }
        catch {
            Write-Error "Failed to remove: $pycacheDir - $($_.Exception.Message)"
        }
    }
}
else {
    Write-Warning "No __pycache__ directories found"
}

# Final summary
Write-Header "CLEANUP COMPLETED"
Write-Host "*** All cleanup operations finished! ***" -ForegroundColor Green
Write-Host ""
