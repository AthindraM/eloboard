import discord
from discord.ext import commands
from discord import app_commands

from token_and_keys import DISCORD_BOT_TOKEN, RIOT_API_KEY


class Client(commands.Bot):
    async def on_ready(self):
        print(f"Logged on as {self.user}")

        try:
            guild = discord.Object(id=1065303021925453835)
            synced = await self.tree.sync(guild=guild)
            print(f"Synced {len(synced)} commands to guild {guild.id}")

        except Exception as e:
            print(f"Error syncing commands: {e}")

    async def on_message(self, message):
        if message.author == self.user:
            return


# COMMANDS
intents = discord.Intents.default()
intents.message_content = True
client = Client(command_prefix="!", intents=intents)

GUILD_ID = discord.Object(id=1065303021925453835)


@client.tree.command(
    name="leaderboard", description="Brings up the leaderboard", guild=GUILD_ID
)
async def leaderboard(interaction: discord.Interaction, game: str):
    embed = discord.Embed(
        title=f"{game} Leaderboard", description=f"{game} leaderboard coming soon!"
    )
    await interaction.response.send_message(embed=embed)


@client.tree.command(
    name="profile", description="Brings up your profile", guild=GUILD_ID
)
async def profile(interaction: discord.Interaction, game_name: str, tagline: str):
    embed = discord.Embed(
        title=f"{game_name}#{tagline}'s OP.gg",
        url=f"https://op.gg/lol/summoners/na/{game_name}-{tagline}",
    )
    embed.set_author(name=interaction.user.name)
    embed.add_field(
        name="Overall Stats", value=f"Rank: \nWin Rate: \nHighest Mastery: "
    )
    await interaction.response.send_message(embed=embed)


client.run(DISCORD_BOT_TOKEN)
