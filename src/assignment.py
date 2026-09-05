import datetime

import discord

import main
import src.db
from src import invite
from src.db import Status, School


def prettydate(x: datetime.datetime) -> str:
    return x.strftime("%a. %Y-%m-%d %H:%M %Z")


class AssignmentSys:
    def __init__(self, bot: main.ClassesBot, db: src.db.ClassesDB) -> None:
        self.bot = bot
        self.db = db

        # self.invite_timeout = datetime.timedelta(hours=36)
        self.invite_timeout = datetime.timedelta(
            minutes=2
        )  # TODO: Reset after tests

    async def fetch_or_deny(self, user_id: int) -> discord.User | None:
        try:
            return await self.bot.fetch_user(user_id)
        except discord.NotFound:
            self.bot.logger.error("User %s could not be found", user_id)
            self.db.set_enrollment_status(user_id, Status.Denied)


    async def send_wait_msg_and_set_status(self, user_id: int):
        user = await self.bot.fetch_user(user_id)
        if user is None:  # TODO: use fetch_or_deny instead and combine with send_invite_and_set_status
            return

        self.bot.logger.info("User %s has been sent a wait message", user_id)

        view = invite.WaitView(self.bot)
        try:
            msg = await user.send(
                "Hey, sadly you didn't get selected this time. You're still in the "
                "queue and might still get a position if someone else doesn't accept "
                "their invite. \n"
                "If you don't want to be in the queue, you can use the button.",
                view=view,
            )

            self.db.set_enrollment_status(user_id, Status.Waiting, msg.id)
        except discord.Forbidden:
            self.bot.logger.info(
                f"user {user_id} had their DMs closed during assignment"
            )
            self.db.set_enrollment_status(user_id, Status.Denied)

    async def send_invite_and_set_status(self, user_id: int, school: School):
        old_msg_id = self.db.get_users_message(user_id)
        user = await self.bot.fetch_user(user_id)

        self.bot.logger.info("User %s has been invited into %s", user_id, school)

        if old_msg_id is not None:
            old_message = await user.fetch_message(old_msg_id)
            await old_message.delete()

        expires_at = datetime.datetime.now(main.TZ) + self.invite_timeout

        view = invite.InviteView(self.bot)
        try:
            msg = await user.send(
                f"You have been selected to join {school.display}.\n"
                f"Please accept or decline by {prettydate(expires_at)} or your "
                f"place will go to the next person.",
                view=view,
            )

            self.db.set_enrollment_status(
                user_id,
                Status.Pending,
                msg.id,
                expiry=expires_at,
                school=school,
            )
        except discord.Forbidden:
            self.bot.logger.info(
                f"user {user_id} had their DMs closed during assignment"
            )
            self.db.set_enrollment_status(user_id, Status.Denied)

    async def expire_and_deny(self, user_id: int, msg_id: int):
        old_msg_id = self.db.get_users_message(user_id)
        user = await self.bot.fetch_user(user_id)

        self.bot.logger.info("Users %s invite expired", user_id)

        if old_msg_id is not None:
            old_message = await user.fetch_message(old_msg_id)
            await old_message.delete()

            try:
                await user.send("Your invite has expired.")
            except discord.Forbidden:
                self.bot.logger.error("User %s has their DMs closed.", user_id)
        else:
            # This path would suggests that the user never received an invite.
            # In this case let's just silently ignore this to avoid crashes.
            pass  # for now?

        self.db.set_enrollment_status(user_id, Status.Denied)

    async def recreate(self):
        """Recreate all the assignments and orders."""
        self.db.reset_enrolls()

    async def advance_states(self):
        """Advances the state machine for the enrolls of the students.
        See the SVG for more info.

        Specifically the dashed lines are covered here while the solid lines are
        activated by the user clicking on a button.

        The Unsent->Denied transitions are covered in `send_invite_and_set_status`
        and `reset_enrolls`.

        """
        # Advance Pending->Denied (expiry)
        for user, msg in self.db.get_expired_invites(
            datetime.datetime.now(main.TZ)
        ):
            await self.expire_and_deny(user, msg)

        # Advance Waiting->Pending (queue)
        await self.move_to_pending(Status.Waiting)

        # Advance Unsent->Pending (queue)
        await self.move_to_pending(Status.Unsent)

        # Advance Unsent->Waiting (queue)
        while x := self.db.get_queue_top(Status.Unsent, []):
            user_id, _ = x
            await self.send_wait_msg_and_set_status(user_id)
        # Given that this is called right after Unsent->Pending this shouldn't
        # send someone waiting who shouldn't be. Otherwise it wouldn't be so bad,
        # as the next iteration will clean it up.

    async def move_to_pending(self, status: Status):
        while x := self.db.get_queue_top(status, self.db.get_full_schools()):
            user_id, school = x
            await self.send_invite_and_set_status(user_id, school)
