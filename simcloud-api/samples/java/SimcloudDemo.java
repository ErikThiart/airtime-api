import java.net.URI;
import java.net.URLEncoder;
import java.net.http.HttpClient;
import java.net.http.HttpRequest;
import java.net.http.HttpResponse;
import java.nio.charset.StandardCharsets;
import java.time.Duration;
import java.util.regex.Matcher;
import java.util.regex.Pattern;

/**
 * SIMcloud REST API client for Java 11+ (JDK only).
 *
 *   java SimcloudDemo.java balance
 *   java SimcloudDemo.java network 0821234567
 *   java SimcloudDemo.java data-products mtn
 *   java SimcloudDemo.java sms +27821234567 "Your order has shipped"
 *   java SimcloudDemo.java airtime 0821234567 vodacom 10 "Airtime for John"
 *   java SimcloudDemo.java electricity-check 01234567890
 *   java SimcloudDemo.java electricity 01234567890 150 0821234567 UnitB-2026-11
 *
 * Environment (defaults target the local mock, so nothing spends money):
 *   SIMCLOUD_BASE_URL (live: https://simcloud.co.za), SIMCLOUD_TOKEN, SIMCLOUD_POLL_MS (default 3000)
 *
 * The JDK has no JSON parser, so this file builds JSON by hand and reads two fields with a regex.
 * In a real project use Jackson or Gson (see ../../docs/language-notes.md).
 */
public class SimcloudDemo {
    static final String BASE = env("SIMCLOUD_BASE_URL", "http://127.0.0.1:8081").replaceAll("/$", "");
    static final String TOKEN = env("SIMCLOUD_TOKEN", "demo-token");
    static final long POLL_MS = Long.parseLong(env("SIMCLOUD_POLL_MS", "3000"));
    static final HttpClient HTTP = HttpClient.newBuilder().connectTimeout(Duration.ofSeconds(15)).build();

    record Result(int status, String body) {}

    static String env(String n, String d) {
        String v = System.getenv(n);
        return v == null || v.isEmpty() ? d : v;
    }

    static String enc(String s) {
        return URLEncoder.encode(s, StandardCharsets.UTF_8);
    }

    static String json(String s) {
        return "\"" + s.replace("\\", "\\\\").replace("\"", "\\\"").replace("\n", "\\n") + "\"";
    }

    static Result request(String method, String pathAndQuery, String jsonBody) throws Exception {
        HttpRequest.Builder b = HttpRequest.newBuilder(URI.create(BASE + pathAndQuery))
            .timeout(Duration.ofSeconds(30))
            .header("Authorization", "Bearer " + TOKEN)
            .header("Accept", "application/json");
        if (jsonBody != null) {
            b.header("Content-Type", "application/json").POST(HttpRequest.BodyPublishers.ofString(jsonBody));
        } else {
            b.GET();
        }
        HttpResponse<String> r = HTTP.send(b.build(), HttpResponse.BodyHandlers.ofString());
        return new Result(r.statusCode(), r.body());
    }

    static String field(String body, String name) {
        Matcher m = Pattern.compile("\"" + name + "\"\\s*:\\s*\"?([^\",}\\s]+)").matcher(body);
        return m.find() ? m.group(1) : null;
    }

    static int emit(Result r) {
        System.out.println("HTTP " + r.status());
        System.out.println(r.body());
        return r.status() >= 200 && r.status() < 300 ? 0 : 1;
    }

    static Result waitForAirtime(String requestId) throws Exception {
        Result r = null;
        for (int i = 0; i < 20; i++) {
            r = request("GET", "/api/airtime.php?request_id=" + enc(requestId), null);
            String s = field(r.body(), "status");
            if (r.status() != 200 || (!"queued".equals(s) && !"pending".equals(s))) return r;
            Thread.sleep(POLL_MS);
        }
        return r;
    }

    /** Poll by client_reference until the order leaves pending. Final: success, failed, cancelled. */
    static Result waitForElectricity(String clientReference) throws Exception {
        Result r = null;
        for (int i = 0; i < 20; i++) {
            r = request("GET", "/api/electricity.php?client_reference=" + enc(clientReference), null);
            if (r.status() != 200 || !"pending".equals(field(r.body(), "status"))) return r;
            Thread.sleep(POLL_MS);
        }
        return r;
    }

    public static void main(String[] a) throws Exception {
        if (a.length == 0) {
            System.out.println("Commands: balance | network <msisdn> | data-products [network] | sms <+27...> <text> | airtime <msisdn> <network> <amount> <reference> | electricity-check <meter> | electricity <meter> <amount> <recipient> <client_reference>");
            System.exit(2);
        }
        int code;
        switch (a[0]) {
            case "balance": code = emit(request("GET", "/api/balance.php", null)); break;
            case "network": code = emit(request("GET", "/api/network.php?msisdn=" + enc(a[1]), null)); break;
            case "data-products": code = emit(request("GET", a.length > 1 ? "/api/data.php?network=" + enc(a[1]) : "/api/data.php?products=1", null)); break;
            case "sms": code = emit(request("POST", "/api/sms.php", "{\"recipient\":" + json(a[1]) + ",\"message\":" + json(a[2]) + "}")); break;
            case "airtime":
                try {
                    Result order = request("POST", "/api/airtime.php",
                        "{\"msisdn\":" + json(a[1]) + ",\"network\":" + json(a[2]) + ",\"amount\":" + Double.parseDouble(a[3]) + ",\"reference\":" + json(a[4]) + "}");
                    if (order.status() == 201) {
                        emit(order);
                        code = emit(waitForAirtime(field(order.body(), "request_id")));
                    } else {
                        code = emit(order);
                    }
                } catch (java.io.IOException e) {
                    // The request may or may not have reached SIMcloud. Never resend blindly.
                    System.out.println("AMBIGUOUS: " + e + ". Do not retry. Check GET /api/transactions.php for reference \"" + a[4] + "\" first.");
                    code = 3;
                }
                break;
            case "electricity-check": code = emit(request("GET", "/api/electricity.php?meter_number=" + enc(a[1]), null)); break;
            case "electricity":
                if (Double.parseDouble(a[2]) != Math.floor(Double.parseDouble(a[2]))) {
                    System.out.println("Amount must be whole rand (R55 to R1000).");
                    code = 2;
                    break;
                }
                try {
                    Result order = request("POST", "/api/electricity.php",
                        "{\"meter_number\":" + json(a[1]) + ",\"amount\":" + (long) Double.parseDouble(a[2]) + ",\"client_reference\":" + json(a[4]) + ",\"recipient\":" + json(a[3]) + "}");
                    if (order.status() == 201 || order.status() == 202) { // 202 = reconciliation pending: keep polling, never rebuy
                        emit(order);
                        code = emit(waitForElectricity(a[4]));
                    } else {
                        code = emit(order);
                    }
                } catch (java.io.IOException e) {
                    System.out.println("AMBIGUOUS: " + e + ". Do not retry or use a new reference. Poll client_reference \"" + a[4] + "\".");
                    code = 3;
                }
                break;
            default: System.out.println("Unknown command"); code = 2;
        }
        System.exit(code);
    }
}
