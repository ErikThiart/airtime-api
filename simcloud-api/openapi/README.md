# SIMcloud OpenAPI contract

[`simcloud-openapi.yaml`](simcloud-openapi.yaml) is a copy of the machine-readable contract SIMcloud publishes at `https://simcloud.co.za/api/openapi.yaml` (OpenAPI 3.0.3). A rendered version is at `https://simcloud.co.za/api/openapi.php`.

[SIMcloud API home](../README.md)

## Use it to

- Generate typed clients (`openapi-generator`, `oapi-codegen`, NSwag, `openapi-typescript`). The contract uses plain JSON over HTTPS, so generators work here, unlike the [Freepaid SOAP API](../../freepaid-api/docs/soap-rpc-encoded.md).
- Import into Postman, Insomnia or Bruno.
- Feed an AI coding assistant, so it does not guess field names.
- Validate requests in contract tests.

## Know its limits

- Response bodies are described only as short text ("SMS queued", "Order not found"), with no response schemas. Use the [endpoint reference](../docs/endpoints.md) for the response fields.
- `GET /api/transactions.php` is documented on the website but is not in this file at the time of writing.
- The file is a snapshot. Compare it with the live copy before you generate code:

```bash
curl -s https://simcloud.co.za/api/openapi.yaml | diff - openapi/simcloud-openapi.yaml && echo "unchanged"
```

## Generate a client (examples)

```bash
# TypeScript types
npx openapi-typescript openapi/simcloud-openapi.yaml -o simcloud.d.ts

# Go
oapi-codegen -package simcloud openapi/simcloud-openapi.yaml > simcloud.gen.go

# Java / Kotlin / C# / Python / many more
openapi-generator-cli generate -i openapi/simcloud-openapi.yaml -g java -o ./simcloud-java
```

These commands are shown for convenience and were not run for this repository.
