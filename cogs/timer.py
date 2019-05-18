import discord
import pytz
import asyncio
import time
from datetime import datetime
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
            return (r.emoji in numberEmojis[:4] or str(r.emoji) == '❌') and u == author

        global currentTimers
        channel = ctx.channel
        author = ctx.author
        user = author.display_name

        if str(channel.category).lower() not in gameCategory:
            await channel.send('Try this command in a game channel!')
            return

        if author.id == 194049802143662080:
            userName = 'Sir'
        else:
            userName = author.name


        startEmbed = discord.Embed (
          colour = discord.Colour.green(),
        )
        startEmbed.add_field(name=f"React with [1-4] for your type of game: **{game}**", value=f"{numberEmojis[0]} New / Junior Friend [1-4]\n{numberEmojis[1]} Journey Friend [5-10]\n{numberEmojis[2]} Elite Friend [11-16]\n{numberEmojis[3]} True Friend [17-20]", inline=False)
        startEmbed.set_author(name=userName, icon_url=author.avatar_url)
        startEmbed.set_footer(text= "React with ❌ to cancel")

        try:
            startEmbedmsg = await channel.send(embed=startEmbed)
            for num in range(0,4): await startEmbedmsg.add_reaction(numberEmojis[num])
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

            await startEmbedmsg.edit(embed=None, content=f"Timer: Starting the timer for - **{game}** ({role} Friend). Type \n\n`{commandPrefix}timer stop` - to stop the current timer. (Can only be used by the user who has started the timer).\n`{commandPrefix}timer stamp` - to view the time elapsed.\n`{commandPrefix}timer addme` - If you are joining the game late, this will add yourself to the timer.\n`{commandPrefix}timer removeme` - If you wish to leave early, this command will calculate your rewards. (If you joined late using $timer addme, it will remove you from the timer.)" )
            currentTimers.append('#'+channel.name)

            timerStopped = False

            while not timerStopped:
                msg = await self.bot.wait_for('message', check=lambda m: (m.content == f"{commandPrefix}timer stop" or m.content == f"{commandPrefix}timer stamp" or m.content == f"{commandPrefix}timer addme" or m.content == f"{commandPrefix}timer removeme") and m.channel == channel)
                if msg.content == f"{commandPrefix}timer stop" and (msg.author == author or "Mod Friend".lower() in [r.name.lower() for r in msg.author.roles] or "Admins".lower() in [r.name.lower() for r in msg.author.roles]):
                    timerStopped = True
                    await ctx.invoke(self.timer.get_command('stop'), start=startTimes, role=role, game=game, datestart=datestart)
                elif msg.content == f"{commandPrefix}timer stamp":
                    await ctx.invoke(self.timer.get_command('stamp'), stamp=startTimes[f"{role} Friend Rewards"], role=role, game=game, author=msg.author, start=startTimes)
                elif msg.content == f"{commandPrefix}timer addme":
                    startTimes = await ctx.invoke(self.timer.get_command('addme'), start=startTimes, user=msg.author.display_name)
                elif msg.content == f"{commandPrefix}timer removeme":
                    startTimes = await ctx.invoke(self.timer.get_command('removeme'), start=startTimes, role=role, user=msg.author.display_name )

            self.timer.get_command('start').reset_cooldown(ctx)
            self.timer.get_command('addme').reset_cooldown(ctx)
            currentTimers.remove('#'+channel.name)
            return

    @commands.cooldown(1, float('inf'), type=commands.BucketType.user) 
    @timer.command()
    async def addme(self,ctx,start={},user=""):
        if ctx.invoked_with == 'start':
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
        if ctx.invoked_with == 'start':
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
        if ctx.invoked_with == 'start':
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

            msg = await ctx.channel.send(content=f"The timer for **{game}** has been running for {durationString}.{timerListString}")

    @timer.command()
    async def stop(self,ctx,*,start={}, role="", game="", datestart=""):
        if ctx.invoked_with == 'start':
            author = ctx.author
            user = author.display_name
            end = time.time()
            dateend=datetime.now(pytz.timezone(timezoneVar)).strftime("%I:%M %p")
            allRewardStrings = {}

            for startItemKey, startItemValue in start.items():
                duration = end - startItemValue
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
            else:
                stopEmbed.colour = discord.Colour(0x38ceff)
            
            stopEmbed.clear_fields()
            stopEmbed.set_footer(text=stopEmbed.Empty)

            for key, value in allRewardStrings.items():
                stopEmbed.add_field(name=key, value=value, inline=False)

            await ctx.channel.send(embed=stopEmbed)

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

def setup(bot):
    bot.add_cog(Timer(bot))
