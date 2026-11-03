[CmdletBinding()]
param(
    [string]$Profile = 'talentsync',
    [ValidateRange(1, 1000)][decimal]$MinimumCreditUsd = 90,
    [ValidateRange(1, 180)][int]$RequiredDays = 31
)

# Read-only: this script never creates resources or changes the account plan.
$ErrorActionPreference = 'Stop'
Set-StrictMode -Version Latest
$repository = Split-Path -Parent $PSScriptRoot
$installed = Get-Command aws -ErrorAction SilentlyContinue
$portable = Join-Path $repository '.tmp/aws-cli-v2/Amazon/AWSCLIV2/aws.exe'
$awsExecutable = if ($installed) { $installed.Source } elseif (Test-Path -LiteralPath $portable) { $portable } else { $null }
if (-not $awsExecutable) { throw 'Falta AWS CLI v2.' }

$previousPager = $env:AWS_PAGER
try {
    $env:AWS_PAGER = ''
    # The Free Tier API is queried independently of the deployment region.
    $raw = & $awsExecutable freetier get-account-plan-state --profile $Profile --region us-east-1 --output json --no-cli-pager 2>$null
    if ($LASTEXITCODE -ne 0 -or -not $raw) {
        throw 'No se pudo comprobar el plan. Inicia sesión en AWS CLI con el perfil indicado; no se han creado recursos.'
    }
    $plan = $raw | ConvertFrom-Json
    $isFree = $plan.accountPlanType -eq 'FREE'
    $isActive = $plan.accountPlanStatus -eq 'ACTIVE'
    $credit = $plan.accountPlanRemainingCredits
    $sufficientCredit = $credit.unit -eq 'USD' -and [decimal]$credit.amount -ge $MinimumCreditUsd
    # PowerShell 7 can deserialize an ISO timestamp directly as DateTime.
    # Converting that value to a culture-specific string breaks on es-CO hosts.
    $expiration = if ($plan.accountPlanExpirationDate -is [DateTime]) {
        [DateTimeOffset]::new($plan.accountPlanExpirationDate.ToUniversalTime())
    } else {
        [DateTimeOffset]::Parse([string]$plan.accountPlanExpirationDate, [Globalization.CultureInfo]::InvariantCulture)
    }
    $enoughDays = $expiration -gt [DateTimeOffset]::UtcNow.AddDays($RequiredDays)
    $report = [ordered]@{
        checked_at = [DateTimeOffset]::UtcNow.ToString('o')
        free_plan = $isFree
        active = $isActive
        remaining_credit_usd = if ($credit.unit -eq 'USD') { $credit.amount } else { $null }
        expiration = $expiration.ToString('o')
        sufficient_credit = $sufficientCredit
        sufficient_days = $enoughDays
        readiness = $isFree -and $isActive -and $sufficientCredit -and $enoughDays
        resources_created = $false
    }
    $privateDirectory = Join-Path $repository '.local'
    New-Item -ItemType Directory -Force -Path $privateDirectory | Out-Null
    $report | ConvertTo-Json | Set-Content -LiteralPath (Join-Path $privateDirectory 'aws-free-plan-check.json') -Encoding UTF8
    if (-not $report.readiness) {
        throw 'Plan, crédito o vigencia insuficientes para el despliegue gratuito previsto. No actualizar a pago ni crear recursos.'
    }
    $localExpiration = [TimeZoneInfo]::ConvertTimeBySystemTimeZoneId($expiration, 'SA Pacific Standard Time')
    Write-Host "Free Plan activo: $($credit.amount) USD; vigente hasta $($localExpiration.ToString('yyyy-MM-dd')) (hora de Colombia)."
    Write-Host 'Validación de cuenta superada. Aún faltan el cálculo de costes de la región y el inventario antes de crear recursos.'
} finally {
    $env:AWS_PAGER = $previousPager
}
