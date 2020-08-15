import discord
import asyncio
import requests
import re
from discord.utils import get        
from discord.ext import commands
from bfunc import db, commandPrefix,  alphaEmojis, roleArray, checkForChar, noodleRoleArray, callAPI, traceBack, numberEmojis
from math import floor

class Shop(commands.Cog):
    def __init__ (self, bot):
        self.bot = bot
    
    @commands.group()
    async def shop(self, ctx):	
        shopCog = self.bot.get_cog('Shop')
        pass

    async def cog_command_error(self, ctx, error):
        msg = None

        if isinstance(error, commands.CommandNotFound):
            await ctx.channel.send(f'Sorry, the command **`{commandPrefix}{ctx.invoked_with}`** requires an additional keyword to the command or is invalid, please try again!')
            return
            
        if isinstance(error, commands.MissingRequiredArgument):
            if error.param.name == 'charName':
                msg = "You're missing your character name in the command.\n"
            elif error.param.name == "buyItem":
                msg = "You're missing the item you want to buy/sell in the command.\n"
            elif error.param.name == "spellName":
                msg = "You're missing the spell you want to copy in the command.\n"
        elif isinstance(error, commands.BadArgument):
            # convert string to int failed
            msg = "The amount you want to buy or sell must be a number.\n"
        # bot.py handles this, so we don't get traceback called.
        elif isinstance(error, commands.CommandOnCooldown):
            return

        if msg:
            if ctx.command.name == "buy":
                msg += f"Please follow this format:\n```yaml\n{commandPrefix}shop buy \"character name\" \"item\" #```\n"
            elif ctx.command.name == "sell":
                msg += f"Please follow this format:\n```yaml\n{commandPrefix}shop sell \"character name\" \"item\" #```\n"
            elif ctx.command.name == "copy":
                msg += f"Please follow this format:\n```yaml\n{commandPrefix}shop copy \"character name\" \"spell name\"```\n"
            elif ctx.command.name == "proficiency":
                msg += f"Please follow this format:\n```yaml\n{commandPrefix}proficiency \"character name\"```\n"

            ctx.command.reset_cooldown(ctx)
            await ctx.channel.send(msg)
        else:
            ctx.command.reset_cooldown(ctx)
            await traceBack(ctx,error)

    @commands.cooldown(1, float('inf'), type=commands.BucketType.user)
    @shop.command()
    async def buy(self, ctx, charName, buyItem, amount=1):
        channel = ctx.channel
        author = ctx.author
        shopEmbed = discord.Embed()
        shopCog = self.bot.get_cog('Shop')

        # Check if character exists
        charRecords, shopEmbedmsg = await checkForChar(ctx, charName, shopEmbed)

        if charRecords:
            def shopEmbedCheck(r, u):
                sameMessage = False
                if shopEmbedmsg.id == r.message.id:
                    sameMessage = True
                return sameMessage and ((str(r.emoji) == '✅') or (str(r.emoji) == '❌')) and u == author

            #If player is trying to buy spell scroll, search for spell scroll in DB, and find level it can be bought at 
            if "spell scroll" in buyItem.lower():
                if "spell scroll" == buyItem.lower().strip():
                    await channel.send(f"""Please be more specific with the type of spell scroll which you're purchasing. Use the following format:\n```yaml\n{commandPrefix}shop buy "character name" "Spell Scroll (spell name)"```""")
                    ctx.command.reset_cooldown(ctx)
                    return 

                spellItem = buyItem.lower().replace("spell scroll", "").replace('(', '').replace(')', '')
                sRecord, shopEmbed, shopEmbedmsg = await callAPI(ctx, shopEmbed, shopEmbedmsg, 'spells', spellItem) 

                if not sRecord:
                    if shopEmbedmsg != "Fail":
                        await channel.send(f'**{buyItem}** doesn\'t exist or is an unbuyable item! Check to see if it is a valid item and check your spelling.')
                    ctx.command.reset_cooldown(ctx)
                    return

                if sRecord['Level'] > 5:
                    await channel.send(f"You cannot purchase a spell scroll of **{sRecord['Name']}**. Spell scrolls higher than 5th level cannot be purchased.")
                    ctx.command.reset_cooldown(ctx)
                    return

                bRecord, shopEmbed, shopEmbedmsg = await callAPI(ctx, shopEmbed, shopEmbedmsg, 'shop', 'spell scroll') 
                bRecord['Name'] = f"Spell Scroll ({sRecord['Name']})"
    
                # GP Prices for Spell Scrolls
                if sRecord['Level'] == 0:
                    bRecord['GP'] = 25
                elif sRecord['Level'] == 1:
                    bRecord['GP'] = 75
                elif sRecord['Level'] == 2:
                    bRecord['GP'] = 150
                elif sRecord['Level'] == 3:
                    bRecord['GP'] = 300
                elif sRecord['Level'] == 4:
                    bRecord['GP'] = 500
                elif sRecord['Level'] == 5:
                    bRecord['GP'] = 1000

            # If it's anything else, see if it exists
            else:
                bRecord, shopEmbed, shopEmbedmsg = await callAPI(ctx, shopEmbed, shopEmbedmsg, 'shop',buyItem) 
        
            # Check if there's enough GP to buy
            if bRecord:
                gpNeeded = (bRecord['GP'] * amount)

                if "Pack" in bRecord:
                    amount *= bRecord['Pack']

                if float(charRecords['GP']) < gpNeeded:
                    await channel.send(f"You do not have enough gp to purchase **{amount}**x **{bRecord['Name']}**!")
                    ctx.command.reset_cooldown(ctx)
                    return

                # {charRecords['Name']} is not bolded because [shopEmbed.title] already bolds everything in that's part of the title.
                newGP = round(charRecords['GP'] - gpNeeded , 2)
                shopEmbed.title = f"Shop (Buy): {charRecords['Name']}"

                # Show contents of pack
                def unpackChoiceCheck(r, u):
                    sameMessage = False
                    if shopEmbedmsg.id == r.message.id:
                        sameMessage = True
                    return ((r.emoji in alphaEmojis[:alphaIndex]) or (str(r.emoji) == '❌')) and u == author and sameMessage

                unpackString = ""
                if "Unpack" in bRecord:
                    alphaIndex = 0
                    unpackDict = []
                    unpackChoiceString = ""
                    unpackString = f"**Contents of {bRecord['Name']}**\n"
                    for pk, pv in bRecord["Unpack"].items():
                        if type(pv) == dict:
                            for pvk, pvv in pv.items():
                                unpackDict.append(pvk)
                                unpackChoiceString += f"{alphaEmojis[alphaIndex]}: {pvk}\n"
                                alphaIndex += 1

                            shopEmbed.add_field(name=f"{bRecord['Name']} lets you choose one {pk}.", value=unpackChoiceString, inline=False)
                            if shopEmbedmsg:
                                await shopEmbedmsg.edit(embed=shopEmbed)
                            else:
                                shopEmbedmsg = await channel.send(embed=shopEmbed)
                            await shopEmbedmsg.add_reaction('❌')
                            try:
                                tReaction, tUser = await self.bot.wait_for("reaction_add", check=unpackChoiceCheck, timeout=60)
                            except asyncio.TimeoutError:
                                await shopEmbedmsg.delete()
                                await channel.send(f'Shop cancelled. Try again using the same command:\n```yaml\n{commandPrefix}shop buy \"character name\" \"item\" #```')
                                self.bot.get_command('buy').reset_cooldown(ctx)
                                return
                            else:
                                await shopEmbedmsg.clear_reactions()
                                if tReaction.emoji == '❌':
                                    await shopEmbedmsg.edit(embed=None, content=f"Shop cancelled. Try again using the same command:\n```yaml\n{commandPrefix}shop buy \"character name\" \"item\" #```")
                                    await shopEmbedmsg.clear_reactions()
                                    self.bot.get_command('buy').reset_cooldown(ctx)

                            unpackChoice = unpackDict[alphaEmojis.index(tReaction.emoji)]
                            del bRecord["Unpack"][pk]
                            bRecord['Unpack'][unpackChoice] = pvv

                            await shopEmbedmsg.clear_reactions()
                            shopEmbed.clear_fields()
                        else:
                            unpackString += f"{pk} x{pv}\n"
                    unpackString += "\n"

                shopEmbed.description = f"Are you sure you want to purchase **{amount}**x **{bRecord['Name']}** for **{gpNeeded} gp**?\n\n{unpackString}Current gp: {charRecords['GP']} gp\nNew gp: {newGP} gp\n\n✅: Yes\n\n❌: Cancel"

                if shopEmbedmsg:
                    await shopEmbedmsg.edit(embed=shopEmbed)
                else:
                    shopEmbedmsg = await channel.send(embed=shopEmbed)

                await shopEmbedmsg.add_reaction('✅')
                await shopEmbedmsg.add_reaction('❌')
                try:
                    tReaction, tUser = await self.bot.wait_for("reaction_add", check=shopEmbedCheck , timeout=60)
                except asyncio.TimeoutError:
                    await shopEmbedmsg.delete()
                    await channel.send(f'Shop cancelled. Try again using the same command!')
                    ctx.command.reset_cooldown(ctx)
                    return
                else:
                    await shopEmbedmsg.clear_reactions()
                    if tReaction.emoji == '❌':
                        await shopEmbedmsg.edit(embed=None, content=f"Shop cancelled. Try again using the same command!")
                        await shopEmbedmsg.clear_reactions()
                        ctx.command.reset_cooldown(ctx)
                        return
                    elif tReaction.emoji == '✅':
                        # If it's a consumable, throw it in consumables, otherwise magic item list
                        if "Consumable" in bRecord:
                            if charRecords['Consumables'] != "None":
                                charRecords['Consumables'] += ', ' + bRecord['Name']
                            else:
                                charRecords['Consumables'] = bRecord['Name']
                        # Unpacks all items, ex. Dungeoneer's Pack
                        elif "Unpack" in bRecord:
                            for pk, pv in bRecord["Unpack"].items():
                                if charRecords['Inventory'] == "None":
                                    charRecords['Inventory'] = {pk : int(pv)}
                                else:
                                    if bRecord['Name'] not in charRecords['Inventory']:
                                        charRecords['Inventory'][pk] = int(pv)
                                    else:
                                        charRecords['Inventory'][pk] += int(pv)
                        else:
                            if charRecords['Inventory'] == "None":
                                charRecords['Inventory'] = {f"{bRecord['Name']}" : amount}
                            else:
                                if bRecord['Name'] not in charRecords['Inventory']:
                                    charRecords['Inventory'][f"{bRecord['Name']}"] = amount 
                                else:
                                    charRecords['Inventory'][f"{bRecord['Name']}"] += amount 
                        try:
                            playersCollection = db.players
                            playersCollection.update_one({'_id': charRecords['_id']}, {"$set": {"Inventory":charRecords['Inventory'], 'GP':newGP, "Consumables": charRecords['Consumables']}})
                        except Exception as e:
                            print ('MONGO ERROR: ' + str(e))
                            shopEmbedmsg = await channel.send(embed=None, content="Uh oh, looks like something went wrong. Please try shop buy again.")
                        else:
                            shopEmbed.description = f"**{amount}**x **{bRecord['Name']}** purchased for **{gpNeeded} gp**!\n\n{unpackString}Current gp: {newGP} gp\n"
                            await shopEmbedmsg.edit(embed=shopEmbed)
                            ctx.command.reset_cooldown(ctx)

            else:
                if shopEmbedmsg != "Fail":
                    await channel.send(f'**{buyItem}** doesn\'t exist or is an unbuyable item! Check to see if it is a valid item and check your spelling.')
                ctx.command.reset_cooldown(ctx)
                return

    @commands.cooldown(1, float('inf'), type=commands.BucketType.user)
    @shop.command()
    async def sell(self, ctx , charName, buyItem, amount=1):
        channel = ctx.channel
        author = ctx.author
        shopEmbed = discord.Embed()
        shopCog = self.bot.get_cog('Shop')
        charRecords, shopEmbedmsg = await checkForChar(ctx, charName, shopEmbed)

        # Check if character exists.
        if charRecords:
            def shopEmbedCheck(r, u):
                sameMessage = False
                if shopEmbedmsg.id == r.message.id:
                    sameMessage = True
                return sameMessage and ((str(r.emoji) == '✅') or (str(r.emoji) == '❌')) and u == author
            
            def apiEmbedCheck(r, u):
                sameMessage = False
                if shopEmbedmsg.id == r.message.id:
                    sameMessage = True
                return sameMessage and (r.emoji in alphaEmojis[:min(len(buyList), 9)]) or (str(r.emoji) == '❌') and u == author

            def apiConsumesEmbedCheck(r, u):
                sameMessage = False
                if shopEmbedmsg.id == r.message.id:
                    sameMessage = True
                return sameMessage and (r.emoji in alphaEmojis[:min(len(sellConsumesList), 9)]) or (str(r.emoji) == '❌') and u == author

            buyList = []
            buyString = ""
            numI = 0

            # Check if the item being sold is a spell scroll, if it is... reject it
            if "spell scroll" in buyItem.lower():
                await channel.send(f'You cannot sell spell scrolls to the shop. Please try again with a different item.')
                ctx.command.reset_cooldown(ctx)
                return

            if charRecords['Inventory'] == "None":
                await channel.send(f'You do not have any items to sell. Please try again with an item.')
                ctx.command.reset_cooldown(ctx)
                return

            # Iterate through character's inventory to see if item is sellable
            if charRecords['Inventory'] != "None":
                for k in charRecords['Inventory'].keys():
                    print(k)
                    if buyItem.lower() in k.lower():
                        buyList.append(k)
                        buyString += f"{alphaEmojis[numI]} {k} \n"
                        numI += 1

            # If the query is in the character's consumables, reject it.
            sellConsumesList = []
            sellConsumesStr = ""
            numJ = 0
            for c in charRecords['Consumables'].split(', '):
                if buyItem.lower() in c.lower():
                    sellConsumesStr += f"{alphaEmojis[numJ]} {c} \n"
                    numJ += 1
                    sellConsumesList.append(c)

            # If there are multiple matches user can pick the correct one
            if (len(buyList) > 1):
                shopEmbed.add_field(name=f"There seems to be multiple results for **{buyItem}**! Please choose the correct one.\nIf the result you are looking for is not here, please cancel the command with ❌ and be more specific.", value=buyString, inline=False)
                if not shopEmbedmsg:
                    shopEmbedmsg = await channel.send(embed=shopEmbed)
                else:
                    await shopEmbedmsg.edit(embed=shopEmbed)

                await shopEmbedmsg.add_reaction('❌')

                try:
                    tReaction, tUser = await self.bot.wait_for("reaction_add", check=apiEmbedCheck, timeout=60)
                except asyncio.TimeoutError:
                    await shopEmbedmsg.delete()
                    await channel.send('Timed out! Try again using the command!')
                    ctx.command.reset_cooldown(ctx)
                    return None, shopEmbed, shopEmbedmsg
                else:
                    if tReaction.emoji == '❌':
                        await shopEmbedmsg.edit(embed=None, content=f"Command cancelled. Try again using the command!")
                        await shopEmbedmsg.clear_reactions()
                        ctx.command.reset_cooldown(ctx)
                        return None, shopEmbed, shopEmbedmsg
                shopEmbed.clear_fields()
                await shopEmbedmsg.clear_reactions()
                buyItem = buyList[alphaEmojis.index(tReaction.emoji)]

            elif len(buyList) == 1:
                buyItem = buyList[0]
            elif len(sellConsumesList) > 1:
                shopEmbed.add_field(name=f"There seems to be multiple results for **{buyItem}**! Please choose the correct one.\nIf the result you are looking for is not here, please cancel the command with ❌ and be more specific.", value=sellConsumesStr, inline=False)
                if not shopEmbedmsg:
                    shopEmbedmsg = await channel.send(embed=shopEmbed)
                else:
                    await shopEmbedmsg.edit(embed=shopEmbed)

                await shopEmbedmsg.add_reaction('❌')

                try:
                    tReaction, tUser = await self.bot.wait_for("reaction_add", check=apiConsumesEmbedCheck, timeout=60)
                except asyncio.TimeoutError:
                    await shopEmbedmsg.delete()
                    await channel.send('Timed out! Try again using the command!')
                    ctx.command.reset_cooldown(ctx)
                    return None, shopEmbed, shopEmbedmsg
                else:
                    if tReaction.emoji == '❌':
                        await shopEmbedmsg.edit(embed=None, content=f"Command cancelled. Try again using the command!")
                        await shopEmbedmsg.clear_reactions()
                        ctx.command.reset_cooldown(ctx)
                        return None, shopEmbed, shopEmbedmsg
                shopEmbed.clear_fields()
                await shopEmbedmsg.clear_reactions()
                buyItem = sellConsumesList[alphaEmojis.index(tReaction.emoji)]
            elif len(sellConsumesList) == 1:
                buyItem = sellConsumesList[0]
            else:
                await channel.send(f'**{buyItem}** cannot be sold because it is not in your inventory! Check to see if it is a valid item and check your spelling.')
                ctx.command.reset_cooldown(ctx)
                return

            bRecord, shopEmbed, shopEmbedmsg = await callAPI(ctx, shopEmbed, shopEmbedmsg,'shop', buyItem, True) 
        
            if bRecord:
                # See if item is a magic item (they are unsellable)
                if 'Magic Item' in bRecord:
                    await channel.send(f"**{bRecord['Name']}** is a magic item and is not sellable. Please try again with a different item.")
                    ctx.command.reset_cooldown(ctx)
                    return

                if 'Consumable' in bRecord:
                    await channel.send(f"**{bRecord['Name']}** is a consumable and is not sellable. Please try again with a different item.")
                    ctx.command.reset_cooldown(ctx)
                    return
                
                if f"{bRecord['Name']}" not in charRecords['Inventory']:
                    await channel.send(f"You do not have any **{bRecord['Name']}** to sell!")
                    ctx.command.reset_cooldown(ctx)
                    return

                elif int(charRecords['Inventory'][f"{bRecord['Name']}"]) < amount:
                    await channel.send(f"You do not have **{amount}**x **{bRecord['Name']}** to sell!")
                    ctx.command.reset_cooldown(ctx)
                    return 

                if "Pack" in bRecord:
                    bRecord['GP'] /= bRecord['Pack']

                gpRefund = round((bRecord['GP'] / 2) * amount, 2)
                newGP = round(charRecords['GP'] + gpRefund,2)

