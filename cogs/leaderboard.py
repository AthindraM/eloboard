import discord
from discord.ext import commands
from discord import app_commands

from cogs.league import LoLQueueView
from cogs.tft import build_tft_leaderboard


class Leaderboard(discord.ui.Select):
    def __init__(self):
        options = [
            discord.SelectOption(
                label="League of Legends",
                value="lol",
                description="Brings up the LoL leaderboard",
            ),
            discord.SelectOption(
                label="Teamfight Tactics",
                value="tft",
                description="Brings up the Teamfight Tactics leaderboard",
            ),
            discord.SelectOption(
                label="Valorant",
                value="valorant",
                description="Brings up the Valorant leaderboard",
            ),
        ]
        super().__init__(
            placeholder="Please choose a game:",
            min_values=1,
            max_values=1,
            options=options,
        )

    async def callback(self, interaction: discord.Interaction):
        game = self.values[0]
        if game == "lol":
            await interaction.response.edit_message(
                content="Choose a queue type:", view=LoLQueueView(game)
            )
        elif game == "valorant":
            await interaction.response.edit_message(
                content="Valorant leaderboard coming soon!", view=None
            )
        elif game == "tft":
            await interaction.response.defer()
            await build_tft_leaderboard(interaction)
        else:
            await interaction.response.edit_message(content="Invalid input!", view=None)


class LeaderboardView(discord.ui.View):
    def __init__(self):
        super().__init__()
        self.add_item(Leaderboard())


class LeaderboardCog(commands.Cog):
    def __init__(self, client: commands.Bot):
        self.client = client

    @app_commands.command(
        name="leaderboard", description="Brings up the leaderboard of a game"
    )
    async def leaderboard(self, interaction: discord.Interaction):
        await interaction.response.send_message(view=LeaderboardView())


async def setup(client: commands.Bot):
    await client.add_cog(LeaderboardCog(client))
