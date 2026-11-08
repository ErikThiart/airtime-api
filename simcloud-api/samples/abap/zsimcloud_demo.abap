*&---------------------------------------------------------------------*
*& Report  ZSIMCLOUD_DEMO
*& SIMcloud REST API from SAP ABAP (NetWeaver 7.40+), using CL_HTTP_CLIENT and /UI2/CL_JSON.
*&
*& STATUS: written from the OpenAPI contract and the documented JSON shapes, but NOT executed in this
*& repository's test run (no SAP system was available). Treat it as a reviewed starting point and run
*& it against the mock server from a sandbox system first.
*&
*& SETUP
*&   - HTTPS needs the simcloud.co.za certificate chain in STRUST (SSL client, Anonymous).
*&   - Keep the API token in a secure store, not in the report or a selection screen default.
*&   - Purchases: do not retry a failed POST. Query the transaction history first (see the guide).
*&---------------------------------------------------------------------*
REPORT zsimcloud_demo.

PARAMETERS: p_base TYPE string LOWER CASE DEFAULT 'http://127.0.0.1:8081',
            p_tok  TYPE string LOWER CASE DEFAULT 'demo-token',
            p_msis TYPE string LOWER CASE DEFAULT '0821234567',
            p_net  TYPE string LOWER CASE DEFAULT 'vodacom',
            p_amt  TYPE string LOWER CASE DEFAULT '10',
            p_ref  TYPE string LOWER CASE DEFAULT 'Airtime for John'.

TYPES: BEGIN OF ty_airtime_request,
         msisdn    TYPE string,
         network   TYPE string,
         amount    TYPE p LENGTH 8 DECIMALS 2,
         reference TYPE string,
       END OF ty_airtime_request,
       BEGIN OF ty_airtime_response,
         status       TYPE string,
         message      TYPE string,
         request_id   TYPE i,
         queue_status TYPE string,
       END OF ty_airtime_response.

CLASS lcl_simcloud DEFINITION FINAL.
  PUBLIC SECTION.
    CLASS-METHODS request
      IMPORTING method TYPE string path TYPE string body TYPE string OPTIONAL
      EXPORTING http_status TYPE i response TYPE string
      RAISING   cx_static_check.
ENDCLASS.

CLASS lcl_simcloud IMPLEMENTATION.
  METHOD request.
    DATA client TYPE REF TO if_http_client.
    DATA reason TYPE string.

    cl_http_client=>create_by_url( EXPORTING url = |{ p_base }{ path }| IMPORTING client = client ).
    client->request->set_method( method ).
    client->request->set_header_field( name = 'Authorization' value = |Bearer { p_tok }| ).
    client->request->set_header_field( name = 'Accept'        value = 'application/json' ).
    IF body IS NOT INITIAL.
      client->request->set_header_field( name = 'Content-Type' value = 'application/json' ).
      client->request->set_cdata( body ).
    ENDIF.

    client->send( EXCEPTIONS OTHERS = 1 ).
    IF sy-subrc <> 0.
      client->close( ).
      " The request may or may not have reached SIMcloud. Never resend a purchase blindly.
      RAISE EXCEPTION TYPE cx_sy_dyn_call_illegal_method. "replace with your own exception class
    ENDIF.
    client->receive( EXCEPTIONS OTHERS = 1 ).
    IF sy-subrc <> 0.
      client->close( ).
      RAISE EXCEPTION TYPE cx_sy_dyn_call_illegal_method.
    ENDIF.
    client->response->get_status( IMPORTING code = http_status reason = reason ).
    response = client->response->get_cdata( ).
    client->close( ).
  ENDMETHOD.
ENDCLASS.

START-OF-SELECTION.
  DATA: status TYPE i, text TYPE string.
  TRY.
      " --- GET /api/balance.php ---
      lcl_simcloud=>request( EXPORTING method = 'GET' path = '/api/balance.php'
                             IMPORTING http_status = status response = text ).
      WRITE: / 'HTTP', status. WRITE: / text.

      " --- POST /api/airtime.php ---
      DATA(order) = VALUE ty_airtime_request( msisdn = p_msis network = p_net amount = p_amt reference = p_ref ).
      DATA(json)  = /ui2/cl_json=>serialize( data = order compress = abap_false pretty_name = /ui2/cl_json=>pretty_mode-low_case ).
      lcl_simcloud=>request( EXPORTING method = 'POST' path = '/api/airtime.php' body = json
                             IMPORTING http_status = status response = text ).
      WRITE: / 'HTTP', status. WRITE: / text.

      IF status = 201.
        DATA queued TYPE ty_airtime_response.
        /ui2/cl_json=>deserialize( EXPORTING json = text pretty_name = /ui2/cl_json=>pretty_mode-low_case CHANGING data = queued ).
        DO 20 TIMES.
          lcl_simcloud=>request( EXPORTING method = 'GET' path = |/api/airtime.php?request_id={ queued-request_id }|
                                 IMPORTING http_status = status response = text ).
          DATA final TYPE ty_airtime_response.
          /ui2/cl_json=>deserialize( EXPORTING json = text pretty_name = /ui2/cl_json=>pretty_mode-low_case CHANGING data = final ).
          IF status <> 200 OR ( final-status <> 'queued' AND final-status <> 'pending' ).
            EXIT.
          ENDIF.
          WAIT UP TO 3 SECONDS.
        ENDDO.
        WRITE: / 'Final status:', final-status.
      ELSEIF status = 409.
        WRITE: / 'Duplicate order inside the 5-minute window. Do not resend.'.
      ENDIF.
    CATCH cx_static_check INTO DATA(lx).
      WRITE: / 'AMBIGUOUS transport error. Do not retry; check the transaction history first.', lx->get_text( ).
  ENDTRY.
