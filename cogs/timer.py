import discord
import pytz
import asyncio
import time
from datetime import datetime
from discord.ext import commands
from bfunc import numberEmojis, calculateTreasure, timeConversion, gameCategory, commandPrefix, roleArray, timezoneVar

class Timer(commands.Cog):
    def __init__ (self, bot):
      self.bot = bot

    @commands.cooldown(1, float('inf'), type=commands.BucketType.channel)
    @commands.command()
    async def timerstart(self, ctx, *, game="D&D Game"):
        def startEmbedcheck(r, u):
            return (r.emoji in numberEmojis[:4] or str(r.emoji) == '❌') and u == author

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
          colour = discord.Colour.blue(),
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
            self.timerstart.reset_cooldown(ctx)
        else:
            await asyncio.sleep(1) 
            await startEmbedmsg.clear_reactions()

            if tReaction.emoji == '❌':
                await startEmbedmsg.edit(embed=None, content=f"Timer canceled. Type `{commandPrefix}timerstart` to start another timer!")
                self.timerstart.reset_cooldown(ctx)
                return

            role = roleArray[int(tReaction.emoji[0]) - 1]

            start = time.time()
            datestart= datetime.now(pytz.timezone(timezoneVar)).strftime("%b-%m-%y %I:%M %p")

            await startEmbedmsg.edit(embed=None, content=f"Timer: Starting the timer for - **{game}** ({role} Friend). Type `{commandPrefix}timerstop` to stop the current timer" )
            msg = await self.bot.wait_for('message', check=lambda m: m.content == (f"{commandPrefix}timerstop") and m.channel == channel and (m.author == author or "Mod Friend".lower() in [r.name.lower() for r in m.author.roles] or "Admins".lower() in [r.name.lower() for r in m.author.roles]))

            end = time.time()
            dateend=datetime.now(pytz.timezone(timezoneVar)).strftime("%b-%m-%y %I:%M %p")
            duration = end - start

            durationString = timeConversion(duration)
            treasureArray = calculateTreasure(duration,role)

            treasureString = f"{treasureArray[0]} CP, {treasureArray[1]} TP, and {treasureArray[2]} GP"

            startEmbed.title = f"Timer: {game}"
            startEmbed.description = f"{user}, you stopped the timer."
            startEmbed.clear_fields()
            startEmbed.set_footer(text=startEmbed.Empty)
            startEmbed.add_field(name="Time Started", value=f"{datestart} CDT", inline=True)
            startEmbed.add_field(name="Time Ended", value=f"{dateend} CDT", inline=True)
            startEmbed.add_field(name="Time Duration", value=durationString, inline=False)
            startEmbed.add_field(name=role +" Friend Rewards", value=treasureString, inline=True)
            await channel.send(embed=startEmbed)
            self.timerstart.reset_cooldown(ctx)

def setup(bot):
    bot.add_cog(Timer(bot))
