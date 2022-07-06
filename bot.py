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
import asyncio
import re
from os import environ
from random import shuffle
from discord.ext import commands
from discord.utils import get
from discord import FFmpegPCMAudio
from DiscordUtils.Pagination import CustomEmbedPaginator as EmbedPaginator
from yt_dlp import YoutubeDL, utils
from lyrics_extractor import SongLyrics, LyricScraperException
from NeodiumUtils import *

FFMPEG_OPTIONS = {
    'before_options': '-reconnect 1 -reconnect_streamed 1 -reconnect_delay_max 5', 
    'options': '-vn'
    }

getCookieFile()

token = environ["TOKEN"]
search_engine = environ["SEARCH_ENGINE"]
search_token = environ["SEARCH_TOKEN"]

activity = discord.Activity(type=discord.ActivityType.listening, name="-help")
client = commands.Bot(command_prefix='-', activity=activity, help_command=NeodiumHelpCommand())  # prefix our commands with '-'
lyrics_api = SongLyrics(search_token, search_engine)
spotify_api = SpotifyClient()
yt_dl_instance = YTdownload(client)
in_dl_instance = INSdownload(client)
private_instance = private_login('login.json')

player = {}
masters = {}
queues = {}
queuelocks = {}


def initGuilds():
    for guild in client.guilds:
        player[guild.id] = {}
        queues[guild.id] = []
        queuelocks[guild.id] = {}
        queuelocks[guild.id]["lock"] = False



class QueueLockCheckFailure(commands.CheckFailure):
    def __init__(self, message=None):
        super().__init__(message)

def checkQueueLock(hard=False, check_if_bot_connected=False):
    async def predicate(ctx):
        voice = get(client.voice_clients, guild=ctx.guild)
        if voice or not check_if_bot_connected:
            if ctx.guild.id in queuelocks.keys() and queuelocks[ctx.guild.id]["lock"] and queuelocks[ctx.guild.id]["author"].voice and queuelocks[ctx.guild.id]["author"].voice.channel == voice.channel and not (not (voice.is_playing() or voice.is_paused()) and queues[ctx.guild.id] == []): 
                if queuelocks[ctx.guild.id]["author"] == ctx.message.author and not hard:
                    return True
                else:
                    raise QueueLockCheckFailure("The queue is currently locked")
            else:
                queuelocks[ctx.guild.id] = {}
                queuelocks[ctx.guild.id]["lock"] = False
                return True
        else:
            raise QueueLockCheckFailure("I am currently not connected to any voice channel")
    return commands.check(predicate)


# main queue manager function to play music in queues
async def check_queue(id, voice, ctx, msg=None):
    while True:
        while voice.is_playing() or voice.is_paused():
            await asyncio.sleep(5)
        if msg:
            await msg.delete()
        if queues[id] != [] and not (voice.is_playing() or voice.is_paused()):
            current = queues[id].pop(0)
            player[ctx.guild.id] = current
    
            embed=discord.Embed(title="Currently Playing", description=f'[{player[id]["title"]}]({player[id]["url"]})', color=0xfe4b81)
            embed.set_thumbnail(url=player[id]["thumbnails"][len(player[id]["thumbnails"])-1]["url"])
    
            voice.play(FFmpegPCMAudio(player[id]["link"], **FFMPEG_OPTIONS))
            msg = await ctx.send(embed=embed)
            await asyncio.sleep(1)
    
            # if anyhow system fails to play the audio it tries to play it again
            while not(voice.is_playing() or voice.is_paused()):
                info = await ydl_async(player[id]["url"], YDL_OPTIONS, False)
                player[id]["link"] = info['url']
                voice.play(FFmpegPCMAudio(player[id]["link"], **FFMPEG_OPTIONS))
                await asyncio.sleep(1)
    
        else:
            player[ctx.guild.id] = {}
            break



# a asyncronus function to get video details because normally some timeout issue occurs but this is slower
async def addsongs(entries, ctx):
    for song in entries:
        url = song["url"]
        try:
            with YoutubeDL(YDL_OPTIONS) as ydl:
                info = ydl.extract_info(url, download=False)
            
            data = {
                "link": info['url'],
                "url": url,
                "title": info['title'],
                "thumbnails": info["thumbnails"]
            }
            queues[ctx.guild.id].append(data)
        except Exception as e:
            print(e)
        await asyncio.sleep(2)
    embed=discord.Embed(title="Playlist items were added to queue", color=0xfe4b81)
    await ctx.send(embed=embed, delete_after=10)



