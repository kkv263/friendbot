import discord
import asyncio
import re
from discord.utils import get        
from discord.ext import commands
from datetime import datetime, timezone,timedelta
from bfunc import callAPI, db, traceBack, timeConversion, calculateTreasure
from pymongo import UpdateOne
from pymongo.errors import BulkWriteError

class Log(commands.Cog):
    def __init__ (self, bot):
        self.bot = bot
        self.logChannel = 728456783466725427 # 728456783466725427 73707667723806312
    
    @commands.group()
    async def session(self, ctx):	
        pass
        
    async def cog_command_error(self, ctx, error):
        msg = None

        if isinstance(error, commands.MissingAnyRole):
            await ctx.channel.send("You do not have the required permissions for this command.")
            bot.get_command(ctx.invoked_with).reset_cooldown(ctx)
            return
        else:
            if isinstance(error, commands.MissingRequiredArgument):
                msg = "Your command was missing an argument! "
            elif isinstance(error, commands.UnexpectedQuoteError) or isinstance(error, commands.ExpectedClosingQuoteError) or isinstance(error, commands.InvalidEndOfQuotedStringError):
              msg = ""

            if msg:
                ctx.command.reset_cooldown(ctx)
                await ctx.channel.send(msg)
                await traceBack(ctx,error)
            else:
                ctx.command.reset_cooldown(ctx)
                await traceBack(ctx,error)
        
    @commands.Cog.listener()
    async def on_raw_reaction_remove(self,payload):
    
        pass

        

    @commands.Cog.listener()
    async def on_raw_reaction_add(self,payload):
        pass
        
        
    @commands.command()
    async def generateLog(self,ctx, num):
        channel = self.bot.get_channel
        logData =db.logdata
        sessionInfo = logData.findOne({"_id": num})
        
        channel = self.bot.get_channel(self.logChannel) # 728456783466725427 737076677238063125
        
        editMessage = await channel.fetch_message(num)

        if not editMessage or editMessage.author != self.bot.user:
            print("Invalid Message")
            return None


        sessionLogEmbed = editMessage.embeds[0]
        summaryIndex = sessionLogEmbed.description.find('Summary:')
        description = sessionLogEmbed.description[:summaryIndex] + "Summary: " + editString+"\n"
        
        role = sessionInfo["Role"]
        game = sessionInfo["Name"]
        start = sessionInfo["Start"] 
        end = sessionInfo["End"] 
        
        guilds = sessionInfo["Guilds"]
        
        players = sessionInfo["Players"] 
        #dictionary indexed by user id
        # {cp, magic items, consumables, inventory, partial, status, user id, character id, character name, character level, character cp, double rewards, guild, }
        
        dm = sessionInfo["DM"] 
        # {cp, magic items, consumables, inventory, partial, status, user id, character id, character name, character level, character cp, double rewards, guild, noodles}
        
        maximumCP = dm["CP"]
        
        deathChars = []
        allRewardStrings = []
                    
        
        
        
        for k, player in players.items():
            # this indicates that the character had died
            if player["Status"] == "Dead":
                deathChars.append(player)
            
            duration = player["CP"] * 60
            
            guildDouble = False
            playerDouble = False
            dmDouble = False
            
            if role != "":
                guildDouble = guilds[player["Guild"]]["Status"] == True and guilds[player["Guild"]]["Rewards"] == True
                
                playerDouble = player["Double"]
                
                dmDouble = False
                
                
                treasureArray  = calculateTreasure(player["Level"], player["Character CP"], tierNum, duration, (player in deathChars), num, guildDouble, playerDouble, dmDouble)
                treasureString = f"{treasureArray[0]} CP, {treasureArray[1]} TP, {treasureArray[2]} GP"

                    
            else:
                # if there were no rewards we only care about the time
                treasureString = timeConversion(duration) 
            groupString = ""
            groupString += guildDouble * "Guild "
            groupString += playerDouble * "Fanatic "
                
            groupString += f'{role} Friend {"Full"*player["Full"]+"Partial"*(not player["Full"])} Rewards - {treasureString}'
            
            # if the player was not present the whole game and it was a no rewards game
            if role == "" and not player["Full"]:
                # check if the reward has already been added to the reward dictionary
                if treasureString not in allRewardStrings:
                    # if not, create the entry
                    allRewardStrings[treasureString] = [player]
                else:
                    # otherwise add the new players
                    allRewardStrings[treasureString] += [player] 
            else:
                # check if the full rewards have already been added, if yes create it and add the players
                if f'{role} Friend Full Rewards - {treasureString}' in allRewardStrings:
                    allRewardStrings[groupString] += [player]
                else:
                    allRewardStrings[groupString] += [player]

 
        datestart = datetime.fromtimestamp(start).strftime("%b-%d-%y %I:%M %p")
        dateend = datetime.fromtimestamp(end).strftime("%b-%d-%y %I:%M %p")
        totalDuration = timeConversion(end - start)
        sessionLogEmbed.title = f"Timer: {game} [END] - {totalDuration}"
        sessionLogEmbed.description = f"{start} to {end} CDT" 
        
        dmRewardsList = []
        #DM REWARD MATH STARTS HERE
        if("Character ID" in dm):
            charLevel = int(dm['Level'])
            # calculate the tier of the DM character
            if charLevel < 5:
                dmRole = 'Junior'
            elif charLevel < 11:
                dmRole = 'Journey'
            elif charLevel < 17:
                dmRole = 'Elite'
            elif charLevel < 21:
                dmRole = 'True'
            
            if role != "":
                guildDouble = guilds[player["Guild"]]["Status"] == True and guilds[player["Guild"]]["Rewards"] == True
                
                playerDouble = player["Double"]
                
                dmDouble = False
                
                
                treasureArray  = calculateTreasure(player["Level"], tierNum, duration, (player in deathChars), num, guildDouble, playerDouble, dmDouble)
                
            
            # add the items that the DM awarded themselves to the items list
            for d in dm["Magic Items"]+dm["Consumables"]["Add"]+dm["Inventory"]["Add"]:
                dmRewardsList.append(d)
        
        # get the collections of characters
        playersCollection = db.players
        
        noodles = dm["Noodles"]
        # Noodles Math
        
        # calculate the hour duration and calculate how many 3h segements were played
        hoursPlayed = maximumCP
        # that is the base line of sparkles and noodles gained
        noodlesGained = sparklesGained = int(hoursPlayed) // 3
        
        # add the noodles to the record or start a record if needed
        
        #update noodle role if dm
        noodleString = "Current Noodles: " + str(noodles)

        # if the game received rewards
        if role != "": 
            # clear the embed message to repopulate it
            sessionLogEmbed.clear_fields() 
            # for every unique set of TP rewards
            for key, value in allRewardStrings.items():
                temp = ""
                # for every player of this reward
                for v in value:
                    vRewardList = []
                    # for every brough consumable for the character
                    for r in  v["Magic Items"]+ v["Consumables"]["Add"]+ v["Inventory"]["Add"]:
                        # add the awarded items to the list of rewards
                        vRewardList.append(r)
                    # if the character was not dead at the end of the game
                    if v not in deathChars:
                        temp += f"{v['Mention']} | {v['Name']} {', '.join(vRewardList).strip()}\n"
                    else:
                        # if they were dead, include that death
                        temp += f"~~{v['Mention']} | {v['Name']}~~ **DEATH** {', '.join(vRewardList).strip()}\n"
                
                # since if there is a player for this reward, temp will have text since every case above results in changes to temp
                # this informs us that there were no players
                if temp == "":
                    temp = 'None'
                # add the information about the reward to the embed object
                sessionLogEmbed.add_field(name=f"**{key}**\n", value=temp, inline=False)
                # add temp to the total output string

            # list of all guilds
            guildsListStr = ""
            
            guildRewardsStr = ""
            
            # passed in parameter, check if there were guilds involved
            if guilds != list():
                guildsListStr = "Guilds: "
                # for every guild in the game
                for g in guilds:
                    # get the DB record of the guild
                    #filter player list by guild
                    gPlayers = [p for p in players if p["Guild"]==g["Name"]]
                    if(len(gPlayers)>0):
                        guildsRecordsList.append[[g, sparklesGained*len(gPlayers)]]
                        guildRewardsStr += f"{g['Name']}: +{sparklesGained} :sparkles:"

            sessionLogEmbed.title = f"\n**{game}**\n*Tier {tierNum} Quest* \n#{ctx.channel}"
            sessionLogEmbed.description = f"{guildsListStr}{', '.join([g['Mention'] for g in guilds])}\n{start} to {end} CDT ({totalDuration})\n"+description
            
            # add the field for the DM's player rewards
            dm_text = "**No Character**"
            dm_name_text = "**No Rewards**"
            # if no character signed up then the character parts are excluded
            if("Character ID" in dm):
                dm_text = f"{dm['Name']} {', '.join(dmRewardsList)}"
                dm_name_text = f"DM Rewards: (Tier {roleArray.index(dmRole) + 1}) - **{dmtreasureArray[0]} CP, {dmtreasureArray[1]} TP, and {dmtreasureArray[2]} GP**\n"
            sessionLogEmbed.add_field(value=f"**DM:** {dm['Mention']} | {dm_text}\n{':star:' * noodlesGained} {noodleString}", name=dm_name_text)
            
            # if there are guild rewards then add a field with relevant information
            if guildRewardsStr != "":
                sessionLogEmbed.add_field(value=guildRewardsStr, name=f"Guild Rewards", inline=False)
            
        
        pass
    


    @session.command()
    async def approve(self,ctx, num):
        channel = self.bot.get_channel
        logData = db.logdata
        sessionInfo = logData.find_one({"Log ID": num})
        
        channel = self.bot.get_channel(self.logChannel) # 728456783466725427 737076677238063125
        
        editMessage = await channel.fetch_message(num)

        if not editMessage or editMessage.author != self.bot.user:
            print("Invalid Session")
            return None


        
        guilds = sessionInfo["Guilds"]
        tierNum = sessionInfo["Tier"]
        role = sessionInfo["Role"]
        
        #dictionary indexed by user id
        players = sessionInfo["Players"] 
        # {cp, magic items, consumables, inventory, status, character id, character name, character level, character cp, double rewards, guild, }
                
                    
        dm = sessionInfo["DM"] 
        # {cp, magic items, consumables, inventory, character id, character name, character level, character cp, double rewards, guild, noodles, dm double}
        
        maximumCP = dm["CP"]
        deathChars = []
        playerUpdates = []
        
        # get the collections of characters
        playersCollection = db.players
        guildCollection = db.guilds
        statsCollection = db.stats
        usersCollection = db.users
        
        characterIDs = [p["Character ID"] for p in players.values()]
        
        
        # the db entry of every character
        characterDBentries = playersCollection.find({"_id": {"$in": characterIDs}})
        
        #print(characterDBentries)
        print(players)
        
        for character in characterDBentries:
            player = players[str(character["User ID"])]
            # this indicates that the character had died
            if player["Status"] == "Dead":
                deathChars.append(player)
            
            duration = player["CP"] * 3600
            

            if role != "":
                guildDouble = guilds[player["Guild"]]["Status"] == True and guilds[player["Guild"]]["Rewards"] == True
                
                playerDouble = player["Double"]
                
                dmDouble = False
                
                
                treasureArray  = calculateTreasure(player["Level"], player["CP"] , tierNum, duration, (player in deathChars), num, guildDouble, playerDouble, dmDouble)
                
                # idea: track gained and removed consumables and do the final adjustment here
                # doubly keep track of removal by shrinking the consumable list as well so things cannot be removed too many times
                # use the same format here for magic items
                
                # create a list of all items the character has
                consumableList = character["Consumables"].split(", ")
                consumablesString = ""
                
                
                #if we know they didnt have any items, we know that changes could only be additions
                if(character["Consumables"]=="None"):
                    # turn the list of added items into the new string
                    consumablesString = ", ".join(player["Consumables"]["Add"])
                else:
                    #remove the removed items from the list of original items and then combine the remaining and the new items                
                    for i in player["Consumables"]["Remove"]:
                        consumableList.remove(i)
                    consumablesString = ", ".join(player["Consumables"]["Add"]+consumableList)
                    
                # if the string is empty, turn it into none
                consumablesString += "None"*(consumablesString=="")
                
                # magic items cannot be removed so we only care about addtions
                # if we have no items and no additions, string is None
                
                magicItemString = "None"
                if(character["Magic Items"]=="None"):
                    if(len(player["Magic Items"])==0):
                        pass
                    else:
                        # otherwise it is just the combination of new items
                        magicItemString = ", ".join(player["Magic Items"])
                else:
                    # otherwise connect up the old and new items
                    consumablesString = character["Magic Items"]+", "+ ", ".join(player["Magic Items"])
                
                
                # increase the relevant inventory entries and create them if necessary
                for i in player["Inventory"]["Add"]:
                    if i in character["Inventory"]:
                        character["Inventory"][i] += 1
                    else:
                        character["Inventory"][i] = 1
                
                # decrement the relevant items and delete the entry when necessary
                for i in player["Inventory"]["Remove"]:
                    character["Inventory"][i] -= 1
                    if int(character["Inventory"][i]) <= 0:
                        del character["Inventory"][i]
                
                # set up all db values that need to be incremented
                increment = {"CP":  treasureArray[0], "GP":  treasureArray[2],"Games": 1}
                # for every TP tier value that was gained create the increment field
                for k,v in treasureArray[1].items():
                    increment[k] = v
                
                # TODO: update CP to be a single number
                charRewards = {'_id': player["Character ID"],  
                                    "fields": {"$unset": {f"GID{num}": 1} ,"$inc": increment, 
                                    "$set": {"Consumables": consumablesString, "Magic Items": magicItemString, "Inventory" : character["Inventory"]}}}
                
                playerUpdates.append(charRewards)
                
            else:
                # if there were no rewards we only care about the time
                pass
                
           
 
        
        dmRewardsList = []
        #DM REWARD MATH STARTS HERE
        if("Character ID" in dm):
        
            player = dm
            
            duration = player["CP"] * 3600
            # the db entry of every character
            print(dm)
            character = playersCollection.find_one({"_id": dm["Character ID"]})
            charLevel = int(dm['Level'])
            # calculate the tier of the DM character
            dmTierNum= 5
            dmRole = "Ascended"
            if charLevel < 5:
                dmRole = 'Junior'
                dmTierNum = 1
            elif charLevel < 11:
                dmRole = 'Journey'
                dmTierNum = 2
            elif charLevel < 17:
                dmRole = 'Elite'
                dmTierNum = 3
            elif charLevel < 20:
                dmRole = 'True'
                dmTierNum = 4
                
            guildDouble = guilds[player["Guild"]]["Status"] == True and guilds[player["Guild"]]["Rewards"] == True
                
            playerDouble = player["Double"]
            
            dmDouble = player["DM Double"]
            
            
            treasureArray  = calculateTreasure(charLevel, player["CP"] , dmTierNum, duration, (player in deathChars), num, guildDouble, playerDouble, dmDouble)
                
            # create a list of all items the character has
            consumableList = character["Consumables"].split(", ")
            consumablesString = ""
            
            
            #if we know they didnt have any items, we know that changes could only be additions
            if(character["Consumables"]=="None"):
                # turn the list of added items into the new string
                consumablesString = ", ".join(player["Consumables"]["Add"])
            else:
                #remove the removed items from the list of original items and then combine the remaining and the new items                
                for i in player["Consumables"]["Remove"]:
                    consumableList.remove(i)
                consumablesString = ", ".join(player["Consumables"]["Add"]+consumableList)
                
            # if the string is empty, turn it into none
            consumablesString += "None"*(consumablesString=="")
            
            # magic items cannot be removed so we only care about addtions
            # if we have no items and no additions, string is None
            magicItemString = "None"
            if(character["Magic Items"]=="None"):
                if(len(player["Magic Items"])==0):
                    pass
                else:
                    # otherwise it is just the combination of new items
                    magicItemString = ", ".join(player["Magic Items"])
            else:
                # otherwise connect up the old and new items
                magicItemString = character["Magic Items"]+", "+ ", ".join(player["Magic Items"])
            
            
            # increase the relevant inventory entries and create them if necessary
            for i in player["Inventory"]["Add"]:
                if i in character["Inventory"]:
                    character["Inventory"][i] += 1
                else:
                    character["Inventory"][i] = 1
            
            # decrement the relevant items and delete the entry when necessary
            for i in player["Inventory"]["Remove"]:
                character["Inventory"][i] -= 1
                if int(character["Inventory"][i]) <= 0:
                    del character["Inventory"][i]
            
            # set up all db values that need to be incremented
            increment = {"CP":  treasureArray[0], "GP":  treasureArray[2],"Games": 1}
            # for every TP tier value that was gained create the increment field
            for k,v in treasureArray[1].items():
                increment[k] = v
            
            # TODO: update CP to be a single number
            charRewards = {'_id': player["Character ID"],  "fields": {"$unset": {f"GID{num}": 1} ,
                            "$inc": increment, 
                             "$set": {"Consumables": consumablesString, "Magic Items": magicItemString, "Inventory" : character["Inventory"]}}}
            
            playerUpdates.append(charRewards)

        
        noodles = dm["Noodles"]
        # Noodles Math
        hoursPlayed = maximumCP
        # that is the base line of sparkles and noodles gained
        noodlesGained = sparklesGained = int(hoursPlayed) // 3
        
        timerData = list(map(lambda item: UpdateOne({'_id': item['_id']}, item['fields']), playerUpdates))
        
        players[dm["ID"]] = dm
        
        guildsData = []
        # if the game received rewards
        if role != "": 
            guildsRecordsList = []
            # passed in parameter, check if there were guilds involved
            if guilds != list():
                # for every guild in the game
                for name, g in guilds.items():
                    # get the DB record of the guild
                    #filter player list by guild
                    print(players.values())
                    gPlayers = [p for p in players.values() if p["Guild"]==name]
                    if(len(gPlayers)>0):
                        gain = sparklesGained*len(gPlayers) + int(dm["Guild"]==name)
                        guildsData.append(UpdateOne({"Name": name},
                                                   {"$inc": {"Games": 1, "Reputation": gain, "Total Reputation": gain}}))
                                                   
        try:
            end = sessionInfo["End"]
            start = sessionInfo["Start"]
            
            totalDuration = timeConversion(end - start)
            
            statsRecordLife  = statsCollection.find_one({'Life': 1})
            # get the stats for the month and create an entry if it doesnt exist yet
            statsIncrement ={"Games": 1}
            statsAddToSet = {}
            statsPush = {}
            for name in [g for g in guilds.keys() if guilds[g]["Status"]]:
                statsIncrement["Guild Games."+name] = 1
            # Total Number of Games for the Month / Life
            
            # increment or create the stat entry for the DM of the game
            statsIncrement[f"DM.{dm['ID']}.T{tierNum}"] = 1
            statsIncrement[f"T{tierNum}"] = 1
            
            # Track how many guild quests there were
            if guilds != {}:
                statsIncrement["GQ"] = 1
                # track how many games had a guild memeber with rewards and how many have not
                if len(guildsData)>0: 
                    statsIncrement["GQM"] = 1
                else:
                    statsIncrement["GQNM"] = 1
            # track a list of unique players
            statsAddToSet = { 'Unique Players': { "$each":  list([p for p in players.keys()])} }
            
            
            # track playtime and players
            statsPush = {"Playtime": totalDuration, 'Players': len(players)}


            
            datestart = datetime.fromtimestamp(start).strftime("%b-%d-%y %I:%M %p")
            dateyear = datestart.split('-')
            # update all the other data entries
            # update the DB stats
            statsCollection.update_one({'Date': dateyear}, {"$set": {'Date': dateyear}, "$inc": statsIncrement, "$addToSet": statsAddToSet, "$push": statsPush}, upsert=True)
            statsCollection.update_one({'Life': 1}, {"$inc": {"Games": 1}}, upsert=True)
            # update the DM' stats
            
            usersCollection.update_one({'User ID': str(dm["ID"])}, {"$set": {'User ID':str(dm["ID"])}, "$inc": {'Noodles': noodles, 'Double': -1*dm["Double"]}}, upsert=True)
            playersCollection.bulk_write(timerData)
            
            usersData = list([UpdateOne({'User ID': key}, {'$inc': {'Games': 1, 'Double': -1*item["Double"] }}, upsert=True) for key, item in players.items()])
            usersCollection.bulk_write(usersData)
                    
            if guildsRecordsList != list():
                # do a bulk write for the guild data
                guildsCollection.bulk_write(guildsData)
                
            #await  self.generateLog(ctx, num)
            
            #logData.delete_one({"Log ID": num})
            
        except BulkWriteError as bwe:
            print(bwe.details)
            charEmbedmsg = await ctx.channel.send(embed=None, content="Uh oh, looks like something went wrong. Please try the timer again.")
        #except Exception as e:
        #    print ('MONGO ERROR: ' + str(e))
        #    charEmbedmsg = await ctx.channel.send(embed=None, content="Uh oh, looks like something went wrong. Please try the timer again.")
        else:
            print('Success')
        pass
    @session.command()
    async def denyGuild(self, ctx, num):
        log = self.bot.get_channel(self.logChannel)
        
    @session.command()
    async def log(self, ctx, num, *, editString=""):
        # The real Bot
        botUser = self.bot.user
        # botUser = self.bot.get_user(650734548077772831)

        # Logs channel 
        # channel = self.bot.get_channel(577227687962214406) 
        channel = self.bot.get_channel(737076677238063125) # 728456783466725427 737076677238063125


        limit = 100
        msgFound = False
        async with channel.typing():
            async for message in channel.history(oldest_first=False, limit=limit):
                print("ID:", message.id)
                print("USer:",message.author)
                if int(num) == message.id and message.author == botUser:
                    editMessage = message
                    msgFound = True
                    break 

        if not msgFound:
            delMessage = await ctx.channel.send(content=f"I couldn't find your game with ID - `{num}` in the last {limit} games. Please try again, I will delete your message and this message in 10 seconds.")
            await asyncio.sleep(10) 
            await delMessage.delete()
            await ctx.message.delete() 
            return


        sessionLogEmbed = editMessage.embeds[0]




        if int(dmID) != ctx.author.id:
            delMessage = await ctx.channel.send(content=f"It doesn't look you were the DM of this game. You won't be able to edit this session log. I will delete your message and this one in 10 seconds.")
            await asyncio.sleep(10) 
            await delMessage.delete()
            await ctx.message.delete() 
            return


        if "✅" in sessionLogEmbed.footer.text:
            summaryIndex = sessionLogEmbed.description.find('Summary:')
            sessionLogEmbed.description = sessionLogEmbed.description[:summaryIndex] + "Summary: " + editString+"\n"
        else:
            sessionLogEmbed.description += "\nSummary: " + editString+"\n"

        await editMessage.edit(embed=sessionLogEmbed)
        delMessage = await ctx.channel.send(content=f"I've edited the summary for quest #{num}.\n```{editString}```\nPlease double-check that the edit is correct. I will now delete your message and this one in 30 seconds.")

        print("Success")
        sessionLogEmbed.set_footer(text=sessionLogEmbed.footer.text + "\n✅ Log complete! Players have been awarded their rewards. The DM may still edit the summary log if they wish.")
        await editMessage.edit(embed=sessionLogEmbed)
        await asyncio.sleep(30) 
        await delMessage.delete()
        await ctx.message.delete()

def setup(bot):
    bot.add_cog(Log(bot))
