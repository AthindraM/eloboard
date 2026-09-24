import requests
import discord

import db
from token_and_keys import RIOT_API_KEY
from utils.ranking import rank_sort_key, format_leaderboard_entry


def get_tft_rank_info(puuid):
    response = requests.get(
        f"https://na1.api.riotgames.com/tft/league/v1/by-puuid/{puuid}?api_key={RIOT_API_KEY}"
    )
    tft_rank_info = response.json()

    if not isinstance(tft_rank_info, list):
        print(f"TFT API error for puuid {puuid}: {tft_rank_info}")
        return []

    return tft_rank_info


def get_tft_rank(rank_info):
    entry = next((e for e in rank_info if e["queueType"] == "RANKED_TFT"), None)
    if entry is None:
        return "Unranked"
    return f"{entry['tier']} {entry['rank']} {entry['leaguePoints']} LP"


async def build_tft_leaderboard(interaction: discord.Interaction):
    if interaction.guild is None:
        await interaction.edit_original_response(
            content="This command can only be used in a server.", view=None
        )
        return

    # TFT shares the same Riot platform account as League, so we pull from
    # accounts linked under "lol" rather than a separate "tft" game entry.
    accounts = await db.get_all_linked_accounts_for_game("lol")

    guild_member_ids = {member.id for member in interaction.guild.members}
    accounts = [a for a in accounts if a["discord_id"] in guild_member_ids]

    if not accounts:
        await interaction.edit_original_response(
            content="No accounts linked yet! Use `/link_account` to add one.", view=None
        )
        return

    entries = []
    for acc in accounts:
        rank_info = get_tft_rank_info(acc["puuid"])
        queue_entry = next(
            (e for e in rank_info if e["queueType"] == "RANKED_TFT"), None
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
            content="No ranked TFT data found.", view=None
        )
        return

    entries.sort(key=rank_sort_key, reverse=True)

    embed = discord.Embed(
        title="🏆 Teamfight Tactics Leaderboard", color=discord.Color(0x37DB91)
    )
    embed.description = "\n".join(
        format_leaderboard_entry(i, e) for i, e in enumerate(entries, start=1)
    )

    await interaction.edit_original_response(content=None, embed=embed, view=None)
