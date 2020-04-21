import discord
import pytz
import asyncio
import time
import requests
import re
import shlex
import decimal
import random
from math import ceil
from itertools import product
from discord.utils import get        
from datetime import datetime, timezone,timedelta
from discord.ext import commands
from bfunc import numberEmojis, calculateTreasure, timeConversion, gameCategory, commandPrefix, roleArray, timezoneVar, currentTimers, headers, db, callAPI, traceBack, settingsRecord
from pymongo import UpdateOne
from pymongo.errors import BulkWriteError


class Timer(commands.Cog):
    def __init__ (self, bot):
        self.bot = bot

    @commands.group(aliases=['t'])
    async def timer(self, ctx):	
        pass

    @timer.command()
    async def help(self,ctx, page="1"):
        helpCommand = self.bot.get_command('help')
        if page == "2":
            await ctx.invoke(helpCommand, pageString='timer2')
        else:
            await ctx.invoke(helpCommand, pageString='timer')

    async def cog_command_error(self, ctx, error):
        msg = None
            
        if isinstance(error, commands.MissingRequiredArgument):
            if error.param.name == 'userList':
                msg = "You're missing players to prep the timer."
        elif isinstance(error, commands.UnexpectedQuoteError) or isinstance(error, commands.ExpectedClosingQuoteError) or isinstance(error, commands.InvalidEndOfQuotedStringError):
           msg = ""

        if msg:
            if ctx.command.name == "prep":
                msg += f'Please follow this format:\n`{commandPrefix}timer prep "@player1 player2 @player3..." gamename*`.\n***** - These items are optional'

            ctx.command.reset_cooldown(ctx)
            await ctx.channel.send(msg)
        else:
            ctx.command.reset_cooldown(ctx)
            await traceBack(ctx,error)


    @commands.cooldown(1, float('inf'), type=commands.BucketType.user) 
    @timer.command()
    async def prep(self, ctx, userList, *, game="D&D Game"):
        def startEmbedcheck(r, u):
            return (r.emoji in numberEmojis[:5] or str(r.emoji) == '❌') and u == author
        channel = ctx.channel
        author = ctx.author
        user = author.display_name
        userName = author.name
        guild = ctx.guild
        prepFormat =  f'Please follow this format:\n`{commandPrefix}timer prep "@player1, @player2, @player3,..." gamename(*optional)`.'
        isCampaign = str(channel.category.id) == settingsRecord['Campaign Category ID']

        if str(channel.category.id) != settingsRecord['Game Category ID'] and str(channel.category.id) != settingsRecord['Campaign Category ID']:
            if str(channel.id) in settingsRecord['Test Channel IDs']:
                pass
            else: 
                await channel.send('Try this command in a game channel! ' + prepFormat)
                self.timer.get_command('prep').reset_cooldown(ctx)
                return

        if '"' not in ctx.message.content and userList != "norewards":
            await channel.send(f"```Please make sure you put quotes `\"` around your list of players and retry the command {prepFormat}```")
            self.timer.get_command('prep').reset_cooldown(ctx)
            return

        if ctx.message.channel_mentions != list():
            await channel.send(f"```It looks like you are trying to add a channel/guild to your timer. \nPlease do this during `{commandPrefix}timer prep` and not before. {prepFormat}```")
            self.timer.get_command('prep').reset_cooldown(ctx)
            return

        prepEmbed = discord.Embed()

        if author in ctx.message.mentions:
            await channel.send(f"```You cannot start a timer with yourself in the player list! {prepFormat} ```")
            self.timer.get_command('prep').reset_cooldown(ctx)
            return 

        playerRoster = [author] + ctx.message.mentions
        prepEmbed.add_field(name=f"React with [1-4] for your type of game: **{game}**\nPlease re-react with your choice if your prompt does not go through.", value=f"{numberEmojis[0]} New / Junior Friend [1-4]\n{numberEmojis[1]} Journeyfriend [5-10]\n{numberEmojis[2]} Elite Friend [11-16]\n{numberEmojis[3]} True Friend [17-20]", inline=False)
        prepEmbed.set_author(name=userName, icon_url=author.avatar_url)
        prepEmbed.set_footer(text= "React with ❌ to cancel")
        prepEmbedMsg = None

        try:
            if not isCampaign:
                prepEmbedMsg = await channel.send(embed=prepEmbed)
                for num in range(0,4): await prepEmbedMsg.add_reaction(numberEmojis[num])
                await prepEmbedMsg.add_reaction('❌')
                tReaction, tUser = await self.bot.wait_for("reaction_add", check=startEmbedcheck, timeout=60)
        except asyncio.TimeoutError:
            await prepEmbedMsg.delete()
            await channel.send('Timer timed out! Try starting the timer again.')
            self.timer.get_command('prep').reset_cooldown(ctx)
            return

        else:
            role = ""

            if not isCampaign:
                await asyncio.sleep(1) 
                await prepEmbedMsg.clear_reactions()

                if tReaction.emoji == '❌':
                    await prepEmbedMsg.edit(embed=None, content=f"Timer canceled. Type `{commandPrefix}timer prep` to prep another timer!")
                    self.timer.get_command('prep').reset_cooldown(ctx)
                    return

                role = roleArray[int(tReaction.emoji[0]) - 1]

            

        prepEmbed.clear_fields()
        if not isCampaign:
            prepEmbed.title = f"{game} (Tier {roleArray.index(role) + 1})"
            prepEmbed.description = f"**Signup:** {commandPrefix}timer signup \"charactername\" \"consumables\"\n**Add to roster:** {commandPrefix}timer add @player\n**Remove from roster:** {commandPrefix}timer remove @player\n**Set guild:** {commandPrefix}timer guild #guild1, #guild2..."

        else:
            prepEmbed.title = f"{game} (Campaign)"
            prepEmbed.description = f"**DM Signup:** {commandPrefix}timer signup \"charactername\"\n**Player Signup:** {commandPrefix}timer signup\n**Add to roster:** {commandPrefix}timer add @player\n**Remove from roster:** {commandPrefix}timer remove @player"

        rosterString = ""
        for p in playerRoster:
            if p == author:
                prepEmbed.add_field(name = f"{author.display_name} **(DM)**", value = "The DM has not yet signed up a character for DM rewards")
            else:
                if not isCampaign:
                    prepEmbed.add_field(name=p.display_name, value='Has not yet signed up a character to play.', inline=False)
                else:
                    prepEmbed.add_field(name=p.display_name, value='Has not yet signed up for the campaign.', inline=False)

        prepEmbed.set_footer(text= f"If enough players are signed up, use {commandPrefix}timer start to start the timer.\n`{commandPrefix}timer help` for a list of timer commands")


        if not prepEmbedMsg:
            prepEmbedMsg = await channel.send(embed=prepEmbed)
        else:
            await prepEmbedMsg.edit(embed=prepEmbed)

        guildsList = []
        signedPlayers = []

        timerStarted = False

        timerAlias = ["timer", "t"]
        timerCommands = ['signup', 'cancel', 'guild', 'start', 'add', 'remove']
      
        timerCombined = []

        for x in product(timerAlias,timerCommands):
            timerCombined.append(f"{commandPrefix}{x[0]} {x[1]}")

        while not timerStarted:
            msg = await self.bot.wait_for('message', check=lambda m: any(x in m.content for x in timerCombined) and m.channel == channel)
            if f"{commandPrefix}timer signup" in msg.content or f"{commandPrefix}t signup" in msg.content:
                if msg.author in playerRoster and msg.author == author:
                    playerChar = await ctx.invoke(self.timer.get_command('signup'), char=msg, author=msg.author, role='DM') 
                elif msg.author in playerRoster:
                    if not isCampaign:
                        playerChar = await ctx.invoke(self.timer.get_command('signup'), char=msg, author=msg.author, role=role) 
                    else:
                        playerChar = await ctx.invoke(self.timer.get_command('signup'), char=None, author=msg.author, role=role) 

                else:
                    await channel.send(f"```{msg.author.display_name}, you are not on the roster to play in this game.```")
                    
                if playerChar:
                    if playerRoster.index(playerChar[0]) == 0:
                        prepEmbed.set_field_at(playerRoster.index(playerChar[0]), name=f"{author.display_name} **(DM)**", value= f"{playerChar[1]['Name']} will recieve DM rewards", inline=False)
                        if playerChar[0] in [s[0] for s in signedPlayers]:
                            signedPlayers[0] = playerChar
                        else:
                            signedPlayers.insert(0,playerChar)
                    else:
                        if not isCampaign:
                            prepEmbed.set_field_at(playerRoster.index(playerChar[0]), name=f"{playerChar[1]['Name']}", value= f"{playerChar[0].mention}\nLevel {playerChar[1]['Level']}: {playerChar[1]['Race']} {playerChar[1]['Class']}\nConsumables: {', '.join(playerChar[2]).strip()}\n", inline=False)
                        else:
                            prepEmbed.set_field_at(playerRoster.index(playerChar[0]), name=playerChar[0].name, value= f"{playerChar[0].mention}", inline=False)
                        
                        foundSignedPlayer = False
                        for s in range(len(signedPlayers)):
                            if playerChar[0] == signedPlayers[s][0]:
                                signedPlayers[s] = playerChar
                                foundSignedPlayer = True
                                break
                        if not foundSignedPlayer:
                            signedPlayers.append(playerChar)
                        
                print(signedPlayers)


            elif (f"{commandPrefix}timer add " in msg.content or f"{commandPrefix}t add " in msg.content) and msg.author == author:
                addUser = await ctx.invoke(self.timer.get_command('add'), msg=msg, prep=True)
                if addUser not in playerRoster:
                    if not isCampaign:
                        prepEmbed.add_field(name=addUser.display_name, value='Has not yet signed up a character to play.', inline=False)
                    else:
                        prepEmbed.add_field(name=addUser.display_name, value='Has not yet signed up for the campaign.', inline=False)

                    playerRoster.append(addUser)
                else:
                    await channel.send(f'```{addUser.display_name} is already on the timer.```')


            elif (f"{commandPrefix}timer remove " in msg.content or f"{commandPrefix}t remove " in msg.content) and msg.author == author:
                removeUser = await ctx.invoke(self.timer.get_command('remove'), msg=msg, prep=True)

                if playerRoster.index(removeUser) != 0:
                    prepEmbed.remove_field(playerRoster.index(removeUser))
                    playerRoster.remove(removeUser)

                    for s in signedPlayers:
                        if removeUser in s:
                            signedPlayers.remove(s)
                else:
                    await channel.send('You cannot remove yourself from the timer.')

            elif msg.content == f"{commandPrefix}timer start" or msg.content == f"{commandPrefix}t start":
                if author not in [a[0] for a in signedPlayers]:
                    await channel.send(f'```The DM has not signed up yet! Please `{commandPrefix}timer signup` your character before starting the timer.```') 
                elif author in [a[0] for a in signedPlayers] and len(signedPlayers) == 1:
                    await channel.send(f'```There are no players signed up! Players, please `{commandPrefix}timer signup` your character before the DM starts the timer.```') 
                else:
                    timerStarted = True

            elif msg.content == f"{commandPrefix}timer cancel" or msg.content == f"{commandPrefix}t cancel":
                await channel.send(f'```Timer canceled! If you would like to prep a new game please use {commandPrefix}timer prep```') 
                self.timer.get_command('prep').reset_cooldown(ctx)
                return

            elif (f'{commandPrefix}timer guild' in msg.content or f'{commandPrefix}t guild' in msg.content) and msg.author == author:
                guildsList = []
                guildsListStr = ""
                guildCategoryID = 678381362398625802
                if (len(msg.channel_mentions) > 3):
                    await channel.send(f"```The number of guilds exceed 3. Please follow this format and try again:\n{commandPrefix}timer guild #guild1 #guild2 ...```") 
                elif msg.channel_mentions != list():
                    guildsList = msg.channel_mentions
                    invalidChannel = False
                    for g in guildsList:
                        if g.category_id != guildCategoryID:
                            invalidChannel = True
                            await channel.send(f"```'{g}' is not a guild channel. Please follow this format and try again:\n{commandPrefix}timer guild #guild1 #guild2 ...```") 
                            guildsList = []
                            break
                            
                    if not invalidChannel:
                        guildsListStr = "Guilds: " 
                        prepEmbed.description = f"{guildsListStr}{', '.join([g.mention for g in guildsList])}\n**Signup:** {commandPrefix}timer signup charactername \"consumables\"\n**Add to roster:** {commandPrefix}timer add @player\n**Remove from roster:** {commandPrefix}timer remove @player\n**Set guild:** {commandPrefix}timer guild #guild1, #guild2..."
                else:
                    await channel.send(f"```I couldn't find any mention of a guild. Please follow this format and try again:\n{commandPrefix}timer guild #guild1 #guild2 ...```") 


            await prepEmbedMsg.delete()
            prepEmbedMsg = await channel.send(embed=prepEmbed)

        await ctx.invoke(self.timer.get_command('start'), userList = signedPlayers, game=game, role=role, guildsList = guildsList)

    @timer.command()
    async def signup(self,ctx, char="", author="", role="", resume=False):
        if ctx.invoked_with == 'prep' or ctx.invoked_with == "resume":
            signupFormat = f'Please follow this format:\n`{commandPrefix}timer signup "charactername" "consumable list"'
            charEmbed = discord.Embed()
            charEmbedmsg = None
            channel = ctx.channel
            guild = ctx.guild
            consumablesList = ""

            if char is None:
                usersCollection = db.users
                userRecord = list(usersCollection.find({"User ID": str(author.id)}))[0]
                return [author, userRecord]

            if f'{commandPrefix}timer signup' == char.content.strip() or f'{commandPrefix}t signup' == char.content.strip():
                if ctx.invoked_with != "resume":
                    await channel.send(content=f'```You did not input a character, please try again. {signupFormat}```')
                return False

            if 'timer signup ' in char.content or 't signup ' in char.content:
                if f'{commandPrefix}timer signup ' in char.content:
                    charList = shlex.split(char.content.split(f'{commandPrefix}timer signup ')[1].strip())
                elif f'{commandPrefix}t signup ' in char.content:
                    charList = shlex.split(char.content.split(f'{commandPrefix}t signup ')[1].strip())
                charName = charList[0]

            else:
                if 'timer add ' in char.content or 't add ' in char.content:
                    if 'timer add ' in char.content:
                        charList = shlex.split(char.content.split(f'{commandPrefix}timer add ')[1].strip())
                    elif 't add' in char.content:
                        charList = shlex.split(char.content.split(f'{commandPrefix}t add ')[1].strip())
                    if len(charList) == 1:
                        if not resume:
                            await ctx.channel.send("```You're missing a character name for the player you're trying to add. Please try again```")
                        return
                    charName = charList[1]
                elif ('timer addme ' in char.content or 't addme ' in char.content) and (char.content != f'{commandPrefix}timer addme ' or char.content != f'{commandPrefix}t addme '):
                    if 'timer addme ' in char.content:
                        charList = shlex.split(char.content.split(f'{commandPrefix}timer addme ')[1].strip())
                    elif 't addme ' in char.content:
                        charList = shlex.split(char.content.split(f'{commandPrefix}t addme ')[1].strip())
                    charName = charList[0]
                        

                else:
                    if not resume:
                        await ctx.channel.send("```I wasn't able to add this character. Please check your format```")
                    return

            if charList[len(charList) - 1] != charName:
                consumablesList = charList[len(charList) - 1].split(', ')

            playersCollection = db.players
            cRecord  = list(playersCollection.find({"User ID": str(author.id), "Name": {"$regex": charName, '$options': 'i' }}))

            if cRecord == list():
                if not resume:
                    await channel.send(content=f'```I was not able to find the character `{charName}`. {signupFormat}```')
                return False

            def apiEmbedCheck(r, u):
                sameMessage = False
                if charEmbedmsg.id == r.message.id:
                    sameMessage = True
                return (r.emoji in numberEmojis[:min(len(cRecord), 9)]) or (str(r.emoji) == '❌') and u == author

            charString = ""
            numI = 0

            print(charList)

            for k in cRecord:
                print(k)
                charString += f"{numberEmojis[numI]} {k['Name']} \n"
                numI += 1

            if (len(cRecord) > 1):
                charEmbed.add_field(name=f"There seems to be multiple results for `{charName}`, please choose the correct one.\nIf the result you are looking for is not here, please cancel the command with ❌ and be more specific", value=charString, inline=False)
                if not charEmbedmsg:
                    charEmbedmsg = await channel.send(embed=charEmbed)
                else:
                    await charEmbedmsg.edit(embed=charEmbed)

                await charEmbedmsg.add_reaction('❌')

                try:
                    tReaction, tUser = await self.bot.wait_for("reaction_add", check=apiEmbedCheck, timeout=60)
                except asyncio.TimeoutError:
                    await charEmbedmsg.delete()
                    await channel.send('Timed out! Try using the command again.')
                    ctx.command.reset_cooldown(ctx)
                    return None, charEmbed, charEmbedmsg
                else:
                    if tReaction.emoji == '❌':
                        await charEmbedmsg.edit(embed=None, content=f"Command canceled. Try using the command again.")
                        await charEmbedmsg.clear_reactions()
                        ctx.command.reset_cooldown(ctx)
                        return None, charEmbed, charEmbedmsg
                charEmbed.clear_fields()
                await charEmbedmsg.clear_reactions()
                cRecord[0] = cRecord[int(tReaction.emoji[0]) - 1]

            elif len(cRecord) == 1:
                pass
            else:
                if not resume:
                    await channel.send(content=f'```I could not find the character "{charName},``` {signupFormat}')
                return False

            if charEmbedmsg:
                await charEmbedmsg.delete()

            if charName == "" or charName is None:
                if not resume:
                    await channel.send(content=f'```You did not input a character,``` {signupFormat}')
                return False

            cpSplit = cRecord[0]['CP'].split('/')
            if 'Death' in cRecord[0]:
                if not resume:
                    await channel.send(content=f'```You cannot signup with `{cRecord[0]["Name"]}`, a dying character, please use `{commandPrefix}char death`.```')
                return False 

            if next((s for s in cRecord[0].keys() if 'GID' in s), None):
                if not resume:
                    await channel.send(content=f'```You cannot signup with `{cRecord[0]["Name"]}`. This character has still not recieved thier rewards from their last game, please wait until the session log has been checked off.```')
                return False    

            validLevelStart = 1
            validLevelEnd = 1
            charLevel = cRecord[0]['Level']

            if role == "True":
                validLevelStart = 17
                validLevelEnd = 20
            elif role == "Elite":
                validLevelStart = 11
                validLevelEnd = 16
            elif role == "Journey":
                validLevelStart = 5
                validLevelEnd = 10
            elif role == "Junior":
                validLevelEnd = 4
            elif role == "DM":
                validLevelEnd = 20

            if charLevel < validLevelStart or charLevel > validLevelEnd:
                if not resume:
                    await channel.send(f"```{cRecord[0]['Name']} is not between levels {validLevelStart} - {validLevelEnd} to play in this game. Please choose a different character```")
                return False 


            if float(cpSplit[0]) >= float(cpSplit[1]):
                if not resume:
                    await channel.send(content=f'```You need to `{commandPrefix}levelup` your character {cRecord[0]["Name"]} before you can join the game!```')
                return False 


            if consumablesList:
                charConsumables = cRecord[0]['Consumables'].split(', ')
                gameConsumables = []
                checkedIndices = []
                notValidConsumables = ""
                consumableLength = 2
                if charLevel > 16:
                    consumableLength = 6
                elif charLevel > 12:
                    consumableLength = 5
                elif charLevel > 8:
                    consumableLength = 4
                elif charLevel > 4:
                    consumableLength = 3

                if len(consumablesList) > consumableLength or len(consumablesList) > len(charConsumables):
                    if not resume:
                        await channel.send(content=f'```You are trying to bring in too many consumables ({len(consumablesList)}/{consumableLength}). The limit for your character is {consumableLength}. ```')
                    return False

                for i in range(len(consumablesList)):
                    for j in range(len(charConsumables)):
                        if j in checkedIndices:
                            continue
                        elif consumablesList[i].lower().replace(" ", "").strip() == charConsumables[j].lower().replace(" ", ""):
                            checkedIndices.append(j)
                            gameConsumables.append(charConsumables[j])
                            break
                        else:
                            notValidConsumables += consumablesList[i] + '\n'
                            break 

                if notValidConsumables:
                    if not resume:
                        await channel.send(f"```These items were not found in your character's consumables:\n`{notValidConsumables}````")
                    return False
                
                if not gameConsumables:
                    gameConsumables = ['None']

                return [author,cRecord[0],gameConsumables, cRecord[0]['_id']]

            return [author,cRecord[0],['None'],cRecord[0]['_id']]

    @timer.command()
    async def deductConsumables(self, ctx, msg,start, resume=False): 
        if ctx.invoked_with == 'prep' or ctx.invoked_with == "resume":
            channel = ctx.channel
            searchQuery =  msg.content.split('-')[1].strip()
            searchItem = searchQuery.lower().replace(' ', '')
            startcopy = start.copy()
            timeKey = ""
            removedItem = ""
            for u, v in startcopy.items():
                for item in v:
                    if item[0] == msg.author:
                        timeKey = u
                        currentItem = item
                        foundItem = None
                        for j in range(len(currentItem[2])):
                            if searchItem == currentItem[2][j].lower().replace(" ", ""):
                                foundItem = currentItem[2][j]
                        if not foundItem:
                            if not resume:
                                await channel.send(f"I could not find the item `{searchQuery}` in your inventory to remove.")
                        elif foundItem:
                            charConsumableList = currentItem[1]['Consumables'].split(', ')
                            charConsumableList.remove(foundItem)
                            currentItem[2].remove(foundItem) 
                            currentItem[1]['Consumables'] = ', '.join(charConsumableList).strip()
                            start[timeKey].remove(item)
                            start[timeKey].append(currentItem)
                            if not resume:
                                await channel.send(f"The item `{foundItem}` has been removed from your inventory.")

            if timeKey == "":
                if not resume:
                    await channel.send(f"Looks like you were trying to remove `{searchItem}` from your inventory. I could not find you on the timer to do that.")
            return start
    
    @timer.command()
    async def start(self, ctx, userList="", game="", role="", guildsList = ""):
        global currentTimers
        timerCog = self.bot.get_cog('Timer')
        if ctx.invoked_with == 'prep':
            channel = ctx.channel
            author = ctx.author
            user = author.display_name
            userName = author.name
            guild = ctx.guild
            dmChar = userList.pop(0)
            # DM Rewards
            dmChar.append(['Junior Noodle',0,0,0,0])


            for r in dmChar[0].roles:
                if 'Noodle' in r.name:
                    dmChar[4] = [r.name,0,0,0,0]
                    break

            if self.timer.get_command('resume').is_on_cooldown(ctx):
                await channel.send(f"There is already a timer that has started in this channel! If you started the timer, type `{commandPrefix}timer stop` to stop the current timer")
                self.timer.get_command('prep').reset_cooldown(ctx)
                return

            startTime = time.time()
            datestart = datetime.now(pytz.timezone(timezoneVar)).strftime("%b-%-d-%y %I:%M %p")
            start = []
            if role != "":
                for u in userList:
                    start.append(u)
                startTimes = {f"{role} Friend Full Rewards:{startTime}":start} 

                roleString = ""
                if role != "":
                    roleString = f"({role} Friend)"
                await channel.send(content=f"Timer: Starting the timer for - **{game}** {roleString}." )

            else:
                for u in userList:
                    start.append(u)
                startTimes = {f"No Rewards:{startTime}":start}
                roleString = "(Campaign)"
                await ctx.channel.send(content=f"Timer: Starting the timer for - **{game}** {roleString}.\n" )

            currentTimers.append('#'+channel.name)

            stampEmbed = discord.Embed()
            stampEmbed.title = f'**{game}**: 0 Hours 0 Minutes\n'
            stampEmbed.set_footer(text=f'#{ctx.channel}\n{commandPrefix}timer help 2 for help with the timer.')
            stampEmbed.set_author(name=f'DM: {userName}', icon_url=author.avatar_url)

            print('USERLIST')
            print(userList)

            if role != "":
                playerList = []
                for u in userList:
                    print('USER')
                    print(u)
                    consumablesString = ""
                    if u[2] != ['None']:
                        consumablesString = "\nConsumables: " + ', '.join(u[2])
                    stampEmbed.add_field(name=f"**{u[0].display_name}**", value=f"**{u[1]['Name']}**{consumablesString}\n", inline=False)
            else:
                playerList = []
                for u in userList:
                    print('USER')
                    print(u)
                    stampEmbed.add_field(name=f"**{u[0].display_name}**", value=u[0].mention, inline=False)
            

            stampEmbedmsg = await channel.send(embed=stampEmbed)

            # During Timer
            await timerCog.duringTimer(ctx, datestart, startTime, startTimes, role, game, author, stampEmbed, stampEmbedmsg,dmChar,guildsList)

            self.timer.get_command('prep').reset_cooldown(ctx)
            currentTimers.remove('#'+channel.name)
            return

    @timer.command()
    async def transfer(self,ctx,user=""):
        if ctx.invoked_with == 'start' or ctx.invoked_with == 'resume':
            guild = ctx.guild
            newUser = guild.get_member_named(user.split('#')[0])
            return newUser 

    @timer.command()
    async def reward(self,ctx,msg,start="",resume=False, dmChar=""):
        if ctx.invoked_with == 'prep' or ctx.invoked_with == 'resume':
            guild = ctx.guild
            rewardList = msg.raw_mentions
            rewardUser = ""

            if rewardList == list():
                if not resume:
                    await ctx.channel.send(content=f"```I could not find any mention of a user to hand out a reward```") 
                return start,dmChar
            else:
                rewardUser = guild.get_member(rewardList[0])
                startcopy = start.copy()
                userFound = False;
                timeKey = ""
                userCount = 0

                if rewardUser == dmChar[0]:
                    userFound = True
                    currentItem = dmChar
                    charConsumableList = currentItem[1]['Consumables'].split(', ')
                    charMagicList = currentItem[1]['Magic Items'].split(', ')
                    charLevel = int(currentItem[1]['Level'])

                for u, v in startcopy.items():
                    if 'Full Rewards' in u:
                        totalDurationTime = (time.time() - float(u.split(':')[1])) // 60
                        if totalDurationTime < 180:
                            if not resume:
                              await ctx.channel.send(content=f"```You may not reward any items if a game's duration is under 3 hours.```") 
                            return start, dmChar
                    for item in v:
                        if item[0] == rewardUser:
                            userCount += 1
                            userFound = True
                            timeKey = u
                            currentItem = oldItem = item
                            charConsumableList = currentItem[1]['Consumables'].split(', ')
                            charMagicList = currentItem[1]['Magic Items'].split(', ')
                            charLevel = int(currentItem[1]['Level'])

                if userFound:
                    if '"' in msg.content:
                        consumablesList = msg.content.split('"')[1::2][0].split(', ')

                    else:
                        if not resume:
                            await ctx.channel.send(content=f'```You need to include quotes around your reward item in your command. Please follow this format: \n{commandPrefix}timer reward @player "reward"```')
                        return start, dmChar

                    for query in consumablesList:
                        # TODO: Deal with this in resume, should not show embed
                        rewardConsumable, charEmbed, charEmbedmsg = await callAPI(ctx, discord.Embed(), None ,'rit',query) 

                        if not rewardConsumable:
                            if not resume:
                                await ctx.channel.send('This does not seem to be a valid reward.')
                            return start, dmChar
                        else:
                            major = dmChar[4][1]
                            minor = dmChar[4][2]
                            dmMajor = dmChar[4][3]
                            dmMinor = dmChar[4][4]

                            dmMnc = False
                            lowerTier = False
                            chooseOr = False

                            totalDurationTimeMultiplier = totalDurationTime // 180

                            if dmChar[4][0] == 'Spicy Noodle':
                                rewardMajorLimit = 3
                                rewardMinorLimit = 7
                                dmMajorLimit = 1 * totalDurationTimeMultiplier 
                                dmMinorLimit = 2 * totalDurationTimeMultiplier 
                            elif dmChar[4][0] == 'Ramen Noodle':
                                rewardMajorLimit = 3
                                rewardMinorLimit =  6
                                dmMajorLimit = 1 * totalDurationTimeMultiplier
                                dmMinorLimit = 1 * totalDurationTimeMultiplier
                            elif dmChar[4][0] == 'True Noodle':
                                rewardMajorLimit = 2
                                rewardMinorLimit = 5
                                dmMajorLimit = 1 * totalDurationTimeMultiplier
                                dmMinorLimit = 1 * totalDurationTimeMultiplier
                            elif dmChar[4][0] == 'Elite Noodle':
                                rewardMajorLimit = 2
                                rewardMinorLimit = 4
                                dmMajorLimit = 1 * totalDurationTimeMultiplier
                                dmMinorLimit = 1 * totalDurationTimeMultiplier
                                lowerTier = True
                                chooseOr = True
                            elif dmChar [4][0] == 'Good Noodle':
                                rewardMajorLimit = 1
                                rewardMinorLimt = 3
                                dmMajorLimit = 0 * totalDurationTimeMultiplier
                                dmMinorLimit = 1 * totalDurationTimeMultiplier
                                lowerTier = True
                            else:
                                dmMnc = True

                            if charLevel < 5:
                                tierNum = 1
                            elif charLevel < 11:
                                tierNum = 2
                            elif charLevel < 17:
                                tierNum = 3
                            elif charLevel < 21:
                                tierNum = 4

                            if lowerTier and rewardUser == dmChar[0]:
                                if tierNum < 2:
                                    tierNum = 1
                                else:
                                    tierNum -= 1

                            print('tierNum')
                            print(tierNum)

                            if '+' + rewardConsumable['Name'] in currentItem[2]:
                                if not resume:
                                    await ctx.channel.send(f"```You cannot award the same reward to player. Please choose a different reward```")
                                return start, dmChar 
                                

                            if int(rewardConsumable['Tier']) > tierNum:
                                if not resume:
                                    if rewardUser == dmChar[0]:
                                        await ctx.channel.send(f"```You cannot award yourself this reward because it is outside of your reward tier.```")
                                    else:
                                        await ctx.channel.send(f"```You cannot award this reward because it is outside of your reward tier.```")
                                return start, dmChar 

                            if dmMnc and rewardUser == dmChar[0] and (rewardConsumable['Minor/Major'] != 'Minor' or not rewardConsumable['Consumable']):
                                if not resume:
                                    await ctx.channel.send(f"```You cannot award yourself this reward. Your reward has to be a minor non-consumable reward```")
                                return start, dmChar 
                                
                            if rewardConsumable['Minor/Major'] == 'Minor':
                                if rewardUser == dmChar[0]:
                                    dmMinor += 1
                                else:
                                    minor += 1
                            elif rewardConsumable['Minor/Major'] == 'Major':
                                if rewardUser == dmChar[0]:
                                    dmMajor += 1
                                else:
                                    major += 1
                               
                            rewardMajorLimit = 1
                            rewardMinorLimit = 2

                            rewardMajorErrorString = f"```You cannot award anymore **major** reward items\nTotal rewarded so far:\n({dmChar[4][1]}) Major Rewards \n**({dmChar[4][2]}) Minor Rewards```"
                            rewardMinorErrorString = f"```You cannot award anymore **minor** reward items\nTotal rewarded so far:\n({dmChar[4][1]}) Major Rewards \n**({dmChar[4][2]}) Minor Rewards```"

                            if rewardUser == dmChar[0]:
                                if totalDurationTime > 180:
                                    if chooseOr:
                                        if dmMajor > dmMajorLimit or dmMinor > dmMinorLimit:
                                            if not resume:
                                                await ctx.channel.send(f"```You cannot award yourself anymore major or minor reward items {dmChar[4][3]}```")
                                            return start, dmChar 
                                    else:
                                        if dmMajor > dmMajorLimit:
                                            if not resume:
                                                await ctx.channel.send(f"```You cannot award yourself anymore major reward items {dmChar[4][3]}```")
                                            return start, dmChar 
                                        elif dmMinor > dmMinorLimit:
                                            if not resume:
                                                await ctx.channel.send(f"```You cannot award yourself anymore minor reward items {dmChar[4][4]}```")
                                            return start, dmChar 
                                else:
                                    if not resume:
                                        await ctx.channel.send(f"```Because you have played less than 3 hours, you cannot reward yourself any rewards.```")
                                    return start, dmChar 
                            
                            else:
                                if dmChar[4][0] == 'Spicy Noodle':
                                    if ((major == rewardMajorLimit and minor > rewardMinorLimit-3) or (major == rewardMajorLimit-2 and minor > rewardMinorLimit-2) or (major == rewardMajorLimit-1 and minor > rewardMinorLimit-1) or (major == 0 and minor > rewardMinorLimit))  and rewardConsumable['Minor/Major'] == 'Minor':
                                        if not resume:
                                            await ctx.channel.send(rewardMinorErrorString)
                                        return start, dmChar
                                    elif ((minor == rewardMinorLimit and major > 0) or (minor == rewardMinorLimit-1 and major > rewardMajorLimit-2) or (minor == rewardMinorLimit-2 and major > rewardMajorLimit-1) or (minor <= rewardMinorLimit-3 and major > rewardMajorLimit)) and rewardConsumable['Minor/Major'] == 'Major':
                                        if not resume:
                                            await ctx.channel.send(rewardMajorErrorString)
                                        return start, dmChar
                                elif dmChar[4][0] == 'Ramen Noodle':
                                    if ((major == rewardMajorLimit and minor > rewardMinorLimit-3) or (major == rewardMajorLimit-1 and minor > rewardMinorLimit-2) or (major == rewardMajorLimit-2 and minor > rewardMinorLimit-1) or (major == 0 and minor > rewardMinorLimit))  and rewardConsumable['Minor/Major'] == 'Minor':
                                        if not resume:
                                            await ctx.channel.send(rewardMinorErrorString)
                                        return start, dmChar
                                    elif ((minor == rewardMinorLimit and major > 0) or (minor == rewardMinorLimit-1 and major > rewardMajorLimit-2) or (minor == rewardMinorLimit-2 and major > rewardMajorLimit-1) or (minor <= rewardMinorLimit-3 and major > rewardMajorLimit)) and rewardConsumable['Minor/Major'] == 'Major':
                                        if not resume:
                                            await ctx.channel.send(rewardMajorErrorString)
                                        return start, dmChar
                                elif dmChar[4][0] == 'True Noodle':
                                    if ((major == rewardMajorLimit and minor > rewardMinorLimit-2) or (major == 1 and minor > rewardMinorLimit-1) or (major == 0 and minor > rewardMinorLimit)) and rewardConsumable['Minor/Major'] == 'Minor':
                                        if not resume:
                                            await ctx.channel.send(rewardMinorErrorString)
                                        return start, dmChar
                                    elif ((minor == rewardMinorLimit and major > 0) or (minor == rewardMinorLimit-1 and major > rewardMajorLimit-1)  or (minor <= rewardMinorLimit-2 and major > rewardMajorLimit-2)) and rewardConsumable['Minor/Major'] == 'Major':
                                        if not resume:
                                            await ctx.channel.send(rewardMajorErrorString)
                                        return start, dmChar
                                elif dmChar[4][0] == 'Elite Noodle':
                                    if ((major == rewardMajorLimit and minor > rewardMinorLimit-2) or (major == rewardMajorLimit-1 and minor > rewardMinorLimit-1) or (major == 0 and minor > rewardMinorLimit)) and rewardConsumable['Minor/Major'] == 'Minor' :
                                        if not resume:
                                            await ctx.channel.send(rewardMinorErrorString)
                                        return start, dmChar
                                    elif ((minor == rewardMinorLimit and major > 0) or (minor == rewardMinorLimit-1 and major > rewardMajorLimit-1) or (minor <= rewardMinorLimit-2 and major > rewardMajorLimit)) and rewardConsumable['Minor/Major'] == 'Major':
                                        if not resume:
                                            await ctx.channel.send(rewardMajorErrorString)
                                        return start, dmChar
                                elif dmChar [4][0] == 'Good Noodle':
                                    if ((major == rewardMajorLimit and minor > rewardMinorLimit-1) or (major == 0 and minor > rewardMinorLimit)) and rewardConsumable['Minor/Major'] == 'Minor':
                                        if not resume:
                                            await ctx.channel.send(rewardMinorErrorString)
                                        return start, dmChar
                                    elif ((minor == rewardMinorLimit and major > 0) or (minor <= rewardMinorLimit-1 and major > rewardMajorLimit)) and rewardConsumable['Minor/Major'] == 'Major':
                                        if not resume:
                                            await ctx.channel.send(rewardMajorErrorString)
                                        return start, dmChar
                                else:
                                    if ((major == rewardMajorLimit and minor > rewardMinorLimit - 1) or (major == 0 and minor > rewardMinorLimit)) and rewardConsumable['Minor/Major'] == 'Minor':
                                        if not resume:
                                            await ctx.channel.send(rewardMinorErrorString)
                                        return start, dmChar
                                    elif ((minor == rewardMinorLimit and major > 0) or (rewardMinorLimit-1 <= 1 and rewardMajorLimit > 1)) and rewardConsumable['Minor/Major'] == 'Major' :
                                        if not resume:
                                            await ctx.channel.send(content=rewardMajorErrorString)
                                        return start, dmChar

                            if 'Consumable' in rewardConsumable:
                                if currentItem[1]['Consumables'] == "None":
                                    charConsumableList = [rewardConsumable['Name']]
                                else:
                                    charConsumableList.append(rewardConsumable['Name'])
                                currentItem[1]['Consumables'] = ', '.join(charConsumableList).strip()
                            else:
                                if currentItem[1]['Magic Items'] == "None":
                                    charMagicList = [rewardConsumable['Name']]
                                else:
                                    charMagicList.append(rewardConsumable['Name'])
                                currentItem[1]['Magic Items'] = ', '.join(charMagicList).strip()

                            if currentItem[2] == ["None"]:
                                currentItem[2] = ['+' + rewardConsumable['Name']]
                            else:
                                currentItem[2].append('+' + rewardConsumable['Name'])

                    if rewardUser != dmChar[0]:
                        start[timeKey].remove(oldItem)
                        start[timeKey].append(currentItem)
                        dmChar[4][2] = minor
                        dmChar[4][1] = major
                    else:
                        dmChar[4][3] = dmMinor
                        dmChar[4][4] = dmMajor

                    if not resume:
                        await ctx.channel.send(content=f"I have rewarded {rewardUser.display_name} `{rewardConsumable['Name']}`.\n```Total rewarded so far:\n({major}) Major Rewards\n({minor}) Minor Rewards\n({dmMajor}) DM Major Rewards\n({dmMinor}) DM Minor Rewards```")

                else:
                    if not resume:
                        await ctx.channel.send(content=f"{rewardUser} is not on the timer to recieve rewards.")
            print(start)
            print('dmChar')
            print(dmChar)
            return start, dmChar

    @timer.command()
    async def addme(self,ctx, *, role="", msg=None, start="" ,prep=None, user="", dmChar=None, resume=False, ):
        if ctx.invoked_with == 'prep' or ctx.invoked_with == 'resume':
            startcopy = start.copy()
            userFound = False;
            timeKey = ""
            addUser = user
            channel = ctx.channel

            def addMeEmbedCheck(r, u):
                sameMessage = False
                if addEmbedmsg.id == r.message.id:
                    sameMessage = True
                return ((str(r.emoji) == '✅') or (str(r.emoji) == '❌')) and u == dmChar[0]

            if not resume:
                startTime = time.time()
            else:
                startTime = msg.created_at.replace(tzinfo=timezone.utc).timestamp()

            for u, v in startcopy.items():
                for item in v:
                    if item[0] == addUser:
                        userFound = True
                        timeKey = u
                        
            if not userFound:
                if role != "":
                    userInfo =  await ctx.invoke(self.timer.get_command('signup'), role=role, char=msg, author=addUser, resume=resume) 
                else:
                    userInfo =  await ctx.invoke(self.timer.get_command('signup'), role=role, char=None, author=addUser, resume=resume) 

                if userInfo:
                    if not resume and dmChar :
                        addEmbed = discord.Embed()
                        if role != "":
                            addEmbed.title = f"Add {userInfo[1]['Name']} to timer?"
                            addEmbed.description = f"{addUser.mention} is requesting their character to be added to the timer.\n{userInfo[1]['Name']} - Level {userInfo[1]['Level']}: {userInfo[1]['Race']} {userInfo[1]['Class']}\nConsumables: {', '.join(userInfo[2])}\n\n✅ : Add to timer\n\n❌: Deny"
                        else:
                            addEmbed.title = f"Add {userInfo[0].display_name} to timer?"
                            addEmbed.description = f"{addUser.mention} is requesting to be added to the timer.\n\n✅ : Add to timer\n\n❌: Deny"
                        addEmbedmsg = await channel.send(embed=addEmbed, content=dmChar[0].mention)
                        await addEmbedmsg.add_reaction('✅')
                        await addEmbedmsg.add_reaction('❌')

                        try:
                            tReaction, tUser = await self.bot.wait_for("reaction_add", check=addMeEmbedCheck , timeout=60)
                        except asyncio.TimeoutError:
                            await addEmbedmsg.delete()
                            await channel.send(f'Timer addme canceled. Use `{commandPrefix}timer addme` command and try again!')
                            return start
                        else:
                            await addEmbedmsg.clear_reactions()
                            if tReaction.emoji == '❌':
                                await addEmbedmsg.edit(embed=None, content=f"Request to be added to timer denied.")
                                await addEmbedmsg.clear_reactions()
                                return start
                            await addEmbedmsg.edit(embed=None, content=f"I've added {addUser.display_name} to the timer.")
                    start[f"+Partial Rewards:{startTime}"] = [userInfo]
                else:
                    pass
            elif '%' in timeKey:
                if not resume:
                    await channel.send(content='Your character is dead, you cannot be re-added to the timer.')
            elif '+' in timeKey or 'Full Rewards' in timeKey or 'No Rewards':
                if not resume:
                    await channel.send(content='You have already been added to the timer')
            elif '-' in timeKey:
                if not resume:
                    await channel.send(content='You have been re-added to the timer')
                start[f"{timeKey.replace('-', '+')}:{startTime}"] = start[timeKey]
                del start[timeKey]
            
            else:
                if not resume:
                    await ctx.channel.send(content=f"I cannot find any mention of the user you are trying to add. Please check your format and spelling")
            print(start)
            return start

    @timer.command()
    async def add(self,ctx, *, msg, role="", start="",prep=None, resume=False):
        if ctx.invoked_with == 'prep' or ctx.invoked_with == 'resume':
            guild = ctx.guild
            addList = msg.raw_mentions
            addUser = ""
            if addList != list():
                addUser = guild.get_member(addList[0])
                if prep:
                    return addUser
                else:
                    await ctx.invoke(self.timer.get_command('addme'), role=role, start=start, msg=msg, user=addUser, resume=resume) 
            print(start)
            return start

    @timer.command()
    async def removeme(self,ctx, msg=None, start={},role="",user="", resume=False, death=False):
        if ctx.invoked_with == 'prep' or ctx.invoked_with == 'resume':
            startcopy = start.copy()
            userFound = False
            for u, v in startcopy.items():
                for item in v:
                    if item[0] == user:
                        userFound = u
                        userInfo = item
            if not resume:
                endTime = time.time()
            else:
                endTime = msg.created_at.replace(tzinfo=timezone.utc).timestamp()
            if not userFound:
                if not resume:
                    await ctx.channel.send(content=f"{user}, I couldn't find you on the timer to remove you.") 
                return start

            timeSplit = (userFound + f'?{endTime}').split(':')

            if '-' in userFound or '%' in userFound: 
                if not resume:
                    await ctx.channel.send(content=f"You have already been removed from the timer.")  
            
            elif 'Full Rewards' in userFound or 'No Rewards':
                start[userFound].remove(userInfo)
                if death:
                    start[f"%Partial Rewards:{userFound.split(':')[1]}?{endTime}"] = [userInfo]
                else:
                    start[f"-Partial Rewards:{userFound.split(':')[1]}?{endTime}"] = [userInfo]
                if not resume:
                    await ctx.channel.send(content=f"{user}, I've have removed you from the timer.")
            elif '+' in userFound:
                if  death:
                    start[f"{userFound.replace('+', '%')}?{endTime}"] = start[userFound]
                    del start[userFound]
                else:
                    start[f"{userFound.replace('+', '-')}?{endTime}"] = start[userFound]
                    del start[userFound]
                if not resume:
                    await ctx.channel.send(content=f"{user}, I've have removed you from the timer.")

        print(start)
        return start

    @timer.command()
    async def death(self,ctx, msg, start={}, role="", resume=False):
        if ctx.invoked_with == 'prep' or ctx.invoked_with == 'resume':
            startTimes = await ctx.invoke(self.timer.get_command('remove'), msg=msg, start=start, role=role, resume=resume, death=True)
            return startTimes

    @timer.command()
    async def remove(self,ctx, msg, start={},role="", prep=False, resume=False, death=False):
        if ctx.invoked_with == 'prep' or ctx.invoked_with == 'resume':
            guild = ctx.guild
            removeList = msg.raw_mentions
            removeUser = ""
            if removeList != list():
                removeUser = guild.get_member(removeList[0])
                if prep:
                    return removeUser
                else:
                    await ctx.invoke(self.timer.get_command('removeme'), start=start, msg=msg, role=role, user=removeUser, resume=resume, death=death)
            else:
                if not resume:
                    await ctx.channel.send(content=f"I cannot find any mention of the user you are trying to remove. Please check your format and spelling")

        return start

    
    @timer.command()
    async def stamp(self,ctx, stamp=0, role="", game="", author="", start={}, embed="", embedMsg=""):
        if ctx.invoked_with == 'prep' or ctx.invoked_with == 'resume':
            startcopy = start.copy()
            user = author.display_name
            end = time.time()
            duration = end - stamp
            durationString = timeConversion(duration)
            embed.clear_fields()

            print(start)

            for key, value in startcopy.items():
                for v in value:
                    if value:
                        consumablesString = ""
                        rewardsString = ""
                        if role != "":
                            if v[2] != ['None'] and v[2] != list():
                                cList = []
                                rList = []

                                for i in v[2]:
                                    if '+' in i:
                                        rList.append(i)
                                    else:
                                        cList.append(i)

                                if cList != list():
                                    consumablesString = "\nConsumables: " + ', '.join(cList)
                                if rList != list():
                                    rewardsString = "\nRewards: " + ', '.join(rList)

                        if "Full Rewards" in key and "-" not in key and '%' not in key:
                            embed.add_field(name= f"**{v[0].display_name}**", value=f"**{v[1]['Name']}**{consumablesString}{rewardsString}", inline=False)
                        elif 'No Rewards' in key:
                            embed.add_field(name= f"**{v[0].display_name}**", value=f"{v[0].mention}", inline=False)
                        elif "-" in key:
                            pass
                        elif '%' in key:
                            embed.add_field(name= f"~~{v[0].display_name}~~", value=f"**{v[1]['Name']}** - **DEATH**{consumablesString}{rewardsString}", inline=False) 
                        else:
                            durationEach = 0
                            timeSplit = (key + f'?{end}').split(':')
                            for t in range(1, len(timeSplit)):
                                ttemp = timeSplit[t].split('?')
                                durationEach += (float(ttemp[1]) - float(ttemp[0]))

                            if role != "":
                                embed.add_field(name= f"**{v[0].display_name}** - {timeConversion(durationEach)} (Latecomer)\n", value=f"**{v[1]['Name']}**{consumablesString}{rewardsString}", inline=False)
                            else:
                                embed.add_field(name= f"**{v[0].display_name}** - {timeConversion(durationEach)} (Latecomer)\n", value=v[0].mention, inline=False)
                  
            embed.title = f'**{game}**: {durationString}'
            msgAfter = False

            if role != "":
                stampHelp = f'```{commandPrefix}timer add @player "charactername" "consumables" - **DM** Adds a player \n{commandPrefix}timer addme charactername "consumables" - Adds your character`\n{commandPrefix}timer remove @player - **DM** Removes a player\n{commandPrefix}timer removeme - Removes yourself from the timer.\n{commandPrefix}timer reward @player "rewards" - **DM** Rewards an item to yourself or a player.\n- Consumable - consumes a consumable.\n{commandPrefix}timer stop - stops the current timer.```'
            else:
                stampHelp = f'```{commandPrefix}timer add @player - **DM** Adds a player \n{commandPrefix}timer addme - Adds yourself to the timer`\n{commandPrefix}timer remove @player - **DM** Removes a player\n{commandPrefix}timer removeme - Removes yourself from the timer.\ntimer stop - stops the current timer.```'

            async for message in ctx.channel.history(after=embedMsg, limit=1):
                msgAfter = True
            if not msgAfter:
                await embedMsg.edit(embed=embed, content=stampHelp)
            else:
                if embedMsg:
                    await embedMsg.delete()
                embedMsg = await ctx.channel.send(embed=embed, content=stampHelp)

            return embedMsg

    @timer.command(aliases=['end'])
    async def stop(self,ctx,*,start={}, role="", game="", datestart="", dmChar="", guildsList=""):
        if ctx.invoked_with == 'prep' or ctx.invoked_with == 'resume':
            if not self.timer.get_command(ctx.invoked_with).is_on_cooldown(ctx):
                await ctx.channel.send(content=f"There is no timer to stop or something went wrong with the timer! If you had a timer previously, try `{commandPrefix}timer resume` to resume a timer")
                return
            end = time.time()
            dateend=datetime.now(pytz.timezone(timezoneVar)).strftime("%I:%M %p")
            allRewardStrings = {}
            treasureString = "No Rewards"
            tierNum = 0
            guild = ctx.guild

            stopEmbed = discord.Embed()

            if role == "True":
                tierNum = 4
            elif role == "Elite":
                tierNum = 3
            elif role == "Journey":
                tierNum = 2
            elif role == "":
                stopEmbed.colour = discord.Colour(0xffffff)
            else:
                tierNum = 1


            def updateCharDB(char, tier, cp, tp, gp, death=False, gameID=""):
                tierTP = f"T{tier} TP"
                if char[1]['Level'] >= 20:
                    tierTP = "T5 TP"
                cpSplit= char[1]['CP'].split('/')
                leftCP = (float(cp) + float(cpSplit[0])) 
                tp = float(tp)
                gp = float(gp)
                unset = None
                crossTier = None

                if settingsRecord['ddmrw'] and char == dmChar:
                    leftCP *= 2
                    gp *= 2
                    tp *= 2
              
                if 'Double Rewards Buff' in char[1]:
                    if char[1]['Double Rewards Buff'] < (datetime.now() + timedelta(days=3)):
                        if settingsRecord['ddmrw'] and char == dmChar:
                            leftCP *= 3
                            gp *= 3
                            tp *= 3
                        else:
                            leftCP *= 2
                            gp *= 2
                            tp *= 2
                    unset = {'Double Rewards Buff':1}

                if 'Double Items Buff' in char[1]:
                    unset = {'Double Items Buff':1}

                if char[1]['Level'] in (4,10,16) and leftCP > float(cpSplit[1]):
                    crossCP = leftCP - float(cpSplit[1])
                    if char[1]['Level'] == 4:
                        crossTP = int(decimal.Decimal((crossCP / 2) * 2).quantize(0, rounding=decimal.ROUND_HALF_UP )) / 2
                        crossTier = 'T2 TP'
                    else:
                        crossTP = crossCP

                    if char[1]['Level'] == 10:
                        crossTier = 'T3 TP'
                    elif char[1]['Level'] == 16:
                        crossTier = 'T4 TP'

                    print(tp)
                    tp -= crossTP

                    if tp < 0:
                        tp = 0.0

                    print(crossCP)
                    print(tp)
                    print(crossTP)


                totalCP = f'{leftCP}/{float(cpSplit[1])}'
                charEndConsumables = char[1]['Consumables']
                charEndMagicList = char[1]['Magic Items']
                if charEndConsumables == '':
                    charEndConsumables = 'None'
                if charEndMagicList == '':
                    charEndMagicList = 'None'

                if (float(treasureArray[0]) + float(cpSplit[0])) > float(cpSplit[1]):
                    totalCP = f'{leftCP}/{cpSplit[1]}'

                if tierTP not in char[1]:
                    tpAdd = 0
                else:
                    tpAdd = char[1][tierTP]

                if float(cp) >= .5:
                    char[1]['Games'] += 1

                if gameID is None:
                    returnData = {'_id': char[3],  "fields": {"$set": {'GP': char[1]['GP'] + gp, tierTP: tpAdd + tp, 'CP': totalCP, 'Games':char[1]['Games']}}}
                else:
                    returnData = {'_id': char[3],  "fields": {"$set": {f"GID{str(gameID)}" : f'{{"GP": {char[1]["GP"] + gp}, "{tierTP}": {tpAdd + tp},"Consumables": "{charEndConsumables}", "Magic Items": "{charEndMagicList}", "CP": "{totalCP}", "Games":{char[1]["Games"]}}}'}}}

                if death:
                    returnData =  {'_id': char[3], "fields": {"$set": {'Death': f'{{"GP": {gp}, "{tierTP}": {tp}, "Consumables": "{charEndConsumables}", "Magic Items": "{charEndMagicList}", "CP": {cp}}}'}}}
                
                elif unset:
                    returnData['fields']['$unset'] = unset
                
                if crossTier:
                    returnData['fields']['$set'][crossTier] = crossTP 

                return returnData

            deathChars = []
            data = {"records":[]}
            # Session Log Channel
            logChannel = self.bot.get_channel(663454980140695553) 
            # logChannel = self.bot.get_channel(577227687962214406)
            if role != "":
                await ctx.channel.send("Timer has been stopped! Your session has been posted in the #session-logs channel")
                sessionMessage = await logChannel.send(embed=stopEmbed)
                stopEmbed.set_footer(text=f"Game ID: {sessionMessage.id}")

            for startItemKey, startItemValue in start.items():
                duration = 0
                playerList = []
                startItemsList = (startItemKey+ f'?{end}').split(':')
                if "Full Rewards" in startItemKey or  "No Rewards" in startItemKey:
                    totalDurationTime = end - float(startItemsList[1].split('?')[0])
                    totalDuration = timeConversion(totalDurationTime)

                if '%' in startItemKey:
                    deathChars.append(startItemValue[0])

                if "?" in startItemKey:
                    for t in range(1, len(startItemsList)):
                        ttemp = startItemsList[t].split('?')
                        duration += (float(ttemp[1]) - float(ttemp[0]))
                else:
                    ttemp = startItemsList[1].split('?')
                    duration = (float(ttemp[1]) - float(ttemp[0]))

                treasureArray = calculateTreasure(duration,role)
                if role != "":
                    treasureString = f"{treasureArray[0]} CP, {treasureArray[1]} TP, and {treasureArray[2]} GP"
                else:
                    treasureString = timeConversion(duration)


                for value in startItemValue:
                    if role != "":
                        if 'Double Items Buff' in value[1]: 
                            if value[1]['Double Items Buff'] < (datetime.now() + timedelta(days=3)):
                                rewardsCollection = db.rit
                                rewardList = list(rewardsCollection.find({"Tier": str(tierNum)}))
                                randomItem = random.choice(rewardList)

                                charConsumableList = value[1]['Consumables'].split(', ')
                                charMagicList = value[1]['Magic Items'].split(', ')

                                if 'Consumable' in randomItem:
                                    if value[1]['Consumables'] == "None":
                                        charConsumableList = [randomItem['Name']]
                                    else:
                                        charConsumableList.append(randomItem['Name'])
                                        charConsumableList.sort()
                                    value[1]['Consumables'] = ', '.join(charConsumableList).strip()
                                else:
                                    if value[1]['Magic Items'] == "None":
                                        charMagicList = [randomItem['Name']]
                                    else:
                                        charMagicList.append(randomItem['Name'])
                                        charMagicList.sort()
                                    value[1]['Magic Items'] = ', '.join(charMagicList).strip()


                                if value[2] != ["None"]:
                                    value[2].append('(DI)+'+ randomItem['Name'])
                                else:
                                    value[2] = ['(DI)+'+ randomItem['Name']]
                              
                        charRewards = updateCharDB(value, tierNum, treasureArray[0], treasureArray[1], treasureArray[2], (value in deathChars), sessionMessage.id)
                        data["records"].append(charRewards)
                    playerList.append(value)

                print('playerList')
                print(playerList)

                if "Partial Rewards" in startItemKey and role == "":
                    if treasureString not in allRewardStrings:
                        allRewardStrings[treasureString] = playerList
                    else:
                        allRewardStrings[treasureString] += playerList 
                else:
                    if f'{role} Friend Full Rewards - {treasureString}' in allRewardStrings:
                        allRewardStrings[f'{role} Friend Full Rewards - {treasureString}'] += playerList
                    elif f"{startItemsList[0].replace('+', '').replace('-', '').replace('%', '')} - {treasureString}" not in allRewardStrings:
                        allRewardStrings[f"{startItemsList[0].replace('+', '').replace('-', '').replace('%', '')} - {treasureString}"] = playerList
                    else:
                        allRewardStrings[f"{startItemsList[0].replace('+', '').replace('-', '').replace('%', '')} - {treasureString}"] += playerList

            stopEmbed.title = f"Timer: {game} [END] - {totalDuration}"
            stopEmbed.description = f"{datestart} to {dateend} CDT" 

            charLevel = int(dmChar[1]['Level'])

            if charLevel < 5:
                dmRole = 'Junior'
            elif charLevel < 11:
                dmRole = 'Journey'
            elif charLevel < 17:
                dmRole = 'Elite'
            elif charLevel < 21:
                dmRole = 'True'

            dmtreasureArray = calculateTreasure(totalDurationTime,dmRole)    
            # DM update
            if 'Double Items Buff' in dmChar[1]: 
                if dmChar[1]['Double Items Buff'] < (datetime.now() + timedelta(days=3)):
                    rewardsCollection = db.rit
                    rewardList = list(rewardsCollection.find({"Tier": str(tierNum)}))
                    randomItem = random.choice(rewardList)

                    charConsumableList = dmChar[1]['Consumables'].split(', ')
                    charMagicList = dmChar[1]['Magic Items'].split(', ')

                    if 'Consumable' in randomItem:
                        if dmChar[1]['Consumables'] == "None":
                            charConsumableList = [randomItem['Name']]
                        else:
                            charConsumableList.append(randomItem['Name'])
                            charConsumableList.sort()
                        dmChar[1]['Consumables'] = ', '.join(charConsumableList).strip()
                    else:
                        if dmChar[1]['Magic Items'] == "None":
                            charMagicList = [randomItem['Name']]
                        else:
                            charMagicList.append(randomItem['Name'])
                            charMagicList.sort()
                        dmChar[1]['Magic Items'] = ', '.join(charMagicList).strip()


                    if dmChar[2] == ["None"]:
                        dmChar[2] = ["(DI)+" + randomItem['Name']]
                    else:
                        dmChar[2].append("(DI)+" + randomItem['Name'])

            dmRewardsList = []
            for d in dmChar[2]:
                if '+' in d:
                    dmRewardsList.append(d)

            if role != "":
                data["records"].append(updateCharDB(dmChar, roleArray.index(dmRole) + 1, dmtreasureArray[0], dmtreasureArray[1], dmtreasureArray[2], False, sessionMessage.id ))
            else:
                data["records"].append(updateCharDB(dmChar, roleArray.index(dmRole) + 1, dmtreasureArray[0], dmtreasureArray[1], dmtreasureArray[2], False, None))

            playersCollection = db.players
            usersCollection = db.users

            # Noodles Math
            uRecord  = usersCollection.find_one({"User ID": str(dmChar[0].id)})
            noodles = 0
            minutesPlayed = totalDurationTime // 60
            minutesRounded = minutesPlayed % 30

            if minutesRounded >= 15:
                minutesPlayed += (30 - minutesRounded)

            hoursPlayed = (minutesPlayed / 60)
            noodlesGained = sparklesGained = int(hoursPlayed) // 3

            print(int(noodlesGained))

            if uRecord:
                if 'Noodles' not in uRecord:
                    uRecord['Noodles'] = 0
                else:
                    noodles += uRecord['Noodles'] + noodlesGained

            noodleString = "Current Noodles: " + str(noodles)
            dmRoleNames = [r.name for r in dmChar[0].roles]
            if noodles >= 150 and 'Ramen Noodle' in dmRoleNames:
                if 'Spicy Noodle' not in dmRoleNames:
                    noodleRole = get(guild.roles, name = 'Spicy Noodle')
                    await dmChar[0].add_roles(noodleRole, reason=f"DMed 150 games. This user has 150+ noodles")
                    await dmChar[0].remove_roles(get(guild.roles, name = 'Ramen Noodle'))
                    noodleString += "\nSpicy Noodle Role recieved! :tada:"
            elif noodles >= 100 and 'True Noodle' in dmRoleNames:
                if 'Ramen Noodle' not in dmRoleNames:
                    noodleRole = get(guild.roles, name = 'Ramen Noodle')
                    await dmChar[0].add_roles(noodleRole, reason=f"DMed 100 games. This user has 100+ noodles")
                    await dmChar[0].remove_roles(get(guild.roles, name = 'True Noodle'))
                    noodleString += "\nRamen Noodle Role recieved! :tada:"

            elif noodles >= 60 and 'Elite Noodle' in dmRoleNames:
                if 'True Noodle' not in dmRoleNames:
                    noodleRole = get(guild.roles, name = 'True Noodle')
                    await dmChar[0].add_roles(noodleRole, reason=f"DMed 60 games. This user has 60+ noodles")
                    await dmChar[0].remove_roles(get(guild.roles, name = 'Elite Noodle'))
                    noodleString += "\nTrue Noodle Role recieved! :tada:"
            
            elif noodles >= 30 and 'Good Noodle' in dmRoleNames:
                if 'Elite Noodle' not in dmRoleNames:
                    noodleRole = get(guild.roles, name = 'Elite Noodle')
                    await dmChar[0].add_roles(noodleRole, reason=f"DMed 30 games. This user has 30+ noodles")
                    await dmChar[0].remove_roles(get(guild.roles, name = 'Good Noodle'))
                    noodleString += "\nElite Noodle Role recieved! :tada:"

            elif noodles >= 10:
                if 'Good Noodle' not in dmRoleNames:
                    noodleRole = get(guild.roles, name = 'Good Noodle')
                    await dmChar[0].add_roles(noodleRole, reason=f"DMed 10 games. This user has 10+ noodles")
                    noodleString += "\nGood Noodle Role recieved! :tada:"

            if role != "": 
                stopEmbed.clear_fields() 
                allRewardsTotalString = ""
                for key, value in allRewardStrings.items():
                    temp = ""
                    for v in value:
                        vRewardList = []
                        for r in v[2]:
                            if '+' in r:
                                vRewardList.append(r)
                        if v not in deathChars:
                            if 'Double Rewards Buff'  in v[1]:
                                temp += f"{v[0].mention} | {v[1]['Name']} **DOUBLE REWARDS!** {', '.join(vRewardList).strip()}\n"
                            else:
                                temp += f"{v[0].mention} | {v[1]['Name']} {', '.join(vRewardList).strip()}\n"
                        else:
                            temp += f"~~{v[0].mention} | {v[1]['Name']}~~ **DEATH** {', '.join(vRewardList).strip()}\n"
                    if temp == "":
                        temp = 'None'
                    stopEmbed.add_field(name=f"**{key}**\n", value=temp, inline=False)
                    allRewardsTotalString += temp + "\n"

                doubleRewardsString = ""
                doubleItemsString = ""        
                
                if 'Double Rewards Buff' in dmChar[1]:
                    doubleRewardsString = ' **(DOUBLE REWARDS)**:'
                if 'Double Items Buff' in dmChar[1] and dmChar[2] != ['None']:
                    doubleItemsString += '- ' + ', '.join(dmChar[2])

                guildsCollection = db.guilds
                guildMember = False
                guildsListStr = ""
                guildsRecordsList = list()

                if guildsList != list():
                    guildsListStr = "Guilds: "
                    for g in guildsList:
                        gRecord  = guildsCollection.find_one({"Channel ID": str(g.id)})
                        if gRecord:
                            gRecord['Old Reputation'] = gRecord['Reputation']
                            if hoursPlayed >= 3:
                                for p in playerList:
                                    if 'Guild' in p[1]:
                                        if gRecord['Name'] in p[1]['Guild']:
                                            guildMember = True
                                            gRecord['Reputation'] += sparklesGained
                                if 'Guild' in dmChar[1]:
                                        if gRecord['Name'] in dmChar[1]['Guild']:
                                            guildMember = True
                                            gRecord['Reputation'] += sparklesGained + 1

                                if 'Games' not in gRecord:
                                    gRecord['Games'] = 1
                                else:
                                    gRecord['Games'] += 1
                                    if gRecord['Games'] % 10 == 0:
                                        guildBuffList = list(playersCollection.find({"Guild": gRecord['Name'], "Reputation": {'$gt':1}}))
                                        if guildBuffList:
                                            for d in data['records']:
                                                if d['_id'] in [gb['_id'] for gb in guildBuffList]:
                                                    d['fields']['$set']['Double Rewards Buff'] = datetime.now()
                                                    if '$unset' in d['fields']:
                                                        if 'Double Rewards Buff' in d['fields']['$unset']:
                                                            del d['fields']['$unset']['Double Rewards Buff']
                                                            if  d['fields']['$unset'] == dict():
                                                                del d['fields']['$unset']

                                    elif gRecord['Games'] % 5 == 0:
                                        guildBuffList = list(playersCollection.find({"Guild": gRecord['Name'], "Reputation": {'$gt':1}}))
                                        if guildBuffList:
                                            for d in data['records']:
                                                if d['_id'] in [gb['_id'] for gb in guildBuffList]:
                                                    d['fields']['$set']['Double Items Buff'] = datetime.now()
                                                    if '$unset' in d['fields']:
                                                        if 'Double Items Buff' in d['fields']['$unset']:
                                                            del d['fields']['$unset']['Double Items Buff']
                                                            if  d['fields']['$unset'] == dict():
                                                                del d['fields']['$unset']
                            guildsRecordsList.append(gRecord)

                timerData = list(map(lambda item: UpdateOne({'_id': item['_id']}, item['fields']), data['records']))

                guildRewardsStr = ""

                for g in guildsRecordsList:
                    guildRewardsStr += f"{g['Name']}: +{g['Reputation'] - gRecord['Old Reputation']} :sparkles:"

                stopEmbed.title = f"\n**{game}**\n*Tier {tierNum} Quest* \n#{ctx.channel}"
                stopEmbed.description = f"{guildsListStr}{', '.join([g.mention for g in guildsList])}\n{datestart} to {dateend} CDT ({totalDuration})"
                stopEmbed.add_field(value=f"**DM:** {dmChar[0].mention} | {dmChar[1]['Name']} {', '.join(dmRewardsList)}{doubleItemsString}\n{':star:' * noodlesGained} {noodleString}", name=f"DM Rewards{doubleRewardsString}: (Tier {roleArray.index(dmRole) + 1}) - **{dmtreasureArray[0]} CP, {dmtreasureArray[1]} TP, and {dmtreasureArray[2]} GP**\n")
                if guildRewardsStr != "":
                    stopEmbed.add_field(value=guildRewardsStr, name=f"Guild Rewards", inline=False)
                sessionLogString = f"\n**{game}**\n*Tier {tierNum} Quest*\n#{ctx.channel}\n\n**Runtime**: {datestart} to {dateend} CDT ({totalDuration})\n\n{allRewardsTotalString}\nGame ID:"

                # Grab stats
                dateyear = datestart.split('-')
                dateyear = dateyear[0] + '-' + dateyear[2][:2]
                statsCollection = db.stats

                statsRecord  = statsCollection.find_one({'Date': dateyear})
                if not statsRecord:
                    statsRecord = {'Date': dateyear, 'DM': {}}
                

                # If greater than 15 mins.
                if float(dmtreasureArray[0]) >= .5:
                    if str(dmChar[0].id) in statsRecord['DM']:
                        if f'T{tierNum}' in statsRecord['DM'][str(dmChar[0].id)]:
                            statsRecord['DM'][str(dmChar[0].id)][f'T{tierNum}'] += 1
                        else:
                            statsRecord['DM'][str(dmChar[0].id)][f'T{tierNum}'] = 1
                    else:
                        statsRecord['DM'][str(dmChar[0].id)] = {f'T{tierNum}':1}
                    

                    if f'T{tierNum}' in statsRecord:
                        statsRecord[f'T{tierNum}'] += 1
                    else:
                        statsRecord[f'T{tierNum}'] = 1

                    if guildsRecordsList != list():
                        if 'GQ' in statsRecord:
                            statsRecord['GQ'] += 1
                        else:
                            statsRecord['GQ'] = 1

                        if guildMember: 
                            if 'GQM' in statsRecord:
                                statsRecord['GQM'] += 1
                            else:
                                statsRecord['GQM'] = 1
                        elif not guildMember:
                            if 'GQNM' in statsRecord:
                                statsRecord['GQNM'] += 1
                            else:
                                statsRecord['GQNM'] = 1

                    if 'Unique Players' not in statsRecord:
                        statsRecord['Unique Players'] = set()

                    statsRecord['Unique Players'] = set(statsRecord['Unique Players'])
                    statsRecord['Unique Players'].update([p[0].id for p in playerList])
                    statsRecord['Unique Players'].add(dmChar[0].id)
                    statsRecord['Unique Players'] = list(statsRecord['Unique Players'])

                    if 'Playtime' in statsRecord:
                        statsRecord['Playtime'].append(totalDurationTime)
                    else:
                        statsRecord['Playtime'] = [totalDurationTime]

                    if 'Players' in statsRecord:
                        statsRecord['Players'].append(len(playerList) + 1)
                    else:
                        statsRecord['Players'] = [len(playerList) + 1] 


                try:
                    playersCollection.bulk_write(timerData)
                except BulkWriteError as bwe:
                    print(bwe.details)
                    return

                await sessionMessage.edit(embed=stopEmbed)

                try:
                    statsCollection.update_one({'Date':dateyear}, {"$set": statsRecord}, upsert=True)
                    usersCollection.update_one({'User ID': str(dmChar[0].id)}, {"$set": {'User ID':str(dmChar[0].id), 'P-Noodles': noodles}}, upsert=True)
                    usersData = list(map(lambda item: UpdateOne({'_id': item[3]}, {'$set': {'User ID':str(item[0].id) }}, upsert=True), playerList))
                    usersCollection.bulk_write(usersData)
                    #TODO: why is it giving one rep?
                    if guildsRecordsList != list():
                        guildsData = list(map(lambda item: UpdateOne({'_id': item['_id']}, {'$set': {'P-Games':item['Games'], 'P-Reputation': item['Reputation']}}, upsert=True), guildsRecordsList))
                        guildsCollection.bulk_write(guildsData)
                except Exception as e:
                    print ('MONGO ERROR: ' + str(e))
                    charEmbedmsg = await ctx.channel.send(embed=None, content="Uh oh, looks like something went wrong. Please try the timer again.")
                else:
                    print('Success')

            else:
                stopEmbed.clear_fields()
                stopEmbed.set_footer(text=stopEmbed.Empty)
                dmRecords = data['records'][0]

                playerData = []
                campaignCollection = db.campaigns
                campaignRecord = list(campaignCollection.find({"Channel ID": str(ctx.channel.id)}))[0]

                for key, value in allRewardStrings.items():
                    temp = ""
                    numbers = [int(word) for word in key.split() if word.isdigit()]
                    tempTime = (numbers[0] * 3600) + (numbers[1] * 60) 
                    for v in value:
                        temp += f"{v[0].mention}\n"
                        v[1]['Campaigns'][campaignRecord['Name']] += tempTime
                        playerData.append(v[1])
                        stopEmbed.add_field(name=key, value=temp, inline=False)

                try:
                    usersCollection.update_one({'User ID': str(dmChar[0].id)}, {"$set": {'User ID':str(dmChar[0].id), 'Noodles': noodles}}, upsert=True)
                    usersData = list(map(lambda item: UpdateOne({'_id': item['_id']}, {'$set': item}, upsert=True), playerData))
                    usersCollection.bulk_write(usersData)
                    playersCollection.update_one({'_id': dmRecords['_id']},  dmRecords['fields'] , upsert=True)
                except Exception as e:
                    print ('MONGO ERROR: ' + str(e))
                    charEmbedmsg = await ctx.channel.send(embed=None, content="Uh oh, looks like something went wrong. Please try the timer again.")
                else:
                    print('Success')  

                await ctx.channel.send(embed=stopEmbed)


            self.timer.get_command('start').reset_cooldown(ctx)
            self.timer.get_command('resume').reset_cooldown(ctx)

        return

    @timer.command()
    @commands.has_any_role('Mod Friend', 'Admins')
    async def list(self,ctx):
        if not currentTimers:
            currentTimersString = "There are currently NO timers running!"
        else:
            currentTimersString = "There are currently timers running in these channels:\n"
        for i in currentTimers:
            currentTimersString = f"{currentTimersString} - {i} \n"
        await ctx.channel.send(content=currentTimersString)

    @timer.command()
    @commands.has_any_role('Mod Friend', 'Admins')
    async def resetcooldown(self,ctx):
        self.timer.get_command('start').reset_cooldown(ctx)
        self.timer.get_command('resume').reset_cooldown(ctx)
        await ctx.channel.send(f"Timer has been reset in #{ctx.channel}")

    @commands.cooldown(1, float('inf'), type=commands.BucketType.channel) 
    @timer.command()
    #TODO: cmapaign resume timer
    async def resume(self,ctx):
        if not self.timer.get_command('start').is_on_cooldown(ctx):
            def predicate(message):
                return message.author.bot

            channel=ctx.channel
        
            if str(channel.category).lower() not in gameCategory:
                if "no-context" in channel.name or "secret-testing-area" or  "bot2-testing" in channel.name:
                    pass
                else:
                    await channel.send('Try this command in a game channel!')
                    self.timer.get_command('resume').reset_cooldown(ctx)
                    return

            if self.timer.get_command('start').is_on_cooldown(ctx):
                await channel.send(f"There is already a timer that has started in this channel! If you started the timer, type `{commandPrefix}timer stop` to stop the current timer")
                self.timer.get_command('resume').reset_cooldown(ctx)
                return

            timerCog = self.bot.get_cog('Timer')
            global currentTimers
            author = ctx.author
            resumeTimes = {}
            timerMessage = None
            guild = ctx.guild

            async for message in ctx.channel.history(limit=200).filter(predicate):
                if "Timer: Starting the timer" in message.content:
                    timerMessage = message
                    startString = (timerMessage.content.split('\n', 1))[0]
                    startRole = re.search('\(([^)]+)', startString)
                    if startRole is None:
                        startRole = ''
                    else: 
                        startRole = startRole.group(1).split()[0]

                    startGame = re.search('\*\*(.*?)\*\*', startString).group(1)
                    startTimerCreate = timerMessage.created_at
                    startTime = startTimerCreate.replace(tzinfo=timezone.utc).timestamp()
                    resumeTimes = {f"{startRole} Friend Rewards":startTime}
                    datestart = startTimerCreate.replace(tzinfo=timezone.utc).astimezone(tz=pytz.timezone(timezoneVar)).strftime("%b-%-d-%y %I:%M %p") 

                    async for m in ctx.channel.history(before=timerMessage, limit=10):
                        if m.embeds:
                            commandMessage = m
                            commandEmbed = (m.embeds[0].to_dict())
                            commandMessage.content += commandEmbed['description']

                            resumeString=[]
                            guildsList = commandMessage.channel_mentions
                            for f in commandEmbed['fields']:
                                if 'DM' in f['name'] or '<@' in f['value']:
                                    resumeString.append(f"{f['name']}={f['value']}")
                            commandMessage.content = ', '.join(resumeString)

                        if m.content == f'{commandPrefix}timer start' or m.content == f'{commandPrefix}t start':
                            playerResumeList = [m.author.id] + commandMessage.raw_mentions
                            author = m.author
                            break

                    start = []

                    playersCollection = db.players
                    if "norewards" not in commandMessage.content and startRole: 
                        # userList = re.search('"([^"]*)"', commandMessage).group(1).split(',')
                        playerInfoList = commandMessage.content.split(',')
                        for p in range (len(playerResumeList)):
                            pTemp = []
                            pConsumables = ['None']
                            pTemp.append(guild.get_member(int(playerResumeList[p])))
                            if p == 0:
                                pName = playerInfoList[p].split(' will recieve DM rewards')[0].split('=')[1]
                               
                            else:
                                pName = playerInfoList[p].split('=')[0]

                            cRecord  = list(playersCollection.find({"User ID": str(playerResumeList[p]), "Name": {"$regex": pName.strip(), '$options': 'i' }}))

                            if p > 0:
                                pConsumables = playerInfoList[p].split('Consumables: ')[1].split(',')
                                pTemp += [cRecord[0],pConsumables,cRecord[0]['_id']]
                                start.append(pTemp)
                            else:
                                pTemp += [cRecord[0],pConsumables,cRecord[0]['_id']] 
                                dmChar = pTemp
                                dmChar.append(['Junior Noodle',0,0,0,0])

                                for r in dmChar[0].roles:
                                    if 'Noodle' in r.name:
                                        dmChar[4] = [r.name,0,0,0,0]
                                        break

                        print(start)
                        resumeTimes = {f"{startRole} Friend Full Rewards:{startTime}":start} 


                    else: 
                        resumeTimes = {f"No Rewards:{startTime}":start}

                    async for message in ctx.channel.history(after=timerMessage):
                        if (f"{commandPrefix}timer add " in message.content or f"{commandPrefix}t add " in message.content) and not message.author.bot:
                            resumeTimes = await ctx.invoke(self.timer.get_command('add'), start=resumeTimes, role=startRole, msg=message, resume=True)
                        elif  (f"{commandPrefix}timer addme" in message.content or f"{commandPrefix}t addme" in message.content) and not message.author.bot and (message.content != f'{commandPrefix}timer addme' or message.content != f'{commandPrefix}t addme'):
                            resumeTimes = await ctx.invoke(self.timer.get_command('addme'), start=resumeTimes, role=startRole, dmChar=dmChar, msg=message, user=message.author, resume=True) 
                        elif ((f"{commandPrefix}timer removeme" in message.content or f"{commandPrefix}timer remove " in message.content) or (f"{commandPrefix}t removeme" in message.content or f"{commandPrefix}t remove " in message.content)) and not message.author.bot: 
                            if f"{commandPrefix}timer removeme" in message.content or f"{commandPrefix}t removeme" in message.content:
                                resumeTimes = await ctx.invoke(self.timer.get_command('removeme'), msg=message, start=resumeTimes, role=startRole, user=message.author, resume=True)
                            elif f"{commandPrefix}timer remove " in message.content or f"{commandPrefix}t remove " in message.content:
                                resumeTimes = await ctx.invoke(self.timer.get_command('remove'), msg=message, start=resumeTimes, role=startRole, resume=True)
                        elif f"{commandPrefix}timer death" in message.content or f"{commandPrefix}t death" in message.content:
                            resumeTimes = await ctx.invoke(self.timer.get_command('death'), msg=message, start=resumeTimes, role=startRole, resume=True) 
                        elif message.content.startswith('-') and message.author != dmChar[0]: 
                            resumeTimes = await ctx.invoke(self.timer.get_command('deductConsumables'), msg=message, start=resumeTimes, resume=True)
                        elif (f"{commandPrefix}timer reward" in message.content or f"{commandPrefix}t reward" in message.content) and (message.author == author):
                            resumeTimes,dmChar = await ctx.invoke(self.timer.get_command('reward'), msg=message, start=resumeTimes, dmChar=dmChar, resume=True)
                        elif ("Timer has been stopped!" in message.content) and message.author.bot:
                            await channel.send("There doesn't seem to be a timer to resume here... Please start a new timer!")
                            self.timer.get_command('resume').reset_cooldown(ctx)
                            return

                    break

                    print(resumeTimes)

            if timerMessage is None or commandMessage is None:
                await channel.send("There is no timer in the last 200 messages. Please start a new timer.")
                self.timer.get_command('resume').reset_cooldown(ctx)
                return

            await channel.send(embed=None, content=f"Timer: I have resumed the timer for - **{startGame}** {startRole}." )
            currentTimers.append('#'+channel.name)

            stampEmbed = discord.Embed()
            stampEmbed.set_footer(text=f'#{ctx.channel}\n{commandPrefix}timer help for help with the timer.')
            stampEmbed.set_author(name=f'DM: {author.display_name}', icon_url=author.avatar_url)
            stampEmbedmsg = None

            # During Timer
            await timerCog.duringTimer(ctx, datestart, startTime, resumeTimes, startRole, startGame, author, stampEmbed, stampEmbedmsg,dmChar,guildsList)

            self.timer.get_command('resume').reset_cooldown(ctx)
            currentTimers.remove('#'+channel.name)
        else:
            await ctx.channel.send(content=f"There is already a timer that has started in this channel! If you started the timer, type `{commandPrefix}timer stop` to stop the current timer")
            return


    async def duringTimer(self,ctx, datestart, startTime, startTimes, role, game, author, stampEmbed, stampEmbedmsg, dmChar, guildsList):
        if ctx.invoked_with == "resume":
            stampEmbedmsg = await ctx.invoke(self.timer.get_command('stamp'), stamp=startTime, role=role, game=game, author=author, start=startTimes, embed=stampEmbed, embedMsg=stampEmbedmsg)
        
        timerStopped = False
        channel = ctx.channel
        user = author.display_name

        timerAlias = ["timer", "t"]

        if role != "":
            timerCommands = ['transfer', 'stop', 'end', 'add', 'remove', 'death', 'reward']
        else:
            timerCommands = ['transfer', 'stop', 'end', 'add', 'remove']

      
        timerCombined = []

        for x in product(timerAlias,timerCommands):
            timerCombined.append(f"{commandPrefix}{x[0]} {x[1]}")

        while not timerStopped:
            try:
                if role != "":
                    msg = await self.bot.wait_for('message', timeout=60.0, check=lambda m: (any(x in m.content for x in timerCombined) or m.content.startswith('-')) and m.channel == channel)
                else:
                    msg = await self.bot.wait_for('message', timeout=60.0, check=lambda m: (any(x in m.content for x in timerCombined)) and m.channel == channel)

                if (f"{commandPrefix}timer transfer " in msg.content or f"{commandPrefix}t transfer " in msg.content) and (msg.author == author or "Mod Friend".lower() in [r.name.lower() for r in msg.author.roles] or "Admins".lower() in [r.name.lower() for r in msg.author.roles]):
                    if f'{commandPrefix}timer transfer ' in msg.content:
                      newUser = msg.content.split(f'{commandPrefix}timer transfer ')[1] 
                    elif f'{commandPrefix}t transfer ' in msg.content:
                      newUser = msg.content.split(f'{commandPrefix}t transfer ')[1] 

                    newAuthor = await ctx.invoke(self.timer.get_command('transfer'), user=newUser) 
                    if newAuthor is not None:
                        author = newAuthor
                        await channel.send(f'{author.mention}, the current timer has been transferred to you. Use `{commandPrefix}timer stop` whenever you would like to stop the timer.')
                    else:
                        await channel.send(f'Sorry, I could not find the user `{newUser}` to transfer the timer')
                elif (msg.content == f"{commandPrefix}timer stop" or msg.content == f"{commandPrefix}timer end" or msg.content == f"{commandPrefix}t stop" or msg.content == f"{commandPrefix}t end") and (msg.author == author or "Mod Friend".lower() in [r.name.lower() for r in msg.author.roles] or "Admins".lower() in [r.name.lower() for r in msg.author.roles]):
                    timerStopped = True
                    await ctx.invoke(self.timer.get_command('stop'), start=startTimes, role=role, game=game, datestart=datestart, dmChar=dmChar, guildsList=guildsList)
                    return
                elif (f"{commandPrefix}timer add " in msg.content or f"{commandPrefix}t add " in msg.content) and '@player' not in msg.content:
                    startTimes = await ctx.invoke(self.timer.get_command('add'), start=startTimes, role=role, msg=msg)
                    stampEmbedmsg = await ctx.invoke(self.timer.get_command('stamp'), stamp=startTime, role=role, game=game, author=author, start=startTimes, embed=stampEmbed, embedMsg=stampEmbedmsg)
                elif (f"{commandPrefix}timer addme " in msg.content or f"{commandPrefix}t addme " in msg.content) and '@player' not in msg.content and (msg.content != f'{commandPrefix}timer addme' or msg.content != f'{commandPrefix}t addme'):
                    startTimes = await ctx.invoke(self.timer.get_command('addme'), start=startTimes, role=role, msg=msg, user=msg.author, dmChar=dmChar)
                    stampEmbedmsg = await ctx.invoke(self.timer.get_command('stamp'), stamp=startTime, role=role, game=game, author=author, start=startTimes, embed=stampEmbed, embedMsg=stampEmbedmsg)
                elif msg.content == f"{commandPrefix}timer removeme" or msg.content == f"{commandPrefix}t removeme":
                    startTimes = await ctx.invoke(self.timer.get_command('removeme'), start=startTimes, role=role, user=msg.author)
                    stampEmbedmsg = await ctx.invoke(self.timer.get_command('stamp'), stamp=startTime, role=role, game=game, author=author, start=startTimes, embed=stampEmbed, embedMsg=stampEmbedmsg)
                elif (f"{commandPrefix}timer remove " in msg.content or f"{commandPrefix}t remove " in msg.content) and (msg.author == author or "Mod Friend".lower() in [r.name.lower() for r in msg.author.roles] or "Admins".lower() in [r.name.lower() for r in msg.author.roles]): 
                    startTimes = await ctx.invoke(self.timer.get_command('remove'), msg=msg, start=startTimes, role=role)
                    stampEmbedmsg = await ctx.invoke(self.timer.get_command('stamp'), stamp=startTime, role=role, game=game, author=author, start=startTimes, embed=stampEmbed, embedMsg=stampEmbedmsg)
                elif (f"{commandPrefix}timer reward" in msg.content or f"{commandPrefix}t reward" in msg.content) and (msg.author == author):
                    startTimes,dmChar = await ctx.invoke(self.timer.get_command('reward'), msg=msg, start=startTimes,dmChar=dmChar)
                    stampEmbedmsg = await ctx.invoke(self.timer.get_command('stamp'), stamp=startTime, role=role, game=game, author=author, start=startTimes, embed=stampEmbed, embedMsg=stampEmbedmsg)
                elif (f"{commandPrefix}timer death" in msg.content or f"{commandPrefix}t death" in msg.content) and (msg.author == author):
                    startTimes = await ctx.invoke(self.timer.get_command('death'), msg=msg, start=startTimes, role=role)
                    stampEmbedmsg = await ctx.invoke(self.timer.get_command('stamp'), stamp=startTime, role=role, game=game, author=author, start=startTimes, embed=stampEmbed, embedMsg=stampEmbedmsg)
                elif msg.content.startswith('-') and msg.author != dmChar[0]:
                    startTimes = await ctx.invoke(self.timer.get_command('deductConsumables'), msg=msg, start=startTimes)
                    stampEmbedmsg = await ctx.invoke(self.timer.get_command('stamp'), stamp=startTime, role=role, game=game, author=author, start=startTimes, embed=stampEmbed, embedMsg=stampEmbedmsg)


            except asyncio.TimeoutError:
                stampEmbedmsg = await ctx.invoke(self.timer.get_command('stamp'), stamp=startTime, role=role, game=game, author=author, start=startTimes, embed=stampEmbed, embedMsg=stampEmbedmsg)
            else:
                pass

def setup(bot):
    bot.add_cog(Timer(bot))
