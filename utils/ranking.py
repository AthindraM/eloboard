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


def format_leaderboard_entry(rank: int, entry: dict) -> str:
    medals = {1: "🥇", 2: "🥈", 3: "🥉"}
    prefix = medals.get(rank, f"**#{rank}**")

    wins = entry.get("wins", 0)
    losses = entry.get("losses", 0)
    total = wins + losses
    winrate = round(wins / total * 100) if total > 0 else 0

    name = f"{entry['game_name']}#{entry['tagline']} ({entry['username']})"
    stat_line = f"{entry['tier']} {entry['rank']} {entry['leaguePoints']}LP  {wins}W {losses}L  {winrate}% WR"

    return f"{prefix}\n`{name:<35}{stat_line:>0}`"
