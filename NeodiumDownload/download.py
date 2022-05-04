import tempfile
import discord
import random
import asyncio
import aiohttp
import concurrent.futures
from os import remove
from shlex import quote
from discord.ext import commands
from json import load, dumps
from string import ascii_letters
from discord import SelectMenu, SelectOption
from yt_dlp import YoutubeDL, utils
from yt_dlp.extractor.instagram import InstagramBaseIE


async def ffmpegPostProcessor(inputfile, vc, ac, ext):
    outfilename = inputfile.split('/')[-1]
    outfiledir = '/'.join(inputfile.split('/')[:-1])+'/output/'
    outfile_name = outfilename.split('.')
    outfile_name[-1] = ext
    outfile = outfiledir+'.'.join(outfile_name)
    mkprocess = await asyncio.create_subprocess_shell(f'mkdir {outfiledir}')
    await mkprocess.wait()
    inputfile_sh = quote(inputfile)
    outfile_sh = quote(outfile)
    ffprocess = await asyncio.create_subprocess_shell(f'ffmpeg -i {inputfile_sh} -c:v {vc} -c:a {ac} {outfile_sh}')
    await ffprocess.wait()
    return outfile

async def ydl_async(url, ytops, d):
    def y_dl(url, ytops, d):
        with YoutubeDL(ytops) as ydl:
            info = ydl.extract_info(url, download=d)
        return info
    loop = asyncio.get_running_loop()
    with concurrent.futures.ThreadPoolExecutor() as pool:
        result = await loop.run_in_executor(pool, y_dl, url, ytops, d)
    return result

class FileBin():
    async def upload(filepath: str, filename: str):
        api = 'https://filebin.net/'
        bin = ''.join(random.choice(ascii_letters) for _ in range(18))
        async with aiohttp.ClientSession() as session:
            with open(filepath, 'rb') as f:
                async with session.post(f'{api}{bin}/{filename}', data=f) as resp:
                    r = await resp.json()
        dl_url = api+r['bin']['id']+'/'+r['file']['filename']
        return dl_url

class Downloader():
    def __init__(self, client: discord.Client, cookie_file: str):
        self.client = client
        self.dl_ytops = {
            'cookiefile': cookie_file,
            'noplaylist': True
        }
        self.vcodecs = ['h264', 'copy']

    async def getUrlInfo(self, url: str):
        video_resolutions = []
        try:
            info = await ydl_async(url, {'noplaylist': True}, False)
        except Exception as e:
            raise e
        
        for format in info['formats']:
            if 'p' in format['format_note'] and format['format_note'] not in video_resolutions:
                video_resolutions.append(format['format_note'])

        return info, video_resolutions

    async def getUserChoice(self, ctx: commands.Context, url: str, copt: int):
        try:
            info, video_resolutions = await self.getUrlInfo(url)
        except utils.DownloadError as e:
            embed=discord.Embed(title='The link is broken, can\'t fetch data', color=0xfe4b81)
            await ctx.send(embed=embed, delete_after=15)
            raise e
        video_title = info['title']
        title = 'Available formats for'

        options = []
        options.append(SelectOption(emoji='🔊', label='Audio Only', value='1', description='.m4a'))
        for i, res in enumerate(video_resolutions):
            options.append(SelectOption(emoji='🎥', label=res, value=res, description='.mp4'))

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

        interaction, select_menu = await self.client.wait_for('selection_select', check=check_selection, timeout=30.0)
        if str(select_menu.values[0]) == '1':
            format = 'bestaudio'
            ext = 'm4a'
            embed=discord.Embed(title='Preparing your file please bear with us...', description='This might take some time due to recent codec convertion update. We will let you know when your file gets ready', color=0xfe4b81)
            await interaction.respond(embed=embed, hidden=True)
            await self.downloadAndSendFile(ctx, url, format, ext, copt)
        else:
            format_note = select_menu.values[0]
            format = f'bestvideo[format_note={format_note}]+bestaudio/best'
            ext = 'mp4'
            embed=discord.Embed(title='Preparing your file please bear with us...', description='This might take some time due to recent codec convertion update. We will let you know when your file gets ready', color=0xfe4b81)
            await interaction.respond(embed=embed, hidden=True)
            await self.downloadAndSendFile(ctx, url, format, ext, copt)

    async def downloadAndSendFile(self, ctx: commands.Context, url: str, format: str, ext: str, copt: int, usrcreds=None):
        if usrcreds:
            ytops = usrcreds
        else:
            ytops = self.dl_ytops
        ytops['format'] = format
        ytops['merge_output_format'] = ext
        InstagramBaseIE._IS_LOGGED_IN = False

        with tempfile.TemporaryDirectory(prefix='neodium_dl_') as tempdirname:
            ytops['outtmpl'] = f'{tempdirname}/%(title)s_[%(resolution)s].%(ext)s'
            with YoutubeDL(ytops) as ydl:
                info = await ydl_async(url, ytops, True)
                filepath = ydl.prepare_filename(info)
                filepath = await ffmpegPostProcessor(filepath, self.vcodecs[copt], 'aac', ext)
                filename = filepath.split('/')[-1]

            try:
                embed=discord.Embed(title='Your file is ready to download', description=f'File requested by {ctx.author.mention}', color=0xfe4b81)
                if usrcreds:
                    await ctx.author.send(embed=embed, file=discord.File(filepath))
                    await ctx.author.send(f'{ctx.author.mention} your file is ready please download it.', delete_after=60)
                else:
                    await ctx.send(embed=embed, file=discord.File(filepath))
                    await ctx.send(f'{ctx.author.mention} your file is ready please download it.', delete_after=60)
            except Exception as e:
                embed=discord.Embed(title='Its taking too long', description='Probably due to file exceeding server upload limit. Don\'t worry we are shiping it to you through filebin, please bear with us.', color=0xfe4b81)
                await ctx.send(embed=embed, delete_after=20)
                dl_url = await FileBin.upload(filepath, filename)
                embed=discord.Embed(title='Your file is ready to download', description=f'[{filename}]({dl_url})\nFile requested by {ctx.author.mention}\n\n**Powered by [filebin.net](https://filebin.net/)**', color=0xfe4b81)
                if usrcreds:
                    await ctx.author.send(embed=embed)
                    await ctx.author.send(f'{ctx.author.mention} your file is ready please download it.', delete_after=60)
                else:
                    await ctx.send(embed=embed)
                    await ctx.send(f'{ctx.author.mention} your file is ready please download it.', delete_after=60)
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

    async def downloadVideo(self, ctx, url, copt, usrcreds):
        if usrcreds:
            ops = usrcreds
        else:
            ops = {
                'cookiefile': self.cookie_file
            }

        InstagramBaseIE._IS_LOGGED_IN = False
        try:
            info = await ydl_async(url, ops, False)
        except utils.DownloadError as e: # try to revive the file through requests, also a private system is to be made
            if usrcreds:
                embed=discord.Embed(title='The link might not be AV or the account is private or try relogging', color=0xfe4b81)
                await ctx.send(embed=embed, delete_after=15)
            else:
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

        interaction, select_menu = await self.client.wait_for('selection_select', check=check_selection, timeout=30.0)
        if str(select_menu.values[0]) == '1':
            format = 'bestaudio'
            ext = 'm4a'
            embed=discord.Embed(title='Preparing your file please bear with us...', description='This might take some time due to recent codec convertion update. We will let you know when your file gets ready', color=0xfe4b81)
            await interaction.respond(embed=embed, hidden=True)
            await self.downloadAndSendFile(ctx, url, format, ext, copt, usrcreds)
            
        else:
            format = 'bestvideo+bestaudio/best'
            ext = 'mp4'
            embed=discord.Embed(title='Preparing your file please bear with us...', description='This might take some time due to recent codec convertion update. We will let you know when your file gets ready', color=0xfe4b81)
            await interaction.respond(embed=embed, hidden=True)
            await self.downloadAndSendFile(ctx, url, format, ext, copt, usrcreds)

