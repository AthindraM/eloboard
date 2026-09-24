import discord
from discord.ext import commands

import db
from token_and_keys import DISCORD_BOT_TOKEN, POSTGRES_DSN


class Client(commands.Bot):
    async def setup_hook(self):
        await db.init_db(POSTGRES_DSN)

        for extension in ["cogs.profile", "cogs.leaderboard"]:
            await self.load_extension(extension)

        synced = await self.tree.sync()
        print(f"Synced {len(synced)} commands globally")

    async def on_ready(self):
        print(f"Logged on as {self.user}")

    async def close(self):
        await db.close_db()
        await super().close()

    async def on_message(self, message):
        if message.author == self.user:
            return


intents = discord.Intents.default()
intents.message_content = True
intents.members = True
client = Client(command_prefix="!", intents=intents)

client.run(DISCORD_BOT_TOKEN)
