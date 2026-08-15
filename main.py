import discord
from discord.ext import commands
from discord import app_commands

from bot_token import BOT_TOKEN


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


intents = discord.Intents.default()
intents.message_content = True
client = Client(command_prefix="!", intents=intents)

GUILD_ID = discord.Object(id=1065303021925453835)


@client.tree.command(
    name="leaderboard", description="Brings up the leaderboard", guild=GUILD_ID
)
async def leaderboard(interaction: discord.Interaction, game: str):
    await interaction.response.send_message(f"{game} leaderboard coming soon!")


client.run(BOT_TOKEN)