# {charRecords['Name']} is not bolded because [shopEmbed.title] already bolds everything in that's part of the title.
                shopEmbed.title = f"Shop (Sell): {charRecords['Name']}"
                shopEmbed.description = f"Are you sure you want to sell **{amount}**x **{bRecord['Name']}** for **{gpRefund} gp**?\nCurrent gp: {charRecords['GP']} gp\nNew gp: {newGP} gp\n\n✅: Yes\n\n❌: Cancel"

                if shopEmbedmsg:
                    await shopEmbedmsg.edit(embed=shopEmbed)
                else:
                    shopEmbedmsg = await channel.send(embed=shopEmbed)

                await shopEmbedmsg.add_reaction('✅')
                await shopEmbedmsg.add_reaction('❌')
                try:
                    tReaction, tUser = await self.bot.wait_for("reaction_add", check=shopEmbedCheck , timeout=60)
                except asyncio.TimeoutError:
                    await shopEmbedmsg.delete()
                    await channel.send(f'Shop cancelled. Try again using the command!')
                    ctx.command.reset_cooldown(ctx)
                    return
                else:
                    await shopEmbedmsg.clear_reactions()
                    if tReaction.emoji == '❌':
                        await shopEmbedmsg.edit(embed=None, content=f"Shop cancelled. Try again using the command!")
                        await shopEmbedmsg.clear_reactions()
                        ctx.command.reset_cooldown(ctx)
                        return
                    elif tReaction.emoji == '✅':
                        charRecords['Inventory'][f"{bRecord['Name']}"] -= amount
                        if int(charRecords['Inventory'][f"{bRecord['Name']}"]) <= 0:
                            del charRecords['Inventory'][f"{bRecord['Name']}"]
                        try:
                            playersCollection = db.players
                            playersCollection.update_one({'_id': charRecords['_id']}, {"$set": {"Inventory":charRecords['Inventory'], 'GP':newGP}})
                        except Exception as e:
                            print ('MONGO ERROR: ' + str(e))
                            shopEmbedmsg = await channel.send(embed=None, content="Uh oh, looks like something went wrong. Please try shop buy again.")
                        else:
                            shopEmbed.description = f"**{amount}**x **{bRecord['Name']}** sold for **{gpRefund} gp**! \n\nCurrent gp: {newGP} gp\n"
                            await shopEmbedmsg.edit(embed=shopEmbed)
                            ctx.command.reset_cooldown(ctx)
            else:
                await channel.send(f'**{buyItem}** doesn\'t exist or is an unsellable magic item! Check to see if it is a valid item and check your spelling.')
                ctx.command.reset_cooldown(ctx)
                return


    @commands.cooldown(1, float('inf'), type=commands.BucketType.user)
    @shop.command()
    async def copy(self, ctx , charName, spellName):
        channel = ctx.channel
        author = ctx.author
        shopEmbed = discord.Embed()
        shopCog = self.bot.get_cog('Shop')
        charRecords, shopEmbedmsg = await checkForChar(ctx, charName, shopEmbed)

        def shopEmbedCheck(r, u):
            sameMessage = False
            if shopEmbedmsg.id == r.message.id:
                sameMessage = True
            return sameMessage and ((str(r.emoji) == '✅') or (str(r.emoji) == '❌')) and u == author

        def bookEmbedCheck(r, u):
            sameMessage = False
            if shopEmbedmsg.id == r.message.id:
                sameMessage = True
            return sameMessage and ((r.emoji in numberEmojis[:2]) or (str(r.emoji) == '❌')) and u == author

        if charRecords:
            #TODO: check for warlock pact of tome and if you want (Book of Ancient Secrets invocation) too
            if 'Wizard' not in charRecords['Class'] and 'Ritual Caster' not in charRecords['Feats']:
                await channel.send(f"You must be a Wizard or have the Ritual Caster feat in order to copy spells into a spellbook!")
                ctx.command.reset_cooldown(ctx)
                return 

            consumes = charRecords['Consumables'].split(', ')

            spellItem = spellName.lower().replace("spell scroll", "").replace('(', '').replace(')', '')
            bRecord, shopEmbed, shopEmbedmsg = await callAPI(ctx, shopEmbed, shopEmbedmsg,'spells',spellItem)

            bookChoice = 0
            gpNeeded = 0
            shopEmbed.title = f"{charRecords['Name']} is copying spell: {bRecord['Name']}"
            if "Ritual Caster" in charRecords['Feats'] and 'Wizard' not in charRecords['Class']:
                bookChoice = "Ritual Book"
            elif "Ritual Caster" not in charRecords['Feats'] and 'Wizard' in charRecords['Class']:
                bookChoice = "Spellbook"
            else:
                shopEmbed.description = f"Which book would you like to copy into?\n\n{numberEmojis[0]}: Ritual Book\n{numberEmojis[1]}: Spell Book"
                if shopEmbedmsg:
                    await shopEmbedmsg.edit(embed=shopEmbed)
                else:
                    shopEmbedmsg = await channel.send(embed=shopEmbed)

                await shopEmbedmsg.add_reaction(numberEmojis[0])
                await shopEmbedmsg.add_reaction(numberEmojis[1])
                await shopEmbedmsg.add_reaction('❌')
                try:
                    tReaction, tUser = await self.bot.wait_for("reaction_add", check=bookEmbedCheck , timeout=60)
                except asyncio.TimeoutError:
                    await shopEmbedmsg.delete()
                    await channel.send(f'Shop canceled. Try again using the same command!')
                    ctx.command.reset_cooldown(ctx)
                    return
                else:
                    await shopEmbedmsg.clear_reactions()
                    if tReaction.emoji == '❌':
                        await shopEmbedmsg.edit(embed=None, content=f"Shop canceled. Try again using the same command!")
                        await shopEmbedmsg.clear_reactions()
                        ctx.command.reset_cooldown(ctx)
                        return
                    elif tReaction.emoji == numberEmojis[1]:
                        bookChoice = "Spellbook"
                    elif tReaction.emoji == numberEmojis[0]:
                        bookChoice = "Ritual Book"

            if bRecord:
                if bookChoice in charRecords:
                        if bRecord['Name'] in [c['Name'] for c in charRecords[bookChoice]]:
                            await channel.send(f"***{charRecords['Name']}*** already has the **{bRecord['Name']}** spell copied in their {bookChoice}!")
                            ctx.command.reset_cooldown(ctx)
                            return  

                if bookChoice == "Ritual Book":
                    ritClass = charRecords["Feats"].split('Ritual Caster (')[1].split(')')[0]
                    if bRecord['Name'] in [c['Name'] for c in charRecords['Ritual Book']]:
                        await channel.send(f"***{charRecords['Name']}*** already has the **{bRecord['Name']}** spell copied in their ritual book!")
                        ctx.command.reset_cooldown(ctx)
                        return 

                    if ritClass not in bRecord['Classes']:
                        await channel.send(f"**{bRecord['Name']}** is not a {ritClass} spell that can be copied into your ritual book.")
                        ctx.command.reset_cooldown(ctx)
                        return

                    if "Ritual" not in bRecord:
                        await channel.send(f"**{bRecord['Name']}** is not a ritual spell, therefore it cannot be copied into your ritual book.")
                        ctx.command.reset_cooldown(ctx)
                        return

                    if charRecords['Level'] < (int(bRecord['Level']) * 2 - 1):
                        await channel.send(f"**{charRecords['Name']}** is not a high enough level to copy a level {bRecord['Level']} spell, therefore it cannot be copied into your ritual book.")
                        ctx.command.reset_cooldown(ctx)
                        return
                    

                if bookChoice == "Spellbook":
                    if 'Wizard' not in bRecord['Classes']:
                        await channel.send(f"**{bRecord['Name']}** is not a Wizard spell that can be copied into your spellbook.")
                        ctx.command.reset_cooldown(ctx)
                        return   

                    if "Chronurgy" in bRecord['Classes'] and "Graviturgy" in bRecord['Classes']:
                        if "Chronurgy" not in charRecords['Class'] and "Graviturgy" not in charRecords['Class']:
                            await channel.send(f"**{bRecord['Name']}** is restricted to the **Chronurgy** and **Graviturgy** schools and cannot be copied into your spellbook.")
                            ctx.command.reset_cooldown(ctx)
                            return

                    elif "Chronurgy" in bRecord['Classes']:
                        if "Chronurgy" not in charRecords['Class']:
                            await channel.send(f"**{bRecord['Name']}** is restricted to the **Chronurgy** school and cannot be copied into your spellbook.")
                            ctx.command.reset_cooldown(ctx)
                            return   
                            
                    elif "Graviturgy" in bRecord['Classes']:
                        if "Graviturgy" not in charRecords['Class']:
                            await channel.send(f"**{bRecord['Name']}** is restricted to the **Graviturgy** school and cannot be copied into your spellbook.")
                            ctx.command.reset_cooldown(ctx)
                            return   

                if 'Free Spells' in charRecords and bookChoice == "Spellbook":
                    requiredSpellLevel = (int(bRecord['Level'])* 2 - 1)
                    if charRecords['Free Spells'][bRecord['Level'] - 1] <= 0 or charRecords["Level"] < requiredSpellLevel:
                        await channel.send(f"**{bRecord['Name']}** is a level {bRecord['Level']} spell that cannot be copied into ***{charRecords['Name']}***'s spellbook! They must be level {requiredSpellLevel} or higher, or you have no more free spells to copy this spell.")
                        ctx.command.reset_cooldown(ctx)
                        return     

                    charRecords['Free Spells'][bRecord['Level'] - 1] -= 1

                elif 'Free Spells' not in charRecords:
                    gpNeeded = bRecord['Level'] * 50
                    if charRecords['Level'] >= 2 and bRecord['School'] in charRecords['Class']:
                        gpNeeded = gpNeeded / 2

                    if gpNeeded > charRecords['GP']:
                        await channel.send(f"***{charRecords['Name']}*** does not have enough gp to copy the **{bRecord['Name']}** spell into their spellbook.")
                        ctx.command.reset_cooldown(ctx)
                        return

                spellCopied = None
                for c in consumes:
                    if bRecord['Name'] in c and 'Spell Scroll' in c:
                        spellCopied = True
                        consumes.remove(c)
                        break

                if consumes == list():
                    consumes = ["None"]

                if not spellCopied:
                    await channel.send(f"***{charRecords['Name']}*** does not have a spell scroll of **{bRecord['Name']}** to copy into their spellbook!")
                    ctx.command.reset_cooldown(ctx)
                    return  


                newGP = charRecords['GP'] - gpNeeded

                if bookChoice not in charRecords:
                    charRecords[bookChoice] = [{'Name':bRecord['Name'], 'School':bRecord['School']}]
                else:
                    charRecords[bookChoice].append({'Name':bRecord['Name'], 'School':bRecord['School']})

                shopEmbed.title = f"Copying a Spell: {charRecords['Name']}"
                shopEmbed.description = f"Are you sure you want to copy the **{bRecord['Name']}** spell for **{gpNeeded} gp**?\nCurrent gp: {charRecords['GP']} gp\nNew gp: {newGP} gp\n\n✅: Yes\n\n❌: Cancel"

                if shopEmbedmsg:
                    await shopEmbedmsg.edit(embed=shopEmbed)
                else:
                    shopEmbedmsg = await channel.send(embed=shopEmbed)

                await shopEmbedmsg.add_reaction('✅')
                await shopEmbedmsg.add_reaction('❌')
                try:
                    tReaction, tUser = await self.bot.wait_for("reaction_add", check=shopEmbedCheck , timeout=60)
                except asyncio.TimeoutError:
                    await shopEmbedmsg.delete()
                    await channel.send(f'Shop cancelled. Try again using the same command!')
                    ctx.command.reset_cooldown(ctx)
                    return
                else:
                    await shopEmbedmsg.clear_reactions()
                    if tReaction.emoji == '❌':
                        await shopEmbedmsg.edit(embed=None, content=f"Shop cancelled. Try again using the same command!")
                        await shopEmbedmsg.clear_reactions()
                        ctx.command.reset_cooldown(ctx)
                        return
                    elif tReaction.emoji == '✅':
                        try:
                            playersCollection = db.players
                            if 'Free Spells' in charRecords:
                                if charRecords['Free Spells'] == [0] * 9:
                                    playersCollection.update_one({'_id': charRecords['_id']}, {"$set": {"Consumables":', '.join(consumes), 'GP':newGP, bookChoice:charRecords[bookChoice]}, "$unset": {"Free Spells":1} })
                                else:
                                    playersCollection.update_one({'_id': charRecords['_id']}, {"$set": {"Consumables":', '.join(consumes), 'GP':newGP, bookChoice:charRecords[bookChoice], 'Free Spells': charRecords['Free Spells']}}) 
                            else:
                                playersCollection.update_one({'_id': charRecords['_id']}, {"$set": {"Consumables":', '.join(consumes), 'GP':newGP, bookChoice:charRecords[bookChoice]}})

                        except Exception as e:
                            print ('MONGO ERROR: ' + str(e))
                            await channel.send(embed=None, content="Uh oh, looks like something went wrong. Please try shop buy again.")
                        else:

                            ordinal = lambda n: "%d%s" % (n,"tsnrhtdd"[(floor(n/10)%10!=1)*(n%10<4)*n%10::4])
                            shopEmbed.title = f"Shop (Copy): {charRecords['Name']}"
                            shopEmbed.description = f"You have copied the **{bRecord['Name']}** spell ({ordinal(bRecord['Level'])} level) into your spellbook for {gpNeeded} gp!\nIf you had a spell scroll of **{bRecord['Name']}**, it has been removed from your inventory. \n\nCurrent gp: {newGP} gp\n"
                            if 'Free Spells' in charRecords:
                                fsString = ""
                                fsIndex = 0
                                for el in charRecords['Free Spells']:
                                    if el > 0:
                                        fsString += f"Level {fsIndex+1}: {el} free spells\n"
                                    fsIndex += 1

                                if fsString:
                                    shopEmbed.add_field(name='Free Spellbook Copies Available', value=fsString , inline=False)

                            await shopEmbedmsg.edit(embed=shopEmbed)
                            ctx.command.reset_cooldown(ctx)

            else:
                await channel.send(f'**{spellName}** doesn\'t exist! Check to see if it is a valid spell and check your spelling.')
                ctx.command.reset_cooldown(ctx)
                return
                
    @commands.group(aliases=['prof'])
    async def proficiency(self, ctx):
        pass
        
    """"
    Extracted purchase menu for simplifying the code
      purchaseOption -> Proficiency or NoodleTraining, to determine which stat to update
      specificationText -> The text to indicate the source of the purchase to the user
      skillFloor -> The point at which the skill option becomes available. After this point there is linear scaling using skillRate
      skillRate -> Because the two versions have different rates at which skill proficiencies can be 
                    gained this is passed through instead of creating an if-else
      gpNeeded -> how much gold the purchase will cost
      charRecords -> the database information of the character being purchased for
      shopEmbed -> the embed message for the shop
      shopEmbedmsg -> the message which is being used to display shopEmbed
      channel -> the channel the interaction is being made in
      author -> who is doing the purchase
    """
    async def purchaseProficiency(self, purchaseOption, specificationText, skillFloor, skillRate, gpNeeded, charRecords, shopEmbed, shopEmbedmsg, channel, author ):
        if gpNeeded > charRecords['GP']:
            await channel.send(f"***{charRecords['Name']}*** does not have enough gp to train a competency in this way.")
            return
        #make sure that only the original author can interact
        def shopEmbedCheck(r, u):
            sameMessage = False
            if shopEmbedmsg.id == r.message.id:
                sameMessage = True
            return sameMessage and ((str(r.emoji) == '✅') or (str(r.emoji) == '❌')) and u == author
        
        #calculate gp after purchase
        newGP = charRecords['GP'] - gpNeeded
        
        #increase the purchase level of the specific option
        charRecords[purchaseOption] += 1
        
        #pick which text to show for the possibility of Skill being an option
        purchasePossibilities = "language or tool"
        if((not charRecords[purchaseOption]<skillFloor) and (charRecords[purchaseOption]-skillFloor)%skillRate == 0):
            purchasePossibilities = purchasePossibilities+" (or skill)"
        
        #update embed text to ask for confirmation
        shopEmbed.title = f"Downtime Training: {charRecords['Name']}"
        shopEmbed.description = f"Are you sure you want to learn your **{specificationText}** {purchasePossibilities} for {gpNeeded} gp?\nCurrent gp: {charRecords['GP']} gp\nNew gp: {newGP} gp\n\n✅: Yes\n\n❌: Cancel"
        
        #if a past message exists update that, otherwise send a new one
        if shopEmbedmsg:
            await shopEmbedmsg.edit(embed=shopEmbed)
        else:
            shopEmbedmsg = await channel.send(embed=shopEmbed)

        #set up menu interaction
        await shopEmbedmsg.add_reaction('✅')
        await shopEmbedmsg.add_reaction('❌')
        try:
            tReaction, tUser = await self.bot.wait_for("reaction_add", check=shopEmbedCheck , timeout=60)
        except asyncio.TimeoutError:
            await shopEmbedmsg.delete()
            await channel.send(f'Downtime Training cancelled. Try again using the same command!')
            return
        else:
            #respond to the user
            await shopEmbedmsg.clear_reactions()
            if tReaction.emoji == '❌':
                await shopEmbedmsg.edit(embed=None, content=f"Downtime Training cancelled. Try again using the same command!")
                await shopEmbedmsg.clear_reactions()
                return
            elif tReaction.emoji == '✅':
                #update the appropriate DB value corresponding to the purchase and update the gold
                try:
                    playersCollection = db.players
                    playersCollection.update_one({'_id': charRecords['_id']}, {"$set": {purchaseOption: charRecords[purchaseOption], 'GP':newGP}})
                except Exception as e:
                    print ('MONGO ERROR: ' + str(e))
                    await shopEmbedmsg.edit(embed=None, content=f"Uh oh, looks like something went wrong. Try again using the same command!")
                else:
                    #Inform of the purchase success
                    shopEmbed.description = f"***{charRecords['Name']}*** has been trained by an instructor and can learn a {purchasePossibilities} of your choice. :tada:\n\nCurrent gp: {newGP} gp\n"
                    await shopEmbedmsg.edit(embed=shopEmbed)
                    
    @proficiency.command()
    async def training(self, ctx , charName):
        channel = ctx.channel
        author = ctx.author
        shopEmbed = discord.Embed()
        charRecords, shopEmbedmsg = await checkForChar(ctx, charName, shopEmbed)
        if charRecords:  
            #create the data entry if it doesnt exist yet
            if 'Proficiency' not in charRecords:
                charRecords['Proficiency'] = 0

            #limit to 5 purchases
            if charRecords['Proficiency'] > 4:
                await channel.send(f"***{charRecords['Name']}*** cannot learn any more competencies.")
                return
            
            # calculate the scaling cost
            gpNeeded = 1000+ charRecords['Proficiency'] * 250
            
            # text used to inform the user which purchase they are making
            textArray = ["1st", "2nd", "3rd", "4th", "5th"]
            
            #call the extracted function
            await self.purchaseProficiency('Proficiency', textArray[charRecords['Proficiency']], 0, 5, gpNeeded, charRecords, shopEmbed, shopEmbedmsg, channel, author )
                
    @proficiency.command()
    async def noodle(self, ctx , charName):
        channel = ctx.channel
        author = ctx.author
        shopEmbed = discord.Embed()
        charRecords, shopEmbedmsg = await checkForChar(ctx, charName, shopEmbed)
        if charRecords:
            roles = author.roles
            
            #check for a noodle role
            noodleRole = None
            for r in roles:
                if 'Noodle' in r.name:
                    noodleRole = r
                    break

            if not noodleRole:
                await channel.send(f"***{author.display_name}***, you don't have any Noodle roles! A Noodle role is required in order for ***{charRecords['Name']}*** to learn a competency in this way.")
                return    
            
            #find which rank it is based on the positioning in the array in bfunc
            noodleLimit = noodleRoleArray.index(noodleRole.name)
            
            #establish the data record if it does not exist yet
            if 'NoodleTraining' not in charRecords:
                charRecords['NoodleTraining'] = 0

            #limit the purchase to only the rank
            if charRecords['NoodleTraining'] > noodleLimit:
                await channel.send(f"**{author.display_name}**, your current **{noodleRole.name}** role does not allow ***{charRecords['Name']}*** to learn a competency in this way.")
                return
            
            #all purchases past the 5th are free, but the formular can never go negative
            gpNeeded = max(0, 500 - charRecords['NoodleTraining'] * 100)
            
            #call the extracted function
            await self.purchaseProficiency('NoodleTraining',noodleRoleArray[charRecords['NoodleTraining']], 3, 2, gpNeeded, charRecords, shopEmbed, shopEmbedmsg, channel, author )
            
           

