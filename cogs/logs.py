import discord
import asyncio
import re
from discord.utils import get        
from discord.ext import commands
from datetime import datetime, timezone,timedelta
from bfunc import callAPI, db, traceBack, timeConversion, calculateTreasure, roleArray,timeConversion
from pymongo import UpdateOne
from pymongo.errors import BulkWriteError

logChannel = 73707667723806312 # 728456783466725427 73707667723806312

async def generateLog(self,  num : int, sessionInfo=None, guildDBEntriesDic=None, characterDBentries=None, userDBEntriesDic=None, ):
    logData =db.logdata
    if sessionInfo == None:
        sessionInfo = logData.find_one({"Log ID": int(num)})
    
    channel = self.bot.get_channel(logChannel) # 728456783466725427 737076677238063125
    editMessage = await channel.fetch_message(num)

    if not editMessage or editMessage.author != self.bot.user:
        print("Invalid Message")
        return None
        
    # get the collections of characters
    playersCollection = db.players
    guildCollection = db.guilds
    statsCollection = db.stats
    usersCollection = db.users

    sessionLogEmbed = editMessage.embeds[0]
    summaryIndex = sessionLogEmbed.description.find('Summary:')
    description = sessionLogEmbed.description[summaryIndex:]+"\n"
    
    role = sessionInfo["Role"]
    game = sessionInfo["Game"]
    start = sessionInfo["Start"] 
    end = sessionInfo["End"] 
    tierNum = sessionInfo["Tier"]
    
    guilds = sessionInfo["Guilds"]
    
    players = sessionInfo["Players"] 
    #dictionary indexed by user id
    # {cp, magic items, consumables, inventory, partial, status, user id, character id, character name, character level, character cp, double rewards, guild, }
    
    dm = sessionInfo["DM"] 
    # {cp, magic items, consumables, inventory, partial, status, user id, character id, character name, character level, character cp, double rewards, guild, noodles}
    
    maximumCP = dm["CP"]
    
    deathChars = []
    allRewardStrings = {}
                
    characterIDs = [p["Character ID"] for p in players.values()]
    userIDs = list(players.keys())
    guildIDs = list(guilds.keys())
    for gt in guildIDs:
        if guilds[gt]["Status"] == False:
            del guilds[gt]
            
    
    guildIDs = list(guilds.keys())
    
    userIDs.append(str(dm["ID"]))
    
    print(userIDs)
    # the db entry of every character
    if characterDBentries == None:
        characterDBentries = playersCollection.find({"_id": {"$in": characterIDs}})
    
    # the db entry of every user
    if userDBEntriesDic == None:
        userDBentries = usersCollection.find({"User ID": {"$in": userIDs}})
        userDBEntriesDic = {}
        for u in userDBentries:
            userDBEntriesDic[u["User ID"]] = u
        
        
    # the db entry of every guild
    if guildDBEntriesDic == None:
        guildDBEntriesDic = {}
        guildDBentries = guildCollection.find({"Name": {"$in": guildIDs}})
        for g in guildDBentries:
            guildDBEntriesDic[g["Name"]] = g
    
    
    
    
    print(userDBEntriesDic)
    
    for k, player in players.items():
        # this indicates that the character had died
        if player["Status"] == "Dead":
            deathChars.append(player)
        
        duration = player["CP"] * 3600
        
        guildDouble = False
        playerDouble = False
        dmDouble = False
        
        if role != "":
            guild_valid =("Guild" in player and 
                            player["Guild"] in guilds and 
                            guilds[player["Guild"]]["Status"])
            guildDouble = (guild_valid and 
                            guilds[player["Guild"]]["Rewards"] and 
                            guildDBEntriesDic[player["Guild"]]["Reputation"]>20)
            if((guild_valid and 
                guilds[player["Guild"]]["Items"] and 
                guildDBEntriesDic[player["Guild"]]["Reputation"]>15+20*guildDouble)):
                print("A", player["Double Items"])
                if player["Double Items"][0] == "Magic Items":
                    player["Magic Items"].append(player["Double Items"][1])
                else:
                    player[player["Double Items"][0]]["Add"].append(player["Double Items"][1])
                
            player["Double"] = "Double" in userDBEntriesDic[k] and userDBEntriesDic[k]["Double"] >0
            playerDouble = player["Double"]
                
            dmDouble = False
            
            
            treasureArray  = calculateTreasure(player["Level"], player["Character CP"], tierNum, duration, (player in deathChars), num, guildDouble, playerDouble, dmDouble)
            treasureString = f"{treasureArray[0]} CP, {sum(treasureArray[1].values())} TP, {treasureArray[2]} GP"

                
        else:
            # if there were no rewards we only care about the time
            treasureString = timeConversion(duration) 
        groupString = ""
        groupString += guildDouble * "Guild "
        groupString += playerDouble * "Fanatic "
            
        groupString += f'{role} Friend {"Full"*(player["CP"]==dm["CP"])+"Partial"*(not player["CP"]==dm["CP"])} Rewards:\n{treasureString}'
        
        # if the player was not present the whole game and it was a no rewards game
        if role == "" and not (player["CP"]==dm["CP"]):
            # check if the reward has already been added to the reward dictionary
            if treasureString not in allRewardStrings:
                # if not, create the entry
                allRewardStrings[treasureString] = [player]
            else:
                # otherwise add the new players
                allRewardStrings[treasureString] += [player] 
        else:
            print(groupString, "\n", allRewardStrings)
            # check if the full rewards have already been added, if yes create it and add the players
            if groupString in allRewardStrings:
                allRewardStrings[groupString] += [player]
            else:
                allRewardStrings[groupString] = [player]


    datestart = datetime.fromtimestamp(start).strftime("%b-%d-%y %I:%M %p")
    dateend = datetime.fromtimestamp(end).strftime("%b-%d-%y %I:%M %p")
    totalDuration = timeConversion(end - start)
    sessionLogEmbed.title = f"Timer: {game} [END] - {totalDuration}"
    sessionLogEmbed.description = f"Start: {datestart} CDT\nEnd: {dateend} CDT\n" 
    
    dm_double_string = ""
    dmRewardsList = []
    #DM REWARD MATH STARTS HERE
    if("Character ID" in dm):
        charLevel = int(dm['Level'])
        player = dm
        # calculate the tier of the DM character
        if charLevel < 5:
            dmRole = 'Junior'
        elif charLevel < 11:
            dmRole = 'Journey'
        elif charLevel < 17:
            dmRole = 'Elite'
        elif charLevel < 20:
            dmRole = 'True'
        else:
            dmRole = 'Ascended'
        duration = player["CP"]*3600
        print(duration)
        if role != "":
            guild_valid =("Guild" in player and 
                            player["Guild"] in guilds and 
                            guilds[player["Guild"]]["Status"])
            guildDouble = (guild_valid and 
                            guilds[player["Guild"]]["Rewards"] and 
                            guildDBEntriesDic[player["Guild"]]["Reputation"]>20)
            player["Double"] = "Double" in userDBEntriesDic[k] and userDBEntriesDic[k]["Double"] >0
            playerDouble = player["Double"]
            if((guild_valid and 
                guilds[player["Guild"]]["Items"] and 
                guildDBEntriesDic[player["Guild"]]["Reputation"]>15+20*guildDouble)):
                print("A", player["Double Items"][0])
                if player["Double Items"][0] == "Magic Items":
                    player["Magic Items"].append(player["Double Items"][1])
                else:
                    player[player["Double Items"][0]]["Add"].append(player["Double Items"][1])
            
            dmDouble = player["DM Double"]
            
            dm_double_string += guildDouble * "Guild "
            dm_double_string += playerDouble * "Fanatic "
            dm_double_string += dmDouble * "DDMRW "
            
            dmtreasureArray  = calculateTreasure(player["Level"], player["CP"], tierNum, duration, (player in deathChars), num, guildDouble, playerDouble, dmDouble)
            
        
        # add the items that the DM awarded themselves to the items list
        for d in dm["Magic Items"]+dm["Consumables"]["Add"]+dm["Inventory"]["Add"]:
            dmRewardsList.append("+"+d)
    
    # get the collections of characters
    playersCollection = db.players
    
    noodles = dm["Noodles"]
    # Noodles Math
    
    # calculate the hour duration and calculate how many 3h segements were played
    hoursPlayed = maximumCP
    # that is the base line of sparkles and noodles gained
    noodlesGained = sparklesGained = int(hoursPlayed) // 3
    print("Noodles:", noodlesGained)
    # add the noodles to the record or start a record if needed
    
    #update noodle role if dm
    noodleString = "Current :star:: " + str(noodles)

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
                    vRewardList.append("+"+r)
                # if the character was not dead at the end of the game
                if v not in deathChars:
                    temp += f"{v['Mention']} | {v['Character Name']} {', '.join(vRewardList).strip()}\n"
                else:
                    # if they were dead, include that death
                    temp += f"~~{v['Mention']} | {v['Character Name']}~~ **DEATH** {', '.join(vRewardList).strip()}\n"
            
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
        players[dm["ID"]] = dm
        # passed in parameter, check if there were guilds involved
        if guilds != dict():
            guildsListStr = "Guilds: "
            # for every guild in the game
            for name, g in guilds.items():
                
                guildsListStr += "\n"+g["Mention"]
                # get the DB record of the guild
                #filter player list by guild
                print(players.values())
                gPlayers = [p for p in players.values() if "Guild" in p and p["Guild"]==name]
                if(len(gPlayers)>0): 
                    gain = sparklesGained*len(gPlayers) + int("Guild" in dm and dm["Guild"]==name)
                    guildRewardsStr += f"{g['Name']}: +{gain} :sparkles:\n"

        sessionLogEmbed.title = f"\n**{game}**\n*Tier {tierNum} Quest* \n{sessionInfo['Channel']}"
        sessionLogEmbed.description = f"{guildsListStr}\nStart: {datestart} CDT\nEnd: {dateend} CDT\nRuntime: {totalDuration}\n"+description
        status_text = "Log is being processed! Characters are currently on hold."
        if sessionInfo["Status"] == "Approved":
            status_text = "✅ Log approved! Players have received their rewards."
        elif sessionInfo["Status"] == "Denied":
            status_text = "❌ Log Denied! Characters have been cleared"
        sessionLogEmbed.set_footer(text=f"Game ID: {num}\n{status_text}")
        
        # add the field for the DM's player rewards
        dm_text = "**No Character**"
        dm_name_text = "**No Rewards**"
        # if no character signed up then the character parts are excluded
        if("Character ID" in dm):
            dm_text = f"{dm['Character Name']} {', '.join(dmRewardsList)}"
            dm_name_text = f"DM {dm_double_string}Rewards (Tier {roleArray.index(dmRole) + 1}):\n**{dmtreasureArray[0]} CP, {sum(dmtreasureArray[1].values())} TP, {dmtreasureArray[2]} GP**\n"
        sessionLogEmbed.add_field(value=f"{dm['Mention']} | {dm_text}\n{'Gained :star:: ' + str(noodlesGained)} \n{noodleString}", name=dm_name_text)
        
        # if there are guild rewards then add a field with relevant information
        if guildRewardsStr != "":
            sessionLogEmbed.add_field(value=guildRewardsStr, name=f"Guild Rewards", inline=False)
        await editMessage.edit(embed=sessionLogEmbed)
    
    pass
        
