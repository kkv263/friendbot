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
    @commands.has_any_role('Mod Friend', 'Admins', 'Trial Mod Friend')
    async def check(self, ctx, numLogs=1):
        # PLayer log channel
        channel = self.bot.get_channel(551994782814044170) 
        numLogs = int(numLogs)

        msgFound = False
        async with channel.typing():
            async for message in channel.history(limit=numLogs, oldest_first=False):
                msgSplit = message.content.splitlines()
                async for messageOld in channel.history(before=message, oldest_first=False):
                  if msgSplit[0] == messageOld.content.splitlines()[0]:
                      oldMsgSplit = messageOld.content.splitlines()
                      msgFound = True
                      break
                if msgFound:
                    break

        patternCP = re.compile(r'([\d.]{0,})(?=CP)\S+(?<=Level)(\d+)\S?\((.*?)\)', re.I)
        oldlistCP = patternCP.search(oldMsgSplit[2].replace(" ",""))
        newlistCP = patternCP.search(msgSplit[2].replace(" ",""))
        # [1] = CP added, [2] = Current Level, [3] = Current CP / Total CP
        print(oldlistCP.groups())
        print(newlistCP.groups())
        print(oldlistTP.groups())
        print(newlistTP.groups())

        oldCurrentCP = oldlistCP.group(3).split('/')
        maxCP = float(oldCurrentCP[1])
        addCP = float(newlistCP.group(1))
        currentCP = newlistCP.group(3).split('/')

        tpItemList = msgSplit[3].split(';')

        patternTP = re.compile(r'([\d.]{0,}\s(?=T))\S+(?<=P).([\w+ ]{0,})\((.*?)\)', re.I)
        oldlistTP = patternTP.search(oldMsgSplit[3])
        newlistTP = patternTP.search(tpItemList[0])

        addTP = float(newlistTP.group(1))
        tpItem = newlistTP.group(2).strip()
        oldCurrentTP = oldlistTP.group(3).split('/')
        currentTP = newlistTP.group(3).split('/')
        tpCheck = False

        queryTP = sheet.findall(re.compile(tpItem, re.IGNORECASE))[0]
        itemMaxTP = int(sheet.cell(3,queryTP.col).value[0:2])
        refreshKey(refreshTime)

        if (float(oldCurrentTP[0]) == float(oldCurrentTP[1])):
            if addTP == float(currentTP[0]):
              tpCheck = True
        else:
            newCurrentTP = addTP + float(oldCurrentTP[0]) if addTP + float(oldCurrentTP[0]) < itemMaxTP else abs((addTP + float(oldCurrentTP[0])) - itemMaxTP)
            print(newCurrentTP)
            if newCurrentTP == float(currentTP[0]):
                tpCheck = True
                

        print (tpCheck)
        print(newCurrentCP == float(currentCP[0]) and float(currentCP[1]) == levelCP)

        newCurrentCP = addCP + float(oldCurrentCP[0]) if addCP + float(oldCurrentCP[0]) < maxCP else abs((addCP + float(oldCurrentCP[0])) - maxCP)
        levelCP = 4 if int(newlistCP.group(2)) < 5 else 8


        if newCurrentCP == float(currentCP[0]) and float(currentCP[1]) == levelCP and tpCheck:
            await message.add_reaction('✅')
        else:
            await message.add_reaction('❌')


def setup(bot):
    bot.add_cog(Log(bot))
