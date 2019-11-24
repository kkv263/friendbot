import discord
import asyncio
from datetime import datetime,timedelta
from discord.utils import get        
from discord.ext import commands
from bfunc import roleArray, calculateTreasure, timeConversion 

class Tp(commands.Cog):
    def __init__ (self, bot):
        self.bot = bot
    
    @commands.group()
    async def tp(self, ctx):	
        pass
      
    @tp.command()
    async def buy(self, ctx ,magicItem, *, charName):
        pass


def setup(bot):
    bot.add_cog(Tp(bot))
