import discord

from geoguessr_download import geoguessr_blackjack


class DiscordClient(discord.Client):
    def __init__(self):
        super().__init__()
        self.players = []

    async def on_ready(self):
        print('Logged on as {0}!'.format(self.user))

    async def on_message(self, message):
        print('Message from {0.author}: {0.content}'.format(message))
        if message.author.bot:
            return
        if message.content == '!new':
            self.players = []
            player_message = 'New Blackjack Round!'
        else:
            self.players = geoguessr_blackjack(message.content, self.players)
            player_message = 'Players in game still:\n\n' + '\n'.join(self.players)
        await message.channel.send(player_message)


client = DiscordClient()
client.run('NzMyMDQ2NzM2NjYyNDYyNTY2.Xwvf6A.72VmsZZmr0C09hOkF92NAomHW9I')
