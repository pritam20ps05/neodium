import discord
import urllib.request
import re
import asyncio
from time import time
from discord.ext import commands
from discord.utils import get
from discord import FFmpegPCMAudio
from DiscordUtils.Pagination import CustomEmbedPaginator as EmbedPaginator
from yt_dlp import YoutubeDL, utils
from lyrics_extractor import SongLyrics, LyricScraperException
from NeodiumDownload import YTdownload, INSdownload, private_login
from json import load

YDL_OPTIONS = {
    'format': 'bestaudio', 
    'noplaylist': 'True', 
    'source_address': '0.0.0.0'
    }

FFMPEG_OPTIONS = {
    'before_options': '-reconnect 1 -reconnect_streamed 1 -reconnect_delay_max 5', 
    'options': '-vn'
    }

with open("credentials.json", "r") as creds:
    cred = load(creds)
    token = cred["token"]
    search_engine = cred["search_engine"]
    search_token = cred["search_token"]

client = commands.Bot(command_prefix='-')  # prefix our commands with '-'
lyrics_api = SongLyrics(search_token, search_engine)
yt_dl_instance = YTdownload(client)
in_dl_instance = INSdownload(client)
private_instance = private_login('login.json')

player = {}
masters = {}
queues = {}
queuelocks = {}



# main queue manager function to play music in queues
async def check_queue(id, voice, ctx, msg=None):
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
            with YoutubeDL(YDL_OPTIONS) as ydl:
                info = ydl.extract_info(player[id]["url"], download=False)
            player[id]["link"] = info['url']
            player[id]["raw"] = info
            voice.play(FFmpegPCMAudio(player[id]["link"], **FFMPEG_OPTIONS))
            await asyncio.sleep(1)

        await check_queue(id, voice, ctx, msg)
    else:
        player[ctx.guild.id] = {}



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
                "thumbnails": info["thumbnails"],
                "raw": info
            }
            queues[ctx.guild.id].append(data)
        except Exception as e:
            print(e)
        await asyncio.sleep(2)
    embed=discord.Embed(title="Playlist items were added to queue", color=0xfe4b81)
    await ctx.send(embed=embed)



# check if bot is ready
@client.event  
async def on_ready():
    print('Bot online')


# command for bot to join the channel of the user, if the bot has already joined and is in a different channel, it will move to the channel the user is in
@client.command()
async def join(ctx):
    if ctx.message.author.voice:
        channel = ctx.message.author.voice.channel
        voice = get(client.voice_clients, guild=ctx.guild)
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



