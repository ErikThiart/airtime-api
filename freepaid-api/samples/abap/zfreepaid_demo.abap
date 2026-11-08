*&---------------------------------------------------------------------*
*& Report  ZFREEPAID_DEMO
*& Freepaid Airtime API from SAP ABAP (NetWeaver 7.40+), using CL_HTTP_CLIENT.
*&
*& STATUS: written against the WSDL and the same envelope the tested samples send, but NOT executed
*& in this repository's test run (no SAP system was available). Treat it as a reviewed starting point
*& and run it against the mock server from a sandbox system first.
*&
*& SETUP
*&   - HTTPS needs the Freepaid server certificate chain in STRUST (SSL client, Anonymous).
*&   - Outbound access to ws.freepaid.co.za:443 must be allowed from the application server.
*&   - Keep the password in a secure store (for example SSF or a Secure Store), not in the report.
*&---------------------------------------------------------------------*
REPORT zfreepaid_demo.

PARAMETERS: p_url  TYPE string LOWER CASE DEFAULT 'http://127.0.0.1:8080/',
            p_user TYPE string LOWER CASE DEFAULT '1000001',
            p_pass TYPE string LOWER CASE DEFAULT 'demo-password',
            p_net  TYPE string LOWER CASE DEFAULT 'p-vodacom',
            p_val  TYPE string LOWER CASE DEFAULT '10.00',
            p_cell TYPE string LOWER CASE DEFAULT '0821234567'.

CONSTANTS c_ns TYPE string VALUE 'https://ws.freepaid.co.za:443/airtimeplus/'.

CLASS lcl_freepaid DEFINITION FINAL.
  PUBLIC SECTION.
    CLASS-METHODS field IMPORTING name TYPE string type TYPE string value TYPE string
                        RETURNING VALUE(xml) TYPE string.
    CLASS-METHODS call  IMPORTING op TYPE string fields TYPE string
                        RETURNING VALUE(response) TYPE string
                        RAISING   cx_static_check.
    CLASS-METHODS tag   IMPORTING xml TYPE string tag TYPE string
                        RETURNING VALUE(value) TYPE string.
ENDCLASS.

CLASS lcl_freepaid IMPLEMENTATION.

  METHOD field.
    DATA(escaped) = value.
    REPLACE ALL OCCURRENCES OF '&' IN escaped WITH '&amp;'.
    REPLACE ALL OCCURRENCES OF '<' IN escaped WITH '&lt;'.
    REPLACE ALL OCCURRENCES OF '>' IN escaped WITH '&gt;'.
    xml = |<{ name } xsi:type="xsd:{ type }">{ escaped }</{ name }>|.
  ENDMETHOD.

  METHOD call.
    DATA client TYPE REF TO if_http_client.

    DATA(body) = |<?xml version="1.0" encoding="UTF-8"?>| &&
      |<SOAP-ENV:Envelope xmlns:SOAP-ENV="http://schemas.xmlsoap.org/soap/envelope/" xmlns:ns1="{ c_ns }" | &&
      |xmlns:xsd="http://www.w3.org/2001/XMLSchema" xmlns:xsi="http://www.w3.org/2001/XMLSchema-instance" | &&
      |xmlns:SOAP-ENC="http://schemas.xmlsoap.org/soap/encoding/" | &&
      |SOAP-ENV:encodingStyle="http://schemas.xmlsoap.org/soap/encoding/"><SOAP-ENV:Body>| &&
      |<ns1:{ op }><request xsi:type="ns1:{ op }In">{ fields }</request></ns1:{ op }>| &&
      |</SOAP-ENV:Body></SOAP-ENV:Envelope>|.

    cl_http_client=>create_by_url( EXPORTING url = p_url IMPORTING client = client ).
    client->request->set_method( if_http_request=>co_request_method_post ).
    client->request->set_header_field( name = 'Content-Type' value = 'text/xml; charset=utf-8' ).
    client->request->set_header_field( name = 'SOAPAction'   value = |"{ c_ns }{ op }"| ).
    client->request->set_cdata( body ).

    client->send( EXCEPTIONS OTHERS = 1 ).
    IF sy-subrc <> 0.
      client->close( ).
      RAISE EXCEPTION TYPE cx_sy_dyn_call_illegal_method. "replace with your own exception class
    ENDIF.
    client->receive( EXCEPTIONS OTHERS = 1 ).
    IF sy-subrc <> 0.
      client->close( ).
      RAISE EXCEPTION TYPE cx_sy_dyn_call_illegal_method.
    ENDIF.
    response = client->response->get_cdata( ).
    client->close( ).
  ENDMETHOD.

  METHOD tag.
    " The reply schema is flat and fixed, so a regular expression is enough for status, errorcode,
    " message, balance and orderno. Use CL_IXML for the vouchers and products arrays.
    FIND REGEX |<{ tag }[^>]*>([^<]*)</{ tag }>| IN xml SUBMATCHES value.
  ENDMETHOD.

ENDCLASS.

START-OF-SELECTION.
  TRY.
      DATA(creds) = lcl_freepaid=>field( name = 'user' type = 'int' value = p_user )
                 && lcl_freepaid=>field( name = 'pass' type = 'string' value = p_pass ).

      DATA(balance_xml) = lcl_freepaid=>call( op = 'fetchBalance' fields = creds ).
      WRITE: / 'status    ', lcl_freepaid=>tag( xml = balance_xml tag = 'status' ),
             / 'errorcode ', lcl_freepaid=>tag( xml = balance_xml tag = 'errorcode' ),
             / 'balance   ', lcl_freepaid=>tag( xml = balance_xml tag = 'balance' ).

      DATA(order_xml) = lcl_freepaid=>call(
        op     = 'placeOrder'
        fields = creds
              && lcl_freepaid=>field( name = 'refno'     type = 'string' value = |abap-{ sy-datum }{ sy-uzeit }| )
              && lcl_freepaid=>field( name = 'network'   type = 'string' value = p_net )
              && lcl_freepaid=>field( name = 'sellvalue' type = 'float'  value = p_val )
              && lcl_freepaid=>field( name = 'count'     type = 'int'    value = `1` )
              && lcl_freepaid=>field( name = 'extra'     type = 'string' value = p_cell ) ).
      WRITE: / 'status    ', lcl_freepaid=>tag( xml = order_xml tag = 'status' ),
             / 'errorcode ', lcl_freepaid=>tag( xml = order_xml tag = 'errorcode' ),
             / 'orderno   ', lcl_freepaid=>tag( xml = order_xml tag = 'orderno' ).
    CATCH cx_static_check INTO DATA(lx).
      WRITE: / 'HTTP error:', lx->get_text( ).
  ENDTRY.
