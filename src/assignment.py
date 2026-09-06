from datetime import datetime as dt
from datetime import timedelta as td

import discord

import main
import src.db
from src import invite
from src.db import Status, School


def prettydate(x: dt) -> str:
    return x.strftime("%a. %Y-%m-%d %H:%M %Z")


class AssignmentSys:
    def __init__(self, bot: main.ClassesBot, db: src.db.ClassesDB) -> None:
        self.bot = bot
        self.db = db

        # self.invite_timeout = td(hours=36)
        self.invite_timeout = td(minutes=2)  # TODO: Reset after tests

    async def gen_invite_text(self, school: School, expiry: dt):
        return (
            f"You have been selected to join {school.display}.\n"
            f"Please accept or decline by {prettydate(expiry)} or your "
            f"place will go to the next person."
        )

    async def gen_wait_text(self):
        return (
            "Hey, sadly you didn't get selected this time. You're still in the "
            "queue and might still get a position if someone else doesn't accept "
            "their invite. \n"
            "If you don't want to be in the queue, you can use the button."
        )

    async def fetch_or_delete(self, user_id: int) -> discord.User | None:
        """Tries to get a user by their ID.

        If they can't be found their account
        was likely deleted, so we'll delete them from our DB as well.
        """
        try:
            return await self.bot.fetch_user(user_id)
        except discord.NotFound:
            self.bot.logger.error("User %s could not be found", user_id)
            self.db.delete_student(user_id)

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
        for user, _ in self.db.get_expired_invites(dt.now(main.TZ)):
            await self.send_msg_and_set_status(user, Status.Denied)

        # Advance Waiting->Pending (queue)
        await self.move_to_pending(Status.Waiting)

        # Advance Unsent->Pending (queue)
        await self.move_to_pending(Status.Unsent)

        # Advance Unsent->Waiting (queue)
        while x := self.db.get_queue_top(Status.Unsent, []):
            user_id, _ = x
            await self.send_msg_and_set_status(user_id, Status.Waiting)
        # Given that this is called right after Unsent->Pending this shouldn't
        # send someone waiting who shouldn't be. Otherwise it wouldn't be so bad,
        # as the next iteration will clean it up.

    async def move_to_pending(self, status: Status):
        while x := self.db.get_queue_top(status, self.db.get_full_schools()):
            user_id, school = x
            await self.send_msg_and_set_status(user_id, Status.Pending, school)

    async def send_msg_and_set_status(
        self, user_id: int, status: Status, school: School | None = None
    ):
        """Sends a user a message depending on `status` and updates their state
        in the DB.

        - `Pending`: Send an invite with _Accept_ and _Decline_ buttons.
        - `Waiting`: Send a waiting message with _Decline_ button.
        - `Denied`: Send an "Invite Expired" message.

        `School` must not be `None` if `status` is `Pending`.
        """
        old_msg_id = self.db.get_users_message(user_id)
        user = await self.fetch_or_delete(user_id)

        if user is None:
            return

        if old_msg_id is not None:
            old_message = await user.fetch_message(old_msg_id)
            await old_message.delete()

        expires_at = None
        match status:
            case Status.Pending:
                assert school is not None
                expires_at = dt.now(main.TZ) + self.invite_timeout
                view = invite.InviteView(self.bot)
                msg_text = await self.gen_invite_text(school, expires_at)
            case Status.Waiting:
                view = invite.WaitView(self.bot)
                msg_text = await self.gen_wait_text()
            case Status.Denied:
                view = discord.utils.MISSING
                msg_text = "Your invite has expired."
                self.bot.logger.info("Users %s invite expired", user_id)
            case s:
                self.bot.logger.error("Unexpected Status %s.", s.display)
                return

        # Extract this into "send" and "update" methods, keep try: in parent function
        try:
            msg = await user.send(content=msg_text, view=view)

            self.db.set_enrollment_status(
                user_id,
                status,
                msg.id,
                expiry=expires_at,
                school=school,
            )

            self.bot.logger.info("Updated user %s to %s", user_id, status.display)
        except discord.Forbidden:
            self.bot.logger.info(
                f"user {user_id} had their DMs closed during assignment"
            )
            self.db.set_enrollment_status(user_id, Status.Denied)
