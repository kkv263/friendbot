import discord
import asyncio
from itertools import cycle
from discord.ext import tasks, commands
from bfunc import statuses

class Stat(commands.Cog):
    def __init__ (self, bot):
        self.bot = bot
        self.status = cycle(statuses)
        self.msg = next(self.status)
        self.status_change.start()
    
    def cog_unload(self):
        self.status_change.cancel()

    @tasks.loop(seconds=5.0)
    async def status_change(self):
        await self.bot.change_presence(activity=discord.Activity(name=self.msg, type=discord.ActivityType.watching))
        self.msg = next(self.status)

    @status_change.before_loop
    async def before_status_change(self):
        print('Waiting...')
        await self.bot.wait_until_ready()

def setup(bot):
    bot.add_cog(Stat(bot))