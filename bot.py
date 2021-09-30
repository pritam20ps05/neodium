from json import loads
import discord
import urllib.request
import re
import asyncio
from discord.ext import commands
from discord.utils import get
from discord import FFmpegPCMAudio
from youtube_dl import YoutubeDL
from json import load

# need a way to actually store cookies.txt remotely
YDL_OPTIONS = {'format': 'bestaudio', 'noplaylist': 'True', 'source_address': '0.0.0.0', 'cookiefile': 'cookies.txt'}
FFMPEG_OPTIONS = {
    'before_options': '-reconnect 1 -reconnect_streamed 1 -reconnect_delay_max 5', 'options': '-vn'}

with open("credentials.json", "r") as creds:
    token = load(creds)["token"]

client = commands.Bot(command_prefix='-')  # prefix our commands with '-'

# players = {}
masters = {}
queues = {}
queuelocks = {}

# main queue manager function to play music in queues
async def check_queue(id, voice, ctx, msg):
    while voice.is_playing() or voice.is_paused():
        await asyncio.sleep(5)
    await msg.delete()
    if queues[id] != []:
        # print(queues[id][0]["URL"])
        embed=discord.Embed(title="Currently Playing", description=f'[{queues[id][0]["title"]}]({queues[id][0]["url"]})', color=0xfe4b81)
        embed.set_thumbnail(url=queues[id][0]["thumbnails"][len(queues[id][0]["thumbnails"])-1]["url"])
        voice.play(FFmpegPCMAudio(queues[id][0]["link"], **FFMPEG_OPTIONS))
        # await ctx.send('Currently playing '+queues[id][0]["title"])
        msg = await ctx.send(embed=embed)
        queues[id].pop(0)
        await check_queue(id, voice, ctx, msg)

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
    else:
        embed=discord.Embed(title="You are currently not connected to any voice channel", color=0xfe4b81)
        await ctx.send(embed=embed, delete_after=10)


# command to play sound from a keyword and queue a song if request is made during playing an audio
@client.command(aliases=['p'])
async def play(ctx, *,keyw):
    html = urllib.request.urlopen("https://www.youtube.com/results?search_query=" + keyw.replace(" ", "+"))
    video_ids = re.findall(r"watch\?v=(\S{11})", html.read().decode())
    url = "https://www.youtube.com/watch?v=" + video_ids[0]

    voice = get(client.voice_clients, guild=ctx.guild)

    # print(voice.is_playing())
    try:
        if voice:
            if not masters[ctx.guild.id].voice or masters[ctx.guild.id].voice.channel != voice.channel or (not (voice.is_playing() or voice.is_paused()) and queues[ctx.guild.id] == []):
                masters[ctx.guild.id] = ctx.message.author
            # check if the bot is already playing
            if not (voice.is_playing() or voice.is_paused()) and queues[ctx.guild.id] == []:
                with YoutubeDL(YDL_OPTIONS) as ydl:
                    info = ydl.extract_info(url, download=False)
                URL = info['url']
                # for song in queues[ctx.guild.id]:
                # print(URL)
                embed=discord.Embed(title="Currently playing", description=f'[{info["title"]}]({url})', color=0xfe4b81)
                embed.set_thumbnail(url=info["thumbnails"][len(info["thumbnails"])-1]["url"])
                voice.play(FFmpegPCMAudio(URL, **FFMPEG_OPTIONS))
                if voice.is_playing():
                    # await ctx.send('Currently playing '+info["title"])
                    msg = await ctx.send(embed=embed)
                await check_queue(ctx.guild.id, voice, ctx, msg)

            else:
                with YoutubeDL(YDL_OPTIONS) as ydl:
                    info = ydl.extract_info(url, download=False)
                data = {
                    "link": info['url'],
                    "url": url,
                    "title": info['title'],
                    "thumbnails": info["thumbnails"]
                }
                queues[ctx.guild.id].append(data)
                # print(ctx.guild.id)
                # print(queues[ctx.guild.id])
                embed=discord.Embed(title="Item queued", description=f'[{info["title"]}]({url})', color=0xfe4b81)
                embed.set_thumbnail(url=info["thumbnails"][len(info["thumbnails"])-1]["url"])
                # await ctx.send("Item queued "+info["title"])
                await ctx.send(embed=embed)
                return
        else: 
            if ctx.message.author.voice:
                channel = ctx.message.author.voice.channel
                # voice = get(client.voice_clients, guild=ctx.guild)
                voice = await channel.connect()
                masters[ctx.guild.id] = ctx.message.author
                queues[ctx.guild.id] = []
                with YoutubeDL(YDL_OPTIONS) as ydl:
                    info = ydl.extract_info(url, download=False)
                URL = info['url']
                # for song in queues[ctx.guild.id]:
                # print()
                embed=discord.Embed(title="Currently playing", description=f'[{info["title"]}]({url})', color=0xfe4b81)
                embed.set_thumbnail(url=info["thumbnails"][len(info["thumbnails"])-1]["url"])
                voice.play(FFmpegPCMAudio(URL, **FFMPEG_OPTIONS))
                if voice.is_playing():
                    # await ctx.send('Currently playing '+info["title"])
                    msg = await ctx.send(embed=embed)
                await check_queue(ctx.guild.id, voice, ctx, msg)
            else:
                embed=discord.Embed(title="You are currently not connected to any voice channel", color=0xfe4b81)
                # await ctx.send('You are not currently connected to any voice channel')
                await ctx.send(embed=embed, delete_after=10)
    except:
        embed=discord.Embed(title="can't play the requested audio", color=0xfe4b81)
        await ctx.send(embed=embed, delete_after=10)

