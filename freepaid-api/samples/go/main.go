// Freepaid Airtime API client for Go 1.18+ (standard library only).
//
//	go run . balance
//	go run . products
//	go run . order-pinless p-vodacom 10 0821234567
//	go run . query 7000001
//	go run . order-pinned vodacom 29 1
//	go run . fetch 7000002
//
// Environment (defaults target the local mock, so nothing spends money):
// FREEPAID_ENDPOINT, FREEPAID_USER, FREEPAID_PASS
package main

import (
	"bytes"
	"encoding/xml"
	"fmt"
	"html"
	"io"
	"net/http"
	"os"
	"strconv"
	"strings"
	"time"
)

const ns = "https://ws.freepaid.co.za:443/airtimeplus/"

func env(name, fallback string) string {
	if v := os.Getenv(name); v != "" {
		return v
	}
	return fallback
}

var (
	endpoint = env("FREEPAID_ENDPOINT", "http://127.0.0.1:8080/")
	user     = env("FREEPAID_USER", "1000001")
	pass     = env("FREEPAID_PASS", "demo-password")
)

type field struct{ name, xsdType, value string }

// envelope builds an RPC/encoded SOAP 1.1 request, as the WSDL requires.
func envelope(op string, fields []field) string {
	var b strings.Builder
	for _, f := range fields {
		fmt.Fprintf(&b, `<%s xsi:type="xsd:%s">%s</%s>`, f.name, f.xsdType, html.EscapeString(f.value), f.name)
	}
	return `<?xml version="1.0" encoding="UTF-8"?>` +
		`<SOAP-ENV:Envelope xmlns:SOAP-ENV="http://schemas.xmlsoap.org/soap/envelope/" xmlns:ns1="` + ns + `" ` +
		`xmlns:xsd="http://www.w3.org/2001/XMLSchema" xmlns:xsi="http://www.w3.org/2001/XMLSchema-instance" ` +
		`xmlns:SOAP-ENC="http://schemas.xmlsoap.org/soap/encoding/" ` +
		`SOAP-ENV:encodingStyle="http://schemas.xmlsoap.org/soap/encoding/"><SOAP-ENV:Body>` +
		`<ns1:` + op + `><request xsi:type="ns1:` + op + `In">` + b.String() + `</request></ns1:` + op + `>` +
		`</SOAP-ENV:Body></SOAP-ENV:Envelope>`
}

// Reply holds every field the service can return. Absent fields stay empty.
type Item struct {
	Fields []struct {
		XMLName xml.Name
		Value   string `xml:",chardata"`
	} `xml:",any"`
}

type Reply struct {
	Status    string `xml:"status"`
	ErrorCode string `xml:"errorcode"`
	Message   string `xml:"message"`
	Balance   string `xml:"balance"`
	OrderNo   string `xml:"orderno"`
	CostPrice string `xml:"costprice"`
	Vouchers  struct {
		Items []Item `xml:"item"`
	} `xml:"vouchers"`
	Products struct {
		Items []Item `xml:"item"`
	} `xml:"products"`
}

type envelopeOut struct {
	Reply Reply `xml:"Body>anyResponse>reply"`
}

func call(op string, extra ...field) (*Reply, error) {
	fields := append([]field{{"user", "int", user}, {"pass", "string", pass}}, extra...)
	req, err := http.NewRequest("POST", endpoint, bytes.NewBufferString(envelope(op, fields)))
	if err != nil {
		return nil, err
	}
	req.Header.Set("Content-Type", "text/xml; charset=utf-8")
	req.Header.Set("SOAPAction", `"`+ns+op+`"`)
	resp, err := (&http.Client{Timeout: 30 * time.Second}).Do(req)
	if err != nil {
		return nil, err
	}
	defer resp.Body.Close()
	body, _ := io.ReadAll(resp.Body)

	// The response root is <Envelope><Body><opResponse><reply>. Go's xml package cannot wildcard
	// the middle element, so decode Body generically and then re-decode the <reply> element.
	var env struct {
		Body struct {
			Inner struct {
				Reply Reply `xml:"reply"`
			} `xml:",any"`
		} `xml:"Body"`
	}
	dec := xml.NewDecoder(bytes.NewReader(body))
	dec.CharsetReader = func(label string, input io.Reader) (io.Reader, error) { return input, nil } // ISO-8859-1 is ASCII-safe here
	if err := dec.Decode(&env); err != nil {
		return nil, fmt.Errorf("bad response (HTTP %d): %w", resp.StatusCode, err)
	}
	return &env.Body.Inner.Reply, nil
}

func (r *Reply) ok() bool { return strings.TrimSpace(r.Status) == "1" }

func show(r *Reply) {
	fmt.Printf("%-10s %s\n%-10s %s\n%-10s %s\n%-10s %s\n", "status", r.Status, "errorcode", r.ErrorCode, "message", r.Message, "balance", r.Balance)
	if r.OrderNo != "" {
		fmt.Printf("%-10s %s\n", "orderno", r.OrderNo)
	}
	if r.CostPrice != "" {
		fmt.Printf("%-10s %s\n", "costprice", r.CostPrice)
	}
	for name, items := range map[string][]Item{"vouchers": r.Vouchers.Items, "products": r.Products.Items} {
		if len(items) == 0 {
			continue
		}
		fmt.Printf("%-10s %d\n", name, len(items))
		for _, it := range items {
			parts := []string{}
			for _, f := range it.Fields {
				parts = append(parts, f.XMLName.Local+"="+f.Value)
			}
			fmt.Println("           " + strings.Join(parts, " "))
		}
	}
	fmt.Printf("%-10s %v\n", "ok", r.ok())
}

func placeOrder(network, value, count, extra string) (*Reply, error) {
	v, err := strconv.ParseFloat(value, 64)
	if err != nil {
		return nil, err
	}
	return call("placeOrder",
		field{"refno", "string", fmt.Sprintf("go-%d", time.Now().UnixNano())},
		field{"network", "string", network},
		field{"sellvalue", "float", fmt.Sprintf("%.2f", v)},
		field{"count", "int", count},
		field{"extra", "string", extra})
}

func main() {
	args := os.Args[1:]
	usage := func() {
		fmt.Println("Commands: balance | products | order-pinless <network> <value> <cell> | query <orderno> | order-pinned <network> <value> [count] | fetch <orderno>")
		os.Exit(2)
	}
	if len(args) == 0 {
		usage()
	}
	arg := func(i int) string {
		if i >= len(args) {
			usage()
		}
		return args[i]
	}
	var r *Reply
	var err error
	switch args[0] {
	case "balance":
		r, err = call("fetchBalance")
	case "products":
		r, err = call("fetchProducts")
	case "order-pinless":
		r, err = placeOrder(arg(1), arg(2), "1", arg(3))
	case "query":
		r, err = call("queryOrder", field{"orderno", "string", arg(1)})
	case "order-pinned":
		count := "1"
		if len(args) > 3 {
			count = args[3]
		}
		r, err = placeOrder(arg(1), arg(2), count, "")
	case "fetch":
		r, err = call("fetchOrder", field{"orderno", "string", arg(1)})
	default:
		usage()
	}
	if err != nil {
		fmt.Fprintln(os.Stderr, "error:", err)
		os.Exit(1)
	}
	show(r)
	if !r.ok() {
		os.Exit(1)
	}
}
