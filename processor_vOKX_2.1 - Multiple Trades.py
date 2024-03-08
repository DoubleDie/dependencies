import time
import math
import okx.Trade as Trade
import okx.MarketData as MarketData
import okx.Account as Account
import okx.PublicData as PublicData

common_terms = ['Target 1:', 'POWER', 'SL Close Below', '<@&1180193532309409874>']
trading_pairs = ['ETC | USDT', 'AVAX | USDT', 'ATOM | USDT', 'LINK | USDT', 'XRP | USDT', 'EOS | USDT', 'AAVE | USDT', 'XTZ | USDT', 'ETH | USDT', 'SAND | USDT', 'BTC | USDT', 'NEAR | USDT', 'QTUM | USDT']
okx_inst = coins = ['ETC-USDT-SWAP', 'AVAX-USDT-SWAP', 'ATOM-USDT-SWAP', 'LINK-USDT-SWAP', 'XRP-USDT-SWAP', 'EOS-USDT-SWAP', 'AAVE-USDT-SWAP', 'XTZ-USDT-SWAP', 'ETH-USDT-SWAP', 'SAND-USDT-SWAP', 'BTC-USDT-SWAP', 'NEAR-USDT-SWAP', 'QTUM-USDT-SWAP']


def init_setup():
	datastream = open("last_message.txt", 'r', encoding='utf8')
	chatlog = datastream.read()
	datastream.close()
	content = chatlog
	return content

def removeComma(number):
	number = number.split(',')
	return ''.join(number)

def filterMessages(message):
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
		
def messageUpdate(content):
	while True:
		time.sleep(0.5)
		datastream = open("last_message.txt", 'r', encoding='utf8')
		chatlog = datastream.read()
		datastream.close()
		if chatlog != content:
			content = chatlog
			if filterMessages(chatlog):
				data_dict = formatData(chatlog)
				stoploss = float(removeComma(data_dict['Stop Loss']))
				buyprice = float(removeComma(data_dict['Buy Price']))
				if stoploss < buyprice:
					#print(data_dict)
					connectAPI(data_dict)

				else:
					print('Short trades yet to be implemented')
				print('------------------------------------------------------------------')


def formatData(message):
	details_dict = {'Coin': '', 'Buy Price': '', 'Stop Loss': '', 'TP1': '', 'TP2': '', 'TP3': '', 'Time Frame': ''}
	if "Target 3" in message:
		message = " ".join(message.split('\n'))
		message = message.split(' ')
		details_dict['Coin'] = message[1] + '-USDT-SWAP'
		details_dict['Buy Price'] = message[5][1:]
		details_dict['Stop Loss'] = removeComma(message[-3])
		details_dict['TP1'] = message[14]
		details_dict['TP2'] = message[19]
		details_dict['TP3'] = message[24]
		details_dict['Time Frame'] = message[7]

	elif "Target 2" in message:
		message = " ".join(message.split('\n'))
		message = message.split(' ')
		details_dict['Coin'] = message[1] + '-USDT-SWAP'
		details_dict['Buy Price'] = message[5][1:]
		details_dict['Stop Loss'] = removeComma(message[-3])
		details_dict['TP1'] = message[14]
		details_dict['TP2'] = message[19]
		details_dict['Time Frame'] = message[7]

	else:
		message = " ".join(message.split('\n'))
		message = message.split(' ')
		details_dict['Coin'] = message[1] + '-USDT-SWAP'
		details_dict['Buy Price'] = message[5][1:]
		details_dict['Stop Loss'] = removeComma(message[-3])
		details_dict['TP1'] = message[14]
		details_dict['Time Frame'] = message[7]
	return details_dict

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

