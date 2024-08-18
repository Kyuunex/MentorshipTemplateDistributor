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
            cycle_id = await cursor.fetchone()

        if not cycle_id:
            await ctx.send("Please set a cycle ID first.")
            return

        async with self.bot.db.execute("SELECT * FROM participation WHERE cycle_id = ?", [int(cycle_id[0])]) as cursor:
            all_participation = await cursor.fetchall()

        # TODO: make this safer for non-docker execution

        with tempfile.TemporaryDirectory() as tempdir:
            with open("participants.json", "w") as f:
                json.dump(participants_json_builder(all_participation), f, indent=4)

            await ctx.send(file=discord.File(fp="participants.json", filename="participants.json"))

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
            all_submissions = await cursor.fetchall()

        with tempfile.TemporaryDirectory() as tempdir:
            os.mkdir(os.path.join(tempdir, "submissions"))
            for submission in all_submissions:
                _, user_id, gamemode, timestamp_submitted, file, status = submission
                
                # TODO: JOIN before
                async with self.bot.db.execute("SELECT nickname FROM participation WHERE cycle_id = ? AND gamemode = ? AND user_id = ?", [cycle_id, gamemode, user_id]) as cursor:
                    username = await cursor.fetchone() or ("")
                
                
                filename = f"{status} {gamemode} {user_id} {username[0]}.osu"
                submission_dir = os.path.join(tempdir, "submissions")
                with open(os.path.join(submission_dir, filename), "w") as f:
                    f.write(file.decode("utf-8"))

            with zipfile.ZipFile(os.path.join(tempdir, "submissions.zip"), "w", zipfile.ZIP_DEFLATED) as zip_file:
                for submission_file in os.listdir(submission_dir):
                    zip_file.write(os.path.join(submission_dir, submission_file), submission_file)

            await ctx.send(file=discord.File(os.path.join(tempdir, "submissions.zip"), filename=f"Submissions Cycle {cycle_id}.zip"))


async def setup(bot):
    await bot.add_cog(ContestTools(bot))
