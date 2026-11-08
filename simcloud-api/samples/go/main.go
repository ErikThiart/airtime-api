// SIMcloud REST API client for Go 1.18+ (standard library only).
//
//	go run . balance
//	go run . network 0821234567
//	go run . data-products mtn
//	go run . sms +27821234567 "Your order has shipped"
//	go run . airtime 0821234567 vodacom 10 "Airtime for John"
//
// Environment (defaults target the local mock, so nothing spends money):
// SIMCLOUD_BASE_URL (live: https://simcloud.co.za), SIMCLOUD_TOKEN, SIMCLOUD_POLL_MS (default 3000)
package main

import (
	"bytes"
	"encoding/json"
	"fmt"
	"io"
	"net/http"
	"net/url"
	"os"
	"strconv"
	"strings"
	"time"
)

func env(name, fallback string) string {
	if v := os.Getenv(name); v != "" {
		return v
	}
	return fallback
}

var (
	base   = strings.TrimRight(env("SIMCLOUD_BASE_URL", "http://127.0.0.1:8081"), "/")
	token  = env("SIMCLOUD_TOKEN", "demo-token")
	client = &http.Client{Timeout: 30 * time.Second}
)

type result struct {
	Status int
	Body   map[string]any
	Raw    []byte
}

// request returns 4xx/5xx as a result. Only transport failures come back as an error.
func request(method, path string, query url.Values, body any) (*result, error) {
	u := base + path
	if len(query) > 0 {
		u += "?" + query.Encode()
	}
	var reader io.Reader
	if body != nil {
		b, _ := json.Marshal(body)
		reader = bytes.NewReader(b)
	}
	req, err := http.NewRequest(method, u, reader)
	if err != nil {
		return nil, err
	}
	req.Header.Set("Authorization", "Bearer "+token)
	req.Header.Set("Accept", "application/json")
	if body != nil {
		req.Header.Set("Content-Type", "application/json")
	}
	resp, err := client.Do(req)
	if err != nil {
		return nil, err
	}
	defer resp.Body.Close()
	raw, _ := io.ReadAll(resp.Body)
	r := &result{Status: resp.StatusCode, Raw: raw}
	if err := json.Unmarshal(raw, &r.Body); err != nil {
		r.Body = map[string]any{"status": "error", "message": string(raw[:min(len(raw), 200)])}
	}
	return r, nil
}

func min(a, b int) int {
	if a < b {
		return a
	}
	return b
}

func emit(r *result) int {
	pretty, _ := json.MarshalIndent(r.Body, "", "  ")
	fmt.Println("HTTP", r.Status)
	fmt.Println(string(pretty))
	if r.Status >= 200 && r.Status < 300 {
		return 0
	}
	return 1
}

func waitForAirtime(requestID string) (*result, error) {
	poll, _ := strconv.Atoi(env("SIMCLOUD_POLL_MS", "3000"))
	var r *result
	for i := 0; i < 20; i++ {
		var err error
		r, err = request("GET", "/api/airtime.php", url.Values{"request_id": {requestID}}, nil)
		if err != nil {
			return nil, err
		}
		status, _ := r.Body["status"].(string)
		if r.Status != 200 || (status != "queued" && status != "pending") {
			return r, nil
		}
		time.Sleep(time.Duration(poll) * time.Millisecond)
	}
	return r, nil
}

func main() {
	a := os.Args[1:]
	usage := func() {
		fmt.Println("Commands: balance | network <msisdn> | data-products [network] | sms <+27...> <text> | airtime <msisdn> <network> <amount> <reference>")
		os.Exit(2)
	}
	if len(a) == 0 {
		usage()
	}
	arg := func(i int) string {
		if i >= len(a) {
			usage()
		}
		return a[i]
	}
	var r *result
	var err error
	switch a[0] {
	case "balance":
		r, err = request("GET", "/api/balance.php", nil, nil)
	case "network":
		r, err = request("GET", "/api/network.php", url.Values{"msisdn": {arg(1)}}, nil)
	case "data-products":
		q := url.Values{"products": {"1"}}
		if len(a) > 1 {
			q = url.Values{"network": {a[1]}}
		}
		r, err = request("GET", "/api/data.php", q, nil)
	case "sms":
		r, err = request("POST", "/api/sms.php", nil, map[string]any{"recipient": arg(1), "message": arg(2)})
	case "airtime":
		amount, perr := strconv.ParseFloat(arg(3), 64)
		if perr != nil {
			usage()
		}
		r, err = request("POST", "/api/airtime.php", nil, map[string]any{"msisdn": arg(1), "network": arg(2), "amount": amount, "reference": arg(4)})
		if err != nil {
			// The request may or may not have reached SIMcloud. Never resend blindly.
			fmt.Printf("AMBIGUOUS: %v. Do not retry. Check GET /api/transactions.php for reference %q first.\n", err, a[4])
			os.Exit(3)
		}
		if r.Status == 201 {
			emit(r)
			id := fmt.Sprintf("%.0f", r.Body["request_id"])
			r, err = waitForAirtime(id)
		}
	default:
		usage()
	}
	if err != nil {
		fmt.Fprintln(os.Stderr, "error:", err)
		os.Exit(1)
	}
	os.Exit(emit(r))
}
