import requests
import config

url = "https://discord.com/api/v8/applications/" + config.BOT_CLIENT_ID + "/guilds/" + config.GUILD_ID + "/commands"


json = {
    "name": "clip",
    "description": "Clips a given youtube url into a mp3 file and adds it to the soundboard",
    "options": [
        {
            "name": "url",
            "description": "URL of youtube clip",
            "type": 3,
            "required": True
        },
        {
            "name": "start_time",
            "description": "start time",
            "type": 4,
            "required": True
        },
        {
            "name": "end_time",
            "description": "end time",
            "type": 4,
            "required": True
        },
        {
            "name": "title",
            "description": "title",
            "type": 3,
            "required": True
        }

    ]
}

headers = {
    "Authorization": ("Bot " + config.TOKEN)
}

r = requests.post(url, headers=headers, json=json)

