param(
  [ValidateRange(1, 65535)]
  [int]$Port = 8000
)

Set-Location "$PSScriptRoot\..\backend"
if (-not (Test-Path ".env")) {
  Copy-Item ".env.example" ".env"
}
& .\.venv\Scripts\python.exe -m uvicorn app.main:app --reload --host 127.0.0.1 --port $Port
