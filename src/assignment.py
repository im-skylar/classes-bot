import main
from main import TZ
import src.db
from src import invite
from src.db import Status, School

import datetime

prettydate = lambda x: x.datetime.datetime.strftime("%a. %Y-%m-%d %H:%M %Z")

class AssignmentSys:
    def __init__(self, bot: main.ClassesBot, db: src.db.ClassesDB) -> None:
        self.bot = bot
        self.db = db
        
        self.invite_timeout = datetime.timedelta(hours=36)
    
    async def send_wait_msg(self, user_id: int):
        user = await self.bot.fetch_user(user_id)

        view = invite.WaitView(self.bot)
        msg = await user.send(
            "Hey, sadly you didn't get selected this time. You're still in the queue and might still get a position if someone else doesn't accept their invite.\nIf you don't want to be in the queue, you can use the button.",
            view=view
        )

        self.db.set_enrollment_status(user_id, Status.Waiting, msg.id, msg.channel.id)

    async def send_invite(self, user_id: int, school: School):
        user = await self.bot.fetch_user(user_id)
        expires_at = datetime.datetime.now(TZ) + self.invite_timeout

        view = invite.InviteView(self.bot)
        msg = await user.send(
            f"You have been selected to join {school}. "
            f"Please accept or decline by {prettydate(expires_at)} or your place will go to the next person.",
            view=view
        )

        self.db.set_enrollment_status(user_id, Status.Pending, msg.id, msg.channel.id, expires_at)

    async def send_next_invite(self):
        self.bot.logger.error("Next invite not implemented!")

