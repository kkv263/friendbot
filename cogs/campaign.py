import pytz
import time
import requests
import re
import shlex
import decimal
import random
import discord
import asyncio
from discord.utils import get        
from discord.ext import commands
from math import ceil, floor
from itertools import product      
from datetime import datetime, timezone,timedelta
from bfunc import numberEmojis, calculateTreasure, timeConversion, gameCategory, commandPrefix, checkForGuild, roleArray, timezoneVar, currentTimers, db, callAPI, traceBack, settingsRecord, alphaEmojis, questBuffsDict, questBuffsArray, noodleRoleArray, checkForChar, tier_reward_dictionary, cp_bound_array
from pymongo import UpdateOne
from pymongo.errors import BulkWriteError

class Campaign(commands.Cog):
    def __init__ (self, bot):
        self.bot = bot
       
    @commands.group(aliases=['c'])
    async def campaign(self, ctx):	
        pass

    async def cog_command_error(self, ctx, error):
        msg = None

        if isinstance(error, commands.CommandNotFound):
            await ctx.channel.send(f'Sorry, the command `{commandPrefix}campaign {ctx.invoked_with}` requires an additional keyword to the command or is invalid, please try again!')
            return
        if isinstance(error, commands.CommandOnCooldown):
            msg = f"You are already preparing a timer in this channel. Please cancel the current timer and try again." 
            await ctx.channel.send(msg)
        elif isinstance(error, commands.MissingAnyRole):
            await ctx.channel.send("You do not have the required permissions for this command.")
            bot.get_command(ctx.invoked_with).reset_cooldown(ctx)
            return
        else:
            if isinstance(error, commands.MissingRequiredArgument):
                print(error.param.name)
                if error.param.name == "roleName":
                    msg = "You're missing the @role for the campaign you want to create"
                elif error.param.name == "channelName":
                    msg = "You're missing the #channel for the campaign you want to create. "
                elif error.param.name == 'userList':
                    msg = "You can't prepare a timer without any players! \n"
                else:
                    msg = "Your command was missing an argument! "
            elif isinstance(error, commands.UnexpectedQuoteError) or isinstance(error, commands.ExpectedClosingQuoteError) or isinstance(error, commands.InvalidEndOfQuotedStringError):
              msg = "There seems to be an unexpected or a missing closing quote mark somewhere, please check your format and retry the command. "

            
            if msg:
                if ctx.command.name == "prep":
                    msg += f'Please follow this format:\n```yaml\n{commandPrefix}campaign timer prep "@player1, @player2, [...]"```'
                
                ctx.command.reset_cooldown(ctx)
                await ctx.channel.send(content=msg)
            else:
                ctx.command.reset_cooldown(ctx)
                await traceBack(ctx,error)
        if msg:
            if ctx.command.name == "create":
                msg += f"Please follow this format:\n`{commandPrefix}campaign create @rolename #channelname`.\n"


            ctx.command.reset_cooldown(ctx)
            await ctx.channel.send(msg)
        else:
            ctx.command.reset_cooldown(ctx)
            await traceBack(ctx,error)

    @commands.cooldown(1, 5, type=commands.BucketType.member)
    @campaign.command()
    async def create(self,ctx, roleName, channelName):
        channel = ctx.channel
        author = ctx.author
        campaignEmbed = discord.Embed()
        campaignEmbedmsg = None
        campaignCog = self.bot.get_cog('Campaign')

        campaignRole = ctx.message.role_mentions
        campaignChannel = ctx.message.channel_mentions
        campaignName = campaignRole[0].name

        roles = [r.name for r in ctx.author.roles]

        if 'Campaign Master' not in roles:
            await channel.send(f"You do not have the Campaign Master role to use this command.")
            return  

        if campaignRole == list() or campaignChannel == list():
            await channel.send(f"A camapign role and campaign channel must be supplied")
            return 

        campaignCollection = db.campaigns
        campaignRecords = campaignCollection.find_one({"Name": {"$regex": campaignName, '$options': 'i' }})

        if campaignRecords:
            await channel.send(f"Another campaign by this name has already been created.")
            return 

        usersCollection = db.users
        userRecords = usersCollection.find_one({"User ID": str(author.id)})

        if userRecords: 
            if 'Campaigns' not in userRecords:
                userRecords['Campaigns'] = {campaignRole[0].name : 0 }
            else:
                userRecords['Campaigns'][campaignRole[0].name] = 0


            campaignDict = {'Name': campaignName, 'Campaign Master ID': str(author.id), 'Role ID': str(campaignRole[0].id), 'Channel ID': str(campaignChannel[0].id)}
            await author.add_roles(campaignRole[0], reason=f"Added campaign {campaignName}")

            try:
                campaignCollection.insert_one(campaignDict)
                usersCollection.update_one({'_id': userRecords['_id']}, {"$set": {"Campaigns": userRecords['Campaigns']}}, upsert=True)
            except Exception as e:
                print ('MONGO ERROR: ' + str(e))
                campaignEmbedmsg = await channel.send(embed=None, content="Uh oh, looks like something went wrong. Please try creating your campaign again.")
            else:
                print('Success')
                campaignEmbed.title = f"Campaign Creation: {campaignName}"
                campaignEmbed.description = f"{author.name} has created **{campaignName}**!\nRole: {campaignRole[0].mention}\nChannel: {campaignChannel[0].mention}"
                if campaignEmbedmsg:
                    await campaignEmbedmsg.clear_reactions()
                    await campaignEmbedmsg.edit(embed=campaignEmbed)
                else: 
                    campaignEmbedmsg = await channel.send(embed=campaignEmbed)

        return

    @commands.cooldown(1, 5, type=commands.BucketType.member)
    @campaign.command()
    async def add(self,ctx, user, campaignName):
        channel = ctx.channel
        author = ctx.author
        campaignEmbed = discord.Embed()
        campaignEmbedmsg = None
        campaignCog = self.bot.get_cog('Campaign')
        guild = ctx.message.guild

        user = ctx.message.mentions

        roles = [r.name for r in ctx.author.roles]

        if 'Campaign Master' not in roles:
            await channel.send(f"You do not have the Campaign Master role to use this command.")
            return  

        if user == list() or len(user) > 1:
            await channel.send(f"I could not find the user you were trying to add to the campaign. Please try again.")
            return  

        campaignCollection = db.campaigns
        campaignRecords = campaignCollection.find_one({"Name": {"$regex": campaignName, '$options': 'i' }})

        if not campaignRecords:
            await channel.send(f"`{campaignName}` doesn\'t exist! Check to see if it is a valid campaign and check your spelling.")
            return

        if campaignRecords['Campaign Master ID'] != str(author.id):
            await channel.send(f"You cannot add users to this campaign because you are not the campaign master of {campaignRecords['Name']}")
            return

        usersCollection = db.users
        userRecords = usersCollection.find_one({"User ID": str(user[0].id)})  

        if 'Campaigns' not in userRecords:
            userRecords['Campaigns'] = {campaignRecords['Name'] : 0 }
        else:
            userRecords['Campaigns'][campaignRecords['Name']] = 0

        await user[0].add_roles(guild.get_role(int(campaignRecords['Role ID'])), reason=f"{author.name} add campaign member to {campaignRecords['Name']}")

        try:
            usersCollection.update_one({'_id': userRecords['_id']}, {"$set": {"Campaigns": userRecords['Campaigns']}}, upsert=True)
        except Exception as e:
            print ('MONGO ERROR: ' + str(e))
            campaignEmbedmsg = await channel.send(embed=None, content="Uh oh, looks like something went wrong. Please try adding to your campaign again.")
        else:
            print('Success')
            campaignEmbed.title = f"Campaign: {campaignRecords['Name']}"
            campaignEmbed.description = f"{author.name} has added {user[0].mention} to **{campaignRecords['Name']}**!"
            if campaignEmbedmsg:
                await campaignEmbedmsg.clear_reactions()
                await campaignEmbedmsg.edit(embed=campaignEmbed)
            else: 
                campaignEmbedmsg = await channel.send(embed=campaignEmbed)

        return

    @commands.cooldown(1, 5, type=commands.BucketType.member)
    @campaign.command()
    async def remove(self,ctx, user, campaignName):
        channel = ctx.channel
        author = ctx.author
        campaignEmbed = discord.Embed()
        campaignEmbedmsg = None
        campaignCog = self.bot.get_cog('Campaign')
        guild = ctx.message.guild

        user = ctx.message.mentions

        roles = [r.name for r in ctx.author.roles]

        if 'Campaign Master' not in roles:
            await channel.send(f"You do not have the Campaign Master role to use this command.")
            return  

        if user == list() or len(user) > 1:
            await channel.send(f"I could not find the user you were trying to remove from the campaign. Please try again.")
            return  

        campaignCollection = db.campaigns
        campaignRecords = campaignCollection.find_one({"Name": {"$regex": campaignName, '$options': 'i' }})

        if not campaignRecords:
            await channel.send(f"`{campaignName}` doesn\'t exist! Check to see if it is a valid campaign and check your spelling.")
            return

        if campaignRecords['Campaign Master ID'] != str(author.id):
            await channel.send(f"You cannot remove users from this campaign because you are not the campaign master of {campaignRecords['Name']}")
            return

        await user[0].remove_roles(guild.get_role(int(campaignRecords['Role ID'])), reason=f"{author.name} remove campaign member from {campaignRecords['Name']}")
        return
    @campaign.group(aliases=['t'])
    async def timer(self, ctx):	
        print(datetime.now(pytz.timezone(timezoneVar)).strftime("%b-%d-%y %I:%M %p"))
        pass

    @timer.command()
    async def help(self,ctx, page="1"):
        helpCommand = self.bot.get_command('help')
        if page == "2":
            await ctx.invoke(helpCommand, pageString='timer2')
        else:
            await ctx.invoke(helpCommand, pageString='timer')


    """
    This is the command meant to setup a timer and allowing people to sign up. Only one of these can be active at a time in a single channel
    The command gets passed in a list of players as a single entry userList
    the last argument passed in will be treated as the quest name
    """
    @commands.cooldown(1, float('inf'), type=commands.BucketType.channel) 
    @commands.has_any_role('D&D Friend', 'Campaign Friend')
    @timer.command()
    async def prep(self, ctx, userList):
        #this checks that only the author's response with one of the Tier emojis allows Tier selection
        #the response is limited to only the embed message
        
        #simplifying access to various variables
        channel = ctx.channel
        author = ctx.author
        #the name shown on the server
        user = author.display_name
        #the general discord name
        userName = author.name
        guild = ctx.guild
        #information on how to use the command, set up here for ease of reading and repeatability
        prepFormat =  f'Please follow this format:\n```yaml\n{commandPrefix}campaign timer prep "@player1, @player2, @player3..." "quest name"(*)```***** - The quest name is optional.'

        #prevent the command if not in a proper channel (game/campaign)
        if str(channel.category.id) != settingsRecord['Campaign Category ID']:
            #exception to the check above in case it is a testing channel
            if str(channel.id) in settingsRecord['Test Channel IDs'] or channel.id in [728456736956088420, 757685149461774477, 757685177907413092]:
                pass
            else: 
                #inform the user of the correct location to use the command and how to use it
                await channel.send('Try this command in a campaign channel! ' + prepFormat)
                #permit the use of the command again
                self.timer.get_command('prep').reset_cooldown(ctx)
                return
        #check if the userList was given in the proper way or if the norewards option was taken, this avoids issues with the game name when multiple players sign up
        if '"' not in ctx.message.content:
            #this informs the user of the correct format
            await channel.send(f"Make sure you put quotes **`\"`** around your list of players and retry the command!\n\n{prepFormat}")
            #permit the use of the command again
            self.timer.get_command('prep').reset_cooldown(ctx)
            return
        #check if the prep command included any channels, the response assumes that this was as a result of trying to add a guild
        if ctx.message.channel_mentions != list():
            #inform the user on the proper way of adding guilds to the game
            await channel.send(f"It looks like you are trying to add a channel/guild to your timer.\nPlease do this during `***{commandPrefix}campaign timer prep***` and not before.\n\n{prepFormat}")
            self.timer.get_command('prep').reset_cooldown(ctx)
            return
        #create an Embed object to use for user communication and information
        prepEmbed = discord.Embed()
        
        #check if the user mentioned themselves in the command, this is also meant to avoid having the user be listed twice in the roster below
        if author in ctx.message.mentions:
            #inform the user of the proper command syntax
            await channel.send(f"You cannot start a timer with yourself in the player list!\n\n{prepFormat}")
            self.timer.get_command('prep').reset_cooldown(ctx)
            return 

        # create a list of all expected players for the game so far, including the user who will always be the first 
        # element creating an invariant of the DM being the first element
        playerRoster = ctx.message.mentions

        


        #create the role variable for future use, default it to no role
        role = ""
        game = ctx.channel.name

        #clear the embed message
        prepEmbed.clear_fields()
        # if is not a campaign add the seleceted tier to the message title and inform the users about the possible commands (signup, add player, remove player, add guild, use guild reputation)

        # otherwise give an appropriate title and inform about the limited commands list (signup, add player, remove player)
        prepEmbed.title = f"{game} (Campaign)"
        prepEmbed.description = f"**DM Signup**: {commandPrefix}campaign timer signup \n**Player Signup**: {commandPrefix}campaign timer signup\n**Add to roster**: {commandPrefix}campaign timer add @player\n**Remove from roster**: {commandPrefix}campaign timer remove @player"
        
        
        #set up the special field for the DM character
        prepEmbed.add_field(name = f"{author.display_name} **(DM)**", value = author.mention)
        
        #setup a variable to store the string showing the current roster for the game
        rosterString = ""
        #now go through the list of the user/DM and the initially given player list and build a string
        for p in playerRoster:
            # create a field in embed for each player and their character, they could not have signed up so the text reflects that
            # the text differs only slightly if it is a campaign
            prepEmbed.add_field(name=p.display_name, value='Has not yet signed up for the campaign.', inline=False)
            
        #set up a field to inform the DM on how to start the timer or how to get help with it
        prepEmbed.set_footer(text= f"If enough players have signed up, use the following command to start the timer: `{commandPrefix}campaign timer start`\nUse the following command to see a list of timer commands: `{commandPrefix}campaign timer help`")

        # if it is a campaign or the previous message somehow failed then the prepEmbedMsg would not exist yet send we now send another message
        prepEmbedMsg = await channel.send(embed=prepEmbed)

        # create a list of all player and characters they have signed up with
        # this is a nested list where the contained entries are [member object, DB character entry, Consumable list for the game, character DB ID]
        # currently this starts with a dummy initial entry for the DM to enable later users of these entries in the code
        # this entry will be overwritten if the DM signs up with a game
        # the DM entry will always be the front entry, this property is maintained by the code
        
        dmRecord = list(usersCollection.find({"User ID": str(author.id)}))[0]
        
        signedPlayers = {"Players" : {},"DM" : {"Member" : author, "DB Entry": dmRecord}}
        #set up a variable for the current state of the timer
        timerStarted = False
        
        # create a list of all possible commands that could be used during the signup phase
        timerAlias = ["timer", "t"]
        timerCommands = ['signup', 'cancel', 'start', 'add', 'remove']
      
        timerCombined = []
        # pair up each command group alias with a command and store it in the list
        for x in product(timerAlias,timerCommands):
            timerCombined.append(f"{commandPrefix}campaign {x[0]} {x[1]}")
        
        """
        This is the heart of the command, this section runs continuously until the start command is used to change the looping variable
        during this process the bot will wait for any message that contains one of the commands listed in timerCombined above 
        and then invoke the appropriate method afterwards, the message check is also limited to only the channel signup was called in
        Relevant commands all have blocks to only run when called
        """
        while not timerStarted:
            # get any message that managed to satisfy the check described above, it has to be a command as a result
            msg = await self.bot.wait_for('message', check=lambda m: any(x in m.content for x in timerCombined) and m.channel == channel)
            """
            the following commands are all down to check which command it was
            the checks are all doubled up since the commands can start with $t and $timer
            the current issue is that it will respond to any message containing these strings, not just when they are at the start
            """
            
            """
            The signup command has different behaviors if the signup is from the DM, a player or campaign player
            
            """
            if msg.content.startswith(f"{commandPrefix}campaign timer signup") or msg.content.startswith(f"{commandPrefix}campaign t signup"):
                # if the message author is the one who started the timer, call signup with the special DM moniker
                # the character is extracted from the message in the signup command 
                # special behavior:
                playerChar = None
                if msg.author in playerRoster:
                    playerChar = await ctx.invoke(self.timer.get_command('signup'), char=None, author=msg.author, role=role) 
                    if playerChar:
                        signedPlayers["Players"][msg.author.id] = playerChar
                # if the message author has not been permitted to the game yet, inform them of such
                # a continue statement could be used to skip the following if statement
                else:
                    await channel.send(f"***{msg.author.display_name}***, you must be on the player roster in order to signup.")
                
                print(signedPlayers)

            # similar issues arise as mentioned above about wrongful calls
            elif (msg.content.startswith(f"{commandPrefix}campaign timer add ") or msg.content.startswith(f"{commandPrefix}campaign t add ")):
                if await self.permissionCheck(msg, author):
                    # this simply checks the message for the user that is being added, the Member object is returned
                    addUser = await ctx.invoke(self.timer.get_command('add'), msg=msg, prep=True)
                    #failure to add a user does not have an error message if no user is being added
                    if addUser is None:
                        pass
                    elif addUser not in playerRoster:
                        # set up the embed fields for the new user if they arent in the roster yet
                        prepEmbed.add_field(name=addUser.display_name, value='Has not yet signed up for the campaign.', inline=False)
                        # add them to the roster
                        playerRoster.append(addUser)
                    else:
                        #otherwise inform the user of the failed add
                        await channel.send(f'***{addUser.display_name}*** is already on the timer.')

            # same issues arise again
            
            elif (msg.content.startswith(f"{commandPrefix}campaign timer remove ") or msg.content.startswith(f"{commandPrefix}campaign t remove ")) :
                if await self.permissionCheck(msg, author):
                    # this simply checks the message for the user that is being added, the Member object is returned
                    removeUser = await ctx.invoke(self.timer.get_command('remove'), msg=msg, prep=True)
                    print (removeUser)
                    if removeUser is None:
                        pass
                    #check if the user is not the DM
                    elif removeUser != author:
                        # remove the embed field of the player
                        prepEmbed.remove_field(playerRoster.index(removeUser))
                        # remove the player from the roster
                        playerRoster.remove(removeUser)
                        # remove the player from the signed up players
                        if removeUser in signedPlayers["Players"]:
                                del signedPlayers["Players"][removeUser.id]
                    else:
                        await channel.send('You cannot remove yourself from the timer.')

            #the command that starts the timer, it does so by allowing the code to move past the loop
            elif (msg.content == f"{commandPrefix}campaign timer start" or msg.content == f"{commandPrefix}campaign t start"):
                if await self.permissionCheck(msg, author):
                    if len(signedPlayers["Players"].keys()) == 0:
                        await channel.send(f'There are no players signed up! Players, use the following command to sign up to the quest with your character before the DM starts the timer:\n```yaml\n{commandPrefix}campaign timer signup```') 
                    else:
                        timerStarted = True
            #the command that cancels the timer, it does so by ending the command all together                              
            elif (msg.content == f"{commandPrefix}campaign timer cancel" or msg.content == f"{commandPrefix}campaign t cancel"):
                if await self.permissionCheck(msg, author):
                    await channel.send(f'Timer cancelled! If you would like to prep a new quest, use the following command:\n```yaml\n{commandPrefix}campaign timer prep```') 
                    # allow the call of this command again
                    self.timer.get_command('prep').reset_cooldown(ctx)
                    return
            await prepEmbedMsg.delete()
            
            prepEmbedMsg = await channel.send(embed=prepEmbed)
        await ctx.invoke(self.timer.get_command('start'), userList = signedPlayers, game=game, role=role, guildsList = guildsList)


    """
    This is the command used to allow people to enter their characters into a game before the timer starts
    char is a message object which makes the default value of "" confusing as a mislabel of the object
    role is a string indicating which tier the game is for or if the player signing up is the DM
    resume is boolean quick check to see if the command was invoked by the resume command   
        this property is technically not needed since it could quickly be checked, 
        but it does open the door to creating certain behaviors even if not commaning from $resume
        the current state would only allow this from prep though, which never sets this property
        The other way around does not work, however since checking for it being true instead of checking for
        the invoke source (ctx.invoked_with == "resume") would allow manual calls to this command
    """
    @timer.command()
    async def signup(self,ctx, char="", author="", role="", resume=False):
        #check if the command was called using one of the permitted other commands
        if ctx.invoked_with == 'prep' or ctx.invoked_with == "resume":
            # set up a informative error message for the user
            signupFormat = f'Please follow this format:\n```yaml\n{commandPrefix}campaign timer signup```'
            # create an embed object
            # This is only true if this is during a campaign, in that case there are no characters or consumables
            if char is None: 
                usersCollection = db.users
                campaignCollection = db.campaigns
                campaignRecords = campaignCollection.find_one({"Channel ID": ctx.channel.id})

                # grab the DB records of the first user with the ID of the author
                userRecord = list(usersCollection.find({"User ID": str(author.id)}))[0]
                if("Campaigns" in userRecord and campaignRecords["Name"] in userRecord["Campaigns"].keys()):
                    # this indicates a selection of user info that seems to never be used
                    return {"Member" : author, "DB Entry": userRecord}
                else:
                    await ctx.channel.send(f"{author.mention} could not be found as part of the campaign.")
        return None

    
    """
    This command handles all the intial setup for a running timer
    this includes setting up the tracking variables of user playing times,
    """
    @timer.command()
    async def start(self, ctx, userList="", game="", role="", guildsList = ""):
        # access the list of all current timers, this list is reset on reloads and resets
        # this is used to enable the list command and as a management tool for seeing if the timers are working
        global currentTimers
        # start cannot be invoked by resume since it has its own structure
        if ctx.invoked_with == 'prep': 
            # make some common variables more accessible
            channel = ctx.channel
            author = ctx.author
            user = author.display_name
            userName = author.name
            guild = ctx.guild
            # this uses the invariant that the DM is always the first signed up
            dmChar = userList["DM"]

            #this check could also be done during prep, the current version allows for a channel to be prepped while another timer is running IF the current timer was created through resuming
            # that seems inintentional
            if self.timer.get_command('resume').is_on_cooldown(ctx):
                await channel.send(f"There is already a timer that has started in this channel! If you started this timer, use the following command to stop it:\n```yaml\n{commandPrefix}campaign timer stop```")
                self.timer.get_command('prep').reset_cooldown(ctx)
                return
            
            # get the current time for tracking the duration
            startTime = time.time()
            userList["Start"] = startTime
            # format the time for a localized version defined in bfunc
            datestart = datetime.now(pytz.timezone(timezoneVar)).strftime("%b-%d-%y %I:%M %p")
            
            for p_key, p_entry in userList["Players"].items():
                p_entry["State"] = "Full"
                p_entry["Latest Join"] = startTime
                p_entry["Duration"] = 0
            
            roleString = "(Campaign)"  
            # Inform the user of the started timer
            await channel.send(content=f"Starting the timer for **{game}** {roleString}.\n" )
            # add the timer to the list of runnign timers
            currentTimers.append('#'+game)
            
            # set up an embed object for displaying the current duration, help info and DM data
            stampEmbed = discord.Embed()
            stampEmbed.title = f'**{game}**: 0 Hours 0 Minutes\n'
            stampEmbed.set_footer(text=f'#{ctx.channel}\nType `{commandPrefix}campaign help timer2` for help with a running timer.')
            stampEmbed.set_author(name=f'DM: {userName}', icon_url=author.avatar_url)

            print('USERLIST')
            print(userList)
            

            for u in userList["Players"].values():
                print('USER')
                print(u)
                stampEmbed.add_field(name=f"**{u['Member'].display_name}**", value=u['Member'].mention, inline=False)
            

            stampEmbedmsg = await channel.send(embed=stampEmbed)

            # During Timer
            await self.duringTimer(ctx, datestart, startTime, userList, role, game, author, stampEmbed, stampEmbedmsg,dmChar)
            
            # allow the creation of a new timer
            self.timer.get_command('prep').reset_cooldown(ctx)
            # when the game concludes, remove the timer from the global tracker
            currentTimers.remove('#'+game)
            return

    
    """
    This command gets invoked by duringTimer and resume
    user -> Member object when passed in which makes the string label confusing
    start -> a dictionary of duration strings and player entry lists
    msg -> the message that caused the invocation, used to find the name of the character being added
    dmChar -> player entry of the DM of the game
    user -> the user being added, required since this command is invoked by add as well where the author is not the user necessarily
    resume -> used to indicate if this was invoked by the resume process where the messages are being retraced
    """
    @timer.command()
    async def addme(self,ctx, *, role="", msg=None, start="", user="", dmChar=None, resume=False, ):
        if ctx.invoked_with == 'prep' or ctx.invoked_with == 'resume':
            # user found is used to check if the user can be found in one of the current entries in start
            userFound = False
            # the key string where the user was found
            timeKey = ""
            # the user to add
            addUser = user
            channel = ctx.channel
                
            # make sure that only the the relevant user can respond
            def addMeEmbedCheck(r, u):
                sameMessage = False
                if addEmbedmsg.id == r.message.id:
                    sameMessage = True
                return sameMessage and ((str(r.emoji) == '✅') or (str(r.emoji) == '❌')) and (u == dmChar[0])
            
            
            # if this command was invoked by during the resume process we need to take the time of the message
            # otherwise we take the current time
            if not resume:
                startTime = time.time()
            else:
                startTime = msg.created_at.replace(tzinfo=timezone.utc).timestamp()
            
            userInfo = None
            # we go over every key value pair in the start dictionary
            # u is a string of format "{Tier} (Friend Partial or Full) Rewards: {duration}" and v is a list player entries [member, char DB entry, consumables, char id]
            for u, v in start["Players"].items():
                # loop over all entries in the player list and check if the addedUser is one of them
                if v["Member"] == addUser:
                    userFound = True
                    # the key of where the user was found
                    userInfo = v
                    break
            # if we didnt find the user we now need to the them to the system
            if not userFound:
                # first we invoke the signup command
                # no character is necessary if there are no rewards
                # this will return a player entry
                userInfo =  await ctx.invoke(self.timer.get_command('signup'), role=role, char=None, author=addUser, resume=resume) 
                # if a character was found we then can proceed to setup the timer tracking
                if userInfo:
                    # if this is not during the resume phase then we cannot afford to do user interactions
                    if not resume:
                        
                        # create an embed object for user communication
                        addEmbed = discord.Embed()
                        # get confirmation to add the player to the game
                        addEmbed.title = f"Add ***{addUser.display_name}*** to timer?"
                        addEmbed.description = f"***{addUser.mention}*** is requesting to be added to the timer.\n\n✅: Add to timer\n\n❌: Deny"
                        # send the message to communicate with the DM and get their response
                        # ping the DM to get their attention to the message
                        addEmbedmsg = await channel.send(embed=addEmbed, content=dmChar[0].mention)
                        await addEmbedmsg.add_reaction('✅')
                        await addEmbedmsg.add_reaction('❌')

                        try:
                            # wait for a response from the user
                            tReaction, tUser = await self.bot.wait_for("reaction_add", check=addMeEmbedCheck , timeout=60)
                        # cancel when the user doesnt respond within the timefram
                        except asyncio.TimeoutError:
                            await addEmbedmsg.delete()
                            await channel.send(f'Timer addme cancelled. Try again using the following command:\n```yaml\n{commandPrefix}campaign timer addme```')
                            # cancel this command and avoid things being added to the timer
                            return start
                        else:
                            await addEmbedmsg.clear_reactions()
                            # cancel if the DM wants to deny the user
                            if tReaction.emoji == '❌':
                                await addEmbedmsg.edit(embed=None, content=f"Request to be added to timer denied.")
                                await addEmbedmsg.clear_reactions()
                                # cancel this command and avoid things being added to the timer
                                return start
                            await addEmbedmsg.edit(embed=None, content=f"I've added ***{addUser.display_name}*** to the timer.")
                            userInfo["Latest Join"] = startTime
                            userInfo["State"] = "Partial"
                            userInfo["Duration"] = 0
                            start["Players"][addUser.id] = userInfo
                else:
                    await addEmbedmsg.edit(embed=None, content=f"***{addUser.display_name}*** could not be added to the timer.")
                    return start
            userInfo["Latest Join"] = startTime
            userInfo["State"] = "Partial"
            print(start)
            return start
    """
    This command is used to add players to the prep list or the running timer
    The code for adding players to the timer has been refactored into 'addme' and here just limits the addition to only one player
    prep does not pass in any value for 'start' but prep = True
    There is an important distinction between checking for invoked_with == 'prep' and prep = True
    the former would not be true if the resume command was used, but the prep property still allows to differentiate between the two stages
    This command returns two different values, if called during the prep stage then the member object of the player is returned, otherwise it is a dictionary as explained in duringTimer startTimes
    msg -> the message that caused the invocation of this command
    start-> this is a confusing variable, if this is called during prep it is returned as a member object and no value is passed in
        if called during resume than it is a timer dictionary as described in duringTimer startTimes
        this works because in that specific case start will be returned
    """
    @timer.command()
    async def add(self,ctx, *, msg, role="", start=None,prep=None, resume=False):
        if ctx.invoked_with == 'prep' or ctx.invoked_with == 'resume':
            guild = ctx.guild
            #if normal mentions were used then no users would have to be gotten later
            addList = msg.mentions
            addUser = None
            # limit adds to only one player at a time
            if len(addList) > 1:
                await ctx.channel.send(content=f"I cannot add more than one player! Please try the command with one player and check your format and spelling.")
                return None
            # if there was no player added
            elif addList == list():
                await ctx.channel.send(content=f"GHOST CHECK THIS IN THE ADD FUNCTION")
                return None
            else:
                # get the first ( and only ) mentioned user 
                return addList[0]
            print(start)
            return start
    
    async def addDuringTimer(self,ctx, *, msg, role="", start=None,resume=False, dmChar=None, ):
        if ctx.invoked_with == 'prep' or ctx.invoked_with == 'resume':
            guild = ctx.guild
            #if normal mentions were used then no users would have to be gotten later
            addList = msg.mentions
            addUser = None
            # limit adds to only one player at a time
            if len(addList) > 1:
                await ctx.channel.send(content=f"I cannot add more than one player! Please try the command with one player and check your format and spelling.")
                return None
            # if there was no player added
            elif addList == list():
                await ctx.channel.send(content=f"GHOST CHECK THIS IN THE ADDDURINGTIMER FUNCTION")
                return None
            else:
                # get the first ( and only ) mentioned user 
                addUser = addList[0]
                # in the duringTimer stage we need to add them to the timerDictionary instead
                # the dictionary gets manipulated directly which affects all versions
                #otherwise we need to add the user properly to the timer and perform the setup
                await ctx.invoke(self.timer.get_command('addme'), role=role, start=start, msg=msg, user=addUser, resume=resume, dmChar=dmChar) 
            return start

    @timer.command()
    async def removeme(self,ctx, msg=None, start="", role="",user="", resume=False):
        if ctx.invoked_with == 'prep' or ctx.invoked_with == 'resume':
            
            # user found is used to check if the user can be found in one of the current entries in start
            userFound = user.id in start["Players"]
            
            # if this command was invoked by during the resume process we need to take the time of the message
            # otherwise we take the current time
            if not resume:
                endTime = time.time()
            else:
                endTime = msg.created_at.replace(tzinfo=timezone.utc).timestamp()
            
            # if no entry could be found we inform the user and return the unchanged state
            if not userFound:
                if not resume:
                    await ctx.channel.send(content=f"***{user}***, I couldn't find you on the timer to remove you.") 
                return start
            # checks if the last entry was because of a death (%) or normal removal (-)
            user_dic = start["Players"][user.id]
            
            if user_dic["State"] == "Removed": 
                # since they have been removed last time, they cannot be removed again
                if not resume:
                    await ctx.channel.send(content=f"You have already been removed from the timer.")  
            
            # if the player has been there the whole time
            else:
                user_dic["State"] = "Removed"
                user_dic["Duration"] += endTime - user_dic["Latest Join"] 
                if not resume:
                    await ctx.channel.send(content=f"***{user}***, you have been removed from the timer.")

        return start

    
    """
    This command is used to remover players from the prep list or the running timer
    The code for removing players from the timer has been refactored into 'removeme' and here just limits the addition to only one player
    prep does not pass in any value for 'start' but prep = True
    msg -> the message that caused the invocation of this command
    role-> which tier the character is
    start-> this would be clearer as a None object since the final return element is a Member object
    """
    @timer.command()
    async def remove(self,ctx, msg, start=None,role="", prep=False, resume=False):
        if ctx.invoked_with == 'prep' or ctx.invoked_with == 'resume':
            guild = ctx.guild
            removeList = msg.mentions
            removeUser = ""

            if len(removeList) > 1:
                await ctx.channel.send(content=f"I cannot remove more than one player! Please try the command with one player and check your format and spelling.")
                return None
            elif removeList != list():
                return removeList[0]
            else:
                if not resume:
                    await ctx.channel.send(content=f"I cannot find any mention of the user you are trying to remove. Please check your format and spelling.")

            return start
            
    async def removeDuringTimer(self,ctx, msg, start=None,role="", resume=False):
        if ctx.invoked_with == 'prep' or ctx.invoked_with == 'resume':
            guild = ctx.guild
            removeList = msg.mentions
            removeUser = ""

            if len(removeList) > 1:
                await ctx.channel.send(content=f"I cannot remove more than one player! Please try the command with one player and check your format and spelling.")
                return None

            elif removeList != list():
                removeUser = removeList[0]
                await ctx.invoke(self.timer.get_command('removeme'), start=start, msg=msg, role=role, user=removeUser, resume=resume)
            else:
                if not resume:
                    await ctx.channel.send(content=f"I cannot find any mention of the user you are trying to remove. Please check your format and spelling.")
            return start

    """
    the command used to display the current state of the game timer to the users
    start -> a dictionary of strings and player list pairs, the strings are made out of the kind of reward and the duration and the value is a list of players entries (format can be found as the return value in signup)
    game -> the name of the running game
    role -> the Tier of the game
    stamp -> the start time of the game
    author -> the Member object of the DM of the game
    """
    @timer.command()
    async def stamp(self,ctx, stamp=0, role="", game="", author="", start="", dmChar={}, embed="", embedMsg=""):
        if ctx.invoked_with == 'prep' or ctx.invoked_with == 'resume':
            user = author.display_name
            # calculate the total duration of the game so far
            end = time.time()
            duration = end - stamp
            durationString = timeConversion(duration)
            # reset the fields in the embed object
            embed.clear_fields()

            print(start)
            # fore every entry in the timer dictionary we need to perform calculations
            for key, v in start["Players"].items():
                if v["State"] == "Full":
                    embed.add_field(name= f"**{v['Member'].display_name}**", value=f"{v['Member'].mention} {durationString}", inline=False)
                elif v["State"] == "Removed":
                    pass
                else:
                    embed.add_field(name= f"**{v['Member'].display_name}**", value=f"{v['Member'].mention} {timeConversion(v['Duration'] + end - v['Lastest Join'] )}", inline=False)
                
            
            # update the title of the embed message with the current time
            embed.title = f'**{game}**: {durationString}'
            msgAfter = False
            
            # we need separate advice strings if there are no rewards
            stampHelp = f'```md\n[Player][Commands]\n# Adding Yourself\n   {commandPrefix}campaign timer addme "character name"\n# Removing Yourself\n   {commandPrefix}campaign timer removeme\n\n[DM][Commands]\n# Adding Players\n   {commandPrefix}campaign timer add @player "character name"\n# Removing Players\n   {commandPrefix}campaign timer remove @player\n# Stopping the Timer\n   {commandPrefix}campaign timer stop```'
            # check if the current message is the last message in the chat
            # this checks the 1 message after the current message, which if there is none will return an empty list therefore msgAfter remains False
            async for message in ctx.channel.history(after=embedMsg, limit=1):
                msgAfter = True
            # if it is the last message then we just need to update
            if not msgAfter:
                await embedMsg.edit(embed=embed, content=stampHelp)
            else:
                # otherwise we delete the old message and resend the time stamp
                if embedMsg:
                    await embedMsg.delete()
                embedMsg = await ctx.channel.send(embed=embed, content=stampHelp)

            return embedMsg

    @timer.command(aliases=['end'])
    async def stop(self,ctx,*,start="", role="", game="", datestart="", dmChar="", guildsList=""):
        if ctx.invoked_with == 'prep' or ctx.invoked_with == 'resume':
            end = time.time() + 3600 * 3
            allRewardStrings = {}
            guild = ctx.guild
            startTime = start["Start"]
            total_duration = end - startTime
            
            stopEmbed = discord.Embed()
            
            stopEmbed.colour = discord.Colour(0xffffff)
        
            for p_key, p_val in start["Players"].items():
                reward_key = timeConversion(end - p_val["Latest Join"] + p_val["Duration"])
                if p_val["State"] == "Removed":
                    reward_key = timeConversion(p_val["Duration"])
                if reward_key in allRewardStrings:
                    allRewardStrings[reward_key].append(p_val)
                else:
                    allRewardStrings[reward_key] = [p_val]

            # Session Log Channel
            logChannel = ctx.channel
            stopEmbed.clear_fields()
            stopEmbed.set_footer(text=stopEmbed.Empty)

            playerData = []
            campaignCollection = db.campaigns
            # get the record of the campaign for the current channel
            campaignRecord = list(campaignCollection.find({"Channel ID": str(ctx.channel.id)}))[0]
            
            # since time is tracked specifically for campaigns we extract the duration by getting the 
            for key, value in allRewardStrings.items():
                temp = ""
                # extract the times from the treasure string of campaigns, this string is already split into hours and minutes
                numbers = [int(word) for word in key.split() if word.isdigit()]
                tempTime = (numbers[0] * 3600) + (numbers[1] * 60) 
                # for every player update their campaign entry with the addition time
                for v in value:
                    temp += f"{v['Member'].mention}\n"
                    v["inc"] = {"Campaigns."+campaignRecord["Name"] :tempTime}
                    playerData.append(v)
                    stopEmbed.add_field(name=key, value=temp, inline=False)

            try:   
                # update the DM's entry
                usersCollection.update_one({'User ID': str(dmChar["Member"].id)}, {"$set": {campaignRecord["Name"]+" inc" : {"Campaigns."+campaignRecord["Name"]: total_duration, 'Noodles': (total_duration/3600)//3}}}, upsert=True)
                # update the player entries in bulk
                usersData = list(map(lambda item: UpdateOne({'_id': item["DB Entry"]['_id']}, {'$set': {campaignRecord["Name"]+" inc" : item["inc"]}}, upsert=True), playerData))
                usersCollection.bulk_write(usersData)
                # don't update the DM's character if they did not sign up with one
                if(dmchar[1]!= "No Rewards"):
                    dmRecords = data['records'][0]
                    playersCollection.update_one({'_id': dmRecords['_id']},  dmRecords['fields'] , upsert=True)
            except BulkWriteError as bwe:
                print(bwe.details)
                charEmbedmsg = await ctx.channel.send(embed=None, content="Uh oh, looks like something went wrong. Please try the timer again.")
            except Exception as e:
                print ('MONGO ERROR: ' + str(e))
                charEmbedmsg = await ctx.channel.send(embed=None, content="Uh oh, looks like something went wrong. Please try the timer again.")
            else:
                print('Success')  

                session_msg = await ctx.channel.send(embed=stopEmbed)

                stopEmbed.set_footer(text=f"Game ID: {sessionMessage.id}")
                
                await session_msg.edit(embed=stopEmbed)

            # enable the starting timer commands
            self.timer.get_command('prep').reset_cooldown(ctx)
            self.timer.get_command('resume').reset_cooldown(ctx)

        return

    
    @timer.command()
    @commands.has_any_role('Mod Friend', 'A d m i n')
    async def resetcooldown(self,ctx):
        self.timer.get_command('prep').reset_cooldown(ctx)
        self.timer.get_command('resume').reset_cooldown(ctx)
        await ctx.channel.send(f"Timer has been reset in #{ctx.channel}")
    
    
    
    #extracted the checks to here to generalize the changes
    async def permissionCheck(self, msg, author):
        # check if the person who sent the message is either the DM, a Mod or a Admin
        if not (msg.author == author or "Mod Friend".lower() in [r.name.lower() for r in msg.author.roles] or "A d m i n s".lower() in [r.name.lower() for r in msg.author.roles]):
            await msg.channel.send(f'You cannot use this command!') 
            return False
        else: 
            return True
    
    """
    This functions runs continuously while the timer is going on and waits for commands to come in and then invokes them itself
    datestart -> the formatted date of when the game started
    startTime -> the specific time that the game started
    startTimes -> the dictionary of all the times that players joined and the player entries at that point (format of entries found in signup)
        the keys for startTimes are of the format "{Tier} (Friend Partial or Full) Rewards: {duration}"
        - in the key indicates a leave time
        % indicates a death
    role -> the tier of the game
    author -> person in control (normally the DM)
    stampEmbed -> the Embed object containing the information in regards to current timer state
    stampEmbedMsg -> the message containing stampEmbed
    dmChar -> the character of the DM 
    guildsList -> the list of guilds involved with the timer
    """
    async def duringTimer(self,ctx, datestart, startTime, startTimes, role, game, author, stampEmbed, stampEmbedmsg, dmChar):
        # if the timer is being restarted then we create a new message with the stamp command
        if ctx.invoked_with == "resume":
            stampEmbedmsg = await ctx.invoke(self.timer.get_command('stamp'), stamp=startTime, role=role, game=game, author=author, start=startTimes, embed=stampEmbed, embedMsg=stampEmbedmsg)
        
        # set up the variable for the continuous loop
        timerStopped = False
        channel = ctx.channel
        user = author.display_name

        timerAlias = ["timer", "t"]

        #in no rewards games characters cannot die or get rewards
        
        timerCommands = ['stop', 'end', 'add', 'remove']

      
        timerCombined = []
        #create a list of all command an alias combinations
        for x in product(timerAlias,timerCommands):
            timerCombined.append(f"{commandPrefix}campaign  campaign {x[0]} {x[1]}")
        
        #repeat this entire chunk until the stop command is given
        while not timerStopped:
            print("On Cooldown Before Command:", self.timer.get_command(ctx.invoked_with).is_on_cooldown(ctx))
            try:
                msg = await self.bot.wait_for('message', timeout=60.0, check=lambda m: (any(x in m.content for x in timerCombined)) and m.channel == channel)
                #transfer ownership of the timer
                # this is the command used to stop the timer
                # it invokes the stop command with the required information, explanations for the parameters can be found in the documentation
                # the 'end' alias could be removed for minimal efficiancy increases
                if (msg.content == f"{commandPrefix}campaign timer stop" or msg.content == f"{commandPrefix}campaign timer end" or msg.content == f"{commandPrefix}campaign t stop" or msg.content == f"{commandPrefix}campaign t end"):
                    # check if the author of the message has the right permissions for this command
                    if await self.permissionCheck(msg, author):
                        await ctx.invoke(self.timer.get_command('stop'), start=startTimes, role=role, game=game, datestart=datestart, dmChar=dmChar)
                        return

                # this behaves just like add above, but skips the ambiguity check of addme since only the author of the message could be added
                elif (msg.content.startswith(f"{commandPrefix}campaign timer addme ") or msg.content.startswith(f"{commandPrefix}campaign t addme ")) and '@player' not in msg.content and (msg.content != f'{commandPrefix}campaign timer addme' or msg.content != f'{commandPrefix}campaign t addme'):
                    # if the message author is the one who started the timer, call signup with the special DM moniker
                # the character is extracted from the message in the signup command 
                # special behavior:
                    startTimes = await ctx.invoke(self.timer.get_command('addme'), start=startTimes, role=role, msg=msg, user=msg.author, dmChar=dmChar)
                    stampEmbedmsg = await ctx.invoke(self.timer.get_command('stamp'), stamp=startTime, role=role, game=game, author=author, start=startTimes, dmChar=dmChar, embed=stampEmbed, embedMsg=stampEmbedmsg)
                # this invokes the add command, since we do not pass prep = True through, the special addme command will be invoked by add
                # @player is a protection from people copying the command
                elif (msg.content.startswith(f"{commandPrefix}campaign timer add ") or msg.content.startswith(f"{commandPrefix}campaign t add ")) and '@player' not in msg.content:
                    # check if the author of the message has the right permissions for this command
                    if await self.permissionCheck(msg, author):
                        # update the startTimes with the new added player
                        await self.addDuringTimer(ctx, start=startTimes, role=role, msg=msg, dmChar = dmChar)
                        # update the msg with the new stamp
                        stampEmbedmsg = await ctx.invoke(self.timer.get_command('stamp'), stamp=startTime, role=role, game=game, author=author, start=startTimes, dmChar=dmChar, embed=stampEmbed, embedMsg=stampEmbedmsg)
                # this invokes the remove command, since we do not pass prep = True through, the special removeme command will be invoked by remove
                elif msg.content == f"{commandPrefix}campaign timer removeme" or msg.content == f"{commandPrefix}campaign t removeme":
                    startTimes = await ctx.invoke(self.timer.get_command('removeme'), start=startTimes, role=role, user=msg.author)
                    stampEmbedmsg = await ctx.invoke(self.timer.get_command('stamp'), stamp=startTime, role=role, game=game, author=author, start=startTimes, dmChar=dmChar, embed=stampEmbed, embedMsg=stampEmbedmsg)
                elif (msg.content.startswith(f"{commandPrefix}campaign timer remove ") or msg.content.startswith(f"{commandPrefix}campaign t remove ")): 
                    if await self.permissionCheck(msg, author): 
                        startTimes = await ctx.invoke(self.timer.get_command('remove'), msg=msg, start=startTimes, role=role)
                        stampEmbedmsg = await ctx.invoke(self.timer.get_command('stamp'), stamp=startTime, role=role, game=game, author=author, start=startTimes, dmChar=dmChar, embed=stampEmbed, embedMsg=stampEmbedmsg)
                

            except asyncio.TimeoutError:
                stampEmbedmsg = await ctx.invoke(self.timer.get_command('stamp'), stamp=startTime, role=role, game=game, author=author, start=startTimes, dmChar=dmChar, embed=stampEmbed, embedMsg=stampEmbedmsg)
            else:
                pass
            print("On Cooldown After Command:", self.timer.get_command(ctx.invoked_with).is_on_cooldown(ctx))
          
    @campaign.command()
    async def log(self, ctx, num : int, *, editString=""):
        # The real Bot
        botUser = self.bot.user
        # botUser = self.bot.get_user(650734548077772831)

        # Logs channel 
        # channel = self.bot.get_channel(577227687962214406) 
        channel = ctx.channel # 728456783466725427 737076677238063125
        

        if str(channel.category.id) != settingsRecord['Campaign Category ID']:
            if str(channel.id) in settingsRecord['Test Channel IDs'] or channel.id in [728456736956088420, 757685149461774477, 757685177907413092]:
                pass
            else: 
                #inform the user of the correct location to use the command and how to use it
                await channel.send('Try this command in a campaign channel! ')
                return
                
        editMessage = await channel.fetch_message(num)

        if not editMessage:
            delMessage = await ctx.channel.send(content=f"I couldn't find your game with ID - `{num}`. Please try again, I will delete your message and this message in 10 seconds.")
            await asyncio.sleep(10) 
            await delMessage.delete()
            await ctx.message.delete() 
            return


        sessionLogEmbed = editMessage.embeds[0]

        charData = []

        for log in sessionLogEmbed.fields:
            for i in "\<>@#&!:":
                log.value = log.value.replace(i, "")
            
            logItems = log.value.split(' | ')

            if "DM" in logItems[0]:
                for i in "*DM":
                    logItems[0] = logItems[0].replace(i, "")
                dmID = logItems[0].strip()
                charData.append(dmID)
            
            # if no character was listed then there will be 2 entries
            # since there is no character to update we block the charData
            if len(logItems)>1:
                charData.append(logItems[0].strip)


        if "✅" in sessionLogEmbed.footer.text:
            summaryIndex = sessionLogEmbed.description.find('Summary:')
            sessionLogEmbed.description = sessionLogEmbed.description[:summaryIndex] + "Summary: " + editString+"\n"
        else:
            sessionLogEmbed.description += "\nSummary: " + editString+"\n"

        await editMessage.edit(embed=sessionLogEmbed)
        delMessage = await ctx.channel.send(content=f"I've edited the summary for quest #{num}.\n```{editString}```\nPlease double-check that the edit is correct. I will now delete your message and this one in 30 seconds.")

        if "✅" not in sessionLogEmbed.footer.text:

            

            usersCollection = db.users
            playersCollection = db.players
            uRecord = usersCollection.find_one({"User ID": dmID})
            charRecordsList = list(playersCollection.find({"User ID" : {"$in": charData }}))
            campaignCollection = db.campaigns
            # get the record of the campaign for the current channel
            campaignRecord = list(campaignCollection.find({"Channel ID": str(ctx.channel.id)}))[0]
            

            for charDict in charRecordsList:
                if f'{campaignRecord["Name"]} inc' in charDict:
                    charRewards = charDict[f'{campaignRecord["Name"]} inc']
                    data.append({'_id': charDict['_id'], "fields": {"$inc": charRewards, "$unset": {f'{campaignRecord["Name"]} inc': 1} }})

            playersData = list(map(lambda item: UpdateOne({'_id': item['_id']}, item['fields']), data))


            try:
                if len(data) > 0:
                    playersCollection.bulk_write(playersData)
            except Exception as e:
                print ('MONGO ERROR: ' + str(e))
                charEmbedmsg = await channel.send(embed=None, content="Uh oh, looks like something went wrong. Please try the command again.")
            else:
                print("Success")
                sessionLogEmbed.set_footer(text=sessionLogEmbed.footer.text + "\n✅ Log complete! Players have been awarded their rewards. The DM may still edit the summary log if they wish.")
                await editMessage.edit(embed=sessionLogEmbed)
                await asyncio.sleep(30) 
                await delMessage.delete()
                await ctx.message.delete()
    
def setup(bot):
    bot.add_cog(Campaign(bot))


