import os
import datetime
import logging
import typing
import traceback

from dotenv import load_dotenv

import discord
from discord.ext import commands

import src.db as db

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
        self.synced = True #False
        self.EXT_DIR = "cogs"

        self.db = db.ClassesDB(os.getenv("DB_LOCATION"))
        self.db.init_db()

        self.tutor_role_id = int(os.getenv("TUTOR_ROLE"))

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
        self.logger.info(f"Logged in as {self.user} ({self.user.id})")

    async def setup_hook(self) -> None:
        await self._load_extensions()
        
        if not self.synced:
            await self.tree.sync()
            self.synced = True
            self.logger.info("Synced command tree")

    async def close(self) -> None:
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