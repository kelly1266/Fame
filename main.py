from __future__ import unicode_literals
import discord
import asyncio
from discord.ext.commands import Bot
import random
import urllib.request
import urllib.parse
import re
from yahoo_fin.stock_info import *
from PyDictionary import PyDictionary
import urllib
import json
import ssl
from gtts import gTTS
from helper_methods import is_word, get_company_name, role_in_list
from pathlib import Path
import logging
from os import listdir
from os.path import isfile, join
import config
import youtube_dl
from pydub import AudioSegment
import os
import glob
import secrets
import datetime
import time
from discord.utils import get


TOKEN = config.TOKEN
# set global variables
intents = discord.Intents.default()
intents.presences = True
intents.members = True
client = Bot(command_prefix=config.BOT_PREFIX, intents=intents)
STREAM_PLAYER = None

# Classes

# create youtube source
youtube_dl.utils.bug_reports_message = lambda: ''


ytdl_format_options = {
    'format': 'bestaudio/best',
    'outtmpl': 'TemporaryAudio\\Youtube-%(title)s.%(ext)s',
    'restrictfilenames': True,
    'noplaylist': True,
    'nocheckcertificate': True,
    'ignoreerrors': False,
    'logtostderr': False,
    'quiet': True,
    'no_warnings': True,
    'default_search': 'auto',
    'source_address': '0.0.0.0',  # bind to ipv4 since ipv6 addresses cause issues sometimes
    'cachedir': False, # don't use local cache directory
}

ffmpeg_options = {
    'options': '-vn'
}

ytdl = youtube_dl.YoutubeDL(ytdl_format_options)


class YTDLSource(discord.PCMVolumeTransformer):
    def __init__(self, source, *, data, volume=0.5):
        super().__init__(source, volume)

        self.data = data
        self.title = data.get('title')
        self.url = data.get('url')
        self.duration = data.get('duration')

    @classmethod
    async def from_url(cls, url, *, loop=None, stream=False):
        loop = loop or asyncio.get_event_loop()
        data = await loop.run_in_executor(None, lambda: ytdl.extract_info(url, download=not stream))

        if 'entries' in data:
            # take first item from a playlist
            data = data['entries'][0]

        filename = data['url'] if stream else ytdl.prepare_filename(data)
        return cls(discord.FFmpegPCMAudio(filename, **ffmpeg_options), data=data)


# Command methods

async def clear_soundboard():
    """
    Function for clearing the soundboard channel
    :return:
    """
    # clear the soundboard channel and replace it with the updated list
    soundboard_channel = client.get_channel(config.SOUNDBOARD_CHANNEL_ID)
    msgs = await soundboard_channel.history(limit=1000).flatten()
    await soundboard_channel.delete_messages(msgs)
    # send a message to the soundboard channel for every file in the Audio directory
    only_files = [f for f in listdir('Audio/') if isfile(join('Audio/', f))]
    for file in only_files:
        file_name = file[:-4]
        await soundboard_channel.send(file_name)
    # get the play emoji
    play_emoji = soundboard_channel.guild.emojis[0]
    # get the new list of messages
    msgs = await soundboard_channel.history(limit=1000).flatten()
    # add the play emoji to each of the messages
    for msg in msgs:
        await msg.add_reaction(play_emoji)
    return


