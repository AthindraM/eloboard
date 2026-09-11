import asyncpg

_pool: asyncpg.Pool | None = None


async def init_db(dsn: str):
    global _pool
    _pool = await asyncpg.create_pool(dsn=dsn, min_size=1, max_size=10)

    async with _pool.acquire() as conn:
        await conn.execute("""
            CREATE TABLE IF NOT EXISTS profiles (
                discord_id BIGINT PRIMARY KEY,
                username TEXT NOT NULL
            )
        """)
        await conn.execute("""
            CREATE TABLE IF NOT EXISTS linked_accounts (
                discord_id BIGINT NOT NULL REFERENCES profiles (discord_id) ON DELETE CASCADE,
                game TEXT NOT NULL,
                game_name TEXT NOT NULL,
                tagline TEXT NOT NULL,
                puuid TEXT,
                PRIMARY KEY (discord_id, game)
            )
        """)


async def close_db():
    """Call on bot shutdown to cleanly close the pool."""
    if _pool is not None:
        await _pool.close()


async def create_profile(discord_id: int, username: str) -> bool:
    async with _pool.acquire() as conn:
        result = await conn.execute(
            """
            INSERT INTO profiles (discord_id, username)
            VALUES ($1, $2)
            ON CONFLICT (discord_id) DO NOTHING
            """,
            discord_id,
            username,
        )
        return result == "INSERT 0 1"


async def remove_profile(discord_id: int) -> bool:
    async with _pool.acquire() as conn:
        # linked_accounts rows are auto-removed via ON DELETE CASCADE
        result = await conn.execute(
            "DELETE FROM profiles WHERE discord_id = $1", discord_id
        )
        return result == "DELETE 1"


async def get_profile(discord_id: int) -> dict | None:
    async with _pool.acquire() as conn:
        row = await conn.fetchrow(
            "SELECT discord_id, username FROM profiles WHERE discord_id = $1",
            discord_id,
        )
        return dict(row) if row else None


async def link_account(
    discord_id: int, game: str, game_name: str, tagline: str, puuid: str = None
):
    async with _pool.acquire() as conn:
        await conn.execute(
            """
            INSERT INTO linked_accounts (discord_id, game, game_name, tagline, puuid)
            VALUES ($1, $2, $3, $4, $5)
            ON CONFLICT (discord_id, game) DO UPDATE SET
                game_name = EXCLUDED.game_name,
                tagline = EXCLUDED.tagline,
                puuid = EXCLUDED.puuid
            """,
            discord_id,
            game,
            game_name,
            tagline,
            puuid,
        )


async def unlink_account(discord_id: int, game: str) -> bool:
    async with _pool.acquire() as conn:
        result = await conn.execute(
            "DELETE FROM linked_accounts WHERE discord_id = $1 AND game = $2",
            discord_id,
            game,
        )
        return result == "DELETE 1"


async def get_linked_accounts(discord_id: int) -> list[dict]:
    async with _pool.acquire() as conn:
        rows = await conn.fetch(
            "SELECT game, game_name, tagline, puuid FROM linked_accounts WHERE discord_id = $1",
            discord_id,
        )
        return [dict(row) for row in rows]
