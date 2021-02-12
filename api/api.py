import asyncio
from quart import Quart
import config
from app import DiscordClient
from quart import request
from quart import jsonify

QUART_APP = Quart(__name__)


@QUART_APP.before_serving
async def before_serving():
    loop = asyncio.get_event_loop()
    QUART_APP.discord_client = DiscordClient()
    await QUART_APP.discord_client.bot.login(config.TOKEN)
    loop.create_task(QUART_APP.discord_client.bot.connect())


@QUART_APP.route("/")
async def hello_world():
    return "Hello World"


@QUART_APP.route("/soundboard/<string:sound>")
async def soundbaord(sound):
    user = request.args.get('user')
    params = {
        "user":user,
        "sound":sound
    }
    await QUART_APP.discord_client.soundboard(sound, user)
    return jsonify(**params)

host = "127.0.0.1"
port = "5000"
QUART_APP.run(host=host, port=port)
