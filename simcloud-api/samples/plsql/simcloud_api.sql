-- SIMcloud REST API from Oracle PL/SQL (Oracle 12.2+ for JSON_OBJECT_T), using UTL_HTTP.
--
-- STATUS: written from the OpenAPI contract and the documented JSON shapes, but NOT executed in this
-- repository's test run (no Oracle database was available). Treat it as a reviewed starting point and
-- run it against the mock server (see ../../mock-server) from a test schema first.
--
-- One-time DBA setup (HTTPS to simcloud.co.za needs a network ACL and a wallet that trusts the certificate):
--   BEGIN
--     DBMS_NETWORK_ACL_ADMIN.APPEND_HOST_ACE(
--       host => 'simcloud.co.za', lower_port => 443, upper_port => 443,
--       ace  => XS$ACE_TYPE(privilege_list => XS$NAME_LIST('http'), principal_name => 'APP_USER', principal_type => XS_ACL.PTYPE_DB));
--   END;
--   /
--   UTL_HTTP.SET_WALLET('file:/u01/app/oracle/wallet', NULL);   -- call in the session before the request
--
-- Never store the API token in source. Read it from a secure table or vault and pass it in.

CREATE OR REPLACE PACKAGE simcloud_api AS
  -- Result of one call. http_status is the HTTP code; body is the parsed JSON.
  TYPE t_result IS RECORD (http_status PLS_INTEGER, body JSON_OBJECT_T);

  FUNCTION request (p_base IN VARCHAR2, p_token IN VARCHAR2, p_method IN VARCHAR2,
                    p_path IN VARCHAR2, p_json IN CLOB DEFAULT NULL) RETURN t_result;

  FUNCTION balance (p_base IN VARCHAR2, p_token IN VARCHAR2) RETURN NUMBER;

  FUNCTION send_sms (p_base IN VARCHAR2, p_token IN VARCHAR2, p_recipient IN VARCHAR2, p_message IN VARCHAR2) RETURN VARCHAR2;

  -- Queues an airtime order and returns request_id. Raises -20409 for the 5-minute duplicate rule (HTTP 409).
  -- If this raises a UTL_HTTP error the outcome is AMBIGUOUS: do not retry, check the transaction history first.
  FUNCTION create_airtime (p_base IN VARCHAR2, p_token IN VARCHAR2, p_msisdn IN VARCHAR2,
                           p_network IN VARCHAR2, p_amount IN NUMBER, p_reference IN VARCHAR2) RETURN NUMBER;

  -- Polls until the order is no longer queued/pending. Returns 'delivered', 'failed' or 'pending' (gave up).
  FUNCTION wait_for_airtime (p_base IN VARCHAR2, p_token IN VARCHAR2, p_request_id IN NUMBER,
                             p_attempts IN PLS_INTEGER DEFAULT 20, p_delay_s IN NUMBER DEFAULT 3) RETURN VARCHAR2;

  -- Prepaid electricity. Returns the meter check status: success, unsupported or unknown.
  FUNCTION check_electricity_meter (p_base IN VARCHAR2, p_token IN VARCHAR2, p_meter IN VARCHAR2) RETURN VARCHAR2;

  -- Places an order (whole rand, R55 to R1000; p_client_reference must be unique per purchase).
  -- Returns the order_id. HTTP 202 reconciliation_pending is NOT an error: poll, never buy again.
  FUNCTION create_electricity (p_base IN VARCHAR2, p_token IN VARCHAR2, p_meter IN VARCHAR2, p_amount IN PLS_INTEGER,
                               p_recipient IN VARCHAR2, p_client_reference IN VARCHAR2) RETURN NUMBER;

  -- Polls by client_reference. Returns success, failed, cancelled, or pending (gave up).
  FUNCTION wait_for_electricity (p_base IN VARCHAR2, p_token IN VARCHAR2, p_client_reference IN VARCHAR2,
                                 p_attempts IN PLS_INTEGER DEFAULT 20, p_delay_s IN NUMBER DEFAULT 3) RETURN VARCHAR2;
END simcloud_api;
/

