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
            self.games[message.author.id] = []
            player_message = 'New Blackjack Round!'
        else:
            if message.author not in self.games:
                self.games[message.author.id] = []
            try:
                self.games[message.author.id] = geoguessr_blackjack(message.content, self.games[message.author.id])
                player_message = 'Players in game still:\n\n' + '\n'.join(self.games[message.author.id])
            except ValueError:
                player_message = (
                        'Incorrect Formatting- Please use this format:\nhttps://www.geoguessr.com/results/ 5000 ' +
                        '15000\n\nNote there are no hypens.  If you want to start a new game, enter \"!new\"'
                )
        if len(player_message) > 1999:
            with open('{}.csv'.format(message.author.id), 'w', encoding='utf-8') as result_file:
                wr = csv.writer(result_file, dialect='excel')
                for item in self.games[message.author.id]:
                    wr.writerow([item, ])
            player_message_list = DiscordClient.character_limit_helper(player_message)
            for message_item in player_message_list:
                await message.channel.send(message_item)
            await message.channel.send(file=discord.File('{}.csv'.format(message.author.id)))
        else:
            await message.channel.send(player_message)

    @staticmethod
    def character_limit_helper(message) -> List[str]:
        player_message_list = []
        while len(message) > 0:
            if message.count('\n') == 1:
                if len(player_message_list[-1]) + len(message) < 2000:
                    player_message_list[-1] = player_message_list[-1] + message
                else:
                    player_message_list.append(message)
                break
            last_new_name_tuple = message[:1999].rsplit('\n', 1)
            player_message_list.append(last_new_name_tuple[0])
            message = message[message[:1999].rfind('\n'):]
        return player_message_list


client = DiscordClient()
client.run('NzMyMDQ2NzM2NjYyNDYyNTY2.Xw_OaA.ssxSPQNTvFIPNvess1y9YJkXWZI')
