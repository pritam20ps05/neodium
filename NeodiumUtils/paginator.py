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
from discord.ext import commands
from discord import ActionRow, Button, ButtonStyle
from .vars import *

class Paginator():
    def __init__(self, bot: commands.Bot) -> None:
        self.bot = bot

    async def flushPage(self, embed: discord.Embed, components: list[ActionRow], msg: discord.Message, disable_btns=False, delete=False):
        for component in components:
            component.disable_all_buttons_if(check=disable_btns)
        if delete:
            await msg.edit(embed=embed, components=components, delete_after=15)
        else:
            await msg.edit(embed=embed, components=components)

    async def handlePages(self, embeds: list[discord.Embed], ctx: commands.Context):
        button_component = [ActionRow(
            Button(
                custom_id='first',
                label='❮❮',
                style=ButtonStyle.Primary
            ),
            Button(
                custom_id='back',
                label='❮',
                style=ButtonStyle.Primary
            ),
            Button(
                custom_id='next',
                label='❯',
                style=ButtonStyle.Primary
            ),
            Button(
                custom_id='last',
                label='❯❯',
                style=ButtonStyle.Primary
            )
        )]

        page_tracker = 0
        msg = await ctx.send(embed=embeds[page_tracker], components=button_component)

        def check(i: discord.Interaction, b):
            return i.message == msg and i.member == ctx.author

        try:
            while True:
                interaction, button = await self.bot.wait_for('button_click', check=check, timeout=30.0)
                await interaction.defer()
                if button.custom_id == 'first':
                    page_tracker = 0
                elif button.custom_id == 'back':
                    if page_tracker > 0:
                        page_tracker = page_tracker - 1
                elif button.custom_id == 'next':
                    if page_tracker < len(embeds) - 1:
                        page_tracker = page_tracker + 1
                elif button.custom_id == 'last':
                    page_tracker = len(embeds) - 1

                await self.flushPage(embed=embeds[page_tracker], components=button_component, msg=msg)
        except asyncio.TimeoutError:
            await self.flushPage(embed=embeds[page_tracker], components=button_component, msg=msg, disable_btns=True)

    async def handleOptions(self, embed: discord.Embed, nops: int, ctx: commands.Context):
        button_row = []
        for i in range(nops):
            button_row.append(
                Button(
                    custom_id=f'opt:{i}',
                    label=f'{i+1}',
                    style=ButtonStyle.Primary
                )
            )
        button_component = [ActionRow(*button_row)]
        msg = await ctx.send(embed=embed, components=button_component)

        def check(i: discord.Interaction, b):
            return i.message == msg and i.member == ctx.author

        try:
            interaction, button = await self.bot.wait_for('button_click', check=check, timeout=30.0)
            await interaction.defer()
            await self.flushPage(embed=embed, components=button_component, msg=msg, disable_btns=True)
            return int(button.custom_id.split(':')[1])
        except asyncio.TimeoutError as e:
            await self.flushPage(embed=embed, components=button_component, msg=msg, disable_btns=True)
            raise e

    async def handleDecision(self, embed: discord.Embed, resp_embed: discord.Embed, ctx: commands.Context, default=False):
        button_component = [ActionRow(
            Button(
                custom_id='yes',
                emoji='👍',
                style=ButtonStyle.Success
            ),
            Button(
                custom_id='no',
                emoji='👎',
                style=ButtonStyle.Danger
            )
        )]

        msg = await ctx.send(embed=embed, components=button_component)

        def check(i: discord.Interaction, b):
            return i.message == msg and i.member == ctx.author

        try:
            interaction, button = await self.bot.wait_for('button_click', check=check, timeout=30.0)
            await interaction.defer()
            if button.custom_id == 'yes':
                await self.flushPage(embed=resp_embed, components=button_component, msg=msg, disable_btns=True)
                return True
            else:
                await self.flushPage(embed=embed, components=button_component, msg=msg, disable_btns=True, delete=True)
                return False
        except asyncio.TimeoutError:
            if default:
                await self.flushPage(embed=resp_embed, components=button_component, msg=msg, disable_btns=True)
                return True
            else:
                await self.flushPage(embed=embed, components=button_component, msg=msg, disable_btns=True, delete=True)
                return False