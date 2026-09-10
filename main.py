import requests
import json
import discord
from discord.ext import commands
from discord import app_commands

from token_and_keys import DISCORD_BOT_TOKEN, RIOT_API_KEY


# --- RIOT API REQS ---
def get_puuid(game_name, tagline):
    response = requests.get(
        f"https://americas.api.riotgames.com/riot/account/v1/accounts/by-riot-id/{game_name}/{tagline}?api_key={RIOT_API_KEY}"
    )
    player_info = response.json()
    puuid = player_info["puuid"]

    return puuid


def get_rank_info(puuid):
    response = requests.get(
        f"https://na1.api.riotgames.com/lol/league/v4/entries/by-puuid/{puuid}?api_key={RIOT_API_KEY}"
    )
    rank_info = response.json()

    return rank_info


def get_soloduo_rank(rank_info):
    entry = next((e for e in rank_info if e["queueType"] == "RANKED_SOLO_5x5"), None)
    if entry is None:
        return "Unranked"
    return f"{entry['tier']} {entry['rank']} {entry['leaguePoints']} LP"


def get_flex_rank(rank_info):
    entry = next((e for e in rank_info if e["queueType"] == "RANKED_FLEX_SR"), None)
    if entry is None:
        return "Unranked"
    return f"{entry['tier']} {entry['rank']} {entry['leaguePoints']} LP"


# --- BOT SETUP ---
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


# --- COMMANDS ---
intents = discord.Intents.default()
intents.message_content = True
client = Client(command_prefix="!", intents=intents)

GUILD_ID = discord.Object(id=1065303021925453835)


@client.tree.command(
    name="league_stats",
    description="Brings up your League of Legends stats",
    guild=GUILD_ID,
)
async def league_stats(interaction: discord.Interaction, game_name: str, tagline: str):
    author_puuid = get_puuid(game_name, tagline)
    rank_info = get_rank_info(author_puuid)
    soloduo_rank = get_soloduo_rank(rank_info)
    flex_rank = get_flex_rank(rank_info)

    game_name = game_name.replace(" ", "")

    embed = discord.Embed(
        title=f"{game_name}#{tagline}'s OP.gg",
        url=f"https://op.gg/lol/summoners/na/{game_name}-{tagline}",
    )
    embed.set_author(name=interaction.user.name)
    embed.add_field(
        name="Ranked Stats", value=f"Solo/Duo: {soloduo_rank}\nFlex: {flex_rank}"
    )
    await interaction.response.send_message(embed=embed)


@client.tree.command(
    name="create_profile",
    description="Creates a profile for your accounts",
    guild=GUILD_ID,
)
async def create_profile(interaction: discord.Interaction):
    await interaction.response.send_message("coming soon!")


@client.tree.command(
    name="remove_profile",
    description="Removes your profile",
    guild=GUILD_ID,
)
async def remove_profile(interaction: discord.Interaction):
    await interaction.response.send_message("coming soon!")


@client.tree.command(
    name="profile",
    description="Shows your profile stats and linked accounts",
    guild=GUILD_ID,
)
async def profile(interaction: discord.Interaction):
    await interaction.response.send_message("coming soon!")


@client.tree.command(
    name="link_account",
    description="Link a game account to your profile",
    guild=GUILD_ID,
)
async def link_account(interaction: discord.Interaction):
    await interaction.response.send_message("coming soon!")


@client.tree.command(
    name="unlink_account",
    description="Unlink a game account from your profile",
    guild=GUILD_ID,
)
async def unlink_account(interaction: discord.Interaction):
    await interaction.response.send_message("coming soon!")


@client.tree.command(
    name="leaderboard",
    description="Brings up the leaderboard of a game",
    guild=GUILD_ID,
)
async def leaderboard(interaction: discord.Interaction):
    await interaction.response.send_message("coming soon!")


client.run(DISCORD_BOT_TOKEN)
