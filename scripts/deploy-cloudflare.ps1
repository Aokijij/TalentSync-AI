[CmdletBinding(SupportsShouldProcess = $true, ConfirmImpact = 'High')]
param(
    [ValidatePattern('^[a-z0-9][a-z0-9-]*$')]
    [string]$ProjectName = 'talentsync-ai',
    [ValidatePattern('^https://[A-Za-z0-9.-]+(?::[0-9]+)?/api/v1/?$')]
    [string]$ApiUrl = 'https://talentsync-3c02d6e1.yellowwater-01e17d41.eastus2.azurecontainerapps.io/api/v1',
    [ValidatePattern('^https://[A-Za-z0-9.-]+/?$')]
    [string]$FrontendOrigin = 'https://talentsync-ai.pages.dev'
)

$ErrorActionPreference = 'Stop'
Set-StrictMode -Version Latest
$repositoryRoot = Split-Path -Parent $PSScriptRoot
$previousApiUrl = $env:VITE_API_URL
Push-Location $repositoryRoot
try {
    $revision = (& git rev-parse HEAD).Trim()
    if ($LASTEXITCODE -ne 0) { throw 'No fue posible identificar la versión Git.' }
    $dirty = & git status --porcelain
    if ($LASTEXITCODE -ne 0) { throw 'No fue posible revisar el estado Git.' }
    if ($dirty -and -not $WhatIfPreference) { throw 'Guarda los cambios en un commit antes de publicar.' }
    $FrontendOrigin = $FrontendOrigin.TrimEnd('/')
    Write-Host "Versión: $revision; API: $ApiUrl; frontend: $FrontendOrigin"
    if ($PSCmdlet.ShouldProcess($ProjectName, 'Compilar y publicar el frontend en Cloudflare Pages')) {
        # Check authentication/project access before building or uploading anything.
        & npx --yes wrangler@4.132.0 pages project list --json
        if ($LASTEXITCODE -ne 0) { throw 'Inicia sesión con npx wrangler@4.132.0 login y verifica el proyecto Pages.' }
        $preflight = Invoke-WebRequest "$ApiUrl/auth/login" -Method Options -Headers @{
            Origin = $FrontendOrigin
            'Access-Control-Request-Method' = 'POST'
            'Access-Control-Request-Headers' = 'content-type'
        } -TimeoutSec 30
        if ($preflight.Headers['Access-Control-Allow-Origin'] -ne $FrontendOrigin) {
            throw 'Azure debe permitir el origen del frontend en CORS antes de publicar.'
        }
        Set-Location (Join-Path $repositoryRoot 'frontend')
        $env:VITE_API_URL = $ApiUrl.TrimEnd('/')
        & npm run build
        if ($LASTEXITCODE -ne 0) { throw 'Falló la compilación. Cloudflare no se ha actualizado.' }
        & npx --yes wrangler@4.132.0 pages deploy dist --project-name $ProjectName --branch main --commit-hash $revision --commit-dirty=false
        if ($LASTEXITCODE -ne 0) { throw 'No se confirmó la publicación en Cloudflare.' }
        foreach ($path in @('/', '/login')) {
            $page = Invoke-WebRequest "$FrontendOrigin$path" -TimeoutSec 30
            if ($page.StatusCode -ne 200 -or $page.Content -notmatch 'id="root"') {
                throw "No se verificó la ruta pública $path en Cloudflare."
            }
        }
        Write-Host "Frontend publicado y rutas verificadas: $FrontendOrigin"
    }
} finally {
    $env:VITE_API_URL = $previousApiUrl
    Pop-Location
}
