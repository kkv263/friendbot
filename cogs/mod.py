import discord
import asyncio
import re
from discord.utils import get        
from discord.ext import commands
from bfunc import db, commandPrefix, numberEmojis, roleArray, callAPI, checkForChar

class Mod(commands.Cog):
    def __init__ (self, bot):
        self.bot = bot

    @commands.has_any_role('Mod Friend', 'Admins', 'Trial Mod Friend')
    @commands.group(aliases=['m'])
    async def mod(self, ctx):	
        pass

    
    # Lookup a users stats and thier characters or a character if there's no "mention"
    @mod.command()
    async def lookup(self, ctx, dbName, *, name):
        channel = ctx.channel
        guild = ctx.guild
        modEmbed = discord.Embed()
        modEmbedmsg = None
        if dbName == 'user':
            mentions = ctx.message.mentions
            if not mentions:
                mentionMsg = await channel.send(f'{name} is not valid in a user lookup. Please use a user mention instead. (Ex. )')
                await mentionMsg.edit(content = f'{name} is not valid in a user lookup. Please use a user mention instead. (Ex. {mentionMsg.author.mention})')
                return

            collection = db.users
            records = collection.find_one({"User ID": str(mentions[0].id)})

            if records:
                modEmbed.title = f"User Stats: {guild.get_member(int(records['User ID'])).display_name}"
        elif dbName == 'guild':
            collection = db.guilds
            records = collection.find_one({"Name": {"$regex": name, '$options': 'i' }})

            if records:
                modEmbed.title = f"Guild: {records['Name']} (GM: {guild.get_member(int(records['Guildmaster ID'])).display_name})"
        elif dbName == 'char':
            records, modEmbedmsg = await checkForChar(ctx, name, modEmbed, mod=True)
            if records:
                modEmbed.title = f"Character: {records['Name']} ({guild.get_member(int(records['User ID'])).display_name})"

        else:
            await channel.send(f'{dbName} is not valid. Please try `user`, `guild`, or `char`')
            return

        if not records:
            await channel.send(f'The {dbName} `{name}` does not exist. Please try again')
            return

        recordString = ""
        for key, value in records.items():
            if key != "_id":
                recordString += f"{key} : {value}"
                if key in ("CP", 'T1 TP', 'T2 TP', 'T3 TP', 'T4 TP', 'GP', 'Reputation', 'Games', 'Proficiency', 'Current Item', 'Proficiency', 'Noodles', 'Guilds'):
                    recordString+= " 🔹"    
                elif key in ('Magic Items', 'Consumables', 'Inventory'):
                    recordString += " 🔸"
                recordString+= "\n"    

        modEmbed.description = recordString
        modEmbed.set_footer(text="🔹 - These fields can be edited using the mod edit command\n🔸 - These fields can be edited using the mod add or mod remove command")

        if modEmbedmsg:
            await modEmbedmsg.edit(embed=modEmbed)
        else:
            await channel.send(embed=modEmbed)
            


    # add stuff to char or user
    @mod.command()
    async def remove(self, ctx, dbName, name, removeKey, removeValue):
        channel = ctx.channel
        author = ctx.author
        guild = ctx.guild
        charEmbed = discord.Embed()
        if dbName == "char":
            charRecords, charEmbedmsg = await checkForChar(ctx, name, charEmbed)
            if charRecords:
                if removeKey == "Magic Items":
                    mRecord = callAPI('mit',removeValue) 
                    if mRecord:
                        removeRecords = charRecords['Magic Items'].split(', ')
                        if mRecord['Name'] in removeRecords and charRecords['Magic Items'] != "None":
                            removeRecords.remove(mRecord['Name'])
                            if removeRecords == list():
                                removeRecords = 'None'
                            else:
                                removeRecords = ', '.join(removeRecords)
                            removeValue = mRecord['Name']
                            attunedRecords = charRecords['Attuned']
                            if mRecord['Name'] in charRecords['Attuned']:
                                attunedRecords = charRecords['Attuned'].split(', ')
                                attunedRecords.remove(mRecord['Name'])
                                attunedRecords = ', '.join(attunedRecords)
                            removeDict = {removeKey : removeRecords, 'Attuned': attunedRecords}
                        else:
                            await channel.send(f"The magic item `{mRecord['Name']}` is not inside {charRecords['Name']}'s magic item list to remove")
                            return 

                    else:
                        cRecord = callAPI('rit',removeValue)
                        if cRecord and 'Consumable' not in  cRecord:
                            removeRecords = charRecords['Magic Items'].split(', ')
                            if cRecord['Name'] in removeRecords and charRecords['Magic Items'] != "None": 
                                removeRecords.remove(cRecord['Name'])
                                if removeRecords == list():
                                    removeRecords = 'None'
                                else:
                                    removeRecords = ', '.join(removeRecords)
                                removeValue = cRecord['Name']
                                removeDict = {removeKey : removeRecords}
                            else:
                                await channel.send(f"The magic item `{cRecord['Name']}` is not inside {charRecords['Name']}'s magic item list to remove or is not a magic item.")
                                return
                        else:
                            await channel.send(f'The magic item `{removeValue}` does not exist or there are no items to remove. Please try again')
                            return 

                elif removeKey == "Inventory":
                    iRecord = callAPI('shop', removeValue);
                    if iRecord:
                        removeRecords = charRecords['Inventory']
                        print(removeRecords)
                        if f"{iRecord['Name']}:{iRecord['Type']}" in removeRecords and removeRecords != "None":
                            del removeRecords[f"{iRecord['Name']}:{iRecord['Type']}"]
                            if removeRecords == dict():
                                removeRecords = 'None'
                            removeDict = {removeKey : removeRecords}
                        else:
                            await channel.send(f"The item `{iRecord['Name']}` is not inside {charRecords['Name']}'s inventory to remove")
                            return

                    else:
                        await channel.send(f"The item `{removeValue}`does not exist or is not a valid shop inventory item")
                        return 
                    
                elif removeKey == "Consumables":
                    cRecord = callAPI('rit',removeValue)
                    if cRecord and 'Consumable' in  cRecord:
                        removeRecords = charRecords['Consumables'].split(', ')
                        if cRecord['Name'] in removeRecords and charRecords['Consumables'] != "None": 
                            removeRecords.remove(cRecord['Name'])
                            if removeRecords == list():
                                removeRecords = 'None'
                            else:
                                removeRecords = ', '.join(removeRecords)
                            removeValue = cRecord['Name']
                            removeDict = {removeKey : removeRecords}
                        else:
                            await channel.send(f"The magic item `{cRecord['Name']}` is not inside {charRecords['Name']}'s consumable list to remove")
                            return

                    else:
                        await channel.send(f"The item `{removeValue}`does not exist or is not a consumable")
                        return 

                else:
                    await channel.send(f"There's no field called `{removeKey}` Please try again")
                    return  
                                
                try:
                    playersCollection = db.players
                    playersCollection.update_one({'_id': charRecords['_id']}, {"$set": removeDict})
                except Exception as e:
                    print ('MONGO ERROR: ' + str(e))
                    await channel.send(embed=None, content="Uh oh, looks like something went wrong. Please try shop buy again.")
                else:
                    await channel.send(f"The value `{removeValue}` has been removed from field {removeKey} for {charRecords['Name']}")

        else:
            await channel.send(f'The {dbName} `{name}` does not have any fields that use this remove command. Please try again')
            return

    @mod.command()
    async def add(self, ctx, dbName, name, addKey, addValue):
        channel = ctx.channel
        author = ctx.author
        guild = ctx.guild
        charEmbed = discord.Embed()
        if dbName == "char":
            charRecords, charEmbedmsg = await checkForChar(ctx, name, charEmbed)
            if charRecords:
                if addKey == "Magic Items":
                    mRecord = callAPI('mit',addValue) 
                    if mRecord:
                        addRecords = charRecords['Magic Items'].split(', ')
                        if mRecord['Name'] not in addRecords:
                            if charRecords['Magic Items'] == "None":
                                addRecords = list()
                            addRecords.append(mRecord['Name'])
                            addRecords = ', '.join(addRecords)
                            addValue = mRecord['Name']
                            addDict = {addKey : addRecords}
                        else:
                            await channel.send(f"The magic item `{mRecord['Name']}` is already in {charRecords['Name']}'s magic item list.")
                            return 

                    else:
                        cRecord = callAPI('rit',addValue)
                        if cRecord and 'Consumable' not in cRecord:
                            addRecords = charRecords['Magic Items'].split(', ')
                            if cRecord['Name'] not in addRecords: 
                                if charRecords['Magic Items'] == "None":
                                    addRecords = list()
                                addRecords.append(cRecord['Name'])
                                addRecords = ', '.join(addRecords)
                                addValue = cRecord['Name']
                                addDict = {addKey : addRecords}
                            else:
                                await channel.send(f"The magic item `{cRecord['Name']}` is already in {charRecords['Name']}'s magic item list.")
                                return
                        else:
                            await channel.send(f'The magic item `{addValue}` does not exist, or is not a magic item. Please try again')
                            return 
                elif addKey == "Inventory":
                    iRecord = callAPI('shop', addValue);
                    if iRecord:
                        addRecords = charRecords['Inventory']
                        if addRecords == 'None':
                            addRecords = dict()
                        if f"{iRecord['Name']}:{iRecord['Type']}" in addRecords:
                            addRecords[f"{iRecord['Name']}:{iRecord['Type']}"] += 1
                        else:
                            addRecords[f"{iRecord['Name']}:{iRecord['Type']}"] = 1
                        addDict = {addKey : addRecords}

                    else:
                        await channel.send(f"The item `{addValue}`does not exist or is not a valid shop inventory item")
                        return 
                elif addKey == "Consumables":
                    cRecord = callAPI('rit',addValue)
                    if cRecord and 'Consumable' in cRecord:
                        addRecords = charRecords['Consumables'].split(', ')
                        if charRecords['Consumables'] == "None":
                            addRecords = list()
                        addRecords.append(cRecord['Name'])
                        addRecords = ', '.join(addRecords)
                        addValue = cRecord['Name']
                        addDict = {addKey : addRecords}

                    else:
                        await channel.send(f"The item `{addValue}`does not exist or is not a consumable")
                        return 

                else:
                    await channel.send(f"There's no field called `{addKey}` Please try again")
                    return  
                
                                
                try:
                    playersCollection = db.players
                    playersCollection.update_one({'_id': charRecords['_id']}, {"$set": addDict})
                except Exception as e:
                    print ('MONGO ERROR: ' + str(e))
                    await channel.send(embed=None, content="Uh oh, looks like something went wrong. Please try shop buy again.")
                else:
                    await channel.send(f"The value `{addValue}` has been added to field {addKey} for {charRecords['Name']}")
        else:
            await channel.send(f'The {dbName} `{name}` does not have any fields that use this add command. Please try again')
            return


def setup(bot):
    bot.add_cog(Mod(bot))
