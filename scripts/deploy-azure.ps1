[CmdletBinding()]
param(
    [string]$ResourceGroup = "rg-talentsync-prod",
    [string]$Location = "eastus2",
    [string]$PostgresAdmin = "talentsyncadmin",
    [string]$PostgresPassword,
    [string]$SecretKey,
    [switch]$ScaleToZero
)

$ErrorActionPreference = "Stop"
Set-StrictMode -Version Latest
$env:PYTHONUTF8 = "1"
$env:PYTHONIOENCODING = "utf-8"

$repositoryRoot = Split-Path -Parent $PSScriptRoot
$azCommand = Get-Command az -ErrorAction SilentlyContinue
if ($azCommand) {
    $azExecutable = $azCommand.Source
} else {
    $portableAz = Get-ChildItem -Path (Join-Path $repositoryRoot ".tmp\azure-cli-*\bin\az.cmd") -ErrorAction SilentlyContinue |
        Sort-Object FullName -Descending |
        Select-Object -First 1
    $azExecutable = if ($portableAz) { $portableAz.FullName } else { $null }
}

if (-not $azExecutable) {
    throw "Azure CLI no esta instalado. Instala Azure CLI y ejecuta primero: az login"
}

if (-not $env:AZURE_CONFIG_DIR) {
    $env:AZURE_CONFIG_DIR = Join-Path $repositoryRoot ".azure"
}
New-Item -ItemType Directory -Force -Path $env:AZURE_CONFIG_DIR | Out-Null

function Invoke-AzJson {
    param([Parameter(ValueFromRemainingArguments = $true)][string[]]$Arguments)
    $output = & $azExecutable @Arguments --only-show-errors --output json
    if ($LASTEXITCODE -ne 0) {
        throw "Azure CLI fallo al ejecutar: az $($Arguments[0..1] -join ' ')"
    }
    if ($output) { return $output | ConvertFrom-Json }
}

function Get-AzJson {
    param([Parameter(ValueFromRemainingArguments = $true)][string[]]$Arguments)
    $output = & $azExecutable @Arguments --only-show-errors --output json 2>$null
    if ($LASTEXITCODE -ne 0 -or -not $output) { return $null }
    return $output | ConvertFrom-Json
}

function Invoke-Az {
    param([Parameter(ValueFromRemainingArguments = $true)][string[]]$Arguments)
    & $azExecutable @Arguments --only-show-errors --output none
    if ($LASTEXITCODE -ne 0) {
        throw "Azure CLI fallo al ejecutar: az $($Arguments[0..1] -join ' ')"
    }
}

$account = Get-AzJson account show
if (-not $account) {
    throw "No hay una suscripcion de Azure activa. Ejecuta az login con una cuenta que tenga suscripcion."
}
if (-not $account.id) {
    throw "No hay una suscripcion de Azure activa. Ejecuta az login con una cuenta que tenga suscripcion."
}

$hash = [Security.Cryptography.SHA256]::HashData(
    [Text.Encoding]::UTF8.GetBytes("$($account.id):$ResourceGroup")
)
$suffix = [Convert]::ToHexString($hash).Substring(0, 8).ToLowerInvariant()
$registryName = "talentsync$suffix"
$storageName = "ts${suffix}storage"
$postgresName = "talentsync-pg-$suffix"
$environmentName = "talentsync-env-$suffix"
$appName = "talentsync-$suffix"
$databaseName = "talentsync"
$containerName = "cvs"
$imageTag = Get-Date -Format "yyyyMMddHHmmss"

Invoke-Az group create --name $ResourceGroup --location $Location
Invoke-Az extension add --name containerapp --upgrade
foreach ($provider in @("Microsoft.App", "Microsoft.OperationalInsights", "Microsoft.ContainerRegistry", "Microsoft.DBforPostgreSQL", "Microsoft.Storage")) {
    Invoke-Az provider register --namespace $provider --wait
}

$registry = Get-AzJson acr show --name $registryName --resource-group $ResourceGroup
if (-not $registry) {
    $registry = Invoke-AzJson acr create --name $registryName --resource-group $ResourceGroup --location $Location --sku Basic --admin-enabled true
}

$storage = Get-AzJson storage account show --name $storageName --resource-group $ResourceGroup
if (-not $storage) {
    $storage = Invoke-AzJson storage account create --name $storageName --resource-group $ResourceGroup --location $Location --sku Standard_LRS --kind StorageV2 --min-tls-version TLS1_2 --allow-blob-public-access false
}
Invoke-Az storage container create --name $containerName --account-name $storageName --auth-mode key

