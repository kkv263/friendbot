import asyncio
import traceback
from discord.ext import commands
from os import listdir
from os.path import isfile, join
from itertools import cycle

from bfunc import *

cogs_dir = "cogs"

async def change_status():
      await bot.wait_until_ready()
      statusLoop = cycle(statuses)

      while not bot.is_closed():
          current_status = next(statusLoop)
          await bot.change_presence(activity=discord.Activity(name=current_status, type=discord.ActivityType.watching))
          await asyncio.sleep(5)

@bot.event
async def on_ready():
    print('We have logged in as ' + bot.user.name)
    # bot.loop.create_task(change_status())

    # print(bot.get_guild(575505442109784067).categories)

    #secret area channel
    # channel = bot.get_channel(577611798442803205) 
    # await channel.send('Hello I have restarted uwu')
  
bot.remove_command('help')

@bot.event
async def on_command_error(ctx,error):
    # TODO: Fix for char create and guild create
    msg = None
    print(ctx.invoked_with)
    print(error)

    if isinstance(error, commands.UnexpectedQuoteError) or isinstance(error, commands.ExpectedClosingQuoteError) or isinstance(error, commands.InvalidEndOfQuotedStringError):
        await ctx.channel.send("There seems to be an unexpected or a missing closing quote mark somewhere, please check your format and retry the command. ")
        bot.get_command(ctx.invoked_with).reset_cooldown(ctx)
        return

    elif isinstance(error, commands.CommandOnCooldown):
        if error.retry_after == float('inf'):
            await ctx.channel.send(f"Sorry, the command `{commandPrefix}{ctx.invoked_with}` is already in progress, please complete the command before trying again.")
        else:
            await ctx.channel.send(f"Sorry, the command `{commandPrefix}{ctx.invoked_with}` is on cooldown for you!\nTry the command in the next " + "{:.1f}seconds".format(error.retry_after))
        return

    elif ctx.cog is not None and ctx.cog._get_overridden_method(ctx.cog.cog_command_error) is not None:
        return

    elif isinstance(error, commands.CommandNotFound):
        await ctx.channel.send(f'Sorry, the command `{commandPrefix}{ctx.invoked_with}` is not valid, please try again!')

    else:
        await traceBack(ctx,error)

