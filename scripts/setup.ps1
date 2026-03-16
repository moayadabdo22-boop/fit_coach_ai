param(
    [switch]$SkipFrontend,
    [switch]$SkipBackend
)

$ErrorActionPreference = "Stop"

function Ensure-EnvFile {
    param(
        [string]$TargetPath,
        [string]$ExamplePath
    )
    if (-not (Test-Path $TargetPath) -and (Test-Path $ExamplePath)) {
        Copy-Item $ExamplePath $TargetPath
    }
}

Write-Host "Setting up FitCoach AI..."

# Create env files if missing
Ensure-EnvFile ".env" ".env.example"
Ensure-EnvFile "ai_backend\.env" "ai_backend\.env.example"

if (-not $SkipBackend) {
    if (-not (Get-Command python -ErrorAction SilentlyContinue)) {
        Write-Host "Python is not installed or not on PATH."
        exit 1
    }

    if (-not (Test-Path "ai_backend\venv")) {
        python -m venv "ai_backend\venv"
    }

    & "ai_backend\venv\Scripts\python.exe" -m pip install --upgrade pip
    & "ai_backend\venv\Scripts\pip.exe" install -r "ai_backend\requirements.txt"
}

if (-not $SkipFrontend) {
    if (-not (Get-Command npm -ErrorAction SilentlyContinue)) {
        Write-Host "npm is not installed or not on PATH."
        exit 1
    }
    npm install
}

Write-Host "Done."
Write-Host "Run backend: .\\ai_backend\\venv\\Scripts\\python.exe -m uvicorn app:app --host 127.0.0.1 --port 8000"
Write-Host "Run frontend: npm run dev"
