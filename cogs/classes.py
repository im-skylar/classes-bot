import datetime

import discord
from discord import app_commands
from discord.ext import commands

class ClassesCog(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @app_commands.command(
        name="list-classes",
        description="List all the classes"
    )
    async def list_classes(self, inter: discord.Interaction) -> None:
        classes = self.bot.db.get_classes()
        classesstr = "\n".join([str(x) for x in classes])

        if classesstr == "":
            classesstr = "No classes exist yet :("

        await inter.response.send_message(classesstr)

    @app_commands.command(
        name="add-class",
        description="add a class with you as a tutor"
    )
    async def add_class(self, inter: discord.Interaction, name: str, dow: int, time: str):
        if not (self.bot.tutor_role_id in [x.id for x in inter.user.roles]):
            await inter.response.send_message("you need to be a tutor to create classes")
            return


        if not dow in range(1, 8):
            await inter.response.send_message("Day of week needs to be within 1 (Monday) - 7 (Sunday)")
            return

        try:
            t = datetime.time.strptime(time, "%H:%M")
        except ValueError:
            await inter.response.send_message("Time needs to be in HH:MM format (ie 16:45)")
            return

        self.bot.db.add_class(name, dow-1, time, inter.user.id)
        await inter.response.send_message("Added class!")
        # TODO: dow seems to default to 1 for some reason??




async def setup(bot):
    await bot.add_cog(ClassesCog(bot))