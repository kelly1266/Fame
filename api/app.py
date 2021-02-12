import discord
from discord.ext.commands import Bot
import config
from os import listdir
from os.path import isfile, join, dirname, abspath
import asyncio

class DiscordClient:
    def __init__(self):
        intents = discord.Intents.default()
        intents.presences = True
        intents.members = True
        self.bot = Bot(command_prefix=config.BOT_PREFIX, intents=intents)

    async def soundboard(self, sound, user):
        directory = dirname(dirname(abspath(__file__))) + "\\Audio\\"
        # get the full mp3 file name
        mp3_file_name = directory + sound + '.mp3'

        # grab the user who sent the command
        voice_channel = None
        try:
            voice_channel = self.bot.get_guild(config.GUILD_ID).get_member_named(user).voice.channel
            print('test')
        except:
            return

        # check if a file with the given name exists
        only_files = [f for f in listdir(directory) if isfile(join(directory, f))]
        file_exists = False
        for file in only_files:
            test_file_name = directory + file
            if mp3_file_name == test_file_name:
                file_exists = True

        # only play music if user is in a voice channel
        if voice_channel is not None and file_exists:
            # create StreamPlayer
            vc = await voice_channel.connect()
            vc.play(discord.FFmpegPCMAudio(mp3_file_name), after=lambda e: print('done', e))
            # loop until the mp3 file is finished playing
            while vc.is_playing():
                await asyncio.sleep(1)
            # disconnect after the player has finished
            vc.stop()
            await vc.disconnect()