@client.command(
    name='clip',
    description='Clips a given youtube url into a mp3 file and adds it to the soundboard',
    pass_context=True,
)
async def clip(context, url, start_time, end_time, *args):
    """
    Clips a given youtube url into a mp3 file and adds it to the soundboard
    :param context: the context in which a command is being invoked under
    :param url: url of the youtube video that audio will be extracted from
    :param start_time: when the clip will begin in seconds
    :param end_time: when the clip will end in seconds
    :param args: the clip title
    :return:
    """
    if len(args) == 0:
        await context.message.channel.send("Failed to clip video: Clip must have a name.")
        return
    # format args into a single string
    name = ''
    for word in args:
        name = name + str(word) + ' '
    if len(name) > 0:
        name = name[:-1]
    parent_dir = config.AUDIO_DIRECTORY  # file path where the clip will be saved to
    filepath = parent_dir + str(name) + '.%(ext)s'  # the clip's complete file path
    ydl_opts = {
        'outtmpl': filepath,
        'format': 'bestaudio/best',
        'postprocessors': [{
            'key': 'FFmpegExtractAudio',
            'preferredcodec': 'mp3',
            'preferredquality': '192',
        }],

    }
    # download the audio for the entire video and save it
    with youtube_dl.YoutubeDL(ydl_opts) as ydl:
        ydl.download([url])
    audio = AudioSegment.from_mp3(parent_dir + str(name) + '.mp3')
    # clip the audio file between the start and end times and overwrite the file save
    start_time = float(start_time)
    end_time = float(end_time)
    start_time *= 1000
    end_time *= 1000
    extract = audio[start_time:end_time]
    extract.export(parent_dir + str(name) + '.mp3', format='mp3')
    # send a message letting the user know the file has been successfully downloaded
    await context.message.channel.send('Sound byte added')
    await clear_soundboard()
    return


@client.command(
    name='define',
    description='Defines a given word.',
    pass_context=True,
)
async def define(context, word):
    """
    Replies to a command call with a list of definitions for the word
    :param context: the context in which a command is being invoked under
    :param word: word to be defined
    :return:
    """
    dictionary = PyDictionary()
    if is_word(word) and not word.isdigit():
        try:
            # get a list of definitions for the given word
            definitions = dictionary.meaning(word)
            # sends a list of definitions separated into major word classes (noun, verb, adjective, adverb)
            for word_type in definitions:
                # send an initial message with the word class
                await context.message.channel.send('**' + word_type + ':**')
                index = 1
                # send all the definitions that fall under the specified word class
                for d in definitions[word_type]:
                    await context.message.channel.send('   ' + str(index) + '. ' + d)
                    index += 1
        except:
            await context.message.channel.send('A definition for '+word+' could not be found.')
    else:
        await context.message.channel.send('\"'+str(word)+'\" is not a word.')


@client.command(
    name='list_soundboard',
    description='Lists all of the possible soundboard options',
    pass_context=True,
)
async def list_soundboard(context):
    """
    Replies to the text channel with a list of all the sound bytes in the audio directory
    :param context: the context in which a command is being invoked under
    :return:
    """
    only_files = [f for f in listdir('Audio/') if isfile(join('Audio/', f))]
    for file in only_files:
        # exclude the file type from the message
        file_name = file[:-4]
        await context.message.channel.send(file_name)
    return


@client.command(
    name='notifications',
    description='Adds or removes the user from notifications when someone joins your channel while idle',
    pass_context=True,
)
async def notifications(context):
    guild = context.guild
    has_role = False
    for role in context.message.author.roles:
        if role.name == 'notifications':
            has_role = True
    if has_role:
        await context.message.author.remove_roles(get(guild.roles, name='notifications'))
        await context.message.channel.send('You will no longer receive notifications.')
    else:
        await context.message.author.add_roles(get(guild.roles, name='notifications'))
        await context.message.channel.send('You will now receive notifications if you are idle and someone joins your channel.')


