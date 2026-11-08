import java.io.ByteArrayInputStream;
import java.net.URI;
import java.net.http.HttpClient;
import java.net.http.HttpRequest;
import java.net.http.HttpResponse;
import java.nio.charset.StandardCharsets;
import java.time.Duration;
import java.util.ArrayList;
import java.util.LinkedHashMap;
import java.util.List;
import java.util.Map;
import javax.xml.parsers.DocumentBuilderFactory;
import org.w3c.dom.Document;
import org.w3c.dom.Element;
import org.w3c.dom.Node;
import org.w3c.dom.NodeList;

/**
 * Freepaid Airtime API client for Java 11+ (JDK only, no dependencies).
 *
 * Run (single-file source launch, Java 11+):
 *   java FreepaidDemo.java balance
 *   java FreepaidDemo.java products
 *   java FreepaidDemo.java order-pinless p-vodacom 10 0821234567
 *   java FreepaidDemo.java query 7000001
 *   java FreepaidDemo.java order-pinned vodacom 29 1
 *   java FreepaidDemo.java fetch 7000002
 *
 * Environment (defaults target the local mock, so nothing spends money):
 *   FREEPAID_ENDPOINT, FREEPAID_USER, FREEPAID_PASS
 *
 * Why not JAX-WS / wsimport? The WSDL is RPC/encoded, which JAX-WS does not support.
 * Building the envelope by hand is shorter and works everywhere.
 */
public class FreepaidDemo {
    static final String NS = "https://ws.freepaid.co.za:443/airtimeplus/";
    static final String ENDPOINT = env("FREEPAID_ENDPOINT", "http://127.0.0.1:8080/");
    static final String USER = env("FREEPAID_USER", "1000001");
    static final String PASS = env("FREEPAID_PASS", "demo-password");
    static final HttpClient HTTP = HttpClient.newBuilder().connectTimeout(Duration.ofSeconds(15)).build();

    static String env(String name, String fallback) {
        String v = System.getenv(name);
        return v == null || v.isEmpty() ? fallback : v;
    }

    static String xml(String s) {
        return s.replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;");
    }

    /** fields: {name, xsdType, value} triples. RPC/encoded SOAP 1.1. */
    static String envelope(String op, List<String[]> fields) {
        StringBuilder b = new StringBuilder();
        for (String[] f : fields) {
            b.append('<').append(f[0]).append(" xsi:type=\"xsd:").append(f[1]).append("\">")
             .append(xml(f[2])).append("</").append(f[0]).append('>');
        }
        return "<?xml version=\"1.0\" encoding=\"UTF-8\"?>"
            + "<SOAP-ENV:Envelope xmlns:SOAP-ENV=\"http://schemas.xmlsoap.org/soap/envelope/\" xmlns:ns1=\"" + NS + "\""
            + " xmlns:xsd=\"http://www.w3.org/2001/XMLSchema\" xmlns:xsi=\"http://www.w3.org/2001/XMLSchema-instance\""
            + " xmlns:SOAP-ENC=\"http://schemas.xmlsoap.org/soap/encoding/\""
            + " SOAP-ENV:encodingStyle=\"http://schemas.xmlsoap.org/soap/encoding/\"><SOAP-ENV:Body>"
            + "<ns1:" + op + "><request xsi:type=\"ns1:" + op + "In\">" + b + "</request></ns1:" + op + ">"
            + "</SOAP-ENV:Body></SOAP-ENV:Envelope>";
    }

    static String local(Node n) {
        String name = n.getNodeName();
        return name.substring(name.indexOf(':') + 1);
    }