# check if bot is ready
@client.event  
async def on_ready():
    print('Bot online')
    initGuilds()


class BasicCommands(commands.Cog, name="Basic", description="This category of commands contains the basic functionalities of the bot such as joining a VC."):
    def __init__(self, bot: commands.Bot):
        self.bot = bot


    # command for bot to join the channel of the user, if the bot has already joined and is in a different channel, it will move to the channel the user is in
    @commands.command(help='Makes the bot join the channel of the user, if the bot has already joined and is in a different channel it will move to the channel the user is in. Only if you are not trying to disturb someone')
    async def join(self, ctx):
        if ctx.message.author.voice:
            channel = ctx.message.author.voice.channel
            voice = get(self.bot.voice_clients, guild=ctx.guild)
            if voice and voice.is_connected():
                if not masters[ctx.guild.id].voice or masters[ctx.guild.id].voice.channel != voice.channel or (not (voice.is_playing() or voice.is_paused()) and queues[ctx.guild.id] == []):
                    await voice.move_to(channel)
                    masters[ctx.guild.id] = ctx.message.author
                else:
                    embed=discord.Embed(title="I am currently under use in your server", color=0xfe4b81)
                    await ctx.send(embed=embed, delete_after=10)

            else:
                voice = await channel.connect()
                queues[ctx.guild.id] = []
                masters[ctx.guild.id] = ctx.message.author
                player[ctx.guild.id] = {}
        else:
            embed=discord.Embed(title="You are currently not connected to any voice channel", color=0xfe4b81)
            await ctx.send(embed=embed, delete_after=10)


    # leaves the vc on demand
    @commands.command(help='Makes the bot leave the voice channel')
    async def leave(self, ctx):
        voice_client = get(self.bot.voice_clients, guild=ctx.guild)

        if voice_client:
            if not masters[ctx.guild.id].voice or masters[ctx.guild.id].voice.channel != voice_client.channel or (not (voice_client.is_playing() or voice_client.is_paused()) and queues[ctx.guild.id] == []):
                if voice_client.is_playing():
                    voice_client.stop()
                player[ctx.guild.id] = {}
                await voice_client.disconnect()
            else:
                    embed=discord.Embed(title="You can't disturb anyone listening to a song", color=0xfe4b81)
                    await ctx.send(embed=embed, delete_after=10)
        else:
            embed=discord.Embed(title="I am currently not connected to a voice channel.", color=0xfe4b81)
            await ctx.send(embed=embed, delete_after=7)