@client.command(
    name='parrot',
    description='Converts arguments into speech and then plays that audio file in the user\'s voice channel.',
    pass_context=True,
)
async def parrot(context, *args):
    """
    Converts args into text to speak and then plays the message in whichever voice channel the user who called the
    command is in
    :param context: the context in which a command is being invoked under
    :param args: the phrase that the user wants to be converted to text to speech
    :return:
    """
    # format arguments into a single string
    phrase = ''
    for word in args:
        phrase = phrase + str(word) + ' '
    if len(phrase) > 0:
        phrase = phrase[:-1]
    # create a mp3 file with the phrase converted to text to speak
    language = 'en'
    phrase_mp3 = gTTS(text=phrase, lang=language, slow=False)
    phrase_mp3.save("TemporaryAudio\\parrot_command.mp3")
    # attempt to get the voice channel that the user is in
    voice_channel = None
    try:
        voice_channel = context.message.author.voice.channel
    except:
        await context.message.channel.send('User is not in a channel.')
    # only play the tts if user is in a voice channel
    if voice_channel is not None:
        # create StreamPlayer
        vc = await voice_channel.connect()
        vc.play(discord.FFmpegPCMAudio('TemporaryAudio\\parrot_command.mp3'), after=lambda e: print('done', e))
        # loop until the mp3 file is finished playing
        while vc.is_playing():
            await asyncio.sleep(1)
        # disconnect after the player has finished
        vc.stop()
        await vc.disconnect()
    # delete the mp3 file once it has finished playing
    if os.path.exists("TemporaryAudio\\parrot_command.mp3"):
        os.remove("TemporaryAudio\\parrot_command.mp3")
    else:
        print("File does not exist.")


@client.command(
    name='pause',
    description='Pauses Fame\'s audio stream.',
    pass_context=True,
)
async def pause(context):
    global STREAM_PLAYER
    if STREAM_PLAYER is not None:
        # if audio is playing, pause it. otherwise resume the audio
        if STREAM_PLAYER.is_playing():
            STREAM_PLAYER.pause()
        else:
            STREAM_PLAYER.resume()


@client.command(
    name='play',
    description='Plays the audio from a specified youtube link. '
                'If the link is not a valid youtube url it will search youtube and play the first result.',
    pass_context=True,
)
async def play(context, url, *args):
    global STREAM_PLAYER
    # if the user is not in a voice channel, abort
    if context.message.author.voice is None:
        await context.message.channel.send('User is not in a channel.')
        return
    # if the user did not enter a url and instead entered a string of text, search it in youtube
    # and return the first result
    if 'https://youtube.com/' not in url:
        search = url
        for arg in args:
            search = search + ' ' + arg
        query_string = urllib.parse.urlencode({"search_query": search})
        html_content = urllib.request.urlopen("http://www.youtube.com/results?" + query_string)
        search_results = re.findall(r'/watch\?v=(.{11})', html_content.read().decode())
        url = "http://www.youtube.com/watch?v=" + search_results[0]
    # get the voice channel that the user who called the play function is in
    voice_channel = context.message.author.voice.channel
    # if the bot is already playing in a channel, add the url to the queue
    if context.voice_client is not None:
        # await context.message.channel.send('Song has been added to queue.')
        return
        # TODO: create a queue system for songs
    # join the voice channel
    voice_client = await voice_channel.connect()
    # create a player
    player = await YTDLSource.from_url(url, loop=client.loop)
    STREAM_PLAYER = context.voice_client
    # begin playing music in the channel
    context.voice_client.play(player, after=lambda e: print('Player error: %s' % e) if e else None)
    start_time = datetime.datetime.now()
    player_duration =time.strftime('%M:%S', time.gmtime(player.duration))
    # send a message with information about the link being played
    embed = discord.Embed(title=player.title)
    embed.add_field(name='Video URL', value=url)
    embed.add_field(name='Duration', value=("00:00/"+player_duration))
    msg = await context.message.channel.send(embed=embed)
    # get the channel's emojis
    soundboard_channel = client.get_channel(config.SOUNDBOARD_CHANNEL_ID)
    emojis = soundboard_channel.guild.emojis
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
            embed.add_field(name='Duration', value=(str(current_time)[2:-7] + "/" + player_duration))
            await msg.edit(embed=embed)
        else:
            await asyncio.sleep(1)
            pause_loop_counter += 1

    # disconnect from channel
    voice_client.stop()
    await voice_client.disconnect()
    STREAM_PLAYER = None
    # delete audio file after it is finished playing
    files = glob.glob("TemporaryAudio/*")
    for f in files:
        if 'Youtube-' in f.title():
            os.remove(f.title())