@client.command(aliases=['s'])
async def search(ctx, *,keyw):
    voice = get(client.voice_clients, guild=ctx.guild)

    opts = {
        "format": "bestaudio", 
        "quiet": True,
        "noplaylist": True, 
        "skip_download": True, 
        'forcetitle': True, 
        'forceurl': True,
        'source_address': '0.0.0.0'
    }

    with YoutubeDL(opts) as ydl:
        songs = ydl.extract_info(f'ytsearch5:{keyw}')

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
        
        react, user = await client.wait_for('reaction_add', check=check, timeout=30.0)
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
                    "thumbnails": info["thumbnails"],
                    "raw": info
                }
                queues[ctx.guild.id].append(data)
                await check_queue(ctx.guild.id, voice, ctx)

            else:
                data = {
                    "link": info['url'],
                    "url": info['webpage_url'],
                    "title": info['title'],
                    "thumbnails": info["thumbnails"],
                    "raw": info
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
                    "thumbnails": info["thumbnails"],
                    "raw": info
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
@client.command(aliases=['p'])
async def play(ctx, *,keyw):
    html = urllib.request.urlopen("https://www.youtube.com/results?search_query=" + keyw.replace(" ", "+"))
    video_ids = re.findall(r"watch\?v=(\S{11})", html.read().decode())
    url = "https://www.youtube.com/watch?v=" + video_ids[0]

    voice = get(client.voice_clients, guild=ctx.guild)

    try:
        with YoutubeDL(YDL_OPTIONS) as ydl:
            info = ydl.extract_info(url, download=False)

        if voice:
            if not masters[ctx.guild.id].voice or masters[ctx.guild.id].voice.channel != voice.channel or (not (voice.is_playing() or voice.is_paused()) and queues[ctx.guild.id] == []):
                masters[ctx.guild.id] = ctx.message.author
            # check if the bot is already playing
            if not (voice.is_playing() or voice.is_paused()) and queues[ctx.guild.id] == []:
                data = {
                    "link": info['url'],
                    "url": url,
                    "title": info['title'],
                    "thumbnails": info["thumbnails"],
                    "raw": info
                }
                queues[ctx.guild.id].append(data)
                await check_queue(ctx.guild.id, voice, ctx)

            else:
                data = {
                    "link": info['url'],
                    "url": url,
                    "title": info['title'],
                    "thumbnails": info["thumbnails"],
                    "raw": info
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
                    "thumbnails": info["thumbnails"],
                    "raw": info
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



@client.command(aliases=['l'])
async def live(ctx, url=None):
    opts = {
        'format': 'bestaudio/best',
        'noplaylist': True,
        'source_address': '0.0.0.0'
    }
    voice = get(client.voice_clients, guild=ctx.guild)

    if url:
        with YoutubeDL(opts) as ydl:
            info = ydl.extract_info(url, download=False)
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



# shows the queued songs of the ctx guild
@client.command(name="queue")
async def listQueue(ctx, limit=10):
    out = ""
    pages = []
    npages = 1
    voice = get(client.voice_clients, guild=ctx.guild)


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



@client.command()
async def lyrics(ctx, index=0):
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



# removes a mentioned song from queue and displays it
@client.command(name="remove")
async def removeQueueSong(ctx, index: int):
    voice = get(client.voice_clients, guild=ctx.guild)

    if voice and (index<=len(queues[ctx.guild.id]) and index>0):
        if ctx.guild.id in queuelocks.keys() and queuelocks[ctx.guild.id]["lock"] and queuelocks[ctx.guild.id]["author"].voice and queuelocks[ctx.guild.id]["author"].voice.channel == voice.channel and not (not (voice.is_playing() or voice.is_paused()) and queues[ctx.guild.id] == []): 
            if queuelocks[ctx.guild.id]["author"] == ctx.message.author:
                rem = queues[ctx.guild.id].pop(index-1)
                embed=discord.Embed(title="Removed from queue", description=f'[{rem["title"]}]({rem["url"]})', color=0xfe4b81)
            else:
                embed=discord.Embed(title="The queue is currently locked", color=0xfe4b81)
        else:
            queuelocks[ctx.guild.id] = {}
            queuelocks[ctx.guild.id]["lock"] = False
            rem = queues[ctx.guild.id].pop(index-1)
            embed=discord.Embed(title="Removed from queue", description=f'[{rem["title"]}]({rem["url"]})', color=0xfe4b81)
    else:
        embed=discord.Embed(title="Invalid request", color=0xfe4b81)
    await ctx.send(embed=embed)



@client.command(name="add-playlist")
async def addPlaylist(ctx, link: str, sp: int = None, ep: int = None):
    voice = get(client.voice_clients, guild=ctx.guild)

    # user link formatting
    if link.split("?")[0] == "https://www.youtube.com/watch":
        id_frt = link.split("?")[1].split("&")[1] # list=PL9bw4S5ePsEEqCMJSiYZ-KTtEjzVy0YvK
        link = "https://www.youtube.com/playlist?" + id_frt
    elif link.split("?")[0] == "https://www.youtube.com/playlist":
        pass
    else:
        # promt with invalid link
        embed=discord.Embed(title="Invalid link", color=0xfe4b81)
        await ctx.send(embed=embed)
        return

    try:
        opts = {
            "extract_flat": True,
            "source_address": "0.0.0.0"
        }
        with YoutubeDL(opts) as ydl:
            info = ydl.extract_info(link, download=False)
            
        # Entry slicing
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
                await ctx.send(embed=embed)
                loop = asyncio.get_event_loop()
                coros = []
                coros.append(addsongs(info["entries"], ctx))
                coros.append(check_queue(ctx.guild.id, voice, ctx))
                loop.run_until_complete(asyncio.gather(*coros))
            else:
                await ctx.send(embed=embed)
                await addsongs(info["entries"], ctx)
        else: 
            if ctx.message.author.voice:
                channel = ctx.message.author.voice.channel
                voice = await channel.connect()
                masters[ctx.guild.id] = ctx.message.author
                queues[ctx.guild.id] = []
                player[ctx.guild.id] = {}
                await ctx.send(embed=embed)
                loop = asyncio.get_event_loop()
                coros = []
                coros.append(addsongs(info["entries"], ctx))
                coros.append(check_queue(ctx.guild.id, voice, ctx))
                loop.run_until_complete(asyncio.gather(*coros))
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



# command to resume voice if it is paused
@client.command()
async def resume(ctx):
    voice = get(client.voice_clients, guild=ctx.guild)
    embed=discord.Embed(title="Resuming...", color=0xfe4b81)

    if voice:
        if ctx.guild.id in queuelocks.keys() and queuelocks[ctx.guild.id]["lock"] and queuelocks[ctx.guild.id]["author"].voice and queuelocks[ctx.guild.id]["author"].voice.channel == voice.channel and not (not (voice.is_playing() or voice.is_paused()) and queues[ctx.guild.id] == []): 
            if queuelocks[ctx.guild.id]["author"] == ctx.message.author:
                if not voice.is_playing():
                    voice.resume()
                    await ctx.send(embed=embed, delete_after=7)
            else:
                embed=discord.Embed(title="The queue is currently locked", color=0xfe4b81)
                await ctx.send(embed=embed, delete_after=7)
        else:
            queuelocks[ctx.guild.id] = {}
            queuelocks[ctx.guild.id]["lock"] = False
            if not voice.is_playing():
                voice.resume()
                await ctx.send(embed=embed, delete_after=7)
    else:
        embed=discord.Embed(title="I am currently not connected to any voice channel", color=0xfe4b81)
        await ctx.send(embed=embed, delete_after=7)



# command to pause voice if it is playing
@client.command()
async def pause(ctx):
    voice = get(client.voice_clients, guild=ctx.guild)
    embed=discord.Embed(title="Pausing...", color=0xfe4b81)

    if voice:
        if ctx.guild.id in queuelocks.keys() and queuelocks[ctx.guild.id]["lock"] and queuelocks[ctx.guild.id]["author"].voice and queuelocks[ctx.guild.id]["author"].voice.channel == voice.channel and not (not (voice.is_playing() or voice.is_paused()) and queues[ctx.guild.id] == []): 
            if queuelocks[ctx.guild.id]["author"] == ctx.message.author:
                if voice.is_playing():
                    voice.pause()
                    await ctx.send(embed=embed, delete_after=7)
            else:
                embed=discord.Embed(title="The queue is currently locked", color=0xfe4b81)
                await ctx.send(embed=embed, delete_after=7)
        else:
            queuelocks[ctx.guild.id] = {}
            queuelocks[ctx.guild.id]["lock"] = False
            if voice.is_playing():
                voice.pause()
                await ctx.send(embed=embed, delete_after=7)
    else:
        embed=discord.Embed(title="I am currently not connected to any voice channel", color=0xfe4b81)
        await ctx.send(embed=embed, delete_after=7)


# command to skip voice
@client.command()
async def skip(ctx):
    voice = get(client.voice_clients, guild=ctx.guild)
    embed=discord.Embed(title="Skipping...", color=0xfe4b81)

    if voice:
        if ctx.guild.id in queuelocks.keys() and queuelocks[ctx.guild.id]["lock"] and queuelocks[ctx.guild.id]["author"].voice and queuelocks[ctx.guild.id]["author"].voice.channel == voice.channel and not (not (voice.is_playing() or voice.is_paused()) and queues[ctx.guild.id] == []): 
            if queuelocks[ctx.guild.id]["author"] == ctx.message.author:
                if voice.is_playing():
                    voice.stop()
                    await ctx.send(embed=embed, delete_after=7)
            else:
                embed=discord.Embed(title="The queue is currently locked", color=0xfe4b81)
                await ctx.send(embed=embed, delete_after=7)
        else:
            queuelocks[ctx.guild.id] = {}
            queuelocks[ctx.guild.id]["lock"] = False
            if voice.is_playing():
                voice.stop()
                await ctx.send(embed=embed, delete_after=7)
    else:
        embed=discord.Embed(title="I am currently not connected to any voice channel", color=0xfe4b81)
        await ctx.send(embed=embed, delete_after=7)



# stops the bot player by clearing the current queue and skipping the current audio
@client.command()
async def stop(ctx):
    voice = get(client.voice_clients, guild=ctx.guild)
    embed=discord.Embed(title="Stopping...", color=0xfe4b81)

    if voice:
        if ctx.guild.id in queuelocks.keys() and queuelocks[ctx.guild.id]["lock"] and queuelocks[ctx.guild.id]["author"].voice and queuelocks[ctx.guild.id]["author"].voice.channel == voice.channel and not (not (voice.is_playing() or voice.is_paused()) and queues[ctx.guild.id] == []): 
            embed=discord.Embed(title="The queue is currently locked", color=0xfe4b81)
            await ctx.send(embed=embed, delete_after=7)
        else:
            queues[ctx.guild.id] = []
            queuelocks[ctx.guild.id] = {}
            queuelocks[ctx.guild.id]["lock"] = False
            if voice.is_playing():
                voice.stop()
                await ctx.send(embed=embed, delete_after=7)
    else:
        embed=discord.Embed(title="I am currently not connected to any voice channel", color=0xfe4b81)
        await ctx.send(embed=embed, delete_after=7)



# leaves the vc on demand
@client.command(name='leave', help='To make the bot leave the voice channel')
async def leave(ctx):
    voice_client = get(client.voice_clients, guild=ctx.guild)

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



# command to clear queue
@client.command(name="clear-queue", aliases=["clear"])
async def clearQueue(ctx):
    voice = get(client.voice_clients, guild=ctx.guild)
    # embed=discord.Embed(title="Stopping...", color=0xfe4b81)
    options = ["👍", "🚫"]

    if voice:
        if ctx.guild.id in queuelocks.keys() and queuelocks[ctx.guild.id]["lock"] and queuelocks[ctx.guild.id]["author"].voice and queuelocks[ctx.guild.id]["author"].voice.channel == voice.channel and not (not (voice.is_playing() or voice.is_paused()) and queues[ctx.guild.id] == []): 
            embed=discord.Embed(title="The queue is currently locked", color=0xfe4b81)
            await ctx.send(embed=embed)
        else:
            queuelocks[ctx.guild.id] = {}
            queuelocks[ctx.guild.id]["lock"] = False
            embed=discord.Embed(title="Do you really want to clear the queue", color=0xfe4b81)
            emb = await ctx.send(embed=embed)

            try:
                for option in options:
                    await emb.add_reaction(option)
                
                def chk(reaction, user):
                    return reaction.message == emb and reaction.message.channel == ctx.channel and user == ctx.author
                
                react, user = await client.wait_for('reaction_add', check=chk, timeout=30.0)
                if react.emoji == "👍":
                    queues[ctx.guild.id] = []
                    await emb.delete()
                    embed=discord.Embed(title="The queue has been cleared", color=0xfe4b81)
                    await ctx.send(embed=embed)
                else:
                    await emb.delete()
            except asyncio.TimeoutError:
                await emb.delete()
    else:
        embed=discord.Embed(title="I am currently not connected to any voice channel", color=0xfe4b81)
        await ctx.send(embed=embed, delete_after=7)



@client.command()
async def lock(ctx):
    voice_client = get(client.voice_clients, guild=ctx.guild)
    
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



@client.command(name='download', aliases=['d'])
@commands.max_concurrency(number=1, per=commands.BucketType.default, wait=False)
async def dl_yt(ctx, url: str = None, copt: int = 0):
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


@client.command()
async def login(ctx, usrn=None, passw=None):
    if isinstance(ctx.channel, discord.DMChannel):
        if usrn and passw:
            await private_instance.login(ctx, usrn, passw)
    else:
        embed=discord.Embed(title='Hey use this command here', description='Login command can only be used from the DM. This helps us keep your credentials private.', color=0xfe4b81)
        await ctx.author.send(embed=embed, delete_after=30)

@client.command()
async def logout(ctx):
    if private_instance.is_user_authenticated(ctx.author.id):
        embed=discord.Embed(title="Do you really want to logout", color=0xfe4b81)
        emb = await ctx.send(embed=embed)

        try:
            await emb.add_reaction('👍')
            await emb.add_reaction('🚫')
            
            def chk(reaction, user):
                return reaction.message == emb and reaction.message.channel == ctx.channel and user == ctx.author
            
            react, user = await client.wait_for('reaction_add', check=chk, timeout=30.0)
            if react.emoji == "👍":
                await private_instance.logout(ctx)
                await emb.delete()
            else:
                await emb.delete()
        except asyncio.TimeoutError:
            await emb.delete()

@client.event
async def on_command_error(ctx, error):
    if isinstance(error, commands.MaxConcurrencyReached):
        embed=discord.Embed(title="Please wait..", description="Someone else is currently using this feature please wait before trying again. This restriction has been implemented to prevent throttling as the bot is currently running on a free server.", color=0xfe4b81)
        await ctx.send(embed=embed, delete_after=20)
    else:
        raise error

client.run(token)