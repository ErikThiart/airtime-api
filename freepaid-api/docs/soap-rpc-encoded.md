# Why this API needs a hand-built SOAP envelope

If you are on Java, .NET or any stack that normally generates a client from a WSDL, read this first.

[Freepaid API home](../README.md)

## The short version

The Freepaid WSDL declares `style="rpc"` and `use="encoded"` (SOAP section 5 encoding). Most modern SOAP toolkits dropped support for that combination years ago, because the WS-I Basic Profile forbids it. Generated clients either refuse the WSDL, produce a client that sends the wrong XML, or fail at runtime.

The reliable fix is small: post the XML yourself over HTTPS and read the reply with your normal XML parser. Every sample in this repository does that, in under 150 lines.

You can see the declaration in the WSDL:

```xml
<soap:binding style="rpc" transport="http://schemas.xmlsoap.org/soap/http"/>
...
<soap:body use="encoded" namespace="https://ws.freepaid.co.za:443/airtimeplus/"
           encodingStyle="http://schemas.xmlsoap.org/soap/encoding/"/>
```

## What the toolkits do

Based on each toolkit's documented behaviour. Check your exact version before you rely on this table.

| Toolkit | RPC/encoded |
|---|---|
| Java JAX-WS / `wsimport`, Apache CXF | Not supported. Use `HttpClient` and an XML parser |
| .NET WCF / `svcutil` / "Add Service Reference" | Not supported. Use `HttpClient` and `XDocument` |
| .NET Framework "Add Web Reference" (ASMX proxy) | Can consume encoded services, but it is legacy tooling |
| PHP `SoapClient` | Works. Generates the same envelope as the samples (checked for this repository) |
| PHP NuSOAP | Works. It is what Freepaid itself uses |
| Python `zeep` | Does not support encoded. Use `urllib`/`requests` and `ElementTree` |
| Python `suds` family | Supports encoded, but the original is unmaintained |
| Node.js `soap` package | Limited. Use `fetch` and a string template |
| Go | No generator. Use `net/http` and `encoding/xml` |
| Oracle PL/SQL, SAP ABAP | Use `UTL_HTTP` / `CL_HTTP_CLIENT` with a string envelope |

## Anatomy of a request

```xml
<SOAP-ENV:Envelope  ...namespaces...  SOAP-ENV:encodingStyle="http://schemas.xmlsoap.org/soap/encoding/">
  <SOAP-ENV:Body>
    <ns1:fetchBalance>                              <!-- operation name, in the service namespace -->
      <request xsi:type="ns1:fetchBalanceIn">       <!-- the single "request" part, typed -->
        <user xsi:type="xsd:int">1234567</user>     <!-- every field carries its XSD type -->
        <pass xsi:type="xsd:string">secret</pass>
      </request>
    </ns1:fetchBalance>
  </SOAP-ENV:Body>
</SOAP-ENV:Envelope>
```

Rules the samples follow:

1. **Namespace:** `https://ws.freepaid.co.za:443/airtimeplus/` for `ns1`. The `:443` is part of the namespace string, even when you connect over plain HTTP to a mock.
2. **Operation element:** `ns1:<operation>`, with one child `request` of type `ns1:<operation>In`.
3. **Typed fields:** every field has `xsi:type="xsd:int"`, `xsd:string` or `xsd:float`. Types per field are in the [operations reference](operations.md).
4. **Headers:** `Content-Type: text/xml; charset=utf-8` and `SOAPAction: "https://ws.freepaid.co.za:443/airtimeplus/<operation>"` (quoted).
5. **Escape values.** A password containing `&`, `<` or `>` must be XML-escaped. Every sample does this, and the test scenario checks it.
6. **Floats:** send `10.00`, with a decimal point, never a comma or a locale-formatted number. Format with an invariant culture. A German or South African locale in .NET or Java can produce `10,00` and the call will fail.

## Reading the reply

The reply root is `<Envelope><Body><opResponse><reply>`. Take the `reply` element and read its children by **local name** (ignore namespace prefixes). Arrays (`products`, `vouchers`) are `<item>` children:

```xml
<reply xsi:type="tns:fetchProductsOut">
  <status xsi:type="xsd:int">1</status> ... 
  <products xsi:type="SOAP-ENC:Array" SOAP-ENC:arrayType="tns:product[2]">
    <item xsi:type="tns:product"> <description>...</description> <network>...</network> ... </item>
    <item ...> ... </item>
  </products>
</reply>
```

Notes for strict environments:

- The server declares `encoding="ISO-8859-1"` in the reply. Let your XML parser read the declaration. Do not force UTF-8 on the bytes.
- Disable DTDs and external entities in your parser. The Java sample shows the flag. A SOAP reply never needs them.
- Treat an HTTP 200 with a SOAP `Fault` as a failure. The samples throw if no `<reply>` element is present.

## Do I still need the WSDL?

No for running the samples. Keep [`wsdl/airtimeplus.wsdl`](../wsdl/airtimeplus.wsdl) as the field reference and for contract tests. Fetch it again from `https://ws.freepaid.co.za/airtimeplus/?wsdl` to confirm nothing changed before a release.
