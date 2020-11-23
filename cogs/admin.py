import discord
import asyncio
import requests
import re
from discord.utils import get        
from discord.ext import commands
import sys
import traceback
from pymongo import UpdateOne
from pymongo.errors import BulkWriteError
from bfunc import db, callAPI, traceBack, settingsRecord


def admin_or_owner():
    async def predicate(ctx):
        
        role = get(ctx.message.guild.roles, name = "A d m i n")
        output = (role in ctx.message.author.roles) or ctx.message.author.id in [220742049631174656, 203948352973438995]
        return  output
    return commands.check(predicate)

class Admin(commands.Cog, name="Admin"):
    def __init__ (self, bot):
        self.bot = bot
    
    @commands.group()
    async def react(self, ctx):	
        pass
    
    
    @react.command()
    @admin_or_owner()
    async def printGuilds(self, ctx):
        out = "All guild channels:\n"
        ch = ctx.guild.get_channel(452704598440804375)
        for channel in ch.text_channels:
            out+="  "+channel.mention+"\n"
        await ctx.channel.send(content=out)
    
    #this function allows you to specify a channel and message and have the bot react with a given emote
    #Not tested with emotes the bot might not have access to
    @react.command()
    @admin_or_owner()
    async def add(self, ctx, channel: int, msg: int, emote: str):
        ch = ctx.guild.get_channel(channel)
        message = await ch.fetch_message(msg)
        await message.add_reaction(emote)
        await ctx.message.delete()
    
    #Allows the sending of messages
    @commands.command()
    @admin_or_owner()
    async def send(self, ctx, channel: int, *, msg: str):
        ch = ctx.guild.get_channel(channel)
        await ch.send(content=msg)
    
    #this function allows you to specify a channel and message and have the bot remove its reaction with a given emote
    #Not tested with emotes the bot might not have access to
    @react.command()
    @admin_or_owner()
    async def remove(self, ctx, channel: int, msg: int, emote: str):
        ch = ctx.guild.get_channel(channel)
        message = await ch.fetch_message(msg)
        await message.remove_reaction(emote, self.bot.user)
        await ctx.message.delete()

    settingsRecord["ddmrw"]
        
    @commands.command()
    async def startDDMRW(self, ctx):
        global settingsRecord
        settingsRecord["ddmrw"] = True
        await ctx.channel.send("Let the games begin!")

    @commands.command()
    async def endDDMRW(self, ctx):
        global settingsRecord
        settingsRecord["ddmrw"] = False        
        await ctx.channel.send("Until next month!")
    
    
    @commands.command()
    @admin_or_owner()
    async def goldUpdate(self, ctx, tier: int, tp: int, gp: int):
        try:
            db.mit.update_many(
               {"Tier": tier, "TP": tp},
               {"$set" : {"GP" : gp}},
            )
            await ctx.channel.send(content=f"Successfully updated the GP cost of all T{tier} items costing {tp} TP to {gp} GP.")
    
        except Exception as e:
            traceback.print_exc()
            
    @commands.command()
    @admin_or_owner()
    async def tpUpdate(self, ctx, tier: int, tp: int, tp2: int):
        try:
            db.mit.update_many(
               {"Tier": tier, "TP": tp},
               {"$set" : {"TP" : tp2}},
            )
            await ctx.channel.send(content=f"Successfully updated the TP cost of all T{tier} items costing {tp} TP to {tp2} TP.")
    
        except Exception as e:
            traceback.print_exc()
            
    @commands.command()
    @admin_or_owner()
    async def printTierItems(self, ctx, tier: int, tp: int):
        try:
            items = list(db.mit.find(
               {"Tier": tier, "TP": tp},
            ))
            
            out = f"Items in Tier {tier} costing TP {tp}:\n"
            def alphaSort(item):
                if "Grouped" in item:
                    return item["Grouped"]
                else:
                    return item["Name"]
            
            items.sort(key = alphaSort)
            for i in items:
                if "Grouped" in i:
                    out += i["Grouped"]
                else:
                    out += i["Name"]
                out += f" GP {i['GP']}\n"
            length = len(out)
            while(length>2000):
                x = out[:2000]
                x = x.rsplit("\n", 1)[0]
                await ctx.channel.send(content=x)
                out = out[len(x):]
                length -= len(x)
            await ctx.channel.send(content=out)
    
        except Exception as e:
            traceback.print_exc()        
    
    @commands.command()
    @admin_or_owner()
    async def ritRework(self, ctx):
        try:
            db.rit.update_many(
               {"Type": {"$exists" : False}},
                {"$set" : {"Type": "Magic Items"}}
            )
            await ctx.channel.send(content=f"Successfully updated the rit.")
    
        except Exception as e:
            traceback.print_exc()
            
    @commands.command()
    @admin_or_owner()
    async def removeAllGID(self, ctx):
        msg = ctx.channel.send("Are you sure you want to remove every GID entry from characters in the database?\n No: ❌\n Yes: ✅")
        author = ctx.author
        
        if(not self.doubleVerify(ctx, msg)):
            return
        try:
            db.players.update_many(
               {"GID": {"$exists": True}},
               {"$unset" : {"GID" : 1}},
            )
            await msg.edit(content=f"Successfully remove the GID entry from all characters.")
    
        except Exception as e:
            traceback.print_exc()
    
    @commands.command()
    @admin_or_owner()
    async def removeAllPlayers(self, ctx):
        msg = ctx.channel.send("Are you sure you want to remove every character in the database?\n No: ❌\n Yes: ✅")
        author = ctx.author
        
        if(not self.doubleVerify(ctx, msg)):
            return
        try:
            count = db.players.delete_many(
               {}
            )
            await msg.edit(content=f"Successfully deleted {count.deletedCount} characters.")
    
        except Exception as e:
            traceback.print_exc()
      
    @commands.command()      
    @admin_or_owner()
    async def removeUserCharacters(self, ctx, userID):
        msg = await ctx.channel.send("Are you sure you want to remove every character in the database?\n No: ❌\n Yes: ✅")
        author = ctx.author
        
        if(not await self.doubleVerify(ctx, msg)):
            return
        
        try:
            count = db.players.delete_many(
               {"User ID": userID}
            )
            await msg.edit(content=f"Successfully deleted {count.deletedCount} characters.")
    
        except Exception as e:
            traceback.print_exc()        
    
            
    @commands.command()
    @admin_or_owner()
    async def moveItem(self, ctx, item, tier: int, tp: int):
        
        moveEmbed = discord.Embed()
        moveEmbedmsg = None
        
        rRecord, moveEmbed, moveEmbedmsg = await callAPI(ctx, moveEmbed, moveEmbedmsg, 'mit', item)
        if(moveEmbedmsg):
            await moveEmbedmsg.edit(embed=None, content=f"Are you sure you want to move and refund {rRecord['Name']}?\n No: ❌\n Yes: ✅")
        else:
            moveEmbedmsg = await  ctx.channel.send(content=f"Are you sure you want to move and refund {rRecord['Name']}?\n No: ❌\n Yes: ✅")
        author = ctx.author
        refundTier = f'T{rRecord["Tier"]} TP'
        
        if(not await self.doubleVerify(ctx, moveEmbedmsg)):
            return
        
        try:
            targetTierInfoItem = db.mit.find_one( {"TP": tp, "Tier": tier})
            print(targetTierInfoItem)
            updatedGP = rRecord["GP"]
            if(targetTierInfoItem):
                updatedGP = targetTierInfoItem["GP"]
                
            returnData = self.characterEntryItemRemovalUpdate(ctx, rRecord, "Current Item", refundTier, tp)
                                                        
            db.mit.update_one( {"_id": rRecord["_id"]},
                                {"$set" : {"Tier" : tier, "TP" : tp, "GP": updatedGP}})
        except Exception as e:
            print("ERRORpr", e)
            traceback.print_exc()
            await traceBack(ctx,e)
            return
        
        print(returnData)
        
        refundData = list(map(lambda item: UpdateOne({'_id': item['_id']}, item['fields']), returnData))
        
        try:
            if(len(refundData)>0):
                db.players.bulk_write(refundData)
        except BulkWriteError as bwe:
            print(bwe.details)
            # if it fails, we need to cancel and use the error details
            return
        await moveEmbedmsg.edit(content="Completed")
    
    def characterEntryItemRemovalUpdate(self, ctx, rRecord, category, refundTier, tp):
        characters = list( db.players.find({"Current Item": {"$regex": f".*?{rRecord['Name']}"}}))
        returnData = []
        print(rRecord)
        for char in characters:
            print(char["Name"])
            items = char[category].split(", ")
            removeItem = None
            refundTP = 0
            for item in items:
                print(item)
                nameSplit = item.split("(")
                if(nameSplit[0].strip() == rRecord["Name"]):
                    removeItem = item
                    refundTP = float(nameSplit[1].split("/")[0])
                    
            print("Remove: ", removeItem)
            
            if(refundTier in char):
                refundTP += char[refundTier]
            if not removeItem:
                continue
                
            items.remove(removeItem)
            if(len(items)==0):
                items.append("None")
            
            entry = {'_id': char["_id"],  
                                "fields": {"$set": {refundTier: refundTP, 
                                                    category: ", ".join(items)}}}

            if("Grouped" in rRecord):
                groupedPair = rRecord["Grouped"]+" : "+rRecord["Name"]
                print(list(char["Grouped"]))
                print(groupedPair)
                updatedGrouped = list(char["Grouped"])
                updatedGrouped.remove(groupedPair)
                entry["fields"]["$set"]["Grouped"] = updatedGrouped
            
            returnData.append(entry)
        return returnData
        
    async def doubleVerify(self, ctx, embedMsg):
        def apiEmbedCheck(r, u):
            sameMessage = False
            if embedMsg.id == r.message.id:
                sameMessage = True
            return ((str(r.emoji) == '❌') or (str(r.emoji) == '✅')) and u == ctx.author and sameMessage
            
        await embedMsg.add_reaction('❌')
        try:
            tReaction, tUser = await self.bot.wait_for("reaction_add", check=apiEmbedCheck, timeout=60)
        except asyncio.TimeoutError:
            #stop if no response was given within the timeframe
            await embedMsg.edit(conten='Timed out! Try using the command again.')
            return False
        else:
            #stop if the cancel emoji was given
            if tReaction.emoji == '❌':
                await embedMsg.edit(embed=None, content=f"Command cancelled.")
                await embedMsg.clear_reactions()
                return False
            elif tReaction.emoji == '✅':
                await embedMsg.clear_reactions()
            else:
                await embedMsg.edit(embed=None, content=f"Command cancelled. Unexpected reaction given.")
                return False
        await embedMsg.edit(content=f"Since this process is irreversible, ARE YOU SURE?\n No: ❌\n Yes: ✅")
        
        await embedMsg.add_reaction('❌')
        try:
            tReaction, tUser = await self.bot.wait_for("reaction_add", check=apiEmbedCheck, timeout=60)
        except asyncio.TimeoutError:
            #stop if no response was given within the timeframe
            await embedMsg.edit(conten='Timed out! Try using the command again.')
            return False
        else:
            #stop if the cancel emoji was given
            if tReaction.emoji == '❌':
                await embedMsg.edit(embed=None, content=f"Command cancelled.")
                await embedMsg.clear_reactions()
                return False
            elif tReaction.emoji == '✅':
                await embedMsg.clear_reactions()
            else:
                await embedMsg.edit(embed=None, content=f"Command cancelled. Unexpected reaction given.")
                return False
        return True
    
    @commands.command()
    @admin_or_owner()
    async def removeItem(self, ctx, item):
        
        removeEmbed = discord.Embed()
        removeEmbedmsg = None
        
        rRecord, removeEmbed, removeEmbedmsg = await callAPI(ctx, removeEmbed, removeEmbedmsg, 'mit', item)
        if(removeEmbedmsg):
            await removeEmbedmsg.edit(embed=None, content=f"Are you sure you want to remove and refund {rRecord['Name']}?\n No: ❌\n Yes: ✅")
        else:
            removeEmbedmsg = await  ctx.channel.send(content=f"Are you sure you want to move and refund {rRecord['Name']}?\n No: ❌\n Yes: ✅")
        author = ctx.author
        refundTier = f'TP {rRecord["Tier"]}'
        
        if(not await self.doubleVerify(ctx, removeEmbedmsg)):
            return
        
        try:
            returnData = self.characterEntryItemRemovalUpdate(ctx, rRecord, "Magic Items")
                                                        
            db.mit.remove_one( {"_id": rRecord["_id"]})
        except Exception as e:
            print("ERRORpr", e)
            traceback.print_exc()
            await traceBack(ctx,e)
            return
        
        print(returnData)
        
        refundData = list(map(lambda item: UpdateOne({'_id': item['_id']}, item['fields']), returnData))
        
        try:
            if(len(refundData)>0):
                db.players.bulk_write(refundData)
        except BulkWriteError as bwe:
            print(bwe.details)
            # if it fails, we need to cancel and use the error details
            return
        await removeEmbedmsg.edit(content="Completed")
        
    @commands.command()
    @admin_or_owner()
    async def killbot(self, ctx):
        await self.bot.logout()
    
    @commands.command()
    @admin_or_owner()
    async def reload(self, ctx, cog: str):
        
        try:
            self.bot.reload_extension('cogs.'+cog)
            print(f"{cog} has been reloaded.")
            await ctx.channel.send(cog+" has been reloaded")
        except commands.ExtensionNotLoaded as e:
            try:
                self.bot.load_extension("cogs." + cog)
                print(f"{cog} has been added.")
                await ctx.channel.send(cog+" has been reloaded")
            except (discord.ClientException, ModuleNotFoundError):
                print(f'Failed to load extension {cog}.')
                traceback.print_exc()
        except Exception as e:
            print(f'Failed to load extension {cog}.')
            traceback.print_exc()


def setup(bot):
    bot.add_cog(Admin(bot))
