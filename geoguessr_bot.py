from typing import List

import discord
import csv

from bs4 import BeautifulSoup

from geoguessr_download import geoguessr_blackjack
import json
import requests


class DiscordClient(discord.Client):
    """
        Class for Discord Client:
            Keeps track of games dictionary, as mapping of users with the bot, along with the
            players who are still in the game, and a mapping of if the users game is paused
    """
    def __init__(self):
        super().__init__()
        self.games = {}
        self.pause = {}

    async def on_ready(self):
        print('Logged on as {0}!'.format(self.user))

    async def on_message(self, message):
        """
        On message, processes message input.  Delegates if new, creates a new game for the user, if the message is stop,
        it pauses the game/start resumes the game, and anything else is processed as 'valid' game input
        :param message: the discord message object containing all information about the message
        """
        print('Message from {0.author}: {0.content}'.format(message))
        if message.author.bot:
            return
        if message.content == '!new' or message.content == '!new -c':
            await message.channel.send(self.respond_new(message))
        else:
            # Determines which game_id to use, either the author, or the channel
            game_id = message.channel.id
            if message.author.id not in self.games and message.channel.id not in self.games:
                game_id = message.author.id
                self.games[message.author.id] = ()

            if '!bl' in message.content:
                await message.channel.send(self.handle_blacklist(game_id, message))
            elif message.content == '!stop':
                await message.channel.send(self.handle_stop_start(game_id, True))
            elif message.content == '!start':
                await message.channel.send(self.handle_stop_start(game_id, False))
            elif game_id not in self.pause or not self.pause[game_id]:
                await self.process_game(message, game_id)

    def respond_new(self, message) -> str:
        """
        Responds to a new game message.
        If -c is in the message, it will treat the channel id as the key to track the game
        :param message: The discord message object containing all information about the message
        :return: String containing info about how to use bot
        """
        self.games[message.channel.id] = ([], [], [])
        # if '-c' in message.content:
        #     self.games[message.channel.id] = (
        #         [], [], []
        #     )
        # else:
        #     self.games.pop(message.channel.id, None)
        #     self.games[message.author.id] = (
        #         [], [], []
        #     )
        player_message = (
                'New Blackjack Round!\nExample message formats include: \n' +
                '      https://www.geoguessr.com/results/ 5000 15000\n' +
                '      https://www.geoguessr.com/results/ 10\n' +
                '      https://www.geoguessr.com/results/ 10%\n' +
                'These represent scores between 5000 and 10000, the top 10 Scorers, and the top 10% Scorers'
        )
        return player_message

    def handle_stop_start(self, game_id, stop_start: bool) -> str:
        """
        Abstract function which handles starting and stopping the game, by changing the self.pause dictionary
        :param game_id: Id of game, either the authors id, or the channels id
        :param stop_start: Determines whether the user is trying to stop or start the bot
        :return: String to respond with, to inform user if bot is stopped
        """
        self.pause[game_id] = stop_start
        resp = 'I will stop talking' if stop_start else 'I\'m Back!'
        return resp

    async def process_game(self, message, game_id):
        """
        Processes the game treating the message content as an actual request to play a round
        :param message: The discord message object containing all information about the message
        :param game_id: Id of game, either the authors id, or the channels id
        """

        player_message = self.retrieve_results(message, game_id)
        # If message is short enough to fit in dm, it will send the results.  Always sends along results as csv as well
        if len(player_message) <= 1999:
            await message.channel.send(player_message)
        if (
                self.games[game_id]
                and len(self.games[game_id][0]) > 0 
                and player_message != 'No players fit between these scores, try another round.'
        ):
            with open('{}.csv'.format(game_id), 'w', encoding='utf-8') as result_file:
                wr = csv.writer(result_file, dialect='excel')
                for name, score in zip(self.games[game_id][1], self.games[game_id][2]):
                    wr.writerow([name, '{:,}'.format(score)])
            await message.channel.send('Here are the results for this round:', file=discord.File('{}.csv'.format(game_id)))
        await message.channel.send('If you want to start a new game, send !new')

    def retrieve_results(self, message, game_id) -> str:
        """
        Retrieves the game results, passing the user's request along to the api download file
        :param message: The discord message object containing all information about the message
        :param game_id: Id of game, either the authors id, or the channels id
        :return: String containing info about players in the game still
        """
        try:
            blacklist = self.retrieve_blacklist(game_id)
            results = geoguessr_blackjack(
                message.content, self.games[game_id][0] if self.games[game_id] else [], blacklist
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
        return player_message

    def handle_blacklist(self, game_id, message) -> str:
        retrieve = message.content == '!bl'
        bl_id = message.content.split('!bl ')[1] if not retrieve else ''

        lines = []
        unblacklist = False
        try:
            with open('{}_blacklist.csv'.format(game_id), 'r') as bl_users:
                reader = csv.reader(bl_users)
                for row in reader:
                    if not retrieve and row and row[1] == bl_id:
                        unblacklist = True
                    elif row:
                        lines.append(row)
            if retrieve:
                if lines:
                    new_lines = []
                    for line in lines:
                        new_lines.append(' | '.join(line))
                    return 'Blacklisted Users:\n' + '\n'.join(new_lines)
                else:
                    return 'There are no users blacklisted at the moment'
        except FileNotFoundError:
            if retrieve:
                return 'There are no users blacklisted at the moment'

        player_url = 'https://www.geoguessr.com/user/{}'.format(bl_id)
        player = requests.get(player_url)
        soup = BeautifulSoup(player.text, 'html.parser')
        username = soup.find_all('title')[0].text.split(' -')[0]

        with open('{}_blacklist.csv'.format(game_id), 'w') as writeFile:
            writer = csv.writer(writeFile)
            for line in lines:
                if line:
                    writer.writerow(lines)
        if unblacklist:
            return 'Un-Blacklisted ' + username
        with open('{}_blacklist.csv'.format(game_id), 'a') as bl_file:
            writer = csv.writer(bl_file)
            writer.writerow([username, bl_id, player_url])
        return 'Blacklisted ' + username

    def retrieve_blacklist(self, game_id):
        users = []
        try:
            with open('{}_blacklist.csv'.format(game_id), 'r') as bl_users:
                reader = csv.reader(bl_users)
                for row in reader:
                    if row:
                        users.append(row[1])
        except FileNotFoundError:
            return users

        return users


client = DiscordClient()
client.run('NzMyMDQ2NzM2NjYyNDYyNTY2.Xwu5pg.Z6VSIDqcaxcnMIA9R0QBk4lq798')
