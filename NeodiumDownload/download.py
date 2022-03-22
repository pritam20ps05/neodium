import tempfile
import discord
import requests
import random
from discord.ext import commands
from string import ascii_letters
from discord import SelectMenu, SelectOption
from yt_dlp import YoutubeDL, utils

class FileBin():
    def upload(filepath: str, filename: str):
        api = 'https://filebin.net/'
        bin = ''.join(random.choice(ascii_letters) for i in range(18))
        r = requests.post(f'{api}{bin}/{filename}', data=open(filepath, 'rb')).json()
        dl_url = api+r['bin']['id']+'/'+r['file']['filename']
        return dl_url

class Downloader():
    def __init__(self, client: discord.Client, cookie_file: str):
        self.client = client
        self.dl_ytops = {
            'cookiefile': cookie_file,
            'noplaylist': True
        }

    def getUrlInfo(self, url: str):
        video_resolutions = []
        try:
            with YoutubeDL({'noplaylist': True}) as ydl:
                info = ydl.extract_info(url, download=False)
        except Exception as e:
            raise e
        
        for format in info['formats']:
            if format['format_note'][-1] == 'p' and format['format_note'] not in video_resolutions:
                video_resolutions.append(format['format_note'])

        return info, video_resolutions

    async def getUserChoice(self, ctx: commands.Context, url: str):
        try:
            info, video_resolutions = self.getUrlInfo(url)
        except utils.DownloadError as e:
            embed=discord.Embed(title='The link is broken, can\'t fetch data', color=0xfe4b81)
            await ctx.send(embed=embed)
            raise e
        video_title = info['title']
        title = 'Available formats for'

        options = []
        options.append(SelectOption(emoji='🔊', label='Audio Only', value='1', description='.webm'))
        for i, res in enumerate(video_resolutions):
            options.append(SelectOption(emoji='🎥', label=res, value=f'{i+2}', description='.mp4'))

        embed=discord.Embed(title=title, description=f'[{video_title}]({url})', color=0xfe4b81)
        emb = await ctx.send(embed=embed, components=[
            [
                SelectMenu(
                    custom_id='_select_it',
                    options=options,
                    placeholder='Select a format',
                    max_values=1,
                    min_values=1 
                )
            ]
        ])

        def check_selection(i: discord.Interaction, select_menu):
            return i.author == ctx.author and i.message == emb

        interaction, select_menu = await self.client.wait_for('selection_select', check=check_selection)
        if int(select_menu.values[0]) == 1:
            format = 'bestaudio'
            ext = 'webm'
            embed=discord.Embed(title='Preparing your file please bear with us...', color=0xfe4b81)
            await interaction.respond(embed=embed, hidden=True)
            await self.downloadAndSendFile(ctx, url, format, ext)
        else:
            resolution = video_resolutions[int(select_menu.values[0])-2][:-1]
            format = f'bestvideo[height<={resolution}]+bestaudio/best[height<={resolution}]'
            ext = 'mp4'
            embed=discord.Embed(title='Preparing your file please bear with us...', color=0xfe4b81)
            await interaction.respond(embed=embed, hidden=True)
            await self.downloadAndSendFile(ctx, url, format, ext)

    async def downloadAndSendFile(self, ctx: commands.Context, url: str, format: str, ext: str):
        ytops = self.dl_ytops
        ytops['format'] = format
        ytops['merge_output_format'] = ext

        with tempfile.TemporaryDirectory(prefix='neodium_dl_') as tempdirname:
            ytops['outtmpl'] = f'{tempdirname}/%(title)s_[%(resolution)s].%(ext)s'
            with YoutubeDL(ytops) as ydl:
                info = ydl.extract_info(url, download=True)

            title = info['title']
            re = info['resolution']
            filename = f'{title}_[{re}].{ext}'
            filepath = f'{tempdirname}/{filename}'

            try:
                embed=discord.Embed(title='Your file is ready to download', color=0xfe4b81)
                await ctx.send(embed=embed, file=discord.File(filepath))
            except Exception as e:
                embed=discord.Embed(title='Its taking too long', description='Probably due to file exceeding server upload limit. Don\'t worry we are shiping it to you through filebin, please bear with us.', color=0xfe4b81)
                await ctx.send(embed=embed, delete_after=10)
                dl_url = FileBin.upload(filepath, filename)
                embed=discord.Embed(title='Your file is ready to download', description=f'[{filename}]({dl_url})\n\n**Powered by [filebin.net](https://filebin.net/)**', color=0xfe4b81)
                await ctx.send(embed=embed)
                raise e
        
class YTdownload(Downloader):
    def __init__(self, client: discord.Client):
        cookie_file = 'yt_cookies.txt'
        super().__init__(client, cookie_file)

    async def downloadVideo(self, ctx, url):
        await self.getUserChoice(ctx, url)

class INSdownload(Downloader):
    def __init__(self, client: discord.Client):
        self.cookie_file = 'insta_cookies.txt'
        super().__init__(client, self.cookie_file)

    async def downloadVideo(self, ctx, url):
        try:
            with YoutubeDL({'cookiefile': self.cookie_file}) as ydl:
                info = ydl.extract_info(url, download=False)
        except utils.DownloadError as e: # try to revive the file through requests, also a private system is to be made
            embed=discord.Embed(title='The link might not be AV or the account is private', color=0xfe4b81)
            await ctx.send(embed=embed)
            raise e
        except Exception as e:
            raise e
        video_title = info['title']
        title = 'Available formats for'

        options = []
        options.append(SelectOption(emoji='🔊', label='Audio Only', value='1', description='.webm'))
        options.append(SelectOption(emoji='🎥', label='Audio and Video', value='2', description='.mp4'))

        embed=discord.Embed(title=title, description=f'[{video_title}]({url})', color=0xfe4b81)
        emb = await ctx.send(embed=embed, components=[
            [
                SelectMenu(
                    custom_id='_select_it',
                    options=options,
                    placeholder='Select a format',
                    max_values=1,
                    min_values=1 
                )
            ]
        ])

        def check_selection(i: discord.Interaction, select_menu):
            return i.author == ctx.author and i.message == emb

        interaction, select_menu = await self.client.wait_for('selection_select', check=check_selection)
        if int(select_menu.values[0]) == 1:
            format = 'bestaudio'
            ext = 'webm'
            embed=discord.Embed(title='Preparing your file please bear with us...', color=0xfe4b81)
            await interaction.respond(embed=embed, hidden=True)
            await self.downloadAndSendFile(ctx, url, format, ext)
            
        else:
            format = 'bestvideo+bestaudio/best'
            ext = 'mp4'
            embed=discord.Embed(title='Preparing your file please bear with us...', color=0xfe4b81)
            await interaction.respond(embed=embed, hidden=True)
            await self.downloadAndSendFile(ctx, url, format, ext)