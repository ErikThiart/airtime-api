<#
.SYNOPSIS
  SIMcloud REST API client for PowerShell 5.1+ and PowerShell 7 (no modules needed).

.EXAMPLE
  ./simcloud.ps1 balance
  ./simcloud.ps1 network 0821234567
  ./simcloud.ps1 data-products mtn
  ./simcloud.ps1 sms +27821234567 "Your order has shipped"
  ./simcloud.ps1 airtime 0821234567 vodacom 10 "Airtime for John"
  ./simcloud.ps1 electricity-check 01234567890
  ./simcloud.ps1 electricity 01234567890 150 0821234567 UnitB-2026-11

.NOTES
  Environment (defaults target the local mock, so nothing spends money):
    SIMCLOUD_BASE_URL (live: https://simcloud.co.za), SIMCLOUD_TOKEN, SIMCLOUD_POLL_MS (default 3000)
  Exit codes: 0 for 2xx, 1 for API errors, 3 for an ambiguous network failure on a purchase.

  STATUS: run against the mock server by this repository's CI (tests/run-samples.sh) on PowerShell 7.
#>
param(
    [Parameter(Position = 0)][string]$Command,
    [Parameter(Position = 1, ValueFromRemainingArguments = $true)][string[]]$Rest
)

$base = $(if ($env:SIMCLOUD_BASE_URL) { $env:SIMCLOUD_BASE_URL } else { 'http://127.0.0.1:8081' }).TrimEnd('/')
$token = if ($env:SIMCLOUD_TOKEN) { $env:SIMCLOUD_TOKEN } else { 'demo-token' }
$pollMs = if ($env:SIMCLOUD_POLL_MS) { [int]$env:SIMCLOUD_POLL_MS } else { 3000 }

# Returns @{ Status = int; Body = object }. 4xx/5xx are returned; transport failures throw.
function Send-Simcloud([string]$Method, [string]$Path, $Body = $null) {
    $params = @{
        Uri = "$base$Path"; Method = $Method; UseBasicParsing = $true; TimeoutSec = 30
        Headers = @{ Authorization = "Bearer $token"; Accept = 'application/json' }
    }
    if ($null -ne $Body) { $params.Body = ($Body | ConvertTo-Json -Compress); $params.ContentType = 'application/json' }
    try {
        $response = Invoke-WebRequest @params
        $status = [int]$response.StatusCode; $text = $response.Content
    } catch [System.Net.WebException] {
        if (-not $_.Exception.Response) { throw }
        $status = [int]$_.Exception.Response.StatusCode
        $text = (New-Object System.IO.StreamReader($_.Exception.Response.GetResponseStream())).ReadToEnd()
    } catch {
        # PowerShell 7: HttpResponseException carries the response
        if ($_.Exception.Response -and $_.Exception.Response.StatusCode) {
            $status = [int]$_.Exception.Response.StatusCode
            $text = $_.ErrorDetails.Message
        } else { throw }
    }
    try { $parsed = if ($text) { $text | ConvertFrom-Json } else { [pscustomobject]@{} } }
    catch { $parsed = [pscustomobject]@{ status = 'error'; message = $text.Substring(0, [Math]::Min(200, $text.Length)) } }
    @{ Status = $status; Body = $parsed }
}

function Write-Result($r) {
    "HTTP $($r.Status)"
    $r.Body | ConvertTo-Json -Depth 10
}

function Wait-Airtime($RequestId) {
    for ($i = 0; $i -lt 20; $i++) {
        $r = Send-Simcloud 'GET' "/api/airtime.php?request_id=$RequestId"
        if ($r.Status -ne 200 -or $r.Body.status -notin 'queued', 'pending') { return $r }
        Start-Sleep -Milliseconds $pollMs
    }
    $r
}

# Poll by client_reference until the order leaves pending. Final: success, failed, cancelled.
function Wait-Electricity($ClientReference) {
    for ($i = 0; $i -lt 20; $i++) {
        $r = Send-Simcloud 'GET' ('/api/electricity.php?client_reference=' + [uri]::EscapeDataString($ClientReference))
        if ($r.Status -ne 200 -or $r.Body.status -ne 'pending') { return $r }
        Start-Sleep -Milliseconds $pollMs
    }
    $r
}

$result = $null
try {
    switch ($Command) {
        'balance'       { $result = Send-Simcloud 'GET' '/api/balance.php' }
        'network'       { $result = Send-Simcloud 'GET' ('/api/network.php?msisdn=' + [uri]::EscapeDataString($Rest[0])) }
        'data-products' { $result = Send-Simcloud 'GET' $(if ($Rest.Count -gt 0) { '/api/data.php?network=' + [uri]::EscapeDataString($Rest[0]) } else { '/api/data.php?products=1' }) }
        'sms'           { $result = Send-Simcloud 'POST' '/api/sms.php' @{ recipient = $Rest[0]; message = $Rest[1] } }
        'airtime' {
            try {
                $order = Send-Simcloud 'POST' '/api/airtime.php' @{ msisdn = $Rest[0]; network = $Rest[1]; amount = [double]::Parse($Rest[2], [cultureinfo]::InvariantCulture); reference = $Rest[3] }
            } catch {
                # The request may or may not have reached SIMcloud. Never resend blindly.
                "AMBIGUOUS: $($_.Exception.Message). Do not retry. Check GET /api/transactions.php for reference `"$($Rest[3])`" first."
                exit 3
            }
            if ($order.Status -eq 201) { Write-Result $order; $result = Wait-Airtime $order.Body.request_id } else { $result = $order }
        }
        'electricity-check' { $result = Send-Simcloud 'GET' ('/api/electricity.php?meter_number=' + [uri]::EscapeDataString($Rest[0])) }
        'electricity' {
            if ($Rest[1] -notmatch '^\d+$') { 'Amount must be whole rand (R55 to R1000).'; exit 2 }
            try {
                $order = Send-Simcloud 'POST' '/api/electricity.php' @{ meter_number = $Rest[0]; amount = [int]$Rest[1]; client_reference = $Rest[3]; recipient = $Rest[2] }
            } catch {
                "AMBIGUOUS: $($_.Exception.Message). Do not retry or use a new reference. Poll client_reference `"$($Rest[3])`"."
                exit 3
            }
            if ($order.Status -in 201, 202) { Write-Result $order; $result = Wait-Electricity $Rest[3] } else { $result = $order }  # 202 = reconciliation pending: keep polling, never rebuy
        }
        default {
            'Commands: balance | network <msisdn> | data-products [network] | sms <+27...> <text> | airtime <msisdn> <network> <amount> <reference> | electricity-check <meter> | electricity <meter> <amount> <recipient> <client_reference>'
            exit 2
        }
    }
} catch {
    [Console]::Error.WriteLine("error: $($_.Exception.Message)")
    exit 1
}
Write-Result $result
exit $(if ($result.Status -ge 200 -and $result.Status -lt 300) { 0 } else { 1 })