# shows the queued songs of the ctx guild
@client.command(name="queue")
async def listQueue(ctx):
    out = ""
    voice = get(client.voice_clients, guild=ctx.guild)
    if voice and not queues[ctx.guild.id] == []:
        for i, song in enumerate(queues[ctx.guild.id]):
            out = out + str(i+1) + f'. [{song["title"]}]({song["url"]})\n'
    else:
        out = "None"
    embed=discord.Embed(title="Currently in queue", description=out, color=0xfe4b81)
    await ctx.send(embed=embed)

# removes a mentioned song from queue and displays it
@client.command(name="remove")
async def removeQueueSong(ctx, index: int):
    voice = get(client.voice_clients, guild=ctx.guild)

    if voice and (index<=len(queues[ctx.guild.id]) and index>0):
        if ctx.guild.id in queuelocks.keys() and queuelocks[ctx.guild.id]["lock"] and queuelocks[ctx.guild.id]["author"].voice and queuelocks[ctx.guild.id]["author"].voice.channel == voice.channel and not (not (voice.is_playing() or voice.is_paused()) and queues[ctx.guild.id] == []): 
            embed=discord.Embed(title="The queue is currently locked", color=0xfe4b81)
        else:
            queuelocks[ctx.guild.id] = {}
            queuelocks[ctx.guild.id]["lock"] = False
            rem = queues[ctx.guild.id].pop(index-1)
            embed=discord.Embed(title="Removed from queue", description=f'[{rem["title"]}]({rem["url"]})', color=0xfe4b81)
    else:
        embed=discord.Embed(title="Invalid request", color=0xfe4b81)
    await ctx.send(embed=embed)

# command to resume voice if it is paused
@client.command()
async def resume(ctx):
    voice = get(client.voice_clients, guild=ctx.guild)
    embed=discord.Embed(title="Resuming...", color=0xfe4b81)

    if voice:
        if not voice.is_playing():
            voice.resume()
            await ctx.send(embed=embed)
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
            embed=discord.Embed(title="The queue is currently locked", color=0xfe4b81)
            await ctx.send(embed=embed)
        else:
            queuelocks[ctx.guild.id] = {}
            queuelocks[ctx.guild.id]["lock"] = False
            if voice.is_playing():
                voice.pause()
                await ctx.send(embed=embed)
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
            embed=discord.Embed(title="The queue is currently locked", color=0xfe4b81)
            await ctx.send(embed=embed)
        else:
            queuelocks[ctx.guild.id] = {}
            queuelocks[ctx.guild.id]["lock"] = False
            if voice.is_playing():
                voice.stop()
                await ctx.send(embed=embed)
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
            await ctx.send(embed=embed)
        else:
            queues[ctx.guild.id] = []
            queuelocks[ctx.guild.id] = {}
            queuelocks[ctx.guild.id]["lock"] = False
            if voice.is_playing():
                voice.stop()
                await ctx.send(embed=embed)
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
            await voice_client.disconnect()
        else:
                embed=discord.Embed(title="You can't disturb anyone listening to a song", color=0xfe4b81)
                await ctx.send(embed=embed, delete_after=10)
    else:
        embed=discord.Embed(title="I am currently not connected to a voice channel.", color=0xfe4b81)
        await ctx.send(embed=embed, delete_after=7)

# command to clear channel messages
@client.command()
async def clear(ctx, amount=5):
    await ctx.channel.purge(limit=amount)
    embed=discord.Embed(title="Messages have been cleared", color=0xfe4b81)
    await ctx.send(embed=embed)

@client.command()
async def lock(ctx):
    voice_client = get(client.voice_clients, guild=ctx.guild)
    
    if ctx.message.author.voice:
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
        embed=discord.Embed(title="You are currently not connected to any voice channel", color=0xfe4b81)
        await ctx.send(embed=embed, delete_after=10)


client.run(token)