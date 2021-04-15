import asyncio
from quart import Quart
import config
from app import DiscordClient
from quart import request, jsonify, render_template
from os import listdir
from os.path import isfile, join, dirname, abspath
import requests


QUART_APP = Quart(__name__)


@QUART_APP.before_serving
async def before_serving():
    loop = asyncio.get_event_loop()
    QUART_APP.discord_client = DiscordClient()
    await QUART_APP.discord_client.bot.login(config.TOKEN)
    loop.create_task(QUART_APP.discord_client.bot.connect())


@QUART_APP.route("/")
async def index():
    sounds=[]
    directory = dirname(dirname(abspath(__file__))) + "\\Audio\\"
    only_files = [f for f in listdir(directory) if isfile(join(directory, f))]
    for file in only_files:
        # exclude the file type from the message
        file_name = file[:-4]
        sounds.append(file_name)
    return await render_template("soundboard.html", sounds=sounds)


@QUART_APP.route("/soundboard/<string:sound>")
async def soundbaord(sound):
    sound = requests.utils.unquote(sound)
    print("sound: " + sound)
    user = request.args.get('user')
    params = {
        "user":user,
        "sound":sound
    }
    await QUART_APP.discord_client.soundboard(sound, user)
    return jsonify(**params)


@QUART_APP.route("/play")
async def play():
    user = request.args.get('user')
    youtube_url = request.args.get('youtubeURL')
    params = {
        "user": user,
        "youtubeURL":youtube_url
    }
    await QUART_APP.discord_client.play(youtube_url, user)
    return jsonify(**params)


@QUART_APP.route("/stop")
async def stop():
    params = {
    }
    await QUART_APP.discord_client.stop()
    return jsonify(**params)


@QUART_APP.route("/pause")
async def pause():
    params = {
    }
    await QUART_APP.discord_client.pause()
    return jsonify(**params)


@QUART_APP.route("/volume")
async def volume():
    vol = request.args.get('vol')
    params = {
        "volume":vol
    }
    await QUART_APP.discord_client.volume(vol)
    return jsonify(**params)


@QUART_APP.route("/volumedown")
async def volumedown():
    params = {

    }
    await QUART_APP.discord_client.volumedown()
    return jsonify(**params)


@QUART_APP.route("/volumeup")
async def volumeup():
    params = {

    }
    await QUART_APP.discord_client.volumeup()
    return jsonify(**params)


QUART_APP.run()
