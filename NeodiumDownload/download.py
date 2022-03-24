import tempfile
import discord
import requests
import random
import subprocess
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

def ffmpegPostProcessor(inputfile, vc, ac, ext):
    outfilename = inputfile.split('/')[-1]
    outfiledir = '/'.join(inputfile.split('/')[:-1])+'/output/'
    outfile_name = outfilename.split('.')
    outfile_name[-1] = ext
    outfile = outfiledir+'.'.join(outfile_name)
    subprocess.run(['mkdir', outfiledir])
    subprocess.run(['ffmpeg', '-i', inputfile, '-c:v', vc, '-c:a', ac, outfile])
    return outfile

class Downloader():
    def __init__(self, client: discord.Client, cookie_file: str):
        self.client = client
        self.dl_ytops = {
            'cookiefile': cookie_file,
            'noplaylist': True
        }
        self.vcodecs = ['h264', 'copy']

    def getUrlInfo(self, url: str):
        video_resolutions = []
        video_formats = []
        try:
            with YoutubeDL({'noplaylist': True}) as ydl:
                info = ydl.extract_info(url, download=False)
        except Exception as e:
            raise e
        
        for format in info['formats']:
            if 'p' in format['format_note'] and format['format_note'] not in video_resolutions:
                video_resolutions.append(format['format_note'])
                video_formats.append(format['format_id'])

        return info, video_resolutions, video_formats

    async def getUserChoice(self, ctx: commands.Context, url: str, copt: int):
        try:
            info, video_resolutions, video_formats = self.getUrlInfo(url)
        except utils.DownloadError as e:
            embed=discord.Embed(title='The link is broken, can\'t fetch data', color=0xfe4b81)
            await ctx.send(embed=embed, delete_after=15)
            raise e
        video_title = info['title']
        title = 'Available formats for'

        options = []
        options.append(SelectOption(emoji='🔊', label='Audio Only', value='1', description='.m4a'))
        for i, res in enumerate(video_resolutions):
            options.append(SelectOption(emoji='🎥', label=res, value=video_formats[i], description='.mp4'))

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
            ext = 'm4a'
            embed=discord.Embed(title='Preparing your file please bear with us...', description='This might take some time due to recent codec convertion update. We will let you know when your file gets ready', color=0xfe4b81)
            await interaction.respond(embed=embed, hidden=True)
            await self.downloadAndSendFile(ctx, url, format, ext, copt)
        else:
            format_id = select_menu.values[0]
            format = f'{format_id}+bestaudio/best'
            ext = 'mp4'
            embed=discord.Embed(title='Preparing your file please bear with us...', description='This might take some time due to recent codec convertion update. We will let you know when your file gets ready', color=0xfe4b81)
            await interaction.respond(embed=embed, hidden=True)
            await self.downloadAndSendFile(ctx, url, format, ext, copt)

    async def downloadAndSendFile(self, ctx: commands.Context, url: str, format: str, ext: str, copt: int):
        ytops = self.dl_ytops
        ytops['format'] = format
        ytops['merge_output_format'] = ext

        with tempfile.TemporaryDirectory(prefix='neodium_dl_') as tempdirname:
            ytops['outtmpl'] = f'{tempdirname}/%(title)s_[%(resolution)s].%(ext)s'
            with YoutubeDL(ytops) as ydl:
                info = ydl.extract_info(url, download=True)
                filepath = ydl.prepare_filename(info)
                filepath = ffmpegPostProcessor(filepath, self.vcodecs[copt], 'aac', ext)
                filename = filepath.split('/')[-1]

            try:
                embed=discord.Embed(title='Your file is ready to download', color=0xfe4b81)
                await ctx.send(embed=embed, file=discord.File(filepath), mention_author=True)
            except Exception as e:
                embed=discord.Embed(title='Its taking too long', description='Probably due to file exceeding server upload limit. Don\'t worry we are shiping it to you through filebin, please bear with us.', color=0xfe4b81)
                await ctx.send(embed=embed, delete_after=10)
                dl_url = FileBin.upload(filepath, filename)
                embed=discord.Embed(title='Your file is ready to download', description=f'[{filename}]({dl_url})\n\n**Powered by [filebin.net](https://filebin.net/)**', color=0xfe4b81)
                await ctx.send(embed=embed, mention_author=True)
                raise e
        
class YTdownload(Downloader):
    def __init__(self, client: discord.Client):
        cookie_file = 'yt_cookies.txt'
        super().__init__(client, cookie_file)

    async def downloadVideo(self, ctx, url, copt):
        await self.getUserChoice(ctx, url, copt)

class INSdownload(Downloader):
    def __init__(self, client: discord.Client):
        self.cookie_file = 'insta_cookies.txt'
        super().__init__(client, self.cookie_file)

    async def downloadVideo(self, ctx, url, copt):
        try:
            with YoutubeDL({'cookiefile': self.cookie_file}) as ydl:
                info = ydl.extract_info(url, download=False)
        except utils.DownloadError as e: # try to revive the file through requests, also a private system is to be made
            embed=discord.Embed(title='The link might not be AV or the account is private', color=0xfe4b81)
            await ctx.send(embed=embed, delete_after=15)
            raise e
        except Exception as e:
            raise e
        video_title = info['title']
        title = 'Available formats for'

        options = []
        options.append(SelectOption(emoji='🔊', label='Audio Only', value='1', description='.m4a'))
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
            ext = 'm4a'
            embed=discord.Embed(title='Preparing your file please bear with us...', description='This might take some time due to recent codec convertion update. We will let you know when your file gets ready', color=0xfe4b81)
            await interaction.respond(embed=embed, hidden=True)
            await self.downloadAndSendFile(ctx, url, format, ext, copt)
            
        else:
            format = 'bestvideo+bestaudio/best'
            ext = 'mp4'
            embed=discord.Embed(title='Preparing your file please bear with us...', description='This might take some time due to recent codec convertion update. We will let you know when your file gets ready', color=0xfe4b81)
            await interaction.respond(embed=embed, hidden=True)
            await self.downloadAndSendFile(ctx, url, format, ext, copt)