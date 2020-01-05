import discord
import asyncio
import re
from discord.utils import get        
from discord.ext import commands
from bfunc import sheet, refreshKey, refreshTime

class Log(commands.Cog):
    def __init__ (self, bot):
        self.bot = bot
    
    @commands.group()
    async def log(self, ctx):	
        pass
      
    @log.command()
    async def edit(self, ctx, num, *, editString=""):
        # The Bot
        botUser = self.bot.get_user(502967681956446209)
        # App Logs channel 
        channel = self.bot.get_channel(577227687962214406) 

        limit = 100
        msgFound = False
        async with channel.typing():
            async for message in channel.history(oldest_first=False, limit=limit):
                if int(num) == message.id and message.author == botUser:
                    editMessage = message
                    msgFound = True
                    break 

        if not msgFound:
            delMessage = await ctx.channel.send(content=f"I couldn't find your game with ID - `{num}` in the last {limit} games. Please try again, I will delete your message and this message in 10 seconds")
            await asyncio.sleep(10) 
            await delMessage.delete()
            await ctx.message.delete() 
            return

        sessionLogEmbed = editMessage.embeds[0]
        sessionLogEmbed.description = editString+"\n"
        await editMessage.edit(embed=sessionLogEmbed)
        delMessage = await ctx.channel.send(content=f"I've edited the summary for Game #{num}.\n```{editString}```\nPlease double check that the edit is correct. I will now delete your message and this message in 30 seconds")
        await asyncio.sleep(30) 
        await delMessage.delete()
        await ctx.message.delete() 

def setup(bot):
    bot.add_cog(Log(bot))
