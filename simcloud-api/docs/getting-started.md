# Getting started with the SIMcloud API

Goal: a successful balance call, then your first airtime order. About 5 minutes.

[SIMcloud API home](../README.md)

## 1. Get a token

1. Register and sign in at [simcloud.co.za](https://simcloud.co.za).
2. Create an API token at [simcloud.co.za/api_token.php](https://simcloud.co.za/api_token.php).
3. Fund your wallet. Airtime, data, VAS, SMS and electricity all draw from it.

The token belongs to your account and wallet. Treat it like a password.

Every request sends it as a bearer token:

```http
Authorization: Bearer YOUR_API_TOKEN
```

## 2. Make a call that costs nothing

```bash
curl -s https://simcloud.co.za/api/balance.php \
  -H "Authorization: Bearer $SIMCLOUD_TOKEN" \
  -H "Accept: application/json"
```

```json
{
  "status": "success",
  "user_id": 123,
  "username": "4250521",
  "name": "John Smith",
  "balance": 5879.33,
  "updated_at": "2026-04-16 17:00:00"
}
```

`balance` is the **last known** balance, with the time it was stored in `updated_at`. After a purchase it can lag by a moment.

Also free, and useful before you buy: a network lookup.

```bash
curl -s "https://simcloud.co.za/api/network.php?msisdn=0821234567" \
  -H "Authorization: Bearer $SIMCLOUD_TOKEN"
# {"status":"success","msisdn":"+27821234567","network":"mtn"}
```

## 3. Place an order (spends money)

```bash
curl -s -X POST https://simcloud.co.za/api/airtime.php \
  -H "Authorization: Bearer $SIMCLOUD_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{"msisdn":"0821234567","network":"mtn","amount":10.00,"reference":"Airtime for John"}'
```

The reply is HTTP **201** and carries an ID, not a result:

```json
{
  "status": "success",
  "message": "Airtime order queued successfully",
  "request_id": 1527245,
  "service": "airtime",
  "msisdn": "+27821234567",
  "queue_status": "queued",
  "timestamp": "..."
}
```

Now poll:

```bash
curl -s "https://simcloud.co.za/api/airtime.php?request_id=1527245" \
  -H "Authorization: Bearer $SIMCLOUD_TOKEN"
```

Keep asking until `status` is `delivered` or `failed`. See [orders, polling and retries](orders-and-polling.md).

## 4. Practise safely first

Run the local mock and point every sample at it. No account, no token, no money.

```bash
python3 mock-server/mock_simcloud.py             # http://127.0.0.1:8081, token: demo-token
cd samples/python && python3 simcloud.py airtime 0821234567 vodacom 10 "Test"
```

## 5. Choose your language

Each folder under [`samples/`](../samples) has the same five commands. See the [language notes](language-notes.md) for JSON libraries and what to watch in each.

## Next

- [Endpoint reference](endpoints.md)
- [Errors](errors.md)
- [Security and operations](security-and-operations.md)