    static Map<String, Object> call(String op, String[]... extra) throws Exception {
        List<String[]> fields = new ArrayList<>();
        fields.add(new String[] {"user", "int", USER});
        fields.add(new String[] {"pass", "string", PASS});
        for (String[] f : extra) fields.add(f);

        HttpRequest request = HttpRequest.newBuilder(URI.create(ENDPOINT))
            .timeout(Duration.ofSeconds(30))
            .header("Content-Type", "text/xml; charset=utf-8")
            .header("SOAPAction", "\"" + NS + op + "\"")
            .POST(HttpRequest.BodyPublishers.ofString(envelope(op, fields), StandardCharsets.UTF_8))
            .build();
        HttpResponse<byte[]> response = HTTP.send(request, HttpResponse.BodyHandlers.ofByteArray());

        DocumentBuilderFactory dbf = DocumentBuilderFactory.newInstance();
        dbf.setNamespaceAware(false);
        dbf.setFeature("http://apache.org/xml/features/disallow-doctype-decl", true); // no XXE
        Document doc = dbf.newDocumentBuilder().parse(new ByteArrayInputStream(response.body()));

        Element reply = null;
        NodeList all = doc.getElementsByTagName("*");
        for (int i = 0; i < all.getLength(); i++) {
            if (local(all.item(i)).equals("reply")) { reply = (Element) all.item(i); break; }
        }
        if (reply == null) throw new IllegalStateException("No <reply> in response (HTTP " + response.statusCode() + ")");

        Map<String, Object> result = new LinkedHashMap<>();
        for (Node c = reply.getFirstChild(); c != null; c = c.getNextSibling()) {
            if (c.getNodeType() != Node.ELEMENT_NODE) continue;
            String name = local(c);
            if (name.equals("vouchers") || name.equals("products")) {
                List<Map<String, String>> items = new ArrayList<>();
                for (Node it = c.getFirstChild(); it != null; it = it.getNextSibling()) {
                    if (it.getNodeType() != Node.ELEMENT_NODE) continue;
                    Map<String, String> row = new LinkedHashMap<>();
                    for (Node f = it.getFirstChild(); f != null; f = f.getNextSibling()) {
                        if (f.getNodeType() == Node.ELEMENT_NODE) row.put(local(f), f.getTextContent());
                    }
                    items.add(row);
                }
                result.put(name, items);
            } else {
                result.put(name, c.getTextContent());
            }
        }
        result.put("ok", "1".equals(result.get("status")));
        return result;
    }

    static Map<String, Object> placeOrder(String network, String value, String count, String extra) throws Exception {
        return call("placeOrder",
            new String[] {"refno", "string", "java-" + System.nanoTime()},
            new String[] {"network", "string", network},
            new String[] {"sellvalue", "float", String.format(java.util.Locale.ROOT, "%.2f", Double.parseDouble(value))},
            new String[] {"count", "int", count},
            new String[] {"extra", "string", extra});
    }

    @SuppressWarnings("unchecked")
    static void show(Map<String, Object> result) {
        for (Map.Entry<String, Object> e : result.entrySet()) {
            if (e.getValue() instanceof List) {
                List<Map<String, String>> items = (List<Map<String, String>>) e.getValue();
                System.out.printf("%-10s %d%n", e.getKey(), items.size());
                for (Map<String, String> row : items) {
                    StringBuilder line = new StringBuilder("          ");
                    row.forEach((k, v) -> line.append(' ').append(k).append('=').append(v));
                    System.out.println(line);
                }
            } else {
                System.out.printf("%-10s %s%n", e.getKey(), e.getValue());
            }
        }
    }

    public static void main(String[] args) throws Exception {
        if (args.length == 0) {
            System.out.println("Commands: balance | products | order-pinless <network> <value> <cell> | query <orderno> | order-pinned <network> <value> [count] | fetch <orderno>");
            System.exit(2);
        }
        Map<String, Object> result;
        switch (args[0]) {
            case "balance": result = call("fetchBalance"); break;
            case "products": result = call("fetchProducts"); break;
            case "order-pinless": result = placeOrder(args[1], args[2], "1", args[3]); break;
            case "query": result = call("queryOrder", new String[] {"orderno", "string", args[1]}); break;
            case "order-pinned": result = placeOrder(args[1], args[2], args.length > 3 ? args[3] : "1", ""); break;
            case "fetch": result = call("fetchOrder", new String[] {"orderno", "string", args[1]}); break;
            default: System.out.println("Unknown command " + args[0]); System.exit(2); return;
        }
        show(result);
        System.exit((Boolean) result.get("ok") ? 0 : 1);
    }
}