@client.command(
    name='reader',
    description='Converts a reddit text post into tts and then reads it in a discord channel',
    pass_context=True,
)
async def reader(context, url):
    return


@client.command(
    name='clear',
    description='Attempts to revive a server by pinging users a set number of times',
    pass_context=True,
)
async def rescue_server(context, num_people, voltage):
    try:
        members = context.guild.members
        members_pinged = []
        while len(members_pinged) < int(num_people) and len(members) > 0:
            person = secrets.choice(members)
            members_pinged.append(person)
            members.remove(person)
        pings = int(re.findall(r'\d+', voltage)[0])
        if pings < 100:
            await context.message.channel.send('Voltage too low!')
            return
        if pings > 1000:
            await context.message.channel.send('Voltage is too high you madman!')
            return
        i = 0
        while i < (pings / 100):
            for member in members_pinged:
                await context.message.channel.send(member.mention)
            i += 1
        return
    except:
        await context.message.channel.send('You\'re no doctor!')
        return


@client.command(
    name='roll',
    description='Rolls dice. Format is [Number of dice to be rolled]d[Max value of dice]',
    pass_context=True,
)
async def roll(context, die):
    """
    Simulates a dice roll.
    :param context: the context in which a command is being invoked under
    :param die: string containing the number of dice to be rolled as well as the max value of the individual die.
    mirrors roll20.net's format for rolling dice
    :return:
    """
    # extract the number of dice and max value from the die argument
    num_die = die.split('d')[0]
    max_val = die.split('d')[1]
    results = []
    total = 0  # combined total of all dice rolls
    # exit condition for if the user tries a roll that would result in a non positive number
    if int(num_die) <= 0 or int(max_val) < 1:
        await context.message.channel.send('Not a valid combination.')
        return
    # roll a random number
    for die in range(1, int(num_die)+1):
        # calculate a random number between 1 and the max_val (inclusive)
        x = random.randrange(1, int(max_val)+1)
        results.append(x)
        # add the number to the total
        total += x
    # create an output message where you can see all the individual rolls and the total
    msg = ''
    for result in results:
        msg += str(result)+' + '
    if msg.endswith(' + '):
        msg = msg[:-3]
    await context.message.channel.send(msg)
    await context.message.channel.send('Total is: '+str(total))


@client.command(
    name='soundboard',
    description='plays a sound from the list of previously saved mp3s',
    pass_context=True,
)
async def soundboard(context, *args):
    """
    Plays a sound from the list of previously saved mp3s in the voice channel that the user who called the command
    is in.
    :param context: the context in which a command is being invoked under
    :param args: the title of the sound byte to be played
    :return:
    """
    # get the full mp3 file name
    mp3_file_name = 'Audio/'
    for arg in args:
        mp3_file_name += arg+' '
    if mp3_file_name.endswith(' '):
        mp3_file_name = mp3_file_name[:-1]
    mp3_file_name += '.mp3'
    mp3_file_name = mp3_file_name.lower()

    # grab the user who sent the command
    voice_channel = None
    try:
        voice_channel = context.message.author.voice.channel
    except:
        await context.message.channel.send('User is not in a channel.')
        return

    # check if a file with the given name exists
    only_files = [f for f in listdir('Audio/') if isfile(join('Audio/', f))]
    file_exists = False
    for file in only_files:
        test_file_name = 'audio/'+file
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
    else:
        await context.message.channel.send('User is not in a channel or file doesnt exist.')


@client.command(
    name='stock',
    description='Grabs the current price of a given stock',
    pass_context=True,
)
async def stock(context, acronym):
    """
    Given a company's ticker, replies with its current stock price.
    :param context: the context in which a command is being invoked under
    :param acronym: a company's ticker symbol (i.e. AAPL or AMZN)
    :return:
    """
    try:
        # checks the current price of the stock using yahoo finance
        price = str(round(get_live_price(acronym), 2))
        company_name = get_company_name(acronym)
        await context.message.channel.send('The current price of ' + company_name + ' stock is $'+price)
    except:
        # if the method cant find the stock it throws an error
        await context.message.channel.send('Not a valid ticker.')


