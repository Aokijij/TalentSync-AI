[CmdletBinding(SupportsShouldProcess = $true, ConfirmImpact = 'High')]
param(
    [string]$ResourceGroup = 'rg-talentsync-prod',
    [string]$ContainerApp = 'talentsync-3c02d6e1'
)

$ErrorActionPreference = 'Stop'
Set-StrictMode -Version Latest
$repositoryRoot = Split-Path -Parent $PSScriptRoot
$az = Get-Command az -ErrorAction SilentlyContinue
$azExecutable = if ($az) { $az.Source } else { Join-Path $repositoryRoot '.tmp/azure-cli-2.90.0/bin/az.cmd' }
if (-not (Test-Path -LiteralPath $azExecutable)) {
    throw 'Instala Azure CLI y ejecuta az login.'
}
if (-not $env:AZURE_CONFIG_DIR) {
    $env:AZURE_CONFIG_DIR = Join-Path $repositoryRoot '.azure'
}

$secureKey = Read-Host 'Pega la clave regional de Jooble Colombia' -AsSecureString
$plainKey = [System.Net.NetworkCredential]::new('', $secureKey).Password
if ([string]::IsNullOrWhiteSpace($plainKey)) {
    throw 'La clave de Jooble no puede estar vacía.'
}

try {
    if ($PSCmdlet.ShouldProcess(
        "$ResourceGroup/$ContainerApp",
        'Guardar la clave de Jooble como secreto y activar la integración'
    )) {
        & $azExecutable containerapp secret set `
            --name $ContainerApp `
            --resource-group $ResourceGroup `
            --secrets "jooble-api-key=$plainKey" `
            --only-show-errors `
            --output none
        if ($LASTEXITCODE -ne 0) { throw 'Azure no pudo guardar el secreto de Jooble.' }

        & $azExecutable containerapp update `
            --name $ContainerApp `
            --resource-group $ResourceGroup `
            --set-env-vars `
                'JOOBLE_API_KEY=secretref:jooble-api-key' `
                'JOOBLE_API_BASE_URL=https://co.jooble.org/api' `
                'JOOBLE_TIMEOUT_SECONDS=20' `
            --only-show-errors `
            --output none
        if ($LASTEXITCODE -ne 0) { throw 'Azure guardó el secreto, pero no pudo activar la variable.' }
        Write-Host 'Jooble quedó conectado en Azure. La clave no se guardó en el repositorio.'
    }
} finally {
    $plainKey = $null
    $secureKey.Dispose()
}
