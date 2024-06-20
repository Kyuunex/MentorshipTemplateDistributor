from discord.ext import commands
from mtd.modules import permissions


class Participation(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    async def eligibility_check(self, user, guild, gamemode):
        async with self.bot.db.execute("SELECT user_id FROM ineligible_users WHERE user_id = ? AND gamemode = ?",
                                       [int(user.id), gamemode]) as cursor:
            is_ineligible = await cursor.fetchone()
        if is_ineligible:
            return False

        member = guild.get_member(int(user.id))

        async with self.bot.db.execute("SELECT role_id FROM eligibility_roles WHERE gamemode = ?",
                                       [{gamemode}]) as cursor:
            eligibility_roles = await cursor.fetchall()

        for eligible_role in eligibility_roles:
            if member.get_role(int(eligible_role[0])):
                return True

        return False

    @commands.command(name="check_eligibility", brief="Check eligibility")
    @commands.check(permissions.is_not_ignored)
    async def check_eligibility(self, ctx):
        guild = ctx.guild
        if not guild:
            guild = self.bot.representing_guild
            if not guild:
                await ctx.send("Bot misconfigured")
                return

        for gamemode in ["osu", "taiko", "mania", "ctb"]:
            if not await self.eligibility_check(ctx.author, guild, gamemode):
                await ctx.send(f"You are not eligible to participate in this contest with gamemode: {gamemode}")
            else:
                await ctx.send(f"You are eligible to participate in this contest with gamemode: {gamemode}")


async def setup(bot):
    await bot.db.execute("""
        CREATE TABLE IF NOT EXISTS "participation" (
            "cycle_id"    INTEGER NOT NULL,
            "user_id"    INTEGER NOT NULL,
            "username"    TEXT NOT NULL,
            "nickname"    TEXT NOT NULL,
            "gamemode"    TEXT NOT NULL,
            "timestamp_requested"    INTEGER NOT NULL,
            "timestamp_submitted"    INTEGER,
            "timestamp_timeslot_deadline"    INTEGER NOT NULL,
            "timestamp_grace_deadline"    INTEGER NOT NULL,
            "status"    TEXT NOT NULL
        )
        """)
    await bot.db.execute("""
        CREATE TABLE IF NOT EXISTS "submissions" (
            "cycle_id"    INTEGER NOT NULL,
            "user_id"    INTEGER NOT NULL,
            "gamemode"    TEXT NOT NULL,
            "timestamp_submitted"    INTEGER NOT NULL,
            "file"    TEXT NOT NULL,
            "status"    TEXT NOT NULL
        )
        """)
    await bot.add_cog(Participation(bot))
