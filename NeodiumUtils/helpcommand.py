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
import asyncio
import discord
from discord.ext import commands
from discord import SelectMenu, SelectOption

class NeodiumHelpCommand(commands.HelpCommand):
    def __init__(self):
        super().__init__()

    async def send_bot_help(self, mapping):
        cog_embeds = {}
        embed=discord.Embed(title='Neodium', description='A bot built by [pritam20ps05](https://github.com/pritam20ps05) made to enhance the experience of music by integrating it into discord. This bot was initially made to replace groovy after its discontinuation but it became something much more than that. This is a vanilla(original) version of the open source project neodium, checkout on github for extended documentation.', url='https://github.com/pritam20ps05/neodium', color=0xfe4b81)
        embed.set_footer(text='Built on neodium core v1.2 by pritam20ps05', icon_url='https://user-images.githubusercontent.com/49360491/170466737-afafd7aa-f067-4503-9a1d-7d74de1b474b.png')
        options = []
        for cog in mapping:
            if cog:
                cog_embeds[cog.qualified_name] = discord.Embed(title=cog.qualified_name, description=cog.description, color=0xfe4b81)
                command_names = []
                for command in mapping[cog]:
                    command_names.append(command.name)
                    alias = ''
                    if command.aliases != []:
                        alias = f', {self.context.prefix}{command.aliases[0]}'
                    cog_embeds[cog.qualified_name].add_field(name=f'{self.context.prefix}{command.name}{alias}', value=command.help)
                cog_embeds[cog.qualified_name].set_footer(text=f'Use {self.context.prefix}help {cog.qualified_name} or {self.context.prefix}help <cmd> to see more details')
                options.append(SelectOption(label=cog.qualified_name, value=cog.qualified_name, description=', '.join(command_names[:4])))

        select_menu_context = SelectMenu(
                    custom_id='_help_select_it',
                    options=options,
                    placeholder='Select a command type for its help',
                    max_values=1,
                    min_values=1 
                )

        msg = await self.get_destination().send(embed=embed, components=[
            [select_menu_context]
        ])
        
        def check_selection(i: discord.Interaction, select_menu):
            return i.author == self.context.author and i.message == msg

        async def selection_callback(msg, interaction: discord.Interaction, select_menu):
            await interaction.defer()
            await msg.edit(embed=cog_embeds[select_menu.values[0]])

        select_menu: SelectMenu = None

        try:
            while True:
                interaction, select_menu = await self.context.bot.wait_for('selection_select', check=check_selection, timeout=30.0)
                await selection_callback(msg, interaction, select_menu)
        except asyncio.TimeoutError:
            select_menu_context.disabled = True
            if not select_menu:
                await msg.edit(embed=embed, components=[[select_menu_context]])
            else:
                await msg.edit(embed=cog_embeds[select_menu.values[0]], components=[[select_menu_context]])


    async def send_cog_help(self, cog):
        command_embeds = {}
        embed=discord.Embed(title=cog.qualified_name, description=cog.description, color=0xfe4b81)
        embed.set_footer(text='Built on neodium core v1.2 by pritam20ps05', icon_url='https://user-images.githubusercontent.com/49360491/170466737-afafd7aa-f067-4503-9a1d-7d74de1b474b.png')
        commands = cog.get_commands()
        options = []
        for command in commands:
            alias = ''
            if command.aliases != []:
                alias = f', {self.context.prefix}{command.aliases[0]}'
            embed.add_field(name=f'{self.context.prefix}{command.name}{alias}', value=command.help)
            command_embeds[command.name] = discord.Embed(title=f'{self.context.prefix}{command.name}{alias} {command.signature}', description=command.help, color=0xfe4b81)
            command_embeds[command.name].set_footer(text=f'Use {self.context.prefix}help {command.name} to see only this message')
            options.append(SelectOption(label=command.name, value=command.name))

        select_menu_context = SelectMenu(
                    custom_id='_help_command_select_it',
                    options=options,
                    placeholder='Select a command for its help',
                    max_values=1,
                    min_values=1 
                )

        msg = await self.get_destination().send(embed=embed, components=[
            [select_menu_context]
        ])
        
        def check_selection(i: discord.Interaction, select_menu):
            return i.author == self.context.author and i.message == msg

        async def selection_callback(msg, interaction: discord.Interaction, select_menu):
            await interaction.defer()
            await msg.edit(embed=command_embeds[select_menu.values[0]])

        select_menu: SelectMenu = None

        try:
            while True:
                interaction, select_menu = await self.context.bot.wait_for('selection_select', check=check_selection, timeout=30.0)
                await selection_callback(msg, interaction, select_menu)
        except asyncio.TimeoutError:
            select_menu_context.disabled = True
            if not select_menu:
                await msg.edit(embed=embed, components=[[select_menu_context]])
            else:
                await msg.edit(embed=command_embeds[select_menu.values[0]], components=[[select_menu_context]])


    async def send_command_help(self, command):
        alias = ''
        if command.aliases != []:
            alias = f', {self.context.prefix}{command.aliases[0]}'
        embed = discord.Embed(title=f'{self.context.prefix}{command.name}{alias} {command.signature}', description=command.help, color=0xfe4b81)
        embed.set_footer(text='Built on neodium core v1.2 by pritam20ps05', icon_url='https://user-images.githubusercontent.com/49360491/170466737-afafd7aa-f067-4503-9a1d-7d74de1b474b.png')
        await self.get_destination().send(embed=embed)