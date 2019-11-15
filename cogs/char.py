import discord
import pytz
import re
import requests
import asyncio
from datetime import datetime, timezone, timedelta 
from discord.ext import commands
from bfunc import refreshKey, refreshTime, numberEmojis, alphaEmojis, commandPrefix, left,right,back

class Character(commands.Cog):
    def __init__ (self, bot):
        self.bot = bot

    @commands.group()
    async def char(self, ctx):	
        pass


    @commands.cooldown(1, float('inf'), type=commands.BucketType.user)
    @char.command()
    async def create(self,ctx, name, level, race, cclass, bg, sStr, sDex, sCon, sInt, sWis, sCha, mItems="", consumes=""):
        roleCreationDict = {
            'Journey Friend':[3],
            'Good Noodle':[4],
            'Elite Noodle':[4,5],
            'True Noodle':[4,5,6],
            'Mega Noodle':[4,5,6,8],
            'Guild Fanatic':[11],
        }
        headers = {
            "Authorization": "Bearer keyw9zLleR35sm21O",
            "Content-Type": "application/json"
        }
        roles = [r.name for r in ctx.author.roles]
        author = ctx.author
        guild = ctx.guild
        channel = ctx.channel
        charEmbed = discord.Embed ()
        charEmbed.set_author(name=ctx.author.display_name, icon_url=ctx.author.avatar_url)
        charEmbed.set_footer(text= "React with ❌ to cancel")
        charEmbedmsg = None
        statNames = ['STR','DEX','CON','INT','WIS','CHA']

        charDict = {
          'User ID': str(author.id),
          'Discord ID': f"{author.name}#{author.discriminator}",
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
          'Feats': 'None'
        }


        lvl = int(level)
        msg = ""
        # name should be less then 50 chars
        if len(name) > 64:
            msg += "- Your character's name is too long! The limit is 64 characters.\n"
        
        
        # level and role check
        roleSet = [1]
        for d in roleCreationDict.keys():
            if d in roles:
                roleSet += roleCreationDict[d]

        roleSet = set(roleSet)

        if "Nitro Booster" in roles:
            roleSet = roleSet.union(set(map(lambda x: x+1,roleSet.copy())))

        if lvl not in roleSet:
            msg += "- You cannot create a character of this level! You do not have the correct role!\n"
        

        # For API requests below
        def callAPI(table, query):
            if query == "":
                return False

            API_URL = ('https://api.airtable.com/v0/appF4hiT6A0ISAhUu/'+ table +'?&filterByFormula=(FIND(LOWER(SUBSTITUTE("' + query.replace(" ", "%20") + '"," ","")),LOWER(SUBSTITUTE({Name}," ",""))))').replace("+", "%2B") 
            r = requests.get(API_URL, headers=headers)
            r = r.json()

            if r['records'] == list():
                return False
            else:
                if (len(r['records']) > 1):
                    if table == 'Races' or table == "Background":
                        for x in r['records']:
                            print(x['fields']['Name'])
                            print(query)
                            if len(x['fields']['Name'].replace(" ", "")) == len(query.replace(" ", "")):
                                return x['fields']

                    if table == 'RIT':
                        minimum = {'fields': {'Tier': 0}}
                        for x in r['records']:
                            if int(x['fields']['Tier']) > int(minimum['fields']['Tier']):
                                min = x
                        
                        return min['fields']

                else:
                    return r['records'][0]['fields']
        # CP
        if lvl < 5:
            maxCP = 4
        else:
            maxCP = 8
        charDict['CP'] = f"0/{maxCP}"
        
        # check magic items and TP
        magicItems = mItems.split(',')
        allMagicItemsString = []
        if lvl > 1 and magicItems != ['']:
            for m in magicItems:
                mRecord = callAPI('MIT',m) 
                if mRecord in allMagicItemsString:
                    msg += '- You cannot spend TP on two of the same magic item.\n'
                    break 
                if not mRecord:
                    msg += '- One or more magic items don\'t exist! Check to see if it\'s on the MIT and check your spelling.\n'
                    break
                else:
                    allMagicItemsString.append(mRecord)


            def calculateMagicItems(lvl):
                bankTP1 = 0
                bankTP2 = 0
                highestTier = 0
                magicItemsCurrent = []
                magicItemsBought = []
                if lvl > 1 and lvl < 6: 
                    bankTP1 = (lvl-1) * 2 
                    highestTier = 1
                elif lvl > 5:
                    bankTP1 = 8;
                    bankTP2 = (lvl-5) * 4
                    highestTier = 2
                
                magicItemsTier2 = []

                for item in allMagicItemsString:
                    if int(item['Tier']) > highestTier:
                        return "- One or more of these magic items cannot be purchased at Level " + str(lvl)
                        
                    else:
                        costTP = int(item['TP'])
                        if int(item['Tier']) == 2:
                            magicItemsTier2.append(item)
                            continue
                        else:
                            bankTP1 = costTP - bankTP1
                            if bankTP1 > 0:
                              magicItemsCurrent.append(item)                       
                              magicItemsCurrent.append(f'{costTP - bankTP1}/{costTP}')
                              charDict['Current Item'] = f'{magicItemsCurrent[0]["Name"]} ({magicItemsCurrent[1]})'
                            else:
                              bankTP1 = abs(bankTP1)
                              magicItemsBought.append(item)


                for item in magicItemsTier2:
                    if magicItemsCurrent:
                        magicItemsCurrentItem = magicItemsCurrent[1].split('/')
                        bankTP2 = int(magicItemsCurrentItem[1]) - int(magicItemsCurrentItem[0]) - bankTP2
                        if bankTP2 > 0:
                            magicItemsCurrent[1] = f'{int(magicItemsCurrentItem[1]) - bankTP2}/{magicItemsCurrentItem[1]}'
                            charDict['Current Item'] = f'{magicItemsCurrent[0]["Name"]} ({magicItemsCurrent[1]})'
                        else:
                            bankTP2 = abs(bankTP2)
                            magicItemsBought.append(magicItemsCurrent[0])
                            magicItemsCurrent = []
                            charDict['Current Item'] = ""

                    if bankTP2 > 0:
                        costTP = int(item['TP'])
                        bankTP2 = costTP - bankTP2
                        if bankTP2 > 0:
                          magicItemsCurrent.append(item)                       
                          magicItemsCurrent.append(f'{costTP - bankTP2}/{costTP}')
                          charDict['Current Item'] = f'{magicItemsCurrent[0]["Name"]} ({magicItemsCurrent[1]})'
                        else:
                          bankTP2 = abs(bankTP2)
                          magicItemsBought.append(item)

                return magicItemsBought

            magicItemsBought = calculateMagicItems(lvl)
            print(magicItemsBought)
            if isinstance(magicItemsBought, str):
                msg += magicItemsBought
            elif magicItemsBought == list():
                pass
            else:
                charDict['Magic Items'] = ', '.join([str(string['Name']) for string in magicItemsBought])
        elif lvl > 1 and magicItems == ['']:
            msg += 'In order to create your character at this level, you must purchase magic item(s) with your TP\n' 
        elif lvl == 1 and magicItems != ['']:
            msg += 'You cannot purchase magic items at Level 1\n'

          
        print(allMagicItemsString)

        #check reward items
        rewardItems = consumes.split(',')
        allRewardItemsString = []
        if lvl > 3 and rewardItems != ['']:
            for r in rewardItems:
                reRecord = callAPI('RIT',r) 
                if not reRecord:
                    msg += '- One or more reward items don\'t exist! Check to see if it\'s on the RIT and check your spelling.\n'
                    break
                else:
                    allRewardItemsString.append(reRecord)

            tier1CountMNC = 0
            tier1Count = 0
            tier2Count = 0
            rewardConsumables = []
            rewardMagics = []
            tier2Rewards = []

            print(allRewardItemsString)

            if lvl == 4:
                tier1Count = 1
            elif lvl == 5:
                tier2Count = 1
                tier1CountMNC = 1
            elif lvl == 6:
                tier1CountMNC = 1
                tier1Count = 1
                tier2Count = 1
            elif lvl == 8:
                tier1CountMNC = 1
                tier1Count = 2
                tier2Count = 2
            elif lvl == 11:
                if 'Good Noodle' in roles:
                    tier1Count = 1
                elif 'Elite Noodle' in roles:
                    tier2Count = 1
                    tier1CountMNC = 1
                elif 'True Noodle' in roles:
                    tier1CountMNC = 1
                    tier1Count = 1
                    tier2Count = 1
                elif 'Mega Noodle' in roles:
                    tier1CountMNC = 1
                    tier1Count = 2
                    tier2Count = 2

            if 'Nitro Booster' in roles:
                tier1CountMNC += 1

            for item in allRewardItemsString:
                if int(item['Tier']) > 2:
                    msg += "- One or more of these reward items cannot be purchased at Level " + str(lvl) + "\n"
                    break

                if lvl > 4 and item['Minor/Major'] == 'Minor' and 'Consumable' not in item and tier1CountMNC > 0:
                    tier1CountMNC -= 1
                elif int(item['Tier']) == 1:
                    tier1Count -= 1
                elif int(item['Tier']) == 2:
                    tier2Rewards.append(item)
    
                if int(item['Tier']) == 1:
                    if 'Consumable' in item:
                        rewardConsumables.append(item) 
                    else:
                        rewardMagics.append(item)

            print(tier2Rewards)
            for item in tier2Rewards:
                if tier1Count > 0 and tier2Count <= 0:
                    tier1Count -= 1
                else:
                    tier2Count -= 1
                rewardConsumables.append(item)


            if tier1CountMNC < 0 or tier1Count < 0 or tier2Count < 0:
                msg += "- You do not have the right roles for these reward items\n"
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

            print(tier1CountMNC)
            print(tier1Count)
            print(tier2Count)
            
        # check race
        rRecord = callAPI('Races',race)
        if not rRecord:
            msg += '- That race isn\'t on the list or it is banned! Check #allowed-and-banned-content and check your spelling.\n'
        else:
            charDict['Race'] = rRecord['Name']
        
        # check class
        cRecord = []
        totalLevel = 0
        if '/' in cclass:
            multiclassList = cclass.replace(' ', '').split('/')
            for m in multiclassList:
                mLevel = re.search('\d+', m)
                if not m:
                    msg += "- You are missing the level for your multiclass class. Please check your format.\n"
                    break
                mLevel = mLevel.group()
                print(m)
                print(m[:len(m) - len(mLevel)])
                mClass = callAPI('Class',m[:len(m) - len(mLevel)])
                if not mClass:
                    cRecord = None
                    break
                cRecord.append({'Class': mClass, 'Level':mLevel})
                totalLevel += int(mLevel)

        else:
            singleClass = callAPI('Class',cclass)
            if singleClass:
                cRecord.append({'Class':singleClass, 'Level':lvl, 'Subclass': 'None'})
            else:
                cRecord = None

        charDict['Class'] = ""


        if not cRecord or cRecord == list():
            msg += '- That class isn\'t on the list or it is banned! Check #allowed-and-banned-content and check your spelling.\n'
        elif totalLevel != lvl and len(cRecord) > 1:
            msg += 'Your classes do not add up to the total level. Please recheck your multiclasses\n'
        else:
            def classEmbedCheck(r, u):
                sameMessage = False
                if charEmbedmsg.id == r.message.id:
                    sameMessage = True
                return (r.emoji in alphaEmojis[:alphaIndex]) or (str(r.emoji) == '❌') and u == author
          
            cRecord = sorted(cRecord, key = lambda i: i['Level'], reverse=True) 
            for m in cRecord:
                if int(m['Level']) < lvl:
                    className = f'{m["Class"]["Name"]} {m["Level"]}'
                else:
                    className = f'{m["Class"]["Name"]}'

                if int(m['Class']['Subclass Level']) <= int(m['Level']) and msg == "":
                    try:
                        subclassesList = m['Class']['Subclasses'].split(',')
                        subclassString = ""
                        for num in range(len(subclassesList)):
                            subclassString += f'{alphaEmojis[num]}: {subclassesList[num]}\n'

                        charEmbed.add_field(name=f"Your class **{m['Class']['Name']}** allows you to pick a subclass at the level you're creating your character. React with the choices below to select your subclass.", value=subclassString, inline=False)
                        alphaIndex = len(subclassesList)
                        if not charEmbedmsg:
                            charEmbedmsg = await channel.send(embed=charEmbed)
                        else:
                            await charEmbedmsg.edit(embed=charEmbed)
                        await charEmbedmsg.add_reaction('❌')
                        tReaction, tUser = await self.bot.wait_for("reaction_add", check=classEmbedCheck, timeout=60)
                    except asyncio.TimeoutError:
                        await charEmbedmsg.delete()
                        await channel.send('Character creation timed out! Try using the command again')
                        self.char.get_command('create').reset_cooldown(ctx)
                        return
                    else:
                        if tReaction.emoji == '❌':
                            await charEmbedmsg.edit(embed=None, content=f"Character creation canceled. Type `{commandPrefix}char create` to try again!")
                            await charEmbedmsg.clear_reactions()
                            self.char.get_command('create').reset_cooldown(ctx)
                            return
                    await charEmbedmsg.clear_reactions()
                    charEmbed.clear_fields()
                    choiceIndex = alphaEmojis.index(tReaction.emoji)
                    subclass = subclassesList[choiceIndex].strip()
                    m['Subclass'] = f'{className} ({subclass})' 

                    if charDict['Class'] == "": 
                        charDict['Class'] = f'{className} ({subclass})'
                    else:
                        charDict['Class'] += f' / {className} ({subclass})'
                else:
                    if charDict['Class'] == "": 
                        charDict['Class'] = className
                    else:
                        charDict['Class'] += f' / {className}'

        print(charDict['Class'])
        # check bg and gp
        bRecord = callAPI('Background',bg)
        if not bRecord:
            msg += '- That background isn\'t on the list or it is banned! Check #allowed-and-banned-content and check your spelling.\n'
        else:
            charDict['Background'] = bRecord['Name']
            totalGP = 0
            if lvl > 1 and lvl < 6: 
                totalGP = (lvl-1) * 160
            if lvl > 5:
                totalGP = (lvl-6) * 960 + 1600

            charDict['GP'] = int(bRecord['GP'] + totalGP)
        
        #check stats - point buy
        def anyCharEmbedcheck(r, u):
            sameMessage = False
            if charEmbedmsg.id == r.message.id:
                sameMessage = True
            anyList.add(r.emoji)
            return ((len(anyList) == anyCheck+1) or str(r.emoji) == '❌') and u == author

        def slashCharEmbedcheck(r, u):
            sameMessage = False
            if charEmbedmsg.id == r.message.id:
                sameMessage = True
            return (r.emoji in numberEmojis[:len(statSplit)]) or (str(r.emoji) == '❌') and u == author

        if not sStr.isdigit() or not sDex.isdigit() or not sCon.isdigit() or not sInt.isdigit() or not sWis.isdigit() or not sCha.isdigit():
            msg += '- One or more of your stats are not numbers. Please check your spelling\n'

        elif rRecord:
            statsArray = [int(sStr), int(sDex), int(sCon), int(sInt), int(sWis), int(sCha)]
            statsBonus = rRecord['Modifiers'].replace(" ", "").split(',')
            for s in statsBonus:
                if '/' in s:
                    statSplit = s[:len(s)-2].replace(" ", "").split('/')
                    statSplitString = ""
                    for num in range(len(statSplit)):
                        statSplitString += f'{numberEmojis[num]}: {statSplit[num]}\n'
                    try:
                        charEmbed.add_field(name=f"Your race **{rRecord['Name']}** lets you choose between {s}. React [1-{len(statSplit)}] below for which stat you picked.", value=statSplitString, inline=False)
                        charEmbedmsg = await channel.send(embed=charEmbed)
                        for num in range(0,len(statSplit)): await charEmbedmsg.add_reaction(numberEmojis[num])
                        await charEmbedmsg.add_reaction('❌')
                        tReaction, tUser = await self.bot.wait_for("reaction_add", check=slashCharEmbedcheck, timeout=60)
                    except asyncio.TimeoutError:
                        await charEmbedmsg.delete()
                        await channel.send('Character creation timed out! Try using the command again')
                        self.char.get_command('create').reset_cooldown(ctx)
                        return
                    else:
                        if tReaction.emoji == '❌':
                            await charEmbedmsg.edit(embed=None, content=f"Character creation canceled. Type `{commandPrefix}char create` to try again!")
                            await charEmbedmsg.clear_reactions()
                            self.char.get_command('create').reset_cooldown(ctx)
                            return
                    await charEmbedmsg.clear_reactions()
                    s = statSplit[int(tReaction.emoji[0]) - 1] + s[-2:]

                if 'STR' in s:
                    statsArray[0] -= int(s[len(s)-1]) if s[len(s)-2] == "+" else int("-" + s[len(s)-1])
                elif 'DEX' in s:
                    statsArray[1] -= int(s[len(s)-1]) if s[len(s)-2] == "+" else int("-" + s[len(s)-1])
                elif 'CON' in s:
                    statsArray[2] -= int(s[len(s)-1]) if s[len(s)-2] == "+" else int("-" + s[len(s)-1])
                elif 'INT' in s:
                    statsArray[3] -= int(s[len(s)-1]) if s[len(s)-2] == "+" else int("-" + s[len(s)-1])
                elif 'WIS' in s:
                    statsArray[4] -= int(s[len(s)-1]) if s[len(s)-2] == "+" else int("-" + s[len(s)-1])
                elif 'CHA' in s:
                    statsArray[5] -= int(s[len(s)-1]) if s[len(s)-2] == "+" else int("-" + s[len(s)-1])
                elif 'ANY' in s:
                    try:
                        anyCheck = int(s[len(s)-1])
                        anyList = set()
                        charEmbed.add_field(name=f"Your race **{rRecord['Name']}** lets you choose {anyCheck} unique stats. React [1-6] below which with stats you allocated", value=f"{numberEmojis[0]}: STR\n{numberEmojis[1]}: DEX\n{numberEmojis[2]}: CON\n{numberEmojis[3]}: INT\n{numberEmojis[4]}: WIS\n{numberEmojis[5]}: CHA", inline=False)
                        if charEmbedmsg:
                            await charEmbedmsg.edit(embed=charEmbed)
                        else: 
                            charEmbedmsg = await channel.send(embed=charEmbed)
                        for num in range(0,6): await charEmbedmsg.add_reaction(numberEmojis[num])
                        await charEmbedmsg.add_reaction('❌')
                        tReaction, tUser = await self.bot.wait_for("reaction_add", check=anyCharEmbedcheck, timeout=60)
                    except asyncio.TimeoutError:
                        await charEmbedmsg.delete()
                        await channel.send('Character creation timed out! Try using the command again')
                        self.char.get_command('create').reset_cooldown(ctx)
                        return

                    else:
                        if tReaction.emoji == '❌':
                            await charEmbedmsg.edit(embed=None, content=f"Character creation canceled. Type `{commandPrefix}char create` to try again!")
                            await charEmbedmsg.clear_reactions()
                            self.char.get_command('create').reset_cooldown(ctx)
                            return

                    charEmbedmsg.clear_reactions()
                    anyList.remove('❌')
                    for s in anyList:
                        statsArray[(int(s[0]) - 1)] -= 1
                    
            totalPoints = 0

            for s in statsArray:
                if (13-s) < 0:
                    totalPoints += ((s - 13) * 2) + 5
                else:
                    totalPoints += (s - 8)

            if totalPoints != 27:
                msg += "- Your stats plus your race's modifers do not add up to 27 using point buy. Please check your point allocation.\n"

            print (statsArray)
            print (statsBonus)

        #feats
        def featCharEmbedCheck(r, u):
            sameMessage = False
            if charEmbedmsg.id == r.message.id:
                sameMessage = True
            return (r.emoji in numberEmojis[:2]) or (str(r.emoji) == '❌') and u == author
        
        def asiCharEmbedCheck(r, u):
            sameMessage = False
            if charEmbedmsg.id == r.message.id:
                sameMessage = True
            return (r.emoji in numberEmojis[:6]) or (str(r.emoji) == '❌') and u == author


        if msg == "":
            featLevels = []
            featChoices = []
            featsPickedList = []
            if rRecord['Name'] == 'Human (Variant)':
                featLevels.append('Human (Variant)')

            for c in cRecord:
                if int(c['Level']) > 3:
                    featLevels.append(4)
                    if 'Fighter' in c['Class']['Name'] and int(c['Level']) > 5:
                        featLevels.append(6)

                if int(c['Level']) > 7:
                    featLevels.append(8)


            for f in featLevels:
                try:
                    charEmbed.clear_fields()
                    if f != 'Human (Variant)':
                        charEmbed.add_field(name=f"Your level allows you to pick either an ability score improvement or a feat. Please react either 1 or 2 for your level {f} feat/ASI", value=f"{numberEmojis[0]}: Ability Score Improvement\n{numberEmojis[1]}: Feat\n", inline=False)
                        if charEmbedmsg:
                            await charEmbedmsg.edit(embed=charEmbed)
                        else: 
                            charEmbedmsg = await channel.send(embed=charEmbed)
                        for num in range(0,2): await charEmbedmsg.add_reaction(numberEmojis[num])
                        await charEmbedmsg.add_reaction('❌')
                        charEmbed.set_footer(text= f"React with ❌ to cancel")
                        tReaction, tUser = await self.bot.wait_for("reaction_add", check=featCharEmbedCheck, timeout=60)
                except asyncio.TimeoutError:
                    await charEmbedmsg.delete()
                    await channel.send('Character creation timed out! Try using the command again')
                    self.char.get_command('create').reset_cooldown(ctx)
                    return
                else:
                    if tReaction.emoji == '❌':
                        await charEmbedmsg.edit(embed=None, content=f"Character creation canceled. Type `{commandPrefix}char create` to try again!")
                        await charEmbedmsg.clear_reactions()
                        self.char.get_command('create').reset_cooldown(ctx)
                        return

                    choice = int(tReaction.emoji[0])
                    await charEmbedmsg.clear_reactions()

                    if f == 'Human (Variant)':
                        choice = 2

                    if choice == 1:
                        try:
                            charEmbed.clear_fields()    
                            charEmbed.add_field(name=f"Choose your first stat for your ASI. React [1-6]", value=f"{numberEmojis[0]}: STR\n{numberEmojis[1]}: DEX\n{numberEmojis[2]}: CON\n{numberEmojis[3]}: INT\n{numberEmojis[4]}: WIS\n{numberEmojis[5]}: CHA", inline=False)
                            await charEmbedmsg.edit(embed=charEmbed)
                            for num in range(0,6): await charEmbedmsg.add_reaction(numberEmojis[num])
                            await charEmbedmsg.add_reaction('❌')
                            tReaction, tUser = await self.bot.wait_for("reaction_add", check=asiCharEmbedCheck, timeout=60)
                        except asyncio.TimeoutError:
                            await charEmbedmsg.delete()
                            await channel.send('Character creation timed out! Try using the command again')
                            self.char.get_command('create').reset_cooldown(ctx)
                            return
                        else:
                            if tReaction.emoji == '❌':
                                await charEmbedmsg.edit(embed=None, content=f"Character creation canceled. Type `{commandPrefix}char create` to try again!")
                                await charEmbedmsg.clear_reactions()
                                self.char.get_command('create').reset_cooldown(ctx)
                                return
                        asi = int(tReaction.emoji[0]) - 1
                        print(asi)
                        charDict[statNames[asi]] = int(charDict[statNames[asi]]) + 1
                        try:
                            charEmbed.clear_fields()    
                            charEmbed.add_field(name=f"Choose your second stat for your ASI. React [1-6]", value=f"{numberEmojis[0]}: STR\n{numberEmojis[1]}: DEX\n{numberEmojis[2]}: CON\n{numberEmojis[3]}: INT\n{numberEmojis[4]}: WIS\n{numberEmojis[5]}: CHA", inline=False)
                            charEmbedmsg2 = await channel.send(embed=charEmbed)
                            for num in range(0,6): await charEmbedmsg2.add_reaction(numberEmojis[num])
                            await charEmbedmsg2.add_reaction('❌')
                            tReaction, tUser = await self.bot.wait_for("reaction_add", check=asiCharEmbedCheck, timeout=60)
                        except asyncio.TimeoutError:
                            await charEmbedmsg2.delete()
                            await channel.send('Character creation timed out! Try using the command again')
                            return
                            self.char.get_command('create').reset_cooldown(ctx)
                        else:
                            if tReaction.emoji == '❌':
                                await charEmbedmsg.edit(embed=None, content=f"Character creation canceled. Type `{commandPrefix}char create` to try again!")
                                await charEmbedmsg.clear_reactions()
                                await charEmbedmsg2.delete()
                                self.char.get_command('create').reset_cooldown(ctx)
                                return
                        asi = int(tReaction.emoji[0]) - 1
                        charDict[statNames[asi]] = int(charDict[statNames[asi]]) + 1
                        await charEmbedmsg2.delete()
                        await charEmbedmsg.clear_reactions()
                        print(asi)

                    elif choice == 2:
                        if featChoices == list():
                            API_URL = ('https://api.airtable.com/v0/appF4hiT6A0ISAhUu/Feats?maxRecords=100&sort%5B0%5D%5Bfield%5D=Name&sort%5B0%5D%5Bdirection%5D=asc').replace(" ", "%20").replace("+", "%2B") 
                            r = requests.get(API_URL, headers=headers)
                            r = r.json()

                            # TODO: feat check restricitons
                            for feat in r['records']:
                                featList = []
                                meetsRestriction = False

                                if 'Race Restriction' not in feat['fields'] and 'Class Restriction' not in feat['fields'] and 'Stat Restriction' not in feat['fields']:
                                    featChoices.append(feat['fields'])

                                else:
                                    if 'Race Restriction' in feat['fields']:
                                        featsList = [x.strip() for x in feat['fields']['Race Restriction'].split(',')]
                                        if charDict['Race'] in featsList:
                                            meetsRestriction = True

                                    if 'Class Restriction' in feat['fields']:
                                        featsList = [x.strip() for x in feat['fields']['Class Restriction'].split(',')]
                                        for c in cRecord:
                                            if c['Class']['Name'] in featList or c['Subclass'] in featsList:
                                                meetsRestriction = True

                                    if 'Stat Restriction' in feat['fields']:
                                        s = feat['fields']['Stat Restriction']
                                        statNumber = int(s[-2:])
                                        print(feat)
                                        if '/' in s:
                                            checkStat = s[:len(s)-2].replace(" ", "").split('/')
                                            statSplitString = ""
                                        else:
                                            checkStat = [s[:len(s)-2].strip()]

                                        print(checkStat)

                                        for stat in checkStat:
                                            if int(charDict[stat]) >= statNumber:
                                                meetsRestriction = True

                                    if meetsRestriction:
                                        featChoices.append(feat['fields'])

                        else:
                            featChoices.remove(featPicked)

                        def featChoiceCheck(r, u):
                            sameMessage = False
                            if charEmbedmsg.id == r.message.id:
                                sameMessage = True
                            return sameMessage and u == author and (r.emoji == left or r.emoji == right or r.emoji == '❌' or r.emoji == back or r.emoji in alphaEmojis[:perPage])

                        page = 0;
                        perPage = 24
                        numPages =((len(featChoices)) // perPage) + 1

                        while True:
                            charEmbed.clear_fields()  
                            if f == 'Human (Variant)':
                                charEmbed.add_field(name=f"Your race **Human (Variant)** allows you to choose a feat. Please choose your feat from the list below.", value=f"-", inline=False)
                            else:
                                charEmbed.add_field(name=f"Please choose your feat from the list below", value=f"-", inline=False)

                            pageStart = perPage*page
                            pageEnd = perPage * (page + 1)
                            alphaIndex = 0
                            for i in range(pageStart, pageEnd if pageEnd < (len(featChoices) - 1) else (len(featChoices)) ):
                                charEmbed.add_field(name=alphaEmojis[alphaIndex], value=featChoices[i]['Name'], inline=True)
                                alphaIndex+=1
                            charEmbed.set_footer(text= f"Page {page+1} of {numPages} -- use {left} or {right} to navigate or ❌ to cancel")
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
                                self.char.get_command('create').reset_cooldown(ctx)
                                return
                            else:
                                if react.emoji == left:
                                    page -= 1
                                    if page < 0:
                                      page = numPages - 1;
                                elif react.emoji == right:
                                    page += 1
                                    if page > numPages - 1: 
                                      page = 0
                                elif react.emoji == '❌':
                                    await charEmbedmsg.edit(embed=None, content=f"Character creation canceled.")
                                    await charEmbedmsg.clear_reactions()
                                    self.char.get_command('create').reset_cooldown(ctx)
                                    return
                                # elif react.emoji == back:
                                #     await charEmbedmsg.delete()
                                #     await ctx.reinvoke()
                                elif react.emoji in alphaEmojis:
                                    await charEmbedmsg.clear_reactions()
                                    break
                                charEmbed.clear_fields()
                                await charEmbedmsg.clear_reactions()
                        
                        featPicked = featChoices[(page * perPage) + alphaEmojis.index(react.emoji)]
                        featsPickedList.append(featPicked)
                        print(featPicked)
                        def slashFeatEmbedcheck(r, u):
                            sameMessage = False
                            if charEmbedmsg.id == r.message.id:
                                sameMessage = True
                            return (r.emoji in numberEmojis[:len(featBonusList)]) or (str(r.emoji) == '❌') and u == author

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
                                    charEmbed.add_field(name=f"The feat you chose **{featPicked['Name']}** lets you choose between {featBonus}. React [1-{len(featBonusList)}] below for which stat you picked.", value=featBonusString, inline=False)
                                    await charEmbedmsg.edit(embed=charEmbed)
                                    for num in range(0,len(featBonusList)): await charEmbedmsg.add_reaction(numberEmojis[num])
                                    await charEmbedmsg.add_reaction('❌')
                                    tReaction, tUser = await self.bot.wait_for("reaction_add", check=slashFeatEmbedcheck, timeout=60)
                                except asyncio.TimeoutError:
                                    await charEmbedmsg.delete()
                                    await channel.send('Character creation timed out! Try using the command again')
                                    self.char.get_command('create').reset_cooldown(ctx)
                                    return
                                else:
                                    if tReaction.emoji == '❌':
                                        await charEmbedmsg.edit(embed=None, content=f"Character creation canceled. Type `{commandPrefix}char create` to try again!")
                                        await charEmbedmsg.clear_reactions()
                                        self.char.get_command('create').reset_cooldown(ctx)
                                        return
                                await charEmbedmsg.clear_reactions()
                                charDict[featBonusList[int(tReaction.emoji[0]) - 1]] = int(charDict[featBonusList[int(tReaction.emoji[0]) - 1]]) + int(featBonus[-1:])
                                    
                            else:
                                featBonusList = featBonus.split(', ')
                                for fb in featBonusList:
                                    charDict[fb[:3]] =  int(charDict[fb[:3]]) + int(fb[-1:])

                        if featsPickedList != list():
                            charDict['Feats'] = ', '.join(str(string['Name']) for string in featsPickedList)            
        #HP
        if cRecord:
            cRecord = sorted(cRecord, key = lambda i: i['Class']['Hit Die Max'],reverse=True) 

            totalHP = 0
            totalHP += cRecord[0]['Class']['Hit Die Max']
            currentLevel = 1
            
            for c in cRecord:
                classLevel = int(c['Level'])
                while currentLevel < classLevel:
                    totalHP += c['Class']['Hit Die Average']
                    currentLevel += 1
                currentLevel = 0

            totalHP += ((charDict['CON'] - 10) // 2 ) * lvl
            charDict['HP'] = totalHP


        if msg:
            if charEmbedmsg:
                await charEmbedmsg.delete()
            await ctx.channel.send(f'There was an error in creating your character:\n```{msg}```')
            self.char.get_command('create').reset_cooldown(ctx)
            return 

        charEmbed.clear_fields()    
        charEmbed.add_field(name='Name', value=charDict['Name'], inline=True)
        charEmbed.add_field(name='Race', value=charDict['Race'], inline=True)
        charEmbed.add_field(name='Level', value=charDict['Level'], inline=True)
        charEmbed.add_field(name='HP', value=charDict['HP'], inline=True)
        charEmbed.add_field(name='Background', value=charDict["Background"], inline=True)
        charEmbed.add_field(name='Class', value=f'{charDict["Class"]}', inline=True)
        charEmbed.add_field(name='CP', value=f"{charDict['CP']}", inline=True)
        charEmbed.add_field(name='GP', value=f"{charDict['GP']} GP", inline=True)
        charEmbed.add_field(name='Current TP Item', value=charDict['Current Item'], inline=True)
        charEmbed.add_field(name='Magic Items', value=charDict['Magic Items'], inline=True)
        charEmbed.add_field(name='Consumables', value=charDict['Consumables'], inline=True)
        charEmbed.add_field(name='Feats', value=charDict['Feats'], inline=True)
        charEmbed.add_field(name='Stats', value=f"**STR:** {charDict['STR']} **DEX:** {charDict['DEX']} **CON:** {charDict['CON']} **INT:** {charDict['INT']} **WIS:** {charDict['WIS']} **CHA:** {charDict['CHA']}", inline=False)
        charEmbed.set_footer(text= charEmbed.Empty)

        API_URL = ('https://api.airtable.com/v0/apppGo3CcmtyTMxwh/Characters')
        data = {
            "fields": charDict
        }

        try:
            r = requests.post(API_URL, headers=headers, json=data)
            print(r)
        except requests.exceptions.RequestException as e:
            print (e)
            charEmbedmsg = await channel.send(embed=None, content="Uh oh, looks like something went wrong. Please try creating your character again.")
        else:
            print('Success')
            if charEmbedmsg:
                await charEmbedmsg.clear_reactions()
                await charEmbedmsg.edit(embed=charEmbed, content ="Congratulations! You have created your character.")
            else: 
                charEmbedmsg = await channel.send(embed=charEmbed, content="Congratulations! You have created your character.")

            self.char.get_command('create').reset_cooldown(ctx)


        # def next_available_row(sheet):
        #     char_list = list(filter(None, sheet.col_values(2)))
        #     refreshKey(refreshTime)
        #     return len(char_list)+1

        # next_row = next_available_row(charDatabase)

        # for index in range(0, len(charRow)):
        #     charDatabase.update_cell(next_row, index+2, charRow[index]) 
        # refreshKey(refreshTime)
    
    @commands.cooldown(1, 5, type=commands.BucketType.member)
    @char.command()
    async def info(self,ctx, *, char):
        headers = {
            "Authorization": "Bearer keyw9zLleR35sm21O",
            "Content-Type": "application/json"
        }
        channel = ctx.channel
        author = ctx.author
        guild = ctx.guild
        roleColors = {r.name:r.colour for r in guild.roles}

        print(roleColors)

        API_URL = ('https://api.airtable.com/v0/apppGo3CcmtyTMxwh/Characters?&filterByFormula=AND((FIND(LOWER(SUBSTITUTE("' + char + '"," ","")),LOWER(SUBSTITUTE({Name}," ","")))), {User ID}=' + str(author.id) + ' )').replace(" ", "%20").replace("+", "%2B") 
        r = requests.get(API_URL, headers=headers)
        r = r.json()

        infoRecords = r['records']
        charDict = {}
        charEmbed = discord.Embed ()

        if infoRecords == list():
            await channel.send(content=f'I was not able to find your character named {char}. Please check your spelling and try again')
            return

        else:
            print(infoRecords[0]['fields'])
            if len(infoRecords) > 1:
                infoString = ""
                for i in range(0, min(len(infoRecords), 6)):
                    infoString += f"{numberEmojis[i]}: {infoRecords[i]['fields']['Name']} ({guild.get_member(int(infoRecords[i]['fields']['User ID']))})\n"
                
                try:
                    def infoCharEmbedcheck(r, u):
                        sameMessage = False
                        if charEmbedmsg.id == r.message.id:
                            sameMessage = True
                        return (r.emoji in numberEmojis[:min(len(infoRecords), 6)]) or (str(r.emoji) == '❌') and u == author

                    charEmbed.add_field(name=f"There seems to be multiple results for `{char}`, please choose the correct character.", value=infoString, inline=False)
                    charEmbedmsg = await channel.send(embed=charEmbed)
                    for num in range(0,min(len(infoRecords), 6)): await charEmbedmsg.add_reaction(numberEmojis[num])
                    await charEmbedmsg.add_reaction('❌')
                    tReaction, tUser = await self.bot.wait_for("reaction_add", check=infoCharEmbedcheck, timeout=60)
                except asyncio.TimeoutError:
                    await charEmbedmsg.delete()
                    await channel.send('Character information timed out! Try using the command again')
                    return
                else:
                    if tReaction.emoji == '❌':
                        await charEmbedmsg.edit(embed=None, content=f"Character information canceled. User `{commandPrefix}char info` command and try again!")
                        await charEmbedmsg.clear_reactions()
                        return
                await charEmbedmsg.clear_reactions()
                charDict = infoRecords[int(tReaction.emoji[0]) - 1]['fields']

            else:
                charDict = r['records'][0]['fields']

            charLevel = charDict['Level']

            charDictAuthor = guild.get_member(int(charDict['User ID']))
            charEmbed.set_author(name=charDictAuthor, icon_url=charDictAuthor.avatar_url)
            charEmbed.clear_fields()    
            charEmbed.add_field(name='Name', value=charDict['Name'], inline=True)
            charEmbed.add_field(name='Race', value=charDict['Race'], inline=True)
            charEmbed.add_field(name='Level', value=charLevel, inline=True)
            charEmbed.add_field(name='HP', value=charDict['HP'], inline=True)
            charEmbed.add_field(name='Background', value=charDict["Background"], inline=True)
            charEmbed.add_field(name='Class', value=f'{charDict["Class"]}', inline=True)
            charEmbed.add_field(name='CP', value=f"{charDict['CP']}", inline=True)
            charEmbed.add_field(name='GP', value=f"{charDict['GP']} GP", inline=True)
            charEmbed.add_field(name='Current TP Item', value=charDict['Current Item'], inline=True)
            charEmbed.add_field(name='Magic Items', value=charDict['Magic Items'], inline=True)
            charEmbed.add_field(name='Consumables', value=charDict['Consumables'], inline=True)
            charEmbed.add_field(name='Feats', value=charDict['Feats'], inline=True)
            charEmbed.add_field(name='Stats', value=f"**STR:** {charDict['STR']} **DEX:** {charDict['DEX']} **CON:** {charDict['CON']} **INT:** {charDict['INT']} **WIS:** {charDict['WIS']} **CHA:** {charDict['CHA']}", inline=False)
            if 'Image' in charDict:
                charEmbed.set_thumbnail(url=charDict['Image'])

            if charLevel < 5:
                charEmbed.colour = (roleColors['Junior Friend'])
            elif charLevel < 11:
                charEmbed.colour = (roleColors['Journey Friend'])
            elif charLevel < 17:
                charEmbed.colour = (roleColors['Elite Friend'])
            elif charLevel < 21:
                charEmbed.colour = (roleColors['True Friend'])
            
            charEmbed.set_footer(text= charEmbed.Empty)
            await ctx.channel.send(embed=charEmbed)
            self.char.get_command('info').reset_cooldown(ctx)
        
    @commands.cooldown(1, 5, type=commands.BucketType.member)
    @char.command()
    async def image(self,ctx, char, url):
        headers = {
            "Authorization": "Bearer keyw9zLleR35sm21O",
            "Content-Type": "application/json"
        }
        channel = ctx.channel
        author = ctx.author
        guild = ctx.guild

        API_URL = ('https://api.airtable.com/v0/apppGo3CcmtyTMxwh/Characters?&filterByFormula=(FIND(LOWER(SUBSTITUTE("' + char + '"," ","")),LOWER(SUBSTITUTE({Name}," ",""))))').replace(" ", "%20").replace("+", "%2B") 
        r = requests.get(API_URL, headers=headers)
        r = r.json()

        infoRecords = r['records']
        charEmbed = discord.Embed ()
        print(url)

        if infoRecords == list():
            await channel.send(content=f'I was not able to find the character {char}. Please check your spelling and try again')
            return
        else:
            if len(infoRecords) > 1:
                infoString = ""
                for i in range(0, min(len(infoRecords), 6)):
                    infoString += f"{numberEmojis[i]}: {infoRecords[i]['fields']['Name']} ({guild.get_member(int(infoRecords[i]['fields']['User ID']))})\n"
                
                try:
                    def infoCharEmbedcheck(r, u):
                        sameMessage = False
                        if charEmbedmsg.id == r.message.id:
                            sameMessage = True
                        return (r.emoji in numberEmojis[:min(len(infoRecords), 6)]) or (str(r.emoji) == '❌') and u == author

                    charEmbed.add_field(name=f"There seems to be multiple results for `{char}`, please choose the correct character.", value=infoString, inline=False)
                    charEmbedmsg = await channel.send(embed=charEmbed)
                    for num in range(0,min(len(infoRecords), 6)): await charEmbedmsg.add_reaction(numberEmojis[num])
                    await charEmbedmsg.add_reaction('❌')
                    tReaction, tUser = await self.bot.wait_for("reaction_add", check=infoCharEmbedcheck, timeout=60)
                except asyncio.TimeoutError:
                    await charEmbedmsg.delete()
                    await channel.send('Character information timed out! Try using the command again')
                    return
                else:
                    if tReaction.emoji == '❌':
                        await charEmbedmsg.edit(embed=None, content=f"Character information canceled. User `{commandPrefix}char info` command and try again!")
                        await charEmbedmsg.clear_reactions()
                        return
                await charEmbedmsg.clear_reactions()
                charID = infoRecords[int(tReaction.emoji[0]) - 1]['id']
                print(charID)

            else:
                charID = r['records'][0]['id']
                print(charID)

            API_URL = ('https://api.airtable.com/v0/apppGo3CcmtyTMxwh/Characters/' + charID)
            data = {
                "fields": {
                  'Image': url
                } 
            }

            try:
                r = requests.patch(API_URL, headers=headers, json=data)
                print(r)
            except requests.exceptions.RequestException as e:
                print (e)
                charEmbedmsg = await channel.send(embed=None, content="Uh oh, looks like something went wrong. Please try the command again")
            else:
                print('Success')
                await ctx.channel.send(content=f'I have updated the image for the character {char}. Please check using the `{commandPrefix}char info` command')


def setup(bot):
    bot.add_cog(Character(bot))