def connectAPI(params):
	flag = '0' # 0 for live trading

	#set to live or demo
	if flag == '1':
		#demo keys
		api_key = '1f3668ae-87a5-4a31-be4a-913db7299d67'
		secret_key = '08BAA0503ACD32CF03A5AE3C4861721E'
		passphrase = 'BigHairyBalls12!@'
	elif flag == '0':
		#live keys
		api_key = '20cf3fd4-24b1-4a8d-86f2-7240a105a228'
		secret_key = 'DFBF64A3D572AF49D4728A1F676A99A1'
		passphrase = 'SpittingBars12!'

	temp = []
	#set as demo trading

	#connection to market api
	marketDataAPI = MarketData.MarketAPI(flag = flag)

	#connect to PublicData api
	PublicDataAPI = PublicData.PublicAPI(flag=flag)

	#connect to account api
	accountAPI = Account.AccountAPI(api_key, secret_key, passphrase, False, flag)

	#connect to trade api
	tradeAPI = Trade.TradeAPI(api_key, secret_key, passphrase, False, flag)

	#set account to long/short mode to allow leverage
	result = accountAPI.set_position_mode(posMode="long_short_mode")


	#check for open positions
	positions = accountAPI.get_positions()
	 
	positions_open = len(positions['data'])
	if positions_open == 2:
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
		take_profit = params['TP2']
		take_profit = removeComma(take_profit)
		take_profit = float(take_profit)
	else:
		take_profit = params['TP1']
		take_profit = removeComma(take_profit)
		take_profit = float(take_profit)

	#get account balance
	balance = accountAPI.get_account_balance()
	for currency in balance['data'][0]['details']:
		if currency['ccy'] == 'USDT':
			USDT_balance = float(currency['availBal'])
	print("||||||||||||||||||||||||||||||||||||||||||||")
	print('|| Available balance: ' + str(USDT_balance) + ' ||')
	print("||||||||||||||||||||||||||||||||||||||||||||")
	
	num = len(coin) - 5
	stripped_coin = coin[:num]	

	#get coin price

	result = marketDataAPI.get_tickers(instType = 'SWAP', uly = stripped_coin)
	print(result)
	price = float(result['data'][0]['last'])

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
	portfolio = USDT_balance
	risk = 0.15 * float(portfolio)
	stop = stoploss
	diff = float(stop) - float(buyprice)
	diff = abs(diff)
	amt = risk/diff
	ausd = amt*float(buyprice)
	print("||||||||||||||||||||||||||||||||||||||||||||")
	print('|| Purchase $' +str(ausd)+' worth of coin. ||')
	print("||||||||||||||||||||||||||||||||||||||||||||")

	#get contract value
	result = PublicDataAPI.get_instruments(instType='SWAP', uly=stripped_coin)
	ctVal = result['data'][0]['ctVal']
	ctMult = result['data'][0]['ctMult']
	contract_value = float(ctVal)*float(ctMult)
	contract_value_usd = contract_value * float(price)
	print("||||||||||||||||||||||||||||||||||||||||||||")
	print('|| Contract Value: ' + str(contract_value_usd) + ' ||')
	


	#check if purchase is possible
	if contract_value_usd > ausd:
		abandon = True
		print('|| Cost per contract too high ||')
	else:
		abandon = False


	#quantity to purchase
	num_of_contracts = ausd/contract_value_usd
	num_of_contracts = math.floor(num_of_contracts)
	print('|| Number of contracts purchased: ' + str(num_of_contracts) + ' ||')
	print("||||||||||||||||||||||||||||||||||||||||||||")

	#calculating required leverage
	if positions_open == 0:
		leverage = ausd/(USDT_balance/2)
		leverage = math.ceil(leverage)
	if positions_open == 1:
		leverage = ausd/USDT_balance
		leverage = math.ceil(leverage)
	

	#calculating buffer
	buffer = buyprice/200

	if not position_open and not abandon:
		#setting leverage
		accountAPI.set_leverage(instId=coin, lever=leverage, mgnMode='isolated', posSide='long')

		#placing trade
		result = tradeAPI.place_order(
	    instId=coin,
	    tdMode="isolated",
	    tpTriggerPx=str(take_profit - buffer),
	    slTriggerPx=str(stoploss + buffer),
	    tpOrdPx=str(take_profit),
	    slOrdPx=str(stoploss),
	    side="buy",
	    posSide='long',
	    ordType="limit",
	    px=str(buyprice),
	    sz=num_of_contracts
		)
		while not position_open:
			time.sleep(2)
			positions = accountAPI.get_positions()
			if positions['data'] == temp:
				position_open = False
			else:
				position_open = True

		orderTable(stripped_coin, buyprice, (int(num_of_contracts) * int(contract_value)), leverage, stoploss, take_profit)
		




	


	





content = init_setup()
print("Processor ready!")
messageUpdate(content)





