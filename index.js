const { Client, Message } = require('discord.js-selfbot-v13')
const fs = require('fs')
let token = 'NDU4MTA5MzM5MTkwOTUxOTUx.GBW8Di.qNtwK7d5SFPPgOwiwldNkaICzhcjrbIWODmIY8';
const client = new Client({
	checkUpdate: false
});

client.on('ready', async () => {
	console.log('Client is ready!')
});




client.on('messageCreate', async (message) => {
	console.log('Message: ' + message.content)
	console.log('------------------------------------------------------------------')
	let messagedata = message.content
	fs.writeFile('last_message.txt', messagedata, (err) => {
		if (err) throw err;
	})


});

client.login(token);
