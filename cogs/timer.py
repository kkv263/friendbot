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
    async def start(self, ctx, *, game="D&D Game"):
        def startEmbedcheck(r, u):
            return (r.emoji in numberEmojis[:5] or str(r.emoji) == '❌') and u == author

        global currentTimers
        channel = ctx.channel
        author = ctx.author
        user = author.display_name
        userName = author.name

        if str(channel.category).lower() not in gameCategory:
            await channel.send('Try this command in a game channel!')
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
            startEmbedmsg = await channel.send(embed=startEmbed)
            for num in range(0,5): await startEmbedmsg.add_reaction(numberEmojis[num])
            await startEmbedmsg.add_reaction('❌')
            tReaction, tUser = await self.bot.wait_for("reaction_add", check=startEmbedcheck, timeout=60)
        except asyncio.TimeoutError:
            await startEmbedmsg.delete()
            await channel.send('Timer timed out! Try starting the timer again.')
            self.timer.get_command('start').reset_cooldown(ctx)
        else:
            await asyncio.sleep(1) 
            await startEmbedmsg.clear_reactions()

            if tReaction.emoji == '❌':
                await startEmbedmsg.edit(embed=None, content=f"Timer canceled. Type `{commandPrefix}timer start` to start another timer!")
                self.timer.get_command('start').reset_cooldown(ctx)
                return

            role = roleArray[int(tReaction.emoji[0]) - 1]

            start = time.time()
            datestart = datetime.now(pytz.timezone(timezoneVar)).strftime("%b-%-d-%y %I:%M %p")
            startTimes = {f"{role} Friend Rewards":start} 

            roleString = ""
            if role != "":
                roleString = f"({role} Friend)"

            await startEmbedmsg.edit(embed=None, content=f"Timer: Starting the timer for - **{game}** {roleString}. Type \n\n`{commandPrefix}timer stop` - to stop the current timer. This can only be used by the member who started the timer or a Mod.\n`{commandPrefix}timer stamp` - to view the time elapsed on the running timer.\n`{commandPrefix}timer addme` - to add yourself to a game which you are joining late.\n`{commandPrefix}timer removeme` - to remove yourself from a game if you wish to leave early. This command will also calculate your rewards. If you joined late using `$timer addme`, it will remove you from the timer.\n`{commandPrefix}timer transfer` - to transfer the timer from the owner to another user." )
            currentTimers.append('#'+channel.name)

            timerStopped = False
            while not timerStopped:
                msg = await self.bot.wait_for('message', check=lambda m: (m.content == f"{commandPrefix}timer stop" or m.content == f"{commandPrefix}timer stamp" or m.content == f"{commandPrefix}timer addme" or m.content == f"{commandPrefix}timer removeme" or f"{commandPrefix}timer transfer " in m.content) and m.channel == channel)
                if f"{commandPrefix}timer transfer " in msg.content and (msg.author == author or "Mod Friend".lower() in [r.name.lower() for r in msg.author.roles] or "Admins".lower() in [r.name.lower() for r in msg.author.roles]):
                    newUser = msg.content.split(f'{commandPrefix}timer transfer ')[1] 
                    newAuthor = await ctx.invoke(self.timer.get_command('transfer'), user=newUser) 
                    if newAuthor is not None:
                        author = newAuthor
                        await channel.send(f'{author.mention}, the current timer has been transferred to you. Use `{commandPrefix}timer stop` whenever you would like to stop the timer.')
                    else:
                        await channel.send(f'Sorry, I could not find the user `{newUser}` to transfer the timer')
                elif msg.content == f"{commandPrefix}timer stop" and (msg.author == author or "Mod Friend".lower() in [r.name.lower() for r in msg.author.roles] or "Admins".lower() in [r.name.lower() for r in msg.author.roles]):
                    timerStopped = True
                    await ctx.invoke(self.timer.get_command('stop'), start=startTimes, role=role, game=game, datestart=datestart)
                elif msg.content == f"{commandPrefix}timer stamp":
                    await ctx.invoke(self.timer.get_command('stamp'), stamp=startTimes[f"{role} Friend Rewards"], role=role, game=game, author=author, start=startTimes)
                elif msg.content == f"{commandPrefix}timer addme":
                    startTimes = await ctx.invoke(self.timer.get_command('addme'), start=startTimes, user=msg.author.display_name)
                elif msg.content == f"{commandPrefix}timer removeme":
                    startTimes = await ctx.invoke(self.timer.get_command('removeme'), start=startTimes, role=role, user=msg.author.display_name )

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
            if user not in start.keys(): 
                datestart = user
                start[datestart] = time.time()
                await ctx.channel.send(content=f"I've added {user} to the timer.")
            else:
                await ctx.channel.send(content='You have already added yourself to the timer')
        elif ctx.invoked_with == 'addme':
            self.timer.get_command('addme').reset_cooldown(ctx)

        return start

    @timer.command()
    async def removeme(self,ctx,start={},role="",user=""):
        if ctx.invoked_with == 'start' or ctx.invoked_with == 'resume':
            if user in start.keys():
                duration = time.time() - start[user] 
                del start[user]
            else:
                duration = time.time() - start[f"{role} Friend Rewards"]

            treasureArray = calculateTreasure(duration,role)
            treasureString = f"{treasureArray[0]} CP, {treasureArray[1]} TP, and {treasureArray[2]} GP"
            await ctx.channel.send(content=f"{user}, I've have removed you from the timer.\nSince you have played for {timeConversion(duration)}, your rewards are - {treasureString}")
            self.timer.get_command('addme').reset_cooldown(ctx)

        return start
    
    @timer.command()
    async def stamp(self,ctx, stamp=0, role="", game="", author="", start={}):
        if ctx.invoked_with == 'start' or ctx.invoked_with == 'resume':
            user = author.display_name
            end = time.time()
            duration = end - stamp
            durationString = timeConversion(duration)

            timerListString = "\n" 
            for key, value in start.items():
                if ("Rewards" in key):
                    pass
                else:
                    timerListString = timerListString + f"{key} - {timeConversion(end - value)}\n"

            msg = await ctx.channel.send(content=f"The timer for **{game}** has been running for {durationString}.{timerListString}Owner: {user}")

    @timer.command()
    async def stop(self,ctx,*,start={}, role="", game="", datestart=""):
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
                duration = end - startItemValue
                if role != "":
                    treasureArray = calculateTreasure(duration,role)
                    treasureString = f"{treasureArray[0]} CP, {treasureArray[1]} TP, and {treasureArray[2]} GP"
                allRewardStrings[f"{startItemKey} - {timeConversion(duration)}"] = treasureString

            stopEmbed = discord.Embed()
            stopEmbed.title = f"Timer: {game} [END]"
            stopEmbed.description = f"{datestart} to {dateend} CDT" 

            if role == "True":
                stopEmbed.colour = discord.Colour(0x9c3dca)
            elif role == "Elite":
                stopEmbed.colour = discord.Colour(0xa87fff)
            elif role == "Journey":
                stopEmbed.colour = discord.Colour(0x689eff)
            elif role == "":
                stopEmbed.colour = discord.Colour(0xffffff)
            else:
                stopEmbed.colour = discord.Colour(0x38ceff)
            
            stopEmbed.clear_fields()
            stopEmbed.set_footer(text=stopEmbed.Empty)

            for key, value in allRewardStrings.items():
                stopEmbed.add_field(name=key, value=value, inline=False)

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

    @commands.cooldown(1, float('inf'), type=commands.BucketType.channel) 
    @timer.command()
    async def resume(self,ctx):
        if not self.timer.get_command('start').is_on_cooldown(ctx):
            def predicate(message):
                return message.author.bot

            channel=ctx.channel
        
            if str(channel.category).lower() not in gameCategory:
                await channel.send('Try this command in a game channel!')
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

                    async for message in ctx.channel.history(after=timerMessage):
                        if "$timer addme" in message.content and not message.author.bot:
                            resumeTimes[message.author.display_name] = message.created_at.replace(tzinfo=timezone.utc).timestamp()
                        elif "$timer removeme" in message.content and not message.author.bot: 
                            if message.author.display_name in resumeTimes:
                                del resumeTimes[message.author.display_name]
                    break

            if timerMessage is None:
                await channel.send("There is no timer in the last 200 messages. Please start a new timer.")
                self.timer.get_command('resume').reset_cooldown(ctx)
                return

            #TODO: if possible reuse below somehow
            await channel.send(embed=None, content=f"Timer: I have resumed the timer for - **{startGame}** {startRole}. Type \n\n`{commandPrefix}timer stop` - to stop the current timer. This can only be used by the member who started the timer or a Mod.\n`{commandPrefix}timer stamp` - to view the time elapsed on the running timer.\n`{commandPrefix}timer addme` - to add yourself to a game which you are joining late.\n`{commandPrefix}timer removeme` - to remove yourself from a game if you wish to leave early. This command will also calculate your rewards. If you joined late using `$timer addme`, it will remove you from the timer.\n`{commandPrefix}timer transfer` - to transfer the timer from the owner to another user." )
            currentTimers.append('#'+channel.name)

            timerStopped = False
            while not timerStopped:
                msg = await self.bot.wait_for('message', check=lambda m: (m.content == f"{commandPrefix}timer stop" or m.content == f"{commandPrefix}timer stamp" or m.content == f"{commandPrefix}timer addme" or m.content == f"{commandPrefix}timer removeme" or f"{commandPrefix}timer transfer " in m.content) and m.channel == channel)
                if f"{commandPrefix}timer transfer " in msg.content and (msg.author == author or "Mod Friend".lower() in [r.name.lower() for r in msg.author.roles] or "Admins".lower() in [r.name.lower() for r in msg.author.roles]):
                    newUser = msg.content.split(f'{commandPrefix}timer transfer ')[1] 
                    newAuthor = await ctx.invoke(self.timer.get_command('transfer'), user=newUser) 
                    if newAuthor is not None:
                        author = newAuthor
                        await channel.send(f'{author.mention}, the current timer has been transferred to you. Use `{commandPrefix}timer stop` whenever you would like to stop the timer.')
                    else:
                        await channel.send(f'Sorry, I could not find the user `{newUser}` to transfer the timer')
                elif msg.content == f"{commandPrefix}timer stop" and (msg.author == author or "Mod Friend".lower() in [r.name.lower() for r in msg.author.roles] or "Admins".lower() in [r.name.lower() for r in msg.author.roles]):
                    timerStopped = True
                    await ctx.invoke(self.timer.get_command('stop'), start=resumeTimes, role=startRole, game=startGame, datestart=datestart)
                elif msg.content == f"{commandPrefix}timer stamp":
                    await ctx.invoke(self.timer.get_command('stamp'), stamp=resumeTimes[f"{startRole} Friend Rewards"], role=startRole, game=startGame, author=author, start=resumeTimes)
                elif msg.content == f"{commandPrefix}timer addme":
                    resumeTimes = await ctx.invoke(self.timer.get_command('addme'), start=resumeTimes, user=msg.author.display_name)
                elif msg.content == f"{commandPrefix}timer removeme":
                    resumeTimes = await ctx.invoke(self.timer.get_command('removeme'), start=resumeTimes, role=startRole, user=msg.author.display_name )

            self.timer.get_command('resume').reset_cooldown(ctx)
            self.timer.get_command('addme').reset_cooldown(ctx)
            currentTimers.remove('#'+channel.name)
        else:
            await ctx.channel.send(content=f"There is already a timer that has started in this channel! If you started the timer, type `{commandPrefix}timer stop` to stop the current timer")
            return

def setup(bot):
    bot.add_cog(Timer(bot))
