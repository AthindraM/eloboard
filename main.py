from os import name

import requests
import discord
from discord.ext import commands
from discord import app_commands

import db
from token_and_keys import DISCORD_BOT_TOKEN, RIOT_API_KEY, POSTGRES_DSN


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
    async def setup_hook(self):
        await db.init_db(POSTGRES_DSN)

    async def on_ready(self):
        print(f"Logged on as {self.user}")

        try:
            guild = discord.Object(id=1065303021925453835)
            synced = await self.tree.sync(guild=guild)
            print(f"Synced {len(synced)} commands to guild {guild.id}")

        except Exception as e:
            print(f"Error syncing commands: {e}")

    async def close(self):
        await db.close_db()
        await super().close()

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


# --Profile & Account--
GAME_DISPLAY_NAMES = {
    "lol": "League of Legends",
    "valorant": "Valorant",
}


@client.tree.command(
    name="create_profile",
    description="Creates a profile for your accounts",
    guild=GUILD_ID,
)
async def create_profile(interaction: discord.Interaction):
    created = await db.create_profile(interaction.user.id, interaction.user.name)
    if created:
        await interaction.response.send_message(
            "Profile created sucessfully! Use '/link_account' to link your game accounts"
        )
    else:
        await interaction.response.send_message("You already have a profile!")


@client.tree.command(
    name="remove_profile",
    description="Removes your profile",
    guild=GUILD_ID,
)
async def remove_profile(interaction: discord.Interaction):
    removed = await db.remove_profile(interaction.user.id)
    if removed:
        await interaction.response.send_message(
            "Your profile and linked accounts have been removed."
        )
    else:
        await interaction.response.send_message("You don't have a profile yet!")


@client.tree.command(
    name="profile",
    description="Shows your profile stats and linked accounts",
    guild=GUILD_ID,
)
async def profile(interaction: discord.Interaction):
    prof = await db.get_profile(interaction.user.id)
    if prof is None:
        await interaction.response.send_message(
            "You don't have a profile yet! Use `/create_profile` to create one!"
        )
        return

    accounts = await db.get_linked_accounts(interaction.user.id)
    embed = discord.Embed(title=f"{prof['username']}'s Profile")

    if not accounts:
        embed.description = "No linked accounts yet. Use `/link_account` to add one!"
    else:
        by_game: dict[str, list[dict]] = {}
        for acc in accounts:
            by_game.setdefault(acc["game"], []).append(acc)

        for game, accs in by_game.items():
            display_name = GAME_DISPLAY_NAMES.get(game, game)
            value = "\n".join(f"{a['game_name']}#{a['tagline']}" for a in accs)
            embed.add_field(name=display_name, value=value, inline=False)

    await interaction.response.send_message(embed=embed)


@client.tree.command(
    name="link_account",
    description="Link a game account to your profile",
    guild=GUILD_ID,
)
@app_commands.choices(
    game=[
        app_commands.Choice(name="League of Legends", value="lol"),
    ]
)
async def link_account(
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
            await interaction.response.edit_message(
                content="Account unlinked.", view=None
            )
        else:
            await interaction.response.edit_message(
                content="Couldn't unlink that account.", view=None
            )


class UnlinkView(discord.ui.View):
    def __init__(self, accounts: list[dict]):
        super().__init__()
        self.add_item(UnlinkSelect(accounts))


@client.tree.command(
    name="unlink_account",
    description="Unlink a game account from your profile",
    guild=GUILD_ID,
)
async def unlink_account(interaction: discord.Interaction):
    accounts = await db.get_linked_accounts(interaction.user.id)
    if not accounts:
        await interaction.response.send_message(
            "You don't have any linked accounts.", ephemeral=True
        )
        return

    await interaction.response.send_message(
        "Select an account to unlink:", view=UnlinkView(accounts), ephemeral=True
    )


# --Leaderboard--
TIER_ORDER = [
    "IRON",
    "BRONZE",
    "SILVER",
    "GOLD",
    "PLATINUM",
    "EMERALD",
    "DIAMOND",
    "MASTER",
    "GRANDMASTER",
    "CHALLENGER",
]
RANK_ORDER = {"IV": 0, "III": 1, "II": 2, "I": 3}


def rank_sort_key(entry):
    tier_index = TIER_ORDER.index(entry["tier"]) if entry["tier"] in TIER_ORDER else -1
    rank_index = RANK_ORDER.get(entry.get("rank", ""), 0)
    lp = entry.get("leaguePoints", 0)
    return (tier_index, rank_index, lp)


class QueueSelect(discord.ui.Select):
    def __init__(self, game: str):
        self.game = game
        options = [
            discord.SelectOption(label="Solo/Duo", value="RANKED_SOLO_5x5"),
            discord.SelectOption(label="Flex", value="RANKED_FLEX_SR"),
        ]
        super().__init__(
            placeholder="Choose a queue type:",
            min_values=1,
            max_values=1,
            options=options,
        )

    async def callback(self, interaction: discord.Interaction):
        await interaction.response.defer()
        queue_type = self.values[0]

        accounts = await db.get_all_linked_accounts_for_game(self.game)
        if not accounts:
            await interaction.edit_original_response(
                content="No accounts linked for this game yet!", view=None
            )
            return

        entries = []
        for acc in accounts:
            rank_info = get_rank_info(acc["puuid"])
            queue_entry = next(
                (e for e in rank_info if e["queueType"] == queue_type), None
            )
            if queue_entry:
                entries.append(
                    {
                        **queue_entry,
                        "username": acc["username"],
                        "game_name": acc["game_name"],
                        "tagline": acc["tagline"],
                    }
                )

        if not entries:
            await interaction.edit_original_response(
                content="No ranked data found for that queue.", view=None
            )
            return

        entries.sort(key=rank_sort_key, reverse=True)

        queue_label = "Solo/Duo" if queue_type == "RANKED_SOLO_5x5" else "Flex"
        embed = discord.Embed(title=f"League of Legends — {queue_label} Leaderboard")
        embed.description = "\n".join(
            f"**{i}.** {e['username']} ({e['game_name']}#{e['tagline']}) — {e['tier']} {e['rank']} {e['leaguePoints']} LP"
            for i, e in enumerate(entries, start=1)
        )

        await interaction.edit_original_response(content=None, embed=embed, view=None)


class QueueView(discord.ui.View):
    def __init__(self, game: str):
        super().__init__()
        self.add_item(QueueSelect(game))


class Leaderboard(discord.ui.Select):
    def __init__(self):
        options = [
            discord.SelectOption(
                label="League of Legends",
                value="lol",
                description="Brings up the LoL leaderboard",
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
                content="Choose a queue type:", view=QueueView(game)
            )
        else:
            await interaction.response.edit_message(
                content="Valorant leaderboard coming soon!", view=None
            )


class LeaderboardView(discord.ui.View):
    def __init__(self):
        super().__init__()
        self.add_item(Leaderboard())


@client.tree.command(
    name="leaderboard",
    description="Brings up the leaderboard of a game",
    guild=GUILD_ID,
)
async def leaderboard(interaction: discord.Interaction):
    await interaction.response.send_message(view=LeaderboardView())


client.run(DISCORD_BOT_TOKEN)