class PlayerCommands(commands.Cog, name="Player", description="This category of commands contains the playable functionalities of the bot. All of them can make bot join vc, play audio and queue audio."):
    def __init__(self, bot: commands.Bot):
        self.bot = bot


    @commands.command(aliases=['s'], help='Searches a query on YT and gives 5 results to choose from. Choosen one will be queued or played')
    async def search(self, ctx, *, query):
        voice = get(self.bot.voice_clients, guild=ctx.guild)

        opts = {
            "format": "bestaudio", 
            "quiet": True,
            "noplaylist": True, 
            "skip_download": True, 
            'forcetitle': True, 
            'forceurl': True,
            'source_address': '0.0.0.0',
            "cookiefile": "yt_cookies.txt"
        }

        songs = await ydl_async(f'ytsearch5:{query}', opts, False)

        videos = songs["entries"]

        try:
            options = {'1️⃣': 0, '2️⃣': 1, '3️⃣': 2, '4️⃣': 3, '5️⃣': 4}
            out = ''

            for i, song in enumerate(videos):
                out = f'{out}{i+1}. [{song["title"]}]({song["webpage_url"]})\n'

            embed=discord.Embed(title="Search results", description=out, color=0xfe4b81)
            emb = await ctx.send(embed=embed)

            for option in options:
                await emb.add_reaction(option)

            def check(reaction, user):
                return reaction.message == emb and reaction.message.channel == ctx.channel and user == ctx.author
            
            react, user = await self.bot.wait_for('reaction_add', check=check, timeout=30.0)
            info = videos[options[react.emoji]]

            if voice:
                if not masters[ctx.guild.id].voice or masters[ctx.guild.id].voice.channel != voice.channel or (not (voice.is_playing() or voice.is_paused()) and queues[ctx.guild.id] == []):
                    masters[ctx.guild.id] = ctx.message.author
                # check if the bot is already playing
                if not (voice.is_playing() or voice.is_paused()) and queues[ctx.guild.id] == []:
                    data = {
                        "link": info['url'],
                        "url": info['webpage_url'],
                        "title": info['title'],
                        "thumbnails": info["thumbnails"]
                    }
                    queues[ctx.guild.id].append(data)
                    await check_queue(ctx.guild.id, voice, ctx)

                else:
                    data = {
                        "link": info['url'],
                        "url": info['webpage_url'],
                        "title": info['title'],
                        "thumbnails": info["thumbnails"]
                    }
                    queues[ctx.guild.id].append(data)
                    embed=discord.Embed(title="Item queued", description=f'[{info["title"]}]({data["url"]})', color=0xfe4b81)
                    embed.set_thumbnail(url=info["thumbnails"][len(info["thumbnails"])-1]["url"])
                    await ctx.send(embed=embed)
            else: 
                if ctx.message.author.voice:
                    channel = ctx.message.author.voice.channel
                    voice = await channel.connect()
                    masters[ctx.guild.id] = ctx.message.author
                    queues[ctx.guild.id] = []
                    player[ctx.guild.id] = {}
                    data = {
                        "link": info['url'],
                        "url": info['webpage_url'],
                        "title": info['title'],
                        "thumbnails": info["thumbnails"]
                    }
                    queues[ctx.guild.id].append(data)
                    await check_queue(ctx.guild.id, voice, ctx)
                else:
                    embed=discord.Embed(title="You are currently not connected to any voice channel", color=0xfe4b81)
                    await ctx.send(embed=embed, delete_after=10)
        except asyncio.TimeoutError:
            # await emb.delete()
            pass
        except Exception as e:
            embed=discord.Embed(title="can't play the requested audio", color=0xfe4b81)
            await ctx.send(embed=embed, delete_after=10)
            raise e



    # command to play sound from a keyword and queue a song if request is made during playing an audio
    @commands.command(aliases=['p'], help='Searches a query on YT and plays or queues the most relevant result')
    async def play(self, ctx, *, query):
        voice = get(self.bot.voice_clients, guild=ctx.guild)

        try:
            info = await ydl_async(f'ytsearch:{query}', YDL_OPTIONS, False)
            info = info['entries'][0]
            url = info['webpage_url']

            if voice:
                if not masters[ctx.guild.id].voice or masters[ctx.guild.id].voice.channel != voice.channel or (not (voice.is_playing() or voice.is_paused()) and queues[ctx.guild.id] == []):
                    masters[ctx.guild.id] = ctx.message.author
                # check if the bot is already playing
                if not (voice.is_playing() or voice.is_paused()) and queues[ctx.guild.id] == []:
                    data = {
                        "link": info['url'],
                        "url": url,
                        "title": info['title'],
                        "thumbnails": info["thumbnails"]
                    }
                    queues[ctx.guild.id].append(data)
                    await check_queue(ctx.guild.id, voice, ctx)

                else:
                    data = {
                        "link": info['url'],
                        "url": url,
                        "title": info['title'],
                        "thumbnails": info["thumbnails"]
                    }
                    queues[ctx.guild.id].append(data)
                    embed=discord.Embed(title="Item queued", description=f'[{info["title"]}]({url})', color=0xfe4b81)
                    embed.set_thumbnail(url=info["thumbnails"][len(info["thumbnails"])-1]["url"])
                    await ctx.send(embed=embed)
            else: 
                if ctx.message.author.voice:
                    channel = ctx.message.author.voice.channel
                    voice = await channel.connect()
                    masters[ctx.guild.id] = ctx.message.author
                    queues[ctx.guild.id] = []
                    player[ctx.guild.id] = {}
                    data = {
                        "link": info['url'],
                        "url": url,
                        "title": info['title'],
                        "thumbnails": info["thumbnails"]
                    }
                    queues[ctx.guild.id].append(data)
                    await check_queue(ctx.guild.id, voice, ctx)
                else:
                    embed=discord.Embed(title="You are currently not connected to any voice channel", color=0xfe4b81)
                    await ctx.send(embed=embed, delete_after=10)
        except Exception as e:
            embed=discord.Embed(title="can't play the requested audio", color=0xfe4b81)
            await ctx.send(embed=embed, delete_after=10)
            raise e



    @commands.command(aliases=['l'], help='Plays a YT live from the URL provided as input')
    async def live(self, ctx, url=None):
        opts = {
            'format': 'bestaudio/best',
            'noplaylist': True,
            'source_address': '0.0.0.0',
            "cookiefile": "yt_cookies.txt"
        }
        voice = get(self.bot.voice_clients, guild=ctx.guild)

        info = await ydl_async(url, opts, False)
        if not info.get('is_live'):
            embed=discord.Embed(title="The link is not of a live video", color=0xfe4b81)
            await ctx.send(embed=embed, delete_after=10)
            return

        if voice:
            if not masters[ctx.guild.id].voice or masters[ctx.guild.id].voice.channel != voice.channel or (not (voice.is_playing() or voice.is_paused()) and queues[ctx.guild.id] == []):
                masters[ctx.guild.id] = ctx.message.author
            if not (voice.is_playing() or voice.is_paused()) and queues[ctx.guild.id] == []:
                voice.play(FFmpegPCMAudio(info["url"], **FFMPEG_OPTIONS))

                embed=discord.Embed(title="Currently Playing (LIVE)", description=f'[{info["title"]}]({info["webpage_url"]})', color=0xfe4b81)
                embed.set_thumbnail(url=info["thumbnails"][len(info["thumbnails"])-1]["url"])

                msg = await ctx.send(embed=embed)

                await check_queue(ctx.guild.id, voice, ctx, msg)
            else:
                embed=discord.Embed(title="Lives can't be queued", color=0xfe4b81)
                await ctx.send(embed=embed, delete_after=10)
        else:
            if ctx.message.author.voice:
                channel = ctx.message.author.voice.channel
                voice = await channel.connect()
                masters[ctx.guild.id] = ctx.message.author
                queues[ctx.guild.id] = []
                player[ctx.guild.id] = {}
                voice.play(FFmpegPCMAudio(info["url"], **FFMPEG_OPTIONS))

                embed=discord.Embed(title="Currently Playing (LIVE)", description=f'[{info["title"]}]({info["webpage_url"]})', color=0xfe4b81)
                embed.set_thumbnail(url=info["thumbnails"][len(info["thumbnails"])-1]["url"])

                msg = await ctx.send(embed=embed)

                await check_queue(ctx.guild.id, voice, ctx, msg)
            else:
                embed=discord.Embed(title="You are currently not connected to any voice channel", color=0xfe4b81)
                await ctx.send(embed=embed, delete_after=10) 



    @commands.command(name="add-playlist", help='Adds a whole YT playlist to queue and starts playing it. Input is taken as the URL to the public or unlisted playlist. You can also mention a starting point or an ending point of the playlist or both')
    async def addPlaylist(self, ctx, url: str, sp: int = None, ep: int = None):
        voice = get(self.bot.voice_clients, guild=ctx.guild)

        source = None
        if 'youtube' in url or 'youtu.be' in url:
            p_id = re.search(r'^.*?(?:list)=(.*?)(?:&|$)', url).groups()
            if p_id:
                link = "https://www.youtube.com/playlist?list=" + p_id[0]
                source = 'youtube'
        elif 'spotify' in url:
            source = 'spotify'
            spotify_tracks = await spotify_api.getPlaylist(url, ctx, sp, ep)
            
        if not source:
            embed=discord.Embed(title="Invalid link", color=0xfe4b81)
            await ctx.send(embed=embed)
            return

        try:
            if source == 'youtube':
                opts = {
                    "extract_flat": True,
                    "source_address": "0.0.0.0",
                    "cookiefile": "yt_cookies.txt"
                }
                info = await ydl_async(link, opts, False)
                info["entries"] = info["entries"][sp:ep]

                if sp or ep:
                    if ep:
                        embed=discord.Embed(title="Adding Playlist", description=f'[{info["title"]}]({link})\n\n**From {sp+1} to {ep}**', color=0xfe4b81)
                    else:
                        embed=discord.Embed(title="Adding Playlist", description=f'[{info["title"]}]({link})\n\n**From {sp+1} to {len(info["entries"])+sp}**', color=0xfe4b81)
                else:
                    embed=discord.Embed(title="Adding Playlist", description=f'[{info["title"]}]({link})', color=0xfe4b81)

            if voice:
                if not masters[ctx.guild.id].voice or masters[ctx.guild.id].voice.channel != voice.channel or (not (voice.is_playing() or voice.is_paused()) and queues[ctx.guild.id] == []):
                    masters[ctx.guild.id] = ctx.message.author
                # check if the bot is already playing
                if not (voice.is_playing() or voice.is_paused()) and queues[ctx.guild.id] == []:
                    if source == 'youtube':
                        await ctx.send(embed=embed)
                        coros = []
                        coros.append(addsongs(info["entries"], ctx))
                        coros.append(check_queue(ctx.guild.id, voice, ctx))
                        asyncio.gather(*coros)
                    elif source == 'spotify':
                        coros = []
                        coros.append(spotify_api.addSongs(spotify_tracks, queues[ctx.guild.id], ctx))
                        coros.append(check_queue(ctx.guild.id, voice, ctx))
                        asyncio.gather(*coros)
                else:
                    if source == 'youtube':
                        await ctx.send(embed=embed)
                        await addsongs(info["entries"], ctx)
                    elif source == 'spotify':
                        await spotify_api.addSongs(spotify_tracks, queues[ctx.guild.id], ctx)
            else: 
                if ctx.message.author.voice:
                    channel = ctx.message.author.voice.channel
                    voice = await channel.connect()
                    masters[ctx.guild.id] = ctx.message.author
                    queues[ctx.guild.id] = []
                    player[ctx.guild.id] = {}
                    if source == 'youtube':
                        await ctx.send(embed=embed)
                        coros = []
                        coros.append(addsongs(info["entries"], ctx))
                        coros.append(check_queue(ctx.guild.id, voice, ctx))
                        asyncio.gather(*coros)
                    elif source == 'spotify':
                        coros = []
                        coros.append(spotify_api.addSongs(spotify_tracks, queues[ctx.guild.id], ctx))
                        coros.append(check_queue(ctx.guild.id, voice, ctx))
                        asyncio.gather(*coros)
                else:
                    embed=discord.Embed(title="You are currently not connected to any voice channel", color=0xfe4b81)
                    await ctx.send(embed=embed, delete_after=10)
        except utils.ExtractorError as e:
            if "ERROR: The playlist does not exist." in e:
                embed=discord.Embed(title="Such a playlist does not exist", color=0xfe4b81)
            else:
                embed=discord.Embed(title="can't queue the requested playlist", color=0xfe4b81)
            await ctx.send(embed=embed, delete_after=10)
        except RuntimeError as e:
            print(e)
        except Exception as e:
            embed=discord.Embed(title="can't queue the requested playlist", color=0xfe4b81)
            await ctx.send(embed=embed, delete_after=10)
            raise e