@client.command(
    name='stop',
    description='Immediately stops whatever audio piper is playing and disconnects piper from the channel',
    pass_context=True
)
async def stop(context):
    global STREAM_PLAYER
    # if the bot is in a voice channel, disconnect
    if context.voice_client is not None:
        await context.voice_client.disconnect()
        STREAM_PLAYER = None


@client.command(
    name='update-intro',
    description='Updates or creates a user\'s intro soundbyte.',
    pass_context=True,
)
async def update_intro(context, url=None, start_time=None, end_time=None):
    """
    Updates a user's intro sound byte
    :param context: the context in which a command is being invoked under
    :param url: optional parameter
    :param start_time: when the clip will begin in seconds
    :param end_time: when the clip will end in seconds
    :return:
    """
    # if the user uploads an mp3 file
    if url is None:
        intro = 'Intro/' + context.message.author.name + '.mp3'  # file path where the intro will be saved to
        # save the mp3 file
        await context.message.attachments[0].save(intro)
        return
    # if the user wants to update their intro using a youtube url
    if url is not None and start_time is not None and end_time is not None:
        parent_dir = config.INTRO_DIRECTORY  # file path where the intro will be saved to
        filepath = parent_dir + str(context.message.author.name) + '.%(ext)s'  # the intro's complete file path
        ydl_opts = {
            'outtmpl': filepath,
            'format': 'bestaudio/best',
            'postprocessors': [{
                'key': 'FFmpegExtractAudio',
                'preferredcodec': 'mp3',
                'preferredquality': '192',
            }],

        }
        # download the audio for the entire video and save it
        with youtube_dl.YoutubeDL(ydl_opts) as ydl:
            ydl.download([url])
        audio = AudioSegment.from_mp3(parent_dir + str(context.message.author.name) + '.mp3')
        # clip the audio file between the start and end times and overwrite the file save
        start_time = float(start_time)
        end_time = float(end_time)
        start_time *= 1000
        end_time *= 1000
        extract = audio[start_time:end_time]
        extract.export(parent_dir + str(context.message.author.name) + '.mp3', format='mp3')
        # send a message letting the user know the file has been successfully downloaded
        await context.message.channel.send('User Intro has been updated')
        return


@client.command(
    name='upload-mp3',
    description='Uploads a new mp3 file to the soundboard. To use: \"!piper upload_soundboard <title>\"',
    pass_context=True,
)
async def upload_mp3(context, *args):
    """
    Upload a mp3 file to the soundboard.
    :param context: the context in which a command is being invoked under
    :param args: the title for the saved mp3 file
    :return:
    """
    # only run if there is an attachment to the message
    if len(context.message.attachments) > 0:
        # create a relative file path to save the mp3 file to
        mp3_file_name = 'Audio/'
        for arg in args:
            mp3_file_name += arg + ' '
        if mp3_file_name.endswith(' '):
            mp3_file_name = mp3_file_name[:-1]
        mp3_file_name += '.mp3'
        mp3_file_name = mp3_file_name.lower()
        # save the mp3 file
        await context.message.attachments[0].save(mp3_file_name)
        await context.message.channel.send('Mp3 file added to soundboard.')
        await clear_soundboard()
    return


