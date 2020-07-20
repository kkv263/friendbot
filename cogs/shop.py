import discord
import asyncio
import requests
import re
from discord.utils import get        
from discord.ext import commands
from bfunc import db, commandPrefix, numberEmojis, roleArray, checkForChar, noodleRoleArray, callAPI, traceBack

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
            await ctx.channel.send(f'Sorry, the command `{commandPrefix}{ctx.invoked_with}` requires an additional keyword to the command or is invalid, please try again!')
            return
            
        if isinstance(error, commands.MissingRequiredArgument):
            if error.param.name == 'charName':
                msg = "You're missing your character name in the command. "
            elif error.param.name == "buyItem":
                msg = "You're missing the item you want to buy/sell in the command. "
            elif error.param.name == "spellName":
                msg = "You're missing the spell you want to copy in the command. "
        elif isinstance(error, commands.BadArgument):
            # convert string to int failed
            msg = "The amount you want to buy/sell must be a number. "
        if msg:
            if ctx.command.name == "buy":
                msg += f"Please follow this format:\n`{commandPrefix}shop buy \"character name\" \"item\" amount`.\n"
            elif ctx.command.name == "sell":
                msg += f"Please follow this format:\n`{commandPrefix}shop sell \"character name\" \"item\" amount`.\n"
            elif ctx.command.name == "copy":
                msg += f"Please follow this format:\n`{commandPrefix}shop copy \"character name\" \"spellname\"`.\n"
            elif ctx.command.name == "proficiency":
                msg += f"Please follow this format:\n`{commandPrefix}proficiency \"character name\"`.\n"

            ctx.command.reset_cooldown(ctx)
            await ctx.channel.send(msg)
        else:
            ctx.command.reset_cooldown(ctx)
            await traceBack(ctx,error)

      
    @shop.command()
    async def buy(self, ctx, charName, buyItem, amount=1):
        channel = ctx.channel
        author = ctx.author
        shopEmbed = discord.Embed()
        shopCog = self.bot.get_cog('Shop')
        charRecords, shopEmbedmsg = await checkForChar(ctx, charName, shopEmbed)

        if charRecords:
            def shopEmbedCheck(r, u):
                sameMessage = False
                if shopEmbedmsg.id == r.message.id:
                    sameMessage = True
                return ((str(r.emoji) == '✅') or (str(r.emoji) == '❌')) and u == author

            if "spell scroll" in buyItem.lower():
                spellItem = buyItem.lower().replace("spell scroll", "").replace('(', '').replace(')', '')
                sRecord, shopEmbed, shopEmbedmsg = await callAPI(ctx, shopEmbed, shopEmbedmsg, 'spells', spellItem) 

                if not sRecord:
                    await channel.send(f'`{buyItem}` doesn\'t exist or is an unbuyable item! Check to see if it is a valid item and check your spelling.')
                    return

                if sRecord['Level'] > 5:
                    await channel.send(f"You cannot purchase spell scroll `{sRecord['Name']}`; Spell scrolls of levels higher than 5 cannot be purchased.")
                    return
                bRecord, shopEmbed, shopEmbedmsg = await callAPI(ctx, shopEmbed, shopEmbedmsg, 'shop', 'spell scroll') 
                bRecord['Name'] = f"Spell Scroll ({sRecord['Name']})"
    
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

            else:
                bRecord, shopEmbed, shopEmbedmsg = await callAPI(ctx, shopEmbed, shopEmbedmsg, 'shop',buyItem) 
        
            if bRecord:
                gpNeeded = (bRecord['GP'] * amount)

                if "Pack" in bRecord:
                    amount *= bRecord['Pack']

                if float(charRecords['GP']) < gpNeeded:
                    await channel.send(f"You do not have enough GP to purchase `{bRecord['Name']}` - Quantity ({amount})")
                    return

                newGP = charRecords['GP'] - gpNeeded
                shopEmbed.title = f"Buying: {amount} x {bRecord['Name']}: ({charRecords['Name']})"
                shopEmbed.description = f"Are you sure you want to continue this purchase?\n\n**{amount} x {bRecord['Name']} ({gpNeeded}gp): ** \n {charRecords['GP']}gp => {newGP}gp\n\n✅ : Yes\n\n❌: Cancel"

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
                    await channel.send(f'Shop canceled. Use `{commandPrefix}shop buy` command and try again!')
                    return
                else:
                    await shopEmbedmsg.clear_reactions()
                    if tReaction.emoji == '❌':
                        await shopEmbedmsg.edit(embed=None, content=f"Shop canceled. Use `{commandPrefix}shop buy` command and try again!")
                        await shopEmbedmsg.clear_reactions()
                        return
                    elif tReaction.emoji == '✅':
                        if "Consumable" in bRecord:
                            if charRecords['Consumables'] != "None":
                                charRecords['Consumables'] += ', ' + bRecord['Name']
                            else:
                                charRecords['Consumables'] = bRecord['Name']
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
                            shopEmbed.description = f"**{bRecord['Name']} purchased! (x{amount})**\n\n**Current gp**: {newGP}\n"
                            await shopEmbedmsg.edit(embed=shopEmbed)

            else:
                await channel.send(f'`{buyItem}` doesn\'t exist or is an unbuyable item! Check to see if it is a valid item and check your spelling.')
                return

    # TODO: Sell consumables
    @shop.command()
    async def sell(self, ctx , charName, buyItem, amount=1):
        channel = ctx.channel
        author = ctx.author
        shopEmbed = discord.Embed()
        shopCog = self.bot.get_cog('Shop')
        charRecords, shopEmbedmsg = await checkForChar(ctx, charName, shopEmbed)

        if charRecords:
            def shopEmbedCheck(r, u):
                sameMessage = False
                if shopEmbedmsg.id == r.message.id:
                    sameMessage = True
                return ((str(r.emoji) == '✅') or (str(r.emoji) == '❌')) and u == author
            
            def apiEmbedCheck(r, u):
                sameMessage = False
                if shopEmbedmsg.id == r.message.id:
                    sameMessage = True
                return (r.emoji in numberEmojis[:min(len(buyList), 9)]) or (str(r.emoji) == '❌') and u == author

            buyList = []
            buyString = ""
            numI = 0
            if "spell scroll" in buyItem.lower():
                await channel.send(f'You cannot sell spell scrolls to the shop. Please try again with a different item.')
                return

            print(charRecords['Inventory'].keys())

            for k in charRecords['Inventory'].keys():
                if buyItem.lower() in k.lower():
                    buyList.append(k)
                    buyString += f"{numberEmojis[numI]} {k} \n"
                    numI += 1

            if (len(buyList) > 1):
                shopEmbed.add_field(name=f"There seems to be multiple results for `{buyItem}`, please choose the correct one.\nIf the result you are looking for is not here, please cancel the command with ❌ and be more specific.", value=buyString, inline=False)
                if not shopEmbedmsg:
                    shopEmbedmsg = await channel.send(embed=shopEmbed)
                else:
                    await shopEmbedmsg.edit(embed=shopEmbed)

                await shopEmbedmsg.add_reaction('❌')

                try:
                    tReaction, tUser = await self.bot.wait_for("reaction_add", check=apiEmbedCheck, timeout=60)
                except asyncio.TimeoutError:
                    await shopEmbedmsg.delete()
                    await channel.send('Timed out! Try using the command again.')
                    ctx.command.reset_cooldown(ctx)
                    return None, shopEmbed, shopEmbedmsg
                else:
                    if tReaction.emoji == '❌':
                        await shopEmbedmsg.edit(embed=None, content=f"Command canceled. Try using the command again.")
                        await shopEmbedmsg.clear_reactions()
                        ctx.command.reset_cooldown(ctx)
                        return None, shopEmbed, shopEmbedmsg
                shopEmbed.clear_fields()
                await shopEmbedmsg.clear_reactions()
                buyItem = buyList[int(tReaction.emoji[0]) - 1]

            elif len(buyList) == 1:
                buyItem = buyList[0]
            else:
                await channel.send(f'`{buyItem}` doesn\'t exist or is a unsellable magic item! Check to see if it is a valid item and check your spelling.')
                return

            bRecord, shopEmbed, shopEmbedmsg = await callAPI(ctx, shopEmbed, shopEmbedmsg,'shop', buyItem, True) 
        
            if bRecord:
                if 'Magic Item' in bRecord:
                    await channel.send(f"{bRecord['Name']} is a magic item and is not sellable. Please try again with a different item.")
                    return
                
                if f"{bRecord['Name']}" not in charRecords['Inventory']:
                    await channel.send(f"You do not have any {bRecord['Name']} to sell!")
                    return

                elif charRecords['Inventory'][f"{bRecord['Name']}"] < amount:
                    await channel.send(f"You do not have {amount} {bRecord['Name']} to sell!")
                    return 

                if "Pack" in bRecord:
                    bRecord['GP'] /= bRecord['Pack']

                gpRefund = round((bRecord['GP'] / 2) * amount, 2)
                newGP = charRecords['GP'] + gpRefund 
                    
                shopEmbed.title = f"Selling: {amount} x {bRecord['Name']}: ({charRecords['Name']})"
                shopEmbed.description = f"Are you sure you want to sell this?\n\n**{amount} x {bRecord['Name']}: ** (+{gpRefund}gp) \n {charRecords['GP']}gp => {newGP}gp\n\n✅ : Yes\n\n❌: Cancel"

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
                    await channel.send(f'Shop canceled. Use `{commandPrefix}shop buy` command and try again!')
                    return
                else:
                    await shopEmbedmsg.clear_reactions()
                    if tReaction.emoji == '❌':
                        await shopEmbedmsg.edit(embed=None, content=f"Shop canceled. Use `{commandPrefix}tp buy` command and try again!")
                        await shopEmbedmsg.clear_reactions()
                        return
                    elif tReaction.emoji == '✅':
                        charRecords['Inventory'][f"{bRecord['Name']}"] -= amount
                        if charRecords['Inventory'][f"{bRecord['Name']}"] <= 0:
                            del charRecords['Inventory'][f"{bRecord['Name']}"]
                        try:
                            playersCollection = db.players
                            playersCollection.update_one({'_id': charRecords['_id']}, {"$set": {"Inventory":charRecords['Inventory'], 'GP':newGP}})
                        except Exception as e:
                            print ('MONGO ERROR: ' + str(e))
                            shopEmbedmsg = await channel.send(embed=None, content="Uh oh, looks like something went wrong. Please try shop buy again.")
                        else:
                            shopEmbed.description = f"**{bRecord['Name']} sold! (x{amount})** \n\n**Current gp**: {newGP}\n"
                            await shopEmbedmsg.edit(embed=shopEmbed)

            else:
                await channel.send(f'`{buyItem}` doesn\'t exist or is a unsellable magic item! Check to see if it is a valid item and check your spelling.')
                return


    @shop.command()
    async def copy(self, ctx , charName, spellName):
        channel = ctx.channel
        author = ctx.author
        shopEmbed = discord.Embed()
        shopCog = self.bot.get_cog('Shop')
        charRecords, shopEmbedmsg = await checkForChar(ctx, charName, shopEmbed)

        if charRecords:
            #TODO: check for warlock pact of tome and if you want (Book of Ancient Secrets invocation) too
            if 'Wizard' not in charRecords['Class'] and 'Ritual Caster' not in charRecords['Feats'] and 'Warlock' not in charRecords['Class']:
                await channel.send(f"You not have the right class/subclass or feat to copy spells!")
                return 

            consumes = charRecords['Consumables'].split(', ')

            bRecord, shopEmbed, shopEmbedmsg = await callAPI(ctx, shopEmbed, shopEmbedmsg,'spells',spellName)

            if bRecord:
                if 'Spellbook' in charRecords:
                    if bRecord['Name'] in [c['Name'] for c in charRecords['Spellbook']]:
                        await channel.send(f"{charRecords['Name']} does already has the spell `{bRecord['Name']}` to copied in their spellbook!")
                        return  

                if 'Free Spells' not in charRecords:
                    spellCopied = None
                    for c in consumes:
                        print(c)
                        if bRecord['Name'] in c and 'Spell Scroll' in c:
                            spellCopied = True
                            consumes.remove(c)
                            break

                    if not spellCopied:
                        await channel.send(f"{charRecords['Name']} does not have the spell `{bRecord['Name']}` to copy into their spellbook!")
                        return  

                    gpNeeded = bRecord['Level'] * 50
                    if charRecords['Level'] >= 2 and bRecord['School'] in charRecords['Class']:
                        gpNeeded = gpNeeded / 2

                    if gpNeeded > charRecords['GP']:
                        await channel.send(f"{charRecords['Name']} does not have enough gp to copy `{bRecord['Name']}`.")
                        return

                else:
                    gpNeeded = 0
                    if bRecord['Level'] > 1:
                        await channel.send(f"`{bRecord['Name']}` is not a level 1 spell that can be copied into your spellbook.")
                        return     

                    if 'Wizard' not in bRecord['Classes']:
                        await channel.send(f"`{bRecord['Name']}` is not a Wizard spell that can be copied into your spellbook.")
                        return     
                    charRecords['Free Spells'] -= 1


                newGP = charRecords['GP'] - gpNeeded

                if 'Spellbook' not in charRecords:
                    charRecords['Spellbook'] = [{'Name':bRecord['Name'], 'School':bRecord['School']}]
                else:
                    charRecords['Spellbook'].append({'Name':bRecord['Name'], 'School':bRecord['School']})

                try:
                    playersCollection = db.players
                    if 'Free Spells' in charRecords:
                        if charRecords['Free Spells'] == 0:
                            playersCollection.update_one({'_id': charRecords['_id']}, {"$set": {"Consumables":', '.join(consumes), 'GP':newGP, 'Spellbook':charRecords['Spellbook']}, "$unset": {"Free Spells":1} })
                        else:
                            playersCollection.update_one({'_id': charRecords['_id']}, {"$set": {"Consumables":', '.join(consumes), 'GP':newGP, 'Spellbook':charRecords['Spellbook'], 'Free Spells': charRecords['Free Spells']}}) 
                    else:
                        playersCollection.update_one({'_id': charRecords['_id']}, {"$set": {"Consumables":', '.join(consumes), 'GP':newGP, 'Spellbook':charRecords['Spellbook']}})

                except Exception as e:
                    print ('MONGO ERROR: ' + str(e))
                    await channel.send(embed=None, content="Uh oh, looks like something went wrong. Please try shop buy again.")
                else:
                    shopEmbed.title = f"Copying Spell: {bRecord['Name']} ({charRecords['Name']})"
                    shopEmbed.description = f"**{bRecord['Name']} (Level {bRecord['Level']})** copied into your spellbook for {gpNeeded}gp!\nIf you had a spell Scroll {bRecord['Name']}, it has been removed from your inventory. \n\n**Current gp**: {newGP}\n"
                    await channel.send (embed=shopEmbed)

            else:
                await channel.send(f'`{spellName}` doesn\'t exist! Check to see if it is a valid spell and check your spelling.')
                return

    @commands.command(aliases=['prof'])
    async def proficiency(self, ctx , charName):
        channel = ctx.channel
        author = ctx.author
        shopEmbed = discord.Embed()
        shopCog = self.bot.get_cog('Shop')
        charRecords, shopEmbedmsg = await checkForChar(ctx, charName, shopEmbed)
        if charRecords:
            roles = author.roles
            
            noodleRole = None
            for r in roles:
                if 'Noodle' in r.name:
                    noodleRole = r
                    break

            if not noodleRole:
                await channel.send(f"{author.display_name}, you don't have any Noodle roles to purchase a proficiency for {charRecords['Name']}.")
                return    

            noodleLimit = noodleRoleArray.index(noodleRole.name)

            if 'Proficiency' not in charRecords:
                charRecords['Proficiency'] = 0

            if charRecords['Proficiency'] > noodleLimit:
                await channel.send(f"{author.display_name}, your current role {noodleRole.name} does not let you purchase any more proficiencies for {charRecords['Name']}.")
                return

            gpNeeded = 0
            if charRecords['Proficiency'] < 4:
                gpNeeded = charRecords['Proficiency'] * 500 
            
            if gpNeeded > charRecords['GP']:
                await channel.send(f"{charRecords['Name']} does not have enough GP to purchase a proficiency.")
                return

            newGP = charRecords['GP'] - gpNeeded
            charRecords['Proficiency'] += 1


            try:
                playersCollection = db.players
                playersCollection.update_one({'_id': charRecords['_id']}, {"$set": {"Proficiency":charRecords['Proficiency'], 'GP':newGP}})
            except Exception as e:
                print ('MONGO ERROR: ' + str(e))
                await channel.send(embed=None, content="Uh oh, looks like something went wrong. Please try `{commandPrefix}proficiency again.")
            else:
                shopEmbed.title = f"Purchasing Proficiency: ({charRecords['Name']})"
                shopEmbed.description = f"**Proficiency Purchased!** You may now apply one language or tool proficiency of your choice for {charRecords['Name']}.\n\n**Current gp**: {newGP}\n"
                await channel.send (embed=shopEmbed)




def setup(bot):
    bot.add_cog(Shop(bot))
