import discord
import asyncio
import requests
import re
from discord.utils import get        
from discord.ext import commands
from bfunc import db, commandPrefix, numberEmojis, roleArray, callAPI, checkForChar, traceBack, alphaEmojis

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
            await ctx.channel.send(f'Sorry, the command `{commandPrefix}{ctx.invoked_with}` requires an additional keyword to the command or is invalid, please try again!')
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
        if msg:
            if ctx.command.name == "buy":
                msg += f"Please follow this format:\n`{commandPrefix}tp buy \"character name\" \"magicitem\"`.\n"
            elif ctx.command.name == "discard":
                msg += f"Please follow this format:\n`{commandPrefix}tp discard \"character name\"`.\n"
            elif ctx.command.name == "abandon":
                msg += f"Please follow this format:\n`{commandPrefix}tp abandon \"character name\" tier`.\n"

            ctx.command.reset_cooldown(ctx)
            await ctx.channel.send(msg)
        else:
            ctx.command.reset_cooldown(ctx)
            await traceBack(ctx,error)

      
    @tp.command()
    async def buy(self, ctx , charName, mItem):

        channel = ctx.channel
        author = ctx.author
        tpEmbed = discord.Embed()
        tpCog = self.bot.get_cog('Tp')
        charRecords, tpEmbedmsg = await checkForChar(ctx, charName, tpEmbed)

        if charRecords:
            def tpChoiceEmbedCheck(r, u):
                sameMessage = False
                if tpEmbedmsg.id == r.message.id:
                    sameMessage = True
                return ((str(r.emoji) == '1️⃣' and haveTP) or (charRecords['GP'] >= gpNeeded and str(r.emoji) == '2️⃣') or (str(r.emoji) == '❌')) and u == author
            def tpEmbedCheck(r, u):
                sameMessage = False
                if tpEmbedmsg.id == r.message.id:
                    sameMessage = True
                return ((str(r.emoji) == '✅') or (str(r.emoji) == '❌')) and u == author

            mRecord, tpEmbed, tpEmbedmsg = await callAPI(ctx, tpEmbed, tpEmbedmsg, 'mit',mItem) 
            if mRecord:
                if mRecord['Name'] in charRecords['Magic Items']:
                    await channel.send(f"You already have `{mRecord['Name']}` and cannot TP or gp on another one.")
                    return 

                tierNum = mRecord['Tier']
                gpNeeded = mRecord['GP']
                currentMagicItems = charRecords['Current Item'].split(', ')

                tpBank = [0,0,0,0]
                tpBankString = ""

                for x in range(0,5):
                    if f'T{x} TP' in charRecords:
                      tpBank[x-1] = (float(charRecords[f'T{x} TP']))
                      tpBankString += f"{tpBank[x-1]} T{x} TP, " 

                haveTP = False
                lowestTp = 0

                for tp in range (int(tierNum) - 1, 4):
                    if tpBank[tp] > 0:
                        haveTP = True
                        lowestTP = tp + 1 
                        break


                tpEmbed.title = f"{mRecord['Name']}\nTier {mRecord['Tier']} - {mRecord['TP']} TP / {mRecord['GP']} gp"

                if not haveTP and float(charRecords['GP']) < gpNeeded:
                    await channel.send(f"You do not have Tier {tierNum} TP or gp to acquire `{mRecord['Name']}`.")
                    return
                  
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

                if haveTP:
                    await tpEmbedmsg.add_reaction('1️⃣')
                if float(charRecords['GP']) >= gpNeeded:
                    await tpEmbedmsg.add_reaction('2️⃣')
                await tpEmbedmsg.add_reaction('❌')
                try:
                    tReaction, tUser = await self.bot.wait_for("reaction_add", check=tpChoiceEmbedCheck , timeout=60)
                except asyncio.TimeoutError:
                    await tpEmbedmsg.delete()
                    await channel.send(f'TP canceled. Use `{commandPrefix}tp buy` command and try again!')
                    return
                else:
                    await tpEmbedmsg.clear_reactions()
                    newGP = ""
                    newTP = ""
                    refundTP = 0.0
                    if tReaction.emoji == '❌':
                        await tpEmbedmsg.edit(embed=None, content=f"TP canceled. Use `{commandPrefix}tp buy` command and try again!")
                        await tpEmbedmsg.clear_reactions()
                        return
                    elif tReaction.emoji == '2️⃣':
                        newGP = charRecords['GP'] - gpNeeded
                        if mRecord['Name'] in charRecords['Current Item']:
                            currentMagicItem = re.search('\(([^)]+)', charRecords['Current Item']).group(1)
                            tpSplit= currentMagicItem.split('/')
                            refundTP = float(tpSplit[0])
                            charRecords['Current Item'] = "None"
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


                    if 'Complete' not in newTP and tReaction.emoji == '1️⃣':
                        pass
                    elif charRecords['Magic Items'] == "None":
                        charRecords['Magic Items'] = mRecord['Name']
                    else:
                        charRecords['Magic Items'] = mRecord['Name']
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
                        return
                    else:
                        await tpEmbedmsg.clear_reactions()
                        if tReaction.emoji == '❌':
                            await tpEmbedmsg.edit(embed=None, content=f"TP canceled. Use `{commandPrefix}tp buy` command and try again!")
                            await tpEmbedmsg.clear_reactions()
                            return
                        elif tReaction.emoji == '✅':
                            tpEmbed.clear_fields()
                            try:
                                playersCollection = db.players
                                setData = {"Current Item":charRecords['Current Item'], "Magic Items":charRecords['Magic Items']}
                                statSplit = None
                                unsetTP = False
                                # For the stat books, this will increase the characters stats permanently here.
                                if 'Attunement' not in mRecord and 'Stat Bonuses' in mRecord:
                                    # statSplit MAX NUM STAT +X
                                    statSplit = mRecord['Stat Bonuses'].split(' +')
                                    maxSplit = statSplit[0].split(' ')
                                    oldStat = charRecords[maxSplit[2]]
                                    charRecords[maxSplit[2]] += int(statSplit[1]) 
                                    # If theres a MAX, it won't go over.
                                    if "MAX" in statSplit[0]:
                                        if charRecords[maxSplit[2]] > int(maxSplit[1]):
                                            charRecords[maxSplit[2]] = maxSplit[1]
                                    setData[maxSplit[2]] = charRecords[maxSplit[2]]

                                    # If the stat increased was con, recalc HP
                                    # The old CON is subtracted, and new CON is added.
                                    # If the player can't destroy magic items, this is done here, otherwise... it will need to be done in $info.
                                    if 'CON' in maxSplit[2]:
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
                                    
                
            else:
                await channel.send(f'`{mItem}` doesn\'t exist! Check to see if it\'s on the Magic Item Table and check your spelling.')
                return

    @tp.command()
    async def discard(self, ctx , charName):
        channel = ctx.channel
        author = ctx.author
        tpEmbed = discord.Embed()
        tpCog = self.bot.get_cog('Tp')
        charRecords, tpEmbedmsg = await checkForChar(ctx, charName, tpEmbed)

        def tpEmbedCheck(r, u):
            sameMessage = False
            if tpEmbedmsg.id == r.message.id:
                sameMessage = True
            return ((str(r.emoji) == '✅') or (str(r.emoji) == '❌')) and u == author

        def discardEmbedCheck(r, u):
            sameMessage = False
            if tpEmbedmsg.id == r.message.id:
                sameMessage = True
            return ((r.emoji in alphaEmojis[:alphaIndex]) or (str(r.emoji) == '❌')) and u == author

        if charRecords:
            # If there are no incomplete TP invested items, cancel command
            if charRecords['Current Item'] == "None":
                await channel.send(f'You currently do not have an incomplete item to discard.')
                return

            # Split curent items into a list and check with user which item they would like to discard
            currentItemList = charRecords['Current Item'].split(', ')
            discardString = ""
            alphaIndex = 0
            for c in currentItemList:
                discardString += f"{alphaEmojis[alphaIndex]}: {c}\n"
                alphaIndex += 1

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
                    return
                await tpEmbedmsg.clear_reactions()
                currentItem = currentItemList.pop(alphaEmojis.index(tReaction.emoji))
            else:
                currentItemList = ["None"]
                
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
                await tpEmbedmsg.delete()
                await channel.send(f'TP canceled. Use `{commandPrefix}tp discard` command and try again!')
                return
            else:
                await tpEmbedmsg.clear_reactions()
                if tReaction.emoji == '❌':
                    await tpEmbedmsg.edit(embed=None, content=f"TP canceled. Use `{commandPrefix}tp discard` command and try again!")
                    await tpEmbedmsg.clear_reactions()
                    return
                elif tReaction.emoji == '✅': 
                    tpEmbed.clear_fields()
                    try:
                        playersCollection = db.players
                        playersCollection.update_one({'_id': charRecords['_id']}, {"$set": {"Current Item":', '.join(currentItemList)}})
                    except Exception as e:
                        print ('MONGO ERROR: ' + str(e))
                        tpEmbedmsg = await channel.send(embed=None, content=f"Uh oh, looks like something went wrong. Please try `{commandPrefix}tp buy` again.")
                    else:
                        tpEmbed.description = f"{currentItem} has been discarded!\n\nCurrent Item(s): {', '.join(currentItemList)}"
                        await tpEmbedmsg.edit(embed=tpEmbed)
          
    @tp.command()
    async def abandon(self, ctx , charName, tierNum):
        channel = ctx.channel
        author = ctx.author
        tpEmbed = discord.Embed()
        tpCog = self.bot.get_cog('Tp')


        if tierNum not in ('1','2','3','4') and tierNum.lower() not in [r.lower() for r in roleArray]:
            await channel.send(f"`{tierNum}` is not a valid tier. Please try again with `1`, `2`, `3`, or `4`. Alternatively, type `Junior`, `Journey`, `Elite`, or `True`.")
            return

        charRecords, tpEmbedmsg = await checkForChar(ctx, charName, tpEmbed)

        if charRecords:
            def tpEmbedCheck(r, u):
                sameMessage = False
                if tpEmbedmsg.id == r.message.id:
                    sameMessage = True
                return ((str(r.emoji) == '✅') or (str(r.emoji) == '❌')) and u == author
            
            role = 0
            if tierNum.isdigit():
                role = int(tierNum)
            else:
                role = roleArray.index(tierNum.capitalize()) + 1

            if f"T{role} TP" not in charRecords:
                await channel.send(f"You do not have T{role} TP to abandon.")
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
                return
            else:
                await tpEmbedmsg.clear_reactions()
                if tReaction.emoji == '❌':
                    await tpEmbedmsg.edit(embed=None, content=f"TP canceled. Use `{commandPrefix}tp abandon` command and try again!")
                    await tpEmbedmsg.clear_reactions()
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


def setup(bot):
    bot.add_cog(Tp(bot))