@client.command(
    name='urban-define',
    description='Scrapes urban dictionary for the definition of a given phrase.',
    pass_context=True
)
async def urban_define(context, *args):
    """
    Replies to a command call with an urban dictionary definition of *args
    :param context: the context in which a command is being invoked under
    :param args: the phrase to be search urban dictionary for
    :return:
    """
    # format the arguments for searching
    phrase = ''
    for word in args:
        phrase = phrase+str(word)+'+'
    if len(phrase) > 0:
        phrase = phrase[:-1]
    url = 'http://api.urbandictionary.com/v0/define?term='+phrase
    phrase = phrase.replace('+', ' ')
    response = urllib.request.urlopen(url)
    # get the json response containing the definition
    data = json.loads(response.read())
    # if a definition was found extract it into a readable format
    if len(data['list']) > 0:
        definition = data['list'][0]['definition']
        definition = definition.replace('[', '')
        definition = definition.replace(']', '')
        # reply to the command call with the definition
        await context.message.channel.send('**'+phrase+'**: '+definition)
    else:
        await context.message.channel.send('No definition found for ' + phrase + '.')


@client.command(
    name='urban-random',
    description='Gives a random urban dictionary definition.',
    pass_context=True
)
async def urban_random(context):
    """
    Replies to a command call with a random urban dictionary definition
    :param context: the context in which a command is being invoked under
    :return:
    """
    # make a json request for a random urban dictionary definition
    url = 'https://api.urbandictionary.com/v0/random'
    verify = ssl._create_unverified_context()
    response = urllib.request.urlopen(url, context=verify)
    # get the json response containing the definition
    data = json.loads(response.read())
    # if a definition was found extract it into a readable format
    if len(data['list']) > 0:
        definition = data['list'][0]['definition']
        definition = definition.replace('[', '')
        definition = definition.replace(']', '')
        # reply to the call with a definition
        await context.message.channel.send('**'+data['list'][0]['word']+'**: '+definition)
    else:
        # if no definition was found reply with an error message
        await context.message.channel.send('An error has occurred, try again.')


@client.command(
    name='volume',
    description='Change the volume that Piper is playing the current song at.',
    pass_context=True,
)
async def volume(context, vol):
    global STREAM_PLAYER
    if STREAM_PLAYER is not None:
        STREAM_PLAYER.source.volume = int(vol)/100


# On event methods
@client.event
async def on_message(message):
    """
    Event that happens when a user sends a message to a text channel
    :param message:
    :return:
    """
    text = message.content.lower()
    if 'bad bot' == text:
        config.BAD_BOT += 1
        msg = 'Thank you for your feedback, I have been called a naughty bot ' + str(config.BAD_BOT) + ' times.'
        await message.channel.send(msg)
    elif 'good bot' == text:
        config.GOOD_BOT += 1
        msg = 'Thank you for your feedback! I have been called a good bot ' + str(config.GOOD_BOT) + ' times!'
        await message.channel.send(msg)
    await client.process_commands(message)


@client.event
async def on_voice_state_update(member, before, after):
    """
    Event that happens when a user changes their voice state
    :param member: user who has updated their voice state
    :param before: previous voice state
    :param after: current voice state
    :return:
    """
    # only if the user who's voice state updated is not a bot and the bot is not already connected to the server
    if not member.bot and len(client.voice_clients) == 0:
        before_channel = before.channel
        after_channel = after.channel
        if before_channel != after_channel and after_channel is not None and before_channel is None:
            # check if a sound byte for the user exists
            path = 'Intro/'+member.name+'.mp3'
            file_check = Path(path)
            if file_check.exists():
                channel = client.get_channel(after_channel.id)
                # create StreamPlayer
                vc = await channel.connect()
                vc.play(discord.FFmpegPCMAudio(path))
                # loop until the mp3 file is finished playing
                while vc.is_playing():
                    await asyncio.sleep(1)
                # disconnect after the player has finished
                vc.stop()
                await vc.disconnect()
        if before_channel != after_channel and after_channel is None and before_channel is not None:
            language = 'en'
            phrase = member.name + ' left'
            phrase_mp3 = gTTS(text=phrase, lang=language, slow=False)
            phrase_mp3.save("TemporaryAudio\\outro.mp3")
            channel = client.get_channel(before_channel.id)
            vc = await channel.connect()
            vc.play(discord.FFmpegPCMAudio('TemporaryAudio\\outro.mp3'), after=lambda e: print('done', e))
            # loop until the mp3 file is finished playing
            while vc.is_playing():
                await asyncio.sleep(1)
            # disconnect after the player has finished
            vc.stop()
            await vc.disconnect()
            # delete the outro file once it has finished playing
            if os.path.exists("TemporaryAudio\\outro.mp3"):
                os.remove("TemporaryAudio\\outro.mp3")
            else:
                print("File does not exist")
    if after.channel is not None and not member.bot and before.channel is not after.channel:
        for connected_user in after.channel.members:
            print(connected_user.status)
            for role in connected_user.roles:
                if role.name == 'notifications' and connected_user is not member and connected_user.status == discord.Status.idle:
                    await connected_user.send('{user} joined the channel while you were away'.format(user=member.name))


    return