class VisualizerCommands(commands.Cog, name="Visualizer", description="This category of commands contains the visualizers which enables you to monitor some states of the bot or get some kind of info about something."):
    def __init__(self, bot: commands.Bot):
        self.bot = bot


    # shows the queued songs of the ctx guild
    @commands.command(name="queue", help='Displays the current queue. Limit is the number of entries shown per page, default is 10')
    async def listQueue(self, ctx, limit=10):
        out = ""
        pages = []
        npages = 1
        voice = get(self.bot.voice_clients, guild=ctx.guild)


        if voice and not queues[ctx.guild.id] == []:
            if len(queues[ctx.guild.id])%limit == 0 and len(queues[ctx.guild.id]) != 0:
                npages = int(len(queues[ctx.guild.id])/limit)
            else:
                npages = int(len(queues[ctx.guild.id])/limit) + 1
            paginator = EmbedPaginator(ctx)
            paginator.add_reaction('⏮️', "first")
            paginator.add_reaction('⏪', "back")
            paginator.add_reaction('⏩', "next")
            paginator.add_reaction('⏭️', "last")

            i = 0
            p = 1
            for j, song in enumerate(queues[ctx.guild.id]):
                if i < limit:
                    out = out + str(j+1) + f'. [{song["title"]}]({song["url"]})\n'
                    i = i + 1
                else:
                    out = out + f'\n**Page {p}/{npages}**'
                    embed=discord.Embed(title="Currently in queue", description=out, color=0xfe4b81)
                    pages.append(embed)
                    out = str(j+1) + f'. [{song["title"]}]({song["url"]})\n'
                    i = 1
                    p = p + 1
            out = out + f'\n**Page {p}/{npages}**'
            embed=discord.Embed(title="Currently in queue", description=out, color=0xfe4b81)
            pages.append(embed)

            await paginator.run(pages)

        else:
            out = "None"
            embed=discord.Embed(title="Currently in queue", description=out, color=0xfe4b81)
            await ctx.send(embed=embed)



    @commands.command(help='Displays the lyrics of the current song if available')
    async def lyrics(self, ctx, index=0):
        out = ""

        if player[ctx.guild.id]:
            try:
                lyric = lyrics_api.get_lyrics(player[ctx.guild.id]['title'])['lyrics']
            except LyricScraperException as e:
                try:
                    if int(e.args[0]["error"]["code"]) == 429:
                        lyric = "Daily quota exceeded"
                    else:
                        lyric = "Something went wrong"
                        print(e.args[0]["error"])
                except:
                    lyric = "Something went wrong"
                    print(e)

            out = f'**{player[ctx.guild.id]["title"]}**\n\n{lyric}'
            if len(lyric) > 50:
                out = f'{out}\n\n**Lyrics provided by [genius.com](https://genius.com/)**'
            embed=discord.Embed(title="Lyrics", description=out, color=0xfe4b81)
        else:
            embed=discord.Embed(title="Nothing currently in the player", color=0xfe4b81)
        await ctx.send(embed=embed)



    @commands.command(name='current', aliases=['c'], help='Displays information about the current song in the player')
    async def currentlyPlaying(self, ctx):
        if player[ctx.guild.id]:
            embed=discord.Embed(title="Currently in the Player", description=f'[{player[ctx.guild.id]["title"]}]({player[ctx.guild.id]["url"]})', color=0xfe4b81)
            embed.set_thumbnail(url=player[ctx.guild.id]["thumbnails"][len(player[ctx.guild.id]["thumbnails"])-1]["url"])
        else:
            embed=discord.Embed(title="Nothing currently in the player", color=0xfe4b81)
        await ctx.send(embed=embed, delete_after=10)



