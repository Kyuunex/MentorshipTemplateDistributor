from discord.ext import commands
from mtd.modules import permissions


class ContestTools(commands.Cog):
    def __init__(self, bot):
        self.bot = bot


async def setup(bot):
    await bot.add_cog(ContestTools(bot))
