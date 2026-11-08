<#
.SYNOPSIS
  Freepaid Airtime API client for PowerShell 5.1+ and PowerShell 7 (no modules needed).

.EXAMPLE
  ./freepaid.ps1 balance
  ./freepaid.ps1 products
  ./freepaid.ps1 order-pinless p-vodacom 10 0821234567
  ./freepaid.ps1 query 7000001
  ./freepaid.ps1 order-pinned vodacom 29 1
  ./freepaid.ps1 fetch 7000002

.NOTES
  Environment (defaults target the local mock, so nothing spends money):
    FREEPAID_ENDPOINT, FREEPAID_USER, FREEPAID_PASS

  STATUS: run against the mock server by this repository's CI (tests/run-samples.sh) on PowerShell 7.
#>
param(
    [Parameter(Position = 0)][string]$Command,
    [Parameter(Position = 1, ValueFromRemainingArguments = $true)][string[]]$Rest
)

$ns = 'https://ws.freepaid.co.za:443/airtimeplus/'
$endpoint = if ($env:FREEPAID_ENDPOINT) { $env:FREEPAID_ENDPOINT } else { 'http://127.0.0.1:8080/' }
$user = if ($env:FREEPAID_USER) { $env:FREEPAID_USER } else { '1000001' }
$pass = if ($env:FREEPAID_PASS) { $env:FREEPAID_PASS } else { 'demo-password' }

function Get-Envelope([string]$Op, [object[]]$Fields) {
    $body = ($Fields | ForEach-Object {
        '<{0} xsi:type="xsd:{1}">{2}</{0}>' -f $_[0], $_[1], [System.Security.SecurityElement]::Escape([string]$_[2])
    }) -join ''
    '<?xml version="1.0" encoding="UTF-8"?><SOAP-ENV:Envelope xmlns:SOAP-ENV="http://schemas.xmlsoap.org/soap/envelope/" ' +
    "xmlns:ns1=`"$ns`" xmlns:xsd=`"http://www.w3.org/2001/XMLSchema`" xmlns:xsi=`"http://www.w3.org/2001/XMLSchema-instance`" " +
    'xmlns:SOAP-ENC="http://schemas.xmlsoap.org/soap/encoding/" SOAP-ENV:encodingStyle="http://schemas.xmlsoap.org/soap/encoding/"><SOAP-ENV:Body>' +
    "<ns1:$Op><request xsi:type=`"ns1:${Op}In`">$body</request></ns1:$Op></SOAP-ENV:Body></SOAP-ENV:Envelope>"
}

function Invoke-Freepaid([string]$Op, [object[]]$Extra = @()) {
    $fields = @(, @('user', 'int', $user)) + @(, @('pass', 'string', $pass)) + $Extra
    $response = Invoke-WebRequest -Uri $endpoint -Method Post -UseBasicParsing `
        -ContentType 'text/xml; charset=utf-8' -Headers @{ SOAPAction = "`"$ns$Op`"" } `
        -Body ([System.Text.Encoding]::UTF8.GetBytes((Get-Envelope $Op $fields))) -TimeoutSec 30
    $xml = [xml]$response.Content
    $reply = $xml.SelectSingleNode('//*[local-name()="reply"]')
    if (-not $reply) { throw "No <reply> in response" }
    $result = [ordered]@{}
    foreach ($child in $reply.ChildNodes) {
        if ($child.LocalName -in 'vouchers', 'products') {
            $result[$child.LocalName] = @($child.ChildNodes | ForEach-Object {
                ($_.ChildNodes | ForEach-Object { '{0}={1}' -f $_.LocalName, $_.InnerText }) -join ' '
            })
        } else { $result[$child.LocalName] = $child.InnerText }
    }
    $result['ok'] = ($result['status'] -eq '1')
    $result
}

function Invoke-Order([string]$Network, [string]$Value, [int]$Count, [string]$Extra) {
    Invoke-Freepaid 'placeOrder' @(
        , @('refno', 'string', ('ps-' + [guid]::NewGuid().ToString('N').Substring(0, 8)))
        , @('network', 'string', $Network)
        , @('sellvalue', 'float', ([double]::Parse($Value, [cultureinfo]::InvariantCulture)).ToString('F2', [cultureinfo]::InvariantCulture))
        , @('count', 'int', $Count)
        , @('extra', 'string', $Extra))
}

try {
    $result = switch ($Command) {
        'balance'       { Invoke-Freepaid 'fetchBalance' }
        'products'      { Invoke-Freepaid 'fetchProducts' }
        'order-pinless' { Invoke-Order $Rest[0] $Rest[1] 1 $Rest[2] }
        'query'         { Invoke-Freepaid 'queryOrder' @(, @('orderno', 'string', $Rest[0])) }
        'order-pinned'  { Invoke-Order $Rest[0] $Rest[1] $(if ($Rest.Count -gt 2) { [int]$Rest[2] } else { 1 }) '' }
        'fetch'         { Invoke-Freepaid 'fetchOrder' @(, @('orderno', 'string', $Rest[0])) }
        default {
            Write-Output 'Commands: balance | products | order-pinless <network> <value> <cell> | query <orderno> | order-pinned <network> <value> [count] | fetch <orderno>'
            exit 2
        }
    }
} catch {
    [Console]::Error.WriteLine("error: $($_.Exception.Message)")
    exit 1
}

foreach ($key in $result.Keys) {
    $value = $result[$key]
    if ($value -is [array]) {
        '{0,-10} {1}' -f $key, $value.Count
        $value | ForEach-Object { '           ' + $_ }
    } else {
        '{0,-10} {1}' -f $key, $(if ($value -is [bool]) { if ($value) { 'True' } else { 'False' } } else { $value })
    }
}
exit $(if ($result['ok']) { 0 } else { 1 })
