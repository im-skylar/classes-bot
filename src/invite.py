import discord

from main import ClassesBot
from src.db import Status, School


class BaseView(discord.ui.View):
    def __init__(self, bot: ClassesBot):
        super().__init__(timeout=None)
        self.bot = bot

    async def interaction_check(self, inter: discord.Interaction) -> bool:
        assert inter.message is not None
        if not self.bot.db.message_exists(inter.message.id):
            await inter.response.edit_message(
                content="This message expired.", view=None
            )
            return False

        return True

    @discord.ui.button(
        label="Decline", style=discord.ButtonStyle.red, custom_id="deny"
    )
    async def deny(self, inter: discord.Interaction, button: discord.ui.Button):
        self.bot.db.set_enrollment_status(inter.user.id, Status.Denied)
        await inter.response.edit_message(content="Declined.", view=None)


class InviteView(BaseView):
    def __init__(self, bot: ClassesBot):
        super().__init__(bot)

    @discord.ui.button(
        label="Accept", style=discord.ButtonStyle.green, custom_id="accept"
    )
    async def accept(
        self, inter: discord.Interaction, button: discord.ui.Button
    ):
        self.bot.db.accept_enrollment(inter.user.id)
        school = self.bot.db.get_users_school(inter.user.id)
        schoolstr = School(school).display if school is not None else "None"
        await inter.response.edit_message(
            content=f"You're in {schoolstr}!", view=None
        )


class WaitView(BaseView):
    def __init__(self, bot: ClassesBot):
        super().__init__(bot)
