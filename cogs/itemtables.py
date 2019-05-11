import discord
import asyncio
import re
from random import randint
from discord.ext import commands
from bfunc import *


class ItemTables(commands.Cog):
    def __init__ (self, bot):
        self.bot = bot

#     async def itemTable(tierArray, tierSubArray,sheet, ctx, random):
#         print('hello')

#     @commands.cooldown(1, 10, type=commands.BucketType.member)
#     @commands.command()
#     async def rit(self, ctx, *, random=""):
#         await itemTable(ritTierArray, ritSubArray, ritSheet, ctx, random)
    
#     @commands.cooldown(1, 10, type=commands.BucketType.member)
#     @commands.command()
#     async def mit(self,ctx, *, queryString=""):
#         await itemTable(tierArray, tpArray, sheet, ctx, queryString) 

def setup(bot):
    bot.add_cog(ItemTables(bot))
