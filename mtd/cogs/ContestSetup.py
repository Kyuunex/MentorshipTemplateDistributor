from discord.ext import commands
from datetime import datetime, timezone
from mtd.modules import permissions


class ContestSetup(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @commands.command(name="set_cycle_id", brief="Set Cycle ID")
    @commands.check(permissions.is_admin)
    @commands.check(permissions.is_not_ignored)
    async def set_cycle_id(self, ctx, cycle_id):
        """
        Which Mentorship cycle is the current number?
        """

        if not cycle_id.isdigit():
            await ctx.send("Cycle ID must be a number")
            return

        await self.bot.db.execute("DELETE FROM contest_config_int WHERE key = ?", ["cycle_id"])
        await self.bot.db.execute("INSERT INTO contest_config_int VALUES (?, ?)", ["cycle_id", int(cycle_id)])

        await self.bot.db.commit()

        await ctx.send(f"Cycle ID set to: {cycle_id}")

    @commands.command(name="set_start", brief="Set contest start time (UTC)")
    @commands.check(permissions.is_admin)
    @commands.check(permissions.is_not_ignored)
    async def set_start(self, ctx, *, timestamp_str):
        """
        Set contest start time (UTC)
        Example input: 2024-06-22 00:00:00
        """

        await self.bot.db.execute("DELETE FROM contest_config_int WHERE key = ?", ["start_time"])

        input_datetime = datetime.strptime(timestamp_str, "%Y-%m-%d %H:%M:%S")
        input_datetime = input_datetime.replace(tzinfo=timezone.utc)
        unix_timestamp = int(input_datetime.timestamp())
        await self.bot.db.execute("INSERT INTO contest_config_int VALUES (?, ?)", ["start_time", unix_timestamp])

        await self.bot.db.commit()

        await ctx.send(f"Contest start time is set to <t:{unix_timestamp}:F>")

    @commands.command(name="set_start_unix", brief="Set contest start time (UNIX)")
    @commands.check(permissions.is_admin)
    @commands.check(permissions.is_not_ignored)
    async def set_start_unix(self, ctx, unix_timestamp):
        """
        Set contest start time (UNIX)
        Example input: 1719014400
        """

        await self.bot.db.execute("DELETE FROM contest_config_int WHERE key = ?", ["start_time"])
        await self.bot.db.execute("INSERT INTO contest_config_int VALUES (?, ?)", ["start_time", int(unix_timestamp)])

        await self.bot.db.commit()

        await ctx.send(f"Contest start time is set to <t:{unix_timestamp}:F>")

    @commands.command(name="set_end", brief="Set contest end time (UTC)")
    @commands.check(permissions.is_admin)
    @commands.check(permissions.is_not_ignored)
    async def set_end(self, ctx, *, timestamp_str):
        """
        Set contest end time (UTC)
        Example input: 2024-06-23 29:59:59
        """

        await self.bot.db.execute("DELETE FROM contest_config_int WHERE key = ?", ["end_time"])

        input_datetime = datetime.strptime(timestamp_str, "%Y-%m-%d %H:%M:%S")
        input_datetime = input_datetime.replace(tzinfo=timezone.utc)
        unix_timestamp = int(input_datetime.timestamp())
        await self.bot.db.execute("INSERT INTO contest_config_int VALUES (?, ?)", ["end_time", unix_timestamp])

        await self.bot.db.commit()

        await ctx.send(f"Contest start time is set to <t:{unix_timestamp}:F>")

    @commands.command(name="set_end_unix", brief="Set contest end time (UNIX)")
    @commands.check(permissions.is_admin)
    @commands.check(permissions.is_not_ignored)
    async def set_end_unix(self, ctx, unix_timestamp):
        """
        Set contest end time (UNIX)
        Example input: 1719187199
        """

        await self.bot.db.execute("DELETE FROM contest_config_int WHERE key = ?", ["end_time"])
        await self.bot.db.execute("INSERT INTO contest_config_int VALUES (?, ?)", ["end_time", int(unix_timestamp)])

        await self.bot.db.commit()

        await ctx.send(f"Contest start time is set to <t:{unix_timestamp}:F>")

    @commands.command(name="set_attachment", brief="Set Attachment")
    @commands.check(permissions.is_admin)
    @commands.check(permissions.is_not_ignored)
    async def set_attachment(self, ctx, url):
        """
        Example input: https://blabla
        """

        await self.bot.db.execute("DELETE FROM contest_config WHERE key = ?", ["attachment"])
        await self.bot.db.execute(
            "INSERT INTO contest_config VALUES (?, ?)",
            ["attachment", url.strip()]
        )
        await self.bot.db.commit()

        await ctx.send(f"{url} has been (re)set as an attachment")

    @commands.command(name="set_instructions", brief="Set Instructions")
    @commands.check(permissions.is_admin)
    @commands.check(permissions.is_not_ignored)
    async def set_instructions(self, ctx, *, text):
        """
        With this command, set instructions that will be shown to the participants upon osz request.
        """

        await self.bot.db.execute("DELETE FROM contest_config WHERE key = ?", ["instructions"])
        await self.bot.db.execute(
            "INSERT INTO contest_config VALUES (?, ?)",
            ["instructions", text.strip()]
        )
        await self.bot.db.commit()

        await ctx.send("Instructions have been (re)set")

    @commands.command(name="set_representing_server", brief="Act on behalf of a specific server")
    @commands.check(permissions.is_admin)
    @commands.check(permissions.is_not_ignored)
    async def set_representing_server(self, ctx, guild_id):
        """
        Some commands require a server to work, so they normally can't be used inside a DM.
        This command will set a server to act on behalf of.
        """

        if not guild_id.isdigit():
            await ctx.send("guild ID must be all numbers")
            return

        guild = self.bot.get_guild(int(guild_id))

        if not guild:
            await ctx.send("no guild found with that ID")
            return

        self.bot.representing_guild = guild

        await self.bot.db.execute("DELETE FROM contest_config_int WHERE key = ?", ["representing_guild"])
        await self.bot.db.execute("INSERT INTO contest_config_int VALUES (?, ?)", ["representing_guild", guild.id])
        await self.bot.db.commit()

        await ctx.send(f"I will now be representing {guild.name} in direct messages.")

    @commands.command(name="add_ineligible", brief="Make user ineligible to participate")
    @commands.check(permissions.is_admin)
    @commands.check(permissions.is_not_ignored)
    async def add_ineligible(self, ctx, gamemode, user_id):
        """
        Set discord users that are not allowed to participate in the contest.
        """

        if not user_id.isdigit():
            await ctx.send("User ID must be a number")
            return

        if not gamemode in ["osu", "taiko", "mania", "ctb"]:
            await ctx.send("Gamemode must be one of: osu, taiko, mania, ctb")
            return

        async with self.bot.db.execute("SELECT user_id FROM ineligible_users WHERE user_id = ? AND gamemode = ?",
                                       [int(user_id), str(gamemode)]) as cursor:
            is_ineligible = await cursor.fetchone()

        if is_ineligible:
            await ctx.send(f"This user is already ineligible to participate in {gamemode} gamemode.")
            return

        await self.bot.db.execute("INSERT INTO ineligible_users VALUES (?, ?)",
                                  [int(user_id), str(gamemode)])
        await self.bot.db.commit()

        await ctx.send(f"Added user {user_id} to {gamemode} ineligible users.")

    @commands.command(name="add_eligible_role", brief="Add a role that may participate in the contest")
    @commands.check(permissions.is_admin)
    @commands.check(permissions.is_not_ignored)
    async def add_eligible_role(self, ctx, gamemode, role_id):
        """
        Set roles that are allowed to participate in the contest.
        """

        if not role_id.isdigit():
            await ctx.send("Role ID must be a number")
            return

        if not gamemode in ["osu", "taiko", "mania", "ctb"]:
            await ctx.send("Gamemode must be one of: osu, taiko, mania, ctb")
            return

        await self.bot.db.execute("DELETE FROM eligibility_roles WHERE role_id = ?", [int(role_id)])
        await self.bot.db.execute("INSERT INTO eligibility_roles VALUES (?, ?)", [int(role_id), gamemode])
        await self.bot.db.commit()

        await ctx.send(f"Added role {role_id} to {gamemode} eligible roles.")

    @commands.command(name="set_duration", brief="Set duration (in minutes)")
    @commands.check(permissions.is_admin)
    @commands.check(permissions.is_not_ignored)
    async def set_duration(self, ctx, gamemode, duration):
        """
        Set duration (in minutes)
        """

        if not duration.isdigit():
            await ctx.send("duration must be a number")
            return

        if not gamemode in ["osu", "taiko", "mania", "ctb"]:
            await ctx.send("Gamemode must be one of: osu, taiko, mania, ctb")
            return

        await self.bot.db.execute("DELETE FROM durations WHERE gamemode = ?", [int(gamemode)])
        await self.bot.db.execute("INSERT INTO durations VALUES (?, ?)", [int(duration), gamemode])
        await self.bot.db.commit()

        await ctx.send(f"Added duration of {duration} minutes to {gamemode}.")


async def setup(bot):
    await bot.db.execute("""
        CREATE TABLE IF NOT EXISTS "contest_config" (
            "key"    TEXT NOT NULL,
            "value"    TEXT NOT NULL
        )
        """)
    await bot.db.execute("""
        CREATE TABLE IF NOT EXISTS "contest_config_int" (
            "key"    TEXT NOT NULL,
            "value"    INTEGER NOT NULL
        )
        """)
    await bot.db.execute("""
        CREATE TABLE IF NOT EXISTS "ineligible_users" (
            "user_id"   INTEGER NOT NULL,
            "gamemode"   TEXT NOT NULL
        )
        """)
    await bot.db.execute("""
        CREATE TABLE IF NOT EXISTS "eligibility_roles" (
            "role_id"   INTEGER NOT NULL,
            "gamemode"   TEXT NOT NULL
        )
        """)
    await bot.db.execute("""
        CREATE TABLE IF NOT EXISTS "durations" (
            "duration"   INTEGER NOT NULL,
            "gamemode"   TEXT NOT NULL
        )
        """)
    await bot.db.commit()

    await bot.add_cog(ContestSetup(bot))
