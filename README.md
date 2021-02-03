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

Our Products
------------

||Network|Description|Type|Group Name|Face Value|Cost Price|
|:--|:------|:----------|:---|:---------|:---------|:---------|
|1|BRANSON|Virgin Mobile|Pinned Voucher|Airtime Voucher|R10.00|R9.15|
|2|BRANSON|Virgin Mobile|Pinned Voucher|Airtime Voucher|R30.00|R27.75|
|3|BRANSON|Virgin Mobile|Pinned Voucher|Airtime Voucher|R50.00|R45.75|
|4|BRANSON|Virgin Mobile|Pinned Voucher|Airtime Voucher|R100.00|R92.50|
|5|BRANSON|Virgin Mobile|Pinned Voucher|Airtime Voucher|R250.00|R231.25|
|6|CELLC|Cell C|Pinned Voucher|Airtime Voucher|R5.00|R4.81|
|7|CELLC|Cell C|Pinned Voucher|Airtime Voucher|R10.00|R9.60|
|8|CELLC|Cell C|Pinned Voucher|Airtime Voucher|R25.00|R24.01|
|9|CELLC|Cell C|Pinned Voucher|Airtime Voucher|R35.00|R33.61|
|10|CELLC|Cell C|Pinned Voucher|Airtime Voucher|R39.00|R37.64|
|11|CELLC|Cell C|Pinned Voucher|Airtime Voucher|R49.00|R47.29|
|12|CELLC|Cell C|Pinned Voucher|Airtime Voucher|R50.00|R48.00|
|13|CELLC|Cell C|Pinned Voucher|Airtime Voucher|R70.00|R67.20|
|14|CELLC|Cell C|Pinned Voucher|Airtime Voucher|R89.00|R85.90|
|15|CELLC|Cell C|Pinned Voucher|Airtime Voucher|R100.00|R96.00|
|16|CELLC|Cell C|Pinned Voucher|Airtime Voucher|R150.00|R145.50|
|17|CELLC|Cell C|Pinned Voucher|Airtime Voucher|R199.00|R194.04|
|18|CELLC|Cell C|Pinned Voucher|Airtime Voucher|R200.00|R194.00|
|19|CELLC|Cell C|Pinned Voucher|Airtime Voucher|R300.00|R291.00|
|20|CELLC|Cell C|Pinned Voucher|Airtime Voucher|R500.00|R485.00|
|21|ESKOM|Eskom|Pinned Voucher|Airtime Voucher|R20.00|R19.50|
|22|ESKOM|Eskom|Pinned Voucher|Airtime Voucher|R50.00|R48.75|
|23|ESKOM|Eskom|Pinned Voucher|Airtime Voucher|R100.00|R97.50|
|24|ESKOM|Eskom|Pinned Voucher|Airtime Voucher|R200.00|R195.00|
|25|ESKOM|Eskom|Pinned Voucher|Airtime Voucher|R500.00|R487.50|
|26|HEITA|8.ta|Pinned Voucher|Airtime Voucher|R5.00|R4.78|
|27|HEITA|8.ta|Pinned Voucher|Airtime Voucher|R10.00|R9.55|
|28|HEITA|8.ta|Pinned Voucher|Airtime Voucher|R20.00|R19.10|
|29|HEITA|8.ta|Pinned Voucher|Airtime Voucher|R30.00|R28.65|
|30|HEITA|8.ta|Pinned Voucher|Airtime Voucher|R50.00|R47.75|
|31|HEITA|8.ta|Pinned Voucher|Airtime Voucher|R100.00|R95.50|
|32|HEITA|8.ta|Pinned Voucher|Airtime Voucher|R250.00|R238.75|
|33|MTN|MTN|Pinned Voucher|Airtime Voucher|R2.00|R1.92|
|34|MTN|MTN|Pinned Voucher|Airtime Voucher|R5.00|R4.83|
|35|MTN|MTN|Pinned Voucher|Airtime Voucher|R10.00|R9.65|
|36|MTN|MTN|Pinned Voucher|Airtime Voucher|R15.00|R14.48|
|37|MTN|MTN|Pinned Voucher|Airtime Voucher|R30.00|R28.95|
|38|MTN|MTN|Pinned Voucher|Airtime Voucher|R60.00|R57.90|
|39|MTN|MTN|Pinned Voucher|Airtime Voucher|R180.00|R172.80|
|40|VODACOM|Vodacom|Pinned Voucher|Airtime Voucher|R2.00|R1.93|
|41|VODACOM|Vodacom|Pinned Voucher|Airtime Voucher|R5.00|R4.84|
|42|VODACOM|Vodacom|Pinned Voucher|Airtime Voucher|R10.00|R9.67|
|43|VODACOM|Vodacom|Pinned Voucher|Airtime Voucher|R12.00|R11.60|
|44|VODACOM|Vodacom|Pinned Voucher|Airtime Voucher|R29.00|R28.05|
|45|VODACOM|Vodacom|Pinned Voucher|Airtime Voucher|R49.00|R47.39|
|46|VODACOM|Vodacom|Pinned Voucher|Airtime Voucher|R55.00|R53.19|
|47|VODACOM|Vodacom|Pinned Voucher|Airtime Voucher|R110.00|R106.37|
|48|VODACOM|Vodacom|Pinned Voucher|Airtime Voucher|R275.00|R265.93|
|49|VODACOM|Vodacom|Pinned Voucher|Airtime Voucher|R1100.00|R951.50|
|50|WORLDCALL|WorldCall|Pinned Voucher|Airtime Voucher|R10.00|R9.70|
|51|WORLDCALL|WorldCall|Pinned Voucher|Airtime Voucher|R50.00|R48.50|
|52|WORLDCALL|WorldCall|Pinned Voucher|Airtime Voucher|R100.00|R97.00|
|53|WORLDCALL|WorldCall|Pinned Voucher|Airtime Voucher|R200.00|R192.00|
|54|WORLDCHAT|WorldChat|Pinned Voucher|Airtime Voucher|R100.00|R80.50|
|55|WORLDCHAT|WorldChat|Pinned Voucher|Airtime Voucher|R200.00|R161.00|
|56|CELLC|CellC R2-R999|Pinless Airtime|Airtime|R0.00|-|
|57|HEITA|Telkom Mobile Airtime|Pinless Airtime|Airtime|R0.00|-|
|58|MTN|MTN R2-R999|Pinless Airtime|Airtime|R0.00|-|
|59|VODACOM|Vodacom Airtime|Pinless Airtime|Airtime|R0.00|-|
|60|CELLC|5MB-R2|Pinless Data|Same Day Data|R2.00|-|
|61|CELLC|25MB-R4|Pinless Data|Same Day Data|R4.00|-|
|62|CELLC|15MB-R5|Pinless Data|30-day Data Bundle|R5.00|-|
|63|CELLC|250MB-R6|Pinless Data|Night Data|R6.00|-|
|64|CELLC|45MB-R8|Pinless Data|5-day Data Bundle|R8.00|-|
|65|CELLC|65MB-R9|Pinless Data|Same Day Data|R9.00|-|
|66|CELLC|40MB-R12|Pinless Data|30-day Data Bundle|R12.00|-|
|67|CELLC|120MB-R14|Pinless Data|Same Day Data|R14.00|-|
|68|CELLC|1GB-R15|Pinless Data|Night Data|R15.00|-|
|69|CELLC|500MB-R17|Pinless Data|Same Day Data|R17.00|-|
|70|CELLC|65MB-R20|Pinless Data|30-day Data Bundle|R20.00|-|
|71|CELLC|250MB-R25|Pinless Data|5-day Data Bundle|R25.00|-|
|72|CELLC|150MB-R29|Pinless Data|30-day Data Bundle|R29.00|-|
|73|CELLC|300MB-R49|Pinless Data|30-day Data Bundle|R49.00|-|
|74|CELLC|600MB-R50|Pinless Data|5-day Data Bundle|R50.00|-|
|75|CELLC|750MB-R80|Pinless Data|30-day Data Bundle|R80.00|-|
|76|CELLC|1GB-R100|Pinless Data|30-day Data Bundle|R100.00|-|
|77|CELLC|1.5GB-149|Pinless Data|30-day Data Bundle|R149.00|-|
|78|CELLC|2GB-R199|Pinless Data|30-day Data Bundle|R199.00|-|
|79|CELLC|3GB-249|Pinless Data|30-day Data Bundle|R249.00|-|
|80|CELLC|6GB-R299|Pinless Data|30-day Data Bundle|R299.00|-|
|81|CELLC|7GB-R399|Pinless Data|30-day Data Bundle|R399.00|-|
|82|CELLC|10GB-R599|Pinless Data|365-day Data Bundle|R599.00|-|
|83|CELLC|20GB-R799|Pinless Data|365-day Data Bundle|R799.00|-|
|84|CELLC|30GB-R899|Pinless Data|365-day Data Bundle|R899.00|-|
|85|CELLC|50GB-R1099|Pinless Data|365-day Data Bundle|R1099.00|-|
|86|CELLC|40GB-R1199|Pinless Data|90-day Data Bundle|R1199.00|-|
|87|CELLC|100GB-R1599|Pinless Data|365-day Data Bundle|R1599.00|-|
|88|CELLC|200GB-R1999|Pinless Data|365-day Data Bundle|R1999.00|-|
|89|CELLC|100GB-R2999|Pinless Data|90-day Data Bundle|R2999.00|-|
|90|HEITA|25MB-R7.30|Pinless Data|Data Bundle|R7.30|-|
|91|HEITA|100MB-R10|Pinless Data|Weekend Data Bundle|R10.00|-|
|92|HEITA|50MB-R14.65|Pinless Data|Data Bundle|R14.65|-|
|93|HEITA|20MB-R15.15|Pinless Data|FreeMe Boost Weekly|R15.15|-|
|94|HEITA|200MB-R19|Pinless Data|Weekend Data Bundle|R19.00|-|
|95|HEITA|100MB-R29.25|Pinless Data|Data Bundle|R29.25|-|
|96|HEITA|250MB-R39.50|Pinless Data|Data Bundle|R39.50|-|
|97|HEITA|300+300MB-R49-7mth|Pinless Data|Weekend Data Bundle|R49.00|-|
|98|HEITA|250MB-R59.50|Pinless Data|FreeMe Boost Weekly|R59.50|-|
|99|HEITA|500MB-R69.60|Pinless Data|Data Bundle|R69.60|-|
|100|HEITA|1GB+1GB-R100|Pinless Data|Data Bundle|R100.00|-|
|101|HEITA|2GB+2GB-R140|Pinless Data|Data Bundle|R140.00|-|
|102|HEITA|3GB+3GB-R201|Pinless Data|Data Bundle|R201.00|-|
|103|HEITA|5GB+5GB-R301|Pinless Data|Data Bundle|R301.00|-|
|104|HEITA|10GB+10GB-R505|Pinless Data|Data Bundle|R505.00|-|
|105|HEITA|20GB-R905|Pinless Data|Data Bundle|R905.00|-|
|106|HEITA|50GB-R1815|Pinless Data|Data Bundle|R1815.00|-|
|107|HEITA|100GB-R3227|Pinless Data|Data Bundle|R3227.00|-|
|108|MTN|15MB-R2|Pinless Data|Rush Hour|R2.00|-|
|109|MTN|25MB-R5|Pinless Data|Same Day Data|R5.00|-|
|110|MTN|50MB-R8|Pinless Data|Same Day Data|R8.00|-|
|111|MTN|40MB-R10|Pinless Data|Data Bundle|R10.00|-|
|112|MTN|150MB-R12|Pinless Data|Rush Hour|R12.00|-|
|113|MTN|120MB-R15|Pinless Data|Same Day Data|R15.00|-|
|114|MTN|120MB-R17|Pinless Data|Weekly Data|R17.00|-|
|115|MTN|100MB-R20|Pinless Data|Data Bundle|R20.00|-|
|116|MTN|200MB-R25|Pinless Data|Weekly Data|R25.00|-|
|117|MTN|300MB-R27|Pinless Data|Same Day Data|R27.00|-|
|118|MTN|150MB-R29|Pinless Data|Data Bundle|R29.00|-|
|119|MTN|1GB-R30|Pinless Data|Rush Hour|R30.00|-|
|120|MTN|500MB-R35|Pinless Data|Night Data|R35.00|-|
|121|MTN|200MB-R39|Pinless Data|Data Bundle|R39.00|-|
|122|MTN|350MB-R40|Pinless Data|Weekly Data|R40.00|-|
|123|MTN|1GB-R50|Pinless Data|Same Day Data|R50.00|-|
|124|MTN|500MB-R55|Pinless Data|Weekly Data|R55.00|-|
|125|MTN|1GB-R59|Pinless Data|Night Data|R59.00|-|
|126|MTN|350MB-R60|Pinless Data|Data Bundle|R60.00|-|
|127|MTN|1GB-R70|Pinless Data|Weekly Data|R70.00|-|
|128|MTN|500MB-R75|Pinless Data|Data Bundle|R75.00|-|
|129|MTN|750MB-R89|Pinless Data|Data Bundle|R89.00|-|
|130|MTN|1GB-R99|Pinless Data|Data Bundle|R99.00|-|
|131|MTN|2GB-R109|Pinless Data|Night Data|R109.00|-|
|132|MTN|1GB-R110|Pinless Data|Fort Nightly Data|R110.00|-|
|133|MTN|5GB-R139|Pinless Data|Night Data|R139.00|-|
|134|MTN|1.5GB-R149|Pinless Data|Data Bundle|R149.00|-|
|135|MTN|100MB-R159|Pinless Data|12mth Pay-once Data|R159.00|-|
|136|MTN|2GB-R189|Pinless Data|Data Bundle|R189.00|-|
|137|MTN|5GB-R199|Pinless Data|Weekly Data|R199.00|-|
|138|MTN|10GB-R209|Pinless Data|Night Data|R209.00|-|
|139|MTN|3GB-R229|Pinless Data|Data Bundle|R229.00|-|
|140|MTN|300MB-R259|Pinless Data|6mth Pay-once Data|R259.00|-|
|141|MTN|500MB-R339|Pinless Data|6mth Pay-once Data|R339.00|-|
|142|MTN|6GB-R399|Pinless Data|Data Bundle|R399.00|-|
|143|MTN|10GB-R469|Pinless Data|Data Bundle|R469.00|-|
|144|MTN|500MB-R529|Pinless Data|12mth Pay-once Data|R529.00|-|
|145|MTN|1GB-R579|Pinless Data|6mth Pay-once Data|R579.00|-|
|146|MTN|20GB-R699|Pinless Data|Data Bundle|R699.00|-|
|147|MTN|30GB-R999|Pinless Data|Data Bundle|R999.00|-|
|148|MTN|2GB-R1399|Pinless Data|12mth Pay-once Data|R1399.00|-|
|149|MTN|50GB-R1499|Pinless Data|Data Bundle|R1499.00|-|
|150|MTN|100GB-R2499|Pinless Data|Data Bundle|R2499.00|-|
|151|VODACOM|R2 10 min call after recharge|Pinless Data|Power Bundle|R2.00|-|
|152|VODACOM|50MB-R4|Pinless Data|Night Data|R4.00|-|
|153|VODACOM|20MB-R5|Pinless Data|Same Day Data|R5.00|-|
|154|VODACOM|100MB-R7|Pinless Data|Night Data|R7.00|-|
|155|VODACOM|60MB-R9|Pinless Data|Same Day Data|R9.00|-|
|156|VODACOM|50MB-R12|Pinless Data|30-day Data Bundle|R12.00|-|
|157|VODACOM|250MB-R14|Pinless Data|Night Data|R14.00|-|
|158|VODACOM|100MB-R15|Pinless Data|Same Day Data|R15.00|-|
|159|VODACOM|100MB-R17|Pinless Data|Weekly Data|R17.00|-|
|160|VODACOM|250MB-R27|Pinless Data|Same Day Data|R27.00|-|
|161|VODACOM|150MB-R29|Pinless Data|30-day Data Bundle|R29.00|-|
|162|VODACOM|250MB-R35|Pinless Data|Weekly Data|R35.00|-|
|163|VODACOM|1GB-R49|Pinless Data|Night Data|R49.00|-|
|164|VODACOM|500MB-R60|Pinless Data|Weekly Data|R60.00|-|
|165|VODACOM|500MB-R79|Pinless Data|30-day Data Bundle|R79.00|-|
|166|VODACOM|1GB-R80|Pinless Data|Weekly Data|R80.00|-|
|167|VODACOM|1GB-R99|Pinless Data|30-day Data Bundle|R99.00|-|
|168|VODACOM|100MB pm-R119|Pinless Data|6mth Pay-once Data|R119.00|-|
|169|VODACOM|2GB-R120|Pinless Data|Weekly Data|R120.00|-|
|170|VODACOM|250MB pm-R219|Pinless Data|6mth Pay-once Data|R219.00|-|
|171|VODACOM|3GB-R229|Pinless Data|30-day Data Bundle|R229.00|-|
|172|VODACOM|500MB pm-R339|Pinless Data|6mth Pay-once Data|R339.00|-|
|173|VODACOM|5GB-R349|Pinless Data|30-day Data Bundle|R349.00|-|
|174|VODACOM|10GB-R469|Pinless Data|30-day Data Bundle|R469.00|-|
|175|VODACOM|20GB-R699|Pinless Data|30-day Data Bundle|R699.00|-|
|176|VODACOM|1GB pm-R899|Pinless Data|12mth Pay-once Data|R899.00|-|
|177|VODACOM|2GB pm-R1399|Pinless Data|12mth Pay-once Data|R1399.00|-|
|178|VODACOM|5GB pm-R3499|Pinless Data|12mth Pay-once Data|R3499.00|-|
|179|VODACOM|10GB pm-R5999|Pinless Data|12mth Pay-once Data|R5999.00|-|
|180|CELLC|40MB-R10|Pinless Data|30-day Data Bundle|R10.00|-|
|181|CELLC|1GB-R95|Pinless Data|30-day Data Bundle|R95.00|-|
|182|CELLC|500MB-R45|Pinless Data|Weekly Data|R45.00|-|
|183|CELLC|1GB-R65|Pinless Data|Weekly Data|R65.00|-|
|184|TELKOM|Telkom Mobile Airtime|Pinless Airtime|Airtime|R0.00|-|
|185|TELKOM|100MB-R10|Pinless Data|Weekend Data Bundle|R10.00|-|
|186|TELKOM|20MB-R15.15|Pinless Data|FreeMe Boost Weekly|R15.15|-|
|187|TELKOM|200MB-R19|Pinless Data|Weekend Data Bundle|R19.00|-|
|188|TELKOM|1GB-R49|Pinless Data|Weekend Data Bundle|R49.00|-|
|189|TELKOM|250MB-R59.50|Pinless Data|FreeMe Boost Weekly|R59.50|-|
|190|HEITA|35+35MB-R7-7mth|Pinless Data|Once Off Data Bundle|R7.00|-|
|191|HEITA|75+75MB-R14-7mth|Pinless Data|Once Off Data Bundle|R14.00|-|
|192|HEITA|150+150MB-R29-7mth|Pinless Data|Once Off Data Bundle|R29.00|-|
|193|HEITA|500+500MB-R69-7mth|Pinless Data|Once Off Data Bundle|R69.00|-|
|194|HEITA|1+1GB-R99-3mth|Pinless Data|Once Off Data Bundle|R99.00|-|
|195|HEITA|2+2GB-R139-3mth|Pinless Data|Once Off Data Bundle|R139.00|-|
|196|HEITA|3+3GB-R199-3mth|Pinless Data|Once Off Data Bundle|R199.00|-|
|197|HEITA|5+5GB-R299-3mth|Pinless Data|Once Off Data Bundle|R299.00|-|
|198|HEITA|10+10GB-R469-3mth|Pinless Data|Once Off Data Bundle|R469.00|-|
|199|HEITA|20GB-R699-7mth|Pinless Data|Once Off Data Bundle|R699.00|-|
|200|HEITA|50GB-R1499-7mth|Pinless Data|Once Off Data Bundle|R1499.00|-|
|201|HEITA|100GB-R2499-7mth|Pinless Data|Once Off Data Bundle|R2499.00|-|


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
