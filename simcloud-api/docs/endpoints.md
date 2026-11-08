# Endpoint reference

Every field below comes from the published SIMcloud docs ([simcloud.co.za/api](https://simcloud.co.za/api/)) and the OpenAPI contract in [`openapi/`](../openapi/simcloud-openapi.yaml). Where the docs do not say something, this page says so rather than guessing.

[SIMcloud API home](../README.md)

**Contents:** [Conventions](#conventions) · [Balance](#balance) · [Network lookup](#network-lookup) · [SMS](#sms) · [Airtime](#airtime) · [Data](#data) · [VAS vouchers](#vas-vouchers) · [Electricity](#electricity) · [Transaction history](#transaction-history) · [Registration](#registration)

## Conventions

- Base URL `https://simcloud.co.za`, all paths end in `.php`.
- Header on every request: `Authorization: Bearer YOUR_API_TOKEN`. Send `Content-Type: application/json` on POST.
- Success bodies carry `"status": "success"` or an order status. Error bodies carry `"status": "error"` and a `message`. The HTTP status code is the signal to branch on.
- **Phone numbers:** `0821234567` and `+27821234567` are both used in the docs. Orders echo back the number in international form (`+27...`). SMS recipients must be `+27` followed by nine digits.
- **Networks:** friendly names are accepted. See the table under [Airtime](#airtime).
- **Amounts** are in rand, with a decimal point.
- Money endpoints are asynchronous. Read [orders, polling and retries](orders-and-polling.md) before you build.

## Balance

`GET /api/balance.php`

```json
{ "status": "success", "user_id": 123, "username": "4250521", "name": "John Smith", "balance": 5879.33, "updated_at": "2026-04-16 17:00:00" }
```

Returns the stored **last known** balance. Errors: 401, 405.

## Network lookup

`GET /api/network.php?msisdn=0821234567`

```json
{ "status": "success", "msisdn": "+27821234567", "network": "mtn" }
```

Errors: 400 (missing or invalid `msisdn`), 401, 404 (no matching network), 405. Each lookup is logged against your account.

Use it before an airtime or data order when the customer did not tell you the network.

## SMS

### Send

`POST /api/sms.php`

| Field | Type | Rule |
|---|---|---|
| `recipient` | string | `+27` and nine digits |
| `message` | string | Up to 459 characters. UTF-8 is supported |

```json
{ "status": "success", "message": "SMS queued successfully", "sms_id": "123456", "sms_count": 1, "timestamp": "2024-10-24 14:30:00" }
```

Credits: 1 up to 160 characters, 2 up to 306, 3 up to 459. Errors: 400, 401, 500.

### Check status

`GET /api/sms.php?sms_id=123456` returns `{ "sms_id": "123456", "status": "delivered" }`.

Statuses the docs list: `queued`, `pending`, `sent`, `failed`, `delivered`, `staged`, `unknown`. Only `delivered` is defined ("received on the recipient handset"). A check made within 15 seconds of sending returns `queued`. Errors: 400, 401, 404.

## Airtime

### Order

`POST /api/airtime.php`

| Field | Type | Rule |
|---|---|---|
| `msisdn` | string | Number to top up |
| `network` | string | See table |
| `amount` | number | R2 to R999 |
| `reference` | string | Your reference |

| Network | Accepted values |
|---|---|
| MTN | `mtn`, `p-mtn` |
| Cell C | `cellc`, `cell-c`, `cell c`, `p-cellc` |
| Vodacom | `vodacom`, `p-vodacom` |
| Telkom | `telkom`, `heita`, `p-heita` |

Reply, HTTP **201**:

```json
{ "status": "success", "message": "Airtime order queued successfully", "request_id": 1527245,
  "service": "airtime", "msisdn": "+27821234567", "network": "mtn", "amount": 10.00,
  "reference": "Airtime for John", "queue_status": "queued", "timestamp": "..." }
```

Rejections:

| Case | HTTP | Body |
|---|---|---|
| Not enough money | 400 per the OpenAPI file (the docs page does not state the code) | `status`, `message`, `required_balance`, `available_balance` |
| Same number and amount within 5 minutes | 409 | `message`: "An order for the same MSISDN and amount has been placed in the last 5 minutes." |
| Bad field | 400 | |
| Bad token | 401 | |

### Check an order

`GET /api/airtime.php?request_id=1527245` (or `?orderno=` once the platform order number exists). At least one is required.

```json
{ "status": "pending", "platform_order_number": "...", "queue_status": "...",
  "final_order_id": "...", "final_order_status": null, "error": null,
  "created_at": "...", "updated_at": "..." }
```

| `status` | Meaning |
|---|---|
| `queued` | Stored, waiting to be placed |
| `pending` | A platform order number exists, no final result yet |
| `delivered` | Done (`final_order_status` is `delivered`, `error` is `Success`) |
| `failed` | Failed |

Errors: 400, 401, 404 (not found under this account).

## Data

### Catalogue

`GET /api/data.php?products=1` (add `&network=mtn` to filter; a bare GET also returns the catalogue)

```json
{ "status": "success", "service": "data", "count": 2,
  "products": [ { "product_id": 101, "network": "pd-mtn", "network_name": "MTN", "description": "MTN 1GB Anytime",
                  "groupname": "Anytime", "amount": 99.0, "sellvalue": 99.0 } ] }
```

### Order

`POST /api/data.php` takes the same fields as airtime (`msisdn`, `network`, `amount`, `reference`; `sellvalue` is an alias for `amount`). The `amount` must match a bundle sell value from the catalogue for that network. Data network codes are `mtn`/`pd-mtn`, `cellc`/`cell-c`/`cell c`/`pd-cellc`, `vodacom`/`pd-vodacom`, `telkom`/`heita`/`pd-heita`.

Reply, status codes, duplicate rule and polling are the same as airtime, with `service: "data"`. Query with `GET /api/data.php?request_id=` or `?orderno=`.

## VAS vouchers

Voucher products such as shop and entertainment vouchers.

1. `GET /api/vas.php` lists active products: product ID, voucher type, slug, default amount, available amounts, logo URL.
2. `POST /api/vas.php` with `product_id` **or** `voucher_type`, plus `amount` (must be an available amount) and `reference` (maximum 200 characters). The docs also accept the aliases `product`, `voucher_supplier`, `user_reference` and `client_reference`. Returns an order ID and a transaction ID (UUID).
3. `GET /api/vas.php?order_id=` or `?transaction_id=` returns the order. Only API-created orders owned by your account are visible.

Status fields: `status` (`pending`, `success`, `failed`), `process_status` (for example `Pending`, `Submitted`, `Completed`), `billing_status`, timestamps (`created_at`, `submitted_at`, `completed_at`, `updated_at`), and supplier diagnostics (`supplier_http_status`, `supplier_error`). On success the reply includes `vouchers`: `voucher_code`, `value`, `expiry_date`. **Voucher codes are secrets**; see [security](security-and-operations.md).

Errors: 400 (validation, unavailable denomination, or insufficient balance: "Amount is not available for this VAS product", "Insufficient balance. Please top up your account."), 401, 404, 405.

## Electricity

Prepaid electricity has more rules than the others. Read the [electricity guide](electricity.md). Summary:

- `GET /api/electricity.php?meter_number=` checks support first (`success`, `unsupported`, `unknown`).
- `POST /api/electricity.php` needs `meter_number`, `amount` (whole rand, R55 to R1000), `client_reference` (unique per purchase) and `recipient`. Optional: `send_sms` (default true), `sms_company_name`.
- `GET /api/electricity.php?order_id=`, `?client_reference=` or `?order_reference_id=` returns status and, on success, the token details.

## Transaction history

`GET /api/transactions.php?date_from=2026-07-01&date_to=2026-07-31&type=airtime,data&limit=50`

| Parameter | Rule |
|---|---|
| `date_from`, `date_to` | Required. `YYYY-MM-DD`, inclusive, Africa/Johannesburg time. Maximum span 90 days |
| `type` | Optional. Comma-separated: `airtime`, `data`, `electricity`, `vas`, `sms` |
| `limit` | 1 to 100, default 50 |
| `cursor` | Opaque value from the previous page. Use it with the **same** dates and type |

```json
{ "status": "success", "date_from": "...", "date_to": "...", "type": "...",
  "transactions": [ { "id": "airtime:1395227", "service": "airtime", "status": "success", "reason": null,
                      "reference": "Airtime for John", "created_at": "...", "updated_at": "..." } ],
  "pagination": { "limit": 50, "next_cursor": "eyJ..." } }
```

Newest first. `status` is `success`, `failed` or `pending`. SMS stays `pending` until SIMcloud receives a `DELIVRD` receipt. Results include transactions from the web portal, CSV import, recurring processing and the API, and **exclude** pricing, wallet values, recipients, SMS content, electricity tokens and voucher codes. Errors: 400, 401.

This is the endpoint to use for reconciliation and for finding an order whose `POST` response you never received. It is documented on the site but is not in the OpenAPI file at the time of writing.

## Registration

The docs describe a registration service that creates a child account under a parent account and returns the child's API token. It is aimed at platforms that onboard their own customers. See [simcloud.co.za/api](https://simcloud.co.za/api/) for the current request fields. It is also available as the `register_simcloud_user` tool in the [MCP server](../../simcloud-mcp/docs/tools-reference.md).
