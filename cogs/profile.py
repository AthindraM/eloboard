import discord
from discord.ext import commands
from discord import app_commands

import db
from utils.riot_api import get_puuid

GAME_DISPLAY_NAMES = {
    "lol": "League of Legends",
    "valorant": "Valorant",
}


class UnlinkSelect(discord.ui.Select):
    def __init__(self, accounts: list[dict]):
        options = [
            discord.SelectOption(
                label=f"{acc['game_name']}#{acc['tagline']}",
                description=acc["game"],
                value=str(acc["id"]),
            )
            for acc in accounts
        ]
        super().__init__(
            placeholder="Choose an account to unlink",
            min_values=1,
            max_values=1,
            options=options,
        )

    async def callback(self, interaction: discord.Interaction):
        account_id = int(self.values[0])
        removed = await db.unlink_account_by_id(interaction.user.id, account_id)
        if removed:
            await interaction.response.edit_message(content="Account unlinked.", view=None)
        else:
            await interaction.response.edit_message(content="Couldn't unlink that account.", view=None)


class UnlinkView(discord.ui.View):
    def __init__(self, accounts: list[dict]):
        super().__init__()
        self.add_item(UnlinkSelect(accounts))


class ProfileCog(commands.Cog):
    def __init__(self, client: commands.Bot):
        self.client = client

    @app_commands.command(name="create_profile", description="Creates a profile for your accounts")
    async def create_profile(self, interaction: discord.Interaction):
        created = await db.create_profile(interaction.user.id, interaction.user.name)
        if created:
            await interaction.response.send_message(
                "Profile created sucessfully! Use '/link_account' to link your game accounts"
            )
        else:
            await interaction.response.send_message("You already have a profile!")

    @app_commands.command(name="remove_profile", description="Removes your profile")
    async def remove_profile(self, interaction: discord.Interaction):
        removed = await db.remove_profile(interaction.user.id)
        if removed:
            await interaction.response.send_message(
                "Your profile and linked accounts have been removed."
            )
        else:
            await interaction.response.send_message("You don't have a profile yet!")

    @app_commands.command(name="profile", description="Shows your profile stats and linked accounts")
    async def profile(self, interaction: discord.Interaction):
        prof = await db.get_profile(interaction.user.id)
        if prof is None:
            await interaction.response.send_message(
                "You don't have a profile yet! Use `/create_profile` to create one!"
            )
            return

        accounts = await db.get_linked_accounts(interaction.user.id)
        embed = discord.Embed(
            title=f"{prof['username']}'s Profile", color=discord.Color(0x37DB91)
        )
        embed.set_thumbnail(url=interaction.user.display_avatar.url)

        if not accounts:
            embed.description = "No linked accounts yet. Use `/link_account` to add one!"
        else:
            by_game: dict[str, list[dict]] = {}
            for acc in accounts:
                by_game.setdefault(acc["game"], []).append(acc)

            for game, accs in by_game.items():
                display_name = GAME_DISPLAY_NAMES.get(game, game)
                value = "\n".join(f"`{a['game_name']}#{a['tagline']}`" for a in accs)
                embed.add_field(name=display_name, value=value, inline=False)

        await interaction.response.send_message(embed=embed)

    @app_commands.command(name="link_account", description="Link a game account to your profile")
    @app_commands.choices(
        game=[
            app_commands.Choice(name="League of Legends", value="lol"),
        ]
    )
    async def link_account(
        self,
        interaction: discord.Interaction,
        game: app_commands.Choice[str],
        game_name: str,
        tagline: str,
    ):
        prof = await db.get_profile(interaction.user.id)
        if prof is None:
            await interaction.response.send_message(
                "You need a profile first! Use `/create_profile` to create one!"
            )
            return

        await interaction.response.defer()

        try:
            puuid = get_puuid(game_name, tagline)
        except (ValueError, KeyError):
            await interaction.followup.send(
                f"Couldn't find {game_name}#{tagline}. Double-check the name and tagline."
            )
            return

        await db.link_account(interaction.user.id, game.value, game_name, tagline, puuid)
        await interaction.followup.send(
            f"Linked {game.name} account: {game_name}#{tagline}"
        )

    @app_commands.command(name="unlink_account", description="Unlink a game account from your profile")
    async def unlink_account(self, interaction: discord.Interaction):
        accounts = await db.get_linked_accounts(interaction.user.id)
        if not accounts:
            await interaction.response.send_message(
                "You don't have any linked accounts.", ephemeral=True
            )
            return

        await interaction.response.send_message(
            "Select an account to unlink:", view=UnlinkView(accounts), ephemeral=True
        )


async def setup(client: commands.Bot):
    await client.add_cog(ProfileCog(client))
