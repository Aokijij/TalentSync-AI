[CmdletBinding()]
param()
$ErrorActionPreference = 'Stop'
$repository = Split-Path -Parent $PSScriptRoot
$identityFile = Join-Path $repository '.local/public-legal.json'
if (-not (Test-Path -LiteralPath $identityFile)) { throw 'Faltan los datos legales autorizados de producción.' }
$identity = Get-Content -LiteralPath $identityFile -Raw -Encoding UTF8 | ConvertFrom-Json
foreach ($field in @('NAME', 'EMAIL', 'CITY', 'COUNTRY', 'ADDRESS', 'PHONE', 'EFFECTIVE_DATE')) {
    if ([string]::IsNullOrWhiteSpace([string]$identity.$field)) { throw "Falta el dato público $field." }
}
$previousApi = $env:VITE_API_URL
Push-Location (Join-Path $repository 'frontend')
try {
    $env:VITE_API_URL = '/api/v1'
    & npx vite build --manifest
    if ($LASTEXITCODE -ne 0) { throw 'Falló la compilación de producción.' }
    & npx vite build --ssr src/public-prerender.jsx --outDir .public-render
    if ($LASTEXITCODE -ne 0) { throw 'Falló el renderizado público.' }
    & node ../scripts/render-public-site.mjs --full-app
    if ($LASTEXITCODE -ne 0) { throw 'Falló el HTML público y legal.' }
    Copy-Item -LiteralPath ../infra/production/cloudflare-worker.mjs -Destination dist/_worker.js
    Set-Content -LiteralPath dist/_redirects -Value '/* /index.html 200' -Encoding ascii
    $unsafe = Get-ChildItem -LiteralPath dist -Recurse -File -Filter '*.js' |
        Select-String -Pattern 'https?://(?:127\.0\.0\.1|localhost):8000|azurecontainerapps\.io|GOCSPX-' -List |
        Select-Object -First 1
    if ($unsafe) { throw 'El artefacto contiene un origen retirado o una credencial. No publicar.' }
    Write-Host 'Aplicación preparada en frontend/dist con proxy y páginas legales legibles sin JavaScript.'
} finally {
    $env:VITE_API_URL = $previousApi
    Pop-Location
}
