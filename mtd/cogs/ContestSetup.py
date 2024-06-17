from discord.ext import commands
from datetime import datetime, timezone
from mtd.modules import permissions


class ContestSetup(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

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

    @commands.command(name="set_representing_server", brief="Act behalf of a specific server")
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
    await bot.db.commit()

    await bot.add_cog(ContestSetup(bot))
