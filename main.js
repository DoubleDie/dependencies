const { RestClientV5 } = require('bybit-api');
const { Client, Message } = require('discord.js-selfbot-v13')
require('dotenv').config()
let token = process.env.DISC_AUTH;
const discordClient = new Client({
	checkUpdate: false
});

discordClient.on('ready', async () => {
	console.log('Client is ready!')
});

const commonTerms = ["Target 1:", "POWER", "SL Close Below", "<@&1180193532309409874>"];
const tradingPairs = ["ETC | USDT", "AVAX | USDT", "ATOM | USDT", "LINK | USDT", "XRP | USDT", "EOS | USDT", "AAVE | USDT", "XTZ | USDT", "ETH | USDT", "SAND | USDT", "BTC | USDT", "NEAR | USDT", "QTUM | USDT", "BAT | USDT", "DOT | USDT", "LTC | USDT", "BNB | USDT", "XLM | USDT", "MATIC | USDT", "FIL | USDT", "UNI | USDT", "SOL | USDT", "FTM | USDT"];
robKey = process.env.ROB_KEY;
robSecret = process.env.ROB_SECRET;
holgerKey = process.env.HOLGER_KEY;
holgerSecret = process.env.HOLGER_SECRET;

function filterMessage( message ) {
    let status;
    if ( message.includes(commonTerms[0]) && message.includes(commonTerms[1]) && message.includes(commonTerms[2]) && message.includes(commonTerms[3]) ) {
        for ( pair of tradingPairs ) {
            if ( message.includes(pair) ) {
                status = true;
                break;
            } else {
                status = false;
            }
        }
    } else {
        status = false;
    }
    return status;
}

function formatSignal( message ) {
    details = {Coin: "", buyPrice: "", stopLoss: "", takeProfit1: "", takeProfit2: ""};
    if ( message.includes("Target 3") ) {
        message = message.split("\n").join(" ").split(" ");
        details.Coin = message[1] + "USDT";
        details.buyPrice = parseFloat(message[5].slice(1).split(",").join(""));
        details.stopLoss = parseFloat(message[30].split(",").join(""));
        details.takeProfit1 = parseFloat(message[14].split(",").join(""));
        details.takeProfit2 = parseFloat(message[19].split(",").join(""));
    } else if ("Target 2") {
        message = message.split("\n").join(" ").split(" ");
        details.Coin = message[1] + "USDT";
        details.buyPrice = parseFloat(message[5].slice(1).split(",").join(""));
        details.stopLoss = parseFloat(message[25].split(",").join(""));
        details.takeProfit1 = parseFloat(message[14].split(",").join(""));
        details.takeProfit2 = parseFloat(message[19].split(",").join(""));
    } else {
        message = message.split("\n").join(" ").split(" ");
        details.Coin = message[1] + "USDT";
        details.buyPrice = parseFloat(message[5].slice(1).split(",").join(""));
        details.stopLoss = parseFloat(message[20].split(",").join(""));
        details.takeProfit1 = parseFloat(message[14].split(",").join(""));
    }
    return details;
}

