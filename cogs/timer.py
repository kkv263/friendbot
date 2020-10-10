import discord
import pytz
import asyncio
import time
import re
from datetime import datetime, timezone
from discord.ext import commands
from bfunc import numberEmojis, calculateTreasure, timeConversion, gameCategory, commandPrefix, roleArray, timezoneVar, currentTimers

class Timer(commands.Cog):
    def __init__ (self, bot):
        self.bot = bot

    @commands.group()
    async def timer(self, ctx):	
        pass
    
    @commands.cooldown(1, float('inf'), type=commands.BucketType.channel) 
    @timer.command()
    async def start(self, ctx, userList, *, game="D&D Game"):
        def startEmbedcheck(r, u):
            return (r.emoji in numberEmojis[:5] or str(r.emoji) == '❌') and u == author

        global currentTimers
        channel = ctx.channel
        author = ctx.author
        user = author.display_name
        userName = author.name
        guild = ctx.guild

        userList = userList.replace(" ", "")


        if str(channel.category).lower() not in gameCategory:
            if "no-context" in channel.name or "secret-testing-area" in channel.name:
                pass
            else: 
                await channel.send('Try this command in a game channel!')
                self.timer.get_command('start').reset_cooldown(ctx)
                return

        if '"' not in ctx.message.content and userList != "norewards":
            await channel.send(f"Please make sure you put quotes `\"` around your list of players and retry the command")
            self.timer.get_command('start').reset_cooldown(ctx)
            return

        if userList != "norewards":
            playerListTemp = userList.split(',')
            playerList = []
            errorList = []
            playerListString = "**Player List:**\n"
            for p in playerListTemp:
                if "<@" in p:
                    userListTemp = re.findall(r'<[@!]*(.*?)>',p)
                    for x in userListTemp:
                        if guild.get_member(int(x)) is not None: 
                            player = guild.get_member(int(x)).display_name
                            playerList.append(player)
                            playerListString += player + '\n'
                        else:
                            errorList.append(p)
                else:
                    if guild.get_member_named(p) is not None: 
                        playerList.append(guild.get_member_named(p).display_name)
                    else:
                        errorList.append(p)

            if errorList: 
                await channel.send(f"I am not able to find these users to start the timer: `{errorList}`")
                self.timer.get_command('start').reset_cooldown(ctx)
                return


        if self.timer.get_command('resume').is_on_cooldown(ctx):
            await channel.send(f"There is already a timer that has started in this channel! If you started the timer, type `{commandPrefix}timer stop` to stop the current timer")
            self.timer.get_command('start').reset_cooldown(ctx)
            return


        startEmbed = discord.Embed ()
        startEmbed.add_field(name=f"React with [1-5] for your type of game: **{game}**\nPlease re-react with your choice if your prompt does not go through.", value=f"{numberEmojis[0]} New / Junior Friend [1-4]\n{numberEmojis[1]} Journey Friend [5-10]\n{numberEmojis[2]} Elite Friend [11-16]\n{numberEmojis[3]} True Friend [17-20]\n{numberEmojis[4]} Timer Only [No Rewards]", inline=False)
        startEmbed.set_author(name=userName, icon_url=author.avatar_url)
        startEmbed.set_footer(text= "React with ❌ to cancel")

        try:
            if userList != "norewards":
                startEmbedmsg = await channel.send(embed=startEmbed)
                for num in range(0,5): await startEmbedmsg.add_reaction(numberEmojis[num])
                await startEmbedmsg.add_reaction('❌')
                tReaction, tUser = await self.bot.wait_for("reaction_add", check=startEmbedcheck, timeout=60)
        except asyncio.TimeoutError:
            if userList != "norewards":
                await startEmbedmsg.delete()
                await channel.send('Timer timed out! You did not pick a tier and will need to start a new timer.')
                self.timer.get_command('start').reset_cooldown(ctx)
        else:
            role = ""
            if userList != "norewards":
                await asyncio.sleep(1) 
                await startEmbedmsg.clear_reactions()

                if tReaction.emoji == '❌':
                    await startEmbedmsg.edit(embed=None, content=f"Timer canceled. Type `{commandPrefix}timer start` to start another timer!")
                    self.timer.get_command('start').reset_cooldown(ctx)
                    return

                role = roleArray[int(tReaction.emoji[0]) - 1]

            startTime = time.time()
            datestart = datetime.now(pytz.timezone(timezoneVar)).strftime("%b-%-d-%y %I:%M %p")
            start = []
            print(userList)
            if userList != "norewards" and role:
                userList = userList.split(',')
                for u in userList:
                    if "<@" in u:
                        userListTemp = re.findall(r'<[@!]*(.*?)>',u)
                        for x in userListTemp:
                            start.append(f"{guild.get_member(int(x))}")
                    else:
                        start.append(f"{guild.get_member_named(u)}")
                startTimes = {f"{role} Friend Full Rewards:{startTime}":start} 

                roleString = ""
                if role != "":
                    roleString = f"({role} Friend)"
                await startEmbedmsg.edit(embed=None, content=f"Timer: Starting the timer for - **{game}** {roleString}. Type \n\n`{commandPrefix}timer stop` - to stop the current timer. This can only be used by the member who started the timer or a Mod.\n`{commandPrefix}timer stamp` - to view the time elapsed on the running timer.\n`{commandPrefix}timer addme` - to add yourself to a game which you are joining late.\n`{commandPrefix}timer removeme` - to remove yourself from a game if you wish to leave early. This command will also calculate your rewards. If you joined late using `$timer addme`, it will remove you from the timer.\n`{commandPrefix}timer remove @player` - exact behavior as `$timer removeme`, but to remove @player. (Timer Owner only)\n`{commandPrefix}timer transfer` - to transfer the timer from the owner to another user.\nPlayer list: `{playerList}`" )

            else:
                startTimes = {f"No Rewards:{startTime}":start}
                roleString = ""
                await ctx.channel.send(content=f"Timer: Starting the timer for - **{game}** {roleString}. Type \n\n`{commandPrefix}timer stop` - to stop the current timer. This can only be used by the member who started the timer or a Mod.\n`{commandPrefix}timer stamp` - to view the time elapsed on the running timer.\n`{commandPrefix}timer addme` - to add yourself to a game which you are joining late.\n`{commandPrefix}timer removeme` - to remove yourself from a game if you wish to leave early. This command will also calculate your rewards. If you joined late using `$timer addme`, it will remove you from the timer.\n`{commandPrefix}timer remove @player` - exact behavior as `$timer removeme`, but to remove @player. (Timer Owner only)\n`{commandPrefix}timer transfer` - to transfer the timer from the owner to another user." )

            print(startTimes)

            currentTimers.append('#'+channel.name)


            stampEmbed = discord.Embed()
            stampEmbed.title = f'**{game}**: 0 Hours 0 Minutes\n'
            stampEmbed.set_footer(text=f'#{ctx.channel}\n{commandPrefix}help timer for help with the timer.')
            stampEmbed.description = playerListString
            stampEmbed.set_author(name=f'DM: {userName}', icon_url=author.avatar_url)
            stampEmbedmsg = await channel.send(embed=stampEmbed)

            timerStopped = False
            while not timerStopped:
                try:
                    msg = await self.bot.wait_for('message', timeout=60.0, check=lambda m: (m.content == f"{commandPrefix}timer stop" or m.content == f"{commandPrefix}timer end" or m.content == f"{commandPrefix}timer stamp" or m.content == f"{commandPrefix}timer addme" or m.content == f"{commandPrefix}timer removeme" or f"{commandPrefix}timer transfer " in m.content or f"{commandPrefix}timer remove " in m.content) and m.channel == channel)
                    if f"{commandPrefix}timer transfer " in msg.content and (msg.author == author or "Mod Friend".lower() in [r.name.lower() for r in msg.author.roles] or "Admins".lower() in [r.name.lower() for r in msg.author.roles]):
                        newUser = msg.content.split(f'{commandPrefix}timer transfer ')[1] 
                        newAuthor = await ctx.invoke(self.timer.get_command('transfer'), user=newUser) 
                        if newAuthor is not None:
                            author = newAuthor
                            await channel.send(f'{author.mention}, the current timer has been transferred to you. Use `{commandPrefix}timer stop` whenever you would like to stop the timer.')
                        else:
                            await channel.send(f'Sorry, I could not find the user `{newUser}` to transfer the timer')
                        stampEmbedmsg = await ctx.invoke(self.timer.get_command('stamp'), stamp=startTime, role=role, game=game, author=author, start=startTimes, embed=stampEmbed, embedMsg=stampEmbedmsg)
                    elif (msg.content == f"{commandPrefix}timer stop" or msg.content == f"{commandPrefix}timer end") and (msg.author == author or "Mod Friend".lower() in [r.name.lower() for r in msg.author.roles] or "Admins".lower() in [r.name.lower() for r in msg.author.roles]):
                        timerStopped = True
                        await ctx.invoke(self.timer.get_command('stop'), start=startTimes, role=role, game=game, datestart=datestart, dmChar=author)
                    elif msg.content == f"{commandPrefix}timer stamp":
                        stampEmbedmsg = await ctx.invoke(self.timer.get_command('stamp'), stamp=startTime, role=role, game=game, author=author, start=startTimes, embed=stampEmbed, embedMsg=stampEmbedmsg)
                    elif msg.content == f"{commandPrefix}timer addme":
                        startTimes = await ctx.invoke(self.timer.get_command('addme'), start=startTimes, user=guild.get_member(msg.author.id))
                        stampEmbedmsg = await ctx.invoke(self.timer.get_command('stamp'), stamp=startTime, role=role, game=game, author=author, start=startTimes, embed=stampEmbed, embedMsg=stampEmbedmsg)
                    elif msg.content == f"{commandPrefix}timer removeme":
                        startTimes = await ctx.invoke(self.timer.get_command('removeme'), start=startTimes, role=role, user=guild.get_member(msg.author.id))
                        stampEmbedmsg = await ctx.invoke(self.timer.get_command('stamp'), stamp=startTime, role=role, game=game, author=author, start=startTimes, embed=stampEmbed, embedMsg=stampEmbedmsg)
                    elif f"{commandPrefix}timer remove" in msg.content and (msg.author == author or "Mod Friend".lower() in [r.name.lower() for r in msg.author.roles] or "Admins".lower() in [r.name.lower() for r in msg.author.roles]): 
                        startTimes = await ctx.invoke(self.timer.get_command('remove'), msg=msg, start=startTimes, role=role)
                        stampEmbedmsg = await ctx.invoke(self.timer.get_command('stamp'), stamp=startTime, role=role, game=game, author=author, start=startTimes, embed=stampEmbed, embedMsg=stampEmbedmsg)

                except asyncio.TimeoutError:
                    stampEmbedmsg = await ctx.invoke(self.timer.get_command('stamp'), stamp=startTime, role=role, game=game, author=author, start=startTimes, embed=stampEmbed, embedMsg=stampEmbedmsg)
                else:
                    pass

            self.timer.get_command('resume').reset_cooldown(ctx)
            self.timer.get_command('start').reset_cooldown(ctx)
            self.timer.get_command('addme').reset_cooldown(ctx)
            currentTimers.remove('#'+channel.name)
        return

    @timer.command()
    async def transfer(self,ctx,user=""):
        if ctx.invoked_with == 'start' or ctx.invoked_with == 'resume':
            guild = ctx.guild
            newUser = guild.get_member_named(user.split('#')[0])
            return newUser 

    @commands.cooldown(1, float('inf'), type=commands.BucketType.user) 
    @timer.command()
    async def addme(self,ctx,start={},user=""):
        if ctx.invoked_with == 'start' or ctx.invoked_with == 'resume':
            startcopy = start.copy()
            userFound = False
            timeKey = ""
            startTime = time.time()
            for u, v in startcopy.items():
                if f"{user.name}#{user.discriminator}" in v:
                    userFound = True
                    timeKey = u
            if not userFound:
                start[f"+Partial Rewards:{startTime}"] = []
                start[f"+Partial Rewards:{startTime}"].append(f"{user.name}#{user.discriminator}")
                await ctx.channel.send(content=f"I've added {user.display_name} to the timer.")
            elif '+' in timeKey or 'Full Rewards' in timeKey:
                await ctx.channel.send(content='You have already been added to the timer')
            elif '-' in timeKey:
                await ctx.channel.send(content='You have been re-added to the timer')
                start[f"{timeKey.replace('-', '+')}:{startTime}"] = start[timeKey]
                del start[timeKey]

        elif ctx.invoked_with == 'addme':
            self.timer.get_command('addme').reset_cooldown(ctx)

        print(start)
        return start

    @timer.command()
    async def removeme(self,ctx,start={},role="",user=""):
        if ctx.invoked_with == 'start' or ctx.invoked_with == 'resume':
            startcopy = start.copy()
            userFound = False
            for u, v in startcopy.items():
                if f"{user.name}#{user.discriminator}" in v:
                    userFound = u

            endTime = time.time()
            if not userFound:
                await ctx.channel.send(content=f"{user}, I couldn't find you on the timer to remove you.") 
                return start

            timeSplit = (userFound + f'?{endTime}').split(':')

            duration = 0
            for t in range(1, len(timeSplit)):
                ttemp = timeSplit[t].split('?')
                duration += (float(ttemp[1]) - float(ttemp[0]))

            # duration = time.time() - float(userFound.split(':')[1])
            treasureArray = calculateTreasure(duration,role)
            treasureString = f"{treasureArray[0]} CP, {treasureArray[1]} TP, and {treasureArray[2]} GP"

            if '-' in userFound: 
               await ctx.channel.send(content=f"You have already been removed from the timer.")  
            
            elif 'Full Rewards' in userFound:
                start[userFound].remove(f"{user.name}#{user.discriminator}")
                start[f"-Partial Rewards:{userFound.split(':')[1]}?{endTime}"] = [f"{user.name}#{user.discriminator}"]
                await ctx.channel.send(content=f"{user}, I've have removed you from the timer.")
            elif '+' in userFound:
                start[f"{userFound.replace('+', '-')}?{endTime}"] = start[userFound]
                del start[userFound]
                await ctx.channel.send(content=f"{user}, I've have removed you from the timer.\nSince you have played for {timeConversion(duration)}, your rewards are - {treasureString}")

            self.timer.get_command('addme').reset_cooldown(ctx)

        print(start)
        return start

    @timer.command()
    async def remove(self,ctx, msg, start={},role=""):
        if ctx.invoked_with == 'start' or ctx.invoked_with == 'resume':
            guild = ctx.guild
            removeList = msg.raw_mentions
            removeUser = ""

            if removeList != list():
                removeUser = guild.get_member(removeList[0])
                await ctx.invoke(self.timer.get_command('removeme'), start=start, role=role, user=removeUser)
            else:
                await ctx.channel.send(content=f"I cannot find any mention of the user you are trying to remove. Please check your format and spelling")

        elif ctx.invoked_with == 'addme':
            self.timer.get_command('addme').reset_cooldown(ctx)

        print(start)
        return start

    
    @timer.command()
    async def stamp(self,ctx, stamp=0, role="", game="", author="", start={}, embed="", embedMsg=""):
        if ctx.invoked_with == 'start' or ctx.invoked_with == 'resume':
            user = author.display_name
            end = time.time()
            duration = end - stamp
            durationString = timeConversion(duration)
            playerStamp = []
            playerListString = ""

            timerListString = "" 
            for key, value in start.items():
                if "-" not in key:
                    playerStamp += start[key]
                if ("Full Rewards" in key or "-" in key or 'No Rewards' in key):
                    pass
                else:
                    durationEach = 0
                    timeSplit = (key + f'?{end}').split(':')
                    for t in range(1, len(timeSplit)):
                        ttemp = timeSplit[t].split('?')
                        durationEach += (float(ttemp[1]) - float(ttemp[0]))
                    
                    timerListString = timerListString + f"{value[0]} - {timeConversion(durationEach)}\n"

            if timerListString:
                timerListString = f'\n**Latecomers:**\n{timerListString}'
                  
            if role != "":
                playerListString = "**Player List:**\n"
                for p in range(len(playerStamp)):
                    playerStamp[p] = ctx.guild.get_member_named(playerStamp[p]).display_name
                    playerListString += playerStamp[p] + '\n' 
            else:
                playerStamp = 'No Rewards'

            embed.title = f'**{game}**: {durationString}'
            embed.description = playerListString + timerListString
            embed.set_author(name=f'DM: {user}', icon_url=author.avatar_url)

            msgAfter = False
            async for message in ctx.channel.history(after=embedMsg, limit=1):
                msgAfter = True
            if not msgAfter and embedMsg:
                await embedMsg.edit(embed=embed)
            else:
                if embedMsg:
                    await embedMsg.delete()
                embedMsg = await ctx.channel.send(embed=embed)

            return embedMsg
            print(start)

    @timer.command(aliases=['end'])
    async def stop(self,ctx,*,start={}, role="", game="", datestart="", dmChar=""):
        if ctx.invoked_with == 'start' or ctx.invoked_with == 'resume':
            if not self.timer.get_command(ctx.invoked_with).is_on_cooldown(ctx):
                await ctx.channel.send(content=f"There is no timer to stop or something went wrong with the timer! If you had a timer previously, try `{commandPrefix}timer resume` to resume a timer")
                return
            author = ctx.author
            user = author.display_name
            end = time.time()
            dateend=datetime.now(pytz.timezone(timezoneVar)).strftime("%I:%M %p")
            allRewardStrings = {}
            treasureString = "No Rewards"


            for startItemKey, startItemValue in start.items():
                duration = 0
                playerList = []
                startItemsList = (startItemKey+ f'?{end}').split(':')
                if "Full Rewards" in startItemKey or  "No Rewards" in startItemKey:
                    totalDuration = timeConversion(end - float(startItemsList[1].split('?')[0]))
                    fullDurationTime = end - float(startItemsList[1].split('?')[0])

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
                    playerList.append(value)

                if "Partial Rewards" in startItemKey and role == "":
                    if treasureString not in allRewardStrings:
                        allRewardStrings[treasureString] = playerList
                    else:
                        allRewardStrings[treasureString] += playerList 
                    
                else:
                    if f'{role} Friend Full Rewards - {treasureString}' in allRewardStrings:
                        allRewardStrings[f'{role} Friend Full Rewards - {treasureString}'] += playerList
                    elif f"{startItemsList[0].replace('+', '').replace('-', '')} - {treasureString}" not in allRewardStrings:
                        allRewardStrings[f"{startItemsList[0].replace('+', '').replace('-', '')} - {treasureString}"] = playerList
                    else:
                        allRewardStrings[f"{startItemsList[0].replace('+', '').replace('-', '')} - {treasureString}"] += playerList

            stopEmbed = discord.Embed()
            stopEmbed.title = f"Timer: {game} [END] - {totalDuration}"
            stopEmbed.description = f"{datestart} to {dateend} CDT" 
            tierNum = 0

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

            if role != "": 
                #sort the elements of reward: player dictionary based on the reward
                def rewardSort(elem):
                    key, value = elem
                    print(key)
                    reg = re.search("(\d+.\d*) CP", key)
                    cp = reg.group(1)
                    return float(cp)
                allRewardsTotalString = ""
                for key, value in sorted(list(allRewardStrings.items()), key=rewardSort, reverse=True):
                    temp = f"**{key}**\n"
                    for v in value:
                      temp += f"@{v} | [Char Name]\n"
                    allRewardsTotalString += temp + "\n"

                dmTotalArray = [calculateTreasure(fullDurationTime,'junior'), calculateTreasure(fullDurationTime,'journey'), calculateTreasure(fullDurationTime,'elite'), calculateTreasure(fullDurationTime,'true')]
                sessionLogString = f"Thanks for playing! Posted below is a session log you can copy and paste into #session-logs.\n```**{game}**\n*Tier {tierNum} Quest*\n#{ctx.channel}\nHobbit-Saving Guild | #hobbit-saving-guild\nFellowship of Friends | #fellowship-of-friends @FellowshipGuildmaster##0002\n\n[Replace this text with an optional flavor description of the quest!]\n\n**Combat**: explain how your quest fulfilled the combat pillar.\n**Exploration**: explain how your quest fulfilled the exploration pillar.\n**Social**: explain how your quest fulfilled the social pillar.\n**HSG**: the party saved Hobbits who were going to be sacrificed.**FoF**: the Fellowship was hired to help save the Hobbits.\n\n**Runtime**: {datestart} to {dateend} CDT ({totalDuration})\n\n{allRewardsTotalString}DM @{dmChar} | [Char Name] (Tier #): #CP/#TP/#GP\n```\nDM, your rewards are listed below depending on the tier of your character.\nJunior T1: {dmTotalArray[0][0]} CP / {dmTotalArray[0][1]} TP / {dmTotalArray[0][2]} GP\nJourney T2: {dmTotalArray[1][0]} CP / {dmTotalArray[1][1]} TP / {dmTotalArray[1][2]} GP\nElite T3: {dmTotalArray[2][0]} CP / {dmTotalArray[2][1]} TP / {dmTotalArray[2][2]} GP\nTrue T4: {dmTotalArray[3][0]} CP / {dmTotalArray[3][1]} TP / {dmTotalArray[3][2]} GP"
                await ctx.channel.send(sessionLogString)

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
    @commands.has_any_role('Dev Friend')
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

            global currentTimers
            author = ctx.author
            user = author.display_name
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
                        if "$timer start" in m.content:
                            commandMessage = m.content
                            author = m.author
                            break

                    start = []
                    if "norewards" not in commandMessage and startRole: 
                        userList = re.search('"([^"]*)"', commandMessage).group(1).split(',')
                        for u in userList:
                            print(u)
                            if "<@" in u:
                                userListTemp = re.findall(r'<[@!]*(.*?)>',u)
                                for x in userListTemp:
                                    start.append(f"{guild.get_member(int(x))}")
                            else:
                                start.append(f"{guild.get_member_named(u)}")
                        resumeTimes = {f"{startRole} Friend Full Rewards:{startTime}":start} 

                    else: 
                        resumeTimes = {f"No Rewards:{startTime}":start}

                    async for message in ctx.channel.history(after=timerMessage):
                        if "$timer addme" in message.content and not message.author.bot:
                            resumeTimesCopy= resumeTimes.copy()
                            userFound = False
                            timeAdd = message.created_at.replace(tzinfo=timezone.utc).timestamp()
                            for u, v in resumeTimesCopy.items():
                                if f"{message.author.name}#{message.author.discriminator}" in v:
                                    userFound = u

                            if not userFound:
                                resumeTimes[f"+Partial Rewards:{timeAdd}"] = [f"{message.author.name}#{message.author.discriminator}"]
                            elif '+' in userFound or 'Full Rewards' in userFound:
                                pass
                            elif '-' in userFound:
                                resumeTimes[f'{userFound.replace("-","+")}:{timeAdd}'] = resumeTimes[userFound]
                                del resumeTimes[userFound]
                        elif ("$timer removeme" in message.content or "$timer remove " in message.content) and not message.author.bot: 
                            if "$timer removeme" in message.content:
                                resumeUser = message.author
                            elif "$timer remove " in message.content:
                              removeList = message.raw_mentions
                              if removeList != list():
                                  resumeUser = guild.get_member(removeList[0])
                              else:
                                  continue
                                
                            resumeTimesCopy= resumeTimes.copy()
                            userFound = False
                            timeRemove = message.created_at.replace(tzinfo=timezone.utc).timestamp() 
                            for u, v in resumeTimesCopy.items():
                                if f"{resumeUser.name}#{resumeUser.discriminator}" in v:
                                    userFound = u

                            if not userFound:
                                pass
                            elif 'Full Rewards' in userFound:
                                resumeTimes[userFound].remove(f"{resumeUser.name}#{resumeUser.discriminator}")
                                resumeTimes[f"-Partial Rewards:{userFound.split(':')[1]}?{timeRemove}"] = [f"{resumeUser.name}#{resumeUser.discriminator}"]
                            elif '+' in userFound:
                                resumeTimes[f"{userFound.replace('+', '-')}?{timeRemove}"] = resumeTimes[userFound]
                                del resumeTimes[userFound]
                        elif ("Thanks for playing!" in message.content) and message.author.bot:
                            await channel.send("There doesn't seem to be a timer to resume here... Please start a new timer!")
                            self.timer.get_command('resume').reset_cooldown(ctx)
                            return
                    break

                    print(resumeTimes)

            if timerMessage is None or commandMessage is None:
                await channel.send("There is no timer in the last 200 messages. Please start a new timer.")
                self.timer.get_command('resume').reset_cooldown(ctx)
                return

            #TODO: if possible reuse below somehow
            await channel.send(embed=None, content=f"Timer: I have resumed the timer for - **{startGame}** {startRole}. Type \n\n`{commandPrefix}timer stop` - to stop the current timer. This can only be used by the member who started the timer or a Mod.\n`{commandPrefix}timer stamp` - to view the time elapsed on the running timer.\n`{commandPrefix}timer addme` - to add yourself to a game which you are joining late.\n`{commandPrefix}timer removeme` - to remove yourself from a game if you wish to leave early. This command will also calculate your rewards. If you joined late using `$timer addme`, it will remove you from the timer.\n`{commandPrefix}timer remove @player` - exact behavior as `$timer removeme`, but to remove @player. (Timer Owner only)\n`{commandPrefix}timer transfer` - to transfer the timer from the owner to another user." )
            currentTimers.append('#'+channel.name)

            stampEmbed = discord.Embed()
            stampEmbed.set_footer(text=f'#{ctx.channel}\n{commandPrefix}help timer for help with the timer.')
            stampEmbed.set_author(name=f'DM: {user}', icon_url=author.avatar_url)
            stampEmbedmsg = None
            stampEmbedmsg = await ctx.invoke(self.timer.get_command('stamp'), stamp=startTime, role=startRole, game=startGame, author=author, start=resumeTimes, embed=stampEmbed, embedMsg=stampEmbedmsg)

            timerStopped = False
            while not timerStopped:
                try:
                    msg = await self.bot.wait_for('message', timeout=60.0, check=lambda m: (m.content == f"{commandPrefix}timer stop" or m.content == f"{commandPrefix}timer end" or m.content == f"{commandPrefix}timer stamp" or m.content == f"{commandPrefix}timer addme" or m.content == f"{commandPrefix}timer removeme" or f"{commandPrefix}timer transfer " in m.content or f"{commandPrefix}timer remove " in m.content) and m.channel == channel)
                    if f"{commandPrefix}timer transfer " in msg.content and (msg.author == author or "Mod Friend".lower() in [r.name.lower() for r in msg.author.roles] or "Admins".lower() in [r.name.lower() for r in msg.author.roles]):
                        newUser = msg.content.split(f'{commandPrefix}timer transfer ')[1] 
                        newAuthor = await ctx.invoke(self.timer.get_command('transfer'), user=newUser) 
                        if newAuthor is not None:
                            author = newAuthor
                            await channel.send(f'{author.mention}, the current timer has been transferred to you. Use `{commandPrefix}timer stop` whenever you would like to stop the timer.')
                        else:
                            await channel.send(f'Sorry, I could not find the user `{newUser}` to transfer the timer')
                        stampEmbedmsg = await ctx.invoke(self.timer.get_command('stamp'), stamp=startTime, role=startRole, game=startGame, author=author, start=resumeTimes, embed=stampEmbed, embedMsg=stampEmbedmsg)
                    elif (msg.content == f"{commandPrefix}timer stop" or msg.content == f"{commandPrefix}timer end") and (msg.author == author or "Mod Friend".lower() in [r.name.lower() for r in msg.author.roles] or "Admins".lower() in [r.name.lower() for r in msg.author.roles]):
                        timerStopped = True
                        await ctx.invoke(self.timer.get_command('stop'), start=resumeTimes, role=startRole, game=startGame, datestart=datestart, dmChar=author)
                    elif msg.content == f"{commandPrefix}timer stamp":
                        stampEmbedmsg = await ctx.invoke(self.timer.get_command('stamp'), stamp=startTime, role=startRole, game=startGame, author=author, start=resumeTimes, embed=stampEmbed, embedMsg=stampEmbedmsg)
                    elif msg.content == f"{commandPrefix}timer addme":
                        resumeTimes = await ctx.invoke(self.timer.get_command('addme'), start=resumeTimes, user=guild.get_member(msg.author.id))
                        stampEmbedmsg = await ctx.invoke(self.timer.get_command('stamp'), stamp=startTime, role=startRole, game=startGame, author=author, start=resumeTimes, embed=stampEmbed, embedMsg=stampEmbedmsg)
                    elif msg.content == f"{commandPrefix}timer removeme":
                        resumeTimes = await ctx.invoke(self.timer.get_command('removeme'), start=resumeTimes, role=startRole, user=guild.get_member(msg.author.id))
                        stampEmbedmsg = await ctx.invoke(self.timer.get_command('stamp'), stamp=startTime, role=startRole, game=startGame, author=author, start=resumeTimes, embed=stampEmbed, embedMsg=stampEmbedmsg)
                    elif f"{commandPrefix}timer remove" in msg.content and '@player' not in msg.content and (msg.author == author or "Mod Friend".lower() in [r.name.lower() for r in msg.author.roles] or "Admins".lower() in [r.name.lower() for r in msg.author.roles]): 
                        resumeTimes = await ctx.invoke(self.timer.get_command('remove'), msg=msg, start=resumeTimes, role=startRole)
                        stampEmbedmsg = await ctx.invoke(self.timer.get_command('stamp'), stamp=startTime, role=startRole, game=startGame, author=author, start=resumeTimes, embed=stampEmbed, embedMsg=stampEmbedmsg)
                except asyncio.TimeoutError:
                    stampEmbedmsg = await ctx.invoke(self.timer.get_command('stamp'), stamp=startTime, role=startRole, game=startGame, author=author, start=resumeTimes, embed=stampEmbed, embedMsg=stampEmbedmsg)
                else:
                    pass

            self.timer.get_command('resume').reset_cooldown(ctx)
            self.timer.get_command('start').reset_cooldown(ctx)
            self.timer.get_command('addme').reset_cooldown(ctx)
            currentTimers.remove('#'+channel.name)
        else:
            await ctx.channel.send(content=f"There is already a timer that has started in this channel! If you started the timer, type `{commandPrefix}timer stop` to stop the current timer")
            return

def setup(bot):
    bot.add_cog(Timer(bot))
