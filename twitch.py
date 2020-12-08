import configparser
import os
from datetime import datetime

import requests

config = configparser.ConfigParser()
config.read("config.txt")

clientID = config["twitch.com"]["TWITCH_CLIENT_ID"]
clientSecret = config["twitch.com"]["TWITCH_SECRET_ID"]

def _get_top_channels_raw(game_id, maxLength=5):
    "Get top channels based on game_id"

    oauthURL = 'https://id.twitch.tv/oauth2/token'
    data = {'client_id': clientID, 'client_secret': clientSecret, 'grant_type': 'client_credentials'}
    r = requests.post(oauthURL, data=data)
    access_token = r.json()['access_token']

    headers = {'Client-ID': clientID, 'Authorization': 'Bearer ' + access_token}

    top_channels = []

    # Getting top channels based on url
    stream_api_url = f"https://api.twitch.tv/helix/streams?game_id={game_id}&first={maxLength}"
    r = requests.get(stream_api_url, headers=headers)
    channels = r.json()

    if "data" not in channels:
        return top_channels
    else:
        channels = channels["data"]
    
    # Getting user_ids based on channels
    # Need to make additional request to user endpoint since user_name is not display name
    # Reference: https://github.com/twitchdev/issues/issues/3
    user_ids = [stream["user_id"] for stream in channels]
    user_api_url = f"https://api.twitch.tv/helix/users?id={'&id='.join(user_ids)}"
    r = requests.get(user_api_url, headers=headers)
    users = r.json()

    if "data" not in users:
        return top_channels
    else:
        users = users["data"]

    for stream, user in zip(channels, users):
        viewers = stream["viewer_count"]
        status = stream["title"]
        name = stream["user_name"]
        user_id = stream["user_id"]
        login_name = user["login"]
        streamer_url = "https://www.twitch.tv/" + login_name

        # Correcting status for display in Markdown
        if '`' in status:
            status = status.replace("`", "\`")
        if '[' in status:
            status = status.replace("[", "\[")
        if ']' in status:
            status = status.replace("]", "\]")
        if '\r' in status:
            status = status.replace("\r", '')
        if '\n' in status:
            status = status.replace("\n", '')

        sidebar_channel = {
            "name": name, 
            "status": status,
            "viewers": viewers, 
            "url": streamer_url
        }
        top_channels.append(sidebar_channel)

    return top_channels

def get_top_channels_raw(sub, maxLength=5):
    "Returns list of channels based on subreddit."
    
    try:
        return _get_top_channels_raw(config['game-ids'][sub.display_name.lower()], maxLength)
    except Exception:
        return []
