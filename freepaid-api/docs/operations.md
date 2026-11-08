# Operations reference

Every field, type and rule below comes from the live WSDL ([`wsdl/airtimeplus.wsdl`](../wsdl/airtimeplus.wsdl)) and Freepaid's published documentation.

[Freepaid API home](../README.md)

**Contents:** [Common fields](#common-fields) · [fetchBalance](#fetchbalance) · [fetchProducts](#fetchproducts) · [placeOrder](#placeorder) · [queryOrder](#queryorder) · [fetchOrder](#fetchorder) · [fetchOrderLatest](#fetchorderlatest) · [Sample envelope](#sample-envelope)

## Common fields

**Every request** carries these two fields:

| Field | Type | Rule |
|---|---|---|
| `user` | int | Your user number (digits only, not your cell number) |
| `pass` | string | Your password |

**Every reply** carries these four fields:

| Field | Type | Meaning |
|---|---|---|
| `status` | int | `1` success, `0` failure |
| `errorcode` | string | Secondary code explaining a failure. See [error codes](error-codes.md) |
| `message` | string | Extended status text. For humans and logs only: **do not parse it** |
| `balance` | float | Your balance after the call, when the request got that far |

The SOAP action for each call is `https://ws.freepaid.co.za:443/airtimeplus/<operation>` (quoted in the `SOAPAction` header).

## fetchBalance

Your current wallet balance. Reads only.

| Request field | Type | Notes |
|---|---|---|
| `user`, `pass` | | |

Reply: the four common fields. `balance` is the figure you want.

## fetchProducts

The catalogue you can order.

| Request field | Type | Notes |
|---|---|---|
| `user`, `pass` | | |

Reply adds `products`, an array of:

| Field | Type | Notes |
|---|---|---|
| `description` | string | Display name |
| `network` | string | The code to send in `placeOrder` (for example `vodacom`, `p-vodacom`) |
| `sellvalue` | float | Face value |
| `costprice` | float | Your cost. **`0` means "not known", not "free"** |
| `groupname` | string | Product group |

Call this before `placeOrder` to learn the valid `network` and `sellvalue` pairs. Data bundles and PINNED vouchers only exist at the denominations the networks have created.

## placeOrder

Buys airtime or data. **This spends money.**

| Request field | Type | Rule |
|---|---|---|
| `refno` | string | Your reference for the request. Freepaid says it **should be unique but does not enforce uniqueness**, so you must prevent duplicates yourself |
| `network` | string | Required. PINLESS codes start with `p-` (`p-vodacom`). PINNED codes are plain (`vodacom`) |
| `sellvalue` | float | Face value. PINLESS airtime accepts R2.00 to R999.00 in cents. Use a **decimal point**, never a comma: `4.55` is right, `4,55` is wrong |
| `count` | int | Number of vouchers. **PINLESS must be `1`** |
| `extra` | string | Required for PINLESS: the cell number to top up. Empty for PINNED |

Reply adds:

| Field | Type | Notes |
|---|---|---|
| `orderno` | string | Freepaid's unique order number. Keep it: you need it for `queryOrder` or `fetchOrder` |

`balance` in the reply is your balance **after** the request, whether or not it succeeded.

What `status` means here:

- PINNED: `status 1` means the order was placed. Call `fetchOrder` for the PINs.
- PINLESS: `status 1` means the order was **accepted**, not necessarily delivered. Freepaid is explicit: "Pinless orders must use the queryOrder call for proper status." Poll `queryOrder`.

## queryOrder

Status of a PINLESS order.

| Request field | Type | Rule |
|---|---|---|
| `orderno` | string | Digits only, from `placeOrder` |

Reply adds `orderno` and `costprice` (what the order cost you).

Outcome: Freepaid's guide says the call "will return 'Success' or 'Failure'". The WSDL does not list a code per outcome. This repository's samples read `status 1` as success, `errorcode 111` as still busy, and any other `status 0` as failed. Confirm the exact codes with Freepaid.

Polling rule from Freepaid: **do not query more than once per minute, and after five attempts, once per hour.** Failures reported by the network are adjusted on your account automatically.

## fetchOrder

Returns the vouchers for a PINNED order. Can be called again to reprint an old voucher.

| Request field | Type | Rule |
|---|---|---|
| `orderno` | string | Digits only, from `placeOrder` |

Reply adds `orderno` and `vouchers`, an array of:

| Field | Type | Notes |
|---|---|---|
| `network` | string | |
| `sellvalue` | float | |
| `pin` | string | The airtime PIN (12 digits). **Treat as a secret** (see [security](security-and-operations.md)) |
| `serial` | string | Voucher serial number |
| `costprice` | float | |

## fetchOrderLatest

Same reply as `fetchOrder`, but you pass the last order number you already fetched and receive the next one. Use it to collect PINNED orders in sequence.

| Request field | Type | Rule |
|---|---|---|
| `last` | string | Digits only. Empty on the first call (the sample in Freepaid's guide notes it "only works 1st time"); then pass the order number returned by the previous call |

## Sample envelope

This is the exact request the samples in this repository send for `placeOrder` (PINLESS, R10 Vodacom). Line breaks added for reading.

```xml
<?xml version="1.0" encoding="UTF-8"?>
<SOAP-ENV:Envelope
    xmlns:SOAP-ENV="http://schemas.xmlsoap.org/soap/envelope/"
    xmlns:ns1="https://ws.freepaid.co.za:443/airtimeplus/"
    xmlns:xsd="http://www.w3.org/2001/XMLSchema"
    xmlns:xsi="http://www.w3.org/2001/XMLSchema-instance"
    xmlns:SOAP-ENC="http://schemas.xmlsoap.org/soap/encoding/"
    SOAP-ENV:encodingStyle="http://schemas.xmlsoap.org/soap/encoding/">
  <SOAP-ENV:Body>
    <ns1:placeOrder>
      <request xsi:type="ns1:placeOrderIn">
        <user xsi:type="xsd:int">1234567</user>
        <pass xsi:type="xsd:string">your-password</pass>
        <refno xsi:type="xsd:string">INV-10045</refno>
        <network xsi:type="xsd:string">p-vodacom</network>
        <sellvalue xsi:type="xsd:float">10.00</sellvalue>
        <count xsi:type="xsd:int">1</count>
        <extra xsi:type="xsd:string">0821234567</extra>
      </request>
    </ns1:placeOrder>
  </SOAP-ENV:Body>
</SOAP-ENV:Envelope>
```

Headers: `Content-Type: text/xml; charset=utf-8` and `SOAPAction: "https://ws.freepaid.co.za:443/airtimeplus/placeOrder"`.

A reply looks like this (the server identifies itself as NuSOAP):

```xml
<SOAP-ENV:Envelope ...><SOAP-ENV:Body>
  <ns1:placeOrderResponse xmlns:ns1="https://ws.freepaid.co.za:443/airtimeplus/">
    <reply xsi:type="tns:placeOrderOut">
      <status xsi:type="xsd:int">1</status>
      <errorcode xsi:type="xsd:string">000</errorcode>
      <message xsi:type="xsd:string">...</message>
      <balance xsi:type="xsd:float">490.00</balance>
      <orderno xsi:type="xsd:string">7000001</orderno>
    </reply>
  </ns1:placeOrderResponse>
</SOAP-ENV:Body></SOAP-ENV:Envelope>
```

The envelope shape was checked against the live service with a `fetchBalance` call that used a deliberately invalid password. The service parsed it and replied `status 0`, `errorcode 103`, `authentication failed`.