class private_login():
    creds = {}
    cred_path = ''
    def __init__(self, cred_path):
        private_login.cred_path = cred_path
        
        try:
            with open(cred_path) as f:
                private_login.creds = load(f)
        except:
            with open(cred_path, 'w') as f:
                f.write('{}')
            with open(cred_path) as f:
                private_login.creds = load(f)

    def flush_data(self):
        dump_data = dumps(private_login.creds, indent=4)

        with open(private_login.cred_path, "w") as outfile:
            outfile.write(dump_data)

    def unique_keygen(self, chs=6):
        return ''.join(random.choice(ascii_letters) for _ in range(chs))

    async def login(self, ctx: commands.Context, usrn, passw):
        is_username_valid = True
        is_password_valid = True
        has_process_failed = False
        ukey = self.unique_keygen()

        if not self.is_user_authenticated(ctx.author.id):
            ops = {
                'username': usrn,
                'password': passw,
                'extract_flat': True,
                'cookiefile': f'userdata/{ukey}_cookie.txt'
            }
            InstagramBaseIE._IS_LOGGED_IN = False

            try:
                _ = await ydl_async('https://www.instagram.com/p/Cbj-9Tglk_i/', ops, False)
            except utils.DownloadError as e:
                if 'The username you entered doesn\'t belong to an account' in e.msg:
                    is_username_valid = False
                elif 'your password was incorrect' in e.msg:
                    is_password_valid = False
                else:
                    has_process_failed = True
                    print(e)
            except Exception as e:
                has_process_failed = True
                print(e)

            if is_username_valid and is_password_valid and not has_process_failed:
                private_login.creds[str(ctx.author.id)] = {
                    'cookiefile': f'userdata/{ukey}_cookie.txt'
                }
                self.flush_data()
                embed=discord.Embed(title='You have been successfully authenticated', color=0xfe4b81)
                await ctx.send(embed=embed)
            elif has_process_failed:
                embed=discord.Embed(title='The authentication was not successfull', description='The authentication was not possible due to some reason. Make sure you have 2 factor auth disabled on your account. If the problem continues report it to the dev', color=0xfe4b81)
                await ctx.send(embed=embed)
            elif not is_username_valid:
                embed=discord.Embed(title='Invalid username', color=0xfe4b81)
                await ctx.send(embed=embed)
            elif not is_password_valid:
                embed=discord.Embed(title='Invalid password', color=0xfe4b81)
                await ctx.send(embed=embed)

    def is_user_authenticated(self, uid: str):
        if str(uid) in private_login.creds.keys():
            return True
        else:
            return False

    def get_usercreds(self, uid: str):
        if self.is_user_authenticated(str(uid)):
            return private_login.creds[str(uid)]
        else:
            return None

    async def logout(self, ctx: commands.Context):
        if self.is_user_authenticated(ctx.author.id):
            data = private_login.creds.pop(str(ctx.author.id))
            remove(data['cookiefile'])
            self.flush_data()
            embed=discord.Embed(title='You have been successfully logged out of your account', color=0xfe4b81)
            await ctx.send(embed=embed)
