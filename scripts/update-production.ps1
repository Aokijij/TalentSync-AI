[CmdletBinding(SupportsShouldProcess = $true, ConfirmImpact = 'High')]
param(
    [string]$ResourceGroup = 'rg-talentsync-prod',
    [string]$ContainerApp = 'talentsync-3c02d6e1',
    [string]$Registry = 'talentsync3c02d6e1',
    [ValidatePattern('^https://[A-Za-z0-9.-]+(?::[0-9]+)?/?$')]
    [string]$FrontendOrigin,
    [switch]$BackupVerified
)

$ErrorActionPreference = 'Stop'
Set-StrictMode -Version Latest
$repositoryRoot = Split-Path -Parent $PSScriptRoot
$az = Get-Command az -ErrorAction SilentlyContinue
$azExecutable = if ($az) { $az.Source } else { Join-Path $repositoryRoot '.tmp/azure-cli-2.90.0/bin/az.cmd' }
if (-not (Test-Path -LiteralPath $azExecutable)) { throw 'Instala Azure CLI y ejecuta az login.' }
if (-not $env:AZURE_CONFIG_DIR) { $env:AZURE_CONFIG_DIR = Join-Path $repositoryRoot '.azure' }

function Read-Az {
    param([Parameter(ValueFromRemainingArguments = $true)][string[]]$Arguments)
    $output = & $azExecutable @Arguments --only-show-errors --output json
    if ($LASTEXITCODE -ne 0) { throw "No fue posible consultar Azure: $($Arguments[0..1] -join ' ')" }
    return $output | ConvertFrom-Json
}

Push-Location $repositoryRoot
try {
    $revision = (& git rev-parse --short=12 HEAD).Trim()
    if ($LASTEXITCODE -ne 0) { throw 'No fue posible identificar la versión Git.' }
    $dirty = & git status --porcelain
    if ($LASTEXITCODE -ne 0) { throw 'No fue posible revisar el estado Git.' }
    if ($dirty -and -not $WhatIfPreference) { throw 'Guarda los cambios en un commit antes de desplegar. No se publica código sin versionar.' }
    $app = Read-Az containerapp show --name $ContainerApp --resource-group $ResourceGroup
    $registryInfo = Read-Az acr show --name $Registry --resource-group $ResourceGroup
    $previousImage = $app.properties.template.containers[0].image
    $previousRevision = $app.properties.latestReadyRevisionName
    $imageTag = "$revision-$(Get-Date -Format yyyyMMddHHmmss)"
    $image = "$($registryInfo.loginServer)/talentsync:$imageTag"
    $url = "https://$($app.properties.configuration.ingress.fqdn)"
    $corsArgument = $null
    if ($FrontendOrigin) {
        $FrontendOrigin = $FrontendOrigin.TrimEnd('/')
        $origins = @($url, $FrontendOrigin)
        $existingCors = $app.properties.template.containers[0].env | Where-Object { $_.name -eq 'CORS_ORIGINS' }
        if ($existingCors -and $existingCors.PSObject.Properties['value']) {
            $origins += @($existingCors.value | ConvertFrom-Json)
        }
        $corsJson = ConvertTo-Json -InputObject @($origins | Select-Object -Unique) -Compress
        # az.cmd uses legacy Windows argument passing: retain JSON quotation marks.
        if ($IsWindows -and $azExecutable.EndsWith('.cmd', [StringComparison]::OrdinalIgnoreCase)) {
            $corsJson = $corsJson.Replace('"', '\"')
        }
        $corsArgument = "CORS_ORIGINS=$corsJson"
        Write-Host "Frontend permitido: $FrontendOrigin"
    }

    Write-Host "Versión: $revision; anterior: $previousRevision"
    Write-Host "Imagen anterior para recuperación: $previousImage"
    Write-Host "Destino: $url"
    if (-not $BackupVerified -and -not $WhatIfPreference) { throw 'Verifica un punto de recuperación de PostgreSQL y el estado de los archivos subidos antes de usar -BackupVerified.' }
    if ($PSCmdlet.ShouldProcess("$ResourceGroup/$ContainerApp", 'Construir la imagen versionada y actualizar producción (incluye migraciones)')) {
        & $azExecutable acr build --registry $Registry --image "talentsync:$imageTag" --file Dockerfile --no-logs . --only-show-errors --output none
        if ($LASTEXITCODE -ne 0) { throw 'Falló la construcción. Producción no se ha modificado.' }
        $updateArguments = @('containerapp', 'update', '--name', $ContainerApp, '--resource-group', $ResourceGroup,
            '--image', $image, '--revision-suffix', "git-$revision-$(Get-Date -Format yyyyMMddHHmmss)",
            '--only-show-errors', '--output', 'none')
        if ($corsArgument) { $updateArguments += @('--set-env-vars', $corsArgument) }
        & $azExecutable @updateArguments
        if ($LASTEXITCODE -ne 0) { throw 'Falló la actualización. Revisa el estado de las revisiones antes de reintentar.' }
        for ($attempt = 1; $attempt -le 24; $attempt++) {
            $current = Read-Az containerapp show --name $ContainerApp --resource-group $ResourceGroup
            $ready = $current.properties.latestReadyRevisionName
            $latest = $current.properties.latestRevisionName
            if ($ready -eq $latest -and $ready -ne $previousRevision) {
                try {
                    $health = Invoke-RestMethod "$url/health" -TimeoutSec 15
                    if ($health.status -eq 'ok') { Write-Host "Actualización verificada: $ready"; return }
                } catch { Write-Verbose 'La nueva revisión aún no responde.' }
            }
            Start-Sleep -Seconds 5
        }
        throw 'No se confirmó la nueva revisión. No basta con que la revisión anterior responda /health. Revisa las migraciones y los registros en Azure.'
    }
} finally {
    Pop-Location
}
