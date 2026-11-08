# Prepaid electricity API: frequently asked questions

[Prepaid electricity home](README.md) · [Repository home](../README.md)

## Can I buy prepaid electricity through an API in South Africa?

Yes. The SIMcloud API lets you check a meter, place an order and fetch the token with a few HTTP calls. See the [guide](README.md) and the [code in 12 languages](README.md#code-in-every-language).

## How do I check whether a meter is supported?

`GET /api/electricity.php?meter_number=...`. The result is `success`, `unsupported` or `unknown`. `unknown` means the municipality could not confirm right now, which is not the same as unsupported, so try again shortly.

## What is the minimum and maximum purchase?

Whole rand from **R55 to R1000**. Fractions are rejected.

## What does the service fee cost?

SIMcloud documents it as `amount x 3 / 103`, capped at R10 and rounded down. For R150 the fee is R4 and R146 buys electricity. See [the fee table](how-it-works.md#the-fee).

## How do I get the token?

Poll the order until `status` is `success`. The reply holds the token details in `recharge_pin_information`. By default SIMcloud also sends the token to the `recipient` by SMS (`send_sms`, default true).

## What are key-change tokens?

Tokens that update the meter's settings. They must be entered before the purchase token, in order `KEY-CHANGE-1`, `KEY-CHANGE-2`. The `entry_order` field tells you the sequence. See [entering the tokens](how-it-works.md#entering-the-tokens).

## What if my request times out?

Do not buy again with a new reference. The purchase may have worked. Poll `GET ...?client_reference=` with the **same** reference. Repeating the same `POST` with the same reference and details returns the original result without buying twice.

## What does HTTP 202 `reconciliation_pending` mean?

SIMcloud could not confirm the purchase yet. It is not a failure. Poll by `client_reference` until it settles. Never rebuy.

## How do I stop duplicate purchases?

Use one unique `client_reference` per customer intent, store it before the first call, and put a unique constraint on it in your own database. See [why client_reference matters](how-it-works.md#why-client_reference-matters-so-much).

## Can I test without spending money?

Yes. Run the [local mock server](../simcloud-api/mock-server/mock_simcloud.py) and point any sample at it. It is not the real service, so finish with one small real purchase.

```bash
python3 simcloud-api/mock-server/mock_simcloud.py
python3 simcloud-api/samples/python/simcloud.py electricity 01234567890 150 0821234567 REF-1
```

## Which languages are supported?

The API is plain JSON over HTTPS, so any language works. This repository has tested examples for Java, Go, Python, Node.js, TypeScript, PHP, Ruby, Swift and Bash, and written (not yet executed) examples for C#, PowerShell and Oracle PL/SQL. See [the language pages](../languages/README.md).

## Which municipalities are covered?

SIMcloud does not publish a list. Use the meter check for each meter.

## Can an AI assistant buy electricity?

Yes, through the [SIMcloud MCP server](../simcloud-mcp/README.md), with a human approving every purchase. See the [tenant electricity use case](../simcloud-mcp/use-cases/06-electricity-for-tenants.md).

## Where do I get an API token?

Create one at [simcloud.co.za/api_token.php](https://simcloud.co.za/api_token.php) after you register. Support: customercare@freepaid.co.za.

## Is the token a secret?

Yes. An electricity token is worth money. Do not log it, and deliver it only to the customer. See [security and operations](../simcloud-api/docs/security-and-operations.md).
