# Freepaid Airtime API 
### Seamless integration & customisable Airtime API

This is an API that enables you to order Vodacom, Cell C, MTN and Telkom Airtime and Data.

![Image of Freepaid](https://i.imgur.com/nfF48Jk.png)


Airtime API (Data and Airtime)
==============================

![Sell MTN, Vodacom, Cell C airtime via an airtime API](https://freepaid.co.za/images/product-pages/sell-airtime-using-the-airtime-api.jpg)

Easily order and receive Vodacom, Cell C, MTN and Telkom Airtime or Data bundles in real time at wholesale prices, from one source.

Freepaid’s API provides seamless, real time access to a wide range of pinned and pinless prepaid products at our transparent, competitive prices. This state-of-the-art programming interface does all the heavy lifting for you. It puts the programming power into your hands, freeing you to put your energy into your own development. Its clean, simple structure cuts down on implementation times and support queries. And once integrated, your application will be supported by unprecedented speed and reliability. Access fee is R99.00 per month plus VAT.

API Overview
------------

You can order PINLESS airtime (direct recharge) or data through this API or you can order a PINNED airtime voucher which is sent to you in the form of a PIN number.

To get started it will be best to create an account on the Development Server with FREEPAID (link below). During registration, we send a ‘user number’ to your Mobile phone via SMS and it will be needed in all future API calls on the Development Server.

Once you have tested your integration you will need to register on the Live FREEPAID website. Once logged in there be sure to go to EDIT MY DETAILS and complete your company information. The information you enter will be used to populate your Tax Invoices (which are also available online).

Then add FREEPAID as a beneficiary on your bank account and deposit funds into the FREEPAID bank account at FNB using only the MOBILE NUMBER that you registered with as the reference number. If you put your Company name or anything else as the reference it will cause a delay since your funds to go to a suspense account and this will have to get rectified manually later.

However, if the reference number is inserted correctly on the EFT then the funds will be allocated to your wallet within seconds of reaching the FREEPAID bank account. This is an automated process and works 24/7. Note that transfers from banks other than FNB can take longer to reach us.

Once the credit is available (we send SMS notification) you can then proceed to order airtime at the wholesale rate via the API. The dealer cost price of each voucher will be deducted from your balance as you transact and the remaining balance in your wallet will be returned with every webservice call.

API Specification
-----------------

We use a SOAP API

The full WSDL is here: [https://ws.freepaid.co.za/airtimeplus/?wsdl](https://ws.freepaid.co.za/airtimeplus/?wsdl)

The full documentation is here [https://ws.freepaid.co.za/airtimeplus/](https://ws.freepaid.co.za/airtimeplus/?wsdl)

### Step 1: Register on the Development server and get Monopoly Money

Before playing with real money it is advisable to set up a play wallet that we can load with Monopoly Money so you can test the API before making your application live.

Register on the Development server at [http://test.freepaid.co.za/home.html](http://test.freepaid.co.za/home.html)

You will receive a OTP (one time pin) via SMS. Save the 7 digit number in that SMS as it will be required in each webservice call when ordering from the Development server. The password (which must also be included in each request) will be the one you entered into the Development website during registration.

Once you have done this, send an email to apisupport@freepaid.co.za with the following subject:
Github | the number you registered with | Sandbox API

We will then allocate monopoly money so you can test your calls on the Development server.

Step 2: Setting up your environment
-----------------------------------

FREEPAID uses PHP, but you're free to use whatever you're comfortable with. We also use a modified PHP NuSOAP library which you can find [here](https://gist.github.com/ErikThiart/b630d2d05290077b19c3b07278e57cfe). It has been modified to make sure it works with PHP 7

On dev use the DEV api endpoint: [http://ws.test.freepaid.co.za/airtimeplus/](http://ws.test.freepaid.co.za/airtimeplus/)

To fetch the balance you will use a call like this:

```php
                require_once( "nusoap.php" );
                  $client = new nusoap_client( "http://ws.test.freepaid.co.za/airtimeplus/" );
                  $err = $client->getError( );
                  if( $err ){
                    print "<p><b>Constructor error: ".$err."</b></p>";
                  }
                  else {
                    $request = array(
                      "user" => "USERXXXX",  # USER number, NOT cell number
                      "pass" => "PASSXXXX",
                    );
                    $result = $client->call( "fetchBalance", array( "request" => $request ) );
                    if( $client->fault ){
                      print "<p><b>Error: <pre>";
                      print_r( $result );
                      print "</pre></b></p>";
                    }
                    else {
                      $err = $client->getError( );
                      if( $err ){
                        print "<p><b>Error: ".$err."</b></p>";
                      }
                      else {
                        print "<pre>";
                        print_r( $result );
                        print "</pre>";
                      }
                    }
                  }
```

Step 3: Getting to understand the process flow.
-----------------------------------------------

The API gives you the ability to order two kinds of vouchers, PINNED and PINLESS. (Note that PINLESS vouchers, by their nature, can not be tested on the Development server)

A PINNED voucher means you can deliver an airtime value by means of a 12 digit PIN which you can deliver electronically or print or send by SMS or whatever.

PINLESS relies on a direct top up of the MSISDN of your customer or client at Network level. In addition data bundles can be delivered as well. This saves the consumer the hassle of converting airtime to a data bundle which is a confusing process for many people.

We prefer pinless for security and other reasons.

Airtime vouchers are available in PINNED or PINLESS format. When you order PINNED vouchers you can only order vouchers that exist on the list of denominations that the Networks have chosen to create.

Below are some common values you may be familiar with...

                CELLC R10.00
                CELLC R25.00
                CELLC R35.00

                MTN R10.00
                MTN R15.00
                MTN R30.00

                VODACOM R10.00
                VODACOM R12.00
                VODACOM R29.00
                

However the PINLESS method for ordering Airtime allows orders from R2.00 all the way to R999.00 so you can order very specific values like Vodacom R2.35 or MTN R111.76.

While data is also PINLESS (it is a direct recharge) it too can only be ordered if it appears on the list of denominations that the Networks has chosen to create.

#### Process Flow: PINNED Vouchers

For PINNED you will first issue a fetchProducts call to get the available product list then you will issue a placeOrder call to place the order, you will receive an order number in the repsonse which you will use in the fetchOrder call. The response (subject to funds being available in your wallet) will be the PIN and serial number of the chosen voucher.

#### Process Flow: PINLESS Vouchers

For PINLESS Airtime or Data you will issue a fetchProducts call to get the product list then you will issue a placeOrder call to place the order. FREEPAID will respond with an order number and you will then use this order number to query the status of the PINLESS recharge using the queryOrder call. This will return ‘Success’ or ‘Failure’.

So in short:

#### PINLESS:

-   Fetch Product List ( PINLESS vouchers will be p-network example p-vodacom)
-   Place PINLESS Order
-   Query PINLESS Order

The steps are

-   Place the order
-   Receive back an order number
-   Use that order number to query the status of the order.

Note: Do not query the status more than once per minute and after five attempts, once per hour. Any failures that we receive from the Network will be adjusted on your account automatically.

For PINNED Airtime vouchers you will use placeOrder to place the order, but then you will use the order number (given in our response) to fetch the actual PINNED order. The response will be a PIN number and the serial number for the voucher, with cost price and remaining balance. (You can also use the order number to re-order old vouchers, for example if you need to do a reprint).

Step 4: Go Live.
----------------

Once you are satisfied with the results on the Development server you can switch to the Live site by changing the API endpoint to https://ws.freepaid.co.za/airtimeplus/ note the "https".

Now register on the Live Server [http://services.freepaid.co.za](http://services.freepaid.co.za/) and use your new live credentials (different 7 digit PIN and (hopefully) a new password) to replace the credentials you had used on the Development server.

Keep the User number for the Live site and the secret password in a safe place.

FAQ
---

#### Does the API work with cents?

Yes, you can only order PINLESS AIRTIME in values like R2.50, R3.20 etc. Please make sure to use a decimal point and NOT a comma. R4.55 is correct. R4,55 is not correct.

#### What is the correct API URL to use?

On the Live Server use [https://ws.freepaid.co.za/airtimeplus/](https://ws.freepaid.co.za/airtimeplus/) note the "https".

On the Development Server use [http://ws.test.freepaid.co.za/airtimeplus/](http://ws.test.freepaid.co.za/airtimeplus/) note the "http" and .test subdomain.

#### What are the error codes for the API?

```php
    define( "airtimeOKAY", "000" );
    define( "airtimePENDING", "001" );
    define( "airtimeEMPTYORDER", "100" );
    define( "airtimeINVALIDUSER", "101" );
    define( "airtimeINVALIDLAST", "102" );
    define( "airtimeINVALIDPASS", "103" );
    define( "airtimeINVALIDNETWORK", "104" );
    define( "airtimeINVALIDSELLVALUE", "105" );
    define( "airtimeFUNDSEXCEEDED", "106" );
    define( "airtimeOUTOFSTOCK", "107" );
    define( "airtimeINVALIDCOUNT", "108" );
    define( "airtimeINVALIDREFNO", "109" );
    define( "airtimeINVALIDREQUEST", "110" );
    define( "airtimeSTILLBUSY", "111" );
    define( "airtimeINVALIDORDERNUMBER", "112" );
    define( "airtimeINVALIDEXTRA", "113" );
    define( "airtimeINTERNAL", "197" );
    define( "airtimeTEMPORARY", "198" );
    define( "airtimeUNKNOWN", "199" );
```                

#### Can I order PINNED Airtime vouchers, PINLESS airtime and data bundles using the same API?

Yes, provided you use the correct calls and values you can do so.

#### What is my USER number and where do I find it?

The USER number is in fact the number associated with your account in our system, which is in turn associated with the mobile number used during registration.

To find the USER number for the Development site login at http://test.freepaid.co.za click on Reports, then SMS log, and find the first SMS we sent you.

The Live USER number is contained in the first SMS which we sent to you during registration on the Live site. If you have already deleted the SMS then login at services.freepaid.co.za, click on Reports, then SMS log, and find the first SMS in the report.

Or call 087 073 6555 during office hours for assistance.

#### Sample Code

Please feel free to send us sample code and snippets, currently only sample code in PHP is available, but it will be good to expand this section to include other languages.

#### fetch balance

```php
      require_once( "nusoap.php" );
      $client = new nusoap_client( "http://ws.test.freepaid.co.za/airtimeplus/" );
      $err = $client->getError( );
      if( $err ){
        print "<p><b>Constructor error: ".$err."</b></p>";
      }
      else {
        $request = array(
          "user" => "USERXXXX",  # USER number, NOT cell number
          "pass" => "PASSXXXX",
        );
        $result = $client->call( "fetchBalance", array( "request" => $request ) );
        if( $client->fault ){
          print "<p><b>Error: <pre>";
          print_r( $result );
          print "</pre></b></p>";
        }
        else {
          $err = $client->getError( );
          if( $err ){
            print "<p><b>Error: ".$err."</b></p>";
          }
          else {
            print "<pre>";
            print_r( $result );
            print "</pre>";
          }
        }
      }
```

#### fetch product list

```php
      require_once( "nusoap.php" );
      $client = new nusoap_client( "http://ws.test.freepaid.co.za/airtimeplus/" );
      $err = $client->getError( );
      if( $err ){
        print "<p><b>Constructor error: ".$err."</b></p>";
      }
      else {
        $request = array(
          "user" => "USERXXXX",  # USER number, NOT cell number
          "pass" => "PASSXXXX",
        );
        $result = $client->call( "fetchProducts", array( "request" => $request ) );
        if( $client->fault ){
          print "<p><b>Error: <pre>";
          print_r( $result );
          print "</pre></b></p>";
        }
        else {
          $err = $client->getError( );
          if( $err ){
            print "<p><b>Error: ".$err."</b></p>";
          }
          else {
            print "<pre>";
            print_r( $result );
            print "</pre>";
          }
        }
      }
```

#### place PINNED order

```php
    require_once( "nusoap.php" );
      $client = new nusoap_client( "http://ws.test.freepaid.co.za/airtimeplus/" );
      $err = $client->getError( );
      if( $err ){
        print "<p><b>Constructor error: ".$err."</b></p>";
      }
      else {
        $request = array(
          "user" => "USERXXXX",  # USER number, NOT cell number
          "pass" => "PASSXXXX",
          "refno" => "TESTXXXX",
          "network" => "vodacom",
          "sellvalue" => "2",
          "count" => "10",
          "extra" => "",
        );
        $result = $client->call( "placeOrder", array( "request" => $request ) );
        if( $client->fault ){
          print "<p><b>Error: <pre>";
          print_r( $result );
          print "</pre></b></p>";
        }
        else {
          $err = $client->getError( );
          if( $err ){
            print "<p><b>Error: ".$err."</b></p>";
          }
          else {
            print "<pre>";
            print_r( $result );
            print "</pre>";
          }
        }
      }
```

#### fetch PINNED order

```php
    require_once( "nusoap.php" );
      $client = new nusoap_client( "http://ws.test.freepaid.co.za/airtimeplus/" );
      $err = $client->getError( );
      if( $err ){
        print "<p><b>Constructor error: ".$err."</b></p>";
      }
      else {
        $request = array(
          "user" => "USERXXXX",  # USER number, NOT cell number
          "pass" => "PASSXXXX",
          "last" => "",  # only works 1st time; use the returned order number for next call
        );
        $result = $client->call( "fetchOrderLatest", array( "request" => $request ) );
        if( $client->fault ){
          print "<p><b>Error: <pre>";
          print_r( $result );
          print "</pre></b></p>";
        }
        else {
          $err = $client->getError( );
          if( $err ){
            print "<p><b>Error: ".$err."</b></p>";
          }
          else {
            print "<pre>";
            print_r( $result );
            print "</pre>";
          }
        }
      }
```

#### place PINLESS order

```php
      require_once( "nusoap.php" );
      $client = new nusoap_client( "http://ws.test.freepaid.co.za/airtimeplus/" );
      $err = $client->getError( );
      if( $err ){
        print "<p><b>Constructor error: ".$err."</b></p>";
      }
      else {
        $request = array(
          "user" => "USERXXXX",  # USER number, NOT cell number
          "pass" => "PASSXXXX",
          "refno" => "TESTXXXX",
          "network" => "p-vodacom",  # PINLESS vodacom
          "sellvalue" => "2",
          "count" => "1",  # ONLY 1 is accepted here for PINLESS
          "extra" => "CELLXXXX",  # CELL number to be recharged
        );
        $result = $client->call( "placeOrder", array( "request" => $request ) );
        if( $client->fault ){
          print "<p><b>Error: <pre>";
          print_r( $result );
          print "</pre></b></p>";
        }
        else {
          $err = $client->getError( );
          if( $err ){
            print "<p><b>Error: ".$err."</b></p>";
          }
          else {
            print "<pre>";
            print_r( $result );
            print "</pre>";
          }
        }
      }
```

#### query PINLESS order

```php
      require_once( "nusoap.php" );
      $client = new nusoap_client( "http://ws.test.freepaid.co.za/airtimeplus/" );
      $err = $client->getError( );
      if( $err ){
        print "<p><b>Constructor error: ".$err."</b></p>";
      }
      else {
        $request = array(
          "user" => "USERXXXX",  # USER number, NOT cell number
          "pass" => "PASSXXXX",
          "orderno" => "ORDERXXX",
        );
        $result = $client->call( "queryOrder", array( "request" => $request ) );
        if( $client->fault ){
          print "<p><b>Error: <pre>";
          print_r( $result );
          print "</pre></b></p>";
        }
        else {
          $err = $client->getError( );
          if( $err ){
            print "<p><b>Error: ".$err."</b></p>";
          }
          else {
            print "<pre>";
            print_r( $result );
            print "</pre>";
          }
        }
      }
```


Follow Us
---------

-   [Twitter](https://twitter.com/freepaidcoza)
-   [Facebook](https://www.facebook.com/Freepaid.co.za/)
-   [LinkedIn](https://www.linkedin.com/company/freepaid/)


 **Office Number:** [087 073 6555](tel:0870736555)

* * * * *

**Office Address:**

104, Building Five, Tygervalley Chambers,
 27 Willie van Schoor Drive,
 Bellville,
 Western Cape

-   2021 © **FREEPAID (PTY) LTD.** All rights reserved Office: 087 073 6555

Menu
----

-   [Home](https://freepaid.co.za/index.php)
-   [Freepaid Login](http://services.freepaid.co.za/home.html)
-   [Blog](https://www.freepaid.co.za/blog/)
-   [About Us](https://freepaid.co.za/about.php)
-   [Airtime API](https://freepaid.co.za/airtime-api.php)
-   [SIM Batch Recharge](https://freepaid.co.za/recharge-simcards.php)
-   [Free Wifi Solutions](https://freepaid.co.za/free-wifi-captive-portal-solutions.php)
-   [Bulk Airtime Printing](https://freepaid.co.za/bulk-airtime.php)
-   [Point Of Sale](https://freepaid.co.za/point-of-sale-airtime.php)
-   [Top Up Now](https://freepaid.co.za/buy-airtime.php)
-   [Start Your Own Business](https://freepaid.co.za/start-your-own-business.php)
-   [Simplified Airtime API](https://freepaid.co.za/simplified-airtime-api.php)
-   [Pinless Airtime](https://freepaid.co.za/pinless-airtime.php)
-   [Contact us](https://freepaid.co.za/contact-airtime-factory.php)