CREATE OR REPLACE PACKAGE BODY simcloud_api AS

  FUNCTION request (p_base IN VARCHAR2, p_token IN VARCHAR2, p_method IN VARCHAR2,
                    p_path IN VARCHAR2, p_json IN CLOB DEFAULT NULL) RETURN t_result IS
    l_req   UTL_HTTP.req;
    l_resp  UTL_HTTP.resp;
    l_chunk VARCHAR2(32767);
    l_text  CLOB;
    l_out   t_result;
  BEGIN
    UTL_HTTP.set_transfer_timeout(30);
    l_req := UTL_HTTP.begin_request(RTRIM(p_base, '/') || p_path, p_method, 'HTTP/1.1');
    UTL_HTTP.set_header(l_req, 'Authorization', 'Bearer ' || p_token);
    UTL_HTTP.set_header(l_req, 'Accept', 'application/json');
    IF p_json IS NOT NULL THEN
      UTL_HTTP.set_header(l_req, 'Content-Type', 'application/json');
      UTL_HTTP.set_header(l_req, 'Content-Length', LENGTHB(p_json));
      UTL_HTTP.write_text(l_req, p_json);
    END IF;

    l_resp := UTL_HTTP.get_response(l_req);          -- 4xx/5xx do NOT raise when http_response_errors is off (default)
    l_out.http_status := l_resp.status_code;
    DBMS_LOB.createtemporary(l_text, TRUE);
    BEGIN
      LOOP
        UTL_HTTP.read_text(l_resp, l_chunk, 32000);
        DBMS_LOB.writeappend(l_text, LENGTH(l_chunk), l_chunk);
      END LOOP;
    EXCEPTION WHEN UTL_HTTP.end_of_body THEN NULL;
    END;
    UTL_HTTP.end_response(l_resp);

    BEGIN
      l_out.body := JSON_OBJECT_T.parse(NVL(l_text, '{}'));
    EXCEPTION WHEN OTHERS THEN
      l_out.body := JSON_OBJECT_T('{"status":"error"}');
      l_out.body.put('message', SUBSTR(l_text, 1, 200));
    END;
    RETURN l_out;
  END request;

  FUNCTION balance (p_base IN VARCHAR2, p_token IN VARCHAR2) RETURN NUMBER IS
    l_r t_result := request(p_base, p_token, 'GET', '/api/balance.php');
  BEGIN
    IF l_r.http_status <> 200 THEN
      RAISE_APPLICATION_ERROR(-20000 - 1, 'SIMcloud HTTP ' || l_r.http_status || ': ' || l_r.body.get_string('message'));
    END IF;
    RETURN l_r.body.get_number('balance');
  END balance;

  FUNCTION send_sms (p_base IN VARCHAR2, p_token IN VARCHAR2, p_recipient IN VARCHAR2, p_message IN VARCHAR2) RETURN VARCHAR2 IS
    l_body JSON_OBJECT_T := JSON_OBJECT_T();
    l_r    t_result;
  BEGIN
    l_body.put('recipient', p_recipient);
    l_body.put('message', p_message);
    l_r := request(p_base, p_token, 'POST', '/api/sms.php', l_body.to_clob());
    IF l_r.http_status <> 200 THEN
      RAISE_APPLICATION_ERROR(-20001, 'SIMcloud HTTP ' || l_r.http_status || ': ' || l_r.body.get_string('message'));
    END IF;
    RETURN l_r.body.get_string('sms_id');
  END send_sms;

  FUNCTION create_airtime (p_base IN VARCHAR2, p_token IN VARCHAR2, p_msisdn IN VARCHAR2,
                           p_network IN VARCHAR2, p_amount IN NUMBER, p_reference IN VARCHAR2) RETURN NUMBER IS
    l_body JSON_OBJECT_T := JSON_OBJECT_T();
    l_r    t_result;
  BEGIN
    l_body.put('msisdn', p_msisdn);
    l_body.put('network', p_network);
    l_body.put('amount', p_amount);
    l_body.put('reference', p_reference);
    l_r := request(p_base, p_token, 'POST', '/api/airtime.php', l_body.to_clob());
    IF l_r.http_status = 409 THEN
      RAISE_APPLICATION_ERROR(-20409, 'Duplicate airtime order within 5 minutes: ' || l_r.body.get_string('message'));
    ELSIF l_r.http_status <> 201 THEN
      RAISE_APPLICATION_ERROR(-20002, 'SIMcloud HTTP ' || l_r.http_status || ': ' || l_r.body.get_string('message'));
    END IF;
    RETURN l_r.body.get_number('request_id');
  END create_airtime;

  FUNCTION wait_for_airtime (p_base IN VARCHAR2, p_token IN VARCHAR2, p_request_id IN NUMBER,
                             p_attempts IN PLS_INTEGER DEFAULT 20, p_delay_s IN NUMBER DEFAULT 3) RETURN VARCHAR2 IS
    l_r      t_result;
    l_status VARCHAR2(30);
  BEGIN
    FOR i IN 1 .. p_attempts LOOP
      l_r := request(p_base, p_token, 'GET', '/api/airtime.php?request_id=' || p_request_id);
      l_status := l_r.body.get_string('status');
      IF l_r.http_status <> 200 OR l_status NOT IN ('queued', 'pending') THEN
        RETURN l_status;
      END IF;
      DBMS_SESSION.sleep(p_delay_s);                 -- Oracle 18c+. On older versions use DBMS_LOCK.sleep.
    END LOOP;
    RETURN 'pending';
  END wait_for_airtime;

  FUNCTION check_electricity_meter (p_base IN VARCHAR2, p_token IN VARCHAR2, p_meter IN VARCHAR2) RETURN VARCHAR2 IS
    l_r t_result := request(p_base, p_token, 'GET', '/api/electricity.php?meter_number=' || UTL_URL.escape(p_meter, TRUE));
  BEGIN
    IF l_r.http_status <> 200 THEN
      RAISE_APPLICATION_ERROR(-20003, 'SIMcloud HTTP ' || l_r.http_status || ': ' || l_r.body.get_string('message'));
    END IF;
    RETURN l_r.body.get_string('status');
  END check_electricity_meter;

  FUNCTION create_electricity (p_base IN VARCHAR2, p_token IN VARCHAR2, p_meter IN VARCHAR2, p_amount IN PLS_INTEGER,
                               p_recipient IN VARCHAR2, p_client_reference IN VARCHAR2) RETURN NUMBER IS
    l_body JSON_OBJECT_T := JSON_OBJECT_T();
    l_r    t_result;
  BEGIN
    l_body.put('meter_number', p_meter);
    l_body.put('amount', p_amount);
    l_body.put('client_reference', p_client_reference);
    l_body.put('recipient', p_recipient);
    l_r := request(p_base, p_token, 'POST', '/api/electricity.php', l_body.to_clob());
    IF l_r.http_status NOT IN (201, 202) THEN
      RAISE_APPLICATION_ERROR(-20004, 'SIMcloud HTTP ' || l_r.http_status || ': ' || l_r.body.get_string('message'));
    END IF;
    RETURN l_r.body.get_number('order_id');   -- may be NULL on 202: poll by client_reference
  END create_electricity;

  FUNCTION wait_for_electricity (p_base IN VARCHAR2, p_token IN VARCHAR2, p_client_reference IN VARCHAR2,
                                 p_attempts IN PLS_INTEGER DEFAULT 20, p_delay_s IN NUMBER DEFAULT 3) RETURN VARCHAR2 IS
    l_r      t_result;
    l_status VARCHAR2(30);
  BEGIN
    FOR i IN 1 .. p_attempts LOOP
      l_r := request(p_base, p_token, 'GET', '/api/electricity.php?client_reference=' || UTL_URL.escape(p_client_reference, TRUE));
      l_status := l_r.body.get_string('status');
      IF l_r.http_status <> 200 OR l_status <> 'pending' THEN
        RETURN l_status;
      END IF;
      DBMS_SESSION.sleep(p_delay_s);
    END LOOP;
    RETURN 'pending';
  END wait_for_electricity;

END simcloud_api;
/

-- Example (anonymous block):
-- SET SERVEROUTPUT ON
-- DECLARE
--   l_id NUMBER;
-- BEGIN
--   DBMS_OUTPUT.PUT_LINE('balance = ' || simcloud_api.balance('http://mock-host:8081', 'demo-token'));
--   l_id := simcloud_api.create_airtime('http://mock-host:8081', 'demo-token', '0821234567', 'vodacom', 10, 'Airtime for John');
--   DBMS_OUTPUT.PUT_LINE('final status = ' || simcloud_api.wait_for_airtime('http://mock-host:8081', 'demo-token', l_id, 20, 1));
-- END;
-- /
