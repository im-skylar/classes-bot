import discord


class Checks:
    def __init__(self) -> None:
        pass

    async def has_role(
        self, inter: discord.Interaction, role: int, role_name: str
    ) -> bool:
        """Replies with error and returns whether user has role."""
        if inter.guild is None:
            await inter.response.send_message(
                "This command needs to be issued from a servers text channel."
            )
            return False

        if not (role in [x.id for x in inter.user.roles]):  # type: ignore
            await inter.response.send_message(
                f":no_entry: You need to be {role_name} for this."
            )
            return False

        return True
