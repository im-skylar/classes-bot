import datetime
import enum

import discord
from discord import app_commands
from discord.ext import commands

from src.checks import Checks
from main import ClassesBot

class School(enum.IntEnum):
    Alteration = 1
    Conjuration = 2
    Illusion = 3
    Restoration = 4
    General_Studies = 5

    @property
    def display(self):
        self.name.replace("_", " ")

class Weekday(int, enum.Enum):
    Monday = 0,
    Tuesday = 1,
    Wednesday = 2,
    Thursday = 3,
    Friday = 4,
    Saturday = 5,
    Sunday = 6

class ClassesCog(commands.Cog):
    def __init__(self, bot):
        self.bot: ClassesBot = bot
        self.checks = Checks()

        self.is_admin = lambda inter: self.checks.has_role(inter, self.bot.admin_role_id, "admin")

    @app_commands.command(
        name="list-schools",
        description="List all the schools"
    )
    async def list_schools(self, inter: discord.Interaction) -> None:
        classes = self.bot.db.get_schools()
        classesstr = "\n".join([str(x) for x in classes])

        if classesstr == "":
            classesstr = "No schools found :("

        await inter.response.send_message(classesstr)

    @app_commands.command(
        name="add-school",
        description="Add a school (capacity can later be changed)"
    )
    async def add_school(self, inter: discord.Interaction, name: str, capacity: int):
        if not await self.is_admin(inter):
            return

        if capacity < 0:
            await inter.response.send_message("capacity needs to be 0 or more")
            return

        id = self.bot.db.add_school(name, capacity)
        # maybe return class id here (ooooh maybe use fancy wordhash function!)
        await inter.response.send_message(f"Added class! New class \"{name}\" has id {id}.")

    @app_commands.command(
        name="modify-school",
        description="Change a schools name or capacity"
    )
    async def modify_school(self, inter: discord.Interaction, id: int, name: str|None, capacity: int|None):
        if not await self.is_admin(inter):
            return

        if capacity is None and name is None:
            await inter.response.send_message("No change occured :dotted_line_face:")
            return

        cap_name = self.bot.db.get_school_capacity_and_name(id)
        if cap_name is None:
            await inter.response.send_message(f"School with ID {id} not found")
            return

        if capacity is not None:
            if capacity < 0:
                await inter.response.send_message("capacity needs to be 0 or more")
                return
        else:
            capacity = cap_name[0]

        if name is None:
            name = cap_name[1]

        self.bot.db.update_school(id, name, capacity)

        await inter.response.send_message(f"Updated school {id} with new name \"{name}\" and {capacity}")

    @app_commands.command(
        name="delete-school",
        description="Delete a school, removing matching enrollments and preferences. This is final."
    )
    async def delete_school(self, inter:discord.Interaction, id: int):
        if not await self.is_admin(inter):
            return

        if not self.bot.db.school_exists(id):
            return await inter.response.send_message(f"School with ID {id} not found")

        self.bot.db.delete_school(id)
        await inter.response.send_message(f"School with ID {id} deleted.")

    @app_commands.command(
        name="choose",
        description="Choose which school you'd prefer to enroll in"
    )
    async def select_enrollment_choice(self, inter:discord.Interaction, first_choice: School, second_choice):
        if not await self.is_admin(inter):
            return

        if not self.bot.db.school_exists(id):
            return await inter.response.send_message(f"School with ID {id} not found")

        self.bot.db.delete_school(id)
        await inter.response.send_message(f"School with ID {id} deleted.")





    


async def setup(bot):
    await bot.add_cog(ClassesCog(bot))