import discord
import pytz
import re
from datetime import datetime, timezone, timedelta 
from discord.ext import commands
from bfunc import charDatabase, sheet, refreshKey, refreshTime

class Character(commands.Cog):
    def __init__ (self, bot):
        self.bot = bot

    @commands.group()
    async def char(self, ctx):	
        pass

    @commands.cooldown(1, 5, type=commands.BucketType.member)
    @char.command()
    async def create(self,ctx, name, lvl, race, cclass, sStr, sDex, sCon, sInt, sWis, sCha, gp, mItems="", consumes=""):
        def errorCheck():
            roleCreationDict = {
                'Journey Friend':[3],
                'Good Noodle':[4],
                'Elite Noodle':[4,5],
                'True Noodle':[4,5,6],
                'Mega Noodle':[4,5,6,8],
            }
            msg = ""
            # name should be less then 50 chars
            if len(name) > 50:
                msg += "- Your character's name is too long. Please limit to 50 characters.\n"
              
            # level and role check
            if int(lvl) < 1:
                msg += "- You did not enter a valid level to create your character.\n"
                
            elif int(lvl) > 1 and int(lvl) not in [3,4,5,6,8]:
                msg += "- You cannot create a character at that level\n"

            else:
                roleSet = []
                for d in roleCreationDict.keys():
                    if d in (r.name for r in ctx.author.roles):
                        roleSet += roleCreationDict[d]

                roleSet = set(roleSet)

                print(roleSet)

                if int(lvl) not in roleSet:
                    msg += "- You do not have the correct role to create a character at that level\n"
            
            # check magic items
            print (mItems)
            for m in mItems.split(','):
                queryTP = sheet.findall(re.compile(m, re.IGNORECASE))
                print(queryTP)
                if queryTP == list():
                    msg += "- One or more items cannot be found on the Magic Item Table\n"
                    break
            refreshKey(refreshTime)

            return msg

        author = ctx.author
        charRow = [f"{author.name}#{author.discriminator}", name, lvl, race, cclass, sStr, sDex, sCon, sInt, sWis, sCha, 0, 0, 0, gp, "", "", mItems, consumes]
        guild = ctx.guild

        errorMsg = errorCheck()

        if errorMsg:
            await ctx.channel.send(f'There was an error in creating your character:\n```{errorMsg}```')
            return 

        def next_available_row(sheet):
            char_list = list(filter(None, sheet.col_values(2)))
            refreshKey(refreshTime)
            return len(char_list)+1

        next_row = next_available_row(charDatabase)

        for index in range(0, len(charRow)):
            print(index)
            charDatabase.update_cell(next_row, index+2, charRow[index]) 
        refreshKey(refreshTime)





def setup(bot):
    bot.add_cog(Character(bot))
