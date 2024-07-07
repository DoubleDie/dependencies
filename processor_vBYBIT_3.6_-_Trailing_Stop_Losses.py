import time
import datetime
import math
import http.client, urllib
from pybit.unified_trading import HTTP
import json
import traceback

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

#load api keys
rob_api_key = '1ypglMwj1gKSmvhsmE'
rob_secret = 'Edlls60jK9yM7DgUmCwvy0lVPQ4YgOnDk43g'

holger_api_key = 'VJMonsFJcJJ0k0kshQ'
holger_secret = 'h6TbfrvvAMgOImJSjiBZqfmRpfsc9ONW6BbE'


def init_setup(): #read value of last message on startup so that last message of previous session is not counted as a new message
	datastream = open("last_message.txt", 'r', encoding='utf8') 
	chatlog = datastream.read()
	datastream.close()
	content = chatlog
	#load symbols with open positions from previous sessions
	return content

def messageUpdate(content): #update latest message and ensure it is a new message
	counter = 0
	while True:
		try:
			time.sleep(0.2)
			counter += 1
			datastream = open("last_message.txt", 'r', encoding='utf8')
			chatlog = datastream.read()
			datastream.close()
			if chatlog != content:
				content = chatlog
				data_dict = chatlog
				print(data_dict)
				if float(data_dict['stopLoss']) < float(data_dict['takeProfit1']):
					connectAPI('rob', data_dict, rob_api_key, rob_secret)
					connectAPI('holger', data_dict, holger_api_key, holger_secret)
				else:
					#implement short trades
					print('Short trades yet to be implemented')
					print('------------------------------------------------------------------')
		except:
			print(traceback.format_exc())
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
		take_profit2 = float(removeComma(params['TP2']))
		take_profit = float(removeComma(params['TP1']))

	else:
		take_profit2 = 'undefined'
		take_profit = float(removeComma(params['TP1']))

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
	if not abandon:
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
		price = str(price)
		if '.' in price:
			dec = price.split('.')[1]
			lpo = len(dec)
		else:
			lpo = 0


	if not position_open and not abandon:
		#setting leverage
		try:
			bybitAPI.set_leverage(category='linear', symbol=coin, buyLeverage=str(leverage), sellLeverage=str(leverage))
		except:
			x = 1
		print(lpo)
		trailing = str(round(abs(float(buyprice) - float(take_profit)), lpo))
		take_profit = str(round(float(take_profit), lpo))
		stoploss = str(round(float(stoploss), lpo))
		
		#placing trade
		init_order = bybitAPI.place_order(
			category='linear',
			symbol=coin,
			side='Buy',
			orderType='Limit',
			qty=str(qty),
			price=str(buyprice)
			)
		print(init_order)
		new_position = 0
		while new_position == 0:
			time.sleep(0.5)
			new_position = len(bybitAPI.get_positions(category='linear', symbol=coin)['result']['list'])
			print(new_position)
		time.sleep(2)
		if take_profit2 != 'undefined':
			first_stop_order = bybitAPI.set_trading_stop(
				category='linear',
				symbol=coin,
				takeProfit=str(take_profit),
				stopLoss=str(stoploss),
				tpslMode='Partial',
				tpOrderType='Market',
				slOrderType='Market',
				slSize=str(float(qty)/2),
				tpSize=str(float(qty)/2),
				positionIdx=0
				)

			second_stop_order = bybitAPI.set_trading_stop(
				category='linear',
				symbol=coin,
				takeProfit=str(take_profit2),
				stopLoss=str(stoploss),
				tpslMode='Partial',
				tpOrderType='Market',
				slOrderType='Market',
				slSize=str(float(qty)/2),
				tpSize=str(float(qty)/2),
				trailingStop=trailing,
				activePrice=str(take_profit),
				positionIdx=0
				)
		else:
			stop_order = bybitAPI.set_trading_stop(
				category='linear',
				symbol=coin,
				takeProfit=str(take_profit),
				stopLoss=str(stoploss),
				tpslMode='Partial',
				tpOrderType='Market',
				slOrderType='Market',
				slSize=str(qty),
				tpSize=str(qty),
				trailingStop=trailing,
				activePrice=(take_profit),
				positionIdx=0
				)

		orderTable(coin, buyprice, ausd, leverage, stoploss, take_profit)

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







