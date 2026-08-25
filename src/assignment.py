import main
import src.db
from src import invite
from src.db import Status, School

import datetime

import discord

def prettydate(x: datetime.datetime) -> str:
    return x.strftime("%a. %Y-%m-%d %H:%M %Z")


class AssignmentSys:
    def __init__(self, bot: main.ClassesBot, db: src.db.ClassesDB) -> None:
        self.bot = bot
        self.db = db
        
        #self.invite_timeout = datetime.timedelta(hours=36)
        self.invite_timeout = datetime.timedelta(minutes=2)
    
    async def send_wait_msg_and_set_status(self, user_id: int):
        user = await self.bot.fetch_user(user_id)

        view = invite.WaitView(self.bot)
        msg = await user.send(
            "Hey, sadly you didn't get selected this time. You're still in the queue and might still get a position if someone else doesn't accept their invite.\nIf you don't want to be in the queue, you can use the button.",
            view=view
        )

        self.db.set_enrollment_status(user_id, Status.Waiting, msg.id)

    async def send_invite_and_set_status(self, user_id: int, school: School):
        old_msg_id = self.db.get_users_message(user_id)
        user = await self.bot.fetch_user(user_id)

        if old_msg_id is not None:
            old_message = await user.fetch_message(old_msg_id)
            await old_message.delete()

        expires_at = datetime.datetime.now(main.TZ) + self.invite_timeout

        view = invite.InviteView(self.bot)
        try:
            msg = await user.send(
                f"You have been selected to join {school.display}. "
                f"Please accept or decline by {prettydate(expires_at)} or your place will go to the next person.",
                view=view
            )

            self.db.set_enrollment_status(user_id, Status.Pending, msg.id, expiry=expires_at, school=school)
        except discord.Forbidden:
            self.bot.logger.info(f"user {user_id} had their DMs closed during assignment")
            # TODO: Mark them as denied
            await self.send_next_invite(user_id=user_id)


    async def send_next_invite(self, user_id: int, old_msg_id: int|None = None):
        school = self.db.get_users_school(user_id)

        if school is None:
            raise AssertionError

        if old_msg_id is not None:
            user = await self.bot.fetch_user(user_id)
            old_msg = await user.fetch_message(old_msg_id)
            self.db.set_enrollment_status(user_id, Status.Expired)
            await old_msg.edit(content="Your invite expired.", view=None)

        nextq = self.db.get_queue(school, 1, Status.Waiting)
        if len(nextq):
            await self.send_invite_and_set_status(nextq[0], school)
        else:
            self.bot.logger.info(f"No more applications for {school} left to assign.")


    async def recreate(self):
        """Recreate all the assignments and orders."""
        self.db.reset_enrolls()

    async def send_initial_invites_and_waits(self):
        # send invites
        for s, capacity in self.db.get_capacities():
            for student in self.db.get_queue(School(s), capacity, Status.Unsent):
                await self.send_invite_and_set_status(student, School(s))

        # send wait messages
        for s, _ in self.db.get_capacities():
            for student in self.db.get_queue(School(s), count=1000000000, status=Status.Unsent):
                await self.send_wait_msg_and_set_status(student)

