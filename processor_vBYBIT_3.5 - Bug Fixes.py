import time
import datetime
import math
import http.client, urllib
from pybit.unified_trading import HTTP
import json

#set up identifiers of a signal, these will be searched for in any new message to ID it as a signal
common_terms = ['Target 1:', 'POWER', 'SL Close Below', '<@&1180193532309409874>']
trading_pairs = [
'ETC | USDT', 
'AVAX | USDT', 
'ATOM | USDT', 
'LINK | USDT', 
'XRP | USDT', 
'EOS | USDT', 
'AAVE | USDT', 
'XTZ | USDT', 
'ETH | USDT', 
'SAND | USDT', 
'BTC | USDT', 
'NEAR | USDT', 
'QTUM | USDT',
'BAT | USDT',
'DOT | USDT',
'LTC | USDT',
'BNB | USDT',
'XLM | USDT',
'MATIC | USDT',
'FIL | USDT',
'UNI | USDT',
'SOL | USDT',
'FTM | USDT'
]
#load json file containing first take profits of previous session, these are used to create trailing stop losses
f = open('trailing_stops.json')
trailing_stops = json.load(f)
f.close()

#load api keys
rob_api_key = '1ypglMwj1gKSmvhsmE'
rob_secret = 'Edlls60jK9yM7DgUmCwvy0lVPQ4YgOnDk43g'

dad_api_key = 'VJMonsFJcJJ0k0kshQ'
dad_secret = 'h6TbfrvvAMgOImJSjiBZqfmRpfsc9ONW6BbE'
#create empty list of symbols with open trades
open_coins = []

def init_setup(): #read value of last message on startup so that last message of previous session is not counted as a new message
	datastream = open("last_message.txt", 'r', encoding='utf8') 
	chatlog = datastream.read()
	datastream.close()
	content = chatlog
	#load symbols with open positions from previous sessions
	f = open('open_coins.txt', 'r')
	coins = f.read()
	open_coins = coins.split('\n')
	f.close()
	return content

def messageUpdate(content): #update latest message and ensure it is a new message
	counter = 0
	while True:
		try:
			time.sleep(0.5)
			counter += 1
			datastream = open("last_message.txt", 'r', encoding='utf8')
			chatlog = datastream.read()
			datastream.close()
			if chatlog != content:
				content = chatlog
				#returns true or false if a signal is detected
				if filterMessages(chatlog):
					#format the data into dict
					data_dict = formatData(chatlog)
					stoploss = float(removeComma(data_dict['Stop Loss']))
					buyprice = float(removeComma(data_dict['Buy Price']))
					#briefly check if signal is long or short
					if stoploss < buyprice:
						#ensure risk/reward ratio is acceptable
						if float(data_dict['Risk/Reward']) >= 2:
							#call on api to place trades
							connectAPI('ROB', data_dict, rob_api_key, rob_secret)
							connectAPI('HOLGER', data_dict, dad_api_key, dad_secret)
					else:
						print('Short trades yet to be implemented')
					print('------------------------------------------------------------------')
			if counter == 10:
				for symbol in open_coins:
					tradeManager(symbol, trailing_stops[symbol])
				counter = 0
		except Exception as error:
			print("An error occurred:", type(error).__name__, "–", error)
			err = (type(error).__name__, "–", error)
			message = []
			message.append(err[0])
			message.append(err[1])
			message.append(str(err[2]))
			message = ' '.join(message)
			sendNotif(message)
			quit()

def filterMessages(message): #determine whether a new message is a valid signal
	message_status = 'Fail'
	counter = 0
	for term in common_terms:
		if term in message:
			counter += 1
	if counter == 4:
		message_status = 'Potential'
		print('Message status: %s' % (message_status))
		counter = 0
	if message_status == 'Potential':
		for pair in trading_pairs:
			if pair in message:
				message_status = 'Pass'
		if message_status == 'Pass':
			print('Message: %s \nMessage status: %s' % (message, message_status))
			return True

		else:
			message_status = 'Fail'


	if message_status == 'Fail':
		print('Message status: %s' % (message_status))
		print('------------------------------------------------------------------')
		return False

