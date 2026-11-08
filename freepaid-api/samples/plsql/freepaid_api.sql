-- Freepaid Airtime API from Oracle PL/SQL (Oracle 12c+), using UTL_HTTP and XMLTYPE.
--
-- STATUS: written against the WSDL and the same envelope the tested samples send, but NOT executed
-- in this repository's test run (no Oracle database was available). Treat it as a reviewed starting
-- point and run it against the mock server (see ../../mock-server) from a test schema first.
--
-- One-time DBA setup (replace APP_USER; the host list must include your endpoint):
--   BEGIN
--     DBMS_NETWORK_ACL_ADMIN.APPEND_HOST_ACE(
--       host => 'ws.freepaid.co.za', lower_port => 443, upper_port => 443,
--       ace  => XS$ACE_TYPE(privilege_list => XS$NAME_LIST('http'), principal_name => 'APP_USER', principal_type => XS_ACL.PTYPE_DB));
--   END;
--   /
-- HTTPS also needs an Oracle wallet that trusts the server certificate:
--   UTL_HTTP.SET_WALLET('file:/u01/app/oracle/wallet', NULL);   -- call before the request
--
-- Credentials: keep them in a table or secret store, not in source. This package takes them as arguments.

CREATE OR REPLACE PACKAGE freepaid_api AS
  c_ns CONSTANT VARCHAR2(100) := 'https://ws.freepaid.co.za:443/airtimeplus/';

  -- Returns the <reply> element of any operation as XMLTYPE.
  FUNCTION call_op (p_endpoint IN VARCHAR2, p_op IN VARCHAR2, p_fields IN VARCHAR2) RETURN XMLTYPE;

  FUNCTION field (p_name IN VARCHAR2, p_type IN VARCHAR2, p_value IN VARCHAR2) RETURN VARCHAR2;

  -- fetchBalance. Raises -20001 if the service reports status 0.
  FUNCTION fetch_balance (p_endpoint IN VARCHAR2, p_user IN NUMBER, p_pass IN VARCHAR2) RETURN NUMBER;

  -- placeOrder. Returns the order number. Pinless: p_network 'p-vodacom', p_count 1, p_extra = cell number.
  FUNCTION place_order (p_endpoint IN VARCHAR2, p_user IN NUMBER, p_pass IN VARCHAR2,
                        p_refno IN VARCHAR2, p_network IN VARCHAR2, p_value IN NUMBER,
                        p_count IN NUMBER DEFAULT 1, p_extra IN VARCHAR2 DEFAULT NULL) RETURN VARCHAR2;
END freepaid_api;
/

