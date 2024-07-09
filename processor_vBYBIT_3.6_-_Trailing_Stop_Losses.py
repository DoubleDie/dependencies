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
				data_dict = json.loads(chatlog)
				print(data_dict)
				if float(data_dict['stopLoss']) < float(data_dict['takeProfit1']):
					connectAPI('rob', data_dict, rob_api_key, rob_secret, 0.05)
					connectAPI('holger', data_dict, holger_api_key, holger_secret, 0.05)
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

def connectAPI(account, params, api_key, secret_key, risk):
	#connect to api
	bybitAPI = HTTP(
		testnet = False,
		api_key = api_key,
		api_secret = secret_key)

	abandon = False
	print("Initiating trade process...")
	#check for positions
	positions = len(bybitAPI.get_positions(category='linear', settleCoin='USDT')['result']['list'])
	 
	if positions <= 2:
	#get account balance
		balance = bybitAPI.get_wallet_balance(accountType='UNIFIED', coin='USDT')
		available = balance['result']['list'][0]['coin'][0]['availableToWithdraw']
		in_positions = balance['result']['list'][0]['coin'][0]['totalPositionIM']
		totalBalance = float(available) + float(in_positions)

		#get coin price
		ticker = bybitAPI.get_tickers(category='linear', symbol=params["Coin"])
		currentPrice = float(ticker['result']['list'][0]['lastPrice'])
		

		#get price diff
		price_diff = abs(float(params["buyPrice"]) - currentPrice)
		if currentPrice > float(params["buyPrice"]):
			params["stopLoss"] = str(float(params["stopLoss"]) + price_diff)
			params["takeProfit1"] = str(float(params["takeProfit1"]) + price_diff)
			if params["takeProfit2"] != "":
				params["takeProfit2"] = str(float(params["takeProfit2"]) + price_diff)
			#params["buyPrice"] = str(float(params["buyPrice"]) + price_diff)
		else:
			params["stopLoss"] = str(float(params["stopLoss"]) - price_diff)
			params["takeProfit1"] = str(float(params["takeProfit1"]) - price_diff)
			if params["takeProfit2"] != "":
				params["takeProfit2"] = str(float(params["takeProfit2"]) - price_diff)
			#params["buyPrice"] = str(float(params["buyPrice"]) - price_diff)

		#calculate risk
		fiatQuantity = ((risk * float(totalBalance)) / (abs(float(params["stopLoss"]) - float(params["buyPrice"])))) * float(params["buyPrice"])
		print(f"Purchase amount: {fiatQuantity}")

		#calculating required leverage
		if positions == 0:
			leverage = math.ceil((fiatQuantity)/(float(available)/2))
		if positions == 1:
			leverage = math.ceil((fiatQuantity)/float(available))

		#calculating qantity
		inst_info = bybitAPI.get_instruments_info(category='linear', symbol=params["Coin"])
		minOrderQty = inst_info['result']['list'][0]['lotSizeFilter']['minOrderQty']
		orderQty = float(fiatQuantity) / float(params["buyPrice"])
		if "." in str(minOrderQty):
			roundTo = len(str(minOrderQty).split(".")[1])
			orderQty = round(orderQty, roundTo)
		else:
			orderQty = math.floor(orderQty)
		if orderQty >= float(minOrderQty):	
			print("Minimum order quantity: pass")
			#checking maximum leverage is above used leverage
			maxlever = inst_info['result']['list'][0]['leverageFilter']['maxLeverage']
			if leverage < float(maxlever):
				print("Leverage: pass")
				#rounding all price figures to the instruments native figures
				if '.' in str(params["buyPrice"]):
					roundTo = len(params["buyPrice"].split('.')[1])
					
				else:
					roundTo = 0

				#setting leverage
				try:
					bybitAPI.set_leverage(category='linear', symbol=params["Coin"], buyLeverage=str(leverage), sellLeverage=str(leverage))
				except:
					x = 1
				trailing = str(round(abs(float(params["buyPrice"]) - float(params["takeProfit1"])), roundTo))
				
				#placing trade
				init_order = bybitAPI.place_order(
					category='linear',
					symbol=params["Coin"],
					side='Buy',
					orderType='Limit',
					qty=str(orderQty),
					price=params["buyPrice"]
					)
				orderId = init_order["result"]["orderId"]
				print(init_order)
				new_position = "0"
				timer = 0
				while new_position == "0" and timer < 60:
					time.sleep(0.5)
					new_position = bybitAPI.get_positions(category='linear', symbol=params["Coin"])['result']['list'][0]["avgPrice"]
					print(f"Position average price: ${new_position}")
					timer += 1
					print(f"Trying for ${timer} more seconds.")
				if timer >= 60:
					print("Trade aborted: Position not filled in time.")
					bybitAPI.cancel_order(category="linear", symbol=params["Coin"], orderId=orderId)
				else:
					if params["takeProfit2"] != "":
						first_stop_order = bybitAPI.set_trading_stop(
							category='linear',
							symbol=params["Coin"],
							takeProfit=params["takeProfit1"],
							stopLoss=params["stopLoss"],
							tpslMode='Partial',
							tpOrderType='Market',
							slOrderType='Market',
							slSize=str(float(orderQty)/2),
							tpSize=str(float(orderQty)/2),
							positionIdx=0
							)

						second_stop_order = bybitAPI.set_trading_stop(
							category='linear',
							symbol=params["Coin"],
							takeProfit=params["takeProfit2"],
							stopLoss=params["stopLoss"],
							tpslMode='Partial',
							tpOrderType='Market',
							slOrderType='Market',
							slSize=str(float(orderQty)/2),
							tpSize=str(float(orderQty)/2),
							trailingStop=trailing,
							activePrice=params["takeProfit1"],
							positionIdx=0
							)
					else:
						stop_order = bybitAPI.set_trading_stop(
							category='linear',
							symbol=params["Coin"],
							takeProfit=params["takeProfit1"],
							stopLoss=params["stopLoss"],
							tpslMode='Partial',
							tpOrderType='Market',
							slOrderType='Market',
							slSize=str(orderQty),
							tpSize=str(orderQty),
							positionIdx=0
							)

					orderTable(params["Coin"], params["buyPrice"], fiatQuantity, leverage, params["stopLoss"], params["takeProfit1"])

def removeComma(number):
	number = number.split(',')
	return ''.join(number)

def orderTable(name, price, size, lever, stoploss, takeprofit):
	nameLine = 'ASSET NAME: ' + name
	priceLine = 'ASSET PRICE: ' + str(price)
	sizeLine = 'ORDER SIZE: ' + str(size)
	leverLine = 'LEVERAGE: ' + str(lever)
	stopLine = 'STOP LOSS: ' + str(stoploss)
	profitLine = 'TAKE PROFIT 1: ' + str(takeprofit)
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