def formatData(message):
	details_dict = {'Coin': '', 'Buy Price': '', 'Stop Loss': '', 'TP1': '', 'TP2': '', 'TP3': '', 'Time Frame': '', 'Risk/Reward': ''}
	if "Target 3" in message:
		message = " ".join(message.split('\n'))
		message = message.split(' ')
		details_dict['Coin'] = message[1] + 'USDT'
		details_dict['Buy Price'] = message[5][1:]
		details_dict['Stop Loss'] = removeComma(message[-3])
		details_dict['TP1'] = message[14]
		details_dict['TP2'] = message[19]
		details_dict['TP3'] = message[24]
		details_dict['Time Frame'] = message[7]
		details_dict['Risk/Reward'] = ''.join(message[21].split(')'))

	elif "Target 2" in message:
		message = " ".join(message.split('\n'))
		message = message.split(' ')
		details_dict['Coin'] = message[1] + 'USDT'
		details_dict['Buy Price'] = message[5][1:]
		details_dict['Stop Loss'] = removeComma(message[-3])
		details_dict['TP1'] = message[14]
		details_dict['TP2'] = message[19]
		details_dict['Time Frame'] = message[7]
		details_dict['Risk/Reward'] = ''.join(message[21].split(')'))

	else:
		message = " ".join(message.split('\n'))
		message = message.split(' ')
		details_dict['Coin'] = message[1] + 'USDT'
		details_dict['Buy Price'] = message[5][1:]
		details_dict['Stop Loss'] = removeComma(message[-3])
		details_dict['TP1'] = message[14]
		details_dict['Time Frame'] = message[7]
		details_dict['Risk/Reward'] = ''.join(message[16].split(')'))
	return details_dict

def connectAPI(account, params, api_key, secret_key):
	#connect to api
	bybitAPI = HTTP(
		testnet = False,
		api_key = api_key,
		api_secret = secret_key)

	abandon = False

	#check for positions
	positions = len(bybitAPI.get_positions(category='linear', settleCoin='USDT')['result']['list'])
	 
	positions_open = positions
	#positions_open += orders_open
	if positions_open >= 2:
		position_open = True 
	else:
		position_open = False

	#get all parameters
	buy_price = params['Buy Price']
	buy_price = removeComma(buy_price)
	buy_price = float(buy_price)

	stoploss = params['Stop Loss']
	stoploss = removeComma(stoploss)
	stoploss = float(stoploss)

	coin = params['Coin']

	if params['TP2'] != '':
		take_profit = float(removeComma(params['TP2']))
		trailing = float(removeComma(params['TP1']))

	else:
		take_profit = float(removeComma(params['TP1']))
		trailing = 'fuck'

	#get account balance
	balance = bybitAPI.get_wallet_balance(accountType='UNIFIED', coin='USDT')
	available = balance['result']['list'][0]['coin'][0]['availableToWithdraw']
	in_positions = balance['result']['list'][0]['coin'][0]['totalPositionIM']
	portfolio = float(available)	
	risk_balance = portfolio + float(in_positions)

	print("||||||||||||||||||||||||||||||||||||||||||||")
	print('|| Available balance: ' + str(portfolio) + ' ||')
	print("||||||||||||||||||||||||||||||||||||||||||||")
	

	#get coin price
	ticker = bybitAPI.get_tickers(category='linear', symbol=coin)
	price = ticker['result']['list'][0]['lastPrice']
	price = float(price)
	

	#get price diff
	price_diff = abs(buy_price - price)
	if price > buy_price:
		stoploss += price_diff
		take_profit += price_diff
		buyprice = buy_price + price_diff
	else:
		stoploss -= price_diff
		take_profit -= price_diff
		buyprice = buy_price - price_diff

	#calculate risk
	ausd = ((0.10 * float(risk_balance))/(abs(float(stoploss) - float(buyprice))))*float(buyprice)
	print("||||||||||||||||||||||||||||||||||||||||||||")
	print('|| Purchase $' +str(ausd)+' worth of coin. ||')
	print("||||||||||||||||||||||||||||||||||||||||||||")

	fees = ausd * 0.02

	#calculating required leverage
	if positions_open == 0:
		leverage = math.ceil((ausd + fees)/(portfolio/2))
	if positions_open == 1:
		leverage = math.ceil((ausd + fees)/portfolio)
	if positions_open > 1:
		abandon = True
	if positions_open <= 1:
		print("||||||||||||||||||||||||||||||||||||||||||||")
		print('|| Requires ' + str(leverage) + 'x leverage ||')
		print("||||||||||||||||||||||||||||||||||||||||||||")

	#calculating qantity
	inst_info = bybitAPI.get_instruments_info(category='linear', symbol=coin)
	qtyStep = inst_info['result']['list'][0]['lotSizeFilter']['minOrderQty']
	minQty = float(qtyStep) * float(buyprice)
	qty = math.floor(ausd)
	qty = qty/buyprice
	qty = math.floor(qty)
	if qty < minQty:
		abandon = True
	maxlever = inst_info['result']['list'][0]['leverageFilter']['maxLeverage']
	if leverage > float(maxlever):
		abandon = True


	if not position_open and not abandon:
		#setting leverage
		try:
			bybitAPI.set_leverage(category='linear', symbol=coin, buyLeverage=str(leverage), sellLeverage=str(leverage))
		except:
			x = 1

		#placing trade
		placed_order = bybitAPI.place_order(
			category='linear',
			symbol=coin,
			side='Buy',
			orderType='Limit',
			qty=str(qty),
			price=str(buyprice),
			takeProfit=str(take_profit),
			stopLoss=str(stoploss),
			tpslMode='Full',
			tpOrderType='Market',
			slOrderType='Market'
			)
		open_coins.append(coin)
		trailing_stops[coin] = str(trailing)
		orderTable(coin, buyprice, ausd, leverage, stoploss, take_profit)