async function processSignal( details, apiKey, apiSecret ) {
    const client = new RestClientV5({testnet: false, key: apiKey, secret: apiSecret});
    let response = await client.getPositionInfo({category: "linear", settleCoin: "USDT"});
    console.log("Position info: ", response);
    let positions = response.result.list.length;
    if ( positions <= 1 ) {
        let response = await client.getWalletBalance({accountType: "UNIFIED", coin: "USDT"});
        console.log("Wallet info: ", response);
        let available = response.result.list[0].coin[0].availableToWithdraw;
        let inPositions = response.result.list[0].coin[0].totalPositionIM;
        let totalBalance = parseFloat(available) + parseFloat(inPositions);
        response = await client.getTickers({category: "linear", symbol: details.Coin});
        console.log("Ticker info: ", response);
        let currentPrice = parseFloat(response.result.list[0].lastPrice);
        let priceDifference = Math.abs(currentPrice - details.buyPrice)
        if ( currentPrice > details.buyPrice ) {
            details.stopLoss = details.stopLoss + priceDifference;
            details.takeProfit1 = details.takeProfit1 + priceDifference;
            if ( details.takeProfit2 !== "" ) {
                details.takeProfit2 = details.takeProfit2 + priceDifference;
            }
        }
        else if ( currentPrice < details.buyPrice ) {
            details.stopLoss = details.stopLoss - priceDifference;
            details.takeProfit1 = details.takeProfit1 - priceDifference;
            if ( details.takeProfit2 !== "" ) {
                details.takeProfit2 = details.takeProfit2 - priceDifference;
            }
        }
        let purchaseAmount = ((0.05 * totalBalance)/Math.abs(details.stopLoss - details.buyPrice)) * details.buyPrice;
        let leverage;
        if ( positions === 0 ) {
            leverage = Math.ceil(purchaseAmount/(totalBalance/2))
        } else if ( positions === 1 ) {
            leverage = Math.ceil(purchaseAmount/totalBalance)
        }
        response = await client.getInstrumentsInfo({category: "linear", symbol: details.Coin});
        console.log("Instument info: ", response);
        let minOrderQty = parseFloat(response.result.list[0].lotSizeFilter.minOrderQty);
        let orderQty = (purchaseAmount / details.buyPrice).toString();
        let decimal;
        if (orderQty.includes(".")) {
            decimal = orderQty.split(".")[1].length;
            orderQty = parseFloat(orderQty.toFixed(decimal));
        } else {
            decimal = 0;
            orderQty = parseFloat(orderQty.toFixed(decimal));
        }
        if (orderQty > minOrderQty) {
            let maxLever = parseInt(data.result.list[0].leverageFilter.maxLeverage)
            if (maxLever >= leverage) {
                try {
                    response = await client.setLeverage({category: "linear", symbol: details.Coin, buyLeverage: leverage.toString(), sellLeverage: leverage.toString()});
                } catch (err) {
                    console.log("Lever already set.")
                }
                let trailing = Math.abs(details.buyPrice - details.takeProfit1).toFixed(decimal);
                let initOrder = client.submitOrder({category: "linear", symbol: details.Coin, side: "Buy", orderType: "Limit", qty: orderQty.toString(), price: details.buyPrice.toString()});
                let newPosition = 0
                while (newPosition === 0) {
                    setTimeout(() => {
                        client.getPositionInfo({category: "linear", symbol: details.Coin})
                        .then(data => {
                            newPosition = data.result.list[0].length;
                        })
                    }, 500)
                }
                setTimeout(() => {
                    if (details.takeProfit2 !== "") {
                        client.setTradingStop({
                            category: "linear",
                            symbol: details.Coin,
                            takeProfit: details.takeProfit.toString(),
                            stopLoss: details.stopLoss.toString(),
                            tpslMode: "Partial",
                            tpOrderType: "Market",
                            slOrderType: "Market",
                            slSize: (orderQty/2).toString(),
                            tpSize: (orderQty/2).toString(),
                            positionIdx: 0
                        })
                        .then((response) => {
                            console.log(response);
                        })
                        .catch((err) => {
                            console.log("Error: ", err)
                        })
                        client.setTradingStop({
                            category: "linear",
                            symbol: details.Coin,
                            takeProfit: details.takeProfit2.toString(),
                            stopLoss: details.stopLoss.toString(),
                            tpslMode: "Partial",
                            tpOrderType: "Market",
                            slOrderType: "Market",
                            slSize: (orderQty/2).toString(),
                            tpSize: (orderQty/2).toString(),
                            trailingStop: trailing,
                            activePrice: details.takeProfit1.toString(),
                            positionIdx: 0
                        })
                        .then((response) => {
                            console.log(response);
                        })
                        .catch((err) => {
                            console.log("Error: ", err)
                        })
                    } else {
                        client.setTradingStop({
                            category: "linear",
                            symbol: details.Coin,
                            takeProfit: details.takeProfit1.toString(),
                            stopLoss: details.stopLoss.toString(),
                            tpslMode: "Partial",
                            tpOrderType: "Market",
                            slOrderType: "Market",
                            slSize: (orderQty).toString(),
                            tpSize: (orderQty).toString(),
                            trailingStop: trailing,
                            activePrice: details.takeProfit1.toString(),
                            positionIdx: 0
                        })
                        .then((response) => {
                            console.log(response);
                        })
                        .catch((err) => {
                            console.log("Error: ", err)
                        })
                    }

                }, 10000)
            }
        }
        



    }

}

discordClient.on('messageCreate', async (message) => {
	console.log('Message: ' + message.content)
    message = message.content;
    let status = filterMessage(message);
    if (status) {
        console.log("Pass");
        let details = formatSignal(message);
        processSignal(details, robKey, robSecret);
        //processSignal(details, holgerKey, holgerSecret)
    }
});
discordClient.login(token);