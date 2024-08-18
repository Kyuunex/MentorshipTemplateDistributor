import discord
from discord.ext import commands
from mtd.modules import permissions
import json
import zipfile
import os
import tempfile


def participants_json_builder(results):
    buffer = []
    for result in results:
        buffer.append({
            "cycle_id": result[0],
            "user_id": result[1],
            "username": result[2],
            "nickname": result[3],
            "gamemode": result[4],
            "timestamp_requested": result[5],
            "timestamp_submitted": result[6],
            "timestamp_timeslot_deadline": result[7],
            "timestamp_grace_deadline": result[8],
            "status": result[9],
        })

    return buffer


class ContestTools(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @commands.command(name="reset_participant", brief="In case something breaks, they get another go.")
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

        await self.bot.db.execute("DELETE FROM participation WHERE user_id = ? AND cycle_id = ?",
                                  [int(user_id), int(cycle_id[0])])
        await self.bot.db.commit()

        await ctx.send(f"{user_id} has been reset")

    @commands.command(name="export_participants", brief="Export participant data (JSON) download")
    @commands.check(permissions.is_admin)
    @commands.check(permissions.is_not_ignored)
    async def export_participants(self, ctx):
        """
        Export participant data in a JSON format. Does not contain submitted files.
        """

        async with self.bot.db.execute("SELECT value FROM contest_config_int WHERE key = ?", ["cycle_id"]) as cursor:
            cycle_id_row = await cursor.fetchone()

        if not cycle_id_row:
            await ctx.send("Please set a cycle ID first.")
            return

        cycle_id = cycle_id_row[0]

        async with self.bot.db.execute("SELECT * FROM participation WHERE cycle_id = ?", [int(cycle_id)]) as cursor:
            all_participation_rows = await cursor.fetchall()

        if not all_participation_rows:
            await ctx.send(f"There are no participants for **cycle {cycle_id}**")
            return

        # TODO: make this safer for non-docker execution
        # UPDATE: Kinda done?

        with tempfile.TemporaryDirectory() as tempdir:
            full_export_path = os.path.join(tempdir, "participants.json")
            with open(full_export_path, "w") as f:
                json.dump(participants_json_builder(all_participation_rows), f, indent=4)

            await ctx.send(file=discord.File(fp=full_export_path, filename="participants.json"))

    @commands.command(name="export_submissions", brief="Export submissions (in a zip download)")
    @commands.check(permissions.is_admin)
    @commands.check(permissions.is_not_ignored)
    async def export_submissions(self, ctx):
        """
        Exports submissions as a ZIP file.

        TODO: Make this safe to run in a non-docker environment.
        """

        async with self.bot.db.execute("SELECT value FROM contest_config_int WHERE key = ?", ["cycle_id"]) as cursor:
            cycle_id_row = await cursor.fetchone()

        if not cycle_id_row:
            await ctx.send("Please set a cycle ID first.")
            return

        cycle_id = cycle_id_row[0]

        async with self.bot.db.execute("SELECT * FROM submissions WHERE cycle_id = ?", [int(cycle_id)]) as cursor:
            all_submission_rows = await cursor.fetchall()

        if not all_submission_rows:
            await ctx.send(f"There are no submissions for **cycle {cycle_id}**")
            return

        with tempfile.TemporaryDirectory() as tempdir:
            submission_dir = os.path.join(tempdir, "submissions")
            os.mkdir(submission_dir)

            for submission_row in all_submission_rows:
                _, user_id, gamemode, timestamp_submitted, file, status = submission_row
                
                # TODO: JOIN before
                async with self.bot.db.execute("SELECT nickname FROM participation "
                                               "WHERE cycle_id = ? AND gamemode = ? AND user_id = ?",
                                               [cycle_id, gamemode, user_id]) as cursor:
                    username_row = await cursor.fetchone()

                # The participate command always sets the nickname in the db,
                # but the debug command does insert participation data
                osu_username = username_row[0] if username_row else "debug_user"

                filename = f"{status} {gamemode} {user_id} {osu_username}.osu"

                with open(os.path.join(submission_dir, filename), "wb") as f:
                    f.write(file)

            zip_path = os.path.join(tempdir, "submissions.zip")

            # Note: zipfile.ZIP_DEFLATED requires zlib, I switched to zipfile.ZIP_STORED as it requires nothing.
            with zipfile.ZipFile(zip_path, "x", zipfile.ZIP_DEFLATED) as zip_file:
                for submission_file in os.listdir(submission_dir):
                    zip_file.write(os.path.join(submission_dir, submission_file), submission_file)

            await ctx.send(file=discord.File(zip_path, filename=f"Submissions Cycle {cycle_id}.zip"))


async def setup(bot):
    await bot.add_cog(ContestTools(bot))
