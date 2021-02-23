import discord
from discord.ext.commands import Bot
import config
from os import listdir
from os.path import isfile, join, dirname, abspath
import asyncio
import glob
import os
import YTDL
import datetime
import time


class DiscordClient():
    def __init__(self):
        intents = discord.Intents.default()
        intents.presences = True
        intents.members = True
        self.bot = Bot(command_prefix=config.BOT_PREFIX, intents=intents)
        self.voice_client = None
        self.STREAM_PLAYER = None

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
        self.voice_client = voice_client
        # create a player
        player = await YTDL.YTDLSource.from_url(url, loop=self.bot.loop)
        self.STREAM_PLAYER = voice_client
        # begin playing music in the channel
        voice_client.play(player, after=lambda e: print('Player error: %s' % e) if e else None)
        #get the text channel
        text_channel = None
        if voice_channel.name == "hidden":
            text_channel = self.bot.get_guild(config.GUILD_ID).get_channel(config.HIDDEN_TEXT_CHANNEL)
        else:
            text_channel = self.bot.get_guild(config.GUILD_ID).get_channel(config.GENERAL_TEXT_CHANNEL)
        start_time = datetime.datetime.now()
        player_duration = time.strftime('%H:%M:%S', time.gmtime(player.duration))
        # send a message with information about the link being played
        embed = discord.Embed(title=player.title)
        url = "https://www.youtube.com/watch?v=" + url
        embed.add_field(name='Video URL', value=url)
        embed.add_field(name='Duration', value=("00:00:00/" + player_duration))
        msg = await text_channel.send(embed=embed)
        # get the channel's emojis
        emojis = text_channel.guild.emojis
        # add all the emojis to the message
        play_pause_emoji = emojis[1]
        stop_emoji = emojis[2]
        down_emoji = emojis[3]
        up_emoji = emojis[4]
        replay_emoji = emojis[5]
        await msg.add_reaction(play_pause_emoji)
        await msg.add_reaction(stop_emoji)
        await msg.add_reaction(down_emoji)
        await msg.add_reaction(up_emoji)
        await msg.add_reaction(replay_emoji)
        pause_loop_counter = 0
        # wait for the player to finish playing the youtube url
        while voice_client.is_playing() or voice_client.is_paused():
            if voice_client.is_playing():
                await asyncio.sleep(0.9)
                current_time = datetime.datetime.now() - start_time - datetime.timedelta(seconds=pause_loop_counter)
                embed = discord.Embed(title=player.title)
                embed.add_field(name='Video URL', value=url)
                embed.add_field(name='Duration', value=("0" + str(current_time)[0:-7] + "/" + player_duration))
                await msg.edit(embed=embed)
            else:
                await asyncio.sleep(1)
                pause_loop_counter += 1

        # disconnect from channel
        voice_client.stop()
        await voice_client.disconnect()
        self.STREAM_PLAYER = None
        self.voice_client = None
        # delete audio file after it is finished playing
        files = glob.glob("TemporaryAudio/*")
        for f in files:
            if 'Youtube-' in f.title():
                os.remove(f.title())
        return


    async def stop(self):
        if self.voice_client is not None:
            await self.voice_client.disconnect()
            self.STREAM_PLAYER = None
            self.voice_client = None
        return


    async def pause(self):
        if self.STREAM_PLAYER is not None:
            # if audio is playing, pause it. otherwise resume the audio
            if self.STREAM_PLAYER.is_playing():
                self.STREAM_PLAYER.pause()
            else:
                self.STREAM_PLAYER.resume()

    async def volume(self, vol):
        if self.STREAM_PLAYER is not None:
            self.STREAM_PLAYER.source.volume = int(vol) / 100


    async def volumedown(self):
        if self.STREAM_PLAYER is not None and self.STREAM_PLAYER.source.volume > 0.0:
            self.STREAM_PLAYER.source.volume -= 0.1


    async def volumeup(self):
        if self.STREAM_PLAYER is not None and self.STREAM_PLAYER.source.volume < 2.0:
            self.STREAM_PLAYER.source.volume += 0.1
