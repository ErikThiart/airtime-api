<?php
/**
 * SIMcloud REST API client for PHP 7.4+ (ext-curl and ext-json, both standard).
 *
 *   php simcloud.php balance
 *   php simcloud.php network 0821234567
 *   php simcloud.php data-products mtn
 *   php simcloud.php sms +27821234567 "Your order has shipped"
 *   php simcloud.php airtime 0821234567 vodacom 10 "Airtime for John"
 *
 * Environment (defaults target the local mock, so nothing spends money):
 *   SIMCLOUD_BASE_URL (live: https://simcloud.co.za), SIMCLOUD_TOKEN, SIMCLOUD_POLL_MS (default 3000)
 *
 * Exit codes: 0 for 2xx, 1 for API errors, 3 for an ambiguous network failure on a purchase
 * (do NOT retry; check the order first).
 */

function sc_env(string $name, string $fallback): string
{
    $v = getenv($name);
    return ($v === false || $v === '') ? $fallback : $v;
}

/** @return array{0:int,1:array} [http status, decoded body]. Throws only on transport failure. */
function sc_request(string $method, string $path, array $query = [], ?array $body = null): array
{
    $url = rtrim(sc_env('SIMCLOUD_BASE_URL', 'http://127.0.0.1:8081'), '/') . $path . ($query ? '?' . http_build_query($query) : '');
    $headers = ['Authorization: Bearer ' . sc_env('SIMCLOUD_TOKEN', 'demo-token'), 'Accept: application/json'];
    $ch = curl_init($url);
    curl_setopt_array($ch, [CURLOPT_RETURNTRANSFER => true, CURLOPT_TIMEOUT => 30, CURLOPT_CUSTOMREQUEST => $method]);
    if ($body !== null) {
        $headers[] = 'Content-Type: application/json';
        curl_setopt($ch, CURLOPT_POSTFIELDS, json_encode($body, JSON_UNESCAPED_UNICODE));
    }
    curl_setopt($ch, CURLOPT_HTTPHEADER, $headers);
    $raw = curl_exec($ch);
    if ($raw === false) {
        throw new RuntimeException(curl_error($ch));
    }
    $status = curl_getinfo($ch, CURLINFO_RESPONSE_CODE);
    curl_close($ch);
    $decoded = json_decode($raw, true);
    return [$status, is_array($decoded) ? $decoded : ['status' => 'error', 'message' => substr($raw, 0, 200)]];
}

function sc_wait_for_airtime($requestId, int $attempts = 20): array
{
    $pollUs = (int) sc_env('SIMCLOUD_POLL_MS', '3000') * 1000;
    for ($i = 0; $i < $attempts; $i++) {
        [$status, $body] = sc_request('GET', '/api/airtime.php', ['request_id' => $requestId]);
        if ($status !== 200 || !in_array($body['status'] ?? '', ['queued', 'pending'], true)) {
            return [$status, $body];
        }
        usleep($pollUs);
    }
    return [200, ['status' => 'pending', 'message' => "Still pending after $attempts checks; keep polling later."]];
}

function sc_emit(int $status, array $body): int
{
    echo "HTTP $status\n", json_encode($body, JSON_PRETTY_PRINT | JSON_UNESCAPED_SLASHES), "\n";
    return ($status >= 200 && $status < 300) ? 0 : 1;
}

if (PHP_SAPI === 'cli' && realpath($_SERVER['SCRIPT_FILENAME'] ?? '') === __FILE__) {
    $a = array_slice($argv, 1);
    $code = 2;
    try {
        switch ($a[0] ?? '') {
            case 'balance':       $code = sc_emit(...sc_request('GET', '/api/balance.php')); break;
            case 'network':       $code = sc_emit(...sc_request('GET', '/api/network.php', ['msisdn' => $a[1]])); break;
            case 'data-products': $code = sc_emit(...sc_request('GET', '/api/data.php', isset($a[1]) ? ['network' => $a[1]] : ['products' => 1])); break;
            case 'sms':           $code = sc_emit(...sc_request('POST', '/api/sms.php', [], ['recipient' => $a[1], 'message' => $a[2]])); break;
            case 'airtime':
                try {
                    [$status, $body] = sc_request('POST', '/api/airtime.php', [], ['msisdn' => $a[1], 'network' => $a[2], 'amount' => (float) $a[3], 'reference' => $a[4]]);
                } catch (RuntimeException $e) {
                    // The request may or may not have reached SIMcloud. Never resend blindly.
                    echo 'AMBIGUOUS: ', $e->getMessage(), ". Do not retry. Check GET /api/transactions.php for reference \"{$a[4]}\" first.\n";
                    exit(3);
                }
                if ($status === 201) {
                    sc_emit($status, $body);
                    $code = sc_emit(...sc_wait_for_airtime($body['request_id']));
                } else {
                    $code = sc_emit($status, $body);
                }
                break;
            default:
                echo "Commands: balance | network <msisdn> | data-products [network] | sms <+27...> <text> | airtime <msisdn> <network> <amount> <reference>\n";
        }
    } catch (Throwable $e) {
        fwrite(STDERR, 'error: ' . $e->getMessage() . "\n");
        $code = 1;
    }
    exit($code);
}
