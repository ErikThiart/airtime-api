# 10. Build an integration with an AI pair programmer

[Use cases](README.md) · [SIMcloud MCP home](../README.md)

## Scenario

You are a developer adding airtime, data or SMS to an app (a CRM, a loyalty system, a support portal, a SaaS product) and want an AI assistant to write the integration correctly: right fields, right status handling, no double spends.

## What to give the assistant

| Give it | Why |
|---|---|
| The [OpenAPI file](../../simcloud-api/openapi/simcloud-openapi.yaml) | Exact paths and request fields, so it does not guess |
| The [endpoint reference](../../simcloud-api/docs/endpoints.md) | Response fields and statuses that OpenAPI omits |
| [Orders, polling and retries](../../simcloud-api/docs/orders-and-polling.md) | The idempotency pattern |
| The [REST sample](../../simcloud-api/samples) for your language | A style to follow |
| The [mock server](../../simcloud-api/mock-server/mock_simcloud.py) | A safe target to run the code against |
| Optional: the MCP connection (read-only) | So it can look up the network, list data products and check the real catalogue while it works |

For Codex, the [SIMcloud plugin](https://github.com/ErikThiart/simcloud-codex-plugin) packages the skill, OpenAPI file and MCP connection for you.

## Try it

> Using simcloud-openapi.yaml and orders-and-polling.md, add a `RewardService` to our Laravel app that sends airtime when a customer reaches 1 000 points. Requirements: store the request_id before returning, unique business key per reward, poll in a queued job with backoff, treat timeouts as UNKNOWN, never retry a purchase, handle 409 and 401. Run it against the mock server. Show me the tests.

> Review this integration for double-spend risks.

> Generate a typed client from the OpenAPI file and wrap it in our HTTP client with a 30 second timeout and structured logging that never prints the bearer token.

## What good looks like

- A database table with a **unique business key** and states `SENDING`, `QUEUED`, `DELIVERED`, `FAILED`, `UNKNOWN`.
- The `request_id` saved **before** anything else.
- A scheduled poller with backoff and a cap.
- `UNKNOWN` on timeouts and 5xx, with a reconciliation job over `GET /api/transactions.php`.
- Tests that run against `mock_simcloud.py` for: success, insufficient balance, 409 duplicate, 401, timeout.
- No token in logs, no secret in the repository.

## Guardrails

- **Never test against the live API with purchase calls.** Use the mock. When you do hit live, use read endpoints and one R2 order to your own number.
- Review every generated retry loop. The most common bug is a retry around the POST.
- Keep the token in the app's secret store. Do not paste it into the assistant.
- Ask for a threat model: what if the queue worker runs twice? What if the response is lost?

## Variations

- Have the assistant write the same integration in a second language to compare, using the [samples](../../simcloud-api/samples) as the contract.
- Generate Postman or Bruno collections from the OpenAPI file for QA.
- Ask it to produce a runbook for support: what each status means and what to do.
