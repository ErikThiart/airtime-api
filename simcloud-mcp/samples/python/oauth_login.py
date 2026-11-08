#!/usr/bin/env python3
"""Get an OAuth access token for the SIMcloud MCP server (Authorization Code + PKCE, standard library only).

  python3 oauth_login.py              # opens your browser, you sign in to SIMcloud and approve
  python3 oauth_login.py --self-test  # checks the PKCE maths against the RFC 7636 example, touches no network

What it does, in order:
  1. Reads the discovery documents the server publishes:
       https://simcloud.co.za/.well-known/oauth-protected-resource
       https://simcloud.co.za/.well-known/oauth-authorization-server
  2. Registers a public client with Dynamic Client Registration (RFC 7591) at the registration endpoint.
  3. Opens the authorisation URL with a PKCE S256 challenge and a localhost redirect.
  4. Catches the code on http://127.0.0.1:8976/callback and exchanges it at the token endpoint.
  5. Saves the tokens to ~/.simcloud-mcp-token.json (mode 600) and prints how to use them.

STATUS: written from SIMcloud's published OAuth metadata. It has NOT been run against the live server in
this repository, because running it registers a client and needs a human to sign in. Treat the first run
as a test, and read the token file it writes before you trust it.

Access tokens last 3600 seconds. A refresh token is issued so you can renew without signing in again
(grant_type=refresh_token at the token endpoint).
"""
import base64
import hashlib
import json
import os
import secrets
import sys
import threading
import urllib.parse
import urllib.request
import webbrowser
from http.server import BaseHTTPRequestHandler, HTTPServer

SERVER = os.environ.get("SIMCLOUD_ORIGIN", "https://simcloud.co.za")
RESOURCE = SERVER + "/api/mcp.php"
PORT = 8976
REDIRECT = "http://127.0.0.1:%d/callback" % PORT
TOKEN_FILE = os.path.expanduser("~/.simcloud-mcp-token.json")


def b64url(data):
    return base64.urlsafe_b64encode(data).rstrip(b"=").decode()


def pkce_challenge(verifier):
    return b64url(hashlib.sha256(verifier.encode()).digest())


def get_json(url):
    with urllib.request.urlopen(url, timeout=30) as response:
        return json.load(response)


def post(url, data, as_json):
    body = json.dumps(data).encode() if as_json else urllib.parse.urlencode(data).encode()
    request = urllib.request.Request(url, data=body, method="POST", headers={
        "Content-Type": "application/json" if as_json else "application/x-www-form-urlencoded",
        "Accept": "application/json",
    })
    with urllib.request.urlopen(request, timeout=30) as response:
        return json.load(response)


class Catcher(BaseHTTPRequestHandler):
    result = {}

    def do_GET(self):
        query = urllib.parse.parse_qs(urllib.parse.urlparse(self.path).query)
        Catcher.result = {k: v[0] for k, v in query.items()}
        self.send_response(200)
        self.send_header("Content-Type", "text/plain; charset=utf-8")
        self.end_headers()
        self.wfile.write(b"SIMcloud sign-in finished. You can close this tab.")

    def log_message(self, *args):
        pass


def login():
    resource_meta = get_json(SERVER + "/.well-known/oauth-protected-resource")
    auth_meta = get_json(resource_meta["authorization_servers"][0] + "/.well-known/oauth-authorization-server")
    scope = "api"

    client = post(auth_meta["registration_endpoint"], {
        "client_name": "SIMcloud MCP sample",
        "redirect_uris": [REDIRECT],
        "grant_types": ["authorization_code", "refresh_token"],
        "response_types": ["code"],
        "token_endpoint_auth_method": "none",
        "scope": scope,
    }, as_json=True)

    verifier = b64url(secrets.token_bytes(48))
    state = secrets.token_urlsafe(16)
    url = auth_meta["authorization_endpoint"] + "?" + urllib.parse.urlencode({
        "response_type": "code",
        "client_id": client["client_id"],
        "redirect_uri": REDIRECT,
        "scope": scope,
        "state": state,
        "code_challenge": pkce_challenge(verifier),
        "code_challenge_method": "S256",
        "resource": RESOURCE,
    })

    server = HTTPServer(("127.0.0.1", PORT), Catcher)
    thread = threading.Thread(target=server.handle_request)
    thread.start()
    print("Opening your browser. If it does not open, visit:\n" + url)
    webbrowser.open(url)
    thread.join(timeout=300)
    server.server_close()

    got = Catcher.result
    if got.get("state") != state or "code" not in got:
        sys.exit("Sign-in did not complete: %s" % (got or "no response"))

    token = post(auth_meta["token_endpoint"], {
        "grant_type": "authorization_code",
        "code": got["code"],
        "redirect_uri": REDIRECT,
        "client_id": client["client_id"],
        "code_verifier": verifier,
        "resource": RESOURCE,
    }, as_json=False)

    saved = {"client_id": client["client_id"], "token_endpoint": auth_meta["token_endpoint"], **token}
    fd = os.open(TOKEN_FILE, os.O_WRONLY | os.O_CREAT | os.O_TRUNC, 0o600)
    with os.fdopen(fd, "w") as handle:
        json.dump(saved, handle, indent=2)
    print("Saved to %s (expires_in %s seconds)." % (TOKEN_FILE, token.get("expires_in")))
    print("Use it:  export SIMCLOUD_MCP_URL=%s SIMCLOUD_MCP_TOKEN=$(python3 -c \"import json,os;print(json.load(open(os.path.expanduser('~/.simcloud-mcp-token.json')))['access_token'])\")" % RESOURCE)


def self_test():
    # RFC 7636 appendix B
    verifier = "dBjftJeZ4CVP-mB92K27uhbUJU1p1r_wW1gFWFOEjXk"
    expected = "E9Melhoa2OwvFrEMTJguCHaoeK1t8URWbuGJSstw-cM"
    actual = pkce_challenge(verifier)
    print("PKCE S256:", "ok" if actual == expected else "MISMATCH %s" % actual)
    return 0 if actual == expected else 1


if __name__ == "__main__":
    sys.exit(self_test() if "--self-test" in sys.argv else (login() or 0))
