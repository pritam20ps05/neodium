import asyncio
import discord
import tekore as tk
from .download import YDL_OPTIONS
from os import environ
from yt_dlp import YoutubeDL
from discord.ext import commands

client_id = environ['SPOTIFY_CLIENT_ID']
client_secret = environ['SPOTIFY_CLIENT_SECRET']

token = tk.request_client_token(client_id, client_secret)
spotify = tk.Spotify(token, asynchronous=True)

class SpotifyClient():
    def getID(self, url: str, rtype: str):
        return url.split(f'{rtype}/')[1].split('?')[0]

    def getURL(self, URI: str):
        rtype, rid = URI.split(':')[1:]
        return f'https://open.spotify.com/{rtype}/{rid}'

    async def addSongs(self, playlist_tracks: list[tk.model.PlaylistTrack], queue, ctx: commands.Context):
        for track in playlist_tracks:
            track = track.track
            if track.track:
                with YoutubeDL(YDL_OPTIONS) as ydl:
                    query = f'{track.artists[0].name} - {track.name} official audio'.replace(":", "").replace("\"", "")
                    info = ydl.extract_info(f'ytsearch:{query}', download=False)
                info = info['entries'][0]
                queue.append({
                    "link": info['url'],
                    "url": self.getURL(track.uri),
                    "title": track.name,
                    "thumbnails": [track.album.images[0].__dict__]
                })
            await asyncio.sleep(2)
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