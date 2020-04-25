import asyncio
import re
import requests
from gtts import gTTS

# Helper Methods


# TODO: write function that determines if the parameter word is a word or not
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

