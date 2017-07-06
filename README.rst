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

<<<<<<< HEAD
Get **krakenex** and **tweepy** from somewhere
=======
 - sudo apt-get install python3 python-pip3
 - sudo pip install virtualenv
 -

 To activate virtual python enviroment with it's dependencies
 virtualenv --no-site-packages --distribute -p /usr/bin/python3 .venv && source .venv/bin/activate && pip3 install -r requirements.txt


 To unactivate and return to normal system python
 - deactivate
>>>>>>> fb884ea... Enabling non-mandatory usage of VirtualENV

Rename **keys.json.preview** to **keys.json** and add your own kraken and twitter keys to it.