def TradeManager(symbol, trailing):
	order = bybitAPI.get_open_orders(category='linear', symbol=symbol)
	if len(order['result']['list']) == 0:
		open_coins.remove(symbol)
		f = open('open_coins.txt', 'w')
		for c in open_coins:
			f.write(c + '\n')
		f.close()
		trailing_stops[symbol] = ''
		f = open('trailing_stops.json', 'w')
		json.dump(trailing_stops, f)
		f.close()
	else:
		#actual trailing stop function
		#check if sl is already trailing sl
		if trailing != 'fuck':
			sl_trigger = order['result']['list'][1]['triggerPrice']
			orderID = order['result']['list'][1]['orderID']
			if sl_trigger != trailing:
				ticker = bybitAPI.get_tickers(category='linear', symbol=symbol)
				price = float(ticker['result']['list'][0]['lastPrice'])
				if price > float(trailing):
					ammended = bybitAPI.amend_order(
						category='linear',
						symbol=symbol,
						orderId=orderID,
						stopLoss=trailing
						)
					print(ammended)


		#get order id
		#amend order to place sl on trailing stop

def removeComma(number):
	number = number.split(',')
	return ''.join(number)

def orderTable(name, price, size, lever, stoploss, takeprofit):
	nameLine = 'ASSET NAME: ' + name
	priceLine = 'ASSET PRICE: ' + str(price)
	sizeLine = 'ORDER SIZE: ' + str(size)
	leverLine = 'LEVERAGE: ' + str(lever)
	stopLine = 'STOP LOSS: ' + str(stoploss)
	profitLine = 'TAKE PROFIT: ' + str(takeprofit)
	top_bottom = ''
	lines = [nameLine, priceLine, sizeLine, leverLine, stopLine, profitLine]
	lines2 = []
	longest = len(nameLine)
	for line in lines:
		if len(line) > longest:
			longest = len(line)
	for char in range(longest + 6):
		top_bottom = top_bottom + '|'
	for line in lines:
		line = '|| ' + line
		while len(line) < (longest + 3):
			line = line + ' '
		line = line + ' ||'
		lines2.append(line)
	print(top_bottom)
	for line in lines2:
		print(line)
	print(top_bottom)

def sendNotif(message):
	head = 'ERROR RAISED'
	errorline = message 
	timeline = 'TIMESTAMP: ' + str(datetime.datetime.now())

	table = head + '\n' + errorline + '\n' + timeline
	secret = 'ammiuntktnnsdx8ojr5m1ijwh8dd5v'
	token = 'uzftevuyfn5kjnwvkwacreewp1q9jo'
	conn = http.client.HTTPSConnection("api.pushover.net:443")
	conn.request("POST", "/1/messages.json",
  	urllib.parse.urlencode({
    	"token": secret,
    	"user": token,
    	"message": table,
  	}), { "Content-type": "application/x-www-form-urlencoded" })
	conn.getresponse()

content = init_setup()
print("Processor ready!")
messageUpdate(content)







