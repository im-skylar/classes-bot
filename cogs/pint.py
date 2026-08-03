import discord
from discord import app_commands
from discord.ext import commands

class TestCog(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @app_commands.command(
        name="pint",
        description="Check the latency"
    )
    async def pint(self, inter: discord.Interaction) -> None:
        await inter.response.send_message(f"Pond! {round(self.bot.latency * 1000)}ms")

    @app_commands.command(
        name="uptime",
        description="Check how long the bot has been running"
    )
    async def uptime(self, inter: discord.Interaction) -> None:
        await inter.response.send_message(f"Uptime: {str(self.bot.uptime)}")

async def setup(bot):
    await bot.add_cog(TestCog(bot))