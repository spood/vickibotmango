import json
from pprint import pprint
import krakenex
from decimal import getcontext, Decimal, ROUND_UP, ROUND_DOWN
import threading
import time
from datetime import datetime
import tweepy
from tweepy import Stream
from tweepy import OAuthHandler
from tweepy.streaming import StreamListener
import os
import sys

ckey = consumer_secret = access_token_key = access_token_secret = ''


usage = "Usage: vickiboy.py \n\
For a manual run add the arguments: m [short/long]"





# help format timedelta objects into strings
def strfdelta(tdelta, fmt):
    d = {"days": tdelta.days}
    d["hours"], rem = divmod(tdelta.seconds, 3600)
    d["minutes"], d["seconds"] = divmod(rem, 60)
    return fmt.format(**d)

# help determine if a number is within a certain percent of another. For 10%, percentAmount should be 0.1
def isNumberWithinPercentOfNumber(numberToCheck, baseNumber, percentAmount):
    lowerRange = baseNumber - (baseNumber * percentAmount)
    upperRange = baseNumber + (baseNumber * percentAmount)
    if lowerRange < numberToCheck < upperRange:
        return True
    return False

# Parse out the tweets from https://twitter.com/vickicryptobot and see if profit is to be made from following them
class VickiBot:

    def __init__(self):
        print("in VickiBot __init__")
        with open('keys/keys.json') as data_file:
            data = json.load(data_file)
            self.kraken = krakenex.API(key=data["kraken"]["api_key"], secret=data["kraken"]["priv_key"])
        #with open('stats.json') as data_file:
        #    self.stats = json.load(data_file)
        print("started")

    #def updateStatsJson(self):
    #    print("updated with new balance stats",self.stats["balances"])
    #    with open("stats.json", "w") as jsonFile:
    #        json.dump(self.stats, jsonFile)

    def getPriceHistoryAverage(self):
        response = self.kraken.query_public('Trades', {'pair': 'XETHXXBT'})
        recentTrades = response["result"]["XETHXXBT"]
        oldestTrade = recentTrades[0]
        # oldestTrade looks like    ['0.101673', '0.00200000', 1499376600.2512, 'b', 'm', '']
        # presumably                [price, volume, timestamp (epoch), buy/sell, market/limit, unknown?]
        middleTrade = recentTrades[len(recentTrades)//2] # floor division so it forces integer
        oldestTradeTime = datetime.fromtimestamp(oldestTrade[2])
        middleTradeTime = datetime.fromtimestamp(middleTrade[2])

        currentTime = datetime.now()
        oldestTimeDiff = currentTime - oldestTradeTime
        oldestTimeDiffStr = strfdelta(oldestTimeDiff, "{hours} hours {minutes} minutes")

        middleTimeDiff = currentTime - middleTradeTime
        middleTimeDiffStr = strfdelta(middleTimeDiff, "{hours} hours {minutes} minutes")

        averagePrice = (Decimal(oldestTrade[0]) + Decimal(middleTrade[0])) / 2
        print("Between",oldestTimeDiffStr,"and",middleTimeDiffStr,"ago the average price was:",averagePrice)
        return averagePrice

    def buyOrderKrakenETHBTC(self,volume,price):
        if isinstance(volume, Decimal) == False:
            raise TypeError('RIP: volume NaN, abandoning ship')

        if isinstance(price, Decimal) == False:
            raise TypeError('RIP: price NaN, abandoning ship')

        if self is None:
            raise ValueError('RIP: self is empty (me_irl), abandoning ship')

        if volume is None:
            raise ValueError('RIP: volume is empty, abandoning ship')

        if price is None:
            raise ValueError('RIP: price is empty, abandoning ship')

        print("Actually placing buy limit order for ETH with BTC at price",price,"with volume",volume)

        self.kraken.query_private('AddOrder', {'pair': 'XETHXXBT',
                                 'type': 'buy',
                                 'ordertype': 'limit',
                                 'price': price,
                                 'volume': volume})


    def sellOrderKrakenETHBTC(self,volume,price):
        if isinstance(volume, Decimal) == False:
            raise TypeError('RIP: volume NaN, abandoning ship')

        if isinstance(price, Decimal) == False:
            raise TypeError('RIP: price NaN, abandoning ship')

        if self is None:
            raise ValueError('RIP: self is empty (me_irl), abandoning ship')

        if volume is None:
            raise ValueError('RIP: volume is empty, abandoning ship')

        if price is None:
            raise ValueError('RIP: price is empty, abandoning ship')

        print("Actually placing sell limit order for ETH with BTC at price",price,"with volume",volume)

        self.kraken.query_private('AddOrder', {'pair': 'XETHXXBT',
                                 'type': 'sell',
                                 'ordertype': 'limit',
                                 'price': price,
                                 'volume': volume})

    def getKrakenOrders(self,pairname):
        if self is None:
            raise ValueError('RIP: self is empty (me_irl), abandoning ship')

        if pairname is None:
            raise ValueError('RIP: pairname is empty, abandoning ship')

        krakenOrders = self.kraken.query_public('Depth',{'pair': pairname, 'count': '10'})
        #print(krakenOrders)

        krakenBuyOrders = krakenOrders['result'][pairname]['bids']
        krakenBuyOrdersD = [[Decimal(price), Decimal(volume)] for price, volume, timestamp in krakenBuyOrders]
        krakenBuyOrdersD.sort(reverse=True)  # sort from highest to lowest
        #print("kraken buy orders:", krakenBuyOrdersD)

        krakenSellOrders = krakenOrders['result'][pairname]['asks']
        krakenSellOrdersD = [[Decimal(price), Decimal(volume)] for price, volume, timestamp in krakenSellOrders]
        krakenSellOrdersD.sort()  # sort from lowest to highest
        #print("kraken sell orders:", krakenSellOrdersD)
        return (krakenBuyOrdersD,krakenSellOrdersD)

    def getKrakenETHBTC(self):
        if self is None:
            raise ValueError('RIP: self is empty (me_irl), abandoning ship')

        return self.getKrakenOrders("XETHXXBT")

    def longPosition(self, sellOrders, currency1, currency2):
        if self is None:
            raise ValueError('RIP: self is empty (me_irl), abandoning ship')

        if sellOrders is None:
            raise ValueError('RIP: sellOrders is empty, abandoning ship')

        if currency1 is None:
            raise ValueError('RIP: currency1 is empty, abandoning ship')

        if currency2 is None:
            raise ValueError('RIP: currency2 is empty, abandoning ship')


        averagePrice = self.getPriceHistoryAverage()

        print("Going long on", currency1, currency2, "(buy eth with btc)")
        ethAmount,btcAmount = self.getKrakenEthBTCBalance()
        #btcAmount = Decimal(0.001)
        countAbleVolume = btcAmount.quantize(Decimal('.00001'), rounding=ROUND_DOWN)
        for kprice, kvolume in sellOrders:
            if(isNumberWithinPercentOfNumber(kprice,averagePrice,Decimal(0.1)) == False):
                print("WARNING: price", kprice, "is not within 10% of the recent average price", averagePrice, "not opening an order")
                break
            print("BTC to spend",countAbleVolume)
            print("viewing sell orders (price,volume):",kprice,kvolume)
            if(countAbleVolume > Decimal(0.00000)):
                volumeToTrade = min(kvolume,countAbleVolume)
                print("Placing buy order for",volumeToTrade,"at price",kprice)
                self.buyOrderKrakenETHBTC(volumeToTrade,kprice)
                countAbleVolume -= volumeToTrade
            else:
                print("done opening orders")
                break

    def shortPosition(self, buyOrders, currency1, currency2):
        if self is None:
            raise ValueError('RIP: self is empty (me_irl), abandoning ship')

        averagePrice = self.getPriceHistoryAverage()

        print("Going short on", currency1, currency2,"(sell btc for eth)")
        ethAmount,btcAmount = self.getKrakenEthBTCBalance()
        #ethAmount = Decimal(0.01)
        countAbleVolume = ethAmount.quantize(Decimal('.00001'), rounding=ROUND_DOWN)
        for kprice, kvolume in buyOrders:
            if(isNumberWithinPercentOfNumber(kprice,averagePrice,Decimal(0.1)) == False):
                print("WARNING: price", kprice, "is not within 10% of the recent average price", averagePrice, "not opening an order")
                break
            print("ETH to spend",countAbleVolume)
            print("viewing buy orders (price,volume):",kprice,kvolume)
            if(countAbleVolume > Decimal(0.00000)):
                volumeToTrade = min(kvolume,countAbleVolume)
                print("Placing sell order for",volumeToTrade,"at price",kprice)
                self.sellOrderKrakenETHBTC(volumeToTrade,kprice)
                countAbleVolume -= volumeToTrade
            else:
                print("done opening orders")
                break

    def longETHBTC(self):
        if self is None:
            raise ValueError('RIP: self is empty (me_irl), abandoning ship')

        (buyOrders, sellOrders) = self.getKrakenETHBTC()
        self.longPosition(sellOrders, "ETH", "BTC")

    def shortETHBTC(self):
        if self is None:
            raise ValueError('RIP: self is empty (me_irl), abandoning ship')

        (buyOrders, sellOrders) = self.getKrakenETHBTC()
        self.shortPosition(buyOrders, "ETH", "BTC")

    def getKrakenEthBTCBalance(self):
        if self is None:
            raise ValueError('RIP: self is empty (me_irl), abandoning ship')

        print("Getting Kraken balance...")
        balance = self.kraken.query_private('Balance')

        balance = balance['result']

        ethbtcBalance = dict()
        newbalance = dict()
        for currency in balance:
            newname = currency[1:]  # remove first symbol ('Z' or 'X')
            newbalance[newname] = balance[currency]
            if(newname == "ETH" or newname == "XBT"):
                ethbtcBalance[newname] = Decimal(balance[currency])
        balance = newbalance

        print(ethbtcBalance)
        #print(balance)
        return ethbtcBalance["ETH"],ethbtcBalance["XBT"]


    def parseTweetInfo(self, tweet):
        if self is None:
            raise ValueError('RIP: self is empty (me_irl), abandoning ship')

        if tweet is None:
            raise ValueError('RIP: tweet 🐦 is empty, abandoning ship')

        print("Parsing out the tweet...")
        tweetUpper = tweet.upper()
        if 'SHORT' in tweetUpper:
            if 'ETHBTC' in tweetUpper:
                self.shortETHBTC()
        elif 'LONG' in tweetUpper:
            if 'ETHBTC' in tweetUpper:
                self.longETHBTC()
        else:
            print("didn't meet any conditions for action")

    def practiceRun(self):

        if self is None:
            raise ValueError('RIP: self is empty (me_irl), abandoning ship')

        t = threading.Timer(20.0, self.practiceRun)
        t.daemon = True
        t.start()

        # limit decimal to 6 decimal places for readability.. have to do this each time it threads
        getcontext().prec = 6
        #self.longBTCUSD()
        #self.shortETHUSD()
        #(krakBuyOrders,krakSellOrders) = self.getKrakenOrders()

        # see if it's worth trading
        #self.arbitrageQuadrigaPreview(quadBuyOrders, krakSellOrders)
        #self.arbitrageKrakenPreview(krakBuyOrders,quadSellOrders)
        #self.baitBuyKrakenPreview(krakBuyOrders, quadBuyOrders)
       # self.baitSellQuadrigaPreview(krakSellOrders, quadSellOrders)
        #print("total trade profit: $", self.baitMoneyMade, "ether traded:",self.volumeTraded,"(about",(self.volumeTraded * 130) + self.KRAKEN_WIRE_COST,"dollars needed for these trades)")
        #print("profits after wire cost:", self.baitMoneyMade - self.KRAKEN_WIRE_COST)


class listener(StreamListener):
    def __init__(self):
        self.vickibot = VickiBot()
 
    def on_data(self, data):
        #print(data)
        jdata = json.loads(data)
        try:
            tweetText = jdata['text']
        except Exception as e:
            tweetText = ''
            print("exception:",e)
        print("tweeted:", tweetText)
        self.vickibot.parseTweetInfo(tweetText)

    def on_status(self, status):
        print(status)
        print(status.text)

    def on_error(self, status):
        print("error",status)

 
with open('keys/keys.json') as data_file:
    data = json.load(data_file)
    ckey = data['twitter']['ckey']
    consumer_secret = data['twitter']['consumer_secret']
    access_token_key = data['twitter']['access_token_key']
    access_token_secret = data['twitter']['access_token_secret']


if len(sys.argv) == 3 and sys.argv[1] == "m":
    practiceTweet = ''
    if(sys.argv[2] == "short"):
        practiceTweet = "I am going short on ETHBTC #ethereum"
    elif(sys.argv[2] == "long"):
        practiceTweet = "I am going long ETHBTC #ethereum"
    else:
        print(usage)
        sys.exit()
    print("Doing manual run using simulated tweet: ", practiceTweet)
    vickibot = VickiBot()
    vickibot.parseTweetInfo(practiceTweet)
elif len(sys.argv) == 2 and sys.argv[1] == "p":
    vickibot = VickiBot()
    averagePrice = vickibot.getPriceHistoryAverage()
    print("verifying if average price:",averagePrice,"is within 10% of 0.11")
    if(isNumberWithinPercentOfNumber(Decimal(0.11),averagePrice,Decimal(0.1))):
        print("it is")
    else:
        print("it isn't")
elif len(sys.argv) == 1:
    print("listening on twitter")
    auth = OAuthHandler(ckey, consumer_secret) #OAuth object
    auth.set_access_token(access_token_key, access_token_secret)

    while(1):
        try:
            twitterStream = Stream(auth, listener()) #initialize Stream object with a time out limit
            twitterStream.filter(follow=['834940874643615744'], async=False) # vicki:  834940874643615744
        except KeyboardInterrupt:
            print("W: interrupt received, stopping…")
        except Exception as e:
            print("some sort of error lol",e)
else:
    print(usage)
    sys.exit()