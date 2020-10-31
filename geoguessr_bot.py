from typing import List

import discord
import csv
from geoguessr_download import geoguessr_blackjack


class DiscordClient(discord.Client):
    def __init__(self):
        super().__init__()
        self.games = {}
        self.pause = {}

    async def on_ready(self):
        print('Logged on as {0}!'.format(self.user))

    async def on_message(self, message):
        print('Message from {0.author}: {0.content}'.format(message))
        if message.author.bot:
            return
        if message.content == '!new' or message.content == '!new -c':
            if '-c' in message.content:
                self.games[message.channel.id] = ([], [])
            else:
                self.games.pop(message.channel.id, None)
                self.games[message.author.id] = ([], [])
            player_message = (
                    'New Blackjack Round!\nExample message formats include: \n' +
                    '      https://www.geoguessr.com/results/ 5000 15000\n' +
                    '      https://www.geoguessr.com/results/ 10\n' +
                    '      https://www.geoguessr.com/results/ 10%\n' +
                    'These represent scores between 5000 and 10000, the top 10 Scorers, and the top 10% Scorers'
            )
            await message.channel.send(player_message)
        else:
            game_id = message.channel.id
            if message.author.id not in self.games and message.channel.id not in self.games:
                game_id = message.author.id
                self.games[message.author.id] = ()
            if message.content == '!stop':
                self.pause[game_id] = True
            if message.content == '!start':
                self.pause[game_id] = False
            if game_id not in self.pause or not self.pause[game_id]:
                try:
                    results = geoguessr_blackjack(
                        message.content, self.games[game_id][0] if self.games[game_id] else []
                    )
                    if len(results[0]) == 0:
                        player_message = 'No players fit between these scores, try another round.'
                    else:
                        self.games[game_id] = results
                        temp_res = list(zip(results[1], results[2]))
                        temp_res = [score[0] + ' | ' + str('{:,}'.format(score[1])) for score in temp_res]
                        player_message = 'Players in game still:\n\n' + '\n'.join(temp_res)
                except ValueError:
                    player_message = (
                            'Incorrect Formatting- Please use this format:\nhttps://www.geoguessr.com/results/ 5000 ' +
                            '15000\n\nNote there are no hypens, no commas, and send the lower score then the higher' +
                            'score.\n You can also send in just one number (n), and that will find the top (n) scorers, or ' +
                            'send a percent (n), and it will send top (n) percent of scorers.'
                    )
                if len(player_message) <= 1999:
                    await message.channel.send(player_message)
                if self.games[game_id] and len(self.games[game_id][0]) > 0:
                    with open('{}.csv'.format(game_id), 'w', encoding='utf-8') as result_file:
                        wr = csv.writer(result_file, dialect='excel')
                        for name, score in zip(self.games[game_id][1], self.games[game_id][2]):
                            wr.writerow([name, '{:,}'.format(score)])
                    await message.channel.send('Here are the results for this round:', file=discord.File('{}.csv'.format(game_id)))
                await message.channel.send('If you want to start a new game, send !new')


client = DiscordClient()
client.run('NzMyMDQ2NzM2NjYyNDYyNTY2.Xwu5pg.pE-FTwUWa2V1vDJ_VrpKK0_RwCw')
