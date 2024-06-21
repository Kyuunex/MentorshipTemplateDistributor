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

    @commands.command(name="participate", brief="Request participation")
    @commands.check(permissions.is_not_ignored)
    async def participate(self, ctx, gamemode=""):
        """
        Examples:
        !participate osu
        !participate taiko
        !participate mania
        !participate catch
        """

        if ctx.guild:
            await ctx.send("This command can only be used in a DM")
            return

        guild = self.bot.representing_guild
        if not guild:
            await ctx.send("Bot misconfigured")
            return

        gamemode = gamemode.lower()

        # we could try to detect which gamemodes the user is allowed to participate in and if it's just one,
        # just note them down for that one

        # Try to guess which gamemode a user is trying to participate in
        if gamemode == "std" or gamemode == "standard" or gamemode == "osu!":
            gamemode = "osu"
        elif gamemode == "osu!taiko" or gamemode == "drums":
            gamemode = "taiko"
        elif gamemode == "osu!mania" or gamemode == "piano":
            gamemode = "mania"
        elif gamemode == "catch" or gamemode == "fruits":
            gamemode = "ctb"

        if not gamemode in ["osu", "taiko", "mania", "ctb"]:
            await ctx.send("Which gamemode would you like to participate in? "
                           "Add one of these after the command: osu, taiko, mania, ctb")
            return

        if not await self.eligibility_check(ctx.author, guild, gamemode):
            await ctx.send(f"You are not eligible to participate in this contest with gamemode: {gamemode}."
                           f"Use the !check_eligibility command to see which gamemodes you are eligible to "
                           f"participate in.")
            return

        member = guild.get_member(int(ctx.author.id))
        if not member:
            await ctx.send(f"You must be in the {guild.name} server to participate in this contest.")
            return

        if not await self.time_check():
            await ctx.send(f"It's either too early or too late to participate in this contest.")
            return

        # at this point we can start participating them

        async with self.bot.db.execute("SELECT value FROM contest_config WHERE key = ?", ["attachment"]) as cursor:
            attachment = await cursor.fetchone()
        async with self.bot.db.execute("SELECT value FROM contest_config WHERE key = ?", ["instructions"]) as cursor:
            instructions = await cursor.fetchone()
        async with self.bot.db.execute("SELECT value FROM contest_config_int WHERE key = ?", ["cycle_id"]) as cursor:
            cycle_id = await cursor.fetchone()
        async with self.bot.db.execute("SELECT duration FROM durations WHERE gamemode = ?", [gamemode]) as cursor:
            duration = await cursor.fetchone()

        if not cycle_id or attachment or instructions or duration:
            await ctx.send("Bot unconfigured!")
            return

        async with self.bot.db.execute(
                "SELECT timestamp_requested, timestamp_timeslot_deadline, timestamp_submitted FROM participation "
                "WHERE user_id = ? AND cycle_id = ? AND gamemode = ?",
                [int(member.id), int(cycle_id), str(gamemode)]
        ) as cursor:
            has_already_participated = await cursor.fetchone()

        if has_already_participated:
            response_str = (f"You have already participated in this contest this cycle. "
                            f"You signed up on <t:{has_already_participated[0]}:f> "
                            f"with deadline of <t:{has_already_participated[1]}:f>. ")
            if has_already_participated[2]:
                response_str += f"You have submitted your entry on <t:{has_already_participated[2]}:f>"
            else:
                response_str += f"You have not submitted an entry."
            await ctx.send(response_str)
            return

        timestamp_requested = int(time.time())
        timestamp_submitted = None
        timestamp_timeslot_deadline = timestamp_requested + (int(duration[0]) * 60)
        timestamp_grace_deadline = timestamp_timeslot_deadline + (5 * 60)
        default_status = "DNS"

        await self.bot.db.execute(
            "INSERT INTO participation VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)",
            [
                int(cycle_id[0]),
                int(member.id),
                str(member.username),
                str(member.display_name),
                str(gamemode),
                timestamp_requested,
                timestamp_submitted,
                timestamp_timeslot_deadline,
                timestamp_grace_deadline,
                str(default_status)
            ]
        )
        await self.bot.db.commit()

        embed = discord.Embed(
            description=instructions[0],
            color=0xFFFFFF
        )

        # source https://www.freepik.com/free-vector/simple-vibing-cat-square-meme_58459053.htm
        embed.set_image(url="https://i.imgur.com/UMhMLui.jpeg")

        if not await self.time_check():
            embed.description += f"\n\n** Attachment: {attachment[0]} **"

        embed.add_field(name="Cycle", value=int(cycle_id[0]))
        embed.add_field(name="Gamemode", value=gamemode)
        embed.add_field(name="Start time", value=f"<t:{timestamp_requested}:f>")
        embed.add_field(name="Deadline", value=f"<t:{timestamp_timeslot_deadline}:f>")
        embed.add_field(name="Hard Deadline", value=f"<t:{timestamp_grace_deadline}:f>")

        embed.set_author(
            name=str(ctx.author.display_name),
            icon_url=ctx.author.display_avatar.url
        )
        await ctx.send(embed=embed)

        # TODO: add a reminder


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
