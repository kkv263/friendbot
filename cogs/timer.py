import discord
import pytz
import asyncio
import time
import requests
import re
from discord.utils import get        
from datetime import datetime, timezone
from discord.ext import commands
from bfunc import numberEmojis, calculateTreasure, timeConversion, gameCategory, commandPrefix, roleArray, timezoneVar, currentTimers, headers, db, callAPI
from pymongo import UpdateOne

class Timer(commands.Cog):
    def __init__ (self, bot):
        self.bot = bot

    @commands.group(aliases=['t'])
    async def timer(self, ctx):	
        pass

    @timer.command()
    async def help(self,ctx):
        helpCommand = self.bot.get_command('help')
        await ctx.invoke(helpCommand, pageString='timer')

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

        if str(channel.category).lower() not in gameCategory:
            if "no-context" in channel.name or "secret-testing-area" in channel.name:
                pass
            else: 
                await channel.send('Try this command in a game channel!')
                self.timer.get_command('prep').reset_cooldown(ctx)
                return

        if '"' not in ctx.message.content and userList != "norewards":
            await channel.send(f"Please make sure you put quotes `\"` around your list of players and retry the command")
            self.timer.get_command('prep').reset_cooldown(ctx)
            return

        prepEmbed = discord.Embed()

        if author in ctx.message.mentions:
            await channel.send(f"You cannot start a timer with yourself in the player list!")
            self.timer.get_command('prep').reset_cooldown(ctx)
            return 

        guildsList = []
        guildsListStr = ""
        if ctx.message.channel_mentions != list():
            guildsList = ctx.message.channel_mentions
            guildsListStr = "Guilds: "

        playerRoster = [author] + ctx.message.mentions

        prepEmbed.add_field(name=f"React with [1-5] for your type of game: **{game}**\nPlease re-react with your choice if your prompt does not go through.", value=f"{numberEmojis[0]} New / Junior Friend [1-4]\n{numberEmojis[1]} Journey Friend [5-10]\n{numberEmojis[2]} Elite Friend [11-16]\n{numberEmojis[3]} True Friend [17-20]\n{numberEmojis[4]} Timer Only [No Rewards]", inline=False)
        prepEmbed.set_author(name=userName, icon_url=author.avatar_url)
        prepEmbed.set_footer(text= "React with ❌ to cancel")

        try:
            prepEmbedMsg = await channel.send(embed=prepEmbed)
            for num in range(0,5): await prepEmbedMsg.add_reaction(numberEmojis[num])
            await prepEmbedMsg.add_reaction('❌')
            tReaction, tUser = await self.bot.wait_for("reaction_add", check=startEmbedcheck, timeout=60)
        except asyncio.TimeoutError:
            await prepEmbedMsg.delete()
            await channel.send('Timer timed out! Try starting the timer again.')
            self.timer.get_command('prep').reset_cooldown(ctx)
            return

        else:
            role = ""
            await asyncio.sleep(1) 
            await prepEmbedMsg.clear_reactions()

            if tReaction.emoji == '❌':
                await prepEmbedMsg.edit(embed=None, content=f"Timer canceled. Type `{commandPrefix}timer start` to start another timer!")
                self.timer.get_command('prep').reset_cooldown(ctx)
                return

            role = roleArray[int(tReaction.emoji[0]) - 1]

        prepEmbed.clear_fields()
        prepEmbed.title = f"{game} (Tier {roleArray.index(role) + 1})"
        prepEmbed.description = f"{guildsListStr}{', '.join([g.mention for g in guildsList])}\n**Signup:** {commandPrefix}timer signup charactername \"consumables\"\n**Add to roster:** {commandPrefix}timer add @player\n**Remove from roster:** {commandPrefix}timer remove @player"
        rosterString = ""
        for p in playerRoster:
            if p == author:
                prepEmbed.add_field(name = f"{author.display_name} **(DM)**", value = "The DM has not yet signed up a character for DM rewards")
            else:
                prepEmbed.add_field(name=p.display_name, value='Has not yet signed up a character to play.', inline=False)

        prepEmbed.set_footer(text= f"If enough players are signed up, use {commandPrefix}timer start to start the timer.\n`{commandPrefix}timer help` for a list of timer commands")
        await prepEmbedMsg.edit(embed=prepEmbed)

        signedPlayers = []

        timerStarted = False
        validLevelStart = 1
        validLevelEnd = 1

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

        while not timerStarted:
            msg = await self.bot.wait_for('message', check=lambda m: (f"{commandPrefix}timer signup" in m.content or m.content == f'{commandPrefix}timer start' or f"{commandPrefix}timer remove " in m.content or f"{commandPrefix}timer add " in m.content) and m.channel == channel)
            if f"{commandPrefix}timer signup" in msg.content:
                if msg.author in playerRoster:
                    playerChar = await ctx.invoke(self.timer.get_command('signup'), char=msg, author=msg.author) 
                else:
                    await channel.send(f"{msg.author.display_name}, you are not on the roster to play in this game.")
                    
                if playerChar:
                    if playerRoster.index(playerChar[0]) == 0:
                        prepEmbed.set_field_at(playerRoster.index(playerChar[0]), name=f"{author.display_name} **(DM)**", value= f"{playerChar[1]['Name']} will recieve DM rewards", inline=False)
                        if playerChar[0] in [s[0] for s in signedPlayers]:
                            signedPlayers[0] = playerChar
                        else:
                            signedPlayers.insert(0,playerChar)
                    else:
                        if playerChar[1]['Level'] >= validLevelStart and playerChar[1]['Level'] <= validLevelEnd:
                            prepEmbed.set_field_at(playerRoster.index(playerChar[0]), name=f"{playerChar[1]['Name']}", value= f"{playerChar[0].mention}\nLevel {playerChar[1]['Level']}: {playerChar[1]['Race']} {playerChar[1]['Class']}\nConsumables: {', '.join(playerChar[2]).strip()}\n", inline=False)
                            
                            foundSignedPlayer = False
                            for s in range(len(signedPlayers)):
                                if playerChar[0] == signedPlayers[s][0]:
                                    signedPlayers[s] = playerChar
                                    foundSignedPlayer = True
                            if not foundSignedPlayer:
                                signedPlayers.append(playerChar)
                        else:
                            await channel.send(f"{playerChar[1]['Name']} is not between levels {validLevelStart} - {validLevelEnd} to play in this game. Please choose a different character")
                        
                print(signedPlayers)


            elif f"{commandPrefix}timer add " in msg.content and msg.author == author:
                addUser = await ctx.invoke(self.timer.get_command('add'), msg=msg, prep=True)
                if addUser not in playerRoster:
                    prepEmbed.add_field(name=addUser.display_name, value='Has not yet signed up a character to play.', inline=False)
                    playerRoster.append(addUser)
                else:
                    await channel.send(f'{addUser.display_name} is already on the timer.')


            elif f"{commandPrefix}timer remove " in msg.content and msg.author == author:
                removeUser = await ctx.invoke(self.timer.get_command('remove'), msg=msg, prep=True)

                if playerRoster.index(removeUser) != 0:
                    prepEmbed.remove_field(playerRoster.index(removeUser))
                    playerRoster.remove(removeUser)

                    for s in signedPlayers:
                        if removeUser in s:
                            signedPlayers.remove(s)
                else:
                    await channel.send('You cannot remove yourself from the timer.')

            elif msg.content == f"{commandPrefix}timer start":
                print(signedPlayers)
                if author not in [a[0] for a in signedPlayers]:
                    await channel.send(f'The DM has not signed up yet! Please `{commandPrefix}signup` your character before starting the timer.') 
                elif author in [a[0] for a in signedPlayers] and len(signedPlayers) == 1:
                    await channel.send(f'There are no players signed up! Players, please `{commandPrefix}signup` your character before the DM starts the timer.') 
                else:
                    timerStarted = True

            await prepEmbedMsg.delete()
            prepEmbedMsg = await channel.send(embed=prepEmbed)

        await ctx.invoke(self.timer.get_command('start'), userList = signedPlayers, game=game, role=role, guildsList = guildsList)

    @timer.command()
    async def signup(self,ctx, char="", author=""):
        if ctx.invoked_with == 'prep' or ctx.invoked_with == "resume":
            channel = ctx.channel
            guild = ctx.guild
            consumablesList = ""
            if f'{commandPrefix}timer signup' == char.content.strip():
                if ctx.invoked_with != "resume":
                    await channel.send(content=f'You did not input a character, please try again.')
                return False

            if 'signup' in char.content:
                charName = char.content.split(f'{commandPrefix}timer signup ')[1]

            else:
                #TODO: make it work with charnames in quotes
                if 'timer add ' in char.content:
                    charName = char.content.split(f'{commandPrefix}timer add ')[1].split(':')[1]
                    charName = charName.strip()
                elif 'timer addme' in char.content:
                    charName = char.content.split(f'{commandPrefix}timer addme')[1]
                    charName = charName.strip() 
                else:
                    await ctx.channel.send("I wasn't able to add this character. Please check your format")
                    return

            if '"' in char.content:
                consumablesList = charName.split('"')[1::2][0].split(', ')
                charName = charName.split('"')[0].strip()


            playersCollection = db.players
            cRecord  = list(playersCollection.find({"User ID": str(author.id), "Name": {"$regex": charName, '$options': 'i' }}))

            if cRecord == list():
                if ctx.invoked_with != "resume":
                    await channel.send(content=f'I was not able to find the character `{charName}`. Please check your spelling and sign up again')
                return False
            if charName == "" or charName is None:
                if ctx.invoked_with != "resume":
                    await channel.send(content=f'You did not input a character, please try again.')
                return False

            cpSplit = cRecord[0]['CP'].split('/')
            if 'Death' in cRecord[0]:
                if ctx.invoked_with != "resume":
                    await channel.send(content=f'You cannot signup with `{cRecord[0]["Name"]}`, a dying character, please use `{commandPrefix}char death`.')
                return False 

            if cpSplit[0] >= cpSplit[1]:
                if ctx.invoked_with != "resume":
                    await channel.send(content=f'You need to `{commandPrefix}levelup` your character before you can join the game!')
                return False 

            charLevel = cRecord[0]['Level']

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
                    if ctx.invoked_with != "resume":
                        await channel.send(content=f'You are trying to bring in too many consumables')
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
                    print('hello 6')
                    if ctx.invoked_with != "resume":
                        await channel.send(f"These items were not found in your character's consumables:\n`{notValidConsumables}`")
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
            dmChar.append(['Junior Noodle',0,0])


            for r in dmChar[0].roles:
                if 'Noodle' in r.name:
                    dmChar[4] = [r.name,0,0]
                    break

            if str(channel.category).lower() not in gameCategory:
                if "no-context" in channel.name or "secret-testing-area" in channel.name:
                    pass
                else: 
                    await channel.send('Try this command in a game channel!')
                    self.timer.get_command('start').reset_cooldown(ctx)
                    return

            if self.timer.get_command('resume').is_on_cooldown(ctx):
                await channel.send(f"There is already a timer that has started in this channel! If you started the timer, type `{commandPrefix}timer stop` to stop the current timer")
                self.timer.get_command('prep').reset_cooldown(ctx)
                return

            startTime = time.time()
            datestart = datetime.now(pytz.timezone(timezoneVar)).strftime("%b-%-d-%y %I:%M %p")
            start = []
            if userList != "norewards" and role:
                for u in userList:
                    start.append(u)
                startTimes = {f"{role} Friend Full Rewards:{startTime}":start} 

                roleString = ""
                if role != "":
                    roleString = f"({role} Friend)"
                await channel.send(content=f"Timer: Starting the timer for - **{game}** {roleString}." )

            else:
                startTimes = {f"No Rewards:{startTime}":start}
                roleString = ""
                await ctx.channel.send(content=f"Timer: Starting the timer for - **{game}** {roleString}.\n" )

            currentTimers.append('#'+channel.name)

            stampEmbed = discord.Embed()
            stampEmbed.title = f'**{game}**: 0 Hours 0 Minutes\n'
            stampEmbed.set_footer(text=f'#{ctx.channel}\n{commandPrefix}timer help for help with the timer.')
            stampEmbed.set_author(name=f'DM: {userName}', icon_url=author.avatar_url)

            if userList != "norewards":
                playerList = []
                for u in userList:
                    consumablesString = ""
                    if u[2] != ['None']:
                        consumablesString = "\nConsumables: " + ', '.join(u[2])
                    stampEmbed.add_field(name=f"**{u[0].display_name}**", value=f"**{u[1]['Name']}**{consumablesString}\n", inline=False)

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
                    await ctx.channel.send(content=f"I could not find any mention of a user to hand out a reward") 
                    return start
            else:
                rewardUser = guild.get_member(rewardList[0])
                startcopy = start.copy()
                userFound = False;
                timeKey = ""
                for u, v in startcopy.items():
                    for item in v:
                        if item[0] == rewardUser:
                            userFound = True
                            timeKey = u
                            currentItem = oldItem = item
                            charConsumableList = currentItem[1]['Consumables'].split(', ')
                            charMagicList = currentItem[1]['Magic Items'].split(', ')
                            break

                if userFound:
                    if '"' in msg.content:
                        consumablesList = msg.content.split('"')[1::2][0].split(', ')

                    else:
                        if not resume:
                            await ctx.channel.send(content=f"You need to reward the user an item from the RIT")
                            return start


                    for query in consumablesList:
                        # API_URL = ('https://api.airtable.com/v0/appF4hiT6A0ISAhUu/RIT?&filterByFormula=(FIND(LOWER(SUBSTITUTE("' + query.replace(" ", "%20") + '"," ","")),LOWER(SUBSTITUTE({Name}," ",""))))').replace("+", "%2B") 

                        rewardConsumable = callAPI('rit',query) 

                        if not rewardConsumable:
                            if not resume:
                                await channel.send('This does not seem to be a valid reward.')
                        else:
                            minor = dmChar[4][2]
                            major = dmChar[4][1]
                              
                            if rewardConsumable['Minor/Major'] == 'Minor':
                                minor += 1
                            elif rewardConsumable['Minor/Major'] == 'Major':
                                major += 1

                            if dmChar[4][0] == 'Mega Noodle':
                                if ((major == 4 and minor > 4) or (major == 3 and minor > 5) or (major == 2 and minor > 6) or (major == 1 and minor > 7) or (major == 0 and minor > 8))  and rewardConsumable['Minor/Major'] == 'Minor':
                                    if not resume:
                                        await ctx.channel.send(content=f"You cannot award anymore minor reward items\nTotal so far: {dmChar[4][1]} Major / {dmChar[4][2]} Minor Items")
                                    return start
                                elif ((minor == 8 and major > 0) or (minor == 7 and major > 1) or (minor == 6 and major > 2) or (minor == 5 and major > 3) or (minor <= 4 and major > 4)) and rewardConsumable['Minor/Major'] == 'Major':
                                    if not resume:
                                        await ctx.channel.send(content=f"You cannot award anymore major reward items\nTotal so far: {dmChar[4][1]} Major / {dmChar[4][2]} Minor Items")
                                    return start
                            elif dmChar[4][0] == 'True Noodle':
                                if ((major == 3 and minor > 3) or (major == 2 and minor > 4) or (major == 1 and minor > 5) or (major == 0 and minor > 6)) and rewardConsumable['Minor/Major'] == 'Minor':
                                    if not resume:
                                        await ctx.channel.send(content=f"You cannot award anymore minor reward items\nTotal so far: {dmChar[4][1]} Major / {dmChar[4][2]} Minor Items")
                                    return start
                                elif ((minor == 6 and major > 0) or (minor == 5 and major > 1) or (minor == 4 and major > 2) or (minor <= 3 and major > 3)) and rewardConsumable['Minor/Major'] == 'Major':
                                    if not resume:
                                        await ctx.channel.send(content=f"You cannot award anymore major reward items\nTotal so far: {dmChar[4][1]} Major / {dmChar[4][2]} Minor Items")
                                    return start
                            elif dmChar[4][0] == 'Elite Noodle':
                                if ((major == 2 and minor > 2) or (major == 1 and minor > 3) or (major == 0 and minor > 4)) and rewardConsumable['Minor/Major'] == 'Minor' :
                                    if not resume:
                                        await ctx.channel.send(content=f"You cannot award anymore minor reward items\nTotal so far: {dmChar[4][1]} Major / {dmChar[4][2]} Minor Items")
                                    return start
                                elif ((minor == 4 and major > 0) or (minor == 3 and major > 1) or (minor <= 2 and major > 2)) and rewardConsumable['Minor/Major'] == 'Major':
                                    if not resume:
                                        await ctx.channel.send(content=f"You cannot award anymore major reward items\nTotal so far: {dmChar[4][1]} Major / {dmChar[4][2]} Minor Items")
                                    return start
                            elif dmChar [4][0] == 'Good Noodle':
                                if ((major == 1 and minor > 2) or (major == 0 and minor > 3)) and rewardConsumable['Minor/Major'] == 'Minor':
                                    if not resume:
                                        await ctx.channel.send(content=f"You cannot award anymore minor reward items\nTotal so far: {dmChar[4][1]} Major / {dmChar[4][2]} Minor Items")
                                    return start
                                elif ((minor == 3 and major > 0) or (minor <= 2 and major > 1)) and rewardConsumable['Minor/Major'] == 'Major':
                                    if not resume:
                                        await ctx.channel.send(content=f"You cannot award anymore major reward items\nTotal so far: {dmChar[4][1]} Major / {dmChar[4][2]} Minor Items")
                                    return start
                            else:
                                if ((major == 1 and minor > 1) or (major == 0 and minor > 2)) and rewardConsumable['Minor/Major'] == 'Minor':
                                    if not resume:
                                        await ctx.channel.send(content=f"You cannot award anymore minor reward items\nTotal so far: {dmChar[4][1]} Major / {dmChar[4][2]} Minor Items")
                                    return start
                                elif ((minor == 2 and major > 0) or (minor <= 1 and major > 1)) and rewardConsumable['Minor/Major'] == 'Major' :
                                    if not resume:
                                        await ctx.channel.send(content=f"You cannot award anymore major reward items\nTotal so far: {dmChar[4][1]} Major / {dmChar[4][2]} Minor Items")
                                    return start

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


                    start[timeKey].remove(oldItem)
                    start[timeKey].append(currentItem)
                    dmChar[4][2] = minor
                    dmChar[4][1] = major

                    if not resume:
                        await ctx.channel.send(content=f"I have rewarded {rewardUser.display_name} `{rewardConsumable['Name']}`.\nTotal so far: {major} Major / {minor} Minor Items")

                else:
                    if not resume:
                        await ctx.channel.send(content=f"{rewardUser} is not on the timer to recieve rewards.")
            return start

    @timer.command()
    async def addme(self,ctx, *, msg, start="" ,prep=None, user="", dmChar="", resume=False, ):
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
                userInfo =  await ctx.invoke(self.timer.get_command('signup'), char=msg, author=addUser) 
                if userInfo:
                    if not resume:
                        addEmbed = discord.Embed()
                        addEmbed.title = f"Add {userInfo[1]['Name']} to timer?"
                        addEmbed.description = f"{addUser.mention} character would to be added to the timer.\n{userInfo[1]['Name']} - Level {userInfo[1]['Level']}: {userInfo[1]['Race']} {userInfo[1]['Class']}\nConsumables: {', '.join(userInfo[2])}\n\n✅ : Add to timer\n\n❌: Deny"
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
            elif '+' in timeKey or 'Full Rewards' in timeKey:
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

            return start

    @timer.command()
    async def add(self,ctx, *, msg, start="",prep=None, resume=False):
        if ctx.invoked_with == 'prep' or ctx.invoked_with == 'resume':
            guild = ctx.guild
            addList = msg.raw_mentions
            addUser = ""
            if addList != list():
                addUser = guild.get_member(addList[0])
                if prep:
                    return addUser
                else:
                    await ctx.invoke(self.timer.get_command('addme'), start=start, msg=msg, user=addUser, resume=resume) 
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

            # duration = 0
            # for t in range(1, len(timeSplit)):
            #     ttemp = timeSplit[t].split('?')
            #     duration += (float(ttemp[1]) - float(ttemp[0]))

            # treasureArray = calculateTreasure(duration,role)
            # treasureString = f"{treasureArray[0]} CP, {treasureArray[1]} TP, and {treasureArray[2]} GP"

            if '-' in userFound or '%' in userFound: 
                if not resume:
                    await ctx.channel.send(content=f"You have already been removed from the timer.")  
            
            elif 'Full Rewards' in userFound:
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

            for key, value in startcopy.items():
                if value:
                    consumablesString = ""
                    rewardsString = ""
                    if value[0][2] != ['None'] and value[0][2] != list():
                        cList = []
                        rList = []

                        for i in value[0][2]:
                            if '+' in i:
                                rList.append(i)
                            else:
                                cList.append(i)

                        if cList != list():
                            consumablesString = "\nConsumables: " + ', '.join(cList)
                        if rList != list():
                            rewardsString = "\nRewards: " + ', '.join(rList)

                    if "Full Rewards" in key and "-" not in key and '%' not in key:
                        embed.add_field(name= f"**{value[0][0].display_name}**", value=f"**{value[0][1]['Name']}**{consumablesString}{rewardsString}", inline=False)
                    elif "-" in key and 'No Rewards' in key:
                        pass
                    elif '%' in key:
                        embed.add_field(name= f"~~{value[0][0].display_name}~~", value=f"**{value[0][1]['Name']}** - **DEATH**{consumablesString}{rewardsString}", inline=False) 
                    else:
                        durationEach = 0
                        timeSplit = (key + f'?{end}').split(':')
                        for t in range(1, len(timeSplit)):
                            ttemp = timeSplit[t].split('?')
                            durationEach += (float(ttemp[1]) - float(ttemp[0]))

                        embed.add_field(name= f"**{value[0][0].display_name}** - {timeConversion(durationEach)} (Latecomer)\n", value=f"**{value[0][1]['Name']}**{consumablesString}{rewardsString}", inline=False)
                  
            embed.title = f'**{game}**: {durationString}'
            msgAfter = False
            async for message in ctx.channel.history(after=embedMsg, limit=1):
                msgAfter = True
            if not msgAfter:
                await embedMsg.edit(embed=embed)
            else:
                if embedMsg:
                    await embedMsg.delete()
                embedMsg = await ctx.channel.send(embed=embed)

            print(start)
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



            def updateCharDB(char, tier, cp, tp, gp, death=False):
                tierTP = f"T{tier} TP"
                cpSplit= char[1]['CP'].split('/')
                leftCP = (float(cp) + float(cpSplit[0])) 
                totalCP = f'{leftCP}/{float(cpSplit[1])}'
                charEndConsumables = char[1]['Consumables']
                charEndMagicList = char[1]['Magic Items']
                if charEndConsumables == '':
                    charEndConsumables = 'None'
                if charEndMagicList == '':
                    charEndMagicList = 'None'

                if (float(treasureArray[0]) + float(cpSplit[0])) > float(cpSplit[1]):
                    totalCP = f'{leftCP}/8.0'

                if tierTP not in char[1]:
                    tpAdd = 0
                else:
                    tpAdd = char[1][tierTP]

                if death:
                    return ({'_id': char[3], "fields": {'Death': f'{{"GP": {float(gp)}, "{tierTP}": {float(tp)}, "Consumables": "{charEndConsumables}", "Magic Items": "{charEndMagicList}", "CP": {float(cp)}}}'}})
                
                return {'_id': char[3], "fields": {'GP': char[1]['GP'] + float(gp), tierTP: tpAdd + float(tp),'Consumables': charEndConsumables, 'Magic Items': charEndMagicList, 'CP': totalCP, 'Games':char[1]['Games'] + 1}}

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

            data = {"records":[]}
            API_URL = ('https://api.airtable.com/v0/apppGo3CcmtyTMxwh/Characters/')

            deathChars = []

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

                if role != "":
                    treasureArray = calculateTreasure(duration,role)
                    treasureString = f"{treasureArray[0]} CP, {treasureArray[1]} TP, and {treasureArray[2]} GP"
                else:
                    treasureString = timeConversion(duration)


                for value in startItemValue:
                    data["records"].append(updateCharDB(value, tierNum, treasureArray[0], treasureArray[1], treasureArray[2], (value in deathChars)))
                    playerList.append(value)

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

            stopEmbed = discord.Embed()
            stopEmbed.title = f"Timer: {game} [END] - {totalDuration}"
            stopEmbed.description = f"{datestart} to {dateend} CDT" 

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
                            temp += f"{v[0].mention} | {v[1]['Name']} {', '.join(vRewardList).strip()}\n"
                        else:
                            temp += f"~~{v[0].mention} | {v[1]['Name']}~~ **DEATH** {', '.join(vRewardList).strip()}\n"
                    if temp == "":
                        temp = 'None'
                    stopEmbed.add_field(name=f"**{key}**\n", value=temp, inline=False)
                    allRewardsTotalString += temp + "\n"

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
                data["records"].append(updateCharDB(dmChar, roleArray.index(dmRole) + 1, treasureArray[3], treasureArray[4], treasureArray[5]))

                playersCollection = db.players
                usersCollection = db.users
                uRecord  = usersCollection.find_one({"User ID": str(dmChar[0].id)})
                noodles = 0
                noodlesGained = int(totalDuration.split(' Hours')[0]) // 3

                print(uRecord)

                if uRecord:
                    noodles += uRecord['Noodles'] + noodlesGained

                noodleString = "\nCurrent Noodles: " + str(noodles)
                dmRoleNames = [r.name for r in dmChar[0].roles]
                if noodles >= 100 and 'True Noodle' in dmRoleNames:
                    noodleRole = get(guild.roles, name = 'Mega Noodle')
                    await dmChar[0].add_roles(noodleRole, reason=f"DMed 100 games. This user has 100+ noodles")
                    await dmChar[0].remove_roles(get(guild.roles, name = 'True Noodle'))
                    noodleString += "\nMega Noodle Role recieved! :tada:"

                elif noodles >= 50 and 'Elite Noodle' in dmRoleNames:
                    noodleRole = get(guild.roles, name = 'True Noodle')
                    await dmChar[0].add_roles(noodleRole, reason=f"DMed 50 games. This user has 50+ noodles")
                    await dmChar[0].remove_roles(get(guild.roles, name = 'Elite Noodle'))
                    noodleString += "\nTrue Noodle Role recieved! :tada:"
                
                elif noodles >= 20 and 'Good Noodle' in dmRoleNames:
                    noodleRole = get(guild.roles, name = 'Elite Noodle')
                    await dmChar[0].add_roles(noodleRole, reason=f"DMed 20 games. This user has 20+ noodles")
                    await dmChar[0].remove_roles(get(guild.roles, name = 'Good Noodle'))
                    noodleString += "\nElite Noodle Role recieved! :tada:"

                elif noodles >= 10:
                    noodleRole = get(guild.roles, name = 'Good Noodle')
                    await dmChar[0].add_roles(noodleRole, reason=f"DMed 10 games. This user has 10+ noodles")
                    noodleString += "\nGood Noodle Role recieved! :tada:"

                timerData = list(map(lambda item: UpdateOne({'_id': item['_id']}, {'$set': item['fields']}), data['records']))

                try:
                    usersCollection.update_one({'User ID': str(dmChar[0].id)}, {"$set": {'User ID':str(dmChar[0].id), 'Noodles': noodles}}, upsert=True)
                    playersCollection.bulk_write(timerData)
                except Exception as e:
                    print ('MONGO ERROR: ' + str(e))
                    charEmbedmsg = await ctx.channel.send(embed=None, content="Uh oh, looks like something went wrong. Please try creating your character again.")
                else:
                    print('Success')

                guildsListStr = ""
                if guildsList != list():
                    guildsListStr = "Guilds: "
                
                stopEmbed.title = f"\n**{game}**\n*Tier {tierNum} Quest* \n#{ctx.channel}"
                stopEmbed.description = f"{guildsListStr}{', '.join([g.mention for g in guildsList])}\n{datestart} to {dateend} CDT ({totalDuration})"
                stopEmbed.add_field(value=f"**DM:** {dmChar[0].mention} | {dmChar[1]['Name']} {':star:' * noodlesGained}{noodleString}", name=f"DM Rewards : (Tier {roleArray.index(dmRole) + 1}) - **{dmtreasureArray[3]} CP, {dmtreasureArray[4]} TP, and {dmtreasureArray[5]} GP**\n")
                sessionLogString = f"\n**{game}**\n*Tier {tierNum} Quest*\n#{ctx.channel}\n\n**Runtime**: {datestart} to {dateend} CDT ({totalDuration})\n\n{allRewardsTotalString}\nGame ID:"

                # Session Log Channel
                logChannel = self.bot.get_channel(577227687962214406) 
                await ctx.channel.send("Timer has been stopped! Your session has been posted in the #session-logs channel")

                sessionMessage = await logChannel.send(embed=stopEmbed)
                stopEmbed.set_footer(text=f"Game ID: {sessionMessage.id}")
                await sessionMessage.edit(embed=stopEmbed)

            else:
                stopEmbed.clear_fields()
                stopEmbed.set_footer(text=stopEmbed.Empty)

                for key, value in allRewardStrings.items():
                  temp = ""
                  for v in value:
                    temp += f"@{v}\n"
                    stopEmbed.add_field(name=key, value=temp, inline=False)
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
    async def resume(self,ctx):
        if not self.timer.get_command('start').is_on_cooldown(ctx):
            def predicate(message):
                return message.author.bot

            channel=ctx.channel
        
            if str(channel.category).lower() not in gameCategory:
                if "no-context" in channel.name or "secret-testing-area" in channel.name:
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

                        if m.content == f'{commandPrefix}timer start':
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
                                dmChar.append(['Junior Noodle',0,0])

                                for r in dmChar[0].roles:
                                    if 'Noodle' in r.name:
                                        dmChar[4] = [r.name,0,0]
                                        break

                        print(start)
                        resumeTimes = {f"{startRole} Friend Full Rewards:{startTime}":start} 


                    else: 
                        resumeTimes = {f"No Rewards:{startTime}":start}

                    async for message in ctx.channel.history(after=timerMessage):
                        if "$timer add " in message.content and not message.author.bot:
                            resumeTimes = await ctx.invoke(self.timer.get_command('add'), start=resumeTimes, msg=message, resume=True)
                        elif  "$timer addme" in message.content and not message.author.bot:
                            resumeTimes = await ctx.invoke(self.timer.get_command('addme'), start=resumeTimes, dmChar=dmChar, msg=message, user=message.author, resume=True) 
                        elif ("$timer removeme" in message.content or "$timer remove " in message.content) and not message.author.bot: 
                            if "$timer removeme" in message.content:
                                resumeTimes = await ctx.invoke(self.timer.get_command('removeme'), msg=message, start=resumeTimes, role=startRole, user=message.author, resume=True)
                            elif "$timer remove " in message.content:
                                resumeTimes = await ctx.invoke(self.timer.get_command('remove'), msg=message, start=resumeTimes, role=startRole, resume=True)
                        elif "$timer death" in message.content:
                            resumeTimes = await ctx.invoke(self.timer.get_command('death'), msg=message, start=resumeTimes, role=startRole, resume=True) 
                        elif message.content.startswith('-') and message.author != dmChar[0]: 
                            resumeTimes = await ctx.invoke(self.timer.get_command('deductConsumables'), msg=message, start=resumeTimes, resume=True)
                        elif f"{commandPrefix}timer reward" in message.content and (message.author == author):
                            resumeTimes = await ctx.invoke(self.timer.get_command('reward'), msg=message, start=resumeTimes, dmChar=dmChar, resume=True)
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
        while not timerStopped:
            try:
                # TODO add alias [$t]
                msg = await self.bot.wait_for('message', timeout=5.0, check=lambda m: (m.content == f"{commandPrefix}timer stop" or m.content == f"{commandPrefix}timer end" or f"{commandPrefix}timer add" in m.content or m.content == f"{commandPrefix}timer removeme" or f"{commandPrefix}timer transfer " in m.content or f"{commandPrefix}timer remove " in m.content or f"{commandPrefix}timer death " in m.content or m.content.startswith('-') or f"{commandPrefix}timer reward" in m.content) and m.channel == channel)
                if f"{commandPrefix}timer transfer " in msg.content and (msg.author == author or "Mod Friend".lower() in [r.name.lower() for r in msg.author.roles] or "Admins".lower() in [r.name.lower() for r in msg.author.roles]):
                    newUser = msg.content.split(f'{commandPrefix}timer transfer ')[1] 
                    newAuthor = await ctx.invoke(self.timer.get_command('transfer'), user=newUser) 
                    if newAuthor is not None:
                        author = newAuthor
                        await channel.send(f'{author.mention}, the current timer has been transferred to you. Use `{commandPrefix}timer stop` whenever you would like to stop the timer.')
                    else:
                        await channel.send(f'Sorry, I could not find the user `{newUser}` to transfer the timer')
                elif (msg.content == f"{commandPrefix}timer stop" or msg.content == f"{commandPrefix}timer end") and (msg.author == author or "Mod Friend".lower() in [r.name.lower() for r in msg.author.roles] or "Admins".lower() in [r.name.lower() for r in msg.author.roles]):
                    timerStopped = True
                    await ctx.invoke(self.timer.get_command('stop'), start=startTimes, role=role, game=game, datestart=datestart, dmChar=dmChar, guildsList=guildsList)
                    return
                elif f"{commandPrefix}timer add " in msg.content and '@player' not in msg.content:
                    startTimes = await ctx.invoke(self.timer.get_command('add'), start=startTimes, msg=msg)
                    stampEmbedmsg = await ctx.invoke(self.timer.get_command('stamp'), stamp=startTime, role=role, game=game, author=author, start=startTimes, embed=stampEmbed, embedMsg=stampEmbedmsg)
                elif f"{commandPrefix}timer addme" in msg.content and '@player' not in msg.content:
                    startTimes = await ctx.invoke(self.timer.get_command('addme'), start=startTimes, msg=msg, user=msg.author, dmChar=dmChar)
                    stampEmbedmsg = await ctx.invoke(self.timer.get_command('stamp'), stamp=startTime, role=role, game=game, author=author, start=startTimes, embed=stampEmbed, embedMsg=stampEmbedmsg)
                elif msg.content == f"{commandPrefix}timer removeme":
                    startTimes = await ctx.invoke(self.timer.get_command('removeme'), start=startTimes, role=role, user=msg.author)
                    stampEmbedmsg = await ctx.invoke(self.timer.get_command('stamp'), stamp=startTime, role=role, game=game, author=author, start=startTimes, embed=stampEmbed, embedMsg=stampEmbedmsg)
                elif f"{commandPrefix}timer remove" in msg.content and (msg.author == author or "Mod Friend".lower() in [r.name.lower() for r in msg.author.roles] or "Admins".lower() in [r.name.lower() for r in msg.author.roles]): 
                    startTimes = await ctx.invoke(self.timer.get_command('remove'), msg=msg, start=startTimes, role=role)
                    stampEmbedmsg = await ctx.invoke(self.timer.get_command('stamp'), stamp=startTime, role=role, game=game, author=author, start=startTimes, embed=stampEmbed, embedMsg=stampEmbedmsg)
                elif f"{commandPrefix}timer reward" in msg.content and (msg.author == author):
                    startTimes = await ctx.invoke(self.timer.get_command('reward'), msg=msg, start=startTimes,dmChar=dmChar)
                    stampEmbedmsg = await ctx.invoke(self.timer.get_command('stamp'), stamp=startTime, role=role, game=game, author=author, start=startTimes, embed=stampEmbed, embedMsg=stampEmbedmsg)
                elif f"{commandPrefix}timer death" in msg.content and (msg.author == author):
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
