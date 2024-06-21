import discord
from discord.ext import commands
from mtd.modules import permissions
import json


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

        await self.bot.db.execute("DELETE FROM participation WHERE user_id = ? AND cycle_id",
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

        async with self.bot.db.execute("SELECT * FROM participation WHERE cycle_id = ?", [int(cycle_id)]) as cursor:
            all_participation = await cursor.fetchall()

        await ctx.send(file=discord.File(fp=json.dumps(participants_json_builder(all_participation), indent=4),
                                         filename="participants.json"))


async def setup(bot):
    await bot.add_cog(ContestTools(bot))
