import requests
import discord

import db
from token_and_keys import RIOT_API_KEY
from utils.ranking import rank_sort_key, format_leaderboard_entry


def get_lol_rank_info(puuid):
    response = requests.get(
        f"https://na1.api.riotgames.com/lol/league/v4/entries/by-puuid/{puuid}?api_key={RIOT_API_KEY}"
    )
    lol_rank_info = response.json()

    if not isinstance(lol_rank_info, list):
        print(f"LoL API error for puuid {puuid}: {lol_rank_info}")
        return []

    return lol_rank_info


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


class LoLQueueSelect(discord.ui.Select):
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

        if interaction.guild is None:
            await interaction.edit_original_response(
                content="This command can only be used in a server.", view=None
            )
            return

        queue_type = self.values[0]

        accounts = await db.get_all_linked_accounts_for_game(self.game)

        guild_member_ids = {member.id for member in interaction.guild.members}
        accounts = [a for a in accounts if a["discord_id"] in guild_member_ids]

        if not accounts:
            await interaction.edit_original_response(
                content="No accounts linked for this game yet!", view=None
            )
            return

        entries = []
        for acc in accounts:
            rank_info = get_lol_rank_info(acc["puuid"])
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
        embed = discord.Embed(
            title=f"🏆 League of Legends — {queue_label} Leaderboard",
            color=discord.Color(0x37DB91),
        )
        embed.description = "\n".join(
            format_leaderboard_entry(i, e) for i, e in enumerate(entries, start=1)
        )

        await interaction.edit_original_response(content=None, embed=embed, view=None)


class LoLQueueView(discord.ui.View):
    def __init__(self, game: str):
        super().__init__()
        self.add_item(LoLQueueSelect(game))
