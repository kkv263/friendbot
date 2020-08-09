import discord
import asyncio
import requests
import re
from discord.utils import get        
from discord.ext import commands
from bfunc import db, commandPrefix, numberEmojis, roleArray, callAPI, checkForChar, traceBack, alphaEmojis
import traceback as traces

class Tp(commands.Cog):
    def __init__ (self, bot):
        self.bot = bot
    
    @commands.group()
    async def tp(self, ctx):	
        tpCog = self.bot.get_cog('Tp')
        pass

    async def cog_command_error(self, ctx, error):
        msg = None

        if isinstance(error, commands.CommandNotFound):
            await ctx.channel.send(f'Sorry, the command **`{commandPrefix}{ctx.invoked_with}`** requires an additional keyword to the command or is invalid, please try again!')
            return
            
        if isinstance(error, commands.MissingRequiredArgument):
            if error.param.name == 'charName':
                msg = "You're missing your character name in the command. "
            elif error.param.name == "mItem":
                msg = "You're missing the item you want to acquire in the command. "
            elif error.param.name == "tierNum":
                msg = "You're missing the tier for the TP you want to abandon. "
        elif isinstance(error, commands.BadArgument):
            # convert string to int failed
            msg = "The amount you want to acquire must be a number. "
        # bot.py handles this, so we don't get traceback called.
        elif isinstance(error, commands.CommandOnCooldown):
            return
        if msg:
            if ctx.command.name == "buy":
                msg += f"Please follow this format:\n```yaml\n{commandPrefix}tp buy \"character name\" \"magic item\"```\n"
            elif ctx.command.name == "discard":
                msg += f"Please follow this format:\n```yaml\n{commandPrefix}tp discard \"character name\"```\n"
            elif ctx.command.name == "abandon":
                msg += f"Please follow this format:\n```yaml\n{commandPrefix}tp abandon \"character name\" tier```\n"

            ctx.command.reset_cooldown(ctx)
            await ctx.channel.send(msg)
        else:
            ctx.command.reset_cooldown(ctx)
            await traceBack(ctx,error)
    @tp.command()
    async def createGroup(self, ctx, query, group):
    
        #channel and author of the original message creating this call
        channel = ctx.channel
        author = ctx.author
        
        collection = db["mit"]
        apiEmbedmsg = None
        apiEmbed = discord.Embed()
        #get the entire table if no query is given
        if query is None:
            return None, apiEmbed, apiEmbedmsg

        #if the query has no text, return nothing
        if query.strip() == "":
            return None, apiEmbed, apiEmbedmsg

        #restructure the query to be more regEx friendly
        query = query.strip()
        query = query.replace('(', '\\(')
        query = query.replace(')', '\\)')
        query = query.replace('+', '\\+')
        
        #search through the table for an element were the Name or Grouped property contain the query
        filterDic = {"Name": {
                            "$regex": query,
                            #make the check case-insensitively
                            "$options": "i"
                          }
                        }
        records = list(collection.find(filterDic))
        
        #restore the original query
        query = query.replace("\\", "")
        #sort elements by either the name, or the first element of the name list in case it is a list
        def sortingEntryAndList(elem):
            if(isinstance(elem['Name'],list)): 
                return elem['Name'][0] 
            else:  
                return elem['Name']
        
        remove_grouper = [] #track all elements that need to be removes since they act as representative for a group of items

        #for every search result check if it contains a group and create entries for each group element if it does
        for entry in records:
            # if the element is part of a group
            if("Grouped" in entry):
                # remove it later
                remove_grouper.append(entry)
        # remove all group representatives
        for group_to_remove in remove_grouper:
            records.remove(group_to_remove)
        
        #sort all items alphabetically 
        records = sorted(records, key = sortingEntryAndList)    
        
        #if no elements are left, return nothing
        if records == list():
            return None, apiEmbed, apiEmbedmsg
        else:
            try:
                latest=" Go"
                latest1=""
                latest2=""
                latest3=""
                #create a string to provide information about the items to the user
                infoString = ""
                collapseList=[]
                for rec in records:
                    infoString = f"{rec['Name']} (Tier {rec['Tier']}): **{rec['TP']} TP: **{rec['GP']} GP**\n"
                    def apiEmbedCheck(r, u):
                        sameMessage = False
                        if apiEmbedmsg.id == r.message.id:
                            sameMessage = True
