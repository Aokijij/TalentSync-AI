[CmdletBinding()]
param(
    [ValidateSet('Build', 'Preview')][string]$Mode = 'Build',
    [ValidatePattern('^[a-z0-9]+$')][string]$Location = 'eastus2',
    [string]$AzureCli = ''
)
$ErrorActionPreference = 'Stop'
$root = Split-Path -Parent $PSScriptRoot
$folder = Join-Path $root '.local/staging'
$template = Join-Path $folder 'foundation.arm.json'
$previousConfig = $env:AZURE_CONFIG_DIR
try {
    if (-not $AzureCli) {
        $portable = Join-Path $root '.tmp/azure-cli-2.90.0/bin/az.cmd'
        $AzureCli = if (Test-Path -LiteralPath $portable) { $portable } else { (Get-Command az -ErrorAction Stop).Source }
    }
    $env:AZURE_CONFIG_DIR = Join-Path $root '.azure'
    New-Item -ItemType Directory -Path $folder -Force | Out-Null
    & $AzureCli bicep build --file (Join-Path $root 'infra/staging/main.bicep') --outfile $template --only-show-errors
    if ($LASTEXITCODE -ne 0) { throw 'No se pudo compilar la plantilla de staging.' }
    $sources = @('main.bicep', 'foundation.bicep') | ForEach-Object {
        @{ file = $_; sha256 = (Get-FileHash -LiteralPath (Join-Path $root "infra/staging/$_") -Algorithm SHA256).Hash }
    }
    $report = @{ mode = $Mode; checkedAt = [DateTime]::UtcNow.ToString('o'); sources = $sources; compiled = $true; deployed = $false }
    if ($Mode -eq 'Preview') {
        # Deliberately fake secure parameter. This script has no deployment/create/build-image command.
        $preview = & $AzureCli deployment sub what-if --location $Location --template-file $template `
            --parameters 'postgresAdminPassword=EXAMPLE-WhatIf-Only-NotARealCredential-2026!' `
            --result-format ResourceIdOnly --no-pretty-print --output json --only-show-errors
        if ($LASTEXITCODE -ne 0) { throw 'Azure no pudo calcular la vista previa.' }
        $plan = ($preview -join "`n") | ConvertFrom-Json
        if ($plan.status -ne 'Succeeded' -or $plan.error -or $plan.potentialChanges -or $plan.diagnostics) {
            throw 'La vista previa contiene errores o cambios sin resolver; revisar antes de avanzar.'
        }
        if (-not $plan.changes -or @($plan.changes | Where-Object {
            $_.resourceId -notmatch '^/subscriptions/[^/]+/resourceGroups/rg-talentsync-staging(/|$)'
        }).Count) { throw 'La vista previa contiene recursos fuera del grupo de staging.' }
        $report.changes = @($plan.changes | ForEach-Object { @{ type = $_.changeType; resourceId = $_.resourceId } })
        $report.previewSucceeded = $true
        $report | ConvertTo-Json -Depth 8 | Set-Content -LiteralPath (Join-Path $folder 'azure-plan.json') -Encoding utf8
        $plan.changes | Group-Object changeType | ForEach-Object { Write-Host "$($_.Name): $($_.Count) recursos" }
    } else {
        $report | ConvertTo-Json -Depth 8 | Set-Content -LiteralPath (Join-Path $folder 'azure-build.json') -Encoding utf8
    }
    Write-Host 'Plantilla comprobada. No se crearon recursos ni se publicó una imagen.'
} finally {
    $env:AZURE_CONFIG_DIR = $previousConfig
}
