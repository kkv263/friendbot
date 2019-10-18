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

        # Test
        # channel = self.bot.get_channel(577227687962214406) 
        numLogs = int(numLogs)

        if numLogs > 5:
            return

        def checkLog(oldMsgSplit,msgSplit):
            patternCP = re.compile(r'([\d.]{0,})(?=CP)\S+(?<=Level)(\d+)[\S?]{0,}\((.*?)\)', re.I)
            oldlistCP = patternCP.search(oldMsgSplit[2].replace(" ",""))
            newlistCP = patternCP.search(msgSplit[2].replace(" ",""))

            oldCurrentCP = oldlistCP.group(3).split('/')
            oldCurrentCP[0] = oldCurrentCP[0].replace("CP","")
            oldCurrentCP[1] = oldCurrentCP[1].replace("CP","")
            print(oldCurrentCP)
            maxCP = float(oldCurrentCP[1])
            addCP = float(newlistCP.group(1))
            currentCP = newlistCP.group(3).split('/')
            currentCP[0] = currentCP[0].replace("CP","")
            currentCP[1] = currentCP[1].replace("CP","")

            tpItemList = msgSplit[3].split(';')
            print(tpItemList)
            print(oldMsgSplit[3])

            patternTP = re.compile(r'([\d.]{0,}\s?(?=T))\S+(?<=P).([\w+ ]{0,})\((.*?)\)', re.I)
            oldlistTP = patternTP.search(oldMsgSplit[3])
            newlistTP = patternTP.search(tpItemList[0])

            # [1] = CP added, [2] = Current Level, [3] = Current CP / Total CP
            print(oldlistCP.groups())
            print(newlistCP.groups())
            print(oldlistTP.groups())
            print(newlistTP.groups())

            addTP = float(newlistTP.group(1))
            tpItem = newlistTP.group(2).strip()
            oldCurrentTP = oldlistTP.group(3).split('/')
            currentTP = newlistTP.group(3).split('/')
            oldCurrentTP[0] = oldCurrentTP[0].replace("TP","")
            oldCurrentTP[1] = oldCurrentTP[1].replace("TP","")
            currentTP[0] = currentTP[0].replace("TP","")
            currentTP[1] = currentTP[1].replace("TP","")
            tpCheck = False
            cpCheck = False

            queryTP = sheet.findall(re.compile(tpItem, re.IGNORECASE))[0]
            itemMaxTP = int(sheet.cell(3,queryTP.col).value[0:2])
            refreshKey(refreshTime)

            # TODO check for two items TP
            if (float(oldCurrentTP[0]) == float(oldCurrentTP[1])):
                if addTP == float(currentTP[0]):
                  tpCheck = True
            else:
                newCurrentTP = addTP + float(oldCurrentTP[0]) if addTP + float(oldCurrentTP[0]) < itemMaxTP else abs((addTP + float(oldCurrentTP[0])) - itemMaxTP)
                if newCurrentTP == float(currentTP[0]):
                    tpCheck = True
                    

            # TODO: Check for levelup
            if (float(oldCurrentCP[0]) == float(oldCurrentCP[1])):
                if addCP == float(currentCP[0]):
                    cpCheck = True
            else:
                newCurrentCP = addCP + float(oldCurrentCP[0]) if addCP + float(oldCurrentCP[0]) < maxCP else abs((addCP + float(oldCurrentCP[0])) - maxCP)
                if newCurrentCP == float(currentCP[0]):
                    cpCheck = True

            levelCP = 4 if int(newlistCP.group(2)) < 5 else 8

            print (tpCheck)
            print (cpCheck)

            return cpCheck and float(currentCP[1]) == levelCP and tpCheck

        # TODO check multiple logs
        msgFound = False
        async with channel.typing():
            async for message in channel.history(limit=numLogs, oldest_first=False):
                msgSplit = message.content.splitlines()
                print(msgSplit)
                async for messageOld in channel.history(before=message, oldest_first=False):
                  if msgSplit[0] == messageOld.content.splitlines()[0]:
                      oldMsgSplit = messageOld.content.splitlines()
                      if (checkLog(oldMsgSplit,msgSplit)):
                          await message.add_reaction('✅')
                      else:
                          await message.add_reaction('❌')
                      break


def setup(bot):
    bot.add_cog(Log(bot))
