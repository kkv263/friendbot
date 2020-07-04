import discord
import asyncio
import requests
import re
from discord.utils import get        
from discord.ext import commands
from cogs.misc import Misc 

def admin_or_owner():
    async def predicate(ctx):
        
        role = get(ctx.message.guild.roles, name = "Admin")
        output = (role in ctx.message.author.roles) or ctx.message.author.id in [220742049631174656, 203948352973438995]
        return  output
    return commands.check(predicate)

class Admin(commands.Cog, name="Admin"):
    def __init__ (self, bot):
        self.bot = bot
    
    @commands.group()
    @admin_or_owner()
    async def reload(self, ctx, cog: str):
        
        try:
            self.bot.reload_extension('cogs.'+cog)
        except Exception as e:
            print(e)


def setup(bot):
    bot.add_cog(Admin(bot))