class QueueCommands(commands.Cog, name="Queue", description="This category of commands contains the commands related to queues. Also there is a concept of queue lock which will dissable any user from using these commands except the user initiating the lock with some more exceptions."):
    def __init__(self, bot: commands.Bot):
        self.bot = bot


    # removes a mentioned song from queue and displays it
    @commands.command(name="remove", help='Removes an mentioned entry from the queue')
    @checkQueueLock(check_if_bot_connected=True)
    async def removeQueueSong(self, ctx, index: int):
        if (index<=len(queues[ctx.guild.id]) and index>0):
            rem = queues[ctx.guild.id].pop(index-1)
            embed=discord.Embed(title="Removed from queue", description=f'[{rem["title"]}]({rem["url"]})', color=0xfe4b81)
        else:
            embed=discord.Embed(title="Invalid request", color=0xfe4b81)
        await ctx.send(embed=embed)


    # command to pause voice if it is playing
    @commands.command(help='Pauses the current player')
    @checkQueueLock(check_if_bot_connected=True)
    async def pause(self, ctx):
        voice = get(self.bot.voice_clients, guild=ctx.guild)
        embed=discord.Embed(title="Pausing...", color=0xfe4b81)
        if voice.is_playing():
            voice.pause()
            await ctx.send(embed=embed, delete_after=7)


    # command to resume voice if it is paused
    @commands.command(help='Resumes the paused player')
    @checkQueueLock(check_if_bot_connected=True)
    async def resume(self, ctx):
        voice = get(self.bot.voice_clients, guild=ctx.guild)
        embed=discord.Embed(title="Resuming...", color=0xfe4b81)
        if not voice.is_playing():
            voice.resume()
            await ctx.send(embed=embed, delete_after=7)


    # command to skip voice
    @commands.command(help='Skips current audio')
    @checkQueueLock(check_if_bot_connected=True)
    async def skip(self, ctx):
        voice = get(self.bot.voice_clients, guild=ctx.guild)
        embed=discord.Embed(title="Skipping...", color=0xfe4b81)
        if voice.is_playing():
            voice.stop()
            await ctx.send(embed=embed, delete_after=7)


    # stops the bot player by clearing the current queue and skipping the current audio
    @commands.command(help='Just like skip but also clears the queue')
    @checkQueueLock(hard=True, check_if_bot_connected=True)
    async def stop(self, ctx):
        voice = get(self.bot.voice_clients, guild=ctx.guild)
        embed=discord.Embed(title="Stopping...", color=0xfe4b81)
        queues[ctx.guild.id] = []
        if voice.is_playing():
            voice.stop()
            await ctx.send(embed=embed, delete_after=7)


    # command to clear queue
    @commands.command(name="clear-queue", aliases=["clear"], help='Clears the queue')
    @checkQueueLock(hard=True, check_if_bot_connected=True)
    async def clearQueue(self, ctx):
        options = ["👍", "🚫"]
        embed=discord.Embed(title="Do you really want to clear the queue", color=0xfe4b81)
        emb = await ctx.send(embed=embed)
        try:
            for option in options:
                await emb.add_reaction(option)
            
            def chk(reaction, user):
                return reaction.message == emb and reaction.message.channel == ctx.channel and user == ctx.author
            
            react, user = await self.bot.wait_for('reaction_add', check=chk, timeout=30.0)
            if react.emoji == "👍":
                queues[ctx.guild.id] = []
                await emb.delete()
                embed=discord.Embed(title="The queue has been cleared", color=0xfe4b81)
                await ctx.send(embed=embed, delete_after=10)
            else:
                await emb.delete()
        except asyncio.TimeoutError:
            await emb.delete()


    @commands.command(name="shuffle", help='Shuffles the whole queue')
    @checkQueueLock(check_if_bot_connected=True)
    async def shuffleQueue(self, ctx):
        options = ["👍", "🚫"]
        embed=discord.Embed(title="Do you really want to shuffle the queue", color=0xfe4b81)
        emb = await ctx.send(embed=embed)
        try:
            for option in options:
                await emb.add_reaction(option)
            
            def chk(reaction, user):
                return reaction.message == emb and reaction.message.channel == ctx.channel and user == ctx.author
            
            react, user = await self.bot.wait_for('reaction_add', check=chk, timeout=30.0)
            if react.emoji == "👍":
                shuffle(queues[ctx.guild.id])
                await emb.delete()
                embed=discord.Embed(title="The queue has been shuffled", color=0xfe4b81)
                await ctx.send(embed=embed, delete_after=10)
            else:
                await emb.delete()
        except asyncio.TimeoutError:
            await emb.delete()


    @commands.command(help='Locks the queue and prevents anyone from damaging anyone\'s experience')
    async def lock(self, ctx):
        voice_client = get(self.bot.voice_clients, guild=ctx.guild)
        
        if ctx.message.author.voice:
            if voice_client:
                if ctx.guild.id in queuelocks.keys() and queuelocks[ctx.guild.id]["lock"] and queuelocks[ctx.guild.id]["author"].voice :
                    if queuelocks[ctx.guild.id]["author"] == ctx.message.author or (not (voice_client.is_playing() or voice_client.is_paused()) and queues[ctx.guild.id] == []):
                        queuelocks[ctx.guild.id]["lock"] = False
                        embed=discord.Embed(title="Queue lock has been removed", color=0xfe4b81)
                        await ctx.send(embed=embed)
                    else:
                        embed=discord.Embed(title=f'{queuelocks[ctx.guild.id]["author"].display_name} has already locked the queue', color=0xfe4b81)
                        await ctx.send(embed=embed)
                else:
                    queuelocks[ctx.guild.id] = {}
                    queuelocks[ctx.guild.id]["lock"] = True
                    queuelocks[ctx.guild.id]["author"] = ctx.message.author
                    embed=discord.Embed(title=f'{queuelocks[ctx.guild.id]["author"].display_name} has initiated queuelock', color=0xfe4b81)
                    await ctx.send(embed=embed)
            else:
                embed=discord.Embed(title="I am currently not connected to any voice channel", color=0xfe4b81)
                await ctx.send(embed=embed, delete_after=10)
        else:
            embed=discord.Embed(title="You are currently not connected to any voice channel", color=0xfe4b81)
            await ctx.send(embed=embed, delete_after=10)



