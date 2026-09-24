import requests

from token_and_keys import RIOT_API_KEY


def get_puuid(game_name, tagline):
    response = requests.get(
        f"https://americas.api.riotgames.com/riot/account/v1/accounts/by-riot-id/{game_name}/{tagline}?api_key={RIOT_API_KEY}"
    )
    player_info = response.json()

    if "puuid" not in player_info:
        raise ValueError(f"Could not find player {game_name}#{tagline}")

    return player_info["puuid"]
