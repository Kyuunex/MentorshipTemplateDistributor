from discord.ext import commands
from mtd.modules import permissions
from mtd.classes.Beatmap import Beatmap
import discord
import time
import asyncio
import logging


class Participation(commands.Cog):
    def __init__(self, bot, saved_reminder_rows):
        self.bot = bot

        for reminder_row in saved_reminder_rows:
            cycle_id, timestamp, user_id, gamemode = reminder_row

            self.bot.background_tasks.append(
                self.bot.loop.create_task(
                    self.reminder_task(int(timestamp), int(user_id), str(gamemode)))
            )

    async def eligibility_check(self, user, guild, gamemode):
        async with self.bot.db.execute("SELECT user_id FROM ineligible_users WHERE user_id = ? AND gamemode = ?",
                                       [int(user.id), gamemode]) as cursor:
            is_ineligible = await cursor.fetchone()
        if is_ineligible:
            return False

        member = guild.get_member(int(user.id))

        async with self.bot.db.execute("SELECT role_id FROM eligibility_roles WHERE gamemode = ?",
                                       [gamemode]) as cursor:
            eligibility_role_rows = await cursor.fetchall()

        for eligible_role_row in eligibility_role_rows:
            if member.get_role(int(eligible_role_row[0])):
                return True

        return False

    async def time_check(self):
        async with self.bot.db.execute("SELECT value FROM contest_config_int WHERE key = ?", ["start_time"]) as cursor:
            start_time_row = await cursor.fetchone()

        async with self.bot.db.execute("SELECT value FROM contest_config_int WHERE key = ?", ["end_time"]) as cursor:
            end_time_row = await cursor.fetchone()

        if not start_time_row or not end_time_row:
            return False

        if int(start_time_row[0]) < time.time() < int(end_time_row[0]):
            return True

        return False

    @commands.command(name="check_eligibility", brief="Check eligibility")
    @commands.check(permissions.is_not_ignored)
    async def check_eligibility(self, ctx):
        if ctx.guild:
            logging.warning("!check_eligibility called in guild")
            return

        guild = self.bot.representing_guild
        if not guild:
            await ctx.send("Bot misconfigured")
            return

        embed = discord.Embed(
            description="",
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
            embed.description += f"It's either too early or too late to participate in this contest."

        embed.set_author(
            name=f"Eligibility: {str(ctx.author.display_name)}",
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
            await ctx.send(f"You are not eligible to participate in this contest with gamemode: {gamemode}. "
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
            attachment_row = await cursor.fetchone()
        async with self.bot.db.execute("SELECT value FROM contest_config WHERE key = ?", ["instructions"]) as cursor:
            instructions_row = await cursor.fetchone()
        async with self.bot.db.execute("SELECT value FROM contest_config_int WHERE key = ?", ["cycle_id"]) as cursor:
            cycle_id_row = await cursor.fetchone()
        async with self.bot.db.execute("SELECT duration FROM durations WHERE gamemode = ?", [gamemode]) as cursor:
            duration_row = await cursor.fetchone()

        if not (cycle_id_row and attachment_row and instructions_row and duration_row):
            await ctx.send("Bot unconfigured!")
            return

        cycle_id = cycle_id_row[0]
        attachment = attachment_row[0]
        instructions = instructions_row[0]
        duration = duration_row[0]

        async with self.bot.db.execute(
                "SELECT timestamp_requested, timestamp_timeslot_deadline, timestamp_submitted, gamemode "
                "FROM participation WHERE user_id = ? AND cycle_id = ?",
                [int(member.id), int(cycle_id)]
        ) as cursor:
            participation_rows = await cursor.fetchall() or []

        for participation_row in participation_rows:
            timestamp_requested, timestamp_deadline, timestamp_submitted, requested_gamemode = participation_row

            if requested_gamemode == gamemode:
                response_str = (f"You have already participated in this gamemode this cycle. "
                                f"You signed up on <t:{timestamp_requested}:f> "
                                f"with deadline of <t:{timestamp_deadline}:f>. ")
                if timestamp_submitted:
                    response_str += f"You have submitted your entry on <t:{timestamp_submitted}:f>"
                else:
                    response_str += f"You have not submitted an entry."
                await ctx.send(response_str)
                return
            else:
                # not submitted and still has time
                if not timestamp_submitted and time.time() < (timestamp_deadline + 5 * 60):
                    response_str = (f"You are already participating in this contest in {requested_gamemode} "
                                    f"and have not submitted an entry. "
                                    f"You signed up on <t:{timestamp_requested}:f> "
                                    f"with deadline of <t:{timestamp_deadline}:f>. ")
                    await ctx.send(response_str)
                    return

        timestamp_requested = int(time.time())
        timestamp_submitted = None
        timestamp_timeslot_deadline = timestamp_requested + (int(duration) * 60)
        timestamp_grace_deadline = timestamp_timeslot_deadline + (5 * 60)
        default_status = "DNS"

        await self.bot.db.execute(
            "INSERT INTO participation VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)",
            [
                int(cycle_id),
                int(member.id),
                str(member.name),
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
            description=instructions,
            color=0xFFFFFF
        )

        # source https://www.freepik.com/free-vector/simple-vibing-cat-square-meme_58459053.htm
        embed.set_image(url="https://i.imgur.com/UMhMLui.jpeg")

        embed.description += (f"\n\nI will remind you when it's time to submit, "
                              f"so make sure your notifications are working. ")

        if member.status == discord.Status.dnd:
            embed.description += f"You are on \"Do not disturb\", turn it off to get the notification in time."

        embed.description += f"\n\n** Attachment: {attachment} **"

        embed.add_field(name="Cycle", value=int(cycle_id))
        embed.add_field(name="Gamemode", value=gamemode)
        embed.add_field(name="Start time", value=f"<t:{timestamp_requested}:f>")
        embed.add_field(name="Mapping Deadline", value=f"<t:{timestamp_timeslot_deadline}:f>")
        embed.add_field(name="Submission Deadline", value=f"<t:{timestamp_grace_deadline}:f>")

        embed.set_author(
            name=f"Participation: {str(ctx.author.display_name)}",
            icon_url=ctx.author.display_avatar.url
        )
        await ctx.send(embed=embed)

        await self.bot.db.execute(
            "INSERT INTO reminders VALUES (?, ?, ?, ?)",
            [int(cycle_id), int(timestamp_timeslot_deadline), int(ctx.author.id), str(gamemode)]
        )
        await self.bot.db.commit()

        self.bot.background_tasks.append(
            self.bot.loop.create_task(self.reminder_task(
                int(timestamp_timeslot_deadline), int(ctx.author.id), gamemode)
            )
        )

    @commands.command(name="submit", brief="Submit entry, MUST attach a .osu file to the message")
    @commands.check(permissions.is_not_ignored)
    async def submit(self, ctx):
        if ctx.guild:
            await ctx.send("This command can only be used in a DM")
            return

        guild = self.bot.representing_guild
        if not guild:
            await ctx.send("Bot misconfigured. Representing server not set.")
            return

        if not len(ctx.message.attachments) == 1:
            await ctx.send(f"Please attach your entry, type !submit, and send. Only attach one file.")
            return

        attachment = ctx.message.attachments[0]

        if not attachment.filename.endswith(".osu"):
            await ctx.send(f"Please submit a **.osu** file. Not **.osz** or anything else.")
            return

        if attachment.size > 2 * 1024 * 1024:
            await ctx.send(f"Attached .osu file is too large, max 2 MB is allowed.")
            return

        contents = await attachment.read()

        beatmap_obj = Beatmap(contents.decode())
        detected_gamemode = beatmap_obj.get_mode_str()

        async with self.bot.db.execute("SELECT value FROM contest_config_int WHERE key = ?", ["cycle_id"]) as cursor:
            cycle_id_row = await cursor.fetchone()

        if not cycle_id_row:
            await ctx.send("Bot misconfigured. Cycle ID not set.")
            return

        cycle_id = cycle_id_row[0]

        async with self.bot.db.execute(
                "SELECT gamemode, timestamp_grace_deadline "
                "FROM participation WHERE user_id = ? AND cycle_id = ? AND gamemode = ?",
                [int(ctx.author.id), int(cycle_id), detected_gamemode]) as cursor:
            participation_data = await cursor.fetchone()

        if not participation_data:
            await ctx.send(f"You have not signed up for the contest, thus you can't submit an entry.")
            return

        gamemode = participation_data[0]

        timestamp_grace_deadline = participation_data[1]

        timestamp_submitted = int(time.time())
        # check deadline

        async with self.bot.db.execute("SELECT value FROM contest_config_int WHERE key = ?",
                                       ["allow_late_submission"]) as cursor:
            allow_late_submission_row = await cursor.fetchone()

        allow_late_submission = False
        status = "VALID"
        is_late = False
        how_late = 0

        if timestamp_submitted > int(timestamp_grace_deadline):
            # Accept late submissions upto 24 hours but mark them as LATE
            # 24 hours is chosen just in case someone complains:
            # "oh no I had a power/internet outage yesterday but pls take it, I still want feedback"

            is_late = True
            how_late = timestamp_submitted - int(timestamp_grace_deadline)
            status = "LATE+" + str(how_late)

            if allow_late_submission_row:
                allow_late_submission = bool(allow_late_submission_row[0])

            print(allow_late_submission)
            if not allow_late_submission:
                await ctx.send(f"Deadline has passed. You can not submit anymore. "
                               f"You had until <t:{timestamp_grace_deadline}:f> to submit your entry. "
                               f"You are late by {str(how_late)} seconds. ")
                return

            if timestamp_submitted > int(timestamp_grace_deadline) + 24 * 60 * 60:  # 24 hours
                await ctx.send(f"Deadline has long passed. You can not submit anymore. "
                               f"You had until <t:{timestamp_grace_deadline}:f> to submit your entry."
                               f"You are late by {str(how_late)} seconds. ")
                return

        async with self.bot.db.execute(
                "SELECT * FROM submissions WHERE user_id = ? AND cycle_id = ? AND gamemode = ?",
                [int(ctx.author.id), int(cycle_id), gamemode]) as cursor:
            has_already_submitted = await cursor.fetchone()

        if has_already_submitted:
            if is_late:
                await ctx.send(f"Deadline has passed. You can not update your submission anymore. "
                               f"You had until <t:{timestamp_grace_deadline}:f> to update your entry.")
                return

            await self.bot.db.execute(
                "UPDATE submissions "
                "SET file = ?, timestamp_submitted = ?, status = ? "
                "WHERE user_id = ? AND cycle_id = ? AND gamemode = ?",
                [contents, timestamp_submitted, status, int(ctx.author.id), int(cycle_id), str(gamemode)])
            await ctx.send(f"I have updated your entry. Please note that you can't do this past the hard deadline.")
        else:
            await self.bot.db.execute(
                "INSERT INTO submissions VALUES (?, ?, ?, ?, ?, ?)",
                [int(cycle_id), int(ctx.author.id), str(gamemode), timestamp_submitted, contents, status])

        await self.bot.db.execute(
            "UPDATE participation "
            "SET timestamp_submitted = ?, status = ? "
            "WHERE user_id = ? AND cycle_id = ? AND gamemode = ?",
            [timestamp_submitted, status, int(ctx.author.id), int(cycle_id), gamemode])

        await self.bot.db.commit()

        embed = discord.Embed(
            color=0xFFFFFF
        )
        embed.set_image(url="https://i.imgur.com/1kSXSXk.png")
        embed.add_field(name="Gamemode", value=gamemode)
        embed.add_field(name="Status", value=status)
        embed.add_field(name="Submission time", value=f"<t:{str(timestamp_submitted)}:f>")

        await ctx.send(f"Submitted!", embed=embed)

        if is_late:
            await ctx.send(f"Please note that the deadline was passed by {str(how_late)} seconds. "
                           f"I have marked your submission as **{status}**.")

    @commands.command(name="debug_reminder", brief="debug_reminder")
    @commands.check(permissions.is_admin)
    @commands.check(permissions.is_not_ignored)
    async def debug_reminder(self, ctx, delay=5, gamemode="osu"):
        async with self.bot.db.execute("SELECT value FROM contest_config_int WHERE key = ?", ["cycle_id"]) as cursor:
            cycle_id_row = await cursor.fetchone()
        cycle_id = cycle_id_row[0]

        timestamp = int(time.time() + int(delay))
        await self.bot.db.execute("INSERT INTO reminders VALUES (?, ?, ?, ?)",
                                  [int(cycle_id), int(timestamp), int(ctx.author.id), str(gamemode)])
        await self.bot.db.commit()

        self.bot.background_tasks.append(
            self.bot.loop.create_task(self.reminder_task(int(timestamp), int(ctx.author.id), gamemode))
        )
        await ctx.send(f"Debug reminder set <t:{timestamp}:R>")

    @commands.command(name="debug_submit", brief="debug_submit")
    @commands.check(permissions.is_admin)
    @commands.check(permissions.is_not_ignored)
    async def debug_submit(self, ctx):
        if not len(ctx.message.attachments) == 1:
            await ctx.send(f"Please attach your entry, type !submit, and send. Only attach one file.")
            return

        attachment = ctx.message.attachments[0]

        if not attachment.filename.endswith(".osu"):
            await ctx.send(f"Please submit a **.osu** file. Not **.osz** or anything else.")
            return

        if attachment.size > 2 * 1024 * 1024:
            await ctx.send(f"Attached .osu file is too large, max 2 MB is allowed.")
            return

        contents = await attachment.read()

        beatmap_obj = Beatmap(contents.decode())

        async with self.bot.db.execute("SELECT value FROM contest_config_int WHERE key = ?", ["cycle_id"]) as cursor:
            cycle_id_row = await cursor.fetchone()

        cycle_id = cycle_id_row[0]

        await self.bot.db.execute(
            "INSERT INTO submissions VALUES (?, ?, ?, ?, ?, ?)",
            [int(cycle_id), int(ctx.author.id), str(beatmap_obj.get_mode_str()), int(time.time()), contents, "DEBUG"])
        await self.bot.db.commit()

        await ctx.send(f"submitted for gamemode: {beatmap_obj.get_mode_str()}")

    @commands.Cog.listener()
    async def on_message(self, message):
        if message.guild:
            return

        if not len(message.attachments) == 1:
            return

        attachment = message.attachments[0]

        if not attachment.filename.endswith(".osu"):
            return

        if attachment.size > 2 * 1024 * 1024:
            return

        if message.content.startswith("!submit"):
            return

        await message.reply("Please use the **!submit** command to submit your entry. "
                            "Type **!submit**, attach your entry and then send.")

    async def reminder_task(self, timestamp, user_id, gamemode):
        await self.bot.wait_until_ready()

        async with self.bot.db.execute("SELECT value FROM contest_config_int WHERE key = ?", ["cycle_id"]) as cursor:
            cycle_id_row = await cursor.fetchone()

        cycle_id = cycle_id_row[0]

        delay_amount = int(timestamp) - int(time.time())

        if delay_amount < 0:
            recipient_str = user_id
            recipient = self.bot.get_user(int(user_id))
            if recipient:
                recipient_str = recipient.name

            print(f"The reminder to {recipient_str} was never sent because the bot was down at that exact time.")
            await self.nuke_reminder(cycle_id, timestamp, user_id, gamemode)
            return

        await asyncio.sleep(delay_amount)

        async with self.bot.db.execute("SELECT * FROM reminders "
                                       "WHERE cycle_id = ? AND timestamp = ? AND user_id = ? AND gamemode = ?",
                                       [int(cycle_id), int(timestamp), int(user_id), str(gamemode)]) as cursor:
            is_not_deleted = await cursor.fetchone()

        async with self.bot.db.execute("SELECT * FROM submissions "
                                       "WHERE cycle_id = ? AND user_id = ? AND gamemode = ?",
                                       [int(cycle_id), int(user_id), str(gamemode)]) as cursor:
            already_submitted = await cursor.fetchone()

        if already_submitted or (not is_not_deleted):
            await self.nuke_reminder(cycle_id, timestamp, user_id, gamemode)
            return

        member = self.bot.get_user(int(user_id))
        if not member:
            await self.nuke_reminder(cycle_id, timestamp, user_id, gamemode)
            return

        grace_deadline = timestamp + ((5 * 60) - 20)  # tell them they have 20 seconds less than they actually have
        # to get rid of possible complains

        await member.send(f"Hi, {member.name}, the deadline to submit your entry is upon you. "
                          f"Now is the time to get the .osu file and send it. "
                          f"Hard submission deadline is <t:{grace_deadline}:R> to account for internet issues, etc. "
                          f"Please do not run this clock down and submit ASAP! ")

    async def nuke_reminder(self, cycle_id, timestamp, user_id, gamemode):
        await self.bot.db.execute("DELETE FROM reminders "
                                  "WHERE cycle_id = ? AND timestamp = ? AND user_id = ? AND gamemode = ?",
                                  [int(cycle_id), int(timestamp), int(user_id), str(gamemode)])
        await self.bot.db.commit()
        return


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
            "file"    BLOB NOT NULL,
            "status"    TEXT NOT NULL
        )
        """)
    await bot.db.execute("""
        CREATE TABLE IF NOT EXISTS "reminders" (
            "cycle_id"    INTEGER NOT NULL,
            "timestamp"    INTEGER NOT NULL,
            "user_id"    INTEGER NOT NULL,
            "gamemode"    TEXT NOT NULL
        )
        """)
    await bot.db.commit()

    async with bot.db.execute("SELECT * FROM reminders") as cursor:
        saved_reminder_rows = await cursor.fetchall()

    await bot.add_cog(Participation(bot, saved_reminder_rows))
