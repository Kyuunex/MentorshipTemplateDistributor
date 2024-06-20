from discord.ext import commands
from mtd.modules import permissions
import discord
import time


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
                                       [gamemode]) as cursor:
            eligibility_roles = await cursor.fetchall()

        for eligible_role in eligibility_roles:
            if member.get_role(int(eligible_role[0])):
                return True

        return False

    async def time_check(self):
        async with self.bot.db.execute("SELECT value FROM contest_config_int WHERE key = ?", ["start_time"]) as cursor:
            start_time = await cursor.fetchone()

        async with self.bot.db.execute("SELECT value FROM contest_config_int WHERE key = ?", ["end_time"]) as cursor:
            end_time = await cursor.fetchone()

        if not start_time or not end_time:
            return False

        if int(start_time[0]) < time.time() < int(end_time[0]):
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

        embed = discord.Embed(
            description="Eligibility check",
            color=0xFFFFFF
        )

        eligibility_count = 0

        for gamemode in ["osu", "taiko", "mania", "ctb"]:
            if not await self.eligibility_check(ctx.author, guild, gamemode):
                embed.add_field(name=gamemode, value="Not eligible")
            else:
                embed.add_field(name=gamemode, value="Eligible")
                eligibility_count += 1

        if eligibility_count == 0:
            embed.set_image(url="https://i.imgur.com/HNxQJVx.jpeg")
        else:
            embed.set_image(url="https://i.imgur.com/6w66FUv.png")

        if not await self.time_check():
            embed.description += f"\n\nIt's either too early or too late to participate in this contest."

        embed.set_author(
            name=str(ctx.author.display_name),
            icon_url=ctx.author.display_avatar.url
        )
        await ctx.send(embed=embed)


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
