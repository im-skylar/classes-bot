import os
from dotenv import load_dotenv

import discord
from discord.ext import commands

load_dotenv()

DC_TOKEN = os.getenv("DISCORD")
if not DC_TOKEN:
    print("Missing discord Token in env")
    exit(1)

intents = discord.Intents.default()
bot = commands.Bot(command_prefix=commands.when_mentioned_or("!"), intents=intents)

async def setup_hook() -> None:
    await bot.tree.sync() # Sync slash commands to discord

bot.setup_hook = setup_hook




@bot.event
async def on_ready() -> None:
    print(f"Logged in as {bot.user}")


@bot.tree.command()
async def pint(inter: discord.Interaction) -> None:
    await inter.response.send_message(f"Pond! {round(bot.latency * 1000)}ms")

bot.run(DC_TOKEN)