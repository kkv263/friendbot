import discord
import decimal
import pytz
import re
import requests
import asyncio
import collections
from discord.utils import get        
from datetime import datetime, timezone, timedelta 
from discord.ext import commands
from urllib.parse import urlparse 
from bfunc import numberEmojis, alphaEmojis, commandPrefix, left,right,back, db, callAPI, checkForChar, timeConversion, traceBack

class Character(commands.Cog):
    def __init__ (self, bot):
        self.bot = bot

    async def cog_command_error(self, ctx, error):
        msg = None
            
        if isinstance(error, commands.MissingRequiredArgument):
            if error.param.name == 'char':
                msg = ":warning: You're missing the character name in the command.\n"
            elif error.param.name == "name":
                msg = ":warning: You're missing the name for the character you want to create or respec.\n"
            elif error.param.name == "newname":
                msg = ":warning: You're missing a new name for the character you want to respec.\n"
            elif error.param.name == "level":
                msg = ":warning: You're missing a level for the character you want to create.\n"
            elif error.param.name == "race":
                msg = ":warning: You're missing a race for the character you want to create.\n"
            elif error.param.name == "cclass":
                msg = ":warning: You're missing a class for the character you want to create.\n"
            elif error.param.name == 'bg':
                msg = ":warning: You're missing a background for the character you want to create.\n"
            elif error.param.name == 'sStr' or  error.param.name == 'sDex' or error.param.name == 'sCon' or error.param.name == 'sInt' or error.param.name == 'sWis' or error.param.name == 'sCha':
                msg = ":warning: You're missing a stat (STR, DEX, CON, INT, WIS, or CHA) for the character you want to create.\n"
            elif error.param.name == 'url':
                msg = ":warning: You're missing a URL to add an image to your character's information window.\n"
            elif error.param.name == 'm':
                msg = ":warning: You're missing a magic item to attune to, or unattune from, your character.\n"

            msg += "**Note: if this error seems incorrect, something else may be incorrect.**\n\n"

        if msg:
            if ctx.command.name == "create":
                msg += f'Please follow this format:\n```yaml\n{commandPrefix}create "name" level "race" "class" "backgound" str dex con int wis cha "magic item 1, magic item 2, [...]" "consumable 1, consumable 2, [...]"```\n'
            elif ctx.command.name == "respec":
                msg += f'Please follow this format:\n```yaml\n{commandPrefix}respec "name" "new name" "race" "class" "background" str dex con int wis cha "magic item 1, magic item2, [...]" "consumable 1, consumable 2, [...]"```\n'
            elif ctx.command.name == "retire":
                msg += f'Please follow this format:\n```yaml\n{commandPrefix}retire "character name"```\n'
            elif ctx.command.name == "death":
                msg += f'Please follow this format:\n```yaml\n{commandPrefix}death "character name"```\n'
            elif ctx.command.name == "inventory":
                msg += f'Please follow this format:\n```yaml\n{commandPrefix}inventory "character name"```\n'
            elif ctx.command.name == "info":
                msg += f'Please follow this format:\n```yaml\n{commandPrefix}info "character name"```\n'
            elif ctx.command.name == "image":
                msg += f'Please follow this format:\n```yaml\n{commandPrefix}image "character name" "URL"```\n'
            elif ctx.command.name == "levelup":
                msg += f'Please follow this format:\n```yaml\n{commandPrefix}levelup "character name"```\n'
            elif ctx.command.name == "attune":
                msg += f'Please follow this format:\n```yaml\n{commandPrefix}attune "character name" "magic item"```\n'
            elif ctx.command.name == "unattune":
                msg += f'Please follow this format:\n```yaml\n{commandPrefix}unattune "character name" "magic item"```\n'
            ctx.command.reset_cooldown(ctx)
            await ctx.channel.send(msg)
        # bot.py handles this, so we don't get traceback called.
        elif isinstance(error, commands.CommandOnCooldown):
            return
        elif isinstance(error, commands.UnexpectedQuoteError) or isinstance(error, commands.ExpectedClosingQuoteError) or isinstance(error, commands.InvalidEndOfQuotedStringError):
             return

        # Whenever there's an error with the parameters that bot cannot deduce
        elif isinstance(error, commands.CommandInvokeError):
            msg = f'The command is not working correctly. Please try again and make sure the format is correct.'
            ctx.command.reset_cooldown(ctx)
            await ctx.channel.send(msg)
            await traceBack(ctx,error, True)
        else:
            ctx.command.reset_cooldown(ctx)
            await traceBack(ctx,error)



    @commands.cooldown(1, float('inf'), type=commands.BucketType.user)
    @commands.command()
    async def create(self,ctx, name, level, race, cclass, bg, sStr, sDex, sCon, sInt, sWis, sCha, mItems="", consumes=""):
        characterCog = self.bot.get_cog('Character')
        roleCreationDict = {
            'Journeyfriend':[3],
            'Elite Friend':[3],
            'True Friend':[3],
            'Good Noodle':[4],
            'Elite Noodle':[4,5],
            'True Noodle':[4,5,6],
            'Ascended Noodle':[4,5,6,7],
            'Immortal Noodle':[4,5,6,7,8],
            'Friend Fanatic': [11,10,9],
            'Guild Fanatic':[11,10,9]
        }
        roles = [r.name for r in ctx.author.roles]
        author = ctx.author
        guild = ctx.guild
        channel = ctx.channel
        charEmbed = discord.Embed ()
        charEmbed.set_author(name=ctx.author.display_name, icon_url=ctx.author.avatar_url)
        charEmbed.set_footer(text= "React with ❌ to cancel.\nPlease react with a choice even if no reactions appear.")
        charEmbedmsg = None
        statNames = ['STR','DEX','CON','INT','WIS','CHA']
        bankTP1 = 0
        bankTP2 = 0

        charDict = {
          'User ID': str(author.id),
          'Name': name,
          'Level': int(level),
          'HP': 0,
          'Class': cclass,
          'Background': bg,
          'STR': int(sStr),
          'DEX': int(sDex),
          'CON': int(sCon),
          'INT': int(sInt),
          'WIS': int(sWis),
          'CHA': int(sCha),
          'CP' : 0,
          'Current Item': 'None',
          'GP': 0,
          'Magic Items': 'None',
          'Consumables': 'None',
          'Feats': 'None',
          'Inventory': 'None',
          'Games': 0
        }

        # Prevents name, level, race, class, background from being blank. Resets infinite cooldown and prompts
        if not name:
            await channel.send(content=":warning: The name of your character cannot be blank! Please try again.\n")
            self.bot.get_command('create').reset_cooldown(ctx)
            return

        if not level:
            await channel.send(content=":warning: The level of your character cannot be blank! Please try again.\n")

            self.bot.get_command('create').reset_cooldown(ctx)
            return

        if not race:
            await channel.send(content=":warning: The race of your character cannot be blank! Please try again.\n")
            self.bot.get_command('create').reset_cooldown(ctx)
            return

        if not cclass:
            await channel.send(content=":warning: The class of your character cannot be blank! Please try again.\n")
            self.bot.get_command('create').reset_cooldown(ctx)
            return
        
        if not bg:
            await channel.send(content=":warning: The background of your character cannot be blank! Please try again.\n")
            self.bot.get_command('create').reset_cooldown(ctx)
            return


        lvl = int(level)

        # Provides an error message at the end. If there are more than one, it will join msg.
        msg = ""

        
        # Name should be less then 50 chars
        if len(name) > 64:
            msg += ":warning: Your character's name is too long! The limit is 64 characters.\n"

        playersCollection = db.players
        userRecords = list(playersCollection.find({"User ID": str(author.id), "Name": name }))

        if userRecords != list():
            msg += f":warning: You already have a character by the name of ***{name}***! Please use a different name.\n"
        
        # ██████╗░░█████╗░██╗░░░░░███████╗  ░░░░██╗  ██╗░░░░░███████╗██╗░░░██╗███████╗██╗░░░░░
        # ██╔══██╗██╔══██╗██║░░░░░██╔════╝  ░░░██╔╝  ██║░░░░░██╔════╝██║░░░██║██╔════╝██║░░░░░
        # ██████╔╝██║░░██║██║░░░░░█████╗░░  ░░██╔╝░  ██║░░░░░█████╗░░╚██╗░██╔╝█████╗░░██║░░░░░
        # ██╔══██╗██║░░██║██║░░░░░██╔══╝░░  ░██╔╝░░  ██║░░░░░██╔══╝░░░╚████╔╝░██╔══╝░░██║░░░░░
        # ██║░░██║╚█████╔╝███████╗███████╗  ██╔╝░░░  ███████╗███████╗░░╚██╔╝░░███████╗███████╗
        # ╚═╝░░╚═╝░╚════╝░╚══════╝╚══════╝  ╚═╝░░░░  ╚══════╝╚══════╝░░░╚═╝░░░╚══════╝╚══════╝

        # Check if level or roles are vaild
        # A set that filters valid levels depending on user's roles
        roleSet = [1]
        for d in roleCreationDict.keys():
            if d in roles:
                roleSet += roleCreationDict[d]

        roleSet = set(roleSet)

        # If roles are present, add base levels + 1 for extra levels for these special roles.
        if ("Nitro Booster" in roles) and lvl < 11:
            roleSet = roleSet.union(set(map(lambda x: x+1,roleSet.copy())))

        if ("Bean Friend" in roles) and lvl < 11:
            roleSet = roleSet.union(set(map(lambda x: x+1,roleSet.copy())))
          
        print (roleSet)

        if lvl not in roleSet:
            msg += f":warning: You cannot create a character of **{lvl}**! You do not have the correct role!\n"
        
        # Checks CP
        if lvl < 5:
            maxCP = 4
        else:
            maxCP = 10
        charDict['CP'] = f"0/{maxCP}"
        
        
        # ███╗░░░███╗░█████╗░░██████╗░██╗░█████╗░  ██╗████████╗███████╗███╗░░░███╗  ░░░░██╗  ████████╗██████╗░
        # ████╗░████║██╔══██╗██╔════╝░██║██╔══██╗  ██║╚══██╔══╝██╔════╝████╗░████║  ░░░██╔╝  ╚══██╔══╝██╔══██╗
        # ██╔████╔██║███████║██║░░██╗░██║██║░░╚═╝  ██║░░░██║░░░█████╗░░██╔████╔██║  ░░██╔╝░  ░░░██║░░░██████╔╝
        # ██║╚██╔╝██║██╔══██║██║░░╚██╗██║██║░░██╗  ██║░░░██║░░░██╔══╝░░██║╚██╔╝██║  ░██╔╝░░  ░░░██║░░░██╔═══╝░
        # ██║░╚═╝░██║██║░░██║╚██████╔╝██║╚█████╔╝  ██║░░░██║░░░███████╗██║░╚═╝░██║  ██╔╝░░░  ░░░██║░░░██║░░░░░
        # ╚═╝░░░░░╚═╝╚═╝░░╚═╝░╚═════╝░╚═╝░╚════╝░  ╚═╝░░░╚═╝░░░╚══════╝╚═╝░░░░░╚═╝  ╚═╝░░░░  ░░░╚═╝░░░╚═╝░░░░░
        # Magic Item / TP
        # Check if magic items exist, and calculates the TP cost of each magic item.
        magicItems = mItems.strip().split(',')
        allMagicItemsString = []

        # If magic items parameter isn't blank, check each magic item to see if valid, and check for duplicates.
        if lvl > 1 and magicItems != ['']:
            for m in magicItems:
                mRecord, charEmbed, charEmbedmsg = await callAPI(ctx, charEmbed, charEmbedmsg, 'mit',m) 
                if charEmbedmsg == "Fail":
                    return

                if mRecord in allMagicItemsString:
                    msg += ':warning: You cannot spend TP on two of the same magic item.\n'
                    break 
                if not mRecord:
                    msg += f':warning: **{m}** doesn\'t exist! Check to see if it\'s on the Magic Item Table and check your spelling.\n'
                    break
                else:
                    allMagicItemsString.append(mRecord)


            def calculateMagicItems(lvl):
                bankTP1 = 0
                bankTP2 = 0
                highestTier = 0
                magicItemsCurrent = []
                magicItemsBought = []

                # Calculates T1/T2 TP that a character should have and their tie level to tier limit
                if lvl > 1 and lvl < 6: 
                    bankTP1 = (lvl-1) * 2 
                    highestTier = 1
                elif lvl > 5:
                    bankTP1 = 8
                    bankTP2 = (lvl-5) * 4
                    highestTier = 2

                magicItemsTier2 = []
                isLeftoverT1 = False
                isLeftoverT2 = False
                buyT2 = False
                buyT1 = False

                for item in allMagicItemsString:
                    #  See if player isn't going over tier 2 or tier 1
                    if int(item['Tier']) > highestTier:
                        return ":warning: One or more of these magic items cannot be acquired at Level " + str(lvl), 0, 0
                        
                    # Split T2 and T1 items.
                    else:
                        costTP = int(item['TP'])
                        if int(item['Tier']) == 2:
                            magicItemsTier2.append(item)
                            continue

                        # Go through T1 Items and spend TP. Puts incomplete magic items as current item.
                        else:
                            buyT1 = True
                            bankTP1 = costTP - bankTP1
                            if bankTP1 > 0:
                              magicItemsCurrent.append(item)                       
                              magicItemsCurrent.append(f'{costTP - bankTP1}/{costTP}')
                              charDict['Current Item'] = f'{magicItemsCurrent[0]["Name"]} ({magicItemsCurrent[1]})'
                              isLeftoverT1= False
                            else:
                              bankTP1 = abs(bankTP1)
                              magicItemsBought.append(item)
                              isLeftoverT1 = True


                # Go through T2 items
                for item in magicItemsTier2:

                    # If there is an incomplete item from T1 TP, see if it can be completed with T2 TP
                    if magicItemsCurrent:
                        magicItemsCurrentItem = magicItemsCurrent[1].split('/')
                        bankTP2 = int(magicItemsCurrentItem[1]) - int(magicItemsCurrentItem[0]) - bankTP2
                        if bankTP2 > 0:
                            buyT2 = True
                            magicItemsCurrent[1] = f'{int(magicItemsCurrentItem[1]) - bankTP2}/{magicItemsCurrentItem[1]}'
                            charDict['Current Item'] = f'{magicItemsCurrent[0]["Name"]} ({magicItemsCurrent[1]})'
                            isLeftoverT2 = False
                        else:
                            bankTP2 = abs(bankTP2)
                            magicItemsBought.append(magicItemsCurrent[0])
                            magicItemsCurrent = []
                            charDict['Current Item'] = ""
                            isLeftoverT2 = True

                    # Spend T2 TP with T2 items
                    if bankTP2 > 0:
                        costTP = int(item['TP'])
                        bankTP2 = costTP - bankTP2
                        if bankTP2 > 0:
                          buyT2 = True
                          magicItemsCurrent.append(item)                       
                          magicItemsCurrent.append(f'{costTP - bankTP2}/{costTP}')
                          charDict['Current Item'] = f'{magicItemsCurrent[0]["Name"]} ({magicItemsCurrent[1]})'
                          isLeftoverT2 = False
                        else:
                          bankTP2 = abs(bankTP2)
                          magicItemsBought.append(item)
                          isLeftoverT2 = True

                
                if not isLeftoverT1 and buyT1:
                    bankTP1 = 0

                if not isLeftoverT2 and buyT2:
                    bankTP2 = 0

                return magicItemsBought, bankTP1, bankTP2


            magicItemsBought, bankTP1, bankTP2 = calculateMagicItems(lvl)
            if isinstance(magicItemsBought, str):
                msg += magicItemsBought
            elif magicItemsBought == list():
                pass
            else:
                charDict['Magic Items'] = ', '.join([str(string['Name']) for string in magicItemsBought])
        
        # Level 1 cannot buy magic items because they have 0 TP to spend.
        elif lvl > 1 and magicItems == ['']:
            if lvl > 1 and lvl < 6: 
                bankTP1 = (lvl-1) * 2 
            elif lvl > 5:
                bankTP1 = 8
                bankTP2 = (lvl-5) * 4
        elif lvl == 1 and magicItems != ['']:
            msg += '• You cannot purchase magic items at Level 1.\n'



        # ██████╗░███████╗░██╗░░░░░░░██╗░█████╗░██████╗░██████╗░  ██╗████████╗███████╗███╗░░░███╗░██████╗
        # ██╔══██╗██╔════╝░██║░░██╗░░██║██╔══██╗██╔══██╗██╔══██╗  ██║╚══██╔══╝██╔════╝████╗░████║██╔════╝
        # ██████╔╝█████╗░░░╚██╗████╗██╔╝███████║██████╔╝██║░░██║  ██║░░░██║░░░█████╗░░██╔████╔██║╚█████╗░
        # ██╔══██╗██╔══╝░░░░████╔═████║░██╔══██║██╔══██╗██║░░██║  ██║░░░██║░░░██╔══╝░░██║╚██╔╝██║░╚═══██╗
        # ██║░░██║███████╗░░╚██╔╝░╚██╔╝░██║░░██║██║░░██║██████╔╝  ██║░░░██║░░░███████╗██║░╚═╝░██║██████╔╝
        # ╚═╝░░╚═╝╚══════╝░░░╚═╝░░░╚═╝░░╚═╝░░╚═╝╚═╝░░╚═╝╚═════╝░  ╚═╝░░░╚═╝░░░╚══════╝╚═╝░░░░░╚═╝╚═════╝░
        # Reward Items

        rewardItems = consumes.strip().split(',')
        allRewardItemsString = []
        if lvl <= 3 and rewardItems != [''] and ('Nitro Booster' not in roles and 'Bean Friend' not in roles):
            msg += f"• Your role does not allow you to create a character with reward items. Please try again."
        elif rewardItems != ['']:
            for r in rewardItems:
                reRecord, charEmbed, charEmbedmsg = await callAPI(ctx, charEmbed, charEmbedmsg, 'rit',r) 
                if charEmbedmsg == "Fail":
                    return
                if not reRecord:
                    msg += f' {r} doesn\'t exist! Check to see if it\'s on the Reward Item Table and check your spelling.\n'
                    break
                else:
                    allRewardItemsString.append(reRecord)

            tier1CountMNC = 0
            tier1Count = 0
            tier2Count = 0
            rewardConsumables = []
            rewardMagics = []
            tier1Rewards = []

            if 'Good Noodle' in roles:
                tier1CountMNC = 1
            elif 'Elite Noodle' in roles:
                tier1CountMNC = 1
                tier1Count = 1
            elif 'True Noodle' in roles:
                tier1CountMNC = 1
                tier2Count = 1
            elif 'Ascended Noodle' in roles:
                tier1CountMNC = 1
                tier1Count = 1
                tier2Count = 1
            elif 'Immortal Noodle' in roles:
                tier1CountMNC = 1
                tier1Count = 2
                tier2Count = 1

            if 'Nitro Booster' in roles:
                tier1CountMNC += 1

            if 'Bean Friend' in roles:
                tier1CountMNC += 1

            startt1MNC = tier1CountMNC
            startt1 = tier1Count
            startt2 = tier2Count

            for item in allRewardItemsString:
                if int(item['Tier']) > 2:
                    msg += ":warning: One or more of these reward items cannot be acquired at Level " + str(lvl) + ".\n"
                    break

                if item['Minor/Major'] == 'Minor' and 'Consumable' not in item and tier1CountMNC > 0:
                    tier1CountMNC -= 1
                    rewardMagics.append(item)
                elif int(item['Tier']) == 2: 
                    tier2Count -= 1
                    if 'Consumable' not in item:
                      rewardMagics.append(item)
                    else:
                        rewardConsumables.append(item)
                elif int(item['Tier']) == 1:
                    tier1Rewards.append(item)
            for item in tier1Rewards:
                if tier1Count > 0 and tier2Count <= 0:
                    tier1Count -= 1
                else:
                    tier2Count -= 1

                if 'Consumable' not in item:
                    rewardMagics.append(item)
                else:
                    rewardConsumables.append(item)


            if tier1CountMNC < 0 or tier1Count < 0 or tier2Count < 0:
                msg += f":warning: You do not have the right roles for these reward items. You can only choose **{startt1MNC}** Tier 1 (Non-Consumable) item(s), **{startt1}** Tier 1 (or lower) item(s), and **{startt2}** Tier 2 (or lower) item(s).\n"
            else:
                for r in rewardConsumables:
                    if charDict['Consumables'] != "None":
                        charDict['Consumables'] += ', ' + r['Name']
                    else:
                        charDict['Consumables'] = r['Name']
                for r in rewardMagics:
                    if charDict['Magic Items'] != "None":
                        charDict['Magic Items'] += ', ' + r['Name']
                    else:
                        charDict['Magic Items'] = r['Name']
                      
        # ██████╗░░█████╗░░█████╗░███████╗░░░  ░█████╗░██╗░░░░░░█████╗░░██████╗░██████╗
        # ██╔══██╗██╔══██╗██╔══██╗██╔════╝░░░  ██╔══██╗██║░░░░░██╔══██╗██╔════╝██╔════╝
        # ██████╔╝███████║██║░░╚═╝█████╗░░░░░  ██║░░╚═╝██║░░░░░███████║╚█████╗░╚█████╗░
        # ██╔══██╗██╔══██║██║░░██╗██╔══╝░░██╗  ██║░░██╗██║░░░░░██╔══██║░╚═══██╗░╚═══██╗
        # ██║░░██║██║░░██║╚█████╔╝███████╗╚█║  ╚█████╔╝███████╗██║░░██║██████╔╝██████╔╝
        # ╚═╝░░╚═╝╚═╝░░╚═╝░╚════╝░╚══════╝░╚╝  ░╚════╝░╚══════╝╚═╝░░╚═╝╚═════╝░╚═════╝░
        # check race
        rRecord, charEmbed, charEmbedmsg = await callAPI(ctx, charEmbed, charEmbedmsg, 'races',race)
        if charEmbedmsg == "Fail":
            return
        if not rRecord:
            msg += f'• {race} isn\'t on the list or it is banned! Check #allowed-and-banned-content and check your spelling.\n'
        else:
            charDict['Race'] = rRecord['Name']

        
        # Check Character's class
        classStat = []
        cRecord = []
        totalLevel = 0
        mLevel = 0
        broke = []
        # If there's a /, character is creating a multiclass character
        if '/' in cclass:
            multiclassList = cclass.replace(' ', '').split('/')
            # Iterates through the multiclass list 
            
            print("MultList ", multiclassList)
            for m in multiclassList:
                # Separate level and class
                mLevel = re.search('\d+', m)
                if not mLevel:
                    msg += ":warning: You are missing the level for your multiclass class. Please check your format.\n"

                    break
                mLevel = mLevel.group()
                mClass, charEmbed, charEmbedmsg = await callAPI(ctx, charEmbed, charEmbedmsg,'classes',m[:len(m) - len(mLevel)])
                if not mClass:
                    cRecord = None
                    broke.append(m[:len(m) - len(mLevel)])

                # Check for class duplicates (ex. Paladin 1 / Paladin 2 = Paladin 3)
                classDupe = False
                
                if(cRecord or cRecord==list()):
                    for c in cRecord:
                        if c['Class'] == mClass:
                            c['Level'] = str(int(c['Level']) + int(mLevel))
                            classDupe = True                    
                            break

                    if not classDupe:
                        cRecord.append({'Class': mClass, 'Level':mLevel})
                    totalLevel += int(mLevel)

        else:
            singleClass, charEmbed, charEmbedmsg = await callAPI(ctx, charEmbed, charEmbedmsg, 'classes',cclass)
            if singleClass:
                cRecord.append({'Class':singleClass, 'Level':lvl, 'Subclass': 'None'})
            else:
                cRecord = None

        charDict['Class'] = ""
        print(len(broke))
        if not mLevel and '/' in cclass:
            pass
        elif len(broke)>0:
            msg += f':warning: **{broke}** isn\'t on the list or it is banned! Check #allowed-and-banned-content and check your spelling.\n'
        elif totalLevel != lvl and len(cRecord) > 1:
            msg += ':warning: Your classes do not add up to the total level. Please double-check your multiclasses.\n'
        else:
            cRecord = sorted(cRecord, key = lambda i: i['Level'], reverse=True) 

            # starting equipment
            def alphaEmbedCheck(r, u):
                sameMessage = False
                if charEmbedmsg.id == r.message.id:
                    sameMessage = True
                return sameMessage and ((r.emoji in alphaEmojis[:alphaIndex]) or (str(r.emoji) == '❌')) and u == author

            if 'Starting Equipment' in cRecord[0]['Class'] and msg == "":
                if charDict['Inventory'] == "None":
                    charDict['Inventory'] = {}
                startEquipmentLength = 0
                if not charEmbedmsg:
                    charEmbedmsg = await channel.send(embed=charEmbed)
                elif charEmbedmsg == "Fail":
                    msg += ":warning: You have either cancelled the command or a value was not found."
                else:
                    await charEmbedmsg.edit(embed=charEmbed)

                for item in cRecord[0]['Class']['Starting Equipment']:
                    seTotalString = ""
                    alphaIndex = 0
                    for seList in item:
                        seString = []
                        for elk, elv in seList.items():
                            if 'Pack' in elk:
                                seString.append(f"{elk} x1")
                            else:
                                seString.append(f"{elk} x{elv}")
                                
                        seTotalString += f"{alphaEmojis[alphaIndex]}: {', '.join(seString)}\n"
                        alphaIndex += 1

                    await charEmbedmsg.clear_reactions()
                    charEmbed.add_field(name=f"Starting Equipment: {startEquipmentLength+ 1} of {len(cRecord[0]['Class']['Starting Equipment'])}", value=seTotalString, inline=False)
                    await charEmbedmsg.edit(embed=charEmbed)
                    if len(item) > 1:
                        for num in range(0,alphaIndex): await charEmbedmsg.add_reaction(alphaEmojis[num])
                        await charEmbedmsg.add_reaction('❌')
                        try:
                            tReaction, tUser = await self.bot.wait_for("reaction_add", check=alphaEmbedCheck, timeout=60)
                        except asyncio.TimeoutError:
                            await charEmbedmsg.delete()
                            await channel.send(f'Character creation timed out! Try again using the same command:\n```yaml\n{commandPrefix}create "character name" level "race" "class" "background" STR DEX CON INT WIS CHA "magic item1, magic item2, [...]" "reward item1, reward item2, [...]"```')
                            self.bot.get_command('create').reset_cooldown(ctx)
                            return 
                        else:
                            if tReaction.emoji == '❌':
                                await charEmbedmsg.edit(embed=None, content=f"Character creation cancelled. Try again using the same command:\n```yaml\n{commandPrefix}create \"character name\" level \"race\" \"class\" \"background\" STR DEX CON INT WIS CHA \"magic item1, magic item2, [...]\" \"reward item1, reward item2, [...]\"```")
                                await charEmbedmsg.clear_reactions()
                                self.bot.get_command('create').reset_cooldown(ctx)
                                return 
                                
                        startEquipmentItem = item[alphaEmojis.index(tReaction.emoji)]
                    else:
                        startEquipmentItem = item[0]

                    await charEmbedmsg.clear_reactions()

                    seiString = ""
                    for seik, seiv in startEquipmentItem.items():
                        seiString += f"{seik} x{seiv}\n"
                        if "Pack" in seik:
                            seiString = f"{seik}:\n"
                            for pk, pv in seiv.items():
                                charDict['Inventory'][pk] = pv
                                seiString += f"+ {pk} x{pv}\n"

                    charEmbed.set_field_at(startEquipmentLength, name=f"Starting Equipment: {startEquipmentLength + 1} of {len(cRecord[0]['Class']['Starting Equipment'])}", value=seiString, inline=False)

                    for k,v in startEquipmentItem.items():
                        if '[' in k and ']' in k:
                            iType = k.split('[')
                            invCollection = db.shop
                            if 'Instrument' in iType[1]:
                                charInv = list(invCollection.find({"Type": {'$all': [re.compile(f".*{iType[1].replace(']','')}.*")]}}))
                            else:
                                charInv = list(invCollection.find({"Type": {'$all': [re.compile(f".*{iType[0]}.*"),re.compile(f".*{iType[1].replace(']','')}.*")]}}))

                            charInv = sorted(charInv, key = lambda i: i['Name']) 

                            typeEquipmentList = []
                            for i in range (0,int(v)):
                                charInvString = f"Please choose from the choices below for {iType[0]} {i+1}:\n"
                                alphaIndex = 0
                                for c in charInv:
                                    if 'Yklwa' not in c['Name'] and 'Light Repeating Crossbow' not in c['Name'] and 'Double-Bladed Scimitar' not in c['Name']:
                                        charInvString += f"{alphaEmojis[alphaIndex]}: {c['Name']}\n"
                                        alphaIndex += 1

                                charEmbed.set_field_at(startEquipmentLength, name=f"Starting Equipment: {startEquipmentLength+1} of {len(cRecord[0]['Class']['Starting Equipment'])}", value=charInvString, inline=False)
                                await charEmbedmsg.clear_reactions()
                                await charEmbedmsg.add_reaction('❌')
                                await charEmbedmsg.edit(embed=charEmbed)

                                try:
                                    tReaction, tUser = await self.bot.wait_for("reaction_add", check=alphaEmbedCheck, timeout=60)
                                except asyncio.TimeoutError:
                                    await charEmbedmsg.delete()
                                    await channel.send(f'Character creation timed out! Try again using the same command:\n```yaml\n{commandPrefix}create "character name" level "race" "class" "background" STR DEX CON INT WIS CHA "magic item1, magic item2, [...]" "reward item1, reward item2, [...]"```')
                                    self.bot.get_command('create').reset_cooldown(ctx)
                                    return 
                                else:
                                    if tReaction.emoji == '❌':
                                        await charEmbedmsg.edit(embed=None, content=f"Character creation cancelled. Try again using the same command:\n```yaml\n{commandPrefix}create \"character name\" level \"race\" \"class\" \"background\" STR DEX CON INT WIS CHA \"magic item1, magic item2, [...]\" \"reward item1, reward item2, [...]\"```")
                                        await charEmbedmsg.clear_reactions()
                                        self.bot.get_command('create').reset_cooldown(ctx)
                                        return 
                                typeEquipmentList.append(charInv[alphaEmojis.index(tReaction.emoji)]['Name'])
                                typeCount = collections.Counter(typeEquipmentList)
                                typeString = ""
                                for tk, tv in typeCount.items():
                                    typeString += f"{tk} x{tv}\n"
                                    charDict['Inventory'][tk] = tv

                            charEmbed.set_field_at(startEquipmentLength, name=f"Starting Equipment: {startEquipmentLength+1} of {len(cRecord[0]['Class']['Starting Equipment'])}", value=seiString.replace(f"{k} x{v}\n", typeString), inline=False)

                        elif 'Pack' not in k:
                            charDict['Inventory'][k] = v
                    startEquipmentLength += 1
                await charEmbedmsg.clear_reactions()
                charEmbed.clear_fields()

            # Subclass
            for m in cRecord:
                m['Subclass'] = 'None'
                if int(m['Level']) < lvl:
                    className = f'{m["Class"]["Name"]} {m["Level"]}'
                else:
                    className = f'{m["Class"]["Name"]}'

                if int(m['Class']['Subclass Level']) <= int(m['Level']) and msg == "":
                    subclassesList = m['Class']['Subclasses'].split(',')
                    subclass, charEmbedmsg = await characterCog.chooseSubclass(ctx, subclassesList, m['Class']['Name'], charEmbed, charEmbedmsg)
                    if not subclass:
                        return

                    m['Subclass'] = f'{className} ({subclass})' 
                    classStat.append(f'{className}-{subclass}')


                    if charDict['Class'] == "": 
                        charDict['Class'] = f'{className} ({subclass})'
                    else:
                        charDict['Class'] += f' / {className} ({subclass})'
                else:
                    classStat.append(className)
                    if charDict['Class'] == "": 
                        charDict['Class'] = className
                    else:
                        charDict['Class'] += f' / {className}'
        # check bg and gp
        bRecord, charEmbed, charEmbedmsg = await callAPI(ctx, charEmbed, charEmbedmsg, 'backgrounds',bg)

        def bgTopItemCheck(r, u):
            sameMessage = False
            if charEmbedmsg.id == r.message.id:
                sameMessage = True
            return ((r.emoji in alphaEmojis[:alphaIndexTop]) or (str(r.emoji) == '❌')) and u == author and sameMessage

        def bgItemCheck(r, u):
            sameMessage = False
            if charEmbedmsg.id == r.message.id:
                sameMessage = True
            return ((r.emoji in alphaEmojis[:alphaIndex]) or (str(r.emoji) == '❌')) and u == author and sameMessage


        if charEmbedmsg == "Fail":
            self.bot.get_command('create').reset_cooldown(ctx)
            return
        if not bRecord:
            msg += f':warning: **{bg}** isn\'t on the list or it is banned! Check #allowed-and-banned-content and check your spelling.\n'
        else:
            charDict['Background'] = bRecord['Name']

            # TODO: make function for inputing in inventory
            # Background items: goes through each background and give extra items for inventory.
            
            for e in bRecord['Equipment']:
                beTopChoiceList = []
                beTopChoiceKeys = []
                alphaIndexTop = 0
                beTopChoiceString = ""
                for ek, ev in e.items():
                    if type(ev) == dict:
                        beTopChoiceKeys.append(ek)
                        beTopChoiceList.append(ev)
                        beTopChoiceString += f"{alphaEmojis[alphaIndexTop]}: {ek}\n"
                        alphaIndexTop += 1
                    else:
                        if charDict['Inventory'] == "None":
                            charDict['Inventory'] = {ek : int(ev)}
                        else:
                            if ek not in charDict['Inventory']:
                                charDict['Inventory'][ek] = int(ev)
                            else:
                                charDict['Inventory'][ek] += int(ev)

                if len(beTopChoiceList) > 0:
                    # Lets user pick between top choices (ex. Game set or Musical Instrument. Then a followup choice.)
                    if len(beTopChoiceList) > 1:
                        charEmbed.add_field(name=f"Your {bRecord['Name']} background lets you choose one type.", value=beTopChoiceString, inline=False)
                        if not charEmbedmsg:
                            charEmbedmsg = await channel.send(embed=charEmbed)
                        else:
                            await charEmbedmsg.edit(embed=charEmbed)

                        await charEmbedmsg.add_reaction('❌')
                        try:
                            tReaction, tUser = await self.bot.wait_for("reaction_add", check=bgTopItemCheck , timeout=60)
                        except asyncio.TimeoutError:
                            await charEmbedmsg.delete()
                            await channel.send(f'Character creation cancelled. Try again using the same command:\n```yaml\n{commandPrefix}create "character name" level "race" "class" "background" STR DEX CON INT WIS CHA "magic item1, magic item2, [...]" "reward item1, reward item2, [...]"```')
                            self.bot.get_command('create').reset_cooldown(ctx)
                            return
                        else:
                            await charEmbedmsg.clear_reactions()
                            if tReaction.emoji == '❌':
                                await charEmbedmsg.edit(embed=None, content=f"Character creation cancelled. Try again using the same command:\n```yaml\n{commandPrefix}create \"character name\" level \"race\" \"class\" \"background\" STR DEX CON INT WIS CHA \"magic item1, magic item2, [...]\" \"reward item1, reward item2, [...]\"```")
                                await charEmbedmsg.clear_reactions()
                                self.bot.get_command('create').reset_cooldown(ctx)
                                return

                        beTopValues = beTopChoiceList[alphaEmojis.index(tReaction.emoji)]
                        beTopKey = beTopChoiceKeys[alphaEmojis.index(tReaction.emoji)]
                    elif len(beTopChoiceList) == 1:
                        beTopValues = beTopChoiceList[0]
                        beTopKey = beTopChoiceKeys[0]

                    beChoiceString = ""
                    alphaIndex = 0
                    beList = []

                    if 'Pack' in beTopKey:
                       for c in beTopValues:
                          if charDict['Inventory'] == "None":
                              charDict['Inventory'] = {c : 1}
                          else:
                              if c not in charDict['Inventory']:
                                  charDict['Inventory'][c] = 1
                              else:
                                  charDict['Inventory'][c] += 1
                    else:
                        for c in beTopValues:
                            beChoiceString += f"{alphaEmojis[alphaIndex]}: {c}\n"
                            beList.append(c)
                            alphaIndex += 1

                        charEmbed.add_field(name=f"Your {bRecord['Name']} background lets you choose one {beTopKey}.", value=beChoiceString, inline=False)
                        if not charEmbedmsg:
                            charEmbedmsg = await channel.send(embed=charEmbed)
                        else:
                            await charEmbedmsg.edit(embed=charEmbed)

                        await charEmbedmsg.add_reaction('❌')
                        try:
                            tReaction, tUser = await self.bot.wait_for("reaction_add", check=bgItemCheck , timeout=60)
                        except asyncio.TimeoutError:
                            await charEmbedmsg.delete()
                            await channel.send(f'Character creation cancelled. Try again using the same command:\n```yaml\n{commandPrefix}create "character name" level "race" "class" "background" STR DEX CON INT WIS CHA "magic item1, magic item2, [...]" "reward item1, reward item2, [...]"```')
                            self.bot.get_command('create').reset_cooldown(ctx)
                            return
                        else:
                            await charEmbedmsg.clear_reactions()
                            if tReaction.emoji == '❌':
                                await charEmbedmsg.edit(embed=None, content=f"Character creation cancelled. Try again using the same command:\n```yaml\n{commandPrefix}create \"character name\" level \"race\" \"class\" \"background\" STR DEX CON INT WIS CHA \"magic item1, magic item2, [...]\" \"reward item1, reward item2, [...]\"```")
                                await charEmbedmsg.clear_reactions()
                                self.bot.get_command('create').reset_cooldown(ctx)
                                return
                            beKey = beList[alphaEmojis.index(tReaction.emoji)]
                            if charDict['Inventory'] == "None":
                                charDict['Inventory'] = {beKey : 1}
                            else:
                                if beKey not in charDict['Inventory']:
                                    charDict['Inventory'][beKey] = 1
                                else:
                                    charDict['Inventory'][beKey] += 1

                    charEmbed.clear_fields()

            totalGP = 0
            if lvl > 1 and lvl < 6: 
                totalGP = (lvl-1) * 240
            if lvl > 5:
                totalGP = (lvl-6) * 960 + 1920

            charDict['GP'] = int(bRecord['GP']) + totalGP
        
        if not sStr.isdigit() or not sDex.isdigit() or not sCon.isdigit() or not sInt.isdigit() or not sWis.isdigit() or not sCha.isdigit():
            msg += ':warning: One or more of your stats are not numbers. Please check your spelling\n'

        # ░██████╗████████╗░█████╗░████████╗░██████╗░░░  ███████╗███████╗░█████╗░████████╗░██████╗
        # ██╔════╝╚══██╔══╝██╔══██╗╚══██╔══╝██╔════╝░░░  ██╔════╝██╔════╝██╔══██╗╚══██╔══╝██╔════╝
        # ╚█████╗░░░░██║░░░███████║░░░██║░░░╚█████╗░░░░  █████╗░░█████╗░░███████║░░░██║░░░╚█████╗░
        # ░╚═══██╗░░░██║░░░██╔══██║░░░██║░░░░╚═══██╗██╗  ██╔══╝░░██╔══╝░░██╔══██║░░░██║░░░░╚═══██╗
        # ██████╔╝░░░██║░░░██║░░██║░░░██║░░░██████╔╝╚█║  ██║░░░░░███████╗██║░░██║░░░██║░░░██████╔╝
        # ╚═════╝░░░░╚═╝░░░╚═╝░░╚═╝░░░╚═╝░░░╚═════╝░░╚╝  ╚═╝░░░░░╚══════╝╚═╝░░╚═╝░░░╚═╝░░░╚═════╝░
        # Stats - Point Buy
        elif msg == "":
            statsArray = [int(sStr), int(sDex), int(sCon), int(sInt), int(sWis), int(sCha)]
            statsArray, charEmbedmsg = await characterCog.pointBuy(ctx, statsArray, rRecord, charEmbed, charEmbedmsg)
            if not statsArray:
                return
            elif statsArray:
                totalPoints = 0
                for s in statsArray:
                    if (13-s) < 0:
                        totalPoints += ((s - 13) * 2) + 5
                    else:
                        totalPoints += (s - 8)

                if totalPoints != 27:
                    msg += f":warning: Your stats plus your race's modifers do not add up to 27 using point buy ({totalPoints}/27). Please check your point allocation.\n"

        #Stats - Feats
        if msg == "":
            featLevels = []
            featChoices = []
            featsChosen = []
            if rRecord['Name'] == 'Human (Variant)':
                featLevels.append('Human (Variant)')

            for c in cRecord:
                if int(c['Level']) > 3:
                    featLevels.append(4)
                if 'Fighter' in c['Class']['Name'] and int(c['Level']) > 5:
                    featLevels.append(6)
                if int(c['Level']) > 7:
                    featLevels.append(8)
                if 'Rogue' in c['Class']['Name'] and int(c['Level']) > 9:
                    featLevels.append(10)

            featsChosen, statsFeats, charEmbedmsg = await characterCog.chooseFeat(ctx, rRecord['Name'], charDict['Class'], cRecord, featLevels, charEmbed, charEmbedmsg, charDict, "")

            if not featsChosen and not statsFeats and not charEmbedmsg:
                self.bot.get_command('create').reset_cooldown(ctx)
                return

            if featsChosen:
                charDict['Feats'] = featsChosen 
            else: 
                charDict['Feats'] = "None" 
            
            for key, value in statsFeats.items():
                charDict[key] = value

            #HP
            hpRecords = []
            for cc in cRecord:
                # Wizards get 2 free spells per wizard level
                if cc['Class']['Name'] == "Wizard":
                    charDict['Free Spells'] = [6,0,0,0,0,0,0,0,0]
                    fsIndex = 0
                    for i in range (2, int(cc['Level']) + 1 ):
                        if i % 2 != 0:
                            fsIndex += 1
                        charDict['Free Spells'][fsIndex] += 2

                hpRecords.append({'Level':cc['Level'], 'Subclass': cc['Subclass'], 'Name': cc['Class']['Name'], 'Hit Die Max': cc['Class']['Hit Die Max'], 'Hit Die Average':cc['Class']['Hit Die Average']})

            if hpRecords:
                charDict['HP'] = await characterCog.calcHP(ctx,hpRecords,charDict,lvl)

            # Multiclass Requirements
            if '/' in cclass and len(cRecord) > 1:
                for m in cRecord:
                    reqFufillList = []
                    statReq = m['Class']['Multiclass'].split(' ')
                    if m['Class']['Multiclass'] != 'None':
                        if '/' not in m['Class']['Multiclass'] and '+' not in m['Class']['Multiclass']:
                            if int(charDict[statReq[0]]) < int(statReq[1]):
                                msg += f":warning: In order to multiclass to or from **{m['Class']['Name']}** you need at least **{m['Class']['Multiclass']}**. Your character only has **{statReq[0]} {charDict[statReq[0]]}**\n"

                        elif '/' in m['Class']['Multiclass']:
                            statReq[0] = statReq[0].split('/')
                            reqFufill = False
                            for s in statReq[0]:
                                if int(charDict[s]) >= int(statReq[1]):
                                  reqFufill = True
                                else:
                                  reqFufillList.append(f"{s} {charDict[s]}")
                            if not reqFufill:
                                msg += f":warning: In order to multiclass to or from **{m['Class']['Name']}** you need at least **{m['Class']['Multiclass']}**. Your character only has **{' and '.join(reqFufillList)}**\n"

                        elif '+' in m['Class']['Multiclass']:
                            statReq[0] = statReq[0].split('+')
                            reqFufill = True
                            for s in statReq[0]:
                                if int(charDict[s]) < int(statReq[1]):
                                  reqFufill = False
                                  reqFufillList.append(f"{s} {charDict[s]}")
                            if not reqFufill:
                                msg += f":warning: In order to multiclass to or from **{m['Class']['Name']}** you need at least **{m['Class']['Multiclass']}**. Your character only has **{' and '.join(reqFufillList)}**\n"

        if msg:
            if charEmbedmsg and charEmbedmsg != "Fail":
                await charEmbedmsg.delete()
            elif charEmbedmsg == "Fail":
                msg = ":warning: You have either cancelled the command or a value was not found."
            await ctx.channel.send(f'There were error(s) when creating your character:\n{msg}')

            self.bot.get_command('create').reset_cooldown(ctx)
            return 

        charEmbed.clear_fields()    
        charEmbed.title = f"{charDict['Name']} (Lv {charDict['Level']}): {charDict['CP']} CP"
        charEmbed.description = f"**Race**: {charDict['Race']}\n**Class**: {charDict['Class']}\n**Background**: {charDict['Background']}\n**Max HP**: {charDict['HP']}\n**gp**: {charDict['GP']} "

        charEmbed.add_field(name='Current TP Item', value=charDict['Current Item'], inline=True)
        if  bankTP1 > 0:
            charDict['T1 TP'] = bankTP1
            charEmbed.add_field(name=':warning: Unused T1 TP', value=charDict['T1 TP'], inline=True)
        if  bankTP2 > 0:
            charDict['T2 TP'] = bankTP2
            charEmbed.add_field(name=':warning: Unused T2 TP', value=charDict['T2 TP'], inline=True)
        if charDict['Magic Items'] != 'None':
            charEmbed.add_field(name='Magic Items', value=charDict['Magic Items'], inline=False)
        if charDict['Consumables'] != 'None':
            charEmbed.add_field(name='Consumables', value=charDict['Consumables'], inline=False)
        charEmbed.add_field(name='Feats', value=charDict['Feats'], inline=True)
        charEmbed.add_field(name='Stats', value=f"**STR**: {charDict['STR']} **DEX**: {charDict['DEX']} **CON**: {charDict['CON']} **INT**: {charDict['INT']} **WIS**: {charDict['WIS']} **CHA**: {charDict['CHA']}", inline=False)

        if 'Wizard' in charDict['Class']:
            charEmbed.add_field(name='Spellbook (Wizard)', value=f"At 1st level, you have a spellbook containing six 1st-level Wizard spells of your choice (+2 free spells for each wizard level). Please use the `{commandPrefix}shop copy` command." , inline=False)

            fsString = ""
            fsIndex = 0
            for el in charDict['Free Spells']:
                if el > 0:
                    fsString += f"Level {fsIndex+1}: {el} free spells\n"
                fsIndex += 1

            if fsString:
                charEmbed.add_field(name='Free Spellbook Copies Available', value=fsString , inline=False)

        
        charDictInvString = ""
        if charDict['Inventory'] != "None":
            for k,v in charDict['Inventory'].items():
                charDictInvString += f"• {k} x{v}\n"
            charEmbed.add_field(name='Starting Equipment', value=charDictInvString, inline=False)
            charEmbed.set_footer(text= charEmbed.Empty)


        def charCreateCheck(r, u):
            sameMessage = False
            if charEmbedmsg.id == r.message.id:
                sameMessage = True
            return sameMessage and ((str(r.emoji) == '✅') or (str(r.emoji) == '❌')) and u == author


        if not charEmbedmsg:
            charEmbedmsg = await channel.send(embed=charEmbed, content="**Double-check** your character information.\nIf this is correct, please react with one of the following:\n✅ to finish creating your character.\n❌ to cancel. ")
        else:
            await charEmbedmsg.edit(embed=charEmbed, content="**Double-check** your character information.\nIf this is correct please react with one of the following:\n✅ to finish creating your character.\n❌ to cancel. ")

        await charEmbedmsg.add_reaction('✅')
        await charEmbedmsg.add_reaction('❌')
        try:
            tReaction, tUser = await self.bot.wait_for("reaction_add", check=charCreateCheck , timeout=60)
        except asyncio.TimeoutError:
            await charEmbedmsg.delete()
            await channel.send(f'Character creation cancelled. Try again using the same command:\n```yaml\n{commandPrefix}create "character name" level "race" "class" "background" STR DEX CON INT WIS CHA "magic item1, magic item2, [...]" "reward item1, reward item2, [...]"```')
            self.bot.get_command('create').reset_cooldown(ctx)
            return
        else:
            await charEmbedmsg.clear_reactions()
            if tReaction.emoji == '❌':
                await charEmbedmsg.edit(embed=None, content=f"Character creation cancelled. Try again using the same command:\n```yaml\n{commandPrefix}create \"character name\" level \"race\" \"class\" \"background\" STR DEX CON INT WIS CHA \"magic item1, magic item2, [...]\" \"reward item1, reward item2, [...]\"```")
                await charEmbedmsg.clear_reactions()
                self.bot.get_command('create').reset_cooldown(ctx)
                return

        statsCollection = db.stats
        statsRecord  = statsCollection.find_one({'Life': 1})

        for c in classStat:
            char = c.split('-')
            if char[0] in statsRecord['Class']:
                statsRecord['Class'][char[0]]['Count'] += 1
            else:
                statsRecord['Class'][char[0]] = {'Count': 1}

            if len(char) > 1:
                if char[1] in statsRecord['Class'][char[0]]:
                    statsRecord['Class'][char[0]][char[1]] += 1
                else:
                    statsRecord['Class'][char[0]][char[1]] = 1

            if charDict['Race'] in statsRecord['Race']:
                statsRecord['Race'][charDict['Race']] += 1
            else:
                statsRecord['Race'][charDict['Race']] = 1

            if charDict['Background'] in statsRecord['Background']:
                statsRecord['Background'][charDict['Background']] += 1
            else:
                statsRecord['Background'][charDict['Background']] = 1

        try:
            playersCollection.insert_one(charDict)
            statsCollection.update_one({'Life':1}, {"$set": statsRecord}, upsert=True)
        except Exception as e:
            print ('MONGO ERROR: ' + str(e))
            charEmbedmsg = await channel.send(embed=None, content="Uh oh, looks like something went wrong. Please try creating your character again.")
        else:
            print('Success')
            if charEmbedmsg:
                await charEmbedmsg.clear_reactions()
                await charEmbedmsg.edit(embed=charEmbed, content =f"Congratulations! :tada: You have created ***{charDict['Name']}***!")
            else: 
                charEmbedmsg = await channel.send(embed=charEmbed, content=f"Congratulations! You have created your ***{charDict['Name']}***!")

        self.bot.get_command('create').reset_cooldown(ctx)

    #TODO: stats for respec
    @commands.cooldown(1, float('inf'), type=commands.BucketType.user)
    @commands.command(aliases=['rs'])
    async def respec(self,ctx, name, newname, race, cclass, bg, sStr, sDex, sCon, sInt, sWis, sCha, mItems="", consumes=""):
        characterCog = self.bot.get_cog('Character')
        author = ctx.author
        guild = ctx.guild
        channel = ctx.channel
        charEmbed = discord.Embed ()
        charEmbed.set_author(name=ctx.author.display_name, icon_url=ctx.author.avatar_url)
        charEmbed.set_footer(text= "React with ❌ to cancel.\nPlease react with a choice even if no reactions appear.")

        statNames = ['STR','DEX','CON','INT','WIS','CHA']
        roles = [r.name for r in ctx.author.roles]
        charDict, charEmbedmsg = await checkForChar(ctx, name, charEmbed)

        if not charDict:
            return

        # Reset  values here
        charNoneKeyList = ['Magic Items', 'Consumables', 'Inventory', 'Current Item']

        charRemoveKeyList = ['Image', 'Spellbook', 'T3 TP', 'T4 TP', 'Attuned', 'Spellbook', 'Guild', 'Guild Rank', 'Grouped']

        for c in charNoneKeyList:
            charDict[c] = "None"

        for c in charRemoveKeyList:
            if c in charDict:
                del charDict[c]
            
        charID = charDict['_id']
        charDict['STR'] = int(sStr)
        charDict['DEX'] = int(sDex)
        charDict['CON'] = int(sCon)
        charDict['INT'] = int(sInt)
        charDict['WIS'] = int(sWis)
        charDict['CHA'] = int(sCha)
        charDict['GP'] = 0

        charDict['Max Stats'] = {'STR':20, 'DEX':20, 'CON':20, 'INT':20, 'WIS':20, 'CHA':20}

        lvl = charDict['Level']
        msg = ""
        bankTP1 = 0
        bankTP2 = 0

        if 'Death' in charDict.keys():
            await channel.send(content=f"You cannot respec a dead character. Use the following command to decide their fate:\n```yaml\n$death \"{charRecords['Name']}\"```")
            return

        # level check
        if lvl > 4:
            msg += "• Your character's level is way too high to respec.\n"
            await ctx.channel.send(msg)
            self.bot.get_command('respec').reset_cooldown(ctx) 
            return
            
        # new name should be less then 50 chars
        if len(newname) > 64:
            msg += ":warning: Your character's new name is too long! The limit is 64 characters.\n"

        # Prevents name, level, race, class, background from being blank. Resets infinite cooldown and prompts
        if not newname:
            await channel.send(content=":warning: The new name of your character cannot be blank! Please try again.\n")
            self.bot.get_command('respec').reset_cooldown(ctx)
            return
        
        playersCollection = db.players
        userRecords = list(playersCollection.find({"User ID": str(author.id), "Name": {"$regex": newname, '$options': 'i' }}))

        if userRecords != list() and newname != name:
            msg += f":warning: You already have a character by the name ***{newname}***. Please use a different name.\n"

        oldName = charDict['Name']
        charDict['Name'] = newname

        if not race:
            await channel.send(content=":warning: The race of your character cannot be blank! Please try again.\n")
            self.bot.get_command('respec').reset_cooldown(ctx)
            return

        if not cclass:
            await channel.send(content=":warning: The class of your character cannot be blank! Please try again.\n")
            self.bot.get_command('respec').reset_cooldown(ctx)
            return
        
        if not bg:
            await channel.send(content=":warning: The background of your character cannot be blank! Please try again.\n")
            self.bot.get_command('respec').reset_cooldown(ctx)
            return

        # ███╗░░░███╗░█████╗░░██████╗░██╗░█████╗░  ██╗████████╗███████╗███╗░░░███╗  ░░░░██╗  ████████╗██████╗░
        # ████╗░████║██╔══██╗██╔════╝░██║██╔══██╗  ██║╚══██╔══╝██╔════╝████╗░████║  ░░░██╔╝  ╚══██╔══╝██╔══██╗
        # ██╔████╔██║███████║██║░░██╗░██║██║░░╚═╝  ██║░░░██║░░░█████╗░░██╔████╔██║  ░░██╔╝░  ░░░██║░░░██████╔╝
        # ██║╚██╔╝██║██╔══██║██║░░╚██╗██║██║░░██╗  ██║░░░██║░░░██╔══╝░░██║╚██╔╝██║  ░██╔╝░░  ░░░██║░░░██╔═══╝░
        # ██║░╚═╝░██║██║░░██║╚██████╔╝██║╚█████╔╝  ██║░░░██║░░░███████╗██║░╚═╝░██║  ██╔╝░░░  ░░░██║░░░██║░░░░░
        # ╚═╝░░░░░╚═╝╚═╝░░╚═╝░╚═════╝░╚═╝░╚════╝░  ╚═╝░░░╚═╝░░░╚══════╝╚═╝░░░░░╚═╝  ╚═╝░░░░  ░░░╚═╝░░░╚═╝░░░░░
        # Magic Item / TP
        # Check if magic items exist, and calculates the TP cost of each magic item.

        magicItems = mItems.strip().split(',')
        allMagicItemsString = []

        # Because we are respeccing we are also adding extra TP based on CP.
        # no needed to to bankTP2 now because limit is lvl 4 to respec
        extraCp = float(charDict['CP'].split('/')[0])

        if extraCp > float(charDict['CP'].split('/')[1]):
            msg += f":warning: {oldName} needs to level up before they can respec into a new character!"

        extraTP = extraCp / 2 

        # If magic items parameter isn't blank, check each magic item to see if valid, and check for duplicates.
        if magicItems != ['']:
            for m in magicItems:
                mRecord, charEmbed, charEmbedmsg = await callAPI(ctx, charEmbed, charEmbedmsg, 'mit',m) 
                if charEmbedmsg == "Fail":
                    return

                if mRecord in allMagicItemsString:
                    msg += ':warning: You cannot spend TP on two of the same magic item!\n'
                    break 
                if not mRecord:
                    msg += f':warning: **{m}** doesn\'t exist! Check to see if it\'s on the Magic Item Table and check your spelling.\n'
                    break
                else:
                    allMagicItemsString.append(mRecord)

            def calculateMagicItems(lvl):
                bankTP1 = 0
                bankTP2 = 0
                highestTier = 0
                magicItemsCurrent = []
                magicItemsBought = []
                

                # Calculates T1/T2 TP that a character should have and their tie level to tier limit
                if lvl > 1 and lvl < 6: 
                    bankTP1 = (lvl-1) * 2 
                    highestTier = 1
                elif lvl > 5:
                    bankTP1 = 8
                    bankTP2 = (lvl-5) * 4
                    highestTier = 2

                bankTP1 += extraTP

                magicItemsTier2 = []
                isLeftoverT1 = False
                isLeftoverT2 = False
                buyT2 = False
                buyT1 = False

                for item in allMagicItemsString:
                    #  See if player isn't going over tier 2 or tier 1
                    if int(item['Tier']) > highestTier:
                        return ":warning: One or more of these magic items cannot be acquired at Level " + str(lvl), 0, 0
                        
                    # Split T2 and T1 items.
                    else:
                        costTP = int(item['TP'])
                        if int(item['Tier']) == 2:
                            magicItemsTier2.append(item)
                            continue

                        # Go through T1 Items and spend TP. Puts incomplete magic items as current item.
                        else:
                            buyT1 = True
                            bankTP1 = costTP - bankTP1
                            if bankTP1 > 0:
                              magicItemsCurrent.append(item)                       
                              magicItemsCurrent.append(f'{costTP - bankTP1}/{costTP}')
                              charDict['Current Item'] = f'{magicItemsCurrent[0]["Name"]} ({magicItemsCurrent[1]})'
                              isLeftoverT1= False
                            else:
                              bankTP1 = abs(bankTP1)
                              magicItemsBought.append(item)
                              isLeftoverT1 = True


                # Go through T2 items
                for item in magicItemsTier2:

                    # If there is an incomplete item from T1 TP, see if it can be completed with T2 TP
                    if magicItemsCurrent:
                        magicItemsCurrentItem = magicItemsCurrent[1].split('/')
                        bankTP2 = int(magicItemsCurrentItem[1]) - int(magicItemsCurrentItem[0]) - bankTP2
                        if bankTP2 > 0:
                            buyT2 = True
                            magicItemsCurrent[1] = f'{int(magicItemsCurrentItem[1]) - bankTP2}/{magicItemsCurrentItem[1]}'
                            charDict['Current Item'] = f'{magicItemsCurrent[0]["Name"]} ({magicItemsCurrent[1]})'
                            isLeftoverT2 = False
                        else:
                            bankTP2 = abs(bankTP2)
                            magicItemsBought.append(magicItemsCurrent[0])
                            magicItemsCurrent = []
                            charDict['Current Item'] = ""
                            isLeftoverT2 = True

                    # Spend T2 TP with T2 items
                    if bankTP2 > 0:
                        costTP = int(item['TP'])
                        bankTP2 = costTP - bankTP2
                        if bankTP2 > 0:
                          buyT2 = True
                          magicItemsCurrent.append(item)                       
                          magicItemsCurrent.append(f'{costTP - bankTP2}/{costTP}')
                          charDict['Current Item'] = f'{magicItemsCurrent[0]["Name"]} ({magicItemsCurrent[1]})'
                          isLeftoverT2 = False
                        else:
                          bankTP2 = abs(bankTP2)
                          magicItemsBought.append(item)
                          isLeftoverT2 = True

                
                if not isLeftoverT1 and buyT1:
                    bankTP1 = 0

                if not isLeftoverT2 and buyT2:
                    bankTP2 = 0

                return magicItemsBought, bankTP1, bankTP2


            magicItemsBought, bankTP1, bankTP2 = calculateMagicItems(lvl)
            if isinstance(magicItemsBought, str):
                msg += magicItemsBought
            elif magicItemsBought == list():
                pass
            else:
                charDict['Magic Items'] = ', '.join([str(string['Name']) for string in magicItemsBought])

        
        elif magicItems == ['']:
            if lvl > 1 and lvl < 6: 
                bankTP1 = (lvl-1) * 2 
            elif lvl > 5:
                bankTP1 = 8
                bankTP2 = (lvl-5) * 4
            bankTP1 += extraTP
        # Level 1 cannot buy magic items because they have 0 TP to spend, unless they respecced with TP
        elif lvl == 1 and magicItems != [''] and extraCP == 0:
            msg += '• You cannot purchase magic items at Level 1 with 0 CP.\n'

        # ██████╗░███████╗░██╗░░░░░░░██╗░█████╗░██████╗░██████╗░  ██╗████████╗███████╗███╗░░░███╗░██████╗
        # ██╔══██╗██╔════╝░██║░░██╗░░██║██╔══██╗██╔══██╗██╔══██╗  ██║╚══██╔══╝██╔════╝████╗░████║██╔════╝
        # ██████╔╝█████╗░░░╚██╗████╗██╔╝███████║██████╔╝██║░░██║  ██║░░░██║░░░█████╗░░██╔████╔██║╚█████╗░
        # ██╔══██╗██╔══╝░░░░████╔═████║░██╔══██║██╔══██╗██║░░██║  ██║░░░██║░░░██╔══╝░░██║╚██╔╝██║░╚═══██╗
        # ██║░░██║███████╗░░╚██╔╝░╚██╔╝░██║░░██║██║░░██║██████╔╝  ██║░░░██║░░░███████╗██║░╚═╝░██║██████╔╝
        # ╚═╝░░╚═╝╚══════╝░░░╚═╝░░░╚═╝░░╚═╝░░╚═╝╚═╝░░╚═╝╚═════╝░  ╚═╝░░░╚═╝░░░╚══════╝╚═╝░░░░░╚═╝╚═════╝░
        # Reward Items

        rewardItems = consumes.strip().split(',')
        allRewardItemsString = []
        if rewardItems != [''] and ('Nitro Booster' not in roles and 'Bean Friend' not in roles):
            msg += f"• Your role does not allow you to create a character with reward items. Please try again."
        elif rewardItems != ['']:
            for r in rewardItems:
                reRecord, charEmbed, charEmbedmsg = await callAPI(ctx, charEmbed, charEmbedmsg, 'rit',r) 
                if charEmbedmsg == "Fail":
                    return
                if not reRecord:
                    msg += f' {r} doesn\'t exist! Check to see if it\'s on the Reward Item Table and check your spelling.\n'
                    break
                else:
                    allRewardItemsString.append(reRecord)

            tier1CountMNC = 0
            tier1Count = 0
            tier2Count = 0
            rewardConsumables = []
            rewardMagics = []
            tier1Rewards = []

            if 'Nitro Booster' in roles:
                tier1CountMNC += 1

            if 'Bean Friend' in roles:
                tier1CountMNC += 1

            startt1MNC = tier1CountMNC
            startt1 = tier1Count
            startt2 = tier2Count

            for item in allRewardItemsString:
                if int(item['Tier']) > 2:
                    msg += ":warning: One or more of these reward items cannot be acquired at Level " + str(lvl) + ".\n"
                    break

                if item['Minor/Major'] == 'Minor' and 'Consumable' not in item and tier1CountMNC > 0:
                    tier1CountMNC -= 1
                    rewardMagics.append(item)
                elif int(item['Tier']) == 2: 
                    tier2Count -= 1
                    if 'Consumable' not in item:
                      rewardMagics.append(item)
                    else:
                        rewardConsumables.append(item)
                elif int(item['Tier']) == 1:
                    tier1Rewards.append(item)
            for item in tier1Rewards:
                if tier1Count > 0 and tier2Count <= 0:
                    tier1Count -= 1
                else:
                    tier2Count -= 1

                if 'Consumable' not in item:
                    rewardMagics.append(item)
                else:
                    rewardConsumables.append(item)


            if tier1CountMNC < 0 or tier1Count < 0 or tier2Count < 0:
                msg += f":warning: You do not have the right roles for these reward items. You can only choose **{startt1MNC}** Tier 1 (Non-Consumable) item(s), **{startt1}** Tier 1 (or lower) item(s), and **{startt2}** Tier 2 (or lower) item(s).\n"
            else:
                for r in rewardConsumables:
                    if charDict['Consumables'] != "None":
                        charDict['Consumables'] += ', ' + r['Name']
                    else:
                        charDict['Consumables'] = r['Name']
                for r in rewardMagics:
                    if charDict['Magic Items'] != "None":
                        charDict['Magic Items'] += ', ' + r['Name']
                    else:
                        charDict['Magic Items'] = r['Name']


        # ██████╗░░█████╗░░█████╗░███████╗░░░  ░█████╗░██╗░░░░░░█████╗░░██████╗░██████╗
        # ██╔══██╗██╔══██╗██╔══██╗██╔════╝░░░  ██╔══██╗██║░░░░░██╔══██╗██╔════╝██╔════╝
        # ██████╔╝███████║██║░░╚═╝█████╗░░░░░  ██║░░╚═╝██║░░░░░███████║╚█████╗░╚█████╗░
        # ██╔══██╗██╔══██║██║░░██╗██╔══╝░░██╗  ██║░░██╗██║░░░░░██╔══██║░╚═══██╗░╚═══██╗
        # ██║░░██║██║░░██║╚█████╔╝███████╗╚█║  ╚█████╔╝███████╗██║░░██║██████╔╝██████╔╝
        # ╚═╝░░╚═╝╚═╝░░╚═╝░╚════╝░╚══════╝░╚╝  ░╚════╝░╚══════╝╚═╝░░╚═╝╚═════╝░╚═════╝░
        # check race
        rRecord, charEmbed, charEmbedmsg = await callAPI(ctx, charEmbed, charEmbedmsg,'races',race)
        if not rRecord:
            msg += f':warning: **{race}** isn\'t on the list or it is banned! Check #allowed-and-banned-content and check your spelling.\n'
        else:
            charDict['Race'] = rRecord['Name']
        
        # Check Character's class
        classStat = []
        cRecord = []
        totalLevel = 0
        mLevel = 0
        broke = []
        # If there's a /, character is creating a multiclass character
        if '/' in cclass:
            multiclassList = cclass.replace(' ', '').split('/')
            # Iterates through the multiclass list 
            
            print("MultList ", multiclassList)
            for m in multiclassList:
                # Separate level and class
                mLevel = re.search('\d+', m)
                if not mLevel:
                    msg += ":warning: You are missing the level for your multiclass class. Please check your format.\n"

                    break
                mLevel = mLevel.group()
                mClass, charEmbed, charEmbedmsg = await callAPI(ctx, charEmbed, charEmbedmsg,'classes',m[:len(m) - len(mLevel)])
                if not mClass:
                    cRecord = None
                    broke.append(m[:len(m) - len(mLevel)])

                # Check for class duplicates (ex. Paladin 1 / Paladin 2 = Paladin 3)
                classDupe = False
                
                if(cRecord or cRecord==list()):
                    for c in cRecord:
                        if c['Class'] == mClass:
                            c['Level'] = str(int(c['Level']) + int(mLevel))
                            classDupe = True                    
                            break

                    if not classDupe:
                        cRecord.append({'Class': mClass, 'Level':mLevel})
                    totalLevel += int(mLevel)

        else:
            singleClass, charEmbed, charEmbedmsg = await callAPI(ctx, charEmbed, charEmbedmsg, 'classes',cclass)
            if singleClass:
                cRecord.append({'Class':singleClass, 'Level':lvl, 'Subclass': 'None'})
            else:
                cRecord = None

        charDict['Class'] = ""
        print(len(broke))
        if not mLevel and '/' in cclass:
            pass
        elif len(broke)>0:
            msg += f':warning: **{broke}** isn\'t on the list or it is banned! Check #allowed-and-banned-content and check your spelling.\n'
        elif totalLevel != lvl and len(cRecord) > 1:
            msg += ':warning: Your classes do not add up to the total level. Please double-check your multiclasses.\n'
        else:
            cRecord = sorted(cRecord, key = lambda i: i['Level'], reverse=True) 

            # starting equipment
            def alphaEmbedCheck(r, u):
                sameMessage = False
                if charEmbedmsg.id == r.message.id:
                    sameMessage = True
                return sameMessage and ((r.emoji in alphaEmojis[:alphaIndex]) or (str(r.emoji) == '❌')) and u == author

            if 'Starting Equipment' in cRecord[0]['Class'] and msg == "":
                if charDict['Inventory'] == "None":
                    charDict['Inventory'] = {}
                startEquipmentLength = 0
                if not charEmbedmsg:
                    charEmbedmsg = await channel.send(embed=charEmbed)
                elif charEmbedmsg == "Fail":
                    msg += ":warning: You have either cancelled the command or a value was not found."
                else:
                    await charEmbedmsg.edit(embed=charEmbed)

                for item in cRecord[0]['Class']['Starting Equipment']:
                    seTotalString = ""
                    alphaIndex = 0
                    for seList in item:
                        seString = []
                        for elk, elv in seList.items():
                            if 'Pack' in elk:
                                seString.append(f"{elk} x1")
                            else:
                                seString.append(f"{elk} x{elv}")
                                
                        seTotalString += f"{alphaEmojis[alphaIndex]}: {', '.join(seString)}\n"
                        alphaIndex += 1

                    await charEmbedmsg.clear_reactions()
                    charEmbed.add_field(name=f"Starting Equipment: {startEquipmentLength+ 1} of {len(cRecord[0]['Class']['Starting Equipment'])}", value=seTotalString, inline=False)
                    await charEmbedmsg.edit(embed=charEmbed)
                    if len(item) > 1:
                        for num in range(0,alphaIndex): await charEmbedmsg.add_reaction(alphaEmojis[num])
                        await charEmbedmsg.add_reaction('❌')
                        try:
                            tReaction, tUser = await self.bot.wait_for("reaction_add", check=alphaEmbedCheck, timeout=60)
                        except asyncio.TimeoutError:
                            await charEmbedmsg.delete()
                            await channel.send(f'Character creation timed out! Try again using the same command:\n```yaml\n{commandPrefix}create "character name" level "race" "class" "background" STR DEX CON INT WIS CHA "magic item1, magic item2, [...]" "reward item1, reward item2, [...]"```')
                            self.bot.get_command('respec').reset_cooldown(ctx)
                            return 
                        else:
                            if tReaction.emoji == '❌':
                                await charEmbedmsg.edit(embed=None, content=f"Character creation cancelled. Try again using the same command:\n```yaml\n{commandPrefix}create \"character name\" level \"race\" \"class\" \"background\" STR DEX CON INT WIS CHA \"magic item1, magic item2, [...]\" \"reward item1, reward item2, [...]\"```")
                                await charEmbedmsg.clear_reactions()
                                self.bot.get_command('respec').reset_cooldown(ctx)
                                return 
                                
                        startEquipmentItem = item[alphaEmojis.index(tReaction.emoji)]
                    else:
                        startEquipmentItem = item[0]

                    await charEmbedmsg.clear_reactions()

                    seiString = ""
                    for seik, seiv in startEquipmentItem.items():
                        seiString += f"{seik} x{seiv}\n"
                        if "Pack" in seik:
                            seiString = f"{seik}:\n"
                            for pk, pv in seiv.items():
                                charDict['Inventory'][pk] = pv
                                seiString += f"+ {pk} x{pv}\n"

                    charEmbed.set_field_at(startEquipmentLength, name=f"Starting Equipment: {startEquipmentLength + 1} of {len(cRecord[0]['Class']['Starting Equipment'])}", value=seiString, inline=False)

                    for k,v in startEquipmentItem.items():
                        if '[' in k and ']' in k:
                            iType = k.split('[')
                            invCollection = db.shop
                            if 'Instrument' in iType[1]:
                                charInv = list(invCollection.find({"Type": {'$all': [re.compile(f".*{iType[1].replace(']','')}.*")]}}))
                            else:
                                charInv = list(invCollection.find({"Type": {'$all': [re.compile(f".*{iType[0]}.*"),re.compile(f".*{iType[1].replace(']','')}.*")]}}))

                            charInv = sorted(charInv, key = lambda i: i['Name']) 

                            typeEquipmentList = []
                            for i in range (0,int(v)):
                                charInvString = f"Please choose from the choices below for {iType[0]} {i+1}:\n"
                                alphaIndex = 0
                                for c in charInv:
                                    if 'Yklwa' not in c['Name'] and 'Light Repeating Crossbow' not in c['Name'] and 'Double-Bladed Scimitar' not in c['Name']:
                                        charInvString += f"{alphaEmojis[alphaIndex]}: {c['Name']}\n"
                                        alphaIndex += 1

                                charEmbed.set_field_at(startEquipmentLength, name=f"Starting Equipment: {startEquipmentLength+1} of {len(cRecord[0]['Class']['Starting Equipment'])}", value=charInvString, inline=False)
                                await charEmbedmsg.clear_reactions()
                                await charEmbedmsg.add_reaction('❌')
                                await charEmbedmsg.edit(embed=charEmbed)

                                try:
                                    tReaction, tUser = await self.bot.wait_for("reaction_add", check=alphaEmbedCheck, timeout=60)
                                except asyncio.TimeoutError:
                                    await charEmbedmsg.delete()
                                    await channel.send(f'Character creation timed out! Try again using the same command:\n```yaml\n{commandPrefix}create "character name" level "race" "class" "background" STR DEX CON INT WIS CHA "magic item1, magic item2, [...]" "reward item1, reward item2, [...]"```')
                                    self.bot.get_command('respec').reset_cooldown(ctx)
                                    return 
                                else:
                                    if tReaction.emoji == '❌':
                                        await charEmbedmsg.edit(embed=None, content=f"Character creation cancelled. Try again using the same command:\n```yaml\n{commandPrefix}create \"character name\" level \"race\" \"class\" \"background\" STR DEX CON INT WIS CHA \"magic item1, magic item2, [...]\" \"reward item1, reward item2, [...]\"```")
                                        await charEmbedmsg.clear_reactions()
                                        self.bot.get_command('respec').reset_cooldown(ctx)
                                        return 
                                typeEquipmentList.append(charInv[alphaEmojis.index(tReaction.emoji)]['Name'])
                                typeCount = collections.Counter(typeEquipmentList)
                                typeString = ""
                                for tk, tv in typeCount.items():
                                    typeString += f"{tk} x{tv}\n"
                                    charDict['Inventory'][tk] = tv

                            charEmbed.set_field_at(startEquipmentLength, name=f"Starting Equipment: {startEquipmentLength+1} of {len(cRecord[0]['Class']['Starting Equipment'])}", value=seiString.replace(f"{k} x{v}\n", typeString), inline=False)

                        elif 'Pack' not in k:
                            charDict['Inventory'][k] = v
                    startEquipmentLength += 1
                await charEmbedmsg.clear_reactions()
                charEmbed.clear_fields()

            # Subclass
            for m in cRecord:
                m['Subclass'] = 'None'
                if int(m['Level']) < lvl:
                    className = f'{m["Class"]["Name"]} {m["Level"]}'
                else:
                    className = f'{m["Class"]["Name"]}'

                if int(m['Class']['Subclass Level']) <= int(m['Level']) and msg == "":
                    subclassesList = m['Class']['Subclasses'].split(',')
                    subclass, charEmbedmsg = await characterCog.chooseSubclass(ctx, subclassesList, m['Class']['Name'], charEmbed, charEmbedmsg)
                    if not subclass:
                        return

                    m['Subclass'] = f'{className} ({subclass})' 
                    classStat.append(f'{className}-{subclass}')


                    if charDict['Class'] == "": 
                        charDict['Class'] = f'{className} ({subclass})'
                    else:
                        charDict['Class'] += f' / {className} ({subclass})'
                else:
                    classStat.append(className)
                    if charDict['Class'] == "": 
                        charDict['Class'] = className
                    else:
                        charDict['Class'] += f' / {className}'

        bRecord, charEmbed, charEmbedmsg = await callAPI(ctx, charEmbed, charEmbedmsg, 'backgrounds',bg)
        if charEmbedmsg == "Fail":
            return
        if not bRecord:
            msg += f':warning: **{bg}** isn\'t on the list or it is banned! Check #allowed-and-banned-content and check your spelling.\n'
        else:
            charDict['Background'] = bRecord['Name']
            totalGP = 0
            if lvl > 1 and lvl < 6: 
                totalGP = (lvl-1) * 240
            if lvl > 5:
                totalGP = (lvl-6) * 960 + 1920

            totalGP += extraCp * 60
            charDict['GP'] = int(bRecord['GP']) + totalGP

        if not sStr.isdigit() or not sDex.isdigit() or not sCon.isdigit() or not sInt.isdigit() or not sWis.isdigit() or not sCha.isdigit():
            msg += ':warning: One or more of your stats are not numbers. Please check your spelling\n'        

        # ░██████╗████████╗░█████╗░████████╗░██████╗░░░  ███████╗███████╗░█████╗░████████╗░██████╗
        # ██╔════╝╚══██╔══╝██╔══██╗╚══██╔══╝██╔════╝░░░  ██╔════╝██╔════╝██╔══██╗╚══██╔══╝██╔════╝
        # ╚█████╗░░░░██║░░░███████║░░░██║░░░╚█████╗░░░░  █████╗░░█████╗░░███████║░░░██║░░░╚█████╗░
        # ░╚═══██╗░░░██║░░░██╔══██║░░░██║░░░░╚═══██╗██╗  ██╔══╝░░██╔══╝░░██╔══██║░░░██║░░░░╚═══██╗
        # ██████╔╝░░░██║░░░██║░░██║░░░██║░░░██████╔╝╚█║  ██║░░░░░███████╗██║░░██║░░░██║░░░██████╔╝
        # ╚═════╝░░░░╚═╝░░░╚═╝░░╚═╝░░░╚═╝░░░╚═════╝░░╚╝  ╚═╝░░░░░╚══════╝╚═╝░░╚═╝░░░╚═╝░░░╚═════╝░
        # Stats - Point Buy
        elif msg == "":
            statsArray = [int(sStr), int(sDex), int(sCon), int(sInt), int(sWis), int(sCha)]
            statsArray, charEmbedmsg = await characterCog.pointBuy(ctx, statsArray, rRecord, charEmbed, charEmbedmsg)
            if not statsArray:
                return
            elif statsArray:
                totalPoints = 0
                for s in statsArray:
                    if (13-s) < 0:
                        totalPoints += ((s - 13) * 2) + 5
                    else:
                        totalPoints += (s - 8)

                if totalPoints != 27:
                    msg += f":warning: Your stats plus your race's modifers do not add up to 27 using point buy ({totalPoints}/27). Please check your point allocation.\n"


        #Stats - Feats
        if msg == "":
            featLevels = []
            featChoices = []
            featsChosen = []
            if rRecord['Name'] == 'Human (Variant)':
                featLevels.append('Human (Variant)')

            for c in cRecord:
                if int(c['Level']) > 3:
                    featLevels.append(4)
                if 'Fighter' in c['Class']['Name'] and int(c['Level']) > 5:
                    featLevels.append(6)
                if int(c['Level']) > 7:
                    featLevels.append(8)
                if 'Rogue' in c['Class']['Name'] and int(c['Level']) > 9:
                    featLevels.append(10)

            featsChosen, statsFeats, charEmbedmsg = await characterCog.chooseFeat(ctx, rRecord['Name'], charDict['Class'], cRecord, featLevels, charEmbed, charEmbedmsg, charDict, "")

            if not featsChosen and not statsFeats and not charEmbedmsg:
                return

            if featsChosen:
                charDict['Feats'] = featsChosen 
            else: 
                charDict['Feats'] = "None" 
            
            for key, value in statsFeats.items():
                charDict[key] = value


            #HP
            hpRecords = []
            for cc in cRecord:
                # Wizards get 2 free spells per wizard level
                if cc['Class']['Name'] == "Wizard":
                    charDict['Free Spells'] = [6,0,0,0,0,0,0,0,0]
                    fsIndex = 0
                    for i in range (2, int(cc['Level']) + 1 ):
                        if i % 2 != 0:
                            fsIndex += 1
                        charDict['Free Spells'][fsIndex] += 2

                hpRecords.append({'Level':cc['Level'], 'Subclass': cc['Subclass'], 'Name': cc['Class']['Name'], 'Hit Die Max': cc['Class']['Hit Die Max'], 'Hit Die Average':cc['Class']['Hit Die Average']})

            if hpRecords:
                charDict['HP'] = await characterCog.calcHP(ctx,hpRecords,charDict,lvl)

            # Multiclass Requirements
            if '/' in cclass and len(cRecord) > 1:
                for m in cRecord:
                    reqFufillList = []
                    statReq = m['Class']['Multiclass'].split(' ')
                    if m['Class']['Multiclass'] != 'None':
                        if '/' not in m['Class']['Multiclass'] and '+' not in m['Class']['Multiclass']:
                            if int(charDict[statReq[0]]) < int(statReq[1]):
                                msg += f":warning: In order to multiclass to or from **{m['Class']['Name']}** you need at least **{m['Class']['Multiclass']}**. Your character only has **{statReq[0]} {charDict[statReq[0]]}**\n"

                        elif '/' in m['Class']['Multiclass']:
                            statReq[0] = statReq[0].split('/')
                            reqFufill = False
                            for s in statReq[0]:
                                if int(charDict[s]) >= int(statReq[1]):
                                  reqFufill = True
                                else:
                                  reqFufillList.append(f"{s} {charDict[s]}")
                            if not reqFufill:
                                msg += f":warning: In order to multiclass to or from **{m['Class']['Name']}** you need at least **{m['Class']['Multiclass']}**. Your character only has **{' and '.join(reqFufillList)}**\n"

                        elif '+' in m['Class']['Multiclass']:
                            statReq[0] = statReq[0].split('+')
                            reqFufill = True
                            for s in statReq[0]:
                                if int(charDict[s]) < int(statReq[1]):
                                  reqFufill = False
                                  reqFufillList.append(f"{s} {charDict[s]}")
                            if not reqFufill:
                                msg += f":warning: In order to multiclass to or from **{m['Class']['Name']}** you need at least **{m['Class']['Multiclass']}**. Your character only has **{' and '.join(reqFufillList)}**\n"


        if msg:
            if charEmbedmsg and charEmbedmsg != "Fail":
                await charEmbedmsg.delete()
            elif charEmbedmsg == "Fail":
                msg = ":warning: You have either cancelled the command or a value was not found."
            await ctx.channel.send(f'There were error(s) when creating your character:\n{msg}')

            self.bot.get_command('respec').reset_cooldown(ctx)
            return 

        charEmbed.clear_fields()    
        charEmbed.title = f"{charDict['Name']} (Lv {charDict['Level']}): {charDict['CP']} CP"
        charEmbed.description = f"**Race**: {charDict['Race']}\n**Class**: {charDict['Class']}\n**Background**: {charDict['Background']}\n**Max HP**: {charDict['HP']}\n**gp**: {charDict['GP']} "

        charEmbed.add_field(name='Current TP Item', value=charDict['Current Item'], inline=True)
        if  bankTP1 > 0:
            charDict['T1 TP'] = bankTP1
            charEmbed.add_field(name=':warning: Unused T1 TP', value=charDict['T1 TP'], inline=True)
        if  bankTP2 > 0:
            charDict['T2 TP'] = bankTP2
            charEmbed.add_field(name=':warning: Unused T2 TP', value=charDict['T2 TP'], inline=True)
        if charDict['Magic Items'] != 'None':
            charEmbed.add_field(name='Magic Items', value=charDict['Magic Items'], inline=False)
        if charDict['Consumables'] != 'None':
            charEmbed.add_field(name='Consumables', value=charDict['Consumables'], inline=False)
        charEmbed.add_field(name='Feats', value=charDict['Feats'], inline=True)
        charEmbed.add_field(name='Stats', value=f"**STR**: {charDict['STR']} **DEX**: {charDict['DEX']} **CON**: {charDict['CON']} **INT**: {charDict['INT']} **WIS**: {charDict['WIS']} **CHA**: {charDict['CHA']}", inline=False)

        if 'Wizard' in charDict['Class']:
            charEmbed.add_field(name='Spellbook (Wizard)', value=f"At 1st level, you have a spellbook containing six 1st-level Wizard spells of your choice (+2 free spells for each wizard level). Please use the `{commandPrefix}shop copy` command. **{charDict['Free Spells']} Free Spells Available**", inline=False)

            fsString = ""
            fsIndex = 0
            for el in charDict['Free Spells']:
                if el > 0:
                    fsString += f"Level {fsIndex+1}: {el} free spells\n"
                fsIndex += 1

            if fsString:
                charEmbed.add_field(name='Free Spellbook Copies Available', value=fsString , inline=False)

        charDictInvString = ""
        if charDict['Inventory'] != "None":
            for k,v in charDict['Inventory'].items():
                charDictInvString += f"• {k} x{v}\n"
            charEmbed.add_field(name='Starting Equipment', value=charDictInvString, inline=False)
            charEmbed.set_footer(text= charEmbed.Empty)

        def charCreateCheck(r, u):
            sameMessage = False
            if charEmbedmsg.id == r.message.id:
                sameMessage = True
            return sameMessage and ((str(r.emoji) == '✅') or (str(r.emoji) == '❌')) and u == author

        if not charEmbedmsg:
            charEmbedmsg = await channel.send(embed=charEmbed, content="**Double-check** your character information.\nIf this is correct, please react with one of the following:\n✅ to finish creating your character.\n❌ to cancel. ")
        else:
            await charEmbedmsg.edit(embed=charEmbed, content="**Double-check** your character information.\nIf this is correct please react with one of the following:\n✅ to finish creating your character.\n❌ to cancel. ")

        await charEmbedmsg.add_reaction('✅')
        await charEmbedmsg.add_reaction('❌')
        try:
            tReaction, tUser = await self.bot.wait_for("reaction_add", check=charCreateCheck , timeout=60)
        except asyncio.TimeoutError:
            await charEmbedmsg.delete()
            await channel.send(f'Character respec cancelled. Use the following command to try again:\n```yaml\n{commandPrefix}respec "character name" "new character name" level "race" "class" "background" STR DEX CON INT WIS CHA```')
            self.bot.get_command('respec').reset_cooldown(ctx)
            return
        else:
            await charEmbedmsg.clear_reactions()
            if tReaction.emoji == '❌':
                await charEmbedmsg.edit(embed=None, content=f"Character respec cancelled. Try again using the same command:\n```yaml\n{commandPrefix}respec \"character name\" \"new character name\" level \"race\" \"class\" \"background\" STR DEX CON INT WIS CHA```")
                await charEmbedmsg.clear_reactions()
                self.bot.get_command('respec').reset_cooldown(ctx)
                return

        #TODO Stats for respec?

        try:
            # Extra to unset
            charRemoveKeyList = {'Image':1, 'Spellbook':1, 'T3 TP':1, 'T4 TP':1, 'Attuned':1, 'Spellbook':1, 'Guild':1, 'Guild Rank':1, 'Grouped':1}
            playersCollection.update_one({'_id': charID}, {"$set": charDict, "$unset": charRemoveKeyList }, upsert=True)
        except Exception as e:
            print ('MONGO ERROR: ' + str(e))
            charEmbedmsg = await channel.send(embed=None, content="Uh oh, looks like something went wrong. Please try creating your character again.")
        else:
            print('Success')
            if charEmbedmsg:
                await charEmbedmsg.clear_reactions()
                await charEmbedmsg.edit(embed=charEmbed, content =f"Congratulations! You have respecced your character!")
            else: 
                charEmbedmsg = await channel.send(embed=charEmbed, content=f"Congratulations! You have respecced your character!")

        self.bot.get_command('respec').reset_cooldown(ctx)

    @commands.cooldown(1, float('inf'), type=commands.BucketType.user)
    @commands.command()
    async def retire(self,ctx, char):
        channel = ctx.channel
        author = ctx.author
        guild = ctx.guild
        charEmbed = discord.Embed()
        charEmbedmsg = None

        charDict, charEmbedmsg = await checkForChar(ctx, char, charEmbed)

        def retireEmbedCheck(r, u):
            sameMessage = False
            if charEmbedmsg.id == r.message.id:
                sameMessage = True
            return sameMessage and ((str(r.emoji) == '✅') or (str(r.emoji) == '❌')) and u == author
        if charDict:
            charID = charDict['_id']

            charEmbed.title = f"Are you sure you want to retire {charDict['Name']}?"
            charEmbed.description = "✅: Yes\n\n❌: Cancel"
            if not charEmbedmsg:
                charEmbedmsg = await channel.send(embed=charEmbed)
            else:
                await charEmbedmsg.edit(embed=charEmbed)

            await charEmbedmsg.add_reaction('✅')
            await charEmbedmsg.add_reaction('❌')
            try:
                tReaction, tUser = await self.bot.wait_for("reaction_add", check=retireEmbedCheck , timeout=60)
            except asyncio.TimeoutError:
                await charEmbedmsg.delete()
                await channel.send(f'Retire cancelled. Try again using the same command:\n```yaml\n{commandPrefix}retire "character name"```')
                self.bot.get_command('retire').reset_cooldown(ctx)
                return
            else:
                await charEmbedmsg.clear_reactions()
                if tReaction.emoji == '❌':
                    await charEmbedmsg.edit(embed=None, content=f'Retire cancelled. Try again using the same command:\n```yaml\n{commandPrefix}retire "character name"```')
                    await charEmbedmsg.clear_reactions()
                    self.bot.get_command('retire').reset_cooldown(ctx)
                    return
                elif tReaction.emoji == '✅':
                    charEmbed.clear_fields()
                    try:
                        playersCollection = db.players
                        deadCollection = db.dead
                        usersCollection = db.users
                        deadCollection.insert_one(charDict)

                        usersRecord = list(usersCollection.find({"User ID": charDict['User ID']}))[0]
                        if 'Games' not in usersRecord:
                            usersRecord['Games'] = charDict['Games']
                        else:
                            usersRecord['Games'] += charDict['Games']

                        usersCollection.update_one({'User ID': charDict['User ID']}, {"$set": {'Games': usersRecord['Games']}}, upsert=True)
                        playersCollection.delete_one({'_id': charID})
                    except Exception as e:
                        print ('MONGO ERROR: ' + str(e))
                        charEmbedmsg = await channel.send(embed=None, content="Uh oh, looks like something went wrong. Please try retiring your character again.")
                    else:
                        print('Success')
                        if charEmbedmsg:
                            await charEmbedmsg.clear_reactions()
                            await charEmbedmsg.edit(embed=None, content =f"Congratulations! You have retired ***{charDict['Name']}***. ")
                        else: 
                            charEmbedmsg = await channel.send(embed=None, content=f"Congratulations! You have retired ***{charDict['Name']}***.")

        self.bot.get_command('retire').reset_cooldown(ctx)

    @commands.cooldown(1, float('inf'), type=commands.BucketType.user)
    @commands.command()
    async def death (self,ctx, char):
        channel = ctx.channel
        author = ctx.author
        guild = ctx.guild
        charEmbed = discord.Embed()
        charEmbedmsg = None
        charDict, charEmbedmsg = await checkForChar(ctx, char, charEmbed)

        def retireEmbedCheck(r, u):
            sameMessage = False
            if charEmbedmsg.id == r.message.id:
                sameMessage = True
            return sameMessage and ((str(r.emoji) == '✅') or (str(r.emoji) == '❌')) and u == author

        def deathEmbedCheck(r, u):
            sameMessage = False
            if charEmbedmsg.id == r.message.id:
                sameMessage = True
            return sameMessage and ((str(r.emoji) == '1️⃣') or (str(r.emoji) == '2️⃣') or (charDict['GP'] >= gpNeeded and str(r.emoji) == '3️⃣') or (str(r.emoji) == '❌')) and u == author

        if charDict:
            if 'Death' not in charDict:
                await channel.send("Your character is not dead. You cannot use this command.")
                self.bot.get_command('death').reset_cooldown(ctx)
                return
            
            charID = charDict['_id']
            charLevel = charDict['Level']
            if charLevel < 5:
                gpNeeded = 250
                tierNum = 1
            elif charLevel < 11:
                gpNeeded = 500
                tierNum = 2
            elif charLevel < 17:
                gpNeeded = 750
                tierNum = 3
            elif charLevel < 21:
                gpNeeded = 1000
                tierNum = 4

            charEmbed.title = f"Character Death - {charDict['Name']}"
            charEmbed.set_footer(text= "React with ❌ to cancel.\nPlease react with a choice even if no reactions appear.")

            if charDict['GP'] < gpNeeded:
                charEmbed.description = f"Please choose between these three options for {charDict['Name']}:\n\n1️⃣: Death - Retires your character.\n2️⃣: Survival - Forfeit rewards and survive.\n3️⃣: ~~Revival~~ - You currently have {charDict['GP']} gp but need {gpNeeded} gp to be revived."
            else:
                charEmbed.description = f"Please choose between these three options for {charDict['Name']}:\n\n1️⃣: Death - Retires your character.\n2️⃣: Survival - Forfeit rewards and survive.\n3️⃣: Revival - Revives your character for {gpNeeded} gp."
            if not charEmbedmsg:
                charEmbedmsg = await channel.send(embed=charEmbed)
            else:
                await charEmbedmsg.edit(embed=charEmbed)

            await charEmbedmsg.add_reaction('1️⃣')
            await charEmbedmsg.add_reaction('2️⃣')
            if charDict['GP'] >= gpNeeded:
                await charEmbedmsg.add_reaction('3️⃣')
            await charEmbedmsg.add_reaction('❌')
            try:
                tReaction, tUser = await self.bot.wait_for("reaction_add", check=deathEmbedCheck , timeout=60)
            except asyncio.TimeoutError:
                await charEmbedmsg.delete()
                await channel.send(f'Death cancelled. Try again using the same command:\n```yaml\n{commandPrefix}death```')
                self.bot.get_command('death').reset_cooldown(ctx)
                return
            else:
                await charEmbedmsg.clear_reactions()
                if tReaction.emoji == '❌':
                    await charEmbedmsg.edit(embed=None, content=f"Death cancelled. Try again using the same command:\n```yaml\n{commandPrefix}death```")
                    await charEmbedmsg.clear_reactions()
                    self.bot.get_command('death').reset_cooldown(ctx)

                    return
                elif tReaction.emoji == '1️⃣':
                    charEmbed.title = f"Are you sure you want to retire {charDict['Name']}?"
                    charEmbed.description = "✅: Yes\n\n❌: Cancel"
                    charEmbed.set_footer(text=charEmbed.Empty)
                    await charEmbedmsg.edit(embed=charEmbed)
                    await charEmbedmsg.add_reaction('✅')
                    await charEmbedmsg.add_reaction('❌')
                    try:
                        tReaction, tUser = await self.bot.wait_for("reaction_add", check=retireEmbedCheck , timeout=60)
                    except asyncio.TimeoutError:
                        await charEmbedmsg.delete()
                        await channel.send(f'Death cancelled. Try again using the same command:\n```yaml\n{commandPrefix}death```')
                        self.bot.get_command('death').reset_cooldown(ctx)
                        return
                    else:
                        await charEmbedmsg.clear_reactions()
                        if tReaction.emoji == '❌':
                            await charEmbedmsg.edit(embed=None, content=f"Death cancelled. Try again using the same command:\n```yaml\n{commandPrefix}death```")
                            await charEmbedmsg.clear_reactions()
                            self.bot.get_command('death').reset_cooldown(ctx)
                            return
                        elif tReaction.emoji == '✅':
                            charEmbed.clear_fields()
                            try:
                                playersCollection = db.players
                                deadCollection = db.dead
                                deadCollection.insert_one(charDict)
                                playersCollection.delete_one({'_id': charID})
                                usersRecord = list(collection.find({"User ID": charDict['User ID']}))[0]

                                if 'Games' not in usersRecord:
                                    usersRecord['Games'] = 1
                                else:
                                    usersRecord['Games'] += 1

                                usersCollection.update_one({'User ID': charDict['User ID']}, {"$set": {'Games': usersRecord['Games']}}, upsert=True)
                                pass
                            except Exception as e:
                                print ('MONGO ERROR: ' + str(e))
                                charEmbedmsg = await channel.send(embed=None, content="Uh oh, looks like something went wrong. Please try retiring your character again.")
                            else:
                                print('Success')
                                if charEmbedmsg:
                                    await charEmbedmsg.clear_reactions()
                                    await charEmbedmsg.edit(embed=None, content ="Congratulations! You have retired your character.")

                                else: 
                                    charEmbedmsg = await channel.send(embed=None, content="Congratulations! You have retired your character.")
                    
                elif tReaction.emoji == '2️⃣' or tReaction.emoji == '3️⃣':
                    deathDict = eval(charDict['Death'])
                    charEmbed.clear_fields()
                    charDict['Death'] = ''
                    data = {
                        'Consumables': deathDict['Consumables'],
                        'Games': charDict['Games'] + 1
                    }
                    surviveString = f"Congratulations! ***{charDict['Name']}*** has survived and has forfeited their rewards."

                    if tReaction.emoji == '3️⃣':
                        cpSplit= charDict['CP'].split('/')
                        leftCP = (float(deathDict['CP']) + float(cpSplit[0])) 
                        totalCP = f'{leftCP}/{float(cpSplit[1])}'
                        data['CP'] = totalCP
                        if f"T{tierNum} TP" in charDict:
                            data[f"T{tierNum} TP"] = charDict[f"T{tierNum} TP"] + float(deathDict[f"T{tierNum} TP"])
                        else:
                            data[f"T{tierNum} TP"] = float(deathDict[f"T{tierNum} TP"])
                        data['GP'] = charDict["GP"] + deathDict["GP"] - gpNeeded
                        data['Magic Items'] = deathDict['Magic Items']

                        surviveString = f"Congratulations! ***{charDict['Name']}*** has been revived and has kept their rewards!"

                    try:
                        playersCollection = db.players
                        playersCollection.update_one({'_id': charID}, {"$set": data, "$unset": {"Death":1}})
                        usersRecord = list(collection.find({"User ID": charDict['User ID']}))[0]

                        if 'Games' not in usersRecord:
                            usersRecord['Games'] = 1
                        else:
                            usersRecord['Games'] += 1

                        usersCollection.update_one({'User ID': charDict['User ID']}, {"$set": {'Games': usersRecord['Games']}}, upsert=True)
                    except Exception as e:
                        print ('MONGO ERROR: ' + str(e))
                        charEmbedmsg = await channel.send(embed=None, content="Uh oh, looks like something went wrong. Please try creating your character again.")
                    else:
                        print("Success")
                        if charEmbedmsg:
                            await charEmbedmsg.clear_reactions()
                            await charEmbedmsg.edit(embed=None, content= surviveString)
                        else: 
                            charEmbedmsg = await channel.send(embed=None, content=surviveString)
        self.bot.get_command('death').reset_cooldown(ctx)


    @commands.cooldown(1, 5, type=commands.BucketType.member)
    @commands.command(aliases=['bag','inv'])
    async def inventory(self,ctx, char):
        channel = ctx.channel
        author = ctx.author
        guild = ctx.guild
        roleColors = {r.name:r.colour for r in guild.roles}
        charEmbed = discord.Embed()
        charEmbedmsg = None

        def userCheck(r,u):
            sameMessage = False
            if charEmbedmsg.id == r.message.id:
                sameMessage = True
            return sameMessage and u == ctx.author and (r.emoji == left or r.emoji == right)

        statusEmoji = ""
        charDict, charEmbedmsg = await checkForChar(ctx, char, charEmbed)
        if charDict:
            footer = f"To view your character's info, type the following command: `{commandPrefix}info {charDict['Name']}`"
            charLevel = charDict['Level']
            if charLevel < 5:
                role = 1
                charEmbed.colour = (roleColors['Junior Friend'])
            elif charLevel < 11:
                role = 2
                charEmbed.colour = (roleColors['Journeyfriend'])
            elif charLevel < 17:
                role = 3
                charEmbed.colour = (roleColors['Elite Friend'])
            elif charLevel < 21:
                role = 4
                charEmbed.colour = (roleColors['True Friend'])

            # Show Spellbook in inventory
            if 'Spellbook' in charDict:
                sPages = 1
                sPageStops = [0]
                spellBookString = ""
                for s in charDict['Spellbook']:
                    spellBookString += f"• {s['Name']} ({s['School']})\n" 
                    if len(spellBookString) > (768 * sPages):
                        sPageStops.append(len(spellBookString))
                        sPages += 1

                sPageStops.append(len(spellBookString))

                if sPages > 1:
                    for p in range(len(sPageStops)-1):
                        charEmbed.add_field(name=f'Spellbook- p. {p+1}', value=spellBookString[sPageStops[p]:sPageStops[p+1]], inline=False)
                else:
                    charEmbed.add_field(name='Spellbook', value=spellBookString, inline=False)

            if 'Ritual Book' in charDict:
                ritualBookString = ""
                for s in charDict['Ritual Book']:
                    ritualBookString += f"• {s['Name']} ({s['School']})\n" 
                charEmbed.add_field(name='Ritual Book', value=ritualBookString, inline=False)

    
            # Show Consumables in inventory.
            cPages = 1
            cPageStops = [0]

            consumesString = ""
            consumesCount = collections.Counter(charDict['Consumables'].split(', '))
            for k, v in consumesCount.items():
                if v == 1:
                    consumesString += f"• {k}\n"
                else:
                    consumesString += f"• {k} x{v}\n"

                if len(consumesString) > (768 * cPages):
                    cPageStops.append(len(consumesString))
                    cPages += 1
            
            cPageStops.append(len(consumesString))

            if cPages > 1:
                for p in range(len(cPageStops)-1):
                    charEmbed.add_field(name=f'Consumables - p. {p+1}', value=consumesString[cPageStops[p]:cPageStops[p+1]], inline=False)
            else:
                charEmbed.add_field(name='Consumables', value=consumesString, inline=False)

            # Show Magic items in inventory.
            mPages = 1
            mPageStops = [0]

            miString = ""
            miArray = collections.Counter(charDict['Magic Items'].split(', '))

            for m,v in miArray.items():
                if v == 1:
                    miString += f"• {m}\n"
                else:
                    miString += f"• {m} x{v}\n"

                if len(miString) > (768 * mPages):
                    mPageStops.append(len(miString))
                    mPages += 1

            mPageStops.append(len(miString))
            if mPages > 1:
                for p in range(len(mPageStops)-1):
                    charEmbed.add_field(name=f'Magic Items - p. {p+1}', value=miString[mPageStops[p]:mPageStops[p+1]], inline=False)
            else:
                charEmbed.add_field(name='Magic Items', value=miString, inline=False)


            charDictAuthor = guild.get_member(int(charDict['User ID']))
            charEmbed.title = f"{charDict['Name']} (Lv {charLevel}): Inventory"
            charEmbed.set_author(name=charDictAuthor, icon_url=charDictAuthor.avatar_url)
            if charDict['Inventory'] != 'None':
                typeDict = {}
                invCollection = db.shop
                namingDict = {}
                searchList = []
                keys = charDict['Inventory'].keys()
                for dbEntry in keys:
                    searchTerm = dbEntry
                    if(searchTerm.startswith("Silvered ")):
                        searchTerm=searchTerm.replace("Silvered ", "", 1)
                    if(searchTerm.startswith("Adamantine ")):
                        searchTerm= searchTerm.replace("Adamantine ", "", 1)
                    if(searchTerm in namingDict):
                        namingDict[searchTerm].append(dbEntry)
                    else:
                        namingDict[searchTerm] = [dbEntry]
                    searchList.append(searchTerm)
                print(namingDict)
                charInv = list(invCollection.find({"Name": {'$in': searchList}}))
                for i in charInv:
                    iType = i['Type'].split('(')
                    if len(iType) == 1:
                        iType.append("")
                    else:
                        iType[1] = '(' + iType[1]
                
                    iType[0] = iType[0].strip()
                    for entry in namingDict[i['Name']]:
                        amt = charDict['Inventory'][entry]
                        if amt == 1:
                            amt = ""
                        else:
                            amt = f"x{amt}"
                        
                        if iType[0] not in typeDict:
                            typeDict[iType[0]] = [f"• {entry} {iType[1]} {amt}\n"]
                        else:
                            typeDict[iType[0]].append(f"• {entry} {iType[1]} {amt}\n")

                for k, v in typeDict.items():
                    v.sort()
                    charEmbed.add_field(name=k, value=''.join(v), inline=False)

            print(len(charEmbed))        
            embedList = [discord.Embed()]
            pages = 1

            if len(charEmbed) > 2048:
                charEmbedDict = charEmbed.to_dict()
                for f in charEmbedDict['fields']:
                    if len(embedList[pages - 1]) > 2048:
                        pages += 1
                        embedList.append(discord.Embed())
                    embedList[pages - 1].add_field(name=f["name"], value=f["value"] ,inline=False)
            else:
                 embedList[0] = charEmbed


            page = 0
            embedList[0].set_footer(text=f"{footer}\nPage {page+1} of {pages}")

            if not charEmbedmsg:
                charEmbedmsg = await ctx.channel.send(embed=embedList[0])
            else:
                await charEmbedmsg.edit(embed=embedList[0])

            while pages > 1:
                await charEmbedmsg.add_reaction(left) 
                await charEmbedmsg.add_reaction(right)
                try:
                    hReact, hUser = await self.bot.wait_for("reaction_add", check=userCheck, timeout=30.0)
                except asyncio.TimeoutError:
                    await charEmbedmsg.edit(content=f"Your user menu has timed out! I'll leave this page open for you. If you need to cycle through the menu again then use the same command!")
                    await charEmbedmsg.clear_reactions()
                    await charEmbedmsg.add_reaction('💤')
                    return
                else:
                    if hReact.emoji == left:
                        page -= 1
                        if page < 0:
                            page = len(embedList) - 1
                    if hReact.emoji == right:
                        page += 1
                        if page > len(embedList) - 1:
                            page = 0
                    embedList[page].set_footer(text=f"{footer}\nPage {page+1} of {pages}")
                    await charEmbedmsg.edit(embed=embedList[page]) 
                    await charEmbedmsg.clear_reactions()

            self.bot.get_command('inv').reset_cooldown(ctx)

    @commands.cooldown(1, 5, type=commands.BucketType.member)
    @commands.command()
    async def user(self,ctx):
        channel = ctx.channel
        author = ctx.author
        guild = ctx.guild
        charEmbed = discord.Embed()
        charEmbedmsg = None

        usersCollection = db.users
        userRecords = usersCollection.find_one({"User ID": str(author.id)})

        def userCheck(r,u):
            sameMessage = False
            if charEmbedmsg.id == r.message.id:
                sameMessage = True
            return sameMessage and u == ctx.author and (r.emoji == left or r.emoji == right)

        if userRecords: 
            playersCollection = db.players
            charRecords = list(playersCollection.find({"User ID": str(author.id)}))
            if charRecords:
                charEmbed.set_author(name=author, icon_url=author.avatar_url)
                charEmbed.title = f"{author.display_name}"

                totalGamesPlayed = 0
                charString = ""
                charString2 = ""

                pages = 1
                pageStops = [0]

                for charDict in charRecords:
                    totalGamesPlayed += charDict['Games'] 
                    tempCharString = charString
                    charString += f"• **{charDict['Name']}**: Lv {charDict['Level']}, {charDict['Race']}, {charDict['Class']}\n"


                    if 'Guild' in charDict:
                        charString += f"~ Guild: *{charDict['Guild']}*\n"

                    if len(charString) > (768 * pages):
                        pageStops.append(len(tempCharString))
                        pages += 1

                pageStops.append(len(charString))

                if 'Games' in userRecords:
                    totalGamesPlayed += userRecords['Games']

                if "Guilds" in userRecords:
                    guildNoodles = "• "
                    guildNoodles += "\n• ".join(userRecords["Guilds"])
                    charEmbed.add_field(name="Guilds", value=f"""You have created **{len(userRecords["Guilds"])}** guilds:\n {guildNoodles}""")
                guildNoodles = "\n".join(userRecords["Guilds"])

                if "Campaigns" in userRecords:
                    campaignString = ""
                    for u, v in userRecords['Campaigns'].items():
                        campaignString += f"• {u} : {v} Hour(s)\n"

                    charEmbed.add_field(name='Campaigns', value=campaignString, inline=False)
                

                if 'Noodles' in userRecords:
                    charEmbed.description = f"Total One-shots Played: {totalGamesPlayed}\nNoodles: {userRecords['Noodles']}"
                else:
                    charEmbed.description = f"Total One-shots Played: {totalGamesPlayed}\nNoodles: 0 (Try hosting sessions to receive Noodles!)"

                userEmbedList = [charEmbed]
                page = 0
                userEmbedList[0].set_footer(text=f"Page {page+1} of {pages}")
                if pages > 1:
                    for p in range(len(pageStops)-1):
                        if p != 0:
                            userEmbedList.append(discord.Embed())
                        userEmbedList[p].add_field(name=f'Characters - p. {p+1}:', value=charString[pageStops[p]:pageStops[p+1]], inline=False)

                else:
                    charEmbed.add_field(name=f'Characters', value=charString, inline=False)

                if not charEmbedmsg:
                    charEmbedmsg = await ctx.channel.send(embed=charEmbed)
                else:
                    await charEmbedmsg.edit(embed=charEmbed)

                while pages > 1:
                    await charEmbedmsg.add_reaction(left) 
                    await charEmbedmsg.add_reaction(right)
                    try:
                        hReact, hUser = await self.bot.wait_for("reaction_add", check=userCheck, timeout=30.0)
                    except asyncio.TimeoutError:
                        await charEmbedmsg.edit(content=f"Your user menu has timed out! I'll leave this page open for you. If you need to cycle through the menu again then use the same command!")
                        await charEmbedmsg.clear_reactions()
                        await charEmbedmsg.add_reaction('💤')
                        return
                    else:
                        if hReact.emoji == left:
                            page -= 1
                            if page < 0:
                                page = len(userEmbedList) - 1
                        if hReact.emoji == right:
                            page += 1
                            if page > len(userEmbedList) - 1:
                                page = 0
                        userEmbedList[page].set_footer(text=f"Page {page+1} of {pages}")
                        await charEmbedmsg.edit(embed=userEmbedList[page]) 
                        await charEmbedmsg.clear_reactions()


        else:
            await channel.send(f'You will need to play at least one session with a character before you can view your user stats.')
            return
            
           
    @commands.cooldown(1, 5, type=commands.BucketType.member)
    @commands.command(aliases=['i', 'char'])
    async def info(self,ctx, char):
        channel = ctx.channel
        author = ctx.author
        guild = ctx.guild
        roleColors = {r.name:r.colour for r in guild.roles}
        charEmbed = discord.Embed()
        charEmbedmsg = None

        statusEmoji = ""
        charDict, charEmbedmsg = await checkForChar(ctx, char, charEmbed)
        if charDict:
            footer = f"To view your character's inventory, type the following command: `{commandPrefix}inv {charDict['Name']}`"
            description = f"{charDict['Race']}\n{charDict['Class']}\n{charDict['Background']}\nGames Played: {charDict['Games']}\n"
            if 'Proficiency' in charDict:
                description +=  f"Extra Training: {charDict['Proficiency']}\n"
            if 'NoodleTraining' in charDict:
                description +=  f"Noodle Training: {charDict['NoodleTraining']}\n"
            description += f":moneybag: {charDict['GP']} gp\n"
            charLevel = charDict['Level']
            if charLevel < 5:
                role = 1
                charEmbed.colour = (roleColors['Junior Friend'])
            elif charLevel < 11:
                role = 2
                charEmbed.colour = (roleColors['Journeyfriend'])
            elif charLevel < 17:
                role = 3
                charEmbed.colour = (roleColors['Elite Friend'])
            elif charLevel < 21:
                role = 4
                charEmbed.colour = (roleColors['True Friend'])

            cpSplit = charDict['CP'].split('/')
            if charLevel < 20 and float(cpSplit[0]) >= float(cpSplit[1]):
                footer += f'\nYou need to level up! Use `{commandPrefix}levelup "character name"` before playing in another quest.'


            if charLevel == 4 or charLevel == 10 or charLevel == 16:
                footer += f'\nYou will no longer receive Tier {role} TP the next time you level up! Please plan accordingly.'

            if 'Death' in charDict:
                statusEmoji = "⚰️"
                description += f"{statusEmoji} Status: **DEAD** -  decide their fate with **`{commandPrefix}death`**." 
                charEmbed.colour = discord.Colour(0xbb0a1e)

            charDictAuthor = guild.get_member(int(charDict['User ID']))
            charEmbed.set_author(name=charDictAuthor, icon_url=charDictAuthor.avatar_url)
            charEmbed.description = description
            charEmbed.clear_fields()    
            charEmbed.title = f"{charDict['Name']} (Lv {charLevel}) - {charDict['CP']} CP"
            tpString = ""
            for i in range (1,5):
                if f"T{i} TP" in charDict:
                    tpString += f"**Tier {i} TP**: {charDict[f'T{i} TP']} " 
            charEmbed.add_field(name='TP', value=f"Current TP Item: **{charDict['Current Item']}**\n{tpString}", inline=True)
            if 'Guild' in charDict:
                charEmbed.add_field(name='Guild', value=f"{charDict['Guild']}\nGuild Rank: {charDict['Guild Rank']}", inline=True)
            charEmbed.add_field(name='Feats', value=charDict['Feats'], inline=False)

            if 'Free Spells' in charDict:
                fsString = ""
                fsIndex = 0
                for el in charDict['Free Spells']:
                    if el > 0:
                        fsString += f"Level {fsIndex+1}: {el} free spells\n"
                    fsIndex += 1

                if fsString:
                    charEmbed.add_field(name='Free Spellbook Copies Available', value=fsString , inline=False)

            if 'Max Stats' not in charDict:
                maxStatDict = charDict['Max Stats'] = {'STR': 20 ,'DEX': 20,'CON': 20, 'INT': 20, 'WIS': 20,'CHA': 20}
            else:
                maxStatDict = charDict['Max Stats']

            for sk in charDict['Max Stats'].keys():
                if charDict[sk] > charDict['Max Stats'][sk]:
                    charDict[sk] = charDict['Max Stats'][sk]
                   
            specialCollection = db.special
            specialRecords = list(specialCollection.find())

            totalHPAdd = 0
            for s in specialRecords:
                                            
                                    
                if 'Attuned' in charDict:
                    if s['Type'] == "Attuned":
                        if s['Name'] in charDict[s['Type']]:
                            if 'HP' in s:
                                totalHPAdd += s['HP']

            # Check for stat increases in attuned magic items.
            if 'Attuned' in charDict:
                charEmbed.add_field(name='Attuned', value='• ' + charDict['Attuned'].replace(', ', '\n• '), inline=False)
                statBonusDict = { 'STR': 0 ,'DEX': 0,'CON': 0, 'INT': 0, 'WIS': 0,'CHA': 0}
                for a in charDict['Attuned'].split(', '):
                    if '[' in a and ']' in a:
                        statBonus = a[a.find("[")+1:a.find("]")] 
                        if '+' not in statBonus and '-' not in statBonus:
                            statSplit = statBonus.split(' ')
                            modStat = str(charDict[statSplit[0]]).replace(')', '').split(' (')[0]
                            if '[' in modStat and ']' in modStat:
                                oldStat = modStat[modStat.find("[")+1:modStat.find("]")] 
                                if '+' not in modStat and '-' not in modStat:
                                    modStat = modStat.split(' [')[0]
                                    if int(oldStat) > int(statSplit[1]):
                                        charDict[statSplit[0]] = f"{modStat} ({oldStat})"
                                else:
                                    modStat = modStat.split(' [')[0]
                                    if (int(modStat) + int(statBonusDict[statSplit[0]])) > int(statSplit[1]):
                                        charDict[statSplit[0]] = f"{modStat} (+{statBonusDict[statSplit[0]]})" 
                                    else:
                                        charDict[statSplit[0]] = f"{modStat} ({statSplit[1]})"

                            elif int(statSplit[1]) > int(modStat):
                                maxStatNum = statSplit[1]
                                if '(' in str(charDict[statSplit[0]]):
                                    maxStatNum = max(int(str((charDict[statSplit[0]])).replace(')', '').split(' (')[1]), int(statSplit[1]) )
                                charDict[statSplit[0]] = f"{modStat} ({maxStatNum})"

                        elif '+' in statBonus:
                            statBonusSplit = statBonus.split(';')
                            statSplit = statBonusSplit[0].split(' +')
                            if 'MAX' in statSplit[0]:
                                maxStat = statSplit[0][:-3]
                                statSplit[0] = statSplit[0].replace(maxStat, "")
                                maxStat = maxStat.split(" ")
                                print(maxStatDict)

                            modStat = str(charDict[statSplit[0]])
                            modStat = modStat.split(' (')[0]
                            statBonusDict[statSplit[0]] += int(statSplit[1])
                            statName = charDict[statSplit[0]]
                            maxStatBonus = []
                            maxCalc = int(modStat) + int(statBonusDict[statSplit[0]]) > maxStatDict[statSplit[0]]

                            if maxCalc:
                                statBonusDict[statSplit[0]] = maxStatDict[statSplit[0]] - int(modStat)
                            if statBonusDict[statSplit[0]] > 0: 
                                charDict[statSplit[0]] = f"{modStat} (+{statBonusDict[statSplit[0]]})" 
                            else:
                                charDict[statSplit[0]] = f"{modStat}" 

                # recalc CON
                if statBonusDict['CON'] != 0 or '(' in str(charDict['CON']):
                    trueConValue = charDict['CON']
                    conValue = charDict['CON'].replace(')', '').split('(')            

                    if len(conValue) > 1:
                        trueConValue = max(conValue)

                    if '+' in conValue[1]:
                        trueConValue = int(conValue[1].replace('+', '')) + int(conValue[0])

                    print(trueConValue)

                    charDict['HP'] -= ((int(conValue[0]) - 10) // 2) * charLevel
                    charDict['HP'] += ((int(trueConValue) - 10) // 2) * charLevel

            charDict['HP'] += totalHPAdd * charLevel

            charEmbed.add_field(name='Stats', value=f":heart: {charDict['HP']} Max HP\n**STR**: {charDict['STR']} **DEX**: {charDict['DEX']} **CON**: {charDict['CON']} **INT**: {charDict['INT']} **WIS**: {charDict['WIS']} **CHA**: {charDict['CHA']}", inline=False)
            if "Double Rewards Buff" in charDict:
                drRemain = charDict['Double Rewards Buff'] + timedelta(days=3) - datetime.now()
                if drRemain > timedelta(seconds=1):
                    charEmbed.add_field(name='Double Rewards Buff', value=f"{drRemain.days * 24 +drRemain.seconds//3600}h : {(drRemain.seconds//60)%60}m remain", inline=False)

            if "Double Items Buff" in charDict:
                diRemain = charDict['Double Items Buff'] + timedelta(days=3) - datetime.now()
                if diRemain > timedelta(seconds=1):
                    charEmbed.add_field(name='Double Items Buff', value=f"{diRemain.days * 24 +diRemain.seconds//3600}h : {(diRemain.seconds//60)%60}m remain", inline=False) 

            charEmbed.set_footer(text=footer)

            if 'Image' in charDict:
                charEmbed.set_thumbnail(url=charDict['Image'])

            if not charEmbedmsg:
                charEmbedmsg = await ctx.channel.send(embed=charEmbed)
            else:
                await charEmbedmsg.edit(embed=charEmbed)

            self.bot.get_command('info').reset_cooldown(ctx)

    @commands.cooldown(1, 5, type=commands.BucketType.member)
    @commands.command(aliases=['img'])
    async def image(self,ctx, char, url):

        channel = ctx.channel
        author = ctx.author
        guild = ctx.guild
        charEmbed = discord.Embed()

        infoRecords, charEmbedmsg = await checkForChar(ctx, char, charEmbed)

        if infoRecords:
            charID = infoRecords['_id']
            data = {
                'Image': url
            }

            try:
                r = requests.head(url)
                if r.status_code != requests.codes.ok:
                    await ctx.channel.send(content=f'It looks like the URL is either invalid or contains a broken image. Please follow this format:\n```yaml\n{commandPrefix}image "character name" URL```\n') 
                    return
            except:
                await ctx.channel.send(content=f'It looks like the URL is either invalid or contains a broken image. Please follow this format:\n```yaml\n{commandPrefix}image "character name" URL```\n') 

                return
              
            try:
                playersCollection = db.players
                playersCollection.update_one({'_id': charID}, {"$set": data})
            except Exception as e:
                print ('MONGO ERROR: ' + str(e))
                charEmbedmsg = await channel.send(embed=None, content="Uh oh, looks like something went wrong. Please try creating your character again.")
            else:
                print('Success')
                await ctx.channel.send(content=f'I have updated the image for ***{char}***. Please double-check using one of the following commands:\n```yaml\n{commandPrefix}info "character name"\n{commandPrefix}char "character name"\n{commandPrefix}i "character name"```')

    @commands.cooldown(1, float('inf'), type=commands.BucketType.user)
    @commands.command(aliases=['lvl', 'lvlup', 'lv'])
    async def levelup(self,ctx, char):
        channel = ctx.channel
        author = ctx.author
        guild = ctx.guild
        levelUpEmbed = discord.Embed ()
        characterCog = self.bot.get_cog('Character')
        infoRecords, levelUpEmbedmsg = await checkForChar(ctx, char, levelUpEmbed)
        charClassChoice = ""
        if infoRecords:
            charID = infoRecords['_id']
            charDict = {}
            charName = infoRecords['Name']
            charClass = infoRecords['Class']
            cpSplit= infoRecords['CP'].split('/')
            charLevel = infoRecords['Level']
            charStats = {'STR':infoRecords['STR'], 'DEX':infoRecords['DEX'], 'CON':infoRecords['CON'], 'INT':infoRecords['INT'], 'WIS':infoRecords['WIS'], 'CHA':infoRecords['CHA']}
            charHP = infoRecords['HP']
            charFeats = infoRecords['Feats']
            freeSpells = [0] * 9

            if 'Free Spells' in infoRecords:
                freeSpells = infoRecords['Free Spells']

            if 'Death' in infoRecords.keys():
                await channel.send(f'You cannot level up a dead character. Use the following command to decide their fate:\n```yaml\n$death "{charRecords["Name"]}"```')
                self.bot.get_command('levelup').reset_cooldown(ctx)
                return

            if charLevel > 19:
                await channel.send(f"***{infoRecords['Name']}*** is level 20 and cannot level up anymore.")
                self.bot.get_command('levelup').reset_cooldown(ctx)
                return
                

            elif float(cpSplit[0]) < float(cpSplit[1]):
                await channel.send(f'***{charName}*** is not ready to level up. They currently have **{cpSplit[0]}/{cpSplit[1]}** CP.')
                self.bot.get_command('levelup').reset_cooldown(ctx)
                return
            else:
                cRecords, levelUpEmbed, levelUpEmbedmsg = await callAPI(ctx, levelUpEmbed, levelUpEmbedmsg,'classes')
                classRecords = sorted(cRecords, key=lambda k: k['Name']) 
                leftCP = float(cpSplit[0]) - float(cpSplit[1])
                newCharLevel = charLevel  + 1
                totalCP = f'{leftCP}/{cpSplit[1]}'
                subclasses = []
                if '/' in charClass:
                    tempClassList = charClass.split(' / ')
                    for t in tempClassList:
                        temp = t.split(' ')
                        tempSub = ""
                        if '(' and ')' in t:
                            tempSub = t[t.find("(")+1:t.find(")")]

                        subclasses.append({'Name':temp[0], 'Subclass':tempSub, 'Level':int(temp[1])})
                else:
                    tempSub = ""
                    if '(' and ')' in charClass:
                        tempSub = charClass[charClass.find("(")+1:charClass.find(")")]
                    subclasses.append({'Name':charClass, 'Subclass':tempSub, 'Level':charLevel})

                for c in classRecords:
                    for s in subclasses:
                        if c['Name'] in s['Name']:
                            s['Hit Die Max'] = c['Hit Die Max']
                            s['Hit Die Average'] = c['Hit Die Average']

                subclasses = sorted(subclasses, key = lambda i: i['Level'], reverse=True)

                if newCharLevel > 4:
                    totalCP = f'{leftCP}/10.0'

                def multiclassEmbedCheck(r, u):
                        sameMessage = False
                        if levelUpEmbedmsg.id == r.message.id:
                            sameMessage = True
                        return sameMessage and ((str(r.emoji) == '✅' and chooseClassString != "") or (str(r.emoji) == '🚫') or (str(r.emoji) == '❌')) and u == author
                def alphaEmbedCheck(r, u):
                        sameMessage = False
                        if levelUpEmbedmsg.id == r.message.id:
                            sameMessage = True
                        return sameMessage and ((r.emoji in alphaEmojis[:alphaIndex]) or (str(r.emoji) == '❌')) and u == author


                levelUpEmbed.clear_fields()
                lvl = charLevel
                newLevel = charLevel + 1
                levelUpEmbed.title = f"{charName}: Level Up! {lvl} → {newLevel}"
                levelUpEmbed.description = f"{infoRecords['Race']}: {charClass}\n**STR**: {charStats['STR']} **DEX**: {charStats['DEX']} **CON**: {charStats['CON']} **INT**: {charStats['INT']} **WIS**: {charStats['WIS']} **CHA**: {charStats['CHA']}"
                chooseClassString = ""
                alphaIndex = 0
                classes = []
                lvlClass = charClass

                # Multiclass Requirements
                failMulticlassList = []
                baseClass = {'Name': ''}
                
                for cRecord in classRecords:
                    if cRecord['Name'] in charClass:
                        baseClass = cRecord

                    statReq = cRecord['Multiclass'].split(' ')
                    if cRecord['Multiclass'] != 'None':
                        if '/' not in cRecord['Multiclass'] and '+' not in cRecord['Multiclass']:
                            if int(infoRecords[statReq[0]]) < int(statReq[1]):
                                failMulticlassList.append(cRecord['Name'])
                                continue
                        elif '/' in cRecord['Multiclass']:
                            statReq[0] = statReq[0].split('/')
                            reqFufill = False
                            for s in statReq[0]:
                                if int(infoRecords[s]) >= int(statReq[1]):
                                    reqFufill = True
                            if not reqFufill:
                                failMulticlassList.append(cRecord['Name'])
                                continue

                        elif '+' in cRecord['Multiclass']:
                            statReq[0] = statReq[0].split('+')
                            reqFufill = True
                            for s in statReq[0]:
                                if int(infoRecords[s]) < int(statReq[1]):
                                    reqFufill = False
                                    break
                            if not reqFufill:
                                failMulticlassList.append(cRecord['Name'])
                                continue


                        if cRecord['Name'] not in failMulticlassList and cRecord['Name'] != baseClass['Name']:
                            chooseClassString += f"{alphaEmojis[alphaIndex]}: {cRecord['Name']}\n"
                            alphaIndex += 1
                            classes.append(cRecord['Name'])


                # New Multiclass
                if chooseClassString != "":
                    levelUpEmbed.add_field(name="Would you like to choose a new multiclass?", value='✅: Yes\n\n🚫: No\n\n❌: Cancel')
                else:
                    levelUpEmbed.add_field(name="""~~Would you like to choose a new multiclass?~~\nThere are no classes available to multiclass into. Please react with "No" to proceed.""", value='~~✅: Yes~~\n\n🚫: No\n\n❌: Cancel')

                if not levelUpEmbedmsg:
                    levelUpEmbedmsg = await channel.send(embed=levelUpEmbed)
                else:
                    await levelUpEmbedmsg.edit(embed=levelUpEmbed)
                if chooseClassString != "":
                    await levelUpEmbedmsg.add_reaction('✅')
                await levelUpEmbedmsg.add_reaction('🚫')
                await levelUpEmbedmsg.add_reaction('❌')
                try:
                    tReaction, tUser = await self.bot.wait_for("reaction_add", check=multiclassEmbedCheck, timeout=60)
                except asyncio.TimeoutError:
                    await levelUpEmbedmsg.delete()
                    await channel.send(f'Level up cancelled. Try again using the same command or one of its shorthand forms:\n```yaml\n{commandPrefix}levelup "character name"\n{commandPrefix}lvlup "character name"\n{commandPrefix}lvl "character name"\n{commandPrefix}lv "character name"```')
                    self.bot.get_command('levelup').reset_cooldown(ctx)
                    return
                else:
                    await levelUpEmbedmsg.clear_reactions()
                    if tReaction.emoji == '❌':
                        await levelUpEmbedmsg.edit(embed=None, content=f"Level up cancelled. Try again using the same command or one of its shorthand forms:\n```yaml\n{commandPrefix}levelup \"character name\"\n{commandPrefix}lvlup \"character name\"\n{commandPrefix}lvl \"character name\"\n{commandPrefix}lv \"character name\"```")
                        await levelUpEmbedmsg.clear_reactions()
                        self.bot.get_command('levelup').reset_cooldown(ctx)
                        return
                    elif tReaction.emoji == '✅':
                        levelUpEmbed.clear_fields()
                        if baseClass['Name'] in failMulticlassList:
                            await levelUpEmbedmsg.edit(embed=None, content=f"You cannot multiclass right now because your base class, **{baseClass['Name']}**, requires at least **{baseClass['Multiclass']}**.\nCurrent stats: **STR**: {charStats['STR']} **DEX**: {charStats['DEX']} **CON**: {charStats['CON']} **INT**: {charStats['INT']} **WIS**: {charStats['WIS']} **CHA**: {charStats['CHA']}")

                            await levelUpEmbedmsg.clear_reactions()
                            self.bot.get_command('levelup').reset_cooldown(ctx)
                            return

                        levelUpEmbed.add_field(name="Pick a new class that you would like to multiclass into.", value=chooseClassString)

                        await levelUpEmbedmsg.edit(embed=levelUpEmbed)
                        await levelUpEmbedmsg.add_reaction('❌')
                        try:
                            tReaction, tUser = await self.bot.wait_for("reaction_add", check=alphaEmbedCheck, timeout=60)
                        except asyncio.TimeoutError:
                            await levelUpEmbedmsg.delete()
                            await channel.send(f'Level up cancelled. Try again using the same command or one of its shorthand forms:\n```yaml\n{commandPrefix}levelup "character name"\n{commandPrefix}lvlup "character name"\n{commandPrefix}lvl "character name"\n{commandPrefix}lv "character name"```')
                            self.bot.get_command('levelup').reset_cooldown(ctx)
                            return
                        else:
                            await levelUpEmbedmsg.clear_reactions()
                            if tReaction.emoji == '❌':
                                await levelUpEmbedmsg.edit(embed=None, content=f"Level up cancelled. Try again using the same command or one of its shorthand forms:\n```yaml\n{commandPrefix}levelup \"character name\"\n{commandPrefix}lvlup \"character name\"\n{commandPrefix}lvl \"character name\"\n{commandPrefix}lv \"character name\"```")
                                await levelUpEmbedmsg.clear_reactions()
                                self.bot.get_command('levelup').reset_cooldown(ctx)
                                return

                            if '/' not in charClass:
                                if '(' in charClass and ')' in charClass:
                                    charClass = charClass.replace('(', f"{lvl} (")
                                else:
                                    charClass += ' ' + str(lvl)
                                
                            charClassChoice = classes[alphaEmojis.index(tReaction.emoji)]
                            charClass += f' / {charClassChoice} 1'
                            lvlClass = charClassChoice
                            for c in classRecords:
                                if c['Name'] in charClassChoice:
                                    subclasses.append({'Name': charClassChoice, 'Subclass': '', 'Level': 1, 'Hit Die Max': c['Hit Die Max'], 'Hit Die Average': c['Hit Die Average']})

                            if "Wizard" in charClassChoice:
                                freeSpells[0] += 6

                            levelUpEmbed.description = f"{infoRecords['Race']}: {charClass}\n**STR**:{charStats['STR']} **DEX**:{charStats['DEX']} **CON**:{charStats['CON']} **INT**:{charStats['INT']} **WIS**:{charStats['WIS']} **CHA**:{charStats['CHA']}"
                            levelUpEmbed.clear_fields()
                    elif tReaction.emoji == '🚫':
                        if '/' not in charClass:
                            lvlClass = charClass
                            subclasses[0]['Level'] += 1
                            if 'Wizard' in charClass: 
                                fsLvl = (subclasses[0]['Level'] - 1) // 2
                                if fsLvl > 8:
                                    fsLvl = 8

                                freeSpells[fsLvl] += 2
                        else:
                            multiclassLevelString = ""
                            alphaIndex = 0
                            for sc in subclasses:
                                multiclassLevelString += f"{alphaEmojis[alphaIndex]}: {sc['Name']} Level {sc['Level']}\n"
                                alphaIndex += 1
                            levelUpEmbed.clear_fields()
                            levelUpEmbed.add_field(name=f"What class would you like to level up?", value=multiclassLevelString, inline=False)
                            await levelUpEmbedmsg.edit(embed=levelUpEmbed)
                            await levelUpEmbedmsg.add_reaction('❌')
                            try:
                                tReaction, tUser = await self.bot.wait_for("reaction_add", check=alphaEmbedCheck, timeout=60)
                            except asyncio.TimeoutError:
                                await levelUpEmbedmsg.delete()
                                await channel.send(f'Level up timed out! Try again using the same command:\n```yaml\n{commandPrefix}create "character name" level "race" "class" "background" STR DEX CON INT WIS CHA "magic item1, magic item2, [...]" "reward item1, reward item2, [...]"```')
                                self.bot.get_command('levelup').reset_cooldown(ctx)
                                return
                            else:
                                if tReaction.emoji == '❌':
                                    await levelUpEmbedmsg.edit(embed=None, content=f"Level up cancelled. Try again using the same command or one of its shorthand forms:\n```yaml\n{commandPrefix}levelup \"character name\"\n{commandPrefix}lvlup \"character name\"\n{commandPrefix}lvl \"character name\"\n{commandPrefix}lv \"character name\"```")
                                    await levelUpEmbedmsg.clear_reactions()
                                    self.bot.get_command('levelup').reset_cooldown(ctx)
                                    return
                            await levelUpEmbedmsg.clear_reactions()
                            levelUpEmbed.clear_fields()
                            choiceLevelClass = multiclassLevelString.split('\n')[alphaEmojis.index(tReaction.emoji)]

                            for s in subclasses:
                                if s['Name'] in choiceLevelClass:
                                    lvlClass = s['Name']
                                    s['Level'] += 1
                                    if 'Wizard' in s['Name']:
                                        fsLvl = (subclasses[0]['Level'] - 1) // 2
                                        if fsLvl > 8:
                                            fsLvl = 8
                                        freeSpells[fsLvl] += 2
                                    break

                            charClass = charClass.replace(f"{lvlClass} {subclasses[alphaEmojis.index(tReaction.emoji)]['Level'] - 1}", f"{lvlClass} {subclasses[alphaEmojis.index(tReaction.emoji)]['Level']}")
                            levelUpEmbed.description = f"{infoRecords['Race']}: {charClass}\n**STR**:{charStats['STR']} **DEX**:{charStats['DEX']} **CON**:{charStats['CON']} **INT**:{charStats['INT']} **WIS**:{charStats['WIS']} **CHA**:{charStats['CHA']}"

                # Choosing a subclass
                subclassCheckClass = subclasses[[s['Name'] for s in subclasses].index(lvlClass)]

                for s in classRecords:
                    if s['Name'] == subclassCheckClass['Name'] and int(s['Subclass Level']) == subclassCheckClass['Level']:
                        subclassesList = s['Subclasses'].split(', ')
                        subclassChoice, levelUpEmbedmsg = await characterCog.chooseSubclass(ctx, subclassesList, s['Name'], levelUpEmbed, levelUpEmbedmsg) 
                        if not subclassChoice:
                            return
                        
                        if '/' not in charClass:
                            levelUpEmbed.description = levelUpEmbed.description.replace(s['Name'], f"{s['Name']} ({subclassChoice})") 
                            charClass = charClass.replace(s['Name'], f"{s['Name']} ({subclassChoice})" )
                        else:
                            levelUpEmbed.description = levelUpEmbed.description.replace(f"{s['Name']} {subclassCheckClass['Level']}", f"{s['Name']} {subclassCheckClass['Level']} ({subclassChoice})" ) 
                            charClass = charClass.replace(f"{s['Name']} {subclassCheckClass['Level']}", f"{s['Name']} {subclassCheckClass['Level']} ({subclassChoice})" )

                        for sub in subclasses:
                            if sub['Name'] == subclassCheckClass['Name']:
                                sub['Subclass'] = subclassChoice
                
                # Feat 
                featLevels = []
                for c in subclasses:
                    if (int(c['Level']) in (4,8,12,16,19) or ('Fighter' in c['Name'] and int(c['Level']) in (6,14)) or ('Rogue' in c['Name'] and int(c['Level']) == 10)) and lvlClass in c['Name']:
                        featLevels.append(int(c['Level']))

                charFeatsGained = ""
                charFeatsGainedStr = ""
                if featLevels != list():
                    featsChosen, statsFeats, charEmbedmsg = await characterCog.chooseFeat(ctx, infoRecords['Race'], charClass, subclasses, featLevels, levelUpEmbed, levelUpEmbedmsg, infoRecords, charFeats)
                    if not featsChosen and not statsFeats and not charEmbedmsg:
                        return

                    charStats = statsFeats 
                    
                    if featsChosen != list():
                        charFeatsGained = featsChosen

                if charFeatsGained != "":
                    charFeatsGainedStr = f"Feats Gained: **{charFeatsGained}**"

                data = {
                      'Class': charClass,
                      'Level': int(newCharLevel),
                      'CP': totalCP,
                      'STR': int(charStats['STR']),
                      'DEX': int(charStats['DEX']),
                      'CON': int(charStats['CON']),
                      'INT': int(charStats['INT']),
                      'WIS': int(charStats['WIS']),
                      'CHA': int(charStats['CHA']),
                }

                if 'Free Spells' in infoRecords:
                    if freeSpells != ([0] * 9):
                        data['Free Spells'] = freeSpells

                if charFeatsGained != "":
                    if infoRecords['Feats'] == 'None':
                        data['Feats'] = charFeatsGained
                    elif infoRecords['Feats'] != None:
                        data['Feats'] = charFeats + ", " + charFeatsGained

                statsCollection = db.stats
                statsRecord  = statsCollection.find_one({'Life': 1})
                
                subclassCheckClass['Name'] = subclassCheckClass['Name'].split(' (')[0]
                if subclassCheckClass['Subclass'] != "" :
                    if subclassCheckClass['Subclass']  in statsRecord['Class'][subclassCheckClass['Name']]:
                        statsRecord['Class'][subclassCheckClass['Name']][subclassCheckClass['Subclass']] += 1
                    else:
                        statsRecord['Class'][subclassCheckClass['Name']][subclassCheckClass['Subclass']] = 1
                else:
                    if subclassCheckClass['Name'] in statsRecord['Class']:
                        statsRecord['Class'][subclassCheckClass['Name']]['Count'] += 1
                    else:
                        statsRecord['Class'][subclassCheckClass['Name']] = {'Count': 1}

                if 'Max Stats' not in infoRecords:
                    infoRecords['Max Stats'] = {'STR':20, 'DEX':20, 'CON':20, 'INT':20, 'WIS':20, 'CHA':20}
                
                data['Max Stats'] = infoRecords['Max Stats']

                #Special stat bonuses (Barbarian cap / giant soul sorc)
                specialCollection = db.special
                specialRecords = list(specialCollection.find())
                specialStatStr = ""
                for s in specialRecords:
                    if 'Bonus Level' in s:
                        for c in subclasses:
                            if s['Bonus Level'] == c['Level'] and s['Name'] in f"{c['Name']} ({c['Subclass']})":
                                if 'MAX' in s['Stat Bonuses']:
                                    statSplit = s['Stat Bonuses'].split('MAX ')[1].split(', ')
                                    for stat in statSplit:
                                        maxSplit = stat.split(' +')
                                        data[maxSplit[0]] += int(maxSplit[1])
                                        charStats[maxSplit[0]] += int(maxSplit[1])
                                        data['Max Stats'][maxSplit[0]] += int(maxSplit[1]) 

                                    specialStatStr = f"Level {s['Bonus Level']} {c['Name']} stat bonus unlocked! {s['Stat Bonuses']}"


                maxStatStr = ""
                for sk in data['Max Stats'].keys():
                    if charStats[sk] > data['Max Stats'][sk]:
                        data[sk] = charStats[sk] = data['Max Stats'][sk]
                        if charFeatsGained != "":
                            maxStatStr += f"\n{infoRecords['Name']}'s {sk} will not increase because their maximum is {data['Max Stats'][sk]}."

                infoRecords['CON'] = charStats['CON']
                charHP = await characterCog.calcHP(ctx, subclasses, infoRecords, int(newCharLevel))
                data['HP'] = charHP

                levelUpEmbed.title = f'{charName} has leveled up to {newCharLevel}!\nCurrent CP: {totalCP} CP'
                levelUpEmbed.description = f"{infoRecords['Race']} {charClass}\n**STR**: {charStats['STR']} **DEX**: {charStats['DEX']} **CON**: {charStats['CON']} **INT**: {charStats['INT']} **WIS**: {charStats['WIS']} **CHA**: {charStats['CHA']}" + f"\n{charFeatsGainedStr}{maxStatStr}\n{specialStatStr}"
                if charClassChoice != "":
                    levelUpEmbed.description += f"Multiclass into: **{charClassChoice}**"
                levelUpEmbed.set_footer(text= levelUpEmbed.Empty)
                levelUpEmbed.clear_fields()

                def charCreateCheck(r, u):
                    sameMessage = False
                    if levelUpEmbedmsg.id == r.message.id:
                        sameMessage = True
                    return sameMessage and ((str(r.emoji) == '✅') or (str(r.emoji) == '❌')) and u == author


                if not levelUpEmbedmsg:
                   levelUpEmbedmsg = await channel.send(embed=levelUpEmbed, content="**Double-check** your character information.\nIf this is correct, please react with one of the following:\n✅ to finish creating your character.\n❌ to cancel. ")
                else:
                    await levelUpEmbedmsg.edit(embed=levelUpEmbed, content="**Double-check** your character information.\nIf this is correct, please react with one of the following:\n✅ to finish creating your character.\n❌ to cancel. ")

                await levelUpEmbedmsg.add_reaction('✅')
                await levelUpEmbedmsg.add_reaction('❌')
                try:
                    tReaction, tUser = await self.bot.wait_for("reaction_add", check=charCreateCheck , timeout=60)
                except asyncio.TimeoutError:
                    await levelUpEmbedmsg.delete()
                    await channel.send(f'Level up cancelled. Try again using the same command or one of its shorthand forms:\n```yaml\n{commandPrefix}levelup "character name"\n{commandPrefix}lvlup "character name"\n{commandPrefix}lvl "character name"\n{commandPrefix}lv "character name"```')
                    self.bot.get_command('levelup').reset_cooldown(ctx)
                    return
                else:
                    await levelUpEmbedmsg.clear_reactions()
                    if tReaction.emoji == '❌':
                        await levelUpEmbedmsg.edit(embed=None, content=f"Try again using the same command or one of its shorthand forms:\n```yaml\n{commandPrefix}levelup \"character name\"\n{commandPrefix}lvlup \"character name\"\n{commandPrefix}lvl \"character name\"\n{commandPrefix}lv \"character name\"```")
                        await levelUpEmbedmsg.clear_reactions()
                        self.bot.get_command('levelup').reset_cooldown(ctx)
                        return

                try:
                    playersCollection = db.players
                    playersCollection.update_one({'_id': charID}, {"$set": data})
                    statsCollection.update_one({'Life':1}, {"$set": statsRecord}, upsert=True)
                except Exception as e:
                    print ('MONGO ERROR: ' + str(e))
                    charEmbedmsg = await channel.send(embed=None, content="Uh oh, looks like something went wrong. Please try creating your character again.")
                else:
                    print("Success")

                roles = [r.name for r in author.roles]
                roleName = ""
                if 'Journeyfriend' not in roles and 'Junior Friend' in roles and newCharLevel > 4:
                    roleName = 'Journeyfriend' 
                    tierRoleStr = 'Tier 2'
                    roleRemoveStr = 'Junior Friend'
                    levelRole = get(guild.roles, name = roleName)
                    tierRole = get(guild.roles, name = tierRoleStr)
                    roleRemove = get(guild.roles, name = roleRemoveStr)
                    await author.add_roles(levelRole, reason=f"***{author}***'s character ***{charName}*** is the first character who has reached level 5!")
                    await author.add_roles(tierRole, reason=f"***{author}***'s character ***{charName}*** is the first character who has reached level 5!")
                    await author.remove_roles(roleRemove)
                if 'Elite Friend' not in roles and 'Journeyfriend' in roles and newCharLevel > 10:
                    roleName = 'Elite Friend'
                    tierRoleStr = 'Tier 3'
                    roleRemoveStr = 'Journeyfriend'
                    levelRole = get(guild.roles, name = roleName)
                    tierRole = get(guild.roles, name = tierRoleStr)
                    roleRemove = get(guild.roles, name = roleRemoveStr)
                    await author.add_roles(levelRole, reason=f"***{author}***'s character ***{charName}*** is the first character who has reached level 11!")
                    await author.add_roles(tierRole, reason=f"***{author}***'s character ***{charName}*** is the first character who has reached level 11!")
                    await author.remove_roles(roleRemove)
                if 'True Friend' not in roles and 'Elite Friend' in roles and newCharLevel > 16:
                    roleName = 'True Friend'
                    tierRoleStr = 'Tier 4'
                    roleRemoveStr = 'Elite Friend'
                    levelRole = get(guild.roles, name = roleName)
                    tierRole = get(guild.roles, name = tierRoleStr)
                    roleRemove = get(guild.roles, name = roleRemoveStr)
                    await author.add_roles(levelRole, reason=f"***{author}***'s character ***{charName}*** is the first character who has reached level 17!")
                    await author.add_roles(tierRole, reason=f"***{author}***'s character ***{charName}*** is the first character who has reached level 17!")
                    await author.remove_roles(roleRemove)

                levelUpEmbed.clear_fields()
                await levelUpEmbedmsg.edit(content=f":arrow_up:   __**L E V E L   U P!**__\n\n:warning:   **Don't forget to spend your TP!** Use the following command to spend your TP:\n```yaml\n$tp buy \"{charName}\" \"magic item\"```", embed=levelUpEmbed)

                if roleName != "":
                    levelUpEmbed.title = f":tada: {roleName} role acquired! :tada:\n" + levelUpEmbed.title
                    await levelUpEmbedmsg.edit(embed=levelUpEmbed)
                    await levelUpEmbedmsg.add_reaction('🎉')
                    await levelUpEmbedmsg.add_reaction('🥳')
                    await levelUpEmbedmsg.add_reaction('🙌')
                    await levelUpEmbedmsg.add_reaction('🎊')
                    await levelUpEmbedmsg.add_reaction('🍾')

        self.bot.get_command('levelup').reset_cooldown(ctx)

    @commands.cooldown(1, 5, type=commands.BucketType.member)
    @commands.command(aliases=['att'])
    async def attune(self,ctx, char, m):
        channel = ctx.channel
        author = ctx.author
        guild = ctx.guild
        charEmbed = discord.Embed ()
        charRecords, charEmbedmsg = await checkForChar(ctx, char, charEmbed)

        if charRecords:
            if 'Death' in charRecords:
                await channel.send(f"You cannot attune to items while your character is dead! Use the following command to decide their fate:\n```yaml\n$death \"{charRecords['Name']}\"```")
                return

            # Check number of items character can attune to. Artificer has exceptions.
            attuneLength = 3
            if charRecords['Class'] == 'Artificer':
                if charRecords['Level'] >= 16:
                    attuneLength = 6
                elif charRecords['Level'] >= 13:
                    attuneLength = 5
                elif charRecords['Level'] >= 10:
                    attuneLength = 4

            if "Attuned" not in charRecords:
                attuned = []
            else:
                attuned = charRecords['Attuned'].split(', ')


            charID = charRecords['_id']
            charRecordMagicItems = charRecords['Magic Items'].split(', ')
            if len(attuned) >= attuneLength:
                await channel.send(f"The maximum number of magic items you can attune to is three! You cannot attune to any more items!")
                return

            def apiEmbedCheck(r, u):
                sameMessage = False
                if charEmbedmsg.id == r.message.id:
                    sameMessage = True
                return sameMessage and ((r.emoji in numberEmojis[:min(len(mList), 9)]) or (str(r.emoji) == '❌')) and u == author

            mList = []
            mString = ""
            numI = 0

            # Check if query is in character's Magic Item List. Limit is 8 to show if there are multiple matches.
            print([a.split(' [')[0] for a in attuned])
            for k in charRecordMagicItems:
                if m.lower() in k.lower():
                    if k not in [a.split(' [')[0] for a in attuned]:
                        mList.append(k)
                        mString += f"{numberEmojis[numI]} {k} \n"
                        numI += 1
                if numI > 8:
                    break

            # IF multiple matches, check which one the player meant.
            if (len(mList) > 1):
                charEmbed.add_field(name=f"There seems to be multiple results for **`{m}`**, please choose the correct one.\nIf the result you are looking for is not here, please cancel the command with ❌ and be more specific.", value=mString, inline=False)
                if not charEmbedmsg:
                    charEmbedmsg = await channel.send(embed=charEmbed)
                else:
                    await charEmbedmsg.edit(embed=charEmbed)

                await charEmbedmsg.add_reaction('❌')

                try:
                    tReaction, tUser = await self.bot.wait_for("reaction_add", check=apiEmbedCheck, timeout=60)
                except asyncio.TimeoutError:
                    await charEmbedmsg.delete()
                    await channel.send('Timed out! Try using the command again.')
                    ctx.command.reset_cooldown(ctx)
                    return None, charEmbed, charEmbedmsg
                else:
                    if tReaction.emoji == '❌':
                        await charEmbedmsg.edit(embed=None, content=f"Command cancelled. Try using the command again.")
                        await charEmbedmsg.clear_reactions()
                        ctx.command.reset_cooldown(ctx)
                        return None,charEmbed, charEmbedmsg
                charEmbed.clear_fields()
                await charEmbedmsg.clear_reactions()
                m = mList[int(tReaction.emoji[0]) - 1]

            elif len(mList) == 1:
                m = mList[0]
            else:
                await channel.send(f"`{m}` isn't in {charRecords['Name']}'s inventory. Please try the command again.")
                return

            # Check if magic item's actually exist, and grab properties. (See if they're attuneable)
            mRecord, charEmbed, charEmbedmsg = await callAPI(ctx, charEmbed, charEmbedmsg,'mit', m, True)
            if not mRecord:
                mRecord, charEmbed, charEmbedmsg = await callAPI(ctx, charEmbed, charEmbedmsg,'rit', m, True)
                if not mRecord:
                    await channel.send(f"`{m}` does not exist on the Magic Item Table or Reward Item Table.")
                    return
                elif mRecord['Name'].lower() not in [x.lower() for x in charRecordMagicItems]:
                    await channel.send(f"You don't have the **{mRecord['Name']}** item in your inventory to attune to.")
                    return
            elif mRecord['Name'].lower() not in [x.lower() for x in charRecordMagicItems]:
                    await channel.send(f"You don't have the **{mRecord['Name']}** item in your inventory to attune to.")
                    return

            # Check if they are already attuned to the item.
            if mRecord['Name'] == 'Hammer of Thunderbolts':
                if 'Max Stats' not in charRecords:
                    charRecords['Max Stats'] = {'STR':20, 'DEX':20, 'CON':20, 'INT':20, 'WIS':20, 'CHA':20}
                # statSplit = MAX STAT +X
                statSplit = mRecord['Stat Bonuses'].split(' +')
                maxSplit = statSplit[0].split(' ')

                #Increase stats from Hammer and add to max stats. 
                if "MAX" in statSplit[0]:
                    charRecords['Max Stats'][maxSplit[1]] += int(statSplit[1]) 

                if 'Belt of' not in charRecords['Magic Items'] and 'Frost Giant Strength' not in charRecords['Magic Items'] and 'Gauntlets of Ogre Power' not in charRecords['Magic Items']:
                    await channel.send(f"`Hammer of Thunderbolts` requires you to have a `Belt of Giant Strength (any variety)` and `Gauntlets of Ogre Power` in your inventory in order to attune to it.")
                    return 

            if mRecord['Name'] in [a.split('[')[0].strip() for a in attuned]:
                await channel.send(f"You are already attuned to **{mRecord['Name']}**!")
                return
            elif 'Attunement' in mRecord:
                if 'Stat Bonuses' in mRecord:
                    attuned.append(f"{mRecord['Name']} [{mRecord['Stat Bonuses']}]")
                else:
                    attuned.append(mRecord['Name'])
            else:
                await channel.send(f"`{m}` does not require attunement so there is no need to try to attune this item.")
                return
                        
            
            charRecords['Attuned'] = ', '.join(attuned)
            data = charRecords

            try:
                playersCollection = db.players
                playersCollection.update_one({'_id': charID}, {"$set": data})
            except Exception as e:
                print ('MONGO ERROR: ' + str(e))
                charEmbedmsg = await channel.send(embed=None, content="Uh oh, looks like something went wrong. Please try creating your character again.")
            else:
                await channel.send(f"You successfully attuned to **{mRecord['Name']}**!")

    @commands.cooldown(1, 5, type=commands.BucketType.member)
    @commands.command(aliases=['uatt', 'unatt'])
    async def unattune(self,ctx, char, m):
        channel = ctx.channel
        author = ctx.author
        guild = ctx.guild
        charEmbed = discord.Embed ()
        charRecords, charEmbedmsg = await checkForChar(ctx, char, charEmbed)

        if charRecords:
            if 'Death' in charRecords:
                await channel.send(f"You cannot unattune from items with a dead character. Use the following command to decide their fate:\n```yaml\n$death \"{charRecords['Name']}\"```")
                return

            if "Attuned" not in charRecords:
                await channel.send(f"You have no attuned items to unattune from.")
                return
            else:
                attuned = charRecords['Attuned'].split(', ')

            charID = charRecords['_id']

            def apiEmbedCheck(r, u):
                sameMessage = False
                if charEmbedmsg.id == r.message.id:
                    sameMessage = True
                return sameMessage and ((r.emoji in numberEmojis[:min(len(mList), 9)]) or (str(r.emoji) == '❌')) and u == author

            mList = []
            mString = ""
            numI = 0

            # Filter through attuned items, some attuned items have [STAT +X]; filter out those too and get raw.
            for k in charRecords['Attuned'].split(', '):
                print(k.lower().split(' [')[0])
                if m.lower() in k.lower().split(' [')[0]:
                    mList.append(k.lower().split(' [')[0])
                    mString += f"{numberEmojis[numI]} {k} \n"
                    numI += 1
                if numI > 8:
                    break

            if (len(mList) > 1):
                charEmbed.add_field(name=f"There seems to be multiple results for `{m}`, please choose the correct one.\nIf the result you are looking for is not here, please cancel the command with ❌ and be more specific.", value=mString, inline=False)
                if not charEmbedmsg:
                    charEmbedmsg = await channel.send(embed=charEmbed)
                else:
                    await charEmbedmsg.edit(embed=charEmbed)

                await charEmbedmsg.add_reaction('❌')

                try:
                    tReaction, tUser = await self.bot.wait_for("reaction_add", check=apiEmbedCheck, timeout=60)
                except asyncio.TimeoutError:
                    await charEmbedmsg.delete()
                    await channel.send('Timed out! Try using the command again.')
                    ctx.command.reset_cooldown(ctx)
                    return None, charEmbed, charEmbedmsg
                else:
                    if tReaction.emoji == '❌':
                        await charEmbedmsg.edit(embed=None, content=f"Command cancelled. Try using the command again.")
                        await charEmbedmsg.clear_reactions()
                        ctx.command.reset_cooldown(ctx)
                        return None,charEmbed, charEmbedmsg
                charEmbed.clear_fields()
                await charEmbedmsg.clear_reactions()
                m = mList[int(tReaction.emoji[0]) - 1]

            elif len(mList) == 1:
                m = mList[0]
            else:
                await channel.send(f'`{m}` doesn\'t exist on the Magic Item Table! Check to see if it is a valid item and check your spelling.')
                return

            mRecord, charEmbed, charEmbedmsg = await callAPI(ctx, charEmbed, charEmbedmsg,'mit', m, True)
            if not mRecord:
                mRecord, charEmbed, charEmbedmsg = await callAPI(ctx, charEmbed, charEmbedmsg,'rit', m, True)
                if not mRecord:
                    await channel.send(f"`{m}` does not exist on the Magic Item Table.")
                    return

            if mRecord['Name'] not in [a.split(' [')[0] for a in attuned]:
                await channel.send(f"**{mRecord['Name']}** cannot be unattuned from because it is currently not attuned to you.")
                return
            else:
                if mRecord['Name'] == 'Hammer of Thunderbolts':
                    statSplit = mRecord['Stat Bonuses'].split(' +')
                    maxSplit = statSplit[0].split(' ')
                    if "MAX" in statSplit[0]:
                        charRecords['Max Stats'][maxSplit[1]] -= int(statSplit[1]) 

                if 'Stat Bonuses' in mRecord:
                    attuned.remove(f"{mRecord['Name']} [{mRecord['Stat Bonuses']}]") 
                else:
                    attuned.remove(mRecord['Name']) 
                  
                charRecords['Attuned'] = ', '.join(attuned)

                try:
                    playersCollection = db.players
                    if attuned != list():
                        playersCollection.update_one({'_id': charID}, {"$set": charRecords})
                    else:
                        playersCollection.update_one({'_id': charID}, {"$unset": {"Attuned":1}})

                except Exception as e:
                    print ('MONGO ERROR: ' + str(e))
                    charEmbedmsg = await channel.send(embed=None, content="Uh oh, looks like something went wrong. Please try creating your character again.")
                else:
                    await channel.send(f"You successfully unattuned from **{mRecord['Name']}**!")
                    

    @commands.command()
    @commands.cooldown(1, 5, type=commands.BucketType.member)
    async def stats(self,ctx):                
        statsCollection = db.stats
        currentDate = datetime.now().strftime("%b-%y")
        statRecords = statsCollection.find_one({"Date": currentDate})
        statRecordsLife = statsCollection.find_one({"Life": 1})
        guild=ctx.guild

        statsEmbed = discord.Embed()

        statsEmbed.title = f'Stats for {currentDate}' 

        statsTotalString = ""
        guildsString = ""
        superTotal = 0
        avgString = ""
        statsString = ""
        charString = ""
        raceString = ""
        bgString = ""

        for k,v in statRecords['DM'].items():
            statsString += guild.get_member(int(k)).display_name + " - "
            for i in range (1,5):
                if f'T{i}' not in v:
                    statsString += f"T{i}:0 / "
                else:
                    statsString += f"T{i}:{v[f'T{i}']} / " 
            for vk, vv in v.items():
                totalGames = 0
                totalGames += vv
                statsString += f"Total:{totalGames}\n"
                superTotal += totalGames

        if 'GQ' in statRecords:
            guildsString += f'Guild quests out of total quests: {round((statRecords["GQ"] / superTotal),2) * 100}%\n'
            guildsString += f"Guild Quests: {statRecords['GQ']}\n"
        else:
            guildsString += f"Guild Quests: 0\n"

        if 'GQM' in statRecords:
            guildsString += f"Guild Quests with Members: {statRecords['GQM']}\n"

        else:
            guildsString += f"Guild Quests with Members: 0\n"


        if 'GQNM' in statRecords:
            guildsString += f"Guild Quests with no Members: {statRecords['GQNM']}\n"
        else:
            guildsString += f"Guild Quests with no Members: 0\n"
            

        if guildsString:
            statsEmbed.add_field(name="Guild Games", value=guildsString, inline=False) 

        if 'Players' in statRecords and 'Playtime' in statRecords:
            avgString += f"Average Number of Player per Game: {sum(statRecords['Players']) / len(statRecords['Players'])}\n" 
            avgString += f"Average Game Time: {timeConversion(sum(statRecords['Playtime']) / len(statRecords['Playtime']))}\n"
            statsEmbed.add_field(name="Averages", value=avgString, inline=False) 

        if statsString:
            statsEmbed.add_field(name="DM Games", value=statsString, inline=False)

        for k, v in statRecordsLife['Class'].items():
            charString += f"{k}:{v['Count']}\n"
            for vk, vv in v.items():
                if vk != 'Count':
                    charString += f"• {vk}:{vv}\n"
            charString += f"━━━━━\n"

        for k, v in statRecordsLife['Race'].items():
            raceString += f"{k}:{v}\n"

        for k, v in statRecordsLife['Background'].items():
            bgString += f"{k}:{v}\n"
            

        statsEmbed.add_field(name="Character Class Stats (Lifetime)", value=charString, inline=False)  
        statsEmbed.add_field(name="Character Race Stats (Lifetime)", value=raceString, inline=False)  
        statsEmbed.add_field(name="Character Background Stats (Lifetime)", value=bgString, inline=False)  


        statsTotalString += f"Total Games for the Month: {superTotal}\n"
        for i in range (1,5):
            if f'T{i}' not in statRecords:
                statsTotalString += f"Tier {i} Games for the Month: 0\n"
            else: 
                statsTotalString += f"Tier {i} Games for the Month: {statRecords[f'T{i}']}\n"


        if 'Players' in statRecords and 'Playtime' in statRecords:
            statsTotalString += f"Total Hours Played: {timeConversion(sum(statRecords['Playtime']))}\n"
            statsTotalString += f"Total Number of Players: {sum(statRecords['Players'])}\n"
        if 'Unique Players' in statRecords and 'Playtime' in statRecords:
            statsTotalString += f"Number of Unique Players: {len(statRecords['Unique Players'])}\n"

        statsEmbed.description = statsTotalString

        await ctx.channel.send(embed=statsEmbed)

    async def calcHP (self, ctx, classes, charDict, lvl):
        # classes = sorted(classes, key = lambda i: i['Hit Die Max'],reverse=True) 
        totalHP = 0
        totalHP += classes[0]['Hit Die Max']
        currentLevel = 1

        for c in classes:
            classLevel = int(c['Level'])
            while currentLevel < classLevel:
                totalHP += c['Hit Die Average']
                currentLevel += 1
            currentLevel = 0

        totalHP += ((int(charDict['CON']) - 10) // 2 ) * lvl

        specialCollection = db.special
        specialRecords = list(specialCollection.find())

        for s in specialRecords:
            if s['Type'] == "Race" or s['Type'] == "Class" or s['Type'] == "Feats" or s['Type'] == "Magic Items":
                if s['Name'] in charDict[s['Type']]:
                    if 'HP' in s:
                        totalHP += s['HP'] * lvl

        return totalHP

    async def pointBuy(self,ctx, statsArray, rRecord, charEmbed, charEmbedmsg):
        author = ctx.author
        channel = ctx.channel
        def anyCharEmbedcheck(r, u):
            sameMessage = False
            if charEmbedmsg.id == r.message.id:
                sameMessage = True
            if (r.emoji in uniqueReacts or r.emoji == '❌') and u == author:
                anyList[charEmbedmsg.id].add(r.emoji)
            print(anyList)

            return sameMessage and ((len(anyList[charEmbedmsg.id]) == anyCheck) or str(r.emoji) == '❌') and u == author

        def slashCharEmbedcheck(r, u):
            sameMessage = False
            if charEmbedmsg.id == r.message.id:
                sameMessage = True
            return sameMessage and ((r.emoji in numberEmojis[:len(statSplit)]) or (str(r.emoji) == '❌')) and u == author

        if rRecord:
            statsBonus = rRecord['Modifiers'].replace(" ", "").split(',')
            uniqueArray = ['STR', 'DEX', 'CON', 'INT', 'WIS', 'CHA']
            allStatsArray = ['STR', 'DEX', 'CON', 'INT', 'WIS', 'CHA']
            for s in statsBonus:
                if '/' in s:
                    statSplit = s[:len(s)-2].replace(" ", "").split('/')
                    statSplitString = ""
                    for num in range(len(statSplit)):
                        statSplitString += f'{numberEmojis[num]}: {statSplit[num]}\n'
                    try:
                        charEmbed.add_field(name=f"The {rRecord['Name']} race lets you choose between {s}. React [1-{len(statSplit)}] below with the stat you chose.", value=statSplitString, inline=False)
                        if charEmbedmsg:
                            await charEmbedmsg.edit(embed=charEmbed)
                        else: 
                            charEmbedmsg = await channel.send(embed=charEmbed)
                        for num in range(0,len(statSplit)): await charEmbedmsg.add_reaction(numberEmojis[num])
                        await charEmbedmsg.add_reaction('❌')
                        tReaction, tUser = await self.bot.wait_for("reaction_add", check=slashCharEmbedcheck, timeout=60)
                    except asyncio.TimeoutError:
                        await charEmbedmsg.delete()
                        await channel.send(f'Character creation timed out! Try again using the same command:\n```yaml\n{commandPrefix}create "character name" level "race" "class" "background" STR DEX CON INT WIS CHA "magic item1, magic item2, [...]" "reward item1, reward item2, [...]"```')
                        self.bot.get_command(ctx.invoked_with).reset_cooldown(ctx)
                        return None, None
                    else:
                        if tReaction.emoji == '❌':
                            await charEmbedmsg.edit(embed=None, content=f"Character creation cancelled. Try again using the same command:\n```yaml\n{commandPrefix}char {ctx.invoked_with}```")
                            await charEmbedmsg.clear_reactions()
                            self.bot.get_command(ctx.invoked_with).reset_cooldown(ctx)
                            return None, None
                    await charEmbedmsg.clear_reactions()
                    s = statSplit[int(tReaction.emoji[0]) - 1] + s[-2:]

                if 'STR' in s:
                    statsArray[0] -= int(s[len(s)-1]) if s[len(s)-2] == "+" else int("-" + s[len(s)-1])
                    uniqueArray.remove('STR')
                elif 'DEX' in s:
                    statsArray[1] -= int(s[len(s)-1]) if s[len(s)-2] == "+" else int("-" + s[len(s)-1])
                    uniqueArray.remove('DEX')
                elif 'CON' in s:
                    statsArray[2] -= int(s[len(s)-1]) if s[len(s)-2] == "+" else int("-" + s[len(s)-1])
                    uniqueArray.remove('CON')
                elif 'INT' in s:
                    statsArray[3] -= int(s[len(s)-1]) if s[len(s)-2] == "+" else int("-" + s[len(s)-1])
                    uniqueArray.remove('INT')
                elif 'WIS' in s:
                    statsArray[4] -= int(s[len(s)-1]) if s[len(s)-2] == "+" else int("-" + s[len(s)-1])
                    uniqueArray.remove('WIS')
                elif 'CHA' in s:
                    statsArray[5] -= int(s[len(s)-1]) if s[len(s)-2] == "+" else int("-" + s[len(s)-1])
                    uniqueArray.remove('CHA')

                elif 'AOU' in s or 'ANY' in s:
                    try:
                        anyList = dict()
                        anyCheck = int(s[len(s)-1])
                        anyList = {charEmbedmsg.id:set()}
                            
                        uniqueStatStr = ""
                        uniqueReacts = []

                        if 'ANY' in s:
                            uniqueArray = ['STR', 'DEX', 'CON', 'INT', 'WIS', 'CHA']

                        for u in range(0,len(uniqueArray)):
                            uniqueStatStr += f'{numberEmojis[u]}: {uniqueArray[u]}\n'
                            uniqueReacts.append(numberEmojis[u])

                        charEmbed.add_field(name=f"The {rRecord['Name']} race lets you choose {anyCheck} extra stats. React below with the stat(s) you chose.", value=uniqueStatStr, inline=False)
                        if charEmbedmsg:
                            await charEmbedmsg.edit(embed=charEmbed)
                        else: 
                            charEmbedmsg = await channel.send(embed=charEmbed)
                        for num in range(0,len(uniqueArray)): await charEmbedmsg.add_reaction(numberEmojis[num])
                        await charEmbedmsg.add_reaction('❌')
                        tReaction, tUser = await self.bot.wait_for("reaction_add", check=anyCharEmbedcheck, timeout=60)
                    except asyncio.TimeoutError:
                        await charEmbedmsg.delete()
                        await channel.send(f'Point buy timed out! Try again using the same command:\n```yaml\n{commandPrefix}create "character name" level "race" "class" "background" STR DEX CON INT WIS CHA "magic item1, magic item2, [...]" "reward item1, reward item2, [...]"```')
                        self.bot.get_command(ctx.invoked_with).reset_cooldown(ctx)
                        return None, None

                    else:
                        if tReaction.emoji == '❌':
                            await charEmbedmsg.edit(embed=None, content=f'Point buy timed out! Try again using the same command:\n```yaml\n{commandPrefix}create "character name" level "race" "class" "background" STR DEX CON INT WIS CHA "magic item1, magic item2, [...]" "reward item1, reward item2, [...]"```')
                            await charEmbedmsg.clear_reactions()
                            self.bot.get_command(ctx.invoked_with).reset_cooldown(ctx)
                            return None, None 

                    charEmbed.clear_fields()
                    await charEmbedmsg.clear_reactions()
                    if 'AOU' in s:
                        for s in anyList[charEmbedmsg.id]:
                            statsArray[allStatsArray.index(uniqueArray[int(s[0]) - 1])] -= 1
                    else:

                        for s in anyList[charEmbedmsg.id]:
                            statsArray[(int(s[0]) - 1)] -= 1
                    
            return statsArray, charEmbedmsg

    async def chooseSubclass(self, ctx, subclassesList, charClass, charEmbed, charEmbedmsg):
        author = ctx.author
        channel = ctx.channel
        def classEmbedCheck(r, u):
            sameMessage = False
            if charEmbedmsg.id == r.message.id:
                sameMessage = True
            return sameMessage and ((r.emoji in alphaEmojis[:alphaIndex]) or (str(r.emoji) == '❌')) and u == author

        try:
            subclassString = ""
            for num in range(len(subclassesList)):
                subclassString += f'{alphaEmojis[num]}: {subclassesList[num]}\n'

            charEmbed.clear_fields()
            charEmbed.add_field(name=f"The {charClass} class allows you to pick a subclass at this level. React to the choices below to select your subclass.", value=subclassString, inline=False)
            alphaIndex = len(subclassesList)
            if charEmbedmsg:
                await charEmbedmsg.edit(embed=charEmbed)
            else: 
                charEmbedmsg = await channel.send(embed=charEmbed)
            await charEmbedmsg.add_reaction('❌')
            tReaction, tUser = await self.bot.wait_for("reaction_add", check=classEmbedCheck, timeout=60)
        except asyncio.TimeoutError:
            await charEmbedmsg.delete()
            await channel.send(f'Character creation timed out! Try again using the same command:\n```yaml\n{commandPrefix}create "character name" level "race" "class" "background" STR DEX CON INT WIS CHA "magic item1, magic item2, [...]" "reward item1, reward item2, [...]"```')
            self.bot.get_command(ctx.invoked_with).reset_cooldown(ctx)
            return None, None
        else:
            if tReaction.emoji == '❌':
                await charEmbedmsg.edit(embed=None, content=f"Character creation cancelled. Try again using the same command:\n```yaml\n{commandPrefix}create \"character name\" level \"race\" \"class\" \"background\" STR DEX CON INT WIS CHA \"magic item1, magic item2, [...]\" \"reward item1, reward item2, [...]\"```")
                await charEmbedmsg.clear_reactions()
                self.bot.get_command(ctx.invoked_with).reset_cooldown(ctx)
                return None, None
        await charEmbedmsg.clear_reactions()
        charEmbed.clear_fields()
        choiceIndex = alphaEmojis.index(tReaction.emoji)
        subclass = subclassesList[choiceIndex].strip()

        return subclass, charEmbedmsg

    async def chooseFeat (self, ctx, race, charClass, cRecord, featLevels, charEmbed,  charEmbedmsg, charStats, charFeats):
        statNames = ['STR','DEX','CON','INT','WIS','CHA']
        author = ctx.author
        channel = ctx.channel

        def featCharEmbedCheck(r, u):
            sameMessage = False
            if charEmbedmsg.id == r.message.id:
                sameMessage = True
            return sameMessage and ((r.emoji in numberEmojis[:2]) or (str(r.emoji) == '❌')) and u == author
        
        def asiCharEmbedCheck(r, u):
            sameMessage = False
            if charEmbedmsg.id == r.message.id:
                sameMessage = True
            return sameMessage and ((r.emoji in alphaEmojis[:asiIndex]) or (str(r.emoji) == '❌')) and u == author

        def asiCharEmbedCheck2(r, u):
            sameMessage = False
            if charEmbedmsg2.id == r.message.id:
                sameMessage = True
            return sameMessage and ((r.emoji in alphaEmojis[:asiIndex]) or (str(r.emoji) == '❌')) and u == author


        featChoices = []
        featsPickedList = []
        featsChosen = ""
        featsCollection = db.feats

        if 'Max Stats' not in charStats:
            charStats['Max Stats'] = {'STR':20, 'DEX':20, 'CON':20, 'INT':20, 'WIS':20, 'CHA':20}

        spellcasting = False
        for f in featLevels:
                charEmbed.clear_fields()
                if f != 'Human (Variant)':
                    try:
                        charEmbed.add_field(name=f"Your level allows you to pick an Ability Score Improvement or a feat. Please react with 1 or 2 for your level {f} ASI/feat.", value=f"{numberEmojis[0]}: Ability Score Improvement\n{numberEmojis[1]}: Feat\n", inline=False)
                        if charEmbedmsg:
                            await charEmbedmsg.edit(embed=charEmbed)
                        else: 
                            charEmbedmsg = await channel.send(embed=charEmbed)
                        for num in range(0,2): await charEmbedmsg.add_reaction(numberEmojis[num])
                        await charEmbedmsg.add_reaction('❌')
                        charEmbed.set_footer(text= "React with ❌ to cancel.\nPlease react with a choice even if no reactions appear.")

                        tReaction, tUser = await self.bot.wait_for("reaction_add", check=featCharEmbedCheck, timeout=60)
                    except asyncio.TimeoutError:
                        await charEmbedmsg.delete()
                        await channel.send(f'Feat selection timed out! Try again using the same command:\n```yaml\n{commandPrefix}create "character name" level "race" "class" "background" STR DEX CON INT WIS CHA "magic item1, magic item2, [...]" "reward item1, reward item2, [...]"```')
                        self.bot.get_command(ctx.invoked_with).reset_cooldown(ctx)
                        return None, None, None
                    else:
                        if tReaction.emoji == '❌':
                            await charEmbedmsg.edit(embed=None, content=f"Feat selection cancelled.  Try again using the same command:\n```yaml\n{commandPrefix}create \"character name\" level \"race\" \"class\" \"background\" STR DEX CON INT WIS CHA \"magic item1, magic item2, [...]\" \"reward item1, reward item2, [...]\"```")
                            await charEmbedmsg.clear_reactions()
                            self.bot.get_command(ctx.invoked_with).reset_cooldown(ctx)
                            return None, None, None

                    choice = int(tReaction.emoji[0])
                    await charEmbedmsg.clear_reactions()

                if f == 'Human (Variant)':
                    choice = 2

                if choice == 1:
                    try:
                        charEmbed.clear_fields()    
                        statsString = ""
                        asiString = ""
                        asiList = []
                        asiIndex = 0
                        for n in range(0,6):
                            if (int(charStats[statNames[n]]) + 1 <= charStats['Max Stats'][statNames[n]]):
                                statsString += f"{statNames[n]}: **{charStats[statNames[n]]}** "
                                asiString += f"{alphaEmojis[asiIndex]}: {statNames[n]}\n"
                                asiList.append(statNames[n])
                                asiIndex += 1
                            else:
                                statsString += f"{statNames[n]}: **{charStats[statNames[n]]}** (MAX) "

                        charEmbed.add_field(name=f"{statsString}\nReact to choose your first stat for your ASI:", value=asiString, inline=False)
                        await charEmbedmsg.edit(embed=charEmbed)
                        await charEmbedmsg.add_reaction('❌')
                        tReaction, tUser = await self.bot.wait_for("reaction_add", check=asiCharEmbedCheck, timeout=60)
                    except asyncio.TimeoutError:
                        await charEmbedmsg.delete()
                        await channel.send(f'Character creation timed out! Try again using the same command:\n```yaml\n{commandPrefix}create "character name" level "race" "class" "background" STR DEX CON INT WIS CHA "magic item1, magic item2, [...]" "reward item1, reward item2, [...]"```')
                        self.bot.get_command(ctx.invoked_with).reset_cooldown(ctx)
                        return None, None, None
                    else:
                        if tReaction.emoji == '❌':
                            await charEmbedmsg.edit(embed=None, content=f"Character creation cancelled. Try again using the same command:\n```yaml\n{commandPrefix}create \"character name\" level \"race\" \"class\" \"background\" STR DEX CON INT WIS CHA \"magic item1, magic item2, [...]\" \"reward item1, reward item2, [...]\"```")
                            await charEmbedmsg.clear_reactions()
                            self.bot.get_command(ctx.invoked_with).reset_cooldown(ctx)
                            return None, None, None
                    asi = alphaEmojis.index(tReaction.emoji)

                    # May not need this at all due to choice omitting maxes
                    # if (int(charStats[statNames[asi]]) + 1 > charStats['Max Stats'][statNames[asi]]):
                    #     await charEmbedmsg.delete()
                    #     await channel.send(f"You cannot increase your character's {statNames[asi]} above your maximum of {charStats['Max Stats'][statNames[asi]]}. Please try creating your character again.")
                    #     self.bot.get_command(ctx.invoked_with).reset_cooldown(ctx)
                    #     return None, None, None

                    charStats[asiList[asi]] = int(charStats[asiList[asi]]) + 1
                    charEmbed.set_field_at(0,name=f"ASI First Stat", value=f"{alphaEmojis[asi]}: {statNames[asi]}", inline=False)
                    if ctx.invoked_with == "levelup":
                         charEmbed.description = f"{race}: {charClass}\n**STR**:{charStats['STR']} **DEX**:{charStats['DEX']} **CON**:{charStats['CON']} **INT**:{charStats['INT']} **WIS**:{charStats['WIS']} **CHA**:{charStats['CHA']}"

                    try:
                        statsString = ""
                        asiString = ""
                        asiIndex = 0
                        asiList = []
                        for n in range(0,6):
                            if (int(charStats[statNames[n]]) + 1 <= charStats['Max Stats'][statNames[n]]):
                                statsString += f"{statNames[n]}: **{charStats[statNames[n]]}** "
                                asiString += f"{alphaEmojis[asiIndex]}: {statNames[n]}\n"
                                asiList.append(statNames[n])
                                asiIndex += 1
                            else:
                                statsString += f"{statNames[n]}: **{charStats[statNames[n]]}** (MAX) "
                            
                        charEmbed.add_field(name=f"{statsString}\nReact to choose your second stat for your ASI:", value=asiString, inline=False)
                        charEmbedmsg2 = await channel.send(embed=charEmbed)
                        await charEmbedmsg2.add_reaction('❌')
                        tReaction, tUser = await self.bot.wait_for("reaction_add", check=asiCharEmbedCheck2, timeout=60)
                    except asyncio.TimeoutError:
                        await charEmbedmsg2.delete()
                        await channel.send(f'Character creation timed out! Try again using the same command:\n```yaml\n{commandPrefix}create "character name" level "race" "class" "background" STR DEX CON INT WIS CHA "magic item1, magic item2, [...]" "reward item1, reward item2, [...]"```')
                        self.bot.get_command(ctx.invoked_with).reset_cooldown(ctx)
                        return None, None, None
                    else:
                        if tReaction.emoji == '❌':
                            await charEmbedmsg.edit(embed=None, content=f"Character creation cancelled. Try again using the same command:\n```yaml\n{commandPrefix}create \"character name\" level \"race\" \"class\" \"background\" STR DEX CON INT WIS CHA \"magic item1, magic item2, [...]\" \"reward item1, reward item2, [...]\"```")
                            await charEmbedmsg.clear_reactions()
                            await charEmbedmsg2.delete()
                            self.bot.get_command(ctx.invoked_with).reset_cooldown(ctx)
                            return None, None, None
                    asi = alphaEmojis.index(tReaction.emoji)

                    # May not need this at all due to choice omitting maxes
                    # if (int(charStats[statNames[asi]]) + 1 > charStats['Max Stats'][statNames[asi]]):
                    #     await channel.send(f"You cannot increase your character's {statNames[asi]} above your MAX {charStats['Max Stats'][statNames[asi]]}. Please try creating your character again.")
                    #     self.bot.get_command(ctx.invoked_with).reset_cooldown(ctx)
                    #     return None, None, None

                    charStats[asiList[asi]] = int(charStats[asiList[asi]]) + 1
                    if ctx.invoked_with == "levelup":
                         charEmbed.description = f"{race}: {charClass}\n**STR**: {charStats['STR']} **DEX**: {charStats['DEX']} **CON**: {charStats['CON']} **INT**: {charStats['INT']} **WIS**: {charStats['WIS']} **CHA**: {charStats['CHA']}"
                    await charEmbedmsg2.delete()
                    await charEmbedmsg.clear_reactions()

                elif choice == 2:
                    if featChoices == list():
                        fRecords, charEmbed, charEmbedmsg = await callAPI(ctx, charEmbed, charEmbedmsg,'feats')
                        for feat in fRecords:
                            featList = []
                            meetsRestriction = False

                            if 'Race Restriction' not in feat and 'Class Restriction' not in feat and 'Stat Restriction' not in feat and feat['Name'] not in charFeats and 'Race Unavailable' not in feat and 'Require Spellcasting' not in feat:
                                featChoices.append(feat)

                            else:
                                if 'Race Restriction' in feat:
                                    featsList = [x.strip() for x in feat['Race Restriction'].split(', ')]

                                    for f in featsList:
                                        if f in race:
                                            meetsRestriction = True

                                if 'Race Unavailable' in feat:
                                    if race not in feat['Race Unavailable']:
                                        meetsRestriction = True

                                if 'Class Restriction' in feat:
                                    featsList = [x.strip() for x in feat['Class Restriction'].split(', ')]
                                    for c in cRecord:
                                        if ctx.invoked_with == "create" or ctx.invoked_with == "respec":
                                            if c['Class']['Name'] in featsList or c['Subclass'] in featsList:
                                                meetsRestriction = True
                                        else:
                                            if c['Name'] in featsList or c['Subclass'] in featsList:
                                                meetsRestriction = True
                                                
                                if 'Stat Restriction' in feat:
                                    s = feat['Stat Restriction']
                                    statNumber = int(s[-2:])
                                    if '/' in s:
                                        checkStat = s[:len(s)-2].replace(" ", "").split('/')
                                        statSplitString = ""
                                    else:
                                        checkStat = [s[:len(s)-2].strip()]

                                    for stat in checkStat:
                                        if int(charStats[stat]) >= statNumber:
                                            meetsRestriction = True

                                if "Require Spellcasting" in feat:
                                    for c in cRecord:
                                        if "Spellcasting" in c["Class"]:
                                            if c["Class"]["Spellcasting"] == True or c["Class"]["Spellcasting"] in charClass:
                                                meetsRestriction = True
                                    
                                    spellcastingFeats = list(featsCollection.find({"Spellcasting": True}))
                                    for f in spellcastingFeats:
                                        if f["Name"] in charFeats:
                                             meetsRestriction = True

                                if meetsRestriction:
                                    featChoices.append(feat)

                    # Whenever a feat that grants spellcasting gets picked.
                    elif spellcasting == True:
                        spellcastingFeats = list(featsCollection.find({"Require Spellcasting": True}))
                        for f in spellcastingFeats:
                            featChoices.append(f)
                    else:
                        featChoices.remove(featPicked)

                    def featChoiceCheck(r, u):
                        sameMessage = False
                        if charEmbedmsg.id == r.message.id:
                            sameMessage = True
                        return sameMessage and u == author and (r.emoji == left or r.emoji == right or r.emoji == '❌' or r.emoji == back or r.emoji in alphaEmojis[:alphaIndex])

                    page = 0
                    perPage = 24
                    numPages =((len(featChoices) - 1) // perPage) + 1
                    featChoices = sorted(featChoices, key = lambda i: i['Name']) 

                    while True:
                        charEmbed.clear_fields()  
                        if f == 'Human (Variant)':
                            charEmbed.add_field(name=f"The **Human (Variant)** race allows you to choose a feat. Please choose your feat from the list below.", value=f"-", inline=False)
                        else:
                            charEmbed.add_field(name=f"Please choose your feat from the list below:", value=f"━━━━━━━━━━━━━━━━━━━━", inline=False)

                        pageStart = perPage*page
                        pageEnd = perPage * (page + 1)
                        alphaIndex = 0
                        for i in range(pageStart, pageEnd if pageEnd < (len(featChoices) - 1) else (len(featChoices)) ):
                            charEmbed.add_field(name=alphaEmojis[alphaIndex], value=featChoices[i]['Name'], inline=True)
                            alphaIndex+=1
                        charEmbed.set_footer(text= f"Page {page+1} of {numPages} -- use {left} or {right} to navigate or ❌ to cancel.")
                        await charEmbedmsg.edit(embed=charEmbed) 
                        await charEmbedmsg.add_reaction(left) 
                        await charEmbedmsg.add_reaction(right)
                        # await charEmbedmsg.add_reaction(back)
                        await charEmbedmsg.add_reaction('❌')

                        try:
                            react, user = await self.bot.wait_for("reaction_add", check=featChoiceCheck, timeout=90.0)
                        except asyncio.TimeoutError:
                            await charEmbedmsg.delete()
                            await channel.send(f"Character creation timed out!")
                            self.bot.get_command(ctx.invoked_with).reset_cooldown(ctx)
                            return None, None, None
                        else:
                            if react.emoji == left:
                                page -= 1
                                if page < 0:
                                  page = numPages - 1
                            elif react.emoji == right:
                                page += 1
                                if page > numPages - 1: 
                                  page = 0
                            elif react.emoji == '❌':
                                await charEmbedmsg.edit(embed=None, content=f"Character creation cancelled. Try again using the same command:\n```yaml\n{commandPrefix}create \"character name\" level \"race\" \"class\" \"background\" STR DEX CON INT WIS CHA \"magic item1, magic item2, [...]\" \"reward item1, reward item2, [...]\"```")
                                await charEmbedmsg.clear_reactions()
                                self.bot.get_command(ctx.invoked_with).reset_cooldown(ctx)
                                return None, None, None
                            # elif react.emoji == back:
                            #     await charEmbedmsg.delete()
                            #     await ctx.reinvoke()
                            elif react.emoji in alphaEmojis:
                                await charEmbedmsg.clear_reactions()
                                break
                            charEmbed.clear_fields()
                            await charEmbedmsg.clear_reactions()
                    
                    featPicked = featChoices[(page * perPage) + alphaEmojis.index(react.emoji)]

                    # If feat picked grants spellcasting
                    if "Spellcasting" in featPicked:
                        spellcasting = True

                    featsPickedList.append(featPicked)

                    # Special Case of Picked Ritual Caster
                    def ritualFeatEmbedcheck(r, u):
                        sameMessage = False
                        if charEmbedmsg.id == r.message.id:
                            sameMessage = True
                        return sameMessage and ((r.emoji in alphaEmojis[:6]) or (str(r.emoji) == '❌')) and u == author

                    def ritualSpellEmbedCheck(r, u):
                        sameMessage = False
                        if charEmbedmsg.id == r.message.id:
                            sameMessage = True

                        if (r.emoji in alphaEmojis[:alphaIndex]) and u == author:
                            ritualChoiceList[charEmbedmsg.id].add(r.emoji)

                        print(ritualChoiceList)

                        return sameMessage and ((len(ritualChoiceList[charEmbedmsg.id]) == 2) or (str(r.emoji) == '❌')) and u == author

                    if featPicked['Name'] == "Ritual Caster":
                        ritualClasses = ["Bard", "Cleric", "Druid", "Sorcerer", "Warlock", "Wizard"]
                        charEmbed.clear_fields()
                        charEmbed.set_footer(text=charEmbed.Empty)
                        charEmbed.add_field(name="For the **Ritual Caster** feat, please pick the spellcasting class.", value=f"{alphaEmojis[0]}: Bard\n{alphaEmojis[1]}: Cleric\n{alphaEmojis[2]}: Druid\n{alphaEmojis[3]}: Sorcerer\n{alphaEmojis[4]}: Warlock\n{alphaEmojis[5]}: Wizard\n", inline=False)

                        try:
                            await charEmbedmsg.edit(embed=charEmbed)
                            await charEmbedmsg.add_reaction('❌')
                            tReaction, tUser = await self.bot.wait_for("reaction_add", check=ritualFeatEmbedcheck, timeout=60)
                        except asyncio.TimeoutError:
                            await charEmbedmsg.delete()
                            await channel.send(f'Character creation timed out! Try again using the same command:\n```yaml\n{commandPrefix}create "character name" level "race" "class" "background" STR DEX CON INT WIS CHA "magic item1, magic item2, [...]" "reward item1, reward item2, [...]"```')
                            self.bot.get_command(ctx.invoked_with).reset_cooldown(ctx)
                            return None, None, None
                        else:
                            if tReaction.emoji == '❌':
                                await charEmbedmsg.edit(embed=None, content=f"Character creation cancelled. Try again using the same command:\n```yaml\n{commandPrefix}create \"character name\" level \"race\" \"class\" \"background\" STR DEX CON INT WIS CHA \"magic item1, magic item2, [...]\" \"reward item1, reward item2, [...]\"```")
                                await charEmbedmsg.clear_reactions()
                                self.bot.get_command(ctx.invoked_with).reset_cooldown(ctx)
                                return None, None, None
                        await charEmbedmsg.clear_reactions()

                        ritualClass = ritualClasses[alphaEmojis.index(tReaction.emoji)]
                        featPicked['Name'] = f"{featPicked['Name']} ({ritualClass})"
                        spellsCollection = db.spells
                        ritualSpellsList = list(spellsCollection.find({"$and": [{"Classes": {"$regex": ritualClass, '$options': 'i' }}, {"Ritual": True}, {"Level": 1}] }))

                        alphaIndex = 0
                        ritualSpellsString = ""
                        for r in ritualSpellsList:
                            ritualSpellsString += f"{alphaEmojis[alphaIndex]}: {r['Name']}\n"
                            alphaIndex += 1

                        charEmbed.set_field_at(0, name=f"For the **Ritual Caster** feat, please pick the spellcasting class.", value=f"{tReaction.emoji}: {ritualClass}", inline=False)
                        charEmbed.add_field(name=f"Please pick two {ritualClass} spells from this list to add to your ritual book.", value=ritualSpellsString, inline=False)
                        ritualChoiceList = {charEmbedmsg.id:set()}

                        charStats['Ritual Book'] = []
                        if len(ritualSpellsList) > 2:
                            try:
                                await charEmbedmsg.edit(embed=charEmbed)
                                await charEmbedmsg.add_reaction('❌')
                                tReaction, tUser = await self.bot.wait_for("reaction_add", check=ritualSpellEmbedCheck, timeout=60)
                            except asyncio.TimeoutError:
                                await charEmbedmsg.delete()
                                await channel.send(f'Character creation timed out! Try again using the same command:\n```yaml\n{commandPrefix}create "character name" level "race" "class" "background" STR DEX CON INT WIS CHA "magic item1, magic item2, [...]" "reward item1, reward item2, [...]"```')
                                self.bot.get_command(ctx.invoked_with).reset_cooldown(ctx)
                                return None, None, None
                            else:
                                if tReaction.emoji == '❌':
                                    await charEmbedmsg.edit(embed=None, content=f"Character creation cancelled. Try again using the same command:\n```yaml\n{commandPrefix}create \"character name\" level \"race\" \"class\" \"background\" STR DEX CON INT WIS CHA \"magic item1, magic item2, [...]\" \"reward item1, reward item2, [...]\"```")
                                    await charEmbedmsg.clear_reactions()
                                    self.bot.get_command(ctx.invoked_with).reset_cooldown(ctx)
                                    return None, None, None
                            await charEmbedmsg.clear_reactions()
                            for r in ritualChoiceList[charEmbedmsg.id]:
                                rChoice = ritualSpellsList[alphaEmojis.index(r)]
                                charStats['Ritual Book'].append({'Name':rChoice['Name'], 'School':rChoice['School']})
                        else:
                            charStats['Ritual Book'].append({'Name':ritualSpellsList[0]['Name'], 'School':ritualSpellsList[0]['School']})
                            charStats['Ritual Book'].append({'Name':ritualSpellsList[1]['Name'], 'School':ritualSpellsList[1]['School']})
                        

                    def slashFeatEmbedcheck(r, u):
                        sameMessage = False
                        if charEmbedmsg.id == r.message.id:
                            sameMessage = True
                        return sameMessage and ((r.emoji in numberEmojis[:len(featBonusList)]) or (str(r.emoji) == '❌')) and u == author

                    if 'Stat Bonuses' in featPicked:
                        featBonus = featPicked['Stat Bonuses']
                        if '/' in featBonus or 'ANY' in featBonus:
                            if '/' in featBonus:
                                featBonusList = featBonus[:len(featBonus) - 3].split('/')
                            elif 'ANY' in featBonus:
                                featBonusList = statNames
                            featBonusString = ""
                            for num in range(len(featBonusList)):
                                featBonusString += f'{numberEmojis[num]}: {featBonusList[num]}\n'

                            try:
                                charEmbed.clear_fields()    
                                charEmbed.set_footer(text= charEmbed.Empty)
                                charEmbed.add_field(name=f"The {featPicked['Name']} feat lets you choose between {featBonus}. React with [1-{len(featBonusList)}] below with the stat you chose.", value=featBonusString, inline=False)
                                await charEmbedmsg.edit(embed=charEmbed)
                                for num in range(0,len(featBonusList)): await charEmbedmsg.add_reaction(numberEmojis[num])
                                await charEmbedmsg.add_reaction('❌')
                                tReaction, tUser = await self.bot.wait_for("reaction_add", check=slashFeatEmbedcheck, timeout=60)
                            except asyncio.TimeoutError:
                                await charEmbedmsg.delete()
                                await channel.send(f'Character creation timed out! Try again using the same command:\n```yaml\n{commandPrefix}create "character name" level "race" "class" "background" STR DEX CON INT WIS CHA "magic item1, magic item2, [...]" "reward item1, reward item2, [...]"```')
                                self.bot.get_command(ctx.invoked_with).reset_cooldown(ctx)
                                return None, None, None
                            else:
                                if tReaction.emoji == '❌':
                                    await charEmbedmsg.edit(embed=None, content=f"Character creation cancelled. Try again using the same command:\n```yaml\n{commandPrefix}create \"character name\" level \"race\" \"class\" \"background\" STR DEX CON INT WIS CHA \"magic item1, magic item2, [...]\" \"reward item1, reward item2, [...]\"```")
                                    await charEmbedmsg.clear_reactions()
                                    self.bot.get_command(ctx.invoked_with).reset_cooldown(ctx)
                                    return None, None, None
                            await charEmbedmsg.clear_reactions()
                            charStats[featBonusList[int(tReaction.emoji[0]) - 1]] = int(charStats[featBonusList[int(tReaction.emoji[0]) - 1]]) + int(featBonus[-1:])
                                
                        else:
                            featBonusList = featBonus.split(', ')
                            for fb in featBonusList:
                                charStats[fb[:3]] =  int(charStats[fb[:3]]) + int(fb[-1:])

                    if featsPickedList != list():
                        featsChosen = ', '.join(str(string['Name']) for string in featsPickedList)            

        if ctx.invoked_with == "levelup":
              charEmbed.description = f"{race}: {charClass}\n**STR**:{charStats['STR']} **DEX**:{charStats['DEX']} **CON**:{charStats['CON']} **INT**:{charStats['INT']} **WIS**:{charStats['WIS']} **CHA**:{charStats['CHA']}"

        return featsChosen, charStats, charEmbedmsg        


def setup(bot):
    bot.add_cog(Character(bot))
