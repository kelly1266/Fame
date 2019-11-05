import asyncio
import re
import requests
from gtts import gTTS

# Helper Methods


def spellbreak_key(code):
    return re.match(r'[A-Z0-9][A-Z0-9][A-Z0-9]-[A-Z0-9][A-Z0-9][A-Z0-9]-[A-Z0-9][A-Z0-9][A-Z0-9]', code)


def is_word(word):
    """
    checks whether or not the parameter word is in the dictionary
    :param word:
    :return: whether it is in the dictionary or not
    """
    return True


def is_int(number):
    try:
        int(number)
        return True
    except:
        return False


def get_company_name(acronym):
    """
    Retrieves the name of a company from yahoo finance given its ticker.
    :param acronym: company's stock market ticker
    :return: company name
    """
    url = "http://d.yimg.com/autoc.finance.yahoo.com/autoc?query={}&region=1&lang=en".format(acronym)
    result = requests.get(url).json()
    for x in result['ResultSet']['Result']:
        if x['symbol'] == acronym:
            return x['name']


def scrape_jokes(subreddit):
    return


# TODO: rewrite the dictate command
async def dictate(context, phrase, vc):
    language = 'en'
    phrase_mp3 = gTTS(text=phrase, lang=language, slow=False)
    phrase_mp3.save("fame_dialogue.mp3")
    # grab the user who sent the command
    user = context.message.author
    voice_channel = user.voice.voice_channel
    channel = None
    # only play music if user is in a voice channel
    if voice_channel != None:
        # grab user's voice channel
        channel = voice_channel.name
        # create StreamPlayer
        player = vc.create_ffmpeg_player('fame_dialogue.mp3', after=lambda: print('done'))
        player.start()
        while not player.is_done():
            await asyncio.sleep(1)
        # disconnect after the player has finished
        player.stop()
    return
