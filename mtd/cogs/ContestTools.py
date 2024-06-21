from discord.ext import commands
from mtd.modules import permissions


class ContestTools(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @commands.command(name="reset_participant", brief="reset_participant")
    @commands.check(permissions.is_admin)
    @commands.check(permissions.is_not_ignored)
    async def reset_participant(self, ctx, user_id):
        if not user_id.isdigit():
            await ctx.send("User ID must be a number")
            return

        async with self.bot.db.execute("SELECT value FROM contest_config_int WHERE key = ?", ["cycle_id"]) as cursor:
            cycle_id = await cursor.fetchone()

        if not cycle_id:
            await ctx.send("Please set a cycle ID first.")
            return

        await self.bot.db.execute("DELETE FROM participation WHERE user_id = ? AND cycle_id",
                                  [int(user_id), int(cycle_id[0])])
        await self.bot.db.commit()

        await ctx.send(f"{user_id} has been reset")


async def setup(bot):
    await bot.add_cog(ContestTools(bot))
