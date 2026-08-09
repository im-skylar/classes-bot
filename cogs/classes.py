import discord
from discord import app_commands
from discord.ext import commands

from src.checks import Checks
from main import ClassesBot
from src.db import School


class ClassesCog(commands.Cog):
    def __init__(self, bot):
        self.bot: ClassesBot = bot
        self.checks = Checks()

        self.is_admin = lambda inter: self.checks.has_role(inter, self.bot.admin_role_id, "admin")

        self.max_prio = 3

        self.no_2_choices_warning = "If you don't have 2 preferences selected when applications close, you won't get higher priority if you don't get assigned."
        self.how_choose = "You can set these with `/choose-prefs`."


    @app_commands.command(
        name="choose-prefs",
        description="Choose which school you'd prefer to enroll in. (Giving no second choice decreases your chances)"
    )
    async def select_enrollment_choice(self, inter: discord.Interaction, first_choice: School, second_choice: School|None):
        if first_choice == second_choice:
            return await inter.response.send_message("Please choose two different schools or leave the second choice empty, if there's only one school you'd like to enroll in.")

        self.bot.db.update_choices(inter.user.id, first_choice, second_choice)

        return await inter.response.send_message("Your choices were updated.\nYou can change them any time by calling this command again or using `/remove-prefs` if you don't want to be assigned next semester.\n"+self.no_2_choices_warning)

    @app_commands.command(
        name="remove-prefs",
        description="Retract you preferences. You won't get assigned next semester and won't gain priority."
    )
    async def remove_enrollment_choices(self, inter: discord.Interaction):
        self.bot.db.update_choices(inter.user.id, None, None)

        return await inter.response.send_message("Your choices were removed. You won't get assigned this semester.\nYou can add them again by calling `/choose-prefs`.\n"+self.no_2_choices_warning)

    @app_commands.command(
        name="list-prefs",
        description="List your current preferences"
    )
    async def list_enrollment_choices(self, inter: discord.Interaction):
        choices = self.bot.db.get_choices(inter.user.id)

        if choices is None or choices == (None, None):
            return await inter.response.send_message("You don't have any preferences set.\nYou can add them with `/choose-prefs`.\n"+self.no_2_choices_warning)

        if choices[1] is None:
            return await inter.response.send_message(f"Your first choice is \"{School(choices[0]).display}\". You don't have a second choice set.\n{self.how_choose} "+self.no_2_choices_warning)

        return await inter.response.send_message(f"Your first choice is \"{School(choices[0]).display}\". Your second choice is \"{School(choices[1]).display}\".\n{self.how_choose}")

    def _school_assignment(self, school: School, prio: int, capacities: dict[School, int], second_choice=False):
        if capacities[school] <= 0:
            return

        applicants = self.bot.db.find_applicants(prio, school, capacities[school], second_choice)
        self.bot.logger.debug(f"Found applicants {applicants} for school {school} and prio{prio}")


        capacities[school] -= len(applicants)

        self.bot.db.enroll_applicants(school, [app[0] for app in applicants])


    @app_commands.command(
        name="close-applications",
        description="Close applications and sort applicants into schools."
    )
    async def close_applications(self, inter: discord.Interaction):
        if not await self.is_admin(inter):
            return

        self.bot.logger.info("Closing applications")

        self.bot.db.assign_aptitudes()

        #await inter.followup.send("Applications closed and aptitudes assigned.")

        capacities = {School(k): v for k, v in self.bot.db.get_schools()}

        self.bot.logger.info(f"Detected capacities {capacities}")

        for prio in reversed(range(self.max_prio+1)):
            self.bot.logger.debug(f"Assigning prio {prio}")
            for school in School:
                self._school_assignment(school, prio, capacities, False)
                self._school_assignment(school, prio, capacities, True)

        await inter.response.send_message("Enrollments created. Use `/list-enrollments` to list them.")

    @app_commands.command(
        name="list-enrollments",
        description="list all the enrollments generated (pinging all enrolled people)"
    )
    async def list_enrollments(self, inter: discord.Interaction):
        if not await self.is_admin(inter):
            return

        msg = ""
        for school in School:
            msg = msg + f"**{school.display}:**\n"

            msg = msg + "\n".join([f"- <@{app}>" for app in self.bot.db.get_enrollments(school)])
            msg = msg + "\n"

        await inter.response.send_message(msg)








        
        





    


async def setup(bot):
    await bot.add_cog(ClassesCog(bot))