[CmdletBinding()]
param([string]$IdentityFile = '', [switch]$Draft)
$ErrorActionPreference = 'Stop'
$repository = Split-Path -Parent $PSScriptRoot
if (-not $IdentityFile) { $IdentityFile = Join-Path $repository '.local/public-legal.json' }
$fields = @('NAME', 'EMAIL', 'CITY', 'COUNTRY', 'ADDRESS', 'PHONE', 'EFFECTIVE_DATE')
$original = @{}
foreach ($key in ($fields | ForEach-Object { "VITE_LEGAL_$_" }) + @('TALENTSYNC_PUBLIC_RELEASE')) { $original[$key] = [Environment]::GetEnvironmentVariable($key, 'Process') }
Push-Location (Join-Path $repository 'frontend')
try {
    if (Test-Path -LiteralPath $IdentityFile) {
        $identity = Get-Content -LiteralPath $IdentityFile -Raw -Encoding UTF8 | ConvertFrom-Json
        foreach ($field in $fields) {
            $value = [string]$identity.$field
            if (-not $Draft -and [string]::IsNullOrWhiteSpace($value)) { throw "Falta el dato público $field." }
            [Environment]::SetEnvironmentVariable("VITE_LEGAL_$field", $value, 'Process')
        }
    } elseif (-not $Draft) { throw 'Falta .local/public-legal.json con los datos autorizados para publicación.' }
    $env:TALENTSYNC_PUBLIC_RELEASE = if ($Draft) { '0' } else { '1' }
    & npm run build:public
    if ($LASTEXITCODE -ne 0) { throw 'No se pudo preparar el sitio público.' }
    & npx vite build --ssr src/public-prerender.jsx --outDir .public-render
    if ($LASTEXITCODE -ne 0) { throw 'No se pudo preparar el renderizado de las páginas.' }
    & node ../scripts/render-public-site.mjs
    if ($LASTEXITCODE -ne 0) { throw 'No se pudo generar el contenido HTML público.' }
    Write-Host 'Sitio informativo preparado en frontend/public-dist. No se ha publicado ni conectado la aplicación.'
} finally {
    foreach ($key in $original.Keys) { [Environment]::SetEnvironmentVariable($key, $original[$key], 'Process') }
    Pop-Location
}