# Proficiency Training
# Characters can receive training and spend their gp on the services of an instructor to learn a language or pick up proficiency with a tool, but cannot gain expertise through this training. The cost of this training varies depending on how many proficiencies you have already learned through this system:
# • 1st proficiency: 1000 gp
# • 2nd proficiency: 1250 gp
# • 3rd proficiency: 1500 gp
# • 4th proficiency: 1750 gp
# • 5th proficiency: 2000 gp *
# Note: when you learn your fifth proficiency, you can instead choose to learn a skill and gain proficiency in it.

# Congratulatory message for learning a skill:
# {charRecords['Name']} has been trained by an instructor and can learn one language or gain proficiency in a tool of your choice. Alternatively, you can choose to gain proficiency in a skill of your choice.


# Proficiency Training for Noodle roles
# The Noodle roles allow your characters to purchase a language or tool proficiency for a nominal fee. As you acquire new Noodle roles on the server, you must first use all previous Noodle roles' benefits before using any new ones.
# Good: 500
# Elite: 400
# True: 300 *
# Asended: 200
# Immortal: 100 *

# Note: when you become True Noodle and Immortal Noodle, you can instead choose to learn a skill and gain proficiency in it.
# Note: all Noodle roles after Immortal are free, with every second one granting the possibility to purchase a skill proficiency.

# Use the same congratulatory message as above for learning a skill.


# IMPORTANT: include a yes/no prompt for training proficiencies, including current and new gp (before and after the purchase). The relevant code is found on line 109.


def setup(bot):
    bot.add_cog(Shop(bot))