class DownloadCommands(commands.Cog, name="Download", description="This category of commands contains recently added download feature which can download YT and instagram audio video files with private support for instagram only."):
    def __init__(self, bot: commands.Bot):
        self.bot = bot


    @commands.command(name='download', aliases=['d'], help='Downloads YT or instagram audio video files from the url. If the bot is already playing something then passing no input will result in selecting that video. Copt is for choosing vcodec, default is 0 for h264 but can be set to 1 for codec provided by vendor')
    @commands.max_concurrency(number=1, per=commands.BucketType.default, wait=False)
    async def dl_yt(self, ctx, url: str = None, copt: int = 0):
        def check_url(url: str):
            if url:
                uw = url.split("://")
                if uw[0] == 'https' or uw[0] == 'http':
                    uweb = uw[1].split('/')[0]
                    if 'youtube' in uweb or 'youtu.be' in uweb:
                        return 1
                    elif 'instagram' in uweb:
                        return 2
                    else:
                        return 0
                else:
                    return 0
            else:
                return 0
            
        if not url and player[ctx.guild.id] != {}:
            url = player[ctx.guild.id]['url']

        url_type: int = check_url(url)
        if url_type == 1:
            await yt_dl_instance.downloadVideo(ctx, url, copt)
        elif url_type == 2:
            usrcreds = private_instance.get_usercreds(ctx.author.id)
            await in_dl_instance.downloadVideo(ctx, url, copt, usrcreds)
        else:
            embed=discord.Embed(title='The link is broken, can\'t fetch data', color=0xfe4b81)
            await ctx.send(embed=embed, delete_after=15)


    @commands.command(help='Supports the instagram private feature. This command Logs in to your inastagram account and uses it to access files through your account. Once logged in use the download command normally. This command can only be used in DMs in order to protect your privacy')
    async def login(self, ctx, usrn=None, passw=None):
        if isinstance(ctx.channel, discord.DMChannel):
            if usrn and passw:
                await private_instance.login(ctx, usrn, passw)
        else:
            embed=discord.Embed(title='Hey use this command here', description='Login command can only be used from the DM. This helps us keep your credentials private.', color=0xfe4b81)
            await ctx.author.send(embed=embed, delete_after=30)

    @commands.command(help='Logout of your account only if you are already logged in')
    async def logout(self, ctx):
        if private_instance.is_user_authenticated(ctx.author.id):
            embed=discord.Embed(title="Do you really want to logout", color=0xfe4b81)
            emb = await ctx.send(embed=embed)

            try:
                await emb.add_reaction('👍')
                await emb.add_reaction('🚫')
                
                def chk(reaction, user):
                    return reaction.message == emb and reaction.message.channel == ctx.channel and user == ctx.author
                
                react, user = await self.bot.wait_for('reaction_add', check=chk, timeout=30.0)
                if react.emoji == "👍":
                    await private_instance.logout(ctx)
                    await emb.delete()
                else:
                    await emb.delete()
            except asyncio.TimeoutError:
                await emb.delete()