$postgres = Get-AzJson postgres flexible-server show --name $postgresName --resource-group $ResourceGroup
$existingApp = Get-AzJson containerapp show --name $appName --resource-group $ResourceGroup
if (-not $postgres) {
    if (-not $PostgresPassword) {
        $PostgresPassword = [Convert]::ToHexString(
            [Security.Cryptography.RandomNumberGenerator]::GetBytes(32)
        ).ToLowerInvariant()
    }
    $postgres = Invoke-AzJson postgres flexible-server create --name $postgresName --resource-group $ResourceGroup --location $Location --admin-user $PostgresAdmin --admin-password $PostgresPassword --sku-name Standard_B1ms --tier Burstable --version 16 --storage-size 32 --public-access 0.0.0.0 --yes
} elseif (-not $existingApp) {
    if (-not $PostgresPassword) {
        $PostgresPassword = [Convert]::ToHexString(
            [Security.Cryptography.RandomNumberGenerator]::GetBytes(32)
        ).ToLowerInvariant()
    }
    Invoke-Az postgres flexible-server update --name $postgresName --resource-group $ResourceGroup --admin-password $PostgresPassword
}
Invoke-Az postgres flexible-server db create --server-name $postgresName --resource-group $ResourceGroup --name $databaseName

if (-not $SecretKey) {
    $SecretKey = [Convert]::ToHexString(
        [Security.Cryptography.RandomNumberGenerator]::GetBytes(48)
    ).ToLowerInvariant()
}

$image = "$($registry.loginServer)/talentsync:$imageTag"
Invoke-Az acr build --registry $registryName --image "talentsync:$imageTag" --file Dockerfile --no-logs .

$environment = Get-AzJson containerapp env show --name $environmentName --resource-group $ResourceGroup
if (-not $environment) {
    $environment = Invoke-AzJson containerapp env create --name $environmentName --resource-group $ResourceGroup --location $Location
}

$app = Get-AzJson containerapp show --name $appName --resource-group $ResourceGroup
if (-not $app) {
    $credentials = Invoke-AzJson acr credential show --name $registryName
    $registryPassword = $credentials.passwords[0].value
    $encodedPassword = [Uri]::EscapeDataString($PostgresPassword)
    $databaseUrl = "postgresql+psycopg://${PostgresAdmin}:${encodedPassword}@${postgresName}.postgres.database.azure.com:5432/${databaseName}?sslmode=require"
    $minimumReplicas = if ($ScaleToZero) { 0 } else { 1 }
    $storageUrl = "https://${storageName}.blob.core.windows.net"
    $app = Invoke-AzJson containerapp create --name $appName --resource-group $ResourceGroup --environment $environmentName --image $image --registry-server $registry.loginServer --registry-username $credentials.username --registry-password $registryPassword --target-port 8000 --ingress external --min-replicas $minimumReplicas --max-replicas 3 --cpu 1.0 --memory 2Gi --system-assigned --secrets "database-url=$databaseUrl" "secret-key=$SecretKey" --env-vars "ENVIRONMENT=production" "DATABASE_URL=secretref:database-url" "SECRET_KEY=secretref:secret-key" "CV_PARSER=pypdf" "CV_OCR_ENABLED=false" "AZURE_STORAGE_ACCOUNT_URL=$storageUrl" "AZURE_STORAGE_CONTAINER=$containerName"
} else {
    $app = Invoke-AzJson containerapp update --name $appName --resource-group $ResourceGroup --image $image
}

$principalId = $app.identity.principalId
if ($principalId) {
    $role = Get-AzJson role assignment list --assignee-object-id $principalId --role "Storage Blob Data Contributor" --scope $storage.id
    if (-not $role) {
        & $azExecutable role assignment create --assignee-object-id $principalId --assignee-principal-type ServicePrincipal --role "Storage Blob Data Contributor" --scope $storage.id --only-show-errors --output none 2>$null
        if ($LASTEXITCODE -ne 0) {
            Write-Warning "No se pudo asignar el rol de Blob Storage. Verifica que tu cuenta pueda crear asignaciones RBAC."
        }
    }
}

$fqdn = (& $azExecutable containerapp show --name $appName --resource-group $ResourceGroup --query properties.configuration.ingress.fqdn --output tsv).Trim()
$healthUrl = "https://$fqdn/health"
for ($attempt = 1; $attempt -le 24; $attempt++) {
    try {
        $health = Invoke-RestMethod -Uri $healthUrl -TimeoutSec 15
        if ($health.status -eq "ok") { break }
    } catch {
        if ($attempt -eq 24) { throw "La aplicacion se desplego, pero no respondio en $healthUrl" }
        Start-Sleep -Seconds 5
    }
}

[pscustomobject]@{
    Url = "https://$fqdn"
    Health = $healthUrl
    ResourceGroup = $ResourceGroup
    ContainerApp = $appName
    PostgreSql = $postgresName
    StorageAccount = $storageName
    ContainerRegistry = $registryName
} | Format-List
