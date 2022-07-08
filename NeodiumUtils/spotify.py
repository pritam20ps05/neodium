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
import discord
import tekore as tk
from discord.ext import commands
from yt_dlp import YoutubeDL
from .download import ydl_async
from .vars import *

token = tk.request_client_token(client_id, client_secret)
spotify = tk.Spotify(token, asynchronous=True)

class SpotifyClient():
    def getID(self, url: str, rtype: str):
        return url.split(f'{rtype}/')[1].split('?')[0]

    def getURL(self, URI: str):
        rtype, rid = URI.split(':')[1:]
        return f'https://open.spotify.com/{rtype}/{rid}'

    async def addSongs(self, playlist_tracks: list[tk.model.PlaylistTrack], queue, ctx: commands.Context):
        for i, track in enumerate(playlist_tracks):
            track = track.track
            if track.track:
                query = f'{track.artists[0].name} - {track.name} official audio'.replace(":", "").replace("\"", "")
                if i == 0:
                    with YoutubeDL(YDL_OPTIONS) as ydl:
                        info = ydl.extract_info(f'ytsearch:{query}', download=False)
                else:
                    info = await ydl_async(f'ytsearch:{query}', YDL_OPTIONS, False)
                info = info['entries'][0]
                queue.append({
                    "link": info['url'],
                    "url": self.getURL(track.uri),
                    "title": f'{track.name} - {track.artists[0].name}',
                    "thumbnails": [track.album.images[0].__dict__]
                })
        embed=discord.Embed(title="Playlist items were added to queue", color=0xfe4b81)
        await ctx.send(embed=embed)

    async def getPlaylist(self, playlist_url: str, ctx: commands.Context, sp: int, ep: int):
        playlist_info = await spotify.playlist(self.getID(playlist_url, 'playlist'))
        playlist_thumbnail = playlist_info.images[0].url
        playlist_title = playlist_info.name
        playlist_description = playlist_info.description
        playlist_url = self.getURL(playlist_info.uri)
        playlist_tracks = playlist_info.tracks.items[sp:ep]
        
        if sp or ep:
            if ep:
                embed=discord.Embed(title="Adding Playlist", description=f'[{playlist_title}]({playlist_url})\n{playlist_description}\n\n**From {sp+1} to {ep}**', color=0xfe4b81)
            else:
                embed=discord.Embed(title="Adding Playlist", description=f'[{playlist_title}]({playlist_url})\n{playlist_description}\n\n**From {sp+1} to {len(playlist_tracks)+sp}**', color=0xfe4b81)
        else:
            embed=discord.Embed(title="Adding Playlist", description=f'[{playlist_title}]({playlist_url})\n{playlist_description}', color=0xfe4b81)
        embed.set_thumbnail(url=playlist_thumbnail)
        embed.set_author(name='Spotify', icon_url='https://user-images.githubusercontent.com/49360491/177480503-96f98632-33a3-4884-a20e-572c13580bc9.png')
        await ctx.send(embed=embed)
        return playlist_tracks