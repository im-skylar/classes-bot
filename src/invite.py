import discord
from discord.ext import commands
from main import ClassesBot
from src.db import Status

class InviteView(discord.ui.View):
    def __init__(self, bot: ClassesBot):
        super().__init__(timeout=None)
        self.bot = bot

    @discord.ui.button(label="Accept", style=discord.ButtonStyle.green, custom_id="accept")
    async def accept(self, inter: discord.Interaction, button: discord.ui.Button):
        self.bot.db.accept_enrollment(inter.user.id)
        await inter.response.edit_message(content="You're in!", view=None)

    @discord.ui.button(label="Decline", style=discord.ButtonStyle.red, custom_id="deny")
    async def deny(self, inter: discord.Interaction, button: discord.ui.Button):
        self.bot.db.set_enrollment_status(inter.user.id, Status.Denied)
        await inter.response.edit_message(content="Declined.", view=None)
        await self.bot.assignments.send_next_invite(inter.user.id)
    

class WaitView(discord.ui.View):
    def __init__(self, bot: ClassesBot):
        super().__init__(timeout=None)
        self.bot = bot

    @discord.ui.button(label="Decline", style=discord.ButtonStyle.red, custom_id="deny")
    async def deny(self, inter: discord.Interaction, button: discord.ui.Button):
        self.bot.db.set_enrollment_status(inter.user.id, Status.Denied)
        await inter.response.edit_message(content="Declined.", view=None)
    