<<<<<<< HEAD
                        return ((str(r.emoji) == '✅') or (str(r.emoji) == '❌') or (str(r.emoji) == '⛔')) and u == author
                    #inform the user of the current information and ask for their selection of an item               
                    apiEmbed.add_field(name=f"Latest Change", value=latest, inline=False)
                    apiEmbed.add_field(name=f"Select which one to collapse.", value=infoString, inline=False)     
=======
                        return ((str(r.emoji) == '✅') or (str(r.emoji) == '❌') or (str(r.emoji) == '⛔')) and u == author and sameMessage
                    #inform the user of the current information and ask for their selection of an item
                    apiEmbed.add_field(name=f"Select which one to collapse.", value=infoString, inline=False)
>>>>>>> pr/4
                    if not apiEmbedmsg or apiEmbedmsg == "Fail":
                        apiEmbedmsg = await channel.send(embed=apiEmbed)
                    else:
                        await apiEmbedmsg.edit(embed=apiEmbed)

                    await apiEmbedmsg.add_reaction('✅')
                    await apiEmbedmsg.add_reaction('❌')
                    await apiEmbedmsg.add_reaction('⛔')
                
                    try:
                        tReaction, tUser = await self.bot.wait_for("reaction_add", check=apiEmbedCheck, timeout=60)
                    except asyncio.TimeoutError:
                        #stop if no response was given within the timeframe and reenable the command
                        await apiEmbedmsg.delete()
                        await channel.send('Timed out! Try using the command again.')
                        ctx.command.reset_cooldown(ctx)
                        return None, apiEmbed, "Fail"
                    else:
                        latest3 = latest2
                        latest2 = latest1
                        latest1 = rec["Name"]+ ": "+tReaction.emoji+"\n"
                        latest=latest3+latest2+latest1
                        
                        #stop if the cancel emoji was given and reenable the command
                        if tReaction.emoji == '❌':
                            pass
                        elif tReaction.emoji == '✅':
                            collapseList.append(rec)
                        else:
                            tpEmbedmsg = await channel.send(embed=None, content=f"Grouping process cancelled")
                            return
                    #return the selected item indexed by the emoji given by the user
                    apiEmbed.clear_fields()
                    await apiEmbedmsg.clear_reactions()
                name_list = list([x["Name"] for x in collapseList])
                charDict = collapseList[0].copy()
                charDict["Name"] = name_list
                charDict["Grouped"] = group
                charDict.pop("_id")
                collection.insert_one(charDict)
                for entry in collapseList:
                    collection.delete_one({'_id': entry['_id']})
                tpEmbedmsg = await channel.send(embed=None, content=f"Grouping process finished. These items have been grouped\n"+"\n".join(name_list))
                return
            except Exception as e:
                print ('MONGO ERROR: ' + str(e))
                traces.print_exc()
                tpEmbedmsg = await channel.send(embed=None, content=f"Uh oh, looks like something went wrong. Please try `{commandPrefix}tp buy` again.")

    @commands.cooldown(1, float('inf'), type=commands.BucketType.user)
    @tp.command()
    async def buy(self, ctx , charName, mItem):

        channel = ctx.channel
        author = ctx.author
        tpEmbed = discord.Embed()
        #this variable is never used
        tpCog = self.bot.get_cog('Tp')
        #find a character matching with charName using the function in bfunc
        charRecords, tpEmbedmsg = await checkForChar(ctx, charName, tpEmbed)

        if charRecords:
            #functions to make sure that only the intended user can respond
            def tpChoiceEmbedCheck(r, u):
                sameMessage = False
                if tpEmbedmsg.id == r.message.id:
                    sameMessage = True
                return ((str(r.emoji) == '1️⃣' and haveTP) or (charRecords['GP'] >= gpNeeded and str(r.emoji) == '2️⃣') or (str(r.emoji) == '❌')) and u == author and sameMessage
            def tpEmbedCheck(r, u):
                sameMessage = False
                if tpEmbedmsg.id == r.message.id:
                    sameMessage = True
                return ((str(r.emoji) == '✅') or (str(r.emoji) == '❌')) and u == author and sameMessage

            #make the call to the bfunc function to retrieve an item matching with mItem
            mRecord, tpEmbed, tpEmbedmsg = await callAPI(ctx, tpEmbed, tpEmbedmsg, 'mit',mItem) 
            #if an item was found
            if mRecord:
                """
                Alright boyo, here is my masterstroke in this madness
                Since callAPI we generated the subitems of a grouping as entries and Grouped property has been maintained for them
                we can now use this to indentify if an item was part of a bigger group
                The Grouped property for characters acts as a tracker of which item the character worked/is working forward in the group
                If the user does not have the property, we can thus skip since they could not have gotten the item
                """
                if("Grouped" in mRecord and "Grouped" in charRecords):
                    """
                    We can now check if the group name is in any of the Groups that character has interacted with
                    We can then check for every element in Grouped if the currently requested item is in any of them
                    The last check is to make sure that all other items beside the initially selected one get blocked
                    
                    if(any(mRecord["Grouped"] in group_item_pair for group_item_pair in charRecords["Grouped"])):
                    """
                    for groupName in charRecords["Grouped"]:
                        group_name_split = groupName.split(":")
                        if(mRecord["Grouped"] == group_name_split[0].strip() and mRecord["Name"] != group_name_split[1].strip()):
                            #inform the user that they already have an item from this group
                            await channel.send(f"***{mRecord['Name']}*** is a variant of the ***{mRecord['Grouped']}*** item and ***{charRecords['Name']}*** already owns a variant of the that item.")
                            ctx.command.reset_cooldown(ctx)
                            return 
                # check if the requested item is already in the inventory
                if(mRecord['Name'] in [name.strip() for name in charRecords['Magic Items'].split(",")]): 
                    await channel.send(f"You already have ***{mRecord['Name']}*** and cannot spend TP or gp on another one.")
                    ctx.command.reset_cooldown(ctx)
                    return 
                
                # get the tier of the item
                tierNum = mRecord['Tier']
                # get the gold cost of the item
                gpNeeded = mRecord['GP']
                #get the list of all items currently being worked towards
                currentMagicItems = charRecords['Current Item'].split(', ')

                tpBank = [0,0,0,0]
                tpBankString = ""
                #grab the available TP of the character
                for x in range(0,5):
                    if f'T{x} TP' in charRecords:
                      tpBank[x-1] = (float(charRecords[f'T{x} TP']))
                      tpBankString += f"{tpBank[x-1]} T{x} TP, " 

                haveTP = False
                lowestTp = 0
                #get the lowest tier available TP
                for tp in range (int(tierNum) - 1, 4):
                    if tpBank[tp] > 0:
                        haveTP = True
                        lowestTP = tp + 1 
                        break

                # display the cost of the item to the user
                tpEmbed.title = f"{mRecord['Name']}\nTier {mRecord['Tier']} - {mRecord['TP']} TP / {mRecord['GP']} gp"
                
                # if the user doesnt have the resources for the purchases, inform them and cancel
                if not haveTP and float(charRecords['GP']) < gpNeeded:
                    await channel.send(f"You do not have Tier {tierNum} TP or gp to acquire `{mRecord['Name']}`.")
                    ctx.command.reset_cooldown(ctx)
                    return
                  
                # get confirmation from the user for the purchase
                elif not haveTP:
                    if tpBank == [0] * 4:
                        tpEmbed.description = f"Do you want to acquire **{mRecord['Name']}** with TP or gp?\n\n You have **no TP** and **{charRecords[f'GP']} gp.**\n\n1️⃣: ~~{mRecord['TP']} TP (Treasure Points)~~ You do not have enough TP.\n2️⃣: {mRecord['GP']} gp (gold pieces)\n\n❌: Cancel"                 
                    else:
                        tpEmbed.description = f"Do you want to acquire **{mRecord['Name']}** with TP or gp?\n\n You have **{tpBankString}** and **{charRecords[f'GP']} gp.**\n\n1️⃣: ~~{mRecord['TP']} TP (Treasure Points)~~ You do not have enough TP.\n2️⃣: {mRecord['GP']} gp (gold pieces)\n\n❌: Cancel"                 

                elif float(charRecords['GP']) < gpNeeded:
                    tpEmbed.description = f"Do you want to acquire **{mRecord['Name']}** with TP or gp?\n\n You have **{tpBankString}** and **{charRecords[f'GP']} gp.**\n\n1️⃣: {mRecord['TP']} TP (Treasure Points)\n2️⃣: ~~{mRecord['GP']} gp (gold pieces)~~ You do not have enough gp.\n\n❌: Cancel"                 

                else:
                    tpEmbed.description = f"Do you want to acquire **{mRecord['Name']}** with TP or gp?\n\n You have **{tpBankString}** and **{charRecords[f'GP']} gp.**\n\n1️⃣: {mRecord['TP']} TP (Treasure Points)\n2️⃣: {mRecord['GP']} gp (gold pieces)\n\n❌: Cancel"                 
                
                if tpEmbedmsg:
                    await tpEmbedmsg.edit(embed=tpEmbed)
                else:
                    tpEmbedmsg = await channel.send(embed=tpEmbed)
                # get choice from the user
                if haveTP:
                    await tpEmbedmsg.add_reaction('1️⃣')
                if float(charRecords['GP']) >= gpNeeded:
                    await tpEmbedmsg.add_reaction('2️⃣')
                await tpEmbedmsg.add_reaction('❌')
                try:
                    tReaction, tUser = await self.bot.wait_for("reaction_add", check=tpChoiceEmbedCheck , timeout=60)
                except asyncio.TimeoutError:
                    #cancel if the user didnt respond within the timeframe
                    await tpEmbedmsg.delete()
                    await channel.send(f'TP canceled. Use `{commandPrefix}tp buy` command and try again!')
                    ctx.command.reset_cooldown(ctx)
                    return
                else:
                    await tpEmbedmsg.clear_reactions()
                    newGP = ""
                    newTP = ""
                    refundTP = 0.0
                    #cancel if the user decided to cancel the purchase
                    if tReaction.emoji == '❌':
                        await tpEmbedmsg.edit(embed=None, content=f"TP canceled. Use `{commandPrefix}tp buy` command and try again!")
                        await tpEmbedmsg.clear_reactions()
                        ctx.command.reset_cooldown(ctx)
                        return
                    #refund the TP in the item if the user decides to purchase with gold
                    elif tReaction.emoji == '2️⃣':
                        newGP = charRecords['GP'] - gpNeeded
                        #search for the item in the items currently worked towards
                        if mRecord['Name'] in charRecords['Current Item']:
                            #grab the matching item
                            currentMagicItem = re.search('\(([^)]+)', charRecords['Current Item']).group(1)
                            #split the current/needed TP
                            tpSplit= currentMagicItem.split('/')
                            refundTP = float(tpSplit[0])
                            charRecords['Current Item'] = "None"
                            #confirm with the user on the purchase
                            tpEmbed.description = f"Are you sure you want to acquire this?\n\n**{mRecord['Name']}**: {charRecords['GP']} → {newGP} gp\nYou will be refunded the TP you have already spent on this item ({refundTP} TP). \n\n✅: Yes\n\n❌: Cancel"
                        else:
                            tpEmbed.description = f"Are you sure you want to acquire this?\n\n**{mRecord['Name']}**: {charRecords['GP']} → {newGP} gp\n\n✅: Yes\n\n❌: Cancel"

                    # If user decides to buy item with TP:
                    elif tReaction.emoji == '1️⃣':
                        tierNum = lowestTP
                        tpNeeded = float(mRecord['TP'])
                        mIndex = 0
                        # If the character has no invested TP items OR:
                        # If the character has invested TP items, but the item they are spending it on is not included
                        if charRecords['Current Item'] == 'None':
                            tpSplit = [0.0, tpNeeded]
                            currentMagicItems = [f"{mRecord['Name']} (0/0)"]
                        elif mRecord['Name'] not in charRecords['Current Item']:
                            tpSplit = [0.0, tpNeeded]
                            currentMagicItems.append(f"{mRecord['Name']} (0/0)")
                            mIndex = len(currentMagicItems) - 1
                        else:
                            mIndex = [m.split(' (')[0] for m in currentMagicItems].index(mRecord['Name'])
                            currentMagicItem = re.search('\(([^)]+)', currentMagicItems[mIndex]).group(1)
                            print(currentMagicItem)
                            tpSplit= currentMagicItem.split('/')
                            tpNeeded = float(tpSplit[1]) - float(tpSplit[0]) 

                        tpResult = tpNeeded - float(charRecords[f"T{tierNum} TP"])

                        # How (xTP/yTP) is calculated. If spent TP is incomplete, else if spending TP completes the item
                        if tpResult > 0:
                            newTP = f"{float(tpSplit[1]) - tpResult}/{tpSplit[1]}"
                            charRecords[f"T{tierNum} TP"] = 0
                            currentMagicItems[mIndex] = f"{mRecord['Name']} ({newTP})"
                            charRecords['Current Item'] = ', '.join(currentMagicItems)
                        else:
                            newTP = f"({tpSplit[1]}/{tpSplit[1]}) - Complete! :tada:"
                            charRecords[f"T{tierNum} TP"] = abs(float(tpResult))
                            if currentMagicItems != list():
                                currentMagicItems.pop(mIndex)
                                charRecords['Current Item'] = ', '.join(currentMagicItems)
                                if currentMagicItems == list():
                                    charRecords['Current Item'] = 'None'

                        tpEmbed.description = f"Are you sure you want to acquire this?\n\n**{mRecord['Name']}**: {tpSplit[0]}/{tpSplit[1]} → {newTP}\n**Leftover T{tierNum} TP**: {charRecords[f'T{tierNum} TP']}\n\n✅: Yes\n\n❌: Cancel"


                    # If not complete, leave in current items, otherwise add to magic item list / consuambles
                    if 'Complete' not in newTP and tReaction.emoji == '1️⃣':
                        pass
                    elif charRecords['Magic Items'] == "None":
                        charRecords['Magic Items'] = mRecord['Name']
                    else:
                        newMagicItems = charRecords['Magic Items'].split(', ')
                        newMagicItems.append(mRecord['Name'])
                        newMagicItems.sort()
                        charRecords['Magic Items'] = ', '.join(newMagicItems)

                    tpEmbed.set_footer(text=tpEmbed.Empty)
                    await tpEmbedmsg.edit(embed=tpEmbed)
                    await tpEmbedmsg.add_reaction('✅')
                    await tpEmbedmsg.add_reaction('❌')
                    try:
                        tReaction, tUser = await self.bot.wait_for("reaction_add", check=tpEmbedCheck , timeout=60)
                    except asyncio.TimeoutError:
                        await tpEmbedmsg.delete()
                        await channel.send(f'TP canceled. Use `{commandPrefix}tp buy` command and try again!')
                        ctx.command.reset_cooldown(ctx)
                        return
                    else:
                        await tpEmbedmsg.clear_reactions()
                        if tReaction.emoji == '❌':
                            await tpEmbedmsg.edit(embed=None, content=f"TP canceled. Use `{commandPrefix}tp buy` command and try again!")
                            await tpEmbedmsg.clear_reactions()
                            ctx.command.reset_cooldown(ctx)
                            return
                        elif tReaction.emoji == '✅':
                            tpEmbed.clear_fields()
                            try:
                                playersCollection = db.players
                                if("Grouped" not in charRecords):
                                    charRecords["Grouped"] = []
                                if("Grouped" in mRecord and mRecord["Grouped"]+" : "+mRecord["Name"] not in charRecords["Grouped"]):
                                    charRecords["Grouped"].append(mRecord["Grouped"]+" : "+mRecord["Name"])
                                setData = {"Current Item":charRecords['Current Item'], "Magic Items":charRecords['Magic Items'], "Grouped":charRecords['Grouped']}
                                statSplit = None
                                unsetTP = False
                                # For the stat books, this will increase the characters stats permanently here.
                                if 'Attunement' not in mRecord and 'Stat Bonuses' in mRecord:
                                    if 'Max Stats' not in charRecords:
                                        charRecords['Max Stats'] = {'STR':20, 'DEX':20, 'CON':20, 'INT':20, 'WIS':20, 'CHA':20}

                                    print(charRecords['Max Stats'])
                                    # statSplit = MAX STAT +X
                                    statSplit = mRecord['Stat Bonuses'].split(' +')
                                    maxSplit = statSplit[0].split(' ')
                                    oldStat = charRecords[maxSplit[1]]

                                    #Increase stats from Manual/Tome and add to max stats. 
                                    if "MAX" in statSplit[0]:
                                        charRecords[maxSplit[1]] += int(statSplit[1]) 
                                        charRecords['Max Stats'][maxSplit[1]] += int(statSplit[1]) 

                                    setData[maxSplit[1]] = int(charRecords[maxSplit[1]])
                                    setData['Max Stats'] = charRecords['Max Stats']                           

                                    # If the stat increased was con, recalc HP
                                    # The old CON is subtracted, and new CON is added.
                                    # If the player can't destroy magic items, this is done here, otherwise... it will need to be done in $info.
                                    if 'CON' in maxSplit[1]:
                                        charRecords['HP'] -= ((int(oldStat) - 10) // 2) * charRecords['Level']
                                        charRecords['HP'] += ((int(charRecords['CON']) - 10) // 2) * charRecords['Level']
                                        setData['HP'] = charRecords['HP']

                                if newTP:
                                    if charRecords[f"T{tierNum} TP"] == 0:
                                        unsetTP = True
                                    else:
                                        setData[f"T{tierNum} TP"] = charRecords[f"T{tierNum} TP"] 
                                elif newGP:
                                    if refundTP:
                                        if f"T{tierNum} TP" not in charRecords:
                                            charRecords[f"T{tierNum} TP"] = 0 

                                        setData[f"T{tierNum} TP"] = charRecords[f"T{tierNum} TP"] + refundTP 
                                        setData['GP'] = newGP
                                    else:
                                        setData['GP'] = newGP

                                if unsetTP:
                                    playersCollection.update_one({'_id': charRecords['_id']}, {"$set": setData, "$unset": {f"T{tierNum} TP":1}})
                                else:
                                    playersCollection.update_one({'_id': charRecords['_id']}, {"$set": setData})

                                
                            except Exception as e:
                                print ('MONGO ERROR: ' + str(e))
                                tpEmbedmsg = await channel.send(embed=None, content=f"Uh oh, looks like something went wrong. Please try `{commandPrefix}tp buy` again.")
                            else:
                                if newTP:
                                    if "Complete" in newTP:
                                        tpEmbed.description = f"**TP spent!** Check out what you got! :tada:\n\n**{mRecord['Name']}**: {newTP}\n\n**Current T{tierNum} TP**: {charRecords[f'T{tierNum} TP']}\n\n"
                                    else:
                                        tpEmbed.description = f"**TP spent!** Your character still needs to spend more TP to complete the item.\n\n**{mRecord['Name']}**: {newTP}\n\n**Current T{tierNum} TP**: {charRecords[f'T{tierNum} TP']}\n\n"
                                elif newGP:
                                    if refundTP:
                                        tpEmbed.description = f"**gp spent!** Check out what you got! :tada:\n\n**{mRecord['Name']}**\n\n**Current gp**: {newGP}\n**Current T{tierNum} TP**: {charRecords[f'T{tierNum} TP'] + refundTP} (Refunded {refundTP})"
                                    else:
                                        tpEmbed.description = f"**gp spent!** Check out what you got! :tada:\n\n**{mRecord['Name']}**\n\n**Current gp**: {newGP}\n"
                                await tpEmbedmsg.edit(embed=tpEmbed)
                                ctx.command.reset_cooldown(ctx)
                                    
                
            else:
                await channel.send(f'`{mItem}` doesn\'t exist! Check to see if it\'s on the Magic Item Table and check your spelling.')
                ctx.command.reset_cooldown(ctx)
                return

    @commands.cooldown(1, float('inf'), type=commands.BucketType.user)
    @tp.command()
    async def discard(self, ctx , charName):
        channel = ctx.channel
        author = ctx.author
        tpEmbed = discord.Embed()
        tpCog = self.bot.get_cog('Tp')
        charRecords, tpEmbedmsg = await checkForChar(ctx, charName, tpEmbed)
        
        #limit responses to just the original user and the appropriate emotes
        def tpEmbedCheck(r, u):
            sameMessage = False
            if tpEmbedmsg.id == r.message.id:
                sameMessage = True
            return ((str(r.emoji) == '✅') or (str(r.emoji) == '❌')) and u == author and sameMessage

        def discardEmbedCheck(r, u):
            sameMessage = False
            if tpEmbedmsg.id == r.message.id:
                sameMessage = True
            return ((r.emoji in alphaEmojis[:alphaIndex]) or (str(r.emoji) == '❌')) and u == author and sameMessage
        
        #if the character was found in the DB
        if charRecords:
            # If there are no incomplete TP invested items, cancel command
            if charRecords['Current Item'] == "None":
                await channel.send(f'You currently do not have an incomplete item to discard.')
                ctx.command.reset_cooldown(ctx)
                return

            # Split curent items into a list and check with user which item they would like to discard
            currentItemList = charRecords['Current Item'].split(', ')
            discardString = ""
            # set up the mapping between letter emoji and item to discard
            alphaIndex = 0
            for c in currentItemList:
                discardString += f"{alphaEmojis[alphaIndex]}: {c}\n"
                alphaIndex += 1
            
            #if there is only one item, select it by default and skip the selection proces
            currentItem = currentItemList[0]

            if len(currentItemList) > 1:
                tpEmbed.description = f"You have multiple items with TP invested. Choose a magic item to discard.\n\n{discardString}"
                if tpEmbedmsg:
                    await tpEmbedmsg.edit(embed=tpEmbed)
                else:
                    tpEmbedmsg = await channel.send(embed=tpEmbed)
                await tpEmbedmsg.add_reaction('❌')

                try:
                    tReaction, tUser = await self.bot.wait_for("reaction_add", check=discardEmbedCheck , timeout=60)
                except asyncio.TimeoutError:
                    await tpEmbedmsg.delete()
                    await channel.send(f'TP canceled. Use `{commandPrefix}tp discard` command and try again!')
                    ctx.command.reset_cooldown(ctx)
                    return
                await tpEmbedmsg.clear_reactions()
                #remove from the list of current items the one that got mapped to the emoji that the user reacted with
                currentItem = currentItemList.pop(alphaEmojis.index(tReaction.emoji))
            else:
                currentItemList = ["None"]
            
            #store the original string of the item and find the item name without TP
            currentItemStr = currentItem
            currentItem = currentItem.split('(')[0].strip()

            # Item has been chosen, prompt user to be sure.
            tpEmbed.title = f'Discard - {currentItem}'
            tpEmbed.description = f"Are you sure you want to discard this magic item? **You will not be refunded any TP which you have put towards it.**\n\nDiscard **{currentItemStr}**? \n\n✅: Yes\n\n❌: Cancel"
            tpEmbed.set_footer(text=tpEmbed.Empty)
            if tpEmbedmsg:
                await tpEmbedmsg.edit(embed=tpEmbed)
            else:
                tpEmbedmsg = await channel.send(embed=tpEmbed)
            await tpEmbedmsg.add_reaction('✅')
            await tpEmbedmsg.add_reaction('❌')

            try:
                tReaction, tUser = await self.bot.wait_for("reaction_add", check=tpEmbedCheck , timeout=60)
            except asyncio.TimeoutError:
                #cancel if no response was given within the timeframe
                await tpEmbedmsg.delete()
                await channel.send(f'TP canceled. Use `{commandPrefix}tp discard` command and try again!')
                ctx.command.reset_cooldown(ctx)
                return
            else:
                await tpEmbedmsg.clear_reactions()
                if tReaction.emoji == '❌':
                    await tpEmbedmsg.edit(embed=None, content=f"TP canceled. Use `{commandPrefix}tp discard` command and try again!")
                    await tpEmbedmsg.clear_reactions()
                    ctx.command.reset_cooldown(ctx)
                    return
                elif tReaction.emoji == '✅': 
                    tpEmbed.clear_fields()
                    try:
                        #filter out the discarded item and its group from the Grouped property
                        def filterGroupedItems(elem):
                            if(elem.split(":")[1].strip() != currentItem):
                                return True
                            else: return None
                        #update the database
                        filtered_grouped = list(filter( filterGroupedItems, charRecords['Grouped']))
                        playersCollection = db.players
                        playersCollection.update_one({'_id': charRecords['_id']}, {"$set": {"Current Item":', '.join(currentItemList), "Grouped":filtered_grouped}})
                    except Exception as e:
                        print ('MONGO ERROR: ' + str(e))
                        tpEmbedmsg = await channel.send(embed=None, content=f"Uh oh, looks like something went wrong. Please try `{commandPrefix}tp buy` again.")
                    else:
                        tpEmbed.description = f"{currentItem} has been discarded!\n\nCurrent Item(s): {', '.join(currentItemList)}"
                        await tpEmbedmsg.edit(embed=tpEmbed)
                        ctx.command.reset_cooldown(ctx)

    @commands.cooldown(1, float('inf'), type=commands.BucketType.user)
    @tp.command()
    async def abandon(self, ctx , charName, tierNum):
        channel = ctx.channel
        author = ctx.author
        tpEmbed = discord.Embed()
        tpCog = self.bot.get_cog('Tp')


        if tierNum not in ('1','2','3','4') and tierNum.lower() not in [r.lower() for r in roleArray]:
            await channel.send(f"`{tierNum}` is not a valid tier. Please try again with `1`, `2`, `3`, or `4`. Alternatively, type `Junior`, `Journey`, `Elite`, or `True`.")
            ctx.command.reset_cooldown(ctx)
            return

        charRecords, tpEmbedmsg = await checkForChar(ctx, charName, tpEmbed)

        if charRecords:
            def tpEmbedCheck(r, u):
                sameMessage = False
                if tpEmbedmsg.id == r.message.id:
                    sameMessage = True
                return ((str(r.emoji) == '✅') or (str(r.emoji) == '❌')) and u == author and sameMessage
            
            role = 0
            if tierNum.isdigit():
                role = int(tierNum)
            else:
                role = roleArray.index(tierNum.capitalize()) + 1

            if f"T{role} TP" not in charRecords:
                await channel.send(f"You do not have T{role} TP to abandon.")
                ctx.command.reset_cooldown(ctx)
                return
            

            tpEmbed.title = f'Abandon - Tier {role} TP'  
            tpEmbed.description = f"Are you sure you want to abandon your Tier {role} TP? You currently have {charRecords[f'T{role} TP']} Tier {role} TP.\n\n**Note: this action is permanent and cannot be reversed.**\n\n✅: Yes\n\n❌: Cancel"
            tpEmbed.set_footer(text=tpEmbed.Empty)
            if tpEmbedmsg:
                await tpEmbedmsg.edit(embed=tpEmbed)
            else:
                tpEmbedmsg = await channel.send(embed=tpEmbed)
            await tpEmbedmsg.add_reaction('✅')
            await tpEmbedmsg.add_reaction('❌')
            try:
                tReaction, tUser = await self.bot.wait_for("reaction_add", check=tpEmbedCheck , timeout=60)
            except asyncio.TimeoutError:
                await tpEmbedmsg.delete()
                await channel.send(f'TP canceled. Use `{commandPrefix}tp abandon` command and try again!')
                ctx.command.reset_cooldown(ctx)
                return
            else:
                await tpEmbedmsg.clear_reactions()
                if tReaction.emoji == '❌':
                    await tpEmbedmsg.edit(embed=None, content=f"TP canceled. Use `{commandPrefix}tp abandon` command and try again!")
                    await tpEmbedmsg.clear_reactions()
                    ctx.command.reset_cooldown(ctx)
                    return
                elif tReaction.emoji == '✅': 
                    tpEmbed.clear_fields()
                    try:
                        playersCollection = db.players
                        playersCollection.update_one({'_id': charRecords['_id']}, {"$unset": {f"T{role} TP":1}})
                    except Exception as e:
                        print ('MONGO ERROR: ' + str(e))
                        tpEmbedmsg = await channel.send(embed=None, content="Uh oh, looks like something went wrong. Please try `{commandPrefix}tp buy` again.")
                    else:
                        tpEmbed.description = f"You have abandoned {charRecords[f'T{role} TP']} T{role} TP!"
                        await tpEmbedmsg.edit(embed=tpEmbed)
                        ctx.command.reset_cooldown(ctx)


def setup(bot):
    bot.add_cog(Tp(bot))
