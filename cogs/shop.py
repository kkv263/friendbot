import discord
import asyncio
import requests
import re
from discord.utils import get        
from discord.ext import commands
from bfunc import db, headers, commandPrefix, numberEmojis, roleArray, callShopAPI, checkForChar, noodleRoleArray

class Shop(commands.Cog):
    def __init__ (self, bot):
        self.bot = bot
    
    @commands.group()
    async def shop(self, ctx):	
        pass
      
    @shop.command()
    async def buy(self, ctx , charName, buyItem, amount=1):
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
        
            bRecord = callShopAPI('Shop',buyItem) 
        
            if bRecord:
                gpNeeded = bRecord['GP'] * amount

                if float(charRecords['GP']) < gpNeeded:
                    await channel.send(f"You do not have enough GP to purchase `{bRecord['Name']}` - Quantity ({amount})")
                    return

                newGP = charRecords['GP'] - gpNeeded
                shopEmbed.title = f"Buying: {amount} x {bRecord['Name']}: ({charRecords['Name']})"
                shopEmbed.description = f"Are you sure you want to continue this purchase?\n\n**{amount} x {bRecord['Name']} (-{gpNeeded}gp): ** \n {charRecords['GP']}gp => {newGP}gp\n\n✅ : Yes\n\n❌: Cancel"

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

                        if charRecords['Inventory'] == "None":
                            charRecords['Inventory'] = {f"{bRecord['Name']}:{bRecord['Type']}" : amount}
                        else:
                            if bRecord['Name'] not in charRecords['Inventory']:
                                charRecords['Inventory'][f"{bRecord['Name']}:{bRecord['Type']}"] = amount 
                            else:
                                charRecords['Inventory'][f"{bRecord['Name']}:{bRecord['Type']}"] += amount 
                        try:
                            playersCollection = db.players
                            playersCollection.update_one({'_id': charRecords['_id']}, {"$set": {"Inventory":charRecords['Inventory'], 'GP':newGP}})
                        except Exception as e:
                            print ('MONGO ERROR: ' + str(e))
                            shopEmbedmsg = await channel.send(embed=None, content="Uh oh, looks like something went wrong. Please try shop buy again.")
                        else:
                            shopEmbed.description = f"**{bRecord['Name']} purchased! (x{amount})**\n\n**Current gp**: {newGP}\n"
                            await shopEmbedmsg.edit(embed=shopEmbed)

                    

            else:
                await channel.send(f'`{buyItem}` doesn\'t exist! Check to see if it is a valid item and check your spelling.')
                return

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
        
            bRecord = callShopAPI('Shop',buyItem) 
        
            if bRecord:
                if f"{bRecord['Name']}:{bRecord['Type']}" not in charRecords['Inventory']:
                    await channel.send(f"You do not have any {bRecord['Name']} to sell!")
                    return

                elif charRecords['Inventory'][f"{bRecord['Name']}:{bRecord['Type']}"] < amount:
                    await channel.send(f"You do not have {amount} {bRecord['Name']} to sell!")
                    return 

                gpRefund = (bRecord['GP'] // 2) * amount
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
                        charRecords['Inventory'][f"{bRecord['Name']}:{bRecord['Type']}"] -= amount
                        if charRecords['Inventory'][f"{bRecord['Name']}:{bRecord['Type']}"] <= 0:
                            del charRecords['Inventory'][f"{bRecord['Name']}:{bRecord['Type']}"]
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
                await channel.send(f'`{buyItem}` doesn\'t exist! Check to see if it is a valid item and check your spelling.')
                return


    # TODO copy spell names
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

            consumes = charRecords['Consumables'].split(' ,')

            bRecord = callShopAPI('Spells',spellName)

            if bRecord:
                spellCopied = None
                for c in consumes:
                    if spellName in c:
                        spellCopied = True
                        consumes.remove(c)
                        break

                if not spellCopied:
                    await channel.send(f"{charRecords['Name']} does not have the spell `{bRecord['Name']}` to copy into thier spellbook!")
                    return  

                gpNeeded = bRecord['Level'] * 50

                if gpNeeded > charRecords['GP']:
                    await channel.send(f"{charRecords['Name']} does not have enough GP to copy `{bRecord['Name']}`")
                    return

                newGP = charRecords['GP'] - gpNeeded

                try:
                    playersCollection = db.players
                    playersCollection.update_one({'_id': charRecords['_id']}, {"$set": {"Consumables":', '.join(consumes), 'GP':newGP}})
                except Exception as e:
                    print ('MONGO ERROR: ' + str(e))
                    await channel.send(embed=None, content="Uh oh, looks like something went wrong. Please try shop buy again.")
                else:
                    shopEmbed.title = f"Copying Spell: {bRecord['Name']} ({charRecords['Name']})"
                    shopEmbed.description = f"**{bRecord['Name']} (Level {bRecord['Level']})** copied into your spellbook!\nSpell Scroll {bRecord['Name']} has been removed from your inventory. \n\n**Current gp**: {newGP}\n"
                    await channel.send (embed=shopEmbed)

            else:
                await channel.send(f'`{spellName}` doesn\'t exist! Check to see if it is a valid item and check your spelling.')
                return

    #TODO: Noodle Proficiency
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
                await channel.send(f"{author.display_name}, you don't have any noodle roles to purchase a proficiency for {charRecords['Name']}.")
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
                shopEmbed.description = f"**Proficiency Purchased!** You may now apply one language or tool proficiency of your choice for {charRecords['Name']}\n\n**Current gp**: {newGP}\n"
                await channel.send (embed=shopEmbed)




def setup(bot):
    bot.add_cog(Shop(bot))