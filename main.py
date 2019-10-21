import discord
import config
from discord.ext.commands import Bot

client = Bot(command_prefix=config.BOT_PREFIX)


@client.command(
    name='ping',
    description='Returns a response',
    pass_context=True,
)
async def ping(context):
    await context.message.channel.send('pong')


@client.event
async def on_ready():
    print('We have logged in as {0.user}'.format(client))
    print('------------------------------')

@client.event
async def on_message(message):
    await client.process_commands(message)

client.run(config.TOKEN)