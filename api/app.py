import discord
from discord.ext.commands import Bot
import config
from os import listdir
from os.path import isfile, join, dirname, abspath
import asyncio
import glob
import os
# from main import STREAM_PLAYER
import YTDL

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

    async def play(self, url, user):
        voice_channel = None
        # if the user is not in a voice channel, abort
        try:
            voice_channel = self.bot.get_guild(config.GUILD_ID).get_member_named(user).voice.channel
        except:
            return
        # join the voice channel
        voice_client = await voice_channel.connect()
        # create a player
        player = await YTDL.YTDLSource.from_url(url, loop=self.bot.loop)
        # begin playing music in the channel
        voice_client.play(player, after=lambda e: print('Player error: %s' % e) if e else None)
        # wait for the player to finish playing the youtube url
        while voice_client.is_playing() or voice_client.is_paused():
            await asyncio.sleep(1)

        # disconnect from channel
        voice_client.stop()
        await voice_client.disconnect()
        # delete audio file after it is finished playing
        files = glob.glob("TemporaryAudio/*")
        for f in files:
            if 'Youtube-' in f.title():
                os.remove(f.title())
        return