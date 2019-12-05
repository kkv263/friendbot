import discord
import asyncio
import requests
import re
from discord.utils import get        
from discord.ext import commands
from bfunc import db, headers, commandPrefix, numberEmojis, roleArray, callShopAPI, checkForChar

class Shop(commands.Cog):
    def __init__ (self, bot):
        self.bot = bot
    
    @commands.group()
    async def shop(self, ctx):	
        pass
      
    #TODO: Stat bonuses for unattuned items
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
                shopEmbed.description = f"Are you sure you want to continue this purchase?\n\n**{amount} x {bRecord['Name']}: ** \n {charRecords['GP']}gp => {newGP}gp\n\n✅ : Yes\n\n❌: Cancel"

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

                        if charRecords['Inventory'] == "None":
                            charRecords['Inventory'] = {bRecord['Name'] : amount}
                        else:
                            if bRecord['Name'] not in charRecords['Inventory']:
                                charRecords['Inventory'][bRecord['Name']] = amount 
                            else:
                                charRecords['Inventory'][bRecord['Name']] += amount 
                        try:
                            playersCollection = db.players
                            playersCollection.update_one({'_id': charRecords['_id']}, {"$set": {"Inventory":charRecords['Inventory'], 'GP':newGP}})
                        except Exception as e:
                            print ('MONGO ERROR: ' + str(e))
                            shopEmbedmsg = await channel.send(embed=None, content="Uh oh, looks like something went wrong. Please try shop buy again.")
                        else:
                            shopEmbed.description = f"**GP spent!** Check out what you got!\n\n**{bRecord['Name']}**\n**Current gp**: {newGP}\n"
                            await shopEmbedmsg.edit(embed=shopEmbed)

                    

            else:
                await channel.send(f'`{buyItem}` doesn\'t exist! Check to see if it is a valid item and check your spelling.')
                return


def setup(bot):
    bot.add_cog(Shop(bot))
