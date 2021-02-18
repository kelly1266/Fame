import asyncio
from quart import Quart
import config
from app import DiscordClient
from quart import request, jsonify, render_template
from os import listdir
from os.path import isfile, join, dirname, abspath


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
    user = request.args.get('user')
    params = {
        "user":user,
        "sound":sound
    }
    await QUART_APP.discord_client.soundboard(sound, user)
    return jsonify(**params)


QUART_APP.run(host=config.HOST, port=config.PORT)
