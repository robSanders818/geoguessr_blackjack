from typing import List

import discord
import csv
from geoguessr_download import geoguessr_blackjack


class DiscordClient(discord.Client):
    def __init__(self):
        super().__init__()
        self.games = {}

    async def on_ready(self):
        print('Logged on as {0}!'.format(self.user))

    async def on_message(self, message):
        print('Message from {0.author}: {0.content}'.format(message))
        if message.author.bot:
            return
        if message.content == '!new':
            self.games[message.author.id] = ([], [])
            player_message = 'New Blackjack Round!'
        else:
            if message.author not in self.games:
                self.games[message.author.id] = []
            try:
                self.games[message.author.id] = geoguessr_blackjack(message.content, self.games[message.author.id])
                player_message = 'Players in game still:\n\n' + '\n'.join(self.games[message.author.id][0])
            except ValueError:
                player_message = (
                        'Incorrect Formatting- Please use this format:\nhttps://www.geoguessr.com/results/ 5000 ' +
                        '15000\n\nNote there are no hypens.  If you want to start a new game, enter \"!new\"'
                )
        if len(player_message) > 1999:
            with open('{}.csv'.format(message.author.id), 'w', encoding='utf-8') as result_file:
                wr = csv.writer(result_file, dialect='excel')
                for name, score in zip(self.games[message.author.id][0], self.games[message.author.id][1]):
                    wr.writerow([name, score])
            await message.channel.send('There are too many players left to fit in one message, here they are:', file=discord.File('{}.csv'.format(message.author.id)))
        else:
            await message.channel.send(player_message)


client = DiscordClient()
client.run('NzMyMDQ2NzM2NjYyNDYyNTY2.XxDtjg.9zw96glT-twG2-9TTMvvF7QT2lc')
