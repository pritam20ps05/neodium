from json import loads
import discord
import os
import urllib.request
import re
import asyncio
# load our local env so we dont have the token in public
from discord.ext import commands
from discord.utils import get
from discord import FFmpegPCMAudio
from discord import TextChannel
from youtube_dl import YoutubeDL
from json import load

YDL_OPTIONS = {'format': 'bestaudio', 'noplaylist': 'True'}
FFMPEG_OPTIONS = {
    'before_options': '-reconnect 1 -reconnect_streamed 1 -reconnect_delay_max 5', 'options': '-vn'}

with open("credentials.json", "r") as creds:
    token = load(creds)["token"]

client = commands.Bot(command_prefix='-')  # prefix our commands with '-'

# players = {}
queues = {}

async def check_queue(id, voice, ctx):
    while voice.is_playing() or voice.is_paused():
        await asyncio.sleep(5)
    if queues[id] != []:
        # print(queues[id][0])
        voice.play(FFmpegPCMAudio(queues[id][0]["link"], **FFMPEG_OPTIONS))
        await ctx.send('Currently playing '+queues[id][0]["title"])
        queues[id].pop(0)
        await check_queue(id, voice, ctx)

@client.event  # check if bot is ready
async def on_ready():
    print('Bot online')


# command for bot to join the channel of the user, if the bot has already joined and is in a different channel, it will move to the channel the user is in
@client.command()
async def join(ctx):
    channel = ctx.message.author.voice.channel
    voice = get(client.voice_clients, guild=ctx.guild)
    if voice and voice.is_connected():
        await voice.move_to(channel)
    else:
        voice = await channel.connect()


# command to play sound from a youtube URL
@client.command()
async def play(ctx, *,keyw):
    html = urllib.request.urlopen("https://www.youtube.com/results?search_query=" + keyw.replace(" ", "+"))
    video_ids = re.findall(r"watch\?v=(\S{11})", html.read().decode())
    url = "https://www.youtube.com/watch?v=" + video_ids[0]

    voice = get(client.voice_clients, guild=ctx.guild)

    # print(voice.is_playing())
    if voice:
        if not voice.is_playing():
            with YoutubeDL(YDL_OPTIONS) as ydl:
                info = ydl.extract_info(url, download=False)
            URL = info['url']
            queues[ctx.guild.id] = []
            # for song in queues[ctx.guild.id]:
            # print(URL)
            voice.play(FFmpegPCMAudio(URL, **FFMPEG_OPTIONS))
            if voice.is_playing():
                await ctx.send('Currently playing '+info["title"])
            await check_queue(ctx.guild.id, voice, ctx)

    # check if the bot is already playing
        else:
            with YoutubeDL(YDL_OPTIONS) as ydl:
                info = ydl.extract_info(url, download=False)
            data = {
                "link": info['url'],
                "title": info['title']
            }
            queues[ctx.guild.id].append(data)
            # print(ctx.guild.id)
            # print(queues[ctx.guild.id])
            await ctx.send("Item queued "+info["title"])
            return
    else: 
        channel = ctx.message.author.voice.channel
        # voice = get(client.voice_clients, guild=ctx.guild)
        if voice and voice.is_connected():
            await voice.move_to(channel)
        else:
            voice = await channel.connect()
        with YoutubeDL(YDL_OPTIONS) as ydl:
            info = ydl.extract_info(url, download=False)
        URL = info['url']
        queues[ctx.guild.id] = []
        # for song in queues[ctx.guild.id]:
        # print(info.keys())
        voice.play(FFmpegPCMAudio(URL, **FFMPEG_OPTIONS))
        if voice.is_playing():
            await ctx.send('Currently playing '+info["title"])
        await check_queue(ctx.guild.id, voice, ctx)


# command to resume voice if it is paused
@client.command()
async def resume(ctx):
    voice = get(client.voice_clients, guild=ctx.guild)

    if not voice.is_playing():
        voice.resume()
        await ctx.send('Audio resuming')


# command to pause voice if it is playing
@client.command()
async def pause(ctx):
    voice = get(client.voice_clients, guild=ctx.guild)

    if voice.is_playing():
        voice.pause()
        await ctx.send('Audio paused')


# command to stop voice
@client.command()
async def skip(ctx):
    voice = get(client.voice_clients, guild=ctx.guild)

    if voice.is_playing():
        voice.stop()
        await ctx.send('Skipping...')

@client.command(name='leave', help='To make the bot leave the voice channel')
async def leave(ctx):
    voice_client = get(client.voice_clients, guild=ctx.guild)

    if voice_client:
        if voice_client.is_playing():
            voice_client.stop()
        await voice_client.disconnect()
    else:
        await ctx.send("The bot is not connected to a voice channel.")

# command to clear channel messages
@client.command()
async def clear(ctx, amount=5):
    await ctx.channel.purge(limit=amount)
    await ctx.send("Messages have been cleared")


client.run(token)