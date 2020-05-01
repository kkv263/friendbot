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
        # This is the channel where the bot will check the logs. If you're using a test channel grab the id and put it here
        channel = self.bot.get_channel(551994782814044170) 

        numLogs = int(numLogs)

        # Number of logs to check, from most recent. You can also set a limit. If it's greater than 10... stop.
        if numLogs > 10:
            return


        # Here it will check the logs with old log and new log.
        # This is actually STEP 2 so check STEP 1 first
        def checkLog(oldMsgSplit,msgSplit, gpMsgSplit):
            oldCpString=oldTpString=newTpString=newCpString=newGpString=oldGpString = ""
            print(gpMsgSplit)

            # Check if CP and TP in the old log
            for o in oldMsgSplit:
                if "CP" in o:
                    oldCpString = o

                if "TP" in o:
                    oldTpString = o

                if oldCpString and oldTpString:
                    break


            # Check for CP TP GP in new log.
            for m in msgSplit:
                if "CP" in m:
                    newCpString = m
                if "TP" in m:
                    newTpString = m
                if "GP" in m:
                    newGpString = m
                if newCpString and newTpString and newGpString:
                    break

            if gpMsgSplit != list():
                oldGpString = "1GP: 0GP"
                            
            else:
                for g in oldMsgSplit:
                    if "GP" in g:
                       oldGpString = g
                       break

            # Uses regex here. Because.... people like to format logs differently. I believe what I'm looking for is CP and "Level" here to get the CP. 
            # TP and GP the same way
            patternCP = re.compile(r'([\d.]{0,})(?=CP)\S+(?<=Level)(\d+)[\S?]{0,}\((.*?)\)', re.I)
            oldlistCP = patternCP.search(oldCpString.replace(" ",""))
            newlistCP = patternCP.search(newCpString.replace(" ",""))

            oldCurrentCP = oldlistCP.group(3).split('/')
            oldCurrentCP[0] = oldCurrentCP[0].replace("CP","")
            oldCurrentCP[1] = oldCurrentCP[1].replace("CP","")
            maxCP = float(oldCurrentCP[1])
            addCP = float(newlistCP.group(1))
            currentCP = newlistCP.group(3).split('/')
            currentCP[0] = currentCP[0].replace("CP","")
            currentCP[1] = currentCP[1].replace("CP","")

            patternTP = re.compile(r'([\d.]{0,}\s?(?=T))\S+(?<=P).\s?([\w*, ]{0,})\((.*?)\);?\s?([\w*, ]{0,})\(?([^\)]+)\)?', re.I)
            oldlistTP = patternTP.search(oldTpString + " ")
            newlistTP = patternTP.search(newTpString + " ")

            patternGP = re.compile(r'[\d.]+(?=\S?GP)', re.I)
            oldlistGP = patternGP.findall(oldGpString.replace(" ","").replace(',', ""))
            newlistGP = patternGP.findall(newGpString.replace(" ","").replace(',', ""))

            # I print stuff to make sure math is right.
            # [1] = CP added, [2] = Current Level, [3] = Current CP / Total CP
            print(oldlistCP.groups())
            print(newlistCP.groups())
            print(oldlistTP.groups())
            print(newlistTP.groups())
            print(oldlistGP)
            print(newlistGP)

            # Here I check if TP Is correct
            addTP = float(newlistTP.group(1))
            if oldlistTP.group(5) != " ":
                oldCurrentTP = oldlistTP.group(5).split('/')
            else:
                oldCurrentTP = oldlistTP.group(3).split('/')

            currentTP = newlistTP.group(3).split('/')
            oldCurrentTP[0] = oldCurrentTP[0].replace("TP","")
            oldCurrentTP[1] = oldCurrentTP[1].replace("TP","")
            currentTP[0] = currentTP[0].replace("TP","")
            currentTP[1] = currentTP[1].replace("TP","")
            tpCheck = False
            cpCheck = False
            gpCheck = False

            # This checks the MIT sheet to make sure its the correct TP.
            tpItem = newlistTP.group(2).strip()
            queryTP = sheet.findall(re.compile(tpItem, re.IGNORECASE))[0]
            itemMaxTP = int(sheet.cell(3,queryTP.col).value[0:2])
            refreshKey(refreshTime)

            if newlistTP.group(5) != " ": 
                newTpItem = newlistTP.group(4).strip()
                queryTP = sheet.findall(re.compile(tpItem, re.IGNORECASE))[0]
                newItemMaxTP = int(sheet.cell(3,queryTP.col).value[0:2])
                refreshKey(refreshTime)
                secondCurrentTP = newlistTP.group(5).split('/')
                secondCurrentTP[0] = float(secondCurrentTP[0].replace("TP",""))
                secondCurrentTP[1] = float(secondCurrentTP[1].replace("TP",""))

            # A bunch of math with CP and TP and GP to make sure they all link up. This is the final check before they get the check mark.
            if (float(oldCurrentTP[0]) == float(oldCurrentTP[1])):
                if newlistTP.group(5) != " ": 
                    if abs(addTP - float(currentTP[1])) > 0 and float(currentTP[1]) == itemMaxTP:
                        if secondCurrentTP[0] == abs(addTP - float(currentTP[1])) and secondCurrentTP[1] == newItemMaxTP:
                            tpCheck = True
                elif addTP == float(currentTP[0]):
                    tpCheck = True
            else:
                newCurrentTP = addTP + float(oldCurrentTP[0]) if addTP + float(oldCurrentTP[0]) < itemMaxTP else abs((addTP + float(oldCurrentTP[0])) - itemMaxTP)
                if newlistTP.group(5) != " ": 

                    if float(currentTP[0]) == itemMaxTP and newItemMaxTP == float(secondCurrentTP[1]) and newCurrentTP == float(secondCurrentTP[0]):
                        tpCheck = True
                else:
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

            if float(oldlistGP[1]) + float(newlistGP[0]) == float(newlistGP[1]) or (int(oldlistGP[0]) == 1 and int(oldlistGP[1]) == 0):
                gpCheck = True

            print (tpCheck)
            print (cpCheck)
            print (gpCheck)

            return cpCheck and float(currentCP[1]) == levelCP and tpCheck and gpCheck

        # TODO check multiple logs
        # STEP 1:
        # Check the channel where logs are located, and basically find keywords. Like CP / TP. Split up those messages.
        msgFound = False
        async with channel.typing():
            async for message in channel.history(limit=numLogs, oldest_first=False):
                msgSplit = message.content.splitlines()
                gpMsgSplit = []
                if 'CP' not in message.content and 'TP' not in message.content:
                      continue
                async for messageOld in channel.history(limit=None, before=message, oldest_first=False):
                  if 'CP' not in messageOld.content and 'TP' not in messageOld.content:
                      if 'GP' in messageOld.content:
                          gpMsgSplit.append(messageOld.content.splitlines())
                      else:
                          continue
                  elif msgSplit[0] == messageOld.content.splitlines()[0]:
                      oldMsgSplit = messageOld.content.splitlines()
                      if gpMsgSplit != list():
                          await message.add_reaction(u"\U0001f538")
                      if (checkLog(oldMsgSplit,msgSplit, gpMsgSplit)):
                          await message.add_reaction('✅')
                      else:
                          await message.add_reaction('❌')
                      break


def setup(bot):
    bot.add_cog(Log(bot))