CREATE OR REPLACE PACKAGE BODY freepaid_api AS

  FUNCTION esc (p IN VARCHAR2) RETURN VARCHAR2 IS
  BEGIN
    RETURN REPLACE(REPLACE(REPLACE(p, '&', '&amp;'), '<', '&lt;'), '>', '&gt;');
  END esc;

  FUNCTION field (p_name IN VARCHAR2, p_type IN VARCHAR2, p_value IN VARCHAR2) RETURN VARCHAR2 IS
  BEGIN
    RETURN '<' || p_name || ' xsi:type="xsd:' || p_type || '">' || esc(p_value) || '</' || p_name || '>';
  END field;

  FUNCTION call_op (p_endpoint IN VARCHAR2, p_op IN VARCHAR2, p_fields IN VARCHAR2) RETURN XMLTYPE IS
    l_body  CLOB;
    l_req   UTL_HTTP.req;
    l_resp  UTL_HTTP.resp;
    l_chunk VARCHAR2(32767);
    l_xml   CLOB;
  BEGIN
    l_body := '<?xml version="1.0" encoding="UTF-8"?>'
      || '<SOAP-ENV:Envelope xmlns:SOAP-ENV="http://schemas.xmlsoap.org/soap/envelope/" xmlns:ns1="' || c_ns || '" '
      || 'xmlns:xsd="http://www.w3.org/2001/XMLSchema" xmlns:xsi="http://www.w3.org/2001/XMLSchema-instance" '
      || 'xmlns:SOAP-ENC="http://schemas.xmlsoap.org/soap/encoding/" '
      || 'SOAP-ENV:encodingStyle="http://schemas.xmlsoap.org/soap/encoding/"><SOAP-ENV:Body>'
      || '<ns1:' || p_op || '><request xsi:type="ns1:' || p_op || 'In">' || p_fields || '</request></ns1:' || p_op || '>'
      || '</SOAP-ENV:Body></SOAP-ENV:Envelope>';

    UTL_HTTP.set_transfer_timeout(30);
    l_req := UTL_HTTP.begin_request(p_endpoint, 'POST', 'HTTP/1.1');
    UTL_HTTP.set_header(l_req, 'Content-Type', 'text/xml; charset=utf-8');
    UTL_HTTP.set_header(l_req, 'SOAPAction', '"' || c_ns || p_op || '"');
    UTL_HTTP.set_header(l_req, 'Content-Length', LENGTHB(l_body));
    UTL_HTTP.write_text(l_req, l_body);

    l_resp := UTL_HTTP.get_response(l_req);
    DBMS_LOB.createtemporary(l_xml, TRUE);
    BEGIN
      LOOP
        UTL_HTTP.read_text(l_resp, l_chunk, 32000);
        DBMS_LOB.writeappend(l_xml, LENGTH(l_chunk), l_chunk);
      END LOOP;
    EXCEPTION
      WHEN UTL_HTTP.end_of_body THEN NULL;
    END;
    UTL_HTTP.end_response(l_resp);

    -- The server declares ISO-8859-1; strip the declaration so XMLTYPE parses the text we already decoded.
    l_xml := REGEXP_REPLACE(l_xml, '^<\?xml[^>]*\?>', '');
    RETURN XMLTYPE(l_xml).extract('//*[local-name()="reply"]');
  END call_op;

  FUNCTION val (p_reply IN XMLTYPE, p_tag IN VARCHAR2) RETURN VARCHAR2 IS
    l_node XMLTYPE := p_reply.extract('//*[local-name()="' || p_tag || '"]/text()');
  BEGIN
    RETURN CASE WHEN l_node IS NULL THEN NULL ELSE l_node.getStringVal() END;
  END val;

  PROCEDURE assert_ok (p_reply IN XMLTYPE) IS
  BEGIN
    IF val(p_reply, 'status') <> '1' THEN
      RAISE_APPLICATION_ERROR(-20001, 'Freepaid error ' || val(p_reply, 'errorcode') || ': ' || val(p_reply, 'message'));
    END IF;
  END assert_ok;

  FUNCTION fetch_balance (p_endpoint IN VARCHAR2, p_user IN NUMBER, p_pass IN VARCHAR2) RETURN NUMBER IS
    l_reply XMLTYPE;
  BEGIN
    l_reply := call_op(p_endpoint, 'fetchBalance', field('user', 'int', TO_CHAR(p_user)) || field('pass', 'string', p_pass));
    assert_ok(l_reply);
    RETURN TO_NUMBER(val(l_reply, 'balance'), '9999999990.99', 'NLS_NUMERIC_CHARACTERS=''.,''');
  END fetch_balance;

  FUNCTION place_order (p_endpoint IN VARCHAR2, p_user IN NUMBER, p_pass IN VARCHAR2,
                        p_refno IN VARCHAR2, p_network IN VARCHAR2, p_value IN NUMBER,
                        p_count IN NUMBER DEFAULT 1, p_extra IN VARCHAR2 DEFAULT NULL) RETURN VARCHAR2 IS
    l_reply XMLTYPE;
  BEGIN
    l_reply := call_op(p_endpoint, 'placeOrder',
         field('user', 'int', TO_CHAR(p_user)) || field('pass', 'string', p_pass)
      || field('refno', 'string', p_refno) || field('network', 'string', p_network)
      || field('sellvalue', 'float', TO_CHAR(p_value, 'FM9999990.00', 'NLS_NUMERIC_CHARACTERS=''.,'''))
      || field('count', 'int', TO_CHAR(p_count)) || field('extra', 'string', NVL(p_extra, '')));
    assert_ok(l_reply);
    RETURN val(l_reply, 'orderno');
  END place_order;

END freepaid_api;
/

-- Example (anonymous block). Against the local mock use an endpoint your DB host can reach.
-- SET SERVEROUTPUT ON
-- DECLARE
--   l_order VARCHAR2(50);
-- BEGIN
--   DBMS_OUTPUT.PUT_LINE('balance = ' || freepaid_api.fetch_balance('http://mock-host:8080/', 1000001, 'demo-password'));
--   l_order := freepaid_api.place_order('http://mock-host:8080/', 1000001, 'demo-password', 'plsql-001', 'p-vodacom', 10, 1, '0821234567');
--   DBMS_OUTPUT.PUT_LINE('orderno = ' || l_order);
-- END;
-- /