class SpecialCommands(commands.Cog, name="Special", description="This category of commands contains the special commands which can only be accessed by the owner of the bot. These commands enables the owner to remotely invoke methods for temporary fixes or other debugging stuff."):
    def __init__(self, bot: commands.Bot):
        self.bot = bot

    async def cog_check(self, ctx):
        if not await ctx.bot.is_owner(ctx.author):
            raise commands.NotOwner('You do not own this bot.')
        return True


    @commands.command(help='Refetches the default cookie files')
    async def refetch(self, ctx, id_insta=None, id_yt=None):
        getCookieFile(id_insta, id_yt)
        embed=discord.Embed(title="Default cookies were refetched and refreshed successfully", color=0xfe4b81)
        await ctx.send(embed=embed, delete_after=20)

    @commands.command(name="add-cog", help='Adds a predefined cog to the bot')
    async def addCog(self, ctx, cog_name):
        if cog_name != 'Special':
            for cog in cog_list:
                if cog.qualified_name == cog_name and not self.bot.get_cog(cog_name):
                    self.bot.add_cog(cog)
                    embed=discord.Embed(title=f"{cog_name} cog was added successfully", color=0xfe4b81)
                    await ctx.send(embed=embed, delete_after=20)

    @commands.command(name="remove-cog", help='Removes a already existing cog. Generally used to disable a functionality of the bot')
    async def removeCog(self, ctx, cog_name):
        if cog_name != 'Special':
            self.bot.remove_cog(cog_name)
            embed=discord.Embed(title=f"{cog_name} cog was removed successfully", color=0xfe4b81)
            await ctx.send(embed=embed, delete_after=20)