@bot.command()
async def help(ctx, *, pageString=''):
    def helpCheck(r,u):
        sameMessage = False
        if helpMsg.id == r.message.id:
            sameMessage = True
        return sameMessage and u == ctx.author and (r.emoji == left or r.emoji == right)

    helpEmbedItems = discord.Embed() 
    helpEmbedTimerOne = discord.Embed()
    helpEmbedTimerTwo = discord.Embed()
    helpEmbedGuild = discord.Embed()

    page = 0

    if 'timer' in pageString or 'timer1' in pageString:
        page = 1
    if 'timer2' in pageString:
        page = 2
    elif 'guild' in pageString:
        page = 3

    helpList = [helpEmbedItems,helpEmbedTimerOne, helpEmbedTimerTwo, helpEmbedGuild]

    helpEmbedItems.title = 'Available Item Table Commands'
    helpEmbedItems.add_field(name=commandPrefix + "mit [optional name search]", value="This shows you items from the Magic Item Table, sorted by tier and TP cost. React to the lists to change pages or view items. You can also search by name, for example: " + commandPrefix + "mit Cloak of Displacement" )
    helpEmbedItems.add_field(name=commandPrefix + "rit [optional name search]", value="This shows you items from the Reward Item Table, sorted by tier and Minor / Major. React to the lists to change pages or view items. You can also search by name, for example: " + commandPrefix + "rit Moon-Touched Sword" )
    helpEmbedItems.add_field(name=commandPrefix + "rit random", value="This randomly awards you a Reward Item based on which tier and sub-tier you react to." )

    helpEmbedTimerOne.title = 'Available Timer Commands: Before starting a timer; pt1.\n(Only available in **Game Rooms** and **Campaigns**)'
    helpEmbedTimerOne.add_field(name=commandPrefix + "reward [XhYm] [tier] ", value="This calculates player and DM rewards based on the time and tier you typein. The tier names are **Junior**, **Journey**, **Elite**, and **True**. Example: " + commandPrefix + 'reward 3h30m Elite', inline=False)
    helpEmbedTimerOne.add_field(name=commandPrefix + 'timer prep "@player1, @player2, @player3,..." #guild1, #guild2 gamename', value="Preps a game for @player's and #guilds. This allows the DM and players to signup characters to recieve rewards.", inline=False)
    helpEmbedTimerOne.add_field(name=commandPrefix + 'timer signup charactername', value="Signs up your character to participate and be eligible for rewards", inline=False)
    helpEmbedTimerOne.add_field(name=commandPrefix + 'timer add @player', value="Adds a player to the roster so they can signup their character", inline=False)
    helpEmbedTimerOne.add_field(name=commandPrefix + 'timer remove @player', value="Removes a player from the roster", inline=False)
    helpEmbedTimerOne.add_field(name=commandPrefix + 'timer start', value=f"**Followed by **:`{commandPrefix}timer prep` - Starts a timer to keep track of time and calculate rewards for your game. Only one timer per channel can be active at once, and the timer can only be stopped by the person who started it or a Mod.", inline=False)
    helpEmbedTimerOne.add_field(name=commandPrefix + "timer resume", value="Resumes the last running timer that was started, and behaves identical to " + commandPrefix + "timer start.", inline=False)

    helpEmbedTimerTwo.title = 'Available Timer Commands: During a timer; pt2.\n(Only available in **Game Rooms** and **Campaigns**)'
    helpEmbedTimerTwo.add_field(name=commandPrefix + "timer transfer", value="Transfer the timer from the owner to another user. The new owner will be able to stop the timer.", inline=False)
    helpEmbedTimerTwo.add_field(name=commandPrefix + "timer add @player:charactername \"consumables\"", value="**DM Only**: If you join a game late, this command will add @player to the running timer. Their individual rewards will be displayed once the timer has been stopped.", inline=False)
    helpEmbedTimerTwo.add_field(name=commandPrefix + "timer remove @player", value="**DM Only**: Remove the user mentioned from the running timer and display their individual rewards for the time they played.", inline=False)
    helpEmbedTimerTwo.add_field(name=commandPrefix + "timer removeme", value="If you leave a game early, this command will remove you from the running timer and display your individual rewards for the time you played.", inline=False)
    helpEmbedTimerTwo.add_field(name=commandPrefix + "timer reward @player \"rewards\"", value="**DM Only**: Rewards @player item(s) from the RIT. Reward limits depend on your Noodle Role.", inline=False)
    helpEmbedTimerTwo.add_field(name=commandPrefix + "timer stop", value="**DM Only**: Stops a timer that you have started and shows how much to CP, TP, and gp to reward the players who played have not removed themselves from the timer. If players added themselves, it will display their rewards separately. The timer can only be stopped by the person who started it or a Mod.", inline=False)

    helpEmbedGuild.title = 'Available Guild Commands'
    helpEmbedGuild.add_field(name=commandPrefix + "guild add [username#1234] ", value="This command is **case-sensitive** and is only available to Guildmasters. It allows a Guildmaster to add a member to one of the guilds that they are a Guildmaster of.")
    helpEmbedGuild.add_field(name=commandPrefix + "guild remove [username#1234] ", value="This command is **case-sensitive** and is only available to Guildmasters. It allows a Guildmaster to remove a member from one of the guilds that they are a Guildmaster of.")

    numPages = len(helpList)

    for i in range(0, len(helpList)):
        helpList[i].set_footer(text= f"Page {i+1} of {numPages} -- use {left} or {right} to navigate. ")

    helpMsg = await ctx.channel.send(embed=helpList[page])
    while True:
        await helpMsg.add_reaction(left) 
        await helpMsg.add_reaction(right)
        try:
            hReact, hUser = await bot.wait_for("reaction_add", check=helpCheck, timeout=30.0)
        except asyncio.TimeoutError:
            await helpMsg.edit(content=f"Your help menu has timed out! I'll leave this page open for you. If you need to cycle through the list of commands again use `{commandPrefix}help`!")
            await helpMsg.clear_reactions()
            await helpMsg.add_reaction('💤')
            return
        else:
            if hReact.emoji == left:
                page -= 1
                if page < 0:
                    page = len(helpList) - 1
            if hReact.emoji == right:
                page += 1
                if page > len(helpList) - 1:
                    page = 0

            await helpMsg.edit(embed=helpList[page]) 
            await helpMsg.clear_reactions()


if __name__ == '__main__':
    for extension in [f.replace('.py', '') for f in listdir(cogs_dir) if isfile(join(cogs_dir, f))]:
        try:
            bot.load_extension(cogs_dir + "." + extension)
        except (discord.ClientException, ModuleNotFoundError):
            print(f'Failed to load extension {extension}.')
            traceback.print_exc()

bot.run(token)