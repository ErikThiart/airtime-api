# Freepaid Airtime API 
### Seamless integration & customisable Airtime API

This is an API that enables you to order Vodacom, Cell C, MTN and Telkom Airtime and Data.

### Overview
You can order pinless airtime and data (direct recharge) through this API as well as order pinned vouchers. You create an account with Freepaid who will then give you a usernumber to use in the API calls.
You deposit money into your account with them and that money will then be allocated to your virtual wallet, you can then proceed to order airtime at a discounted rate through their API and it will be billed against the money inside your virtual wallet with them. In essence as long as there is funds in your account you will be able to order pinned and pinless airtime and data at a discount.

#### API Spec
The API is soap

The full WSDL can be found here: https://ws.freepaid.co.za/airtimeplus/?wsdl

The full documentation can be found here https://ws.freepaid.co.za/airtimeplus/ 

#### Step 1: Register for Monopoly Money
First you need to setup a virtual wallet that will be loaded with sandbox money to test the API and the integration into your application.

Register on the dev site: http://dev.freepaid.co.za/home.html 

They will send you a OTP (One time pin), save this as it will be used as your usernumber.
The password will be the one you entered into the website during registration. 

Once you have done this, send an email to apisupport@freepaid.co.za with the following subject: 

**Github | the number you registered with | Sandbox API** 

They will then allocate R10 000 worth of monopoly money to your account to test with.

### Step 2: Setting up your enviroument
They use a PHP/NuSOAP library, but you're free to use whatever you're comfortable with. I also use a modified PHP NuSOAP library which you can find here https://gist.github.com/ErikThiart/b630d2d05290077b19c3b07278e57cfe I have made some modifications to make sure it works with PHP 7

To fetch the balance you will use a call like this:

```php

  require_once( "nusoap.php" );
  $client = new nusoap_client( "http://ws.dev.freepaid.co.za/airtimeplus/" );
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

### Step 3: Getting to understand the process flow.
The API gives you the ability to issue to kinds of vouchers, Pinned and Pinless.


Pinned vouchers are the most reliable to issue because they sit on their server so Freepaid can always guarantee delivery of pinned vouchers, pinless relies heavily on the networks and they do have delays from time to time.

Airtime vouchers are available both as Pinned and Pinless vouchers, when you order pinned vouchers you can only order vouchers that exist with the network for example:

```
CELLC R10.00
CELLC R25.00
CELLC R35.00


MTN R10.00
MTN R15.00
MTN R30.00


VODACOM R10.00
VODACOM R12.00
VODACOM R29.00
```

However on pinless you can order any amount from R2.00 all the way to R999 so you can order **Vodacom R2.35** or **MTN R11.76** this is often used in apps to act as an incentive for users to stay engaged since the company can issue any amount small to large however they see fit.

#### Process Flow Pinned Vouchers
For pinned you will issue a **fetchProducts** call to get the products then you will issue a **placeOrder** call to place the order and then you will receive back the pin and serial of the voucher.

#### Process Flow Pinless Vouchers
For pinless vocuhers you will issue a **fetchProducts** call to get the products then you will issue a **placeOrder** call to place the order and then you will receive back an order number, you will then use this order number to query the status of the pinless recharge using the **queryOrder** call which will return success or failure.

So in essence:

**Pinless:**

* Fetch Product List ( Pinless vouchers will be p-network example p-vodacom)
* Place Pinless Order
```php
     "user" => "USERXXXX",  # USER number, NOT cell number
     "pass" => "PASSXXXX",
     "refno" => "TESTXXXX", # Your own refno
     "network" => "p-vodacom",  # pinless vodacom
     "sellvalue" => "2.44",
     "count" => "1",  # ONLY 1 is accepted here for pinless
     "extra" => "CELLXXXX",  # CELL number to be recharged
```
* Query Pinless Order
```php
      "user" => "USERXXXX",  # USER number, NOT cell number
      "pass" => "PASSXXXX",
      "orderno" => "ORDERXXX",
```

The steps are you place the order and receive back an order number you then use that order number to query the status of the order. 

For **pinned** you will use placeOrder to place the order, but then you will use the order number to fetch the actual pinned order receiving back a pin and serial for the voucher. (You can use the order number to re-order old vouchers, reprints).

### FAQ
#### Does the API work with cents?
Yes, you can order pinless in values like R2.50, R3.20. Please make sure to use a decimal point and not a comma. R4.55 is correct. R4,55 is not correct.

##### What is the correct API url to use?
On **live** use https://ws.freepaid.co.za/airtimeplus/ note the "https".

On **dev** use http://ws.dev.freepaid.co.za/airtimeplus/ note the "http" and .dev subdomain.

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

#### Can I order PINNED vouchers, pinless airtime and data bundles using the same API?
Yes, provided you use the correct calls and values you can do so.

#### What is my USER number and where do I find it?
The USER number is in fact the number associated with your account in our system, which is in turn associated with the mobile number that you registered with. The USER number is contained in the first SMS which we sent to you during registration. If you have deleted the SMS then login at services.freepaid.co.za, click on reports, then SMS log, and find the first SMS we sent you. To find the USER number for the DEV site, login at http://dev.freepaid.co.za click on Reports, then SMS log, and find the first SMS we sent you.

### Sample Code
Please feel free to add sample code and snippets to this readme, currently I only have sample code in PHP, but would like to expand this section to include other langauges.

#### fetch balance
```php
  require_once( "nusoap.php" );
  $client = new nusoap_client( "http://ws.dev.freepaid.co.za/airtimeplus/" );
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
  $client = new nusoap_client( "http://ws.dev.freepaid.co.za/airtimeplus/" );
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

#### place pinned order
```php
  require_once( "nusoap.php" );
  $client = new nusoap_client( "http://ws.dev.freepaid.co.za/airtimeplus/" );
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

#### fetch pinned order
```php
  require_once( "nusoap.php" );
  $client = new nusoap_client( "http://ws.dev.freepaid.co.za/airtimeplus/" );
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

#### place pinless order
```php
  require_once( "nusoap.php" );
  $client = new nusoap_client( "http://ws.dev.freepaid.co.za/airtimeplus/" );
  $err = $client->getError( );
  if( $err ){
    print "<p><b>Constructor error: ".$err."</b></p>";
  }
  else {
    $request = array(
      "user" => "USERXXXX",  # USER number, NOT cell number
      "pass" => "PASSXXXX",
      "refno" => "TESTXXXX",
      "network" => "p-vodacom",  # pinless vodacom
      "sellvalue" => "2",
      "count" => "1",  # ONLY 1 is accepted here for pinless
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

#### query pinless order
```php
  require_once( "nusoap.php" );
  $client = new nusoap_client( "http://ws.dev.freepaid.co.za/airtimeplus/" );
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

Feel free to submit code snippets done in other programming languages.
