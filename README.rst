=============================================
vickibot mango
=============================================

Makes trades on Kraken based on what Vicki the crypto bot does.

::

  Usage: vickibot.py [args]

  Examples:

  vickibot.py                                    Waits for Vicki to make a tweet then trades based on that
  vickibot.py m [short|long]                     Execute a short or long trade manually


Supported Pairs:

- ETHBTC


Config
************

 - sudo apt-get install pip
 - sudo pip install virtualenv

 To activate virtual python enviroment with it's dependencies
 - source vickibotmango/bin/activate

 To unactivate and return to normal system python
 - deactivate

Rename **keys.json.preview** to **keys.json** and add your own kraken and twitter keys to it.
