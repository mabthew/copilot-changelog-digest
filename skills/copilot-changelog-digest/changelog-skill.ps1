# Copilot Changelog Skill - PowerShell Wrapper
# Analyzes Copilot changelog and ranks by workflow impact
# Usage: ./changelog-skill.ps1 -Days 7 -Repo . -Output markdown

param(
    [int]$Days = 7,
    [string]$Repo = ".",
    [ValidateSet("markdown", "interactive", "json")]
    [string]$Output = "markdown"
)

# Validate prerequisites
function Test-Prerequisites {
    Write-Host "Validating prerequisites..." -ForegroundColor Cyan

    # Check Python
    $pythonExists = $null -ne (Get-Command python3 -ErrorAction SilentlyContinue)
    if (-not $pythonExists) {
        $pythonExists = $null -ne (Get-Command python -ErrorAction SilentlyContinue)
    }

    if (-not $pythonExists) {
        Write-Host "ERROR: Python 3.9+ is required but not installed" -ForegroundColor Red
        Write-Host "Please install Python from https://www.python.org/downloads/" -ForegroundColor Yellow
        exit 1
    }

    Write-Host "✓ Python found" -ForegroundColor Green

    # Check repo exists
    if (-not (Test-Path $Repo -PathType Container)) {
        Write-Host "ERROR: Repository path does not exist: $Repo" -ForegroundColor Red
        exit 1
    }

    Write-Host "✓ Repository path exists: $Repo" -ForegroundColor Green
}

# Install Python dependencies
function Install-Dependencies {
    Write-Host "Installing Python dependencies..." -ForegroundColor Cyan

    $pythonCmd = "python3"
    if ($null -eq (Get-Command python3 -ErrorAction SilentlyContinue)) {
        $pythonCmd = "python"
    }

    $scriptDir = Split-Path -Parent $MyInvocation.MyCommand.Path
    $reqFile = Join-Path $scriptDir "requirements.txt"

    if (Test-Path $reqFile) {
        & $pythonCmd -m pip install -q -r $reqFile 2>$null
        if ($LASTEXITCODE -eq 0) {
            Write-Host "✓ Dependencies installed" -ForegroundColor Green
        }
        else {
            Write-Host "⚠ Failed to install some dependencies (continuing anyway)" -ForegroundColor Yellow
        }
    }
}

# Main execution
function Run-Skill {
    Write-Host "Copilot Changelog Skill" -ForegroundColor Cyan
    Write-Host "========================" -ForegroundColor Cyan
    Write-Host "Analyzing Copilot changelog for last $Days days" -ForegroundColor White
    Write-Host "Repository: $Repo" -ForegroundColor White
    Write-Host "Output format: $Output" -ForegroundColor White
    Write-Host ""

    # Get script directory
    $scriptDir = Split-Path -Parent $MyInvocation.MyCommand.Path
    $pythonScript = Join-Path $scriptDir "src" "main.py"

    $pythonCmd = "python3"
    if ($null -eq (Get-Command python3 -ErrorAction SilentlyContinue)) {
        $pythonCmd = "python"
    }

    # Convert repo path to absolute
    $repoAbsolute = (Resolve-Path $Repo).Path

    # Run Python backend
    Write-Host "Phase 1: Fetching Copilot changelog and analyzing repository..." -ForegroundColor Cyan

    $output = & $pythonCmd $pythonScript --days $Days --repo $repoAbsolute --output $Output 2>&1

    if ($LASTEXITCODE -eq 0) {
        Write-Host $output
        Write-Host ""
        Write-Host "✓ Analysis complete" -ForegroundColor Green
    }
    else {
        Write-Host "ERROR: Analysis failed" -ForegroundColor Red
        Write-Host $output
        exit 1
    }
}

# Main entry point
Test-Prerequisites
Install-Dependencies
Run-Skill
