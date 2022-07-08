"""
copyright (c) 2021  pritam20ps05(Pritam Das)

    This program is free software: you can redistribute it and/or modify
    it under the terms of the GNU General Public License as published by
    the Free Software Foundation, either version 3 of the License, or
    (at your option) any later version.

    This program is distributed in the hope that it will be useful,
    but WITHOUT ANY WARRANTY; without even the implied warranty of
    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
    GNU General Public License for more details.
"""
from os import environ

token = environ["TOKEN"]
search_engine = environ["SEARCH_ENGINE"]
search_token = environ["SEARCH_TOKEN"]
yt_file_id = environ['YT_COOKIEFILE_ID']
ig_file_id = environ['INSTA_COOKIEFILE_ID']
client_id = environ['SPOTIFY_CLIENT_ID']
client_secret = environ['SPOTIFY_CLIENT_SECRET']

YDL_OPTIONS = {
    'format': 'bestaudio', 
    'noplaylist': 'True', 
    'source_address': '0.0.0.0',
    "cookiefile": "yt_cookies.txt"
}

FFMPEG_OPTIONS = {
    'before_options': '-reconnect 1 -reconnect_streamed 1 -reconnect_delay_max 5', 
    'options': '-vn'
}