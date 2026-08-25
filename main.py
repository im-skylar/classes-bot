import os
import datetime
import logging
import typing
import traceback

from dotenv import load_dotenv

import discord
from discord.ext import commands, tasks

import src.db as db
import src.invite as invite
from src.assignment import AssignmentSys

TZ = datetime.timezone.utc



class ClassesBot(commands.Bot):
    _uptime = datetime.datetime.now(TZ)

    def __init__(self, *args: typing.Any, **kwargs: typing.Any) -> None:
        load_dotenv()

        intents = discord.Intents.default()

        super().__init__(
            *args,
            **kwargs,
            command_prefix=commands.when_mentioned_or(""),
            intents=intents
        )

        self.logger = logging.getLogger(self.__class__.__name__)
        self.synced = False#True#False
        self.EXT_DIR = "cogs"

        self.db = db.ClassesDB(self.some_or_error(os.getenv("DB_LOCATION")))
        self.db.init_db()

        self.assignments = AssignmentSys(self, self.db)

        self.admin_role_id = int(self.some_or_error(os.getenv("ADMIN_ROLE")))

    def some_or_error(self, x: typing.Any|None) -> typing.Any:
        if x is None:
            self.logger.error("Expected some value, not none!")
            raise AssertionError
        else:
            return x

    async def _load_extensions(self) -> None:
        for fn in [
            f"{self.EXT_DIR}.{x[:-3]}"
            for x
            in os.listdir(self.EXT_DIR)
            if x.endswith(".py")
            and not x.startswith("_")]:
            try:
                await self.load_extension(fn)
                self.logger.info(f"Loaded extension {fn}")
            except commands.ExtensionError:
                self.logger.error(f"Failed to load extension {fn}\n{traceback.format_exc()}")


    async def on_error(self, event_method: str, /, *args, **kwargs) -> None:
        self.logger.error(f"Error in {event_method}.\n{traceback.format_exc()}")

    async def on_ready(self) -> None:
        self.logger.info(f"Logged in as {self.user} ({self.some_or_error(self.user).id})")

    async def setup_hook(self) -> None:
        await self._load_extensions()
        self.add_view(invite.InviteView(self))
        self.add_view(invite.WaitView(self))
        
        if not self.synced:
            await self.tree.sync()
            self.synced = True
            self.logger.info("Synced command tree")

        self.expiry_cleanup.start()

    async def close(self) -> None:
        self.db.close()
        await super().close()
    
    def run(self, *args, **kwargs) -> None:
        DC_TOKEN = os.getenv("DISCORD")
        if not DC_TOKEN:
            self.logger.error("Missing Discord token, exiting.")
            exit(1)

        try:
            super().run(DC_TOKEN, *args, **kwargs)
        except (KeyboardInterrupt):
            self.logger.info("Exiting.")
            exit()
        except discord.LoginFailure:
            self.logger.error("Failed to login. Is the token valid?")
            exit(1)

    @tasks.loop(minutes=1)
    async def expiry_cleanup(self):
        expired = self.db.get_expired_invites(datetime.datetime.now(TZ))

        for user_id, old_msg in expired:
            await self.assignments.send_next_invite(user_id, old_msg)

        # make sure empty slots are filled up

    @expiry_cleanup.before_loop
    async def before_cleanup(self):
        await self.wait_until_ready()

    @property
    def uptime(self) -> datetime.timedelta:
        return datetime.datetime.now(TZ) - self._uptime

def main() -> None:
    logging.basicConfig(
        level=logging.INFO,
        format=f"[%(asctime)s] %(levelname)s: %(message)s"
    )

    bot = ClassesBot()
    bot.run()

if __name__ == "__main__":
    main()