@client.event
async def on_reaction_add(reaction, user):
    await when_reaction(reaction, user)


@client.event
async def on_reaction_remove(reaction, user):
    await when_reaction(reaction, user)


async def when_reaction(reaction, user):
    global STREAM_PLAYER
    soundboard_channel = client.get_channel(config.SOUNDBOARD_CHANNEL_ID)
    play_emoji = soundboard_channel.guild.emojis[0]
    play_pause_emoji = soundboard_channel.guild.emojis[1]
    stop_emoji = soundboard_channel.guild.emojis[2]
    down_emoji = soundboard_channel.guild.emojis[3]
    up_emoji = soundboard_channel.guild.emojis[4]
    if reaction.message.channel is soundboard_channel and not user.bot and user.voice is not None:
        voice_channel = user.voice.channel
        mp3_file_name = 'Audio/' + reaction.message.content + '.mp3'
        # check if a file with the given name exists
        only_files = [f for f in listdir('Audio/') if isfile(join('Audio/', f))]
        file_exists = False
        for file in only_files:
            test_file_name = 'Audio/' + file
            if mp3_file_name == test_file_name:
                file_exists = True
        # only play music if user is in a voice channel
        if voice_channel is not None and file_exists:
            # create StreamPlayer
            vc = await user.voice.channel.connect()
            vc.play(discord.FFmpegPCMAudio(mp3_file_name), after=lambda e: print('done', e))
            # loop until the mp3 file is finished playing
            while vc.is_playing():
                await asyncio.sleep(1)
            # disconnect after the player has finished
            vc.stop()
            await vc.disconnect()
    if not user.bot and user.voice is not None and STREAM_PLAYER is not None:
        # pause / resume audio if user reacts with the play pause emoji
        if reaction.emoji is play_pause_emoji:
            if STREAM_PLAYER.is_playing():
                STREAM_PLAYER.pause()
            else:
                STREAM_PLAYER.resume()
        if reaction.emoji is stop_emoji:
            await STREAM_PLAYER.disconnect()
            STREAM_PLAYER = None
        if reaction.emoji is down_emoji and STREAM_PLAYER.source.volume > 0.0:
            STREAM_PLAYER.source.volume -= 0.1
        if reaction.emoji is up_emoji and STREAM_PLAYER.source.volume < 1.0:
            STREAM_PLAYER.source.volume += 0.1
    return


@client.event
async def on_ready():
    """
    Displays a short message in the console when the bot is initially run
    :return:
    """
    print('Logged in as')
    print(client.user.name)
    print(client.user.id)
    # clear all the messages in the soundboard channel
    # await clear_soundboard()
    print('------')


# code for logging errors and debug errors to the file discord.log
logger = logging.getLogger('discord')
logger.setLevel(logging.DEBUG)
handler = logging.FileHandler(filename='discord.log', encoding='utf-8', mode='w')
handler.setFormatter(logging.Formatter('%(asctime)s:%(levelname)s:%(name)s: %(message)s'))
logger.addHandler(handler)

client.run(TOKEN)