class Log(commands.Cog):
    def __init__ (self, bot):
        self.bot = bot
        self.logChannel = 73707667723806312 # 728456783466725427 73707667723806312
    
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
        

    

    @commands.has_any_role('Mod Friend', 'Admins')
    @session.command()
    async def approve(self,ctx,  num : int):
        channel = self.bot.get_channel
        logData = db.logdata
        sessionInfo = logData.find_one({"Log ID": int(num)})
        channel = self.bot.get_channel(self.logChannel) # 728456783466725427 737076677238063125
        
        editMessage = await channel.fetch_message(num)

        if not editMessage or editMessage.author != self.bot.user:
            return ctx.channel.send("Session has no corresponding message in the log channel.")


        
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
        userIDs = list(players.keys())
        guildIDs = list(guilds.keys())
        
        userIDs.append(str(dm["ID"]))
        
        # the db entry of every character
        characterDBentries = playersCollection.find({"_id": {"$in": characterIDs}})
        
        # the db entry of every user
        userDBentries = usersCollection.find({"User ID": {"$in": userIDs}})
    
        # the db entry of every guild
        guildDBentries = guildCollection.find({"Name": {"$in": guildIDs}})
        print("GUILD", guildDBentries)
        guildDBEntriesDic = {}
        for g in guildDBentries:
            guildDBEntriesDic[g["Name"]] = g
        
        userDBEntriesDic = {}
        for u in userDBentries:
            userDBEntriesDic[u["User ID"]] = u

        #print(characterDBentries)
        print(players)
        
        for character in characterDBentries:
            player = players[str(character["User ID"])]
            # this indicates that the character had died
            if player["Status"] == "Dead":
                deathChars.append(player)
            
            duration = player["CP"] * 3600
            guildDouble = False
            playerDouble = False
            dmDouble = False

            if role != "":
                guild_valid =("Guild" in player and 
                                player["Guild"] in guilds and 
                                guilds[player["Guild"]]["Status"])
                guildDouble = (guild_valid and 
                                guilds[player["Guild"]]["Rewards"] and 
                                guildDBEntriesDic[player["Guild"]]["Reputation"]>20)
                

                player["Double"] = "Double" in userDBEntriesDic[str(character["User ID"])] and userDBEntriesDic[str(character["User ID"])]["Double"] >0
                playerDouble = player["Double"]
                dmDouble = False
                
                
                treasureArray  = calculateTreasure(player["Level"], player["Character CP"] , tierNum, duration, (player in deathChars), num, guildDouble, playerDouble, dmDouble)
                
                if((guild_valid and 
                        guilds[player["Guild"]]["Items"] and 
                        guildDBEntriesDic[player["Guild"]]["Reputation"]>15+20*guildDouble)):
                    if player["Double Items"][0] == "Inventory":
                        player["Inventory"].append(player["Double Items"][1])
                    else:
                        player[player["Double Items"][0]]["Add"].append(player["Double Items"][1])
                
                
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
                    magicItemString = character["Magic Items"]+(", "+ ", ".join(player["Magic Items"]))*(len(player["Magic Items"])>0)
                
                
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
                print("IIIIIIIIIIIIIIIIIIIIII", increment)
                charRewards = {'_id': player["Character ID"],  
                                    "fields": {"$unset": {f"GID": 1} ,"$inc": increment, 
                                    "$set": {"Consumables": consumablesString, "Magic Items": magicItemString, "Inventory" : character["Inventory"]}}}
                if(player["Status"] == "Dead"):
                    del charRewards["fields"]["$inc"]["Games"]
                    print("charRewards 1", charRewards)
                    deathDic = {"inc": increment.copy(), "set": charRewards["fields"]["$set"]}
                    charRewards["fields"]["$inc"] = {"Games": 1}
                    charRewards["fields"]["$set"] = {"Death": deathDic}
                    print("death", deathDic)
                    print("charRewards 2", charRewards)
                playerUpdates.append(charRewards)
                
            else:
                # if there were no rewards we only care about the time
                pass
                
        dmRewardsList = []
        dm["Double"] = False
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
            
            guild_valid =("Guild" in player and 
                                player["Guild"] in guilds and 
                                guilds[player["Guild"]]["Status"])
            guildDouble = (guild_valid and 
                            guilds[player["Guild"]]["Rewards"] and 
                            guildDBEntriesDic[player["Guild"]]["Reputation"]>20)
                
            
             
            player["Double"] = "Double" in userDBEntriesDic[dm["ID"]] and userDBEntriesDic[dm["ID"]]["Double"] >0
            playerDouble = player["Double"]
            
            dmDouble = player["DM Double"]
            
            
            treasureArray  = calculateTreasure(charLevel, player["Character CP"] , dmTierNum, duration, (player in deathChars), num, guildDouble, playerDouble, dmDouble)
                
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
                magicItemString = character["Magic Items"]+(", "+ ", ".join(player["Magic Items"]))*(len(player["Magic Items"])>0)
                
                
            
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
            
            charRewards = {'_id': player["Character ID"],  "fields": {"$unset": {f"GID": 1} ,
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
                for g in guildDBentries:
                    name = g["Name"]
                    # get the DB record of the guild
                    #filter player list by guild
                    gPlayers = [p for p in players.values() if "Guild" in p and p["Guild"] == name]
                    p_count = len(gPlayers) - int("Guild" in dm and dm["Guild"] == name)
                    guilds[g["Name"]]["Player Sparkles"] = sparklesGained*p_count
                    guilds[g["Name"]]["DM Sparkles"] = sparklesGained*int("Guild" in dm and dm["Guild"] == name)
                    if(len(gPlayers)>0):
                        reputationCost = (20*guilds[g["Name"]]["Rewards"]+15*guilds[g["Name"]]["Items"])*guilds[g["Name"]]["Status"]
                        gain = sparklesGained*len(gPlayers) + int("Guild" in dm and dm["Guild"] == name)
                        guildsData.append(UpdateOne({"Name": name},
                                                   {"$inc": {"Games": 1, "Reputation": gain- reputationCost, "Total Reputation": gain}}))
                                                   
        try:
            end = sessionInfo["End"]
            start = sessionInfo["Start"]
            
            totalDuration = end - start
            
            # get the stats for the month and create an entry if it doesnt exist yet
            statsIncrement ={"Games": 1, "Playtime": totalDuration, 'Players': len(players)}
            statsAddToSet = {}
            for name in [g["Name"] for g in guilds.values() if g["Status"]]:
                statsIncrement["Guilds."+name] = 1# Track how many guild quests there were
                statsIncrement["Guilds."+name+".GQ"] = 1
                statsIncrement["Guilds."+name+".Player Sparkles"] = guilds[g["Name"]]["Player Sparkles"]
                statsIncrement["Guilds."+name+".DM Sparkles"] = guilds[g["Name"]]["DM Sparkles"]
                # track how many games had a guild memeber with rewards and how many have not
                if guilds[g["Name"]]["Player Sparkles"] > 0: 
                    statsIncrement["Guilds."+name+".GQM"] = 1
                elif guilds[g["Name"]]["DM Sparkles"] > 0:
                    statsIncrement["Guilds."+name+".GQDM"] = 1
                else:
                    statsIncrement["Guilds."+name+".GQNM"] = 1
            # Total Number of Games for the Month / Life
            
            # increment or create the stat entry for the DM of the game
            statsIncrement[f"DM.{dm['ID']}.T{tierNum}"] = 1
            statsIncrement[f"T{tierNum}"] = 1
            
            
            # track a list of unique players
            statsAddToSet = { 'Unique Players': { "$each":  list([p for p in players.keys()])} }
            
            
            # track playtime and players


            
            dateyear = datetime.fromtimestamp(start).strftime("%b-%y")
            # update all the other data entries
            # update the DB stats
            statsCollection.update_one({'Date': dateyear}, {"$set": {'Date': dateyear}, "$inc": statsIncrement, "$addToSet": statsAddToSet}, upsert=True)
            statsCollection.update_one({'Life': 1}, {"$inc": statsIncrement, "$addToSet": statsAddToSet}, upsert=True)
            # update the DM' stats
            
            usersCollection.update_one({'User ID': str(dm["ID"])}, {"$set": {'User ID':str(dm["ID"])}, "$inc": {'Games': 1, 'Noodles': noodlesGained, 'Double': -1*dm["Double"]}}, upsert=True)
            playersCollection.bulk_write(timerData)
            
            usersData = list([UpdateOne({'User ID': key}, {'$inc': {'Games': 1, 'Double': -1*item["Double"] }}, upsert=True) for key, item in players.items()])
            usersCollection.bulk_write(usersData)
            
            logData.update_one({"_id": sessionInfo["_id"]}, {"$set" : {"Status": "Approved"}})
            sessionInfo["Status"]="Approved"
            
            if guildsRecordsList != list():
                # do a bulk write for the guild data
                guildsCollection.bulk_write(guildsData)
            del players[dm["ID"]]
            
            await  generateLog(ctx, num, sessionInfo=sessionInfo, userDBEntriesDic=userDBEntriesDic, guildDBEntriesDic=guildDBEntriesDic, characterDBentries=characterDBentries)
            
            del players[dm["ID"]]
            game = sessionInfo["Game"]
            for k,p in players.items():
                c = ctx.guild.get_member(int(k))
                if(c):
                    await c.send(f"The session log for **{game}** has been approved. **{p['Character Name']}** has received their rewards.")
            dm_text = ""
            if("Character ID" in dm):
                dm_text += f" **{dm['Character Name']}** has received their rewards."
            
            c = ctx.guild.get_member(int(dm["ID"]))
            if(c):
                await c.send(f"Your session log for **{game}** has been approved."+dm_text)
            #logData.delete_one({"Log ID": num})
            
        except BulkWriteError as bwe:
            print(bwe.details)
            charEmbedmsg = await ctx.channel.send(embed=None, content="Uh oh, looks like something went wrong. Please try the timer again.")
        #except Exception as e:
        #    print ('MONGO ERROR: ' + str(e))
        #    charEmbedmsg = await ctx.channel.send(embed=None, content="Uh oh, looks like something went wrong. Please try the timer again.")
        else:
            print('Success')
        guild = ctx.guild
        dmUser = ctx.guild.get_member(int(dm["ID"]))
        if dmUser:
            dmRoleNames = [r.name for r in dmUser.roles]
            # for each noodle roll cut-off check if the user would now qualify for the roll and if they do not have it and remove the old roll
            if noodles >= 150:
                if 'Immortal Noodle' not in dmRoleNames:
                    noodleRole = get(guild.roles, name = 'Immortal Noodle')
                    await dmUser.add_roles(noodleRole, reason=f"Hosted 150 sessions. This user has 150+ Noodles.")
                    if 'Ascended Noodle' in dmRoleNames:
                        await dmUser.remove_roles(get(guild.roles, name = 'Ascended Noodle'))
                    noodleString += "\n**Immortal Noodle** role received! :tada:"
            elif noodles >= 100:
                if 'Ascended Noodle' not in dmRoleNames:
                    noodleRole = get(guild.roles, name = 'Ascended Noodle')
                    await dmUser.add_roles(noodleRole, reason=f"Hosted 100 sessions. This user has 100+ Noodles.")
                    if 'True Noodle' in dmRoleNames:
                        await dmUser.remove_roles(get(guild.roles, name = 'True Noodle'))
                    noodleString += "\n**Ascended Noodle** role received! :tada:"

            elif noodles >= 60:
                if 'True Noodle' not in dmRoleNames:
                    noodleRole = get(guild.roles, name = 'True Noodle')
                    await dmUser.add_roles(noodleRole, reason=f"Hosted 60 sessions. This user has 60+ Noodles.")
                    if 'Elite Noodle' in dmRoleNames:
                        await dmUser.remove_roles(get(guild.roles, name = 'Elite Noodle'))
                    noodleString += "\n**True Noodle** role received! :tada:"
            
            elif noodles >= 30:
                if 'Elite Noodle' not in dmRoleNames:
                    noodleRole = get(guild.roles, name = 'Elite Noodle')
                    await dmUser.add_roles(noodleRole, reason=f"Hosted 30 sessions. This user has 30+ Noodles.")
                    if 'Good Noodle' in dmRoleNames:
                        await dmUser.remove_roles(get(guild.roles, name = 'Good Noodle'))
                    noodleString += "\n**Elite Noodle** role received! :tada:"

            elif noodles >= 10:
                if 'Good Noodle' not in dmRoleNames:
                    noodleRole = get(guild.roles, name = 'Good Noodle')
                    await dmUser.add_roles(noodleRole, reason=f"Hosted 10 sessions. This user has 10+ Noodles.")
                    noodleString += "\n**Good Noodle** role received! :tada:"
      
    @commands.has_any_role('Mod Friend', 'Admins')
    @session.command()
    async def deny(self,ctx,  num : int):
        channel = self.bot.get_channel
        logData = db.logdata
        sessionInfo = logData.find_one({"Log ID": int(num)})
        channel = self.bot.get_channel(self.logChannel) # 728456783466725427 737076677238063125
        
        editMessage = await channel.fetch_message(num)

        if not editMessage or editMessage.author != self.bot.user:
            return ctx.channel.send("Session has no corresponding message in the log channel.")

        sessionLogEmbed = editMessage.embeds[0]
        #dictionary indexed by user id
        players = sessionInfo["Players"] 
        # {cp, magic items, consumables, inventory, status, character id, character name, character level, character cp, double rewards, guild, }
                
                 
        playerUpdates = []   
        dm = sessionInfo["DM"] 
        # {cp, magic items, consumables, inventory, character id, character name, character level, character cp, double rewards, guild, noodles, dm double}
        if "Character ID" in dm:
            charRewards = {'_id': dm["Character ID"],  
                                "fields": {"$unset": {f"GID": 1} }}
            playerUpdates.append(charRewards)
        
        role = sessionInfo["Role"]
        
        # get the collections of characters
        playersCollection = db.players

        
        for player in players.values():
            if role != "":
                charRewards = {'_id': player["Character ID"],  
                                    "fields": {"$unset": {f"GID": 1} }}
                playerUpdates.append(charRewards)
                
            else:
                # if there were no rewards we only care about the time
                pass
                
        timerData = list(map(lambda item: UpdateOne({'_id': item['_id']}, item['fields']), playerUpdates))
        
                                               
        try:                
            playersCollection.bulk_write(timerData)
            logData.update_one({"_id": sessionInfo["_id"]}, {"$set" : {"Status": "Denied"}})
            
            game = sessionInfo["Game"]
            for k,p in players.items():
                c = ctx.guild.get_member(int(k))
                if(c):
                    await c.send(f"The session log for **{game}** has been denied. **{p['Character Name']}** has been cleared.")
            dm_text = ""
            if("Character ID" in dm):
                dm_text += f" **{dm['Character Name']}** has been cleared."
            
            c = ctx.guild.get_member(int(dm["ID"]))
            if(c):
                await c.send(f"Your session log for **{game}** has been denied."+dm_text)
            #logData.delete_one({"Log ID": num})
            sessionLogEmbed.set_footer(text=f"Game ID: {num}\n❌ Log Denied! Characters have been cleared.")
            await editMessage.edit(embed=sessionLogEmbed)
        except BulkWriteError as bwe:
            print(bwe.details)
            charEmbedmsg = await ctx.channel.send(embed=None, content="Uh oh, looks like something went wrong. Please try the timer again.")
        #except Exception as e:
        #    print ('MONGO ERROR: ' + str(e))
        #    charEmbedmsg = await ctx.channel.send(embed=None, content="Uh oh, looks like something went wrong. Please try the timer again.")
        else:
            print('Success')

    @session.command()
    async def denyGuild(self, ctx,  num : int, *, guilds):
        await self.guildPermission(ctx, num, "Status", False, 0)
    @session.command()
    async def permitGuild(self, ctx,  num : int, *, guilds):
        await self.guildPermission(ctx, num, "Status", True, 0)
        
    @session.command()
    async def denyRewards(self, ctx,  num : int, *, guilds):
        await self.guildPermission(ctx, num, "Rewards", False, 0)
    @session.command()
    async def permitRewards(self, ctx,  num : int, *, guilds):
        await self.guildPermission(ctx, num, "Rewards", True, 3)
        
    @session.command()
    async def denyItems(self, ctx,  num : int, *, guilds):
        await self.guildPermission(ctx, num, "Items", False, 0)
    @session.command()
    async def permitItems(self, ctx,  num : int, *, guilds):
        await self.guildPermission(ctx, num, "Items", True, 3)
        
    async def guildPermission(self, ctx, num : int, target, goal, min_members):
        logData = db.logdata
        sessionInfo = logData.find_one({"Log ID": int(num)})
        if( sessionInfo):
            if( (str(ctx.author.id) == sessionInfo["DM"]["ID"]) or "Mod Friend" in [r.name for r in ctx.author.roles]):
            # if the game received rewards
                if sessionInfo["Role"] != "": 
                    players = sessionInfo["Players"]
                    players[sessionInfo["DM"]["ID"]] = sessionInfo["DM"]
                    guilds = sessionInfo["Guilds"]
                    guild_dic = {}
                    for g in guilds.values():
                        guild_dic[g["Mention"]] = g
                    err_message = ""
                    for guildChannel in ctx.message.channel_mentions:
                        m = guildChannel.mention
                        # filter player list by guild
                        gPlayers = [p for p in players.values() if "Guild" in p and guilds[p["Guild"]]["Mention"] == m]
                        if(len(gPlayers) >= min_members):
                            print(guilds)
                            if guildChannel.mention in guild_dic:
                                try:
                                    db.logdata.update_one({"_id": sessionInfo["_id"]}, {"$set": {"Guilds."+guild_dic[m]["Name"]+"."+target: goal}})
                                except BulkWriteError as bwe:
                                    print(e)
                            else:
                                err_message += m +" not found in game.\n"
                        else:
                            err_message += "Not enough members to apply this change for "+ m +"\n"
                    if err_message != "":
                        await ctx.channel.send(err_message)
                    else:
                        await ctx.channel.send("Session updated.")
                        await generateLog(self, num)
            else:
                await ctx.channel.send("You do not have the permissions to perform this change to the session.")
        else:
            await ctx.channel.send("The session could not be found, please double check your number or if the session has already been approved.")
     
    @commands.has_any_role('Mod Friend', 'Admins')      
    @session.command()
    async def denyDDMRW(self, ctx,  num : int):
        await self.session_set(ctx, num, "DDMRW", False)
        
    @commands.has_any_role('Mod Friend', 'Admins')
    @session.command()
    async def permitDDMRW(self, ctx,  num : int):
        await self.session_set(ctx, num, "DDMRW", True)
        
    async def session_set(self, ctx, num : int, target, goal):
        logData = db.logdata
        sessionInfo = logData.find_one({"Log ID": int(num)})
        if( sessionInfo):
            try:
                db.logdata.update_one({"_id": sessionInfo["_id"]}, {"$set": {target: goal}})
            except BulkWriteError as bwe:
                print(e)
            await ctx.channel.send("Session updated.")
            await generateLog(self, num)
        else:
            await ctx.channel.send("The session could not be found, please double check your number or if the session has already been approved.")
                        
          
            
    @session.command()
    async def optout(self, ctx, num):
        await self.opt(ctx, num, False)
    @session.command()
    async def optin(self, ctx, num):
        await self.opt(ctx, num, True)
    
    # allows DMs to opt in or out of DDMRW
    async def opt(self, ctx, num : int, goal):
        logData =db.logdata
        sessionInfo = logData.find_one({"Log ID": int(num)})
        if( sessionInfo):
            if (str(ctx.author.id) == sessionInfo["DM"]["ID"] or "Mod Friend" in [r.name for r in ctx.author.roles] and sessionInfo["DDMRW"]):
            
                try:
                    db.logdata.update_one({"_id": sessionInfo["_id"]}, {"$set": {"DM.DM Double": goal}})
                    await generateLog(self, num)
                except BulkWriteError as bwe:
                    print(e)
            else:
                await ctx.channel.send("You were not the DM of that session or it was not DDMRW.")
        else:
            await ctx.channel.send("The session could not be found, please double check your number or if the session has already been approved.")
            
    @session.command()
    async def log(self, ctx,  num : int, *, editString=""):
        # The real Bot
        botUser = self.bot.user

        # Logs channel 
        # channel = self.bot.get_channel(577227687962214406) 
        channel = self.bot.get_channel(self.logChannel) # 728456783466725427 737076677238063125


        limit = 100
        msgFound = False
        async with channel.typing():
            async for message in channel.history(oldest_first=False, limit=limit):
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


        logData =db.logdata
        sessionInfo = logData.find_one({"Log ID": int(num)})
        if( sessionInfo):
            if (str(ctx.author.id) == sessionInfo["DM"]["ID"] or "Mod Friend" in [r.name for r in ctx.author.roles] and sessionInfo["DDMRW"]):
                pass
                 
            else:
                await ctx.channel.send("You were not the DM of that session.")
                return 
        else:
            await ctx.channel.send("The session could not be found, please double check your number or if the session has already been approved.")
            return
        sessionLogEmbed = editMessage.embeds[0]


        summaryIndex = sessionLogEmbed.description.find('Summary:')
        sessionLogEmbed.description = sessionLogEmbed.description[:summaryIndex] + "Summary: " + editString+"\n"


        await editMessage.edit(embed=sessionLogEmbed)
        delMessage = await ctx.channel.send(content=f"I've edited the summary for quest #{num}.\n```{editString}```\nPlease double-check that the edit is correct. I will now delete your message and this one in 30 seconds.")

        await editMessage.edit(embed=sessionLogEmbed)
        await asyncio.sleep(30) 
        await delMessage.delete()
        await ctx.message.delete()

def setup(bot):
    bot.add_cog(Log(bot))