cog_list = []

cog_list.append(BasicCommands(client))
cog_list.append(PlayerCommands(client))
cog_list.append(VisualizerCommands(client))
cog_list.append(QueueCommands(client))
cog_list.append(DownloadCommands(client))
cog_list.append(SpecialCommands(client))

for cog in cog_list:
    client.add_cog(cog)

@client.event
async def on_command_error(ctx, error):
    if isinstance(error, commands.MaxConcurrencyReached):
        embed=discord.Embed(title="Please wait..", description="Someone else is currently using this feature please wait before trying again. This restriction has been implemented to prevent throttling as the bot is currently running on a free server.", color=0xfe4b81)
        await ctx.send(embed=embed, delete_after=20)
    elif isinstance(error, commands.NotOwner):
        embed=discord.Embed(title="Access Denied", description=f"It is a special command and is reserved to the owner of the bot only. This types of commands enables the owner to remotely triggure some functions for ease of use. Read more about them from `{ctx.prefix}help Special`.", color=0xfe4b81)
        await ctx.reply(embed=embed, delete_after=20)
    elif isinstance(error, QueueLockCheckFailure):
        embed=discord.Embed(title=error, color=0xfe4b81)
        await ctx.send(embed=embed, delete_after=10)
    elif isinstance(error, commands.CommandNotFound):
        print(error)
    elif isinstance(error, commands.errors.MissingRequiredArgument):
        print(error)
    else:
        raise error

client.run(token)
