import discord
import asyncio
import requests
import re
from discord.utils import get        
from discord.ext import commands
from bfunc import db, headers, commandPrefix, numberEmojis, roleArray

class Tp(commands.Cog):
    def __init__ (self, bot):
        self.bot = bot
    
    @commands.group()
    async def tp(self, ctx):	
        pass
      
    @tp.command()
    async def buy(self, ctx , charName, mItem):

        channel = ctx.channel
        author = ctx.author
        tpEmbed = discord.Embed()
        tpCog = self.bot.get_cog('Tp')
        charRecords, tpEmbedmsg = await tpCog.checkForChar(ctx, charName, tpEmbed)

        if charRecords:
            def tpChoiceEmbedCheck(r, u):
                sameMessage = False
                if tpEmbedmsg.id == r.message.id:
                    sameMessage = True
                return ((str(r.emoji) == '1️⃣' and f'T{tierNum} TP' in charRecords) or (charRecords['GP'] >= gpNeeded and str(r.emoji) == '2️⃣') or (str(r.emoji) == '❌')) and u == author
            def tpEmbedCheck(r, u):
                sameMessage = False
                if tpEmbedmsg.id == r.message.id:
                    sameMessage = True
                return ((str(r.emoji) == '✅') or (str(r.emoji) == '❌')) and u == author

            mRecord = await tpCog.callAPI('MIT',mItem) 
            if mRecord:
                if mRecord['Name'] in charRecords['Magic Items']:
                    await channel.send(f"You already have `{mRecord['Name']}`, and cannot spend more TP/GP on another one.")
                    return 

                tierNum = mRecord['Tier']
                gpNeeded = mRecord['GP']
                currentMagicItems = charRecords['Current Item'].split(', ')
            
                if f'T{tierNum} TP' in charRecords:
                    tpBank = charRecords[f'T{tierNum} TP']
                else:
                    tpBank = 0

                tpEmbed.title = f"{mRecord['Name']} - Tier {mRecord['Tier']} {mRecord['TP']}TP / {mRecord['GP']}gp"

                if f"T{tierNum} TP" not in charRecords and float(charRecords['GP']) < gpNeeded:
                    await channel.send(f"You do not have Tier {tierNum} TP to spend TP or enough GP  to purchase `{mRecord['Name']}`")
                    return
                  
                elif f"T{tierNum} TP" not in charRecords:
                    tpEmbed.description = f"Do you want to buy **{mRecord['Name']}** with GP or TP?\n\n You have **{tpBank} T{tierNum} TP** and **{charRecords[f'GP']}gp**\n\n~~1️⃣: {mRecord['TP']}TP (Treasure Points)~~ You do not have TP\n2️⃣: {mRecord['GP']}GP (Gold)\n\n❌: Cancel"                 

                elif float(charRecords['GP']) < gpNeeded:
                    tpEmbed.description = f"Do you want to buy **{mRecord['Name']}** with GP or TP?\n\n You have **{tpBank} T{tierNum} TP** and **{charRecords[f'GP']}gp**\n\n1️⃣: {mRecord['TP']}TP (Treasure Points)\n~~2️⃣: {mRecord['GP']}GP (Gold)~~ You do not have enough GP\n\n❌: Cancel"                 

                else:
                    tpEmbed.description = f"Do you want to buy **{mRecord['Name']}** with GP or TP?\n\n You have **{tpBank} T{tierNum} TP** and **{charRecords[f'GP']}gp**\n\n1️⃣: {mRecord['TP']}TP (Treasure Points)\n2️⃣: {mRecord['GP']}GP (Gold)\n\n❌: Cancel"                 
                
                if tpEmbedmsg:
                    await tpEmbedmsg.edit(embed=tpEmbed)
                else:
                    tpEmbedmsg = await channel.send(embed=tpEmbed)

                if f"T{tierNum} TP" in charRecords:
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
                        # TODO: Buy With gold
                        newGP = charRecords['GP'] - gpNeeded
                        if mRecord['Name'] in charRecords['Current Item']:
                            currentMagicItem = re.search('\(([^)]+)', charRecords['Current Item']).group(1)
                            tpSplit= currentMagicItem.split('/')
                            refundTP = float(tpSplit[0])
                            charRecords['Current Item'] = "None"
                            tpEmbed.description = f"Are you sure you want to continue this purchase?\n\n**{mRecord['Name']}** - {charRecords['GP']} => {newGP}gp\nYou will be refunded the TP you have already spent on this item ({refundTP} TP) \n\n✅ : Yes\n\n❌: Cancel"
                        else:
                            tpEmbed.description = f"Are you sure you want to continue this purchase?\n\n**{mRecord['Name']}** - {charRecords['GP']} => {newGP}gp\n\n✅ : Yes\n\n❌: Cancel"

                            
                    elif tReaction.emoji == '1️⃣':
                        if mRecord['Name'] in charRecords['Current Item'] or charRecords['Current Item'] == 'None':
                            if charRecords['Current Item'] == 'None':
                                tpNeeded = float(mRecord['TP'])
                                tpSplit = [0.0, tpNeeded]
                                tpNeeded = float(mRecord['TP'])
                            else:
                                currentMagicItem = re.search('\(([^)]+)', charRecords['Current Item']).group(1)
                                tpSplit= currentMagicItem.split('/')
                                tpNeeded = float(tpSplit[1]) - float(tpSplit[0])

                            tpResult = tpNeeded - float(charRecords[f"T{tierNum} TP"])


                            if tpResult > 0:
                                newTP = f"({float(tpSplit[1]) - tpResult}/{tpSplit[1]})"
                                charRecords[f"T{tierNum} TP"] = 0
                                charRecords['Current Item'] = f"{mRecord['Name']} {newTP}"
                            else:
                                newTP = f"({tpSplit[1]}/{tpSplit[1]}) Complete! :tada:"
                                charRecords[f"T{tierNum} TP"] = abs(float(tpResult))
                                charRecords['Current Item'] = 'None'

                            print(newTP)
                            print(charRecords[f"T{tierNum} TP"])
                            tpEmbed.description = f"Are you sure you want to continue this purchase?\n\n**{mRecord['Name']}** - ({tpSplit[0]}/{tpSplit[1]}) => {newTP}\n**Leftover T{tierNum} TP**: {charRecords[f'T{tierNum} TP']}\n\n✅ : Yes\n\n❌: Cancel"


                    if charRecords['Magic Items'] == "None":
                        charRecords['Magic Items'] = mRecord['Name']
                    else:
                        newMagicItems = charRecords['Magic Items'].split(', ')
                        newMagicItems.append(mRecord['Name'])
                        newMagicItems.sort()
                        charRecords['Magic Items'] = ', '.join(newMagicItems)

                    print(charRecords['Current Item'])
                    print(charRecords['Magic Items'])

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
                                # uncomment when ready
                                if newTP:
                                    if charRecords[f"T{tierNum} TP"] == 0:
                                        playersCollection.update_one({'_id': charRecords['_id']}, {"$set": {"Current Item":charRecords['Current Item'], "Magic Items":charRecords['Magic Items']}, "$unset": {f"T{tierNum} TP":1}})
                                    else:
                                        playersCollection.update_one({'_id': charRecords['_id']}, {"$set": {"Current Item":charRecords['Current Item'], "Magic Items":charRecords['Magic Items'], f"T{tierNum} TP":charRecords[f"T{tierNum} TP"]}})
                                        playersCollection.update_one({'_id': charRecords['_id']}, {"$set": {"Current Item":charRecords['Current Item'], "Magic Items":charRecords['Magic Items'], f"T{tierNum} TP":charRecords[f"T{tierNum} TP"]}})
                                elif newGP:
                                    if refundTP:
                                        if f"T{tierNum} TP" not in charRecords:
                                            charRecords[f"T{tierNum} TP"] = 0 
                                        playersCollection.update_one({'_id': charRecords['_id']}, {"$set": {"Current Item":charRecords['Current Item'], "Magic Items":charRecords['Magic Items'], f"T{tierNum} TP":charRecords[f"T{tierNum} TP"] + refundTP, 'GP':newGP}})
                                    else:
                                        playersCollection.update_one({'_id': charRecords['_id']}, {"$set": {"Current Item":charRecords['Current Item'], "Magic Items":charRecords['Magic Items'], 'GP':newGP}})
                            except Exception as e:
                                print ('MONGO ERROR: ' + str(e))
                                tpEmbedmsg = await channel.send(embed=None, content="Uh oh, looks like something went wrong. Please try tp buy again.")
                            else:
                                if newTP:
                                    tpEmbed.description = f"**TP spent!** Check out what you got!\n\n**{mRecord['Name']}** - {newTP}\n**Current T{tierNum} TP**: {charRecords[f'T{tierNum} TP']}\n\n"
                                elif newGP:
                                    if refundTP:
                                        tpEmbed.description = f"**GP spent!** Check out what you got!\n\n**{mRecord['Name']}**\n**Current gp**: {newGP}\n**Current T{tierNum} TP**: {charRecords[f'T{tierNum} TP'] + refundTP} (Refunded {refundTP})"
                                    else:
                                        tpEmbed.description = f"**GP spent!** Check out what you got!\n\n**{mRecord['Name']}**\n**Current gp**: {newGP}\n"
                                await tpEmbedmsg.edit(embed=tpEmbed)
                                    
                
            else:
                await channel.send(f'`{mItem}` doesn\'t exist! Check to see if it\'s on the MIT and check your spelling.')
                return

    @tp.command()
    async def discard(self, ctx , charName):
        channel = ctx.channel
        author = ctx.author
        tpEmbed = discord.Embed()
        tpCog = self.bot.get_cog('Tp')
        charRecords, tpEmbedmsg = await tpCog.checkForChar(ctx, charName, tpEmbed)

        def tpEmbedCheck(r, u):
            sameMessage = False
            if tpEmbedmsg.id == r.message.id:
                sameMessage = True
            return ((str(r.emoji) == '✅') or (str(r.emoji) == '❌')) and u == author

        if charRecords:
            if charRecords['Current Item'] == "None":
                await channel.send(f'You do not have a current incomplete item to discard.')
                return

            currentItem = charRecords['Current Item'].split('(')[0].strip()

            tpEmbed.title = f'Discard - {currentItem}'
            tpEmbed.description = f"Are you sure you want to discard this magic item? **You will not be refunded TP**.\n\n**{charRecords['Current Item']}** \n\n✅ : Yes\n\n❌: Cancel"
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
                        # uncomment when ready
                        playersCollection.update_one({'_id': charRecords['_id']}, {"$set": {"Current Item":'None'}})
                    except Exception as e:
                        print ('MONGO ERROR: ' + str(e))
                        tpEmbedmsg = await channel.send(embed=None, content="Uh oh, looks like something went wrong. Please try tp buy again.")
                    else:
                        tpEmbed.description = f"I have discarded {currentItem}!"
                        await tpEmbedmsg.edit(embed=tpEmbed)
          
    @tp.command()
    async def abandon(self, ctx , charName, tierNum):
        channel = ctx.channel
        author = ctx.author
        tpEmbed = discord.Embed()
        tpCog = self.bot.get_cog('Tp')


        if tierNum not in ('1','2','3','4') and tierNum.lower() not in [r.lower() for r in roleArray]:
            await channel.send(f"`{tierNum}` is not a valid tier. Please try again with 1,2,3, or 4 or (Junior, Journey, Elite, or True)")
            return

        charRecords, tpEmbedmsg = await tpCog.checkForChar(ctx, charName, tpEmbed)

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
            tpEmbed.description = f"Are you sure you want to abandon your Tier {role} TP? You currently have {charRecords[f'T{role} TP']}\n**This action is permanent and cannot be reversed**.\n\n✅ : Yes\n\n❌: Cancel"
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
                        tpEmbedmsg = await channel.send(embed=None, content="Uh oh, looks like something went wrong. Please try tp buy again.")
                    else:
                        tpEmbed.description = f"I have abandoned your T{role} TP!"
                        await tpEmbedmsg.edit(embed=tpEmbed)

        
    async def checkForChar(self, ctx, char, charEmbed=""):
        channel = ctx.channel
        author = ctx.author
        guild = ctx.guild

        playersCollection = db.players
        charRecords = list(playersCollection.find({"User ID": str(author.id), "Name": {"$regex": char, '$options': 'i' }}))

        if charRecords == list():
            await channel.send(content=f'I was not able to find your character named {char}. Please check your spelling and try again')
            self.char.get_command(ctx.invoked_with).reset_cooldown(ctx)
            return None, None

        else:
            if len(charRecords) > 1:
                infoString = ""
                charRecords = list(charRecords)
                print(charRecords)
                for i in range(0, min(len(charRecords), 9)):
                    infoString += f"{numberEmojis[i]}: {charRecords[i]['Name']}\n"
                
                try:
                    def infoCharEmbedcheck(r, u):
                        sameMessage = False
                        if charEmbedmsg.id == r.message.id:
                            sameMessage = True
                        return (r.emoji in numberEmojis[:min(len(charRecords), 9)]) or (str(r.emoji) == '❌') and u == author

                    charEmbed.add_field(name=f"There seems to be multiple results for `{char}`, please choose the correct character.", value=infoString, inline=False)
                    charEmbedmsg = await channel.send(embed=charEmbed)
                    for num in range(0,min(len(charRecords), 6)): await charEmbedmsg.add_reaction(numberEmojis[num])
                    await charEmbedmsg.add_reaction('❌')
                    tReaction, tUser = await self.bot.wait_for("reaction_add", check=infoCharEmbedcheck, timeout=60)
                except asyncio.TimeoutError:
                    await charEmbedmsg.delete()
                    await channel.send('Character information timed out! Try using the command again')
                    self.char.get_command(ctx.invoked_with).reset_cooldown(ctx)
                    return None, None
                else:
                    if tReaction.emoji == '❌':
                        await charEmbedmsg.edit(embed=None, content=f"Character information canceled. User `{commandPrefix}char info` command and try again!")
                        await charEmbedmsg.clear_reactions()
                        self.char.get_command(ctx.invoked_with).reset_cooldown(ctx)
                        return None, None
                charEmbed.clear_fields()
                await charEmbedmsg.clear_reactions()
                return charRecords[int(tReaction.emoji[0]) - 1], charEmbedmsg

        return charRecords[0], None

    async def callAPI(self, table, query):
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

def setup(bot):
    bot.add_cog(Tp(bot))
