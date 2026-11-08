<?php
/**
 * Freepaid Airtime API client for PHP 7.4+ (needs ext-curl and ext-simplexml, both standard).
 *
 *   php freepaid.php balance
 *   php freepaid.php products
 *   php freepaid.php order-pinless p-vodacom 10 0821234567
 *   php freepaid.php query 7000001
 *   php freepaid.php order-pinned vodacom 29 1
 *   php freepaid.php fetch 7000002
 *
 * Environment (defaults target the local mock, so nothing spends money):
 *   FREEPAID_ENDPOINT, FREEPAID_USER, FREEPAID_PASS
 *
 * PHP's built-in SoapClient also handles this RPC/encoded WSDL. This file builds the envelope
 * by hand so it behaves the same way as every other language in this repository.
 */

const FREEPAID_NS = 'https://ws.freepaid.co.za:443/airtimeplus/';

function fp_env(string $name, string $fallback): string
{
    $v = getenv($name);
    return ($v === false || $v === '') ? $fallback : $v;
}

/** @param array<int, array{0:string,1:string,2:string|int|float}> $fields name, xsd type, value */
function fp_envelope(string $op, array $fields): string
{
    $body = '';
    foreach ($fields as [$name, $type, $value]) {
        $body .= sprintf('<%s xsi:type="xsd:%s">%s</%s>', $name, $type, htmlspecialchars((string) $value, ENT_XML1 | ENT_QUOTES, 'UTF-8'), $name);
    }
    return '<?xml version="1.0" encoding="UTF-8"?>'
        . '<SOAP-ENV:Envelope xmlns:SOAP-ENV="http://schemas.xmlsoap.org/soap/envelope/" xmlns:ns1="' . FREEPAID_NS . '" '
        . 'xmlns:xsd="http://www.w3.org/2001/XMLSchema" xmlns:xsi="http://www.w3.org/2001/XMLSchema-instance" '
        . 'xmlns:SOAP-ENC="http://schemas.xmlsoap.org/soap/encoding/" '
        . 'SOAP-ENV:encodingStyle="http://schemas.xmlsoap.org/soap/encoding/"><SOAP-ENV:Body>'
        . "<ns1:$op><request xsi:type=\"ns1:{$op}In\">$body</request></ns1:$op>"
        . '</SOAP-ENV:Body></SOAP-ENV:Envelope>';
}

function fp_call(string $op, array $extra = []): array
{
    $fields = array_merge([
        ['user', 'int', fp_env('FREEPAID_USER', '1000001')],
        ['pass', 'string', fp_env('FREEPAID_PASS', 'demo-password')],
    ], $extra);

    $ch = curl_init(fp_env('FREEPAID_ENDPOINT', 'http://127.0.0.1:8080/'));
    curl_setopt_array($ch, [
        CURLOPT_POST => true,
        CURLOPT_POSTFIELDS => fp_envelope($op, $fields),
        CURLOPT_RETURNTRANSFER => true,
        CURLOPT_TIMEOUT => 30,
        CURLOPT_HTTPHEADER => ['Content-Type: text/xml; charset=utf-8', 'SOAPAction: "' . FREEPAID_NS . $op . '"'],
    ]);
    $raw = curl_exec($ch);
    if ($raw === false) {
        throw new RuntimeException('HTTP error: ' . curl_error($ch));
    }
    curl_close($ch);

    $prev = libxml_use_internal_errors(true);
    $xml = simplexml_load_string($raw, 'SimpleXMLElement', LIBXML_NONET);
    libxml_use_internal_errors($prev);
    if ($xml === false) {
        throw new RuntimeException('Response is not valid XML');
    }
    $reply = $xml->xpath('//*[local-name()="reply"]')[0] ?? null;
    if ($reply === null) {
        throw new RuntimeException('No <reply> in response');
    }

    $result = [];
    foreach ($reply->children() as $child) {
        $name = $child->getName();
        if ($name === 'vouchers' || $name === 'products') {
            $result[$name] = [];
            foreach ($child->children() as $item) {
                $row = [];
                foreach ($item->children() as $f) {
                    $row[$f->getName()] = (string) $f;
                }
                $result[$name][] = $row;
            }
        } else {
            $result[$name] = (string) $child;
        }
    }
    $result['ok'] = ($result['status'] ?? '') === '1';
    return $result;
}

function fp_place_order(string $network, $value, int $count = 1, string $extra = ''): array
{
    return fp_call('placeOrder', [
        ['refno', 'string', 'php-' . bin2hex(random_bytes(4))],
        ['network', 'string', $network],
        ['sellvalue', 'float', number_format((float) $value, 2, '.', '')],
        ['count', 'int', $count],
        ['extra', 'string', $extra],
    ]);
}

function fp_show(array $result): void
{
    foreach ($result as $k => $v) {
        if (is_array($v)) {
            printf("%-10s %d\n", $k, count($v));
            foreach ($v as $row) {
                $parts = [];
                foreach ($row as $a => $b) {
                    $parts[] = "$a=$b";
                }
                echo '           ', implode(' ', $parts), "\n";
            }
        } else {
            printf("%-10s %s\n", $k, is_bool($v) ? ($v ? 'True' : 'False') : $v);
        }
    }
}

if (PHP_SAPI === 'cli' && realpath($_SERVER['SCRIPT_FILENAME'] ?? '') === __FILE__) {
    $a = array_slice($argv, 1);
    $cmd = $a[0] ?? '';
    try {
        switch ($cmd) {
            case 'balance':       $r = fp_call('fetchBalance'); break;
            case 'products':      $r = fp_call('fetchProducts'); break;
            case 'order-pinless': $r = fp_place_order($a[1], $a[2], 1, $a[3]); break;
            case 'query':         $r = fp_call('queryOrder', [['orderno', 'string', $a[1]]]); break;
            case 'order-pinned':  $r = fp_place_order($a[1], $a[2], (int) ($a[3] ?? 1)); break;
            case 'fetch':         $r = fp_call('fetchOrder', [['orderno', 'string', $a[1]]]); break;
            default:
                fwrite(STDOUT, "Commands: balance | products | order-pinless <network> <value> <cell> | query <orderno> | order-pinned <network> <value> [count] | fetch <orderno>\n");
                exit(2);
        }
    } catch (Throwable $e) {
        fwrite(STDERR, 'error: ' . $e->getMessage() . "\n");
        exit(1);
    }
    fp_show($r);
    exit($r['ok'] ? 0 : 1);
}